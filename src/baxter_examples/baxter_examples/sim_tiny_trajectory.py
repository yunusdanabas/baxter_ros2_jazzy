#!/usr/bin/env python3

from typing import List, Optional

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint


LEFT_JOINTS = [
    "left_s0",
    "left_s1",
    "left_e0",
    "left_e1",
    "left_w0",
    "left_w1",
    "left_w2",
]

RIGHT_JOINTS = [
    "right_s0",
    "right_s1",
    "right_e0",
    "right_e1",
    "right_w0",
    "right_w1",
    "right_w2",
]

MOTION_JOINT_INDEX = 1
JOINT_OFFSET_RAD = 0.15
TRAJECTORY_DURATION_SEC = 2.0


def positions_for_joints(joint_state: JointState, joint_names: List[str]) -> List[float]:
    name_to_position = dict(zip(joint_state.name, joint_state.position))
    missing = [name for name in joint_names if name not in name_to_position]
    if missing:
        raise RuntimeError(f"Missing joints in /joint_states: {missing}")
    return [name_to_position[name] for name in joint_names]


class SimTinyTrajectory(Node):
    def __init__(self) -> None:
        super().__init__("sim_tiny_trajectory")
        self._latest_joint_state: Optional[JointState] = None
        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 10)

    def _joint_state_cb(self, msg: JointState) -> None:
        self._latest_joint_state = msg

    def wait_for_joint_states(self, timeout_sec: float = 30.0) -> JointState:
        deadline = self.get_clock().now() + rclpy.duration.Duration(seconds=timeout_sec)
        while rclpy.ok() and self._latest_joint_state is None:
            if self.get_clock().now() >= deadline:
                raise RuntimeError("Timed out waiting for /joint_states")
            rclpy.spin_once(self, timeout_sec=0.1)
        if self._latest_joint_state is None:
            raise RuntimeError("Failed to receive /joint_states")
        return self._latest_joint_state

    def send_tiny_trajectory(
        self,
        action_name: str,
        joint_names: List[str],
        start_positions: List[float],
    ) -> None:
        client = ActionClient(self, FollowJointTrajectory, action_name)
        if not client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError(f"Action server not available: {action_name}")

        target_positions = start_positions.copy()
        target_positions[MOTION_JOINT_INDEX] += JOINT_OFFSET_RAD
        motion_joint = joint_names[MOTION_JOINT_INDEX]
        self.get_logger().info(
            f"{action_name}: moving {motion_joint} "
            f"{start_positions[MOTION_JOINT_INDEX]:.3f} -> "
            f"{target_positions[MOTION_JOINT_INDEX]:.3f} rad"
        )

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = joint_names

        start_point = JointTrajectoryPoint()
        start_point.positions = start_positions
        start_point.time_from_start.sec = 0

        end_point = JointTrajectoryPoint()
        end_point.positions = target_positions
        end_point.time_from_start.sec = int(TRAJECTORY_DURATION_SEC)
        end_point.time_from_start.nanosec = int(
            (TRAJECTORY_DURATION_SEC - int(TRAJECTORY_DURATION_SEC)) * 1e9
        )

        goal.trajectory.points = [start_point, end_point]

        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            raise RuntimeError(f"Goal rejected by {action_name}")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        if result.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            raise RuntimeError(
                f"{action_name} failed with error_code {result.error_code}: {result.error_string}"
            )

        self.get_logger().info(f"{action_name} succeeded")


def main() -> None:
    rclpy.init()
    node = SimTinyTrajectory()

    try:
        joint_state = node.wait_for_joint_states()
        left_start = positions_for_joints(joint_state, LEFT_JOINTS)
        right_start = positions_for_joints(joint_state, RIGHT_JOINTS)

        node.send_tiny_trajectory(
            "/left_arm_controller/follow_joint_trajectory",
            LEFT_JOINTS,
            left_start,
        )
        node.send_tiny_trajectory(
            "/right_arm_controller/follow_joint_trajectory",
            RIGHT_JOINTS,
            right_start,
        )
        node.get_logger().info("Tiny trajectories completed for both arms")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
