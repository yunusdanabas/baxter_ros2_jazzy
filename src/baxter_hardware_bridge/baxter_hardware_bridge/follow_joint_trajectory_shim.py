#!/usr/bin/env python3
"""FollowJointTrajectory action shim for Baxter hardware.

Accepts control_msgs/action/FollowJointTrajectory goals on
/robot/limb/{side}/follow_joint_trajectory, validates robot state
and joint names, then publishes baxter_core_msgs/JointCommand at a
bounded rate to /robot/limb/{side}/joint_command.

Safety rules (from S04 bridge architecture):
  - Reject goals unless /robot/state is safe (ready, enabled, not stopped,
    no error, no e-stop).
  - Validate exact 7-joint Baxter names per arm.
  - Publish low set_speed_ratio and joint_command_timeout on startup.
  - On cancel or safety violation: hold current position via JointCommand.
    Never call /robot/set_super_stop for routine cancellation.
  - POSITION_MODE only (mode=1). SAFE_CMD in baxter_bridge clamps to
    position/velocity anyway.

Dry-run mode: set mock_mode:=true to skip the actual JointCommand publishes
so the shim can be tested without a real robot or bridge.
"""

import math
import time
from typing import List, Optional

import rclpy
from baxter_core_msgs.msg import JointCommand
from baxter_hardware_bridge.safety import SafetyStateChecker
from control_msgs.action import FollowJointTrajectory
from control_msgs.msg import JointTrajectoryControllerState
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
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

JOINT_COMMAND_MODE_POSITION = 1
COMMAND_RATE_HZ = 100.0
DEFAULT_SPEED_RATIO = 0.1
DEFAULT_COMMAND_TIMEOUT = 0.2
STATE_TIMEOUT_SEC = 2.0


class FollowJointTrajectoryShim(Node):
    """ROS 2 action server that translates FollowJointTrajectory to JointCommand."""

    def __init__(self) -> None:
        super().__init__("follow_joint_trajectory_shim")

        self.declare_parameter("side", "left")
        self.declare_parameter("mock_mode", False)
        self.declare_parameter("speed_ratio", DEFAULT_SPEED_RATIO)
        self.declare_parameter("command_timeout", DEFAULT_COMMAND_TIMEOUT)
        self.declare_parameter("command_rate", COMMAND_RATE_HZ)

        self._side: str = self.get_parameter("side").value
        self._mock_mode: bool = self.get_parameter("mock_mode").value
        self._speed_ratio: float = self.get_parameter("speed_ratio").value
        self._command_timeout: float = self.get_parameter("command_timeout").value
        self._command_rate: float = self.get_parameter("command_rate").value

        if self._side not in ("left", "right"):
            raise ValueError(f"Invalid side '{self._side}', expected 'left' or 'right'")

        self._joints: List[str] = LEFT_JOINTS if self._side == "left" else RIGHT_JOINTS
        self._action_name: str = f"/robot/limb/{self._side}/follow_joint_trajectory"
        self._cmd_topic: str = f"/robot/limb/{self._side}/joint_command"
        self._speed_topic: str = f"/robot/limb/{self._side}/set_speed_ratio"
        self._timeout_topic: str = f"/robot/limb/{self._side}/joint_command_timeout"

        self._latest_joint_state: Optional[JointState] = None
        self._latest_positions: List[float] = [0.0] * len(self._joints)
        self._cb_group = ReentrantCallbackGroup()

        self._safety = SafetyStateChecker(self)

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
            JointState, "/robot/joint_states", self._joint_state_cb, state_qos
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

        self.get_logger().info(
            f"Action shim ready: {self._action_name} "
            f"-> {self._cmd_topic} (mock_mode={self._mock_mode})"
        )

    def _joint_state_cb(self, msg: JointState) -> None:
        self._latest_joint_state = msg
        name_to_pos = dict(zip(msg.name, msg.position))
        for i, jn in enumerate(self._joints):
            if jn in name_to_pos:
                self._latest_positions[i] = name_to_pos[jn]

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
        if not self._mock_mode:
            self._cmd_pub.publish(self._make_command(positions))
        else:
            self.get_logger().debug(
                f"mock: would publish JointCommand to {self._cmd_topic}",
                throttle_duration_sec=0.5,
            )

    def _hold_position(self) -> None:
        self._publish_command(self._latest_positions)

    def _goal_callback(self, goal_request) -> GoalResponse:
        goal_joints = goal_request.trajectory.joint_names
        if goal_joints != self._joints:
            self.get_logger().error(
                f"Rejected: joint names mismatch. Expected {self._joints}, "
                f"got {goal_joints}"
            )
            return GoalResponse.REJECT

        if not self._safety.is_safe_for_motion():
            self.get_logger().error(
                f"Rejected: robot not safe for motion: {self._safety.describe()}"
            )
            return GoalResponse.REJECT

        self._publish_safety_params()
        self.get_logger().info("Goal accepted")
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle) -> CancelResponse:
        self.get_logger().info("Cancel requested - will hold position")
        return CancelResponse.ACCEPT

    def _execute_callback(self, goal_handle):
        goal: FollowJointTrajectory.Goal = goal_handle.request
        traj = goal.trajectory
        points: List[JointTrajectoryPoint] = traj.points

        if not points:
            goal_handle.abort()
            return FollowJointTrajectory.Result(
                error_code=FollowJointTrajectory.Result.INVALID_GOAL,
                error_string="Empty trajectory",
            )

        feedback = FollowJointTrajectory.Feedback()
        result = FollowJointTrajectory.Result()
        period = 1.0 / self._command_rate
        start_time = time.monotonic()

        for pi, point in enumerate(points):
            target_time = start_time + point.time_from_start.sec + point.time_from_start.nanosec / 1e9

            if pi == 0:
                prev_positions = list(self._latest_positions)
                prev_time = start_time
            else:
                prev = points[pi - 1]
                prev_positions = list(prev.positions)
                prev_time = start_time + prev.time_from_start.sec + prev.time_from_start.nanosec / 1e9

            while True:
                if not rclpy.ok():
                    goal_handle.abort()
                    result.error_code = FollowJointTrajectory.Result.ABORTED
                    result.error_string = "rclpy shutdown"
                    return result

                if goal_handle.is_cancel_requested:
                    self._hold_position()
                    goal_handle.canceled()
                    result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
                    result.error_string = "Canceled, holding position"
                    self.get_logger().info("Goal canceled, holding position")
                    return result

                if not self._safety.is_safe_for_motion():
                    self._hold_position()
                    goal_handle.abort()
                    result.error_code = FollowJointTrajectory.Result.ABORTED
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

                time.sleep(period)

            self._publish_command(list(point.positions))
            self._latest_positions = list(point.positions)

        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        result.error_string = "Goal reached"
        self.get_logger().info("Goal succeeded")
        return result


def main() -> None:
    rclpy.init()
    node = FollowJointTrajectoryShim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
