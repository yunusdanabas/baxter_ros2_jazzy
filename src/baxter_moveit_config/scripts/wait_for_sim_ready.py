#!/usr/bin/env python3

import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState


REQUIRED_JOINTS = {
    "left_s0",
    "left_s1",
    "left_e0",
    "left_e1",
    "left_w0",
    "left_w1",
    "left_w2",
    "right_s0",
    "right_s1",
    "right_e0",
    "right_e1",
    "right_w0",
    "right_w1",
    "right_w2",
    "head_pan",
    "l_gripper_l_finger_joint",
    "r_gripper_l_finger_joint",
}


class WaitForSimReady(Node):
    def __init__(self) -> None:
        super().__init__("wait_for_sim_ready")
        self.declare_parameter("timeout_sec", 60.0)
        self._timeout_sec = self.get_parameter("timeout_sec").value
        self._joint_names = set()
        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 1)
        self._action_names = [
            "/left_arm_controller/follow_joint_trajectory",
            "/right_arm_controller/follow_joint_trajectory",
        ]
        self._action_clients = [
            ActionClient(self, FollowJointTrajectory, name)
            for name in self._action_names
        ]

    def _joint_state_cb(self, msg: JointState) -> None:
        self._joint_names = set(msg.name)

    def wait(self) -> None:
        deadline = time.monotonic() + self._timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            actions_ready = all(client.server_is_ready() for client in self._action_clients)
            if actions_ready and REQUIRED_JOINTS <= self._joint_names:
                self.get_logger().info(
                    "Simulation ready: both arm actions and all 17 independent joints are available"
                )
                return
        missing_joints = sorted(REQUIRED_JOINTS - self._joint_names)
        missing_actions = [
            name
            for name, client in zip(self._action_names, self._action_clients)
            if not client.server_is_ready()
        ]
        raise RuntimeError(
            f"Simulation readiness timed out after {self._timeout_sec:.1f}s; "
            f"missing_joints={missing_joints}; missing_actions={missing_actions}"
        )


def main() -> None:
    rclpy.init()
    node = WaitForSimReady()
    exit_code = 0
    try:
        node.wait()
    except Exception as error:
        node.get_logger().error(str(error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
