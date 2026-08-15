#!/usr/bin/env python3

import time
from typing import List, Optional

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint

from baxter_examples.trajectory_helpers import (
    DEFAULT_MOTION_JOINT,
    JOINT_DELTA_RAD,
    JOINT_LIMITS,
    LEFT_JOINTS,
    RIGHT_JOINTS,
    cancel_active_goal,
    choose_reversible_target,
    positions_for_joints_list as positions_for_joints,
    wait_for_future,
)

FINAL_TOLERANCE_RAD = 0.02
TRAJECTORY_DURATION_SEC = 3.0
SETTLE_TIMEOUT_SEC = 2.0
HOLD_WINDOW_SEC = 1.0


class SimTinyTrajectory(Node):
    def __init__(self) -> None:
        super().__init__("sim_tiny_trajectory")
        self.declare_parameter("cancel_after_sec", 0.0)
        # Defaults are the sim controllers/topic. Hardware overrides these with
        # the shim actions and the bridged /robot/joint_states; the motion logic
        # (measured start, reversible target, tolerance check) is identical.
        self.declare_parameter(
            "left_action", "/left_arm_controller/follow_joint_trajectory"
        )
        self.declare_parameter(
            "right_action", "/right_arm_controller/follow_joint_trajectory"
        )
        self.declare_parameter("joint_states_topic", "/joint_states")
        # Distance and duration were hardcoded, so every run was gentle motion
        # and no tolerance number said anything about speed. Raise offset or
        # drop duration to walk the move toward the shim's 2.0 rad/s clamp.
        self.declare_parameter("duration", TRAJECTORY_DURATION_SEC)
        self.declare_parameter("offset", JOINT_DELTA_RAD)
        # Which joint moves. Everything measured so far moved s1; comparing the
        # same joint on both arms is what tells an asymmetric plan apart from an
        # asymmetric arm (see logs/I20_fast_motion_and_srdf.log.md).
        self.declare_parameter("joint", DEFAULT_MOTION_JOINT)
        self._cancel_after_sec = self.get_parameter("cancel_after_sec").value
        self._duration = float(self.get_parameter("duration").value)
        self._offset = float(self.get_parameter("offset").value)
        self._joint = str(self.get_parameter("joint").value)
        if self._joint not in JOINT_LIMITS:
            raise RuntimeError(
                f"Unknown joint '{self._joint}'; expected one of {sorted(JOINT_LIMITS)}"
            )
        self.left_action = self.get_parameter("left_action").value
        self.right_action = self.get_parameter("right_action").value
        joint_states_topic = self.get_parameter("joint_states_topic").value
        self._latest_joint_state: Optional[JointState] = None
        self._joint_state_sequence = 0
        self._active_goal = None
        self.create_subscription(JointState, joint_states_topic, self._joint_state_cb, 1)

    def _joint_state_cb(self, msg: JointState) -> None:
        # Baxter publishes /robot/joint_states from two nodes: the realtime loop
        # (17 arm + head joints, ~100 Hz) and the end-effector publisher (the
        # gripper joints, ~40 Hz). A single message therefore need not carry the
        # arm at all, so keep a merged view rather than the last message. In sim
        # one publisher sends everything and this is a no-op.
        merged = {}
        if self._latest_joint_state is not None:
            merged.update(
                zip(self._latest_joint_state.name, self._latest_joint_state.position)
            )
        merged.update(zip(msg.name, msg.position))
        combined = JointState()
        combined.header = msg.header
        combined.name = list(merged)
        combined.position = [merged[name] for name in combined.name]
        self._latest_joint_state = combined
        self._joint_state_sequence += 1

    def _motion_index(self, joint_names: List[str]) -> int:
        """Position of the joint being moved, by suffix, in this arm's name list."""
        suffixes = [name.rsplit("_", 1)[1] for name in joint_names]
        try:
            return suffixes.index(self._joint)
        except ValueError:
            raise RuntimeError(
                f"Joint '{self._joint}' is not in {joint_names}"
            )

    def _wait_for_future(self, future, timeout_sec: float, description: str):
        return wait_for_future(self, future, timeout_sec, description)

    def wait_for_fresh_joint_state(
        self, joint_names: List[str], after_sequence: Optional[int] = None, timeout_sec: float = 10.0
    ) -> JointState:
        if after_sequence is None:
            after_sequence = self._joint_state_sequence
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok():
            if self._joint_state_sequence > after_sequence and self._latest_joint_state is not None:
                try:
                    positions_for_joints(self._latest_joint_state, joint_names)
                except RuntimeError:
                    pass          # merged view not complete yet; keep waiting
                else:
                    return self._latest_joint_state
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Timed out waiting for a fresh /joint_states sample")
            rclpy.spin_once(self, timeout_sec=min(0.1, remaining))
        raise RuntimeError("ROS shut down while waiting for /joint_states")

    # Kept as a method, thin: CI's cleanup-handler AST check looks for an
    # attribute call named _cancel_active_goal inside `except BaseException`.
    # Calling the module function directly there would disarm that guard.
    def _cancel_active_goal(self) -> bool:
        canceled = cancel_active_goal(self, self._active_goal, "Controller")
        self._active_goal = None
        return canceled

    def _check_hold(self, joint_names: List[str]) -> None:
        # Judging the first window after cancel measures the settle transient,
        # not a hold failure: a real arm is still decelerating (~0.02 rad on
        # hardware) while sim and mock stop dead. Same settle-then-judge shape
        # as the goal check in send_trajectory — retry the window until the arm
        # is quiet, and fail only if it never goes quiet.
        settle_start = time.monotonic()
        deadline = settle_start + SETTLE_TIMEOUT_SEC
        while True:
            first = self.wait_for_fresh_joint_state(joint_names)
            first_positions = positions_for_joints(first, joint_names)
            window_end = time.monotonic() + HOLD_WINDOW_SEC
            while time.monotonic() < window_end:
                rclpy.spin_once(self, timeout_sec=0.1)
            second = self.wait_for_fresh_joint_state(joint_names)
            second_positions = positions_for_joints(second, joint_names)
            drift = max(
                abs(actual - held)
                for actual, held in zip(second_positions, first_positions)
            )
            if drift <= FINAL_TOLERANCE_RAD or time.monotonic() >= deadline:
                break
        settled_after = time.monotonic() - settle_start
        if drift > FINAL_TOLERANCE_RAD:
            raise RuntimeError(
                f"Canceled trajectory did not hold: drift={drift:.4f} rad after "
                f"{settled_after:.2f} s of settling"
            )
        self.get_logger().info(
            f"Cancellation hold verified: max_drift={drift:.4f} rad "
            f"(settled in {settled_after:.2f} s)"
        )

    def send_trajectory(
        self,
        action_name: str,
        joint_names: List[str],
        start_positions: List[float],
        target_positions: List[float],
        label: str,
    ) -> bool:
        client = ActionClient(self, FollowJointTrajectory, action_name)
        if not client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError(f"Action server not available: {action_name}")

        index = self._motion_index(joint_names)
        motion_joint = joint_names[index]
        travel = abs(target_positions[index] - start_positions[index])
        self.get_logger().info(
            f"{action_name} {label}: {motion_joint} "
            f"{start_positions[index]:.3f} -> "
            f"{target_positions[index]:.3f} rad "
            f"in {self._duration:.2f} s ({travel / self._duration:.2f} rad/s)"
        )

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = joint_names
        # No point at time_from_start=0. The shim seeds its interpolation from
        # the measured pose, so a leading t=0 point is redundant, and the shim
        # now rejects one — it would otherwise be commanded in a single step.
        end_point = JointTrajectoryPoint()
        end_point.positions = target_positions
        end_point.time_from_start.sec = int(self._duration)
        end_point.time_from_start.nanosec = int(
            (self._duration - int(self._duration)) * 1e9
        )
        goal.trajectory.points = [end_point]

        feedback_count = 0

        def on_feedback(_msg) -> None:
            nonlocal feedback_count
            feedback_count += 1

        send_future = client.send_goal_async(goal, feedback_callback=on_feedback)
        goal_handle = self._wait_for_future(send_future, 5.0, f"{action_name} goal response")
        if not goal_handle.accepted:
            raise RuntimeError(f"Goal rejected by {action_name}")

        self._active_goal = goal_handle
        result_future = goal_handle.get_result_async()
        result_started = time.monotonic()
        try:
            while rclpy.ok() and not result_future.done():
                if self._cancel_after_sec > 0 and time.monotonic() - result_started >= self._cancel_after_sec:
                    self._cancel_active_goal()
                    self._check_hold(joint_names)
                    return False
                if time.monotonic() - result_started >= 90.0:
                    raise RuntimeError(f"Timed out waiting for {action_name} result")
                rclpy.spin_once(self, timeout_sec=0.1)
            if not result_future.done():
                raise RuntimeError(f"ROS shut down while waiting for {action_name} result")
            result = result_future.result().result
        except BaseException:
            # A failing cleanup must not replace the exception being propagated.
            # main() dispatches on its type, so letting a cancellation
            # RuntimeError escape here turns Ctrl-C into a misleading error.
            try:
                self._cancel_active_goal()
            except Exception as cancel_error:
                self.get_logger().error(f"Cancellation also failed: {cancel_error}")
            raise
        finally:
            self._active_goal = None

        if result.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            raise RuntimeError(
                f"{action_name} failed with error_code {result.error_code}: {result.error_string}"
            )

        # The I12 gate requires feedback, so a silent action server fails here
        # rather than passing on the strength of the result alone.
        if feedback_count == 0:
            raise RuntimeError(f"{action_name} {label} published no feedback")
        self.get_logger().info(f"{action_name} {label} feedback: {feedback_count} messages")

        # Let the arm settle before judging it. Sim/mock converge on the first
        # sample; a real series-elastic joint is still catching up ~10 ms after
        # the action result, and the error is a max over all 7 joints — the six
        # that only hold station still deviate while s1 swings.
        # ponytail: fixed settle window, no re-commanding. The SDK's
        # move_to_joint_positions re-commands in a 15 s loop; do that instead if
        # a real arm turns out to need help converging rather than just time.
        sequence = self._joint_state_sequence
        settle_deadline = time.monotonic() + SETTLE_TIMEOUT_SEC
        settle_start = time.monotonic()
        while True:
            final_state = self.wait_for_fresh_joint_state(joint_names, after_sequence=sequence)
            sequence = self._joint_state_sequence
            actual_positions = positions_for_joints(final_state, joint_names)
            error = max(
                abs(actual - target)
                for actual, target in zip(actual_positions, target_positions)
            )
            if error <= FINAL_TOLERANCE_RAD or time.monotonic() >= settle_deadline:
                break
        settled_after = time.monotonic() - settle_start
        if error > FINAL_TOLERANCE_RAD:
            raise RuntimeError(
                f"{action_name} {label} final error {error:.4f} rad exceeds "
                f"{FINAL_TOLERANCE_RAD} rad after {settled_after:.2f} s of settling"
            )
        self.get_logger().info(
            f"{action_name} {label} verified: max_error={error:.4f} rad "
            f"(settled in {settled_after:.2f} s)"
        )
        return True

    def run_arm(self, action_name: str, joint_names: List[str]) -> bool:
        start_state = self.wait_for_fresh_joint_state(joint_names)
        start_positions = positions_for_joints(start_state, joint_names)
        target_positions = start_positions.copy()
        index = self._motion_index(joint_names)
        target_positions[index] = choose_reversible_target(
            start_positions[index], self._offset, self._joint
        )
        if not self.send_trajectory(
            action_name, joint_names, start_positions, target_positions, "outbound"
        ):
            return False

        return_state = self.wait_for_fresh_joint_state(joint_names)
        return_positions = positions_for_joints(return_state, joint_names)
        return self.send_trajectory(
            action_name, joint_names, return_positions, start_positions, "return"
        )


def main() -> None:
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = SimTinyTrajectory()
    exit_code = 0
    try:
        if not node.run_arm(node.left_action, LEFT_JOINTS):
            return
        if not node.run_arm(node.right_action, RIGHT_JOINTS):
            return
        node.get_logger().info("Reversible trajectories verified for both arms")
    except KeyboardInterrupt:
        node.get_logger().warning("Interrupted; canceling the active trajectory")
        try:
            node._cancel_active_goal()
        except RuntimeError as error:
            node.get_logger().error(str(error))
            exit_code = 1
    except Exception as error:
        node.get_logger().error(str(error))
        try:
            node._cancel_active_goal()
        except RuntimeError as cancel_error:
            node.get_logger().error(str(cancel_error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
