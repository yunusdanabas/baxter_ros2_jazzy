#!/usr/bin/env python3

import time
from typing import Optional

import rclpy
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState


LEFT_JOINTS = [
    "left_s0",
    "left_s1",
    "left_e0",
    "left_e1",
    "left_w0",
    "left_w1",
    "left_w2",
]
MOTION_JOINT = "left_s1"
JOINT_OFFSET_RAD = 0.05


class MoveItLeftTiny(Node):
    def __init__(self) -> None:
        super().__init__("moveit_left_tiny")
        self._joint_state: Optional[JointState] = None
        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 10)
        self._client = ActionClient(self, MoveGroup, "/move_action")

    def _joint_state_cb(self, msg: JointState) -> None:
        self._joint_state = msg

    def wait_for_joint_state(self, timeout_sec: float = 30.0) -> JointState:
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and self._joint_state is None:
            if time.monotonic() >= deadline:
                raise RuntimeError("Timed out waiting for /joint_states")
            rclpy.spin_once(self, timeout_sec=0.1)
        if self._joint_state is None:
            raise RuntimeError("Failed to receive /joint_states")
        return self._joint_state

    def run(self) -> None:
        joint_state = self.wait_for_joint_state()
        positions = dict(zip(joint_state.name, joint_state.position))
        missing = [joint for joint in LEFT_JOINTS if joint not in positions]
        if missing:
            raise RuntimeError(f"Missing left arm joints in /joint_states: {missing}")
        if not self._client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError("MoveGroup action server not available: /move_action")

        goal = MoveGroup.Goal()
        goal.request.group_name = "left_arm"
        goal.request.pipeline_id = "ompl"
        goal.request.planner_id = "RRTConnectkConfigDefault"
        goal.request.allowed_planning_time = 5.0
        goal.request.num_planning_attempts = 5
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        constraints = Constraints()
        constraints.name = "tiny_left_arm_delta"
        for joint in LEFT_JOINTS:
            constraint = JointConstraint()
            constraint.joint_name = joint
            constraint.position = positions[joint]
            if joint == MOTION_JOINT:
                constraint.position += JOINT_OFFSET_RAD
            constraint.tolerance_above = 0.01
            constraint.tolerance_below = 0.01
            constraint.weight = 1.0
            constraints.joint_constraints.append(constraint)

        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.planning_scene_diff.robot_state.is_diff = True

        self.get_logger().info(
            f"MoveIt left_arm: moving {MOTION_JOINT} "
            f"{positions[MOTION_JOINT]:.3f} -> "
            f"{positions[MOTION_JOINT] + JOINT_OFFSET_RAD:.3f} rad"
        )
        send_future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            raise RuntimeError("MoveGroup goal rejected")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=60.0)
        if not result_future.done():
            raise RuntimeError("Timed out waiting for MoveGroup result")
        result = result_future.result().result
        if result.error_code.val != 1:
            raise RuntimeError(f"MoveGroup failed with error code {result.error_code.val}")
        self.get_logger().info("MoveIt left-arm plan+execute passed")


def main() -> None:
    rclpy.init()
    node = MoveItLeftTiny()
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
