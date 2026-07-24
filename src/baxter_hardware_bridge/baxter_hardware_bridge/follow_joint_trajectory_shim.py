#!/usr/bin/env python3
"""FollowJointTrajectory action shim for Baxter hardware.

Accepts control_msgs/action/FollowJointTrajectory goals on
/robot/limb/{side}/follow_joint_trajectory, validates robot state
and joint names, then publishes baxter_core_msgs/JointCommand at a
bounded rate to /robot/limb/{side}/joint_command.

Safety rules (from S04 bridge architecture):
  - Reject goals unless /robot/state is safe (ready, enabled, not stopped,
    no error, no e-stop) and /robot/joint_states is present and fresh.
  - Validate exact 7-joint Baxter names per arm, matching point lengths,
    finite positions inside the URDF joint limits, strictly increasing
    time_from_start, and per-segment velocity within both the URDF limit and
    the speed the per-cycle clamp can actually deliver.
    Malformed goals are rejected, never silently repaired.
  - One goal at a time: reject a new goal while another is executing, so two
    executor threads cannot fight over the same joint_command topic.
  - Publish low set_speed_ratio and joint_command_timeout on startup and
    on each accepted goal.
  - Seed the command state from measured joint positions at each goal start,
    so the first command continues from where the arm actually is.
  - Clamp every published command to max_step_rad_per_cycle away from the
    previous one. This is the backstop: nothing reaches the robot without
    passing through it, whatever shape the goal had.
  - On cancel: hold last commanded position via JointCommand, republished for
    hold_duration_sec. A single publish expires with the robot's own
    joint_command_timeout and the arm then falls to gravity compensation.
    Never call /robot/set_super_stop for routine cancellation.
  - On safety violation: stop publishing commands (do not hold-via-command).
    This applies inside a hold too — a hold in progress is abandoned.
  - Abort while holding when a joint lags the command actually sent by more
    than path_tolerance_rad, or when a joint is still moving faster than
    stopped_velocity_tolerance after the final point has been held for
    goal_time_sec. Both hold rather than stop: a lagging arm is not an unsafe
    robot, and stopping commands would drop it into gravity compensation. A
    path-tolerance abort holds the *measured* pose, not the commanded one,
    so a blocked arm is not driven further into whatever is blocking it.
  - POSITION_MODE only (mode=1).

Dry-run mode: set mock_mode:=true to skip the actual JointCommand publishes
so the shim can be tested without a real robot or bridge.
"""

import math
import threading
import time
from typing import List, Optional

import rclpy
from baxter_core_msgs.msg import JointCommand
from baxter_hardware_bridge.executor_util import make_shim_executor
from baxter_hardware_bridge.safety import SafetyStateChecker
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
from trajectory_msgs.msg import JointTrajectoryPoint

LEFT_JOINTS = [
    "left_s0", "left_s1", "left_e0", "left_e1",
    "left_w0", "left_w1", "left_w2",
]
RIGHT_JOINTS = [
    "right_s0", "right_s1", "right_e0", "right_e1",
    "right_w0", "right_w1", "right_w2",
]

# (lower, upper, max_velocity) per joint suffix, transcribed from
# baxter_description/urdf/baxter_base/baxter_base.urdf.xacro. Left and right
# carry identical limits there, so one table serves both arms.
JOINT_LIMITS = {
    "s0": (-1.70167993878, 1.70167993878, 1.5),
    "s1": (-2.147, 1.047, 1.5),
    "e0": (-3.05417993878, 3.05417993878, 1.5),
    "e1": (-0.05, 2.618, 1.5),
    "w0": (-3.059, 3.059, 4.0),
    "w1": (-1.57079632679, 2.094, 4.0),
    "w2": (-3.059, 3.059, 4.0),
}

JOINT_COMMAND_MODE_POSITION = 1
COMMAND_RATE_HZ = 100.0
DEFAULT_SPEED_RATIO = 0.1
DEFAULT_COMMAND_TIMEOUT = 0.2
# 0.02 rad/cycle at 100 Hz = 2 rad/s. The I12 move is 0.35 rad over 3 s
# (~0.0012 rad/cycle), so this leaves ~16x headroom and never binds normally.
DEFAULT_MAX_STEP_RAD = 0.02
DEFAULT_HOLD_DURATION_SEC = 1.0
DEFAULT_JOINT_STATES_STALE_SEC = 2.0
# Both from Rethink's PositionJointTrajectoryActionServer.cfg, the values the
# legacy ROS 1 server actually shipped enabled.
DEFAULT_PATH_TOLERANCE_RAD = 0.2
DEFAULT_STOPPED_VELOCITY_TOLERANCE = 0.25
# Legacy `goal_time`: how long the final point keeps being commanded before the
# stopped-velocity check runs.
DEFAULT_GOAL_TIME_SEC = 0.1

# control_msgs FollowJointTrajectory.Result has no CANCELED/ABORTED codes.
# Use distinct negatives so clients that only read error_code do not treat
# cancel or safety abort as SUCCESSFUL (0). Tolerance failures do have standard
# codes (PATH_TOLERANCE_VIOLATED = -4, GOAL_TOLERANCE_VIOLATED = -5) and use them.
RESULT_CANCELED = -100
RESULT_ABORTED = -101


class FollowJointTrajectoryShim(Node):
    """ROS 2 action server that translates FollowJointTrajectory to JointCommand."""

    def __init__(self) -> None:
        super().__init__("follow_joint_trajectory_shim")

        self.declare_parameter("side", "left")
        self.declare_parameter("mock_mode", False)
        self.declare_parameter("speed_ratio", DEFAULT_SPEED_RATIO)
        self.declare_parameter("command_timeout", DEFAULT_COMMAND_TIMEOUT)
        self.declare_parameter("command_rate", COMMAND_RATE_HZ)
        self.declare_parameter("max_step_rad_per_cycle", DEFAULT_MAX_STEP_RAD)
        self.declare_parameter("hold_duration_sec", DEFAULT_HOLD_DURATION_SEC)
        self.declare_parameter("joint_states_stale_sec", DEFAULT_JOINT_STATES_STALE_SEC)
        self.declare_parameter("path_tolerance_rad", DEFAULT_PATH_TOLERANCE_RAD)
        self.declare_parameter(
            "stopped_velocity_tolerance", DEFAULT_STOPPED_VELOCITY_TOLERANCE
        )
        self.declare_parameter("goal_time_sec", DEFAULT_GOAL_TIME_SEC)

        self._side: str = self.get_parameter("side").value
        self._mock_mode: bool = self.get_parameter("mock_mode").value
        self._speed_ratio: float = self.get_parameter("speed_ratio").value
        self._command_timeout: float = self.get_parameter("command_timeout").value
        self._command_rate: float = self.get_parameter("command_rate").value
        self._max_step: float = self.get_parameter("max_step_rad_per_cycle").value
        self._hold_duration: float = self.get_parameter("hold_duration_sec").value
        self._joint_states_stale_sec: float = self.get_parameter(
            "joint_states_stale_sec"
        ).value
        self._path_tolerance: float = self.get_parameter("path_tolerance_rad").value
        self._stopped_velocity: float = self.get_parameter(
            "stopped_velocity_tolerance"
        ).value
        self._goal_time: float = self.get_parameter("goal_time_sec").value

        if self._side not in ("left", "right"):
            raise ValueError(f"Invalid side '{self._side}', expected 'left' or 'right'")

        self._joints: List[str] = LEFT_JOINTS if self._side == "left" else RIGHT_JOINTS
        # index-paired with self._joints: (lower, upper, max_velocity)
        self._limits = [JOINT_LIMITS[j.rsplit("_", 1)[1]] for j in self._joints]
        self._action_name: str = f"/robot/limb/{self._side}/follow_joint_trajectory"
        self._cmd_topic: str = f"/robot/limb/{self._side}/joint_command"
        self._speed_topic: str = f"/robot/limb/{self._side}/set_speed_ratio"
        self._timeout_topic: str = f"/robot/limb/{self._side}/joint_command_timeout"

        self._latest_joint_state: Optional[JointState] = None
        self._joint_state_ns: int = 0
        self._latest_positions: List[float] = [0.0] * len(self._joints)
        self._latest_velocities: List[float] = [0.0] * len(self._joints)
        self._last_commanded: List[float] = [0.0] * len(self._joints)
        self._goal_lock = threading.Lock()
        self._goal_active = False
        self._cb_group = ReentrantCallbackGroup()

        self._safety = SafetyStateChecker(self, callback_group=self._cb_group)

        cmd_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._cmd_pub = self.create_publisher(JointCommand, self._cmd_topic, cmd_qos)
        self._speed_pub = self.create_publisher(Float64, self._speed_topic, cmd_qos)
        self._timeout_pub = self.create_publisher(Float64, self._timeout_topic, cmd_qos)

        state_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.create_subscription(
            JointState, "/robot/joint_states", self._joint_state_cb, state_qos,
            callback_group=self._cb_group,
        )

        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            self._action_name,
            execute_callback=self._execute_callback,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=self._cb_group,
        )

        self._publish_safety_params()
        self.get_logger().info(
            f"Action shim ready: {self._action_name} "
            f"-> {self._cmd_topic} (mock_mode={self._mock_mode})"
        )

    def _joint_state_cb(self, msg: JointState) -> None:
        self._latest_joint_state = msg
        self._joint_state_ns = self.get_clock().now().nanoseconds
        name_to_pos = dict(zip(msg.name, msg.position))
        # Same preserve-on-missing rule as position. Defaulting a missing joint
        # to 0.0 would let one short velocity array report a fast joint as
        # stopped, and a missed abort is worse than a stale one.
        name_to_vel = dict(zip(msg.name, msg.velocity))
        for i, jn in enumerate(self._joints):
            if jn in name_to_pos:
                self._latest_positions[i] = name_to_pos[jn]
            if jn in name_to_vel:
                self._latest_velocities[i] = name_to_vel[jn]

    def _joint_states_age_sec(self) -> float:
        """Seconds since the last /robot/joint_states, or inf if never seen."""
        if self._latest_joint_state is None:
            return float("inf")
        return (self.get_clock().now().nanoseconds - self._joint_state_ns) / 1e9

    def _publish_safety_params(self) -> None:
        self._speed_pub.publish(Float64(data=self._speed_ratio))
        self._timeout_pub.publish(Float64(data=self._command_timeout))

    def _make_command(self, positions: List[float]) -> JointCommand:
        cmd = JointCommand()
        cmd.mode = JOINT_COMMAND_MODE_POSITION
        cmd.names = list(self._joints)
        cmd.command = list(positions)
        return cmd

    def _publish_command(self, positions: List[float]) -> None:
        """Publish one JointCommand, clamped to max_step_rad_per_cycle.

        Every command reaches the robot through here, so the clamp bounds the
        arm's speed regardless of how the goal that produced it was built.
        """
        step = self._max_step
        clamped = [
            min(max(p, last - step), last + step)
            for p, last in zip(positions, self._last_commanded)
        ]
        if any(c != p for c, p in zip(clamped, positions)):
            self.get_logger().warn(
                f"Command step clamped to {step} rad/cycle", throttle_duration_sec=1.0
            )
        self._last_commanded = clamped
        if not self._mock_mode:
            self._cmd_pub.publish(self._make_command(clamped))
        else:
            self.get_logger().debug(
                f"mock: would publish JointCommand to {self._cmd_topic}",
                throttle_duration_sec=0.5,
            )

    def _hold_position(
        self, positions: Optional[List[float]] = None, duration: Optional[float] = None
    ) -> None:
        """Republish one pose for a while, defaulting to the last command.

        A single publish would expire with the robot's own
        joint_command_timeout (0.2 s), after which the arm falls back to
        gravity compensation instead of holding.

        Pass `positions` to hold somewhere other than the last commanded pose —
        a path-tolerance abort holds the *measured* pose, because the commanded
        one is by definition the pose the arm just failed to reach.
        """
        held = list(self._last_commanded if positions is None else positions)
        period = 1.0 / self._command_rate
        deadline = time.monotonic() + (
            self._hold_duration if duration is None else duration
        )
        while rclpy.ok() and time.monotonic() < deadline:
            # Stated policy: stop commanding on unsafe, never hold through an
            # e-stop. Without this the hold keeps publishing for a full second
            # after the robot goes unsafe.
            if not self._safety.is_safe_for_motion():
                self.get_logger().error(
                    f"Hold abandoned, robot not safe: {self._safety.describe()}"
                )
                return
            self._publish_command(held)
            time.sleep(period)

    def _normalized_points(self, traj):
        """Put a goal trajectory into this shim's joint order and drop a leading
        start-state point. Returns (points, rejection_reason).

        Two things real planners do that a naive reading of the action spec does
        not lead you to expect, both confirmed against MoveIt:

        * The joint order is the planner's, not ours -- MoveIt sends them
          alphabetically (e0, e1, s0, s1, w0, w1, w2). The action defines the
          mapping by *name*, so any permutation is legal and we reorder rather
          than reject.
        * Point 0 is the current state at time_from_start=0, which standard
          controllers treat as "start here". We drop it so the
          strictly-increasing-time rule still guards the case it was written
          for: a t=0 point that is NOT where the arm is, which would exit the
          interpolation loop immediately and command the raw target in one jump.
        """
        names = list(traj.joint_names)
        if sorted(names) != sorted(self._joints):
            return None, (
                f"joint names mismatch. Expected {self._joints}, got {names}"
            )
        for i, point in enumerate(traj.points):
            if len(point.positions) != len(self._joints):
                return None, (
                    f"point {i} has {len(point.positions)} positions, "
                    f"expected {len(self._joints)}"
                )

        order = [names.index(joint) for joint in self._joints]
        if order == list(range(len(self._joints))):
            points = list(traj.points)
        else:
            points = []
            for point in traj.points:
                reordered = JointTrajectoryPoint()
                reordered.positions = [point.positions[i] for i in order]
                reordered.time_from_start = point.time_from_start
                points.append(reordered)

        if not points:
            return points, None
        first = points[0]
        t0 = first.time_from_start.sec + first.time_from_start.nanosec / 1e9
        if t0 > 0.0:
            return points, None
        gap = max(
            abs(pos - measured)
            for pos, measured in zip(first.positions, self._latest_positions)
        )
        # Reuse the path tolerance rather than adding a knob: a genuine start
        # state comes from the current robot state, so the gap is ~0 in practice.
        if gap > self._path_tolerance:
            return points, (
                f"point 0 has time_from_start=0 but is {gap:.3f} rad from the "
                f"measured pose (limit {self._path_tolerance:.3f} rad); a t=0 "
                f"point is only accepted as the current start state"
            )
        if len(points) == 1:
            return points, "trajectory has no points after the start state"
        return points[1:], None

    def _validate_values(self, points) -> Optional[str]:
        """Check positions and timing. Returns a rejection reason, or None.

        Segment 0 is measured against the current arm position, so this must
        only run once /robot/joint_states is known fresh.
        """
        prev_t = 0.0
        prev_pos = list(self._latest_positions)
        # The clamp in _publish_command caps every joint at this speed, so a
        # segment above it can never be delivered: the command falls behind the
        # setpoint every cycle until path tolerance aborts. Reject at accept
        # time with a clear reason instead. Binds only on the wrists, whose URDF
        # limit (4.0 rad/s) is above the clamp's 2.0 rad/s.
        clamp_vmax = self._max_step * self._command_rate
        for i, point in enumerate(points):
            t = point.time_from_start.sec + point.time_from_start.nanosec / 1e9
            if t <= prev_t:
                # A zero/negative/non-increasing time makes the interpolation
                # loop exit immediately and command the raw target in one step.
                return (
                    f"point {i} time_from_start={t:.3f}s must be greater than the "
                    f"previous point's {prev_t:.3f}s"
                )
            for k, pos in enumerate(point.positions):
                lo, hi, vmax = self._limits[k]
                if not math.isfinite(pos):
                    return f"point {i} {self._joints[k]} position is not finite ({pos})"
                if not lo <= pos <= hi:
                    return (
                        f"point {i} {self._joints[k]} position {pos:.3f} is outside "
                        f"limit [{lo:.3f}, {hi:.3f}]"
                    )
                limit = min(vmax, clamp_vmax)
                vel = abs(pos - prev_pos[k]) / (t - prev_t)
                if vel > limit:
                    source = "URDF" if limit == vmax else "max_step_rad_per_cycle"
                    return (
                        f"point {i} {self._joints[k]} needs {vel:.2f} rad/s, "
                        f"limit is {limit:.2f} rad/s ({source})"
                    )
            prev_t = t
            prev_pos = list(point.positions)
        return None

    def _goal_callback(self, goal_request) -> GoalResponse:
        points, reason = self._normalized_points(goal_request.trajectory)
        if reason is not None:
            self.get_logger().error(f"Rejected: {reason}")
            return GoalResponse.REJECT

        age = self._joint_states_age_sec()
        if age > self._joint_states_stale_sec:
            self.get_logger().error(
                f"Rejected: /robot/joint_states is {age:.2f}s old "
                f"(limit {self._joint_states_stale_sec:.2f}s), arm position unknown"
            )
            return GoalResponse.REJECT

        reason = self._validate_values(points)
        if reason is not None:
            self.get_logger().error(f"Rejected: {reason}")
            return GoalResponse.REJECT

        if not self._safety.is_safe_for_motion():
            self.get_logger().error(
                f"Rejected: robot not safe for motion: {self._safety.describe()}"
            )
            return GoalResponse.REJECT

        # One goal at a time. The MultiThreadedExecutor would otherwise run two
        # _execute_callback threads publishing conflicting joint_command values.
        with self._goal_lock:
            if self._goal_active:
                self.get_logger().error("Rejected: another goal is already executing")
                return GoalResponse.REJECT
            self._goal_active = True

        self._publish_safety_params()
        self.get_logger().info("Goal accepted")
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle) -> CancelResponse:
        self.get_logger().info("Cancel requested - will hold position")
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle):
        try:
            return self._run_trajectory(goal_handle)
        finally:
            with self._goal_lock:
                self._goal_active = False

    def _run_trajectory(self, goal_handle):
        goal: FollowJointTrajectory.Goal = goal_handle.request
        traj = goal.trajectory
        # Same view of the trajectory the goal was validated against, so the two
        # cannot disagree about whether a leading start-state point is present.
        points: Optional[List[JointTrajectoryPoint]]
        points, norm_reason = self._normalized_points(traj)

        if not points or norm_reason is not None:
            goal_handle.abort()
            return FollowJointTrajectory.Result(
                error_code=FollowJointTrajectory.Result.INVALID_GOAL,
                error_string=norm_reason or "Empty trajectory",
            )

        # The arm is where the encoders say it is, not where the last goal left
        # _last_commanded. Without this the first goal after startup interpolates
        # from all-zeros and commands a large jump.
        self._last_commanded = list(self._latest_positions)

        feedback = FollowJointTrajectory.Feedback()
        result = FollowJointTrajectory.Result()
        period = 1.0 / self._command_rate
        start_time = time.monotonic()

        for pi, point in enumerate(points):
            target_time = (
                start_time + point.time_from_start.sec + point.time_from_start.nanosec / 1e9
            )

            if pi == 0:
                prev_positions = list(self._last_commanded)
                prev_time = start_time
            else:
                prev = points[pi - 1]
                prev_positions = list(prev.positions)
                prev_time = (
                    start_time + prev.time_from_start.sec + prev.time_from_start.nanosec / 1e9
                )

            while True:
                if not rclpy.ok():
                    goal_handle.abort()
                    result.error_code = RESULT_ABORTED
                    result.error_string = "rclpy shutdown"
                    return result

                if goal_handle.is_cancel_requested:
                    self._hold_position()
                    goal_handle.canceled()
                    result.error_code = RESULT_CANCELED
                    result.error_string = "Canceled, holding position"
                    self.get_logger().info("Goal canceled, holding position")
                    return result

                if not self._safety.is_safe_for_motion():
                    # Stop commanding on unsafe — do not hold-via-command.
                    goal_handle.abort()
                    result.error_code = RESULT_ABORTED
                    result.error_string = f"Safety violation: {self._safety.describe()}"
                    self.get_logger().error(result.error_string)
                    return result

                now = time.monotonic()
                if now >= target_time:
                    break

                if target_time > prev_time:
                    alpha = min(1.0, (now - prev_time) / (target_time - prev_time))
                else:
                    alpha = 1.0

                interp = [
                    prev_positions[k] + alpha * (point.positions[k] - prev_positions[k])
                    for k in range(len(self._joints))
                ]
                self._publish_command(interp)

                feedback.joint_names = list(self._joints)
                feedback.desired.positions = list(interp)
                feedback.actual.positions = list(self._latest_positions)
                feedback.error.positions = [
                    interp[k] - self._latest_positions[k]
                    for k in range(len(self._joints))
                ]
                goal_handle.publish_feedback(feedback)

                # Path tolerance. Measured against the command actually sent,
                # not against `interp` — an executor stall makes `interp` jump
                # past what the clamp let through, and the arm must not be
                # blamed for a setpoint it was never given. Skipped in
                # mock_mode, where nothing is published at all and the measured
                # pose therefore cannot track by construction.
                if not self._mock_mode:
                    tracking = [
                        self._last_commanded[k] - self._latest_positions[k]
                        for k in range(len(self._joints))
                    ]
                    lag = self._worst_tracking_error(tracking)
                    if lag is not None:
                        self._hold_position(self._latest_positions)
                        goal_handle.abort()
                        result.error_code = (
                            FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                        )
                        result.error_string = lag
                        self.get_logger().error(lag)
                        return result

                time.sleep(period)

            self._publish_command(list(point.positions))

        # Settle before judging. Interpolation is linear, so the arm is still at
        # segment speed when the last point lands; checking velocity at that
        # instant measures the cruise, not the stop. The legacy re-commands the
        # final point for `goal_time` before running its own goal check.
        self._hold_position(list(points[-1].positions), self._goal_time)

        still_moving = self._worst_moving_joint()
        if still_moving is not None:
            self._hold_position()
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
            result.error_string = still_moving
            self.get_logger().error(still_moving)
            return result

        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        result.error_string = "Goal reached"
        self.get_logger().info("Goal succeeded")
        return result

    def _worst_tracking_error(self, errors: List[float]) -> Optional[str]:
        """Describe the worst joint lagging past path_tolerance_rad, else None."""
        k = max(range(len(errors)), key=lambda i: abs(errors[i]))
        if abs(errors[k]) <= self._path_tolerance:
            return None
        return (
            f"Path tolerance violated: {self._joints[k]} lags its setpoint by "
            f"{errors[k]:.3f} rad (limit {self._path_tolerance:.3f} rad)"
        )

    def _worst_moving_joint(self) -> Optional[str]:
        """Describe the fastest joint still moving at goal end, else None."""
        vels = self._latest_velocities
        k = max(range(len(vels)), key=lambda i: abs(vels[i]))
        if abs(vels[k]) <= self._stopped_velocity:
            return None
        return (
            f"Goal tolerance violated: {self._joints[k]} still moving at "
            f"{vels[k]:.3f} rad/s (limit {self._stopped_velocity:.3f} rad/s)"
        )


def main() -> None:
    rclpy.init()
    node = FollowJointTrajectoryShim()
    executor = make_shim_executor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
