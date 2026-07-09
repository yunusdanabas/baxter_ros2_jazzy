#!/usr/bin/env python3
"""Mock Baxter robot for dry-run testing of hardware action shims.

Publishes safe /robot/state and /robot/joint_states so the
FollowJointTrajectory action shim can be exercised without a real
robot or baxter_bridge. Does NOT simulate physics — joint states
stay at the last commanded position (feedthrough).

Usage:
  ros2 run baxter_hardware_bridge mock_robot
  # then in another terminal:
  ros2 run baxter_hardware_bridge follow_joint_trajectory_shim --ros-args -p side:=left -p mock_mode:=true
"""

from typing import List

import rclpy
from baxter_core_msgs.msg import AssemblyState, JointCommand
from rclpy.node import Node
from sensor_msgs.msg import JointState

ALL_JOINTS = [
    "left_s0", "left_s1", "left_e0", "left_e1",
    "left_w0", "left_w1", "left_w2",
    "right_s0", "right_s1", "right_e0", "right_e1",
    "right_w0", "right_w1", "right_w2",
    "head_pan",
]

NEUTRAL_POSITIONS = {
    "left_s0": 0.0, "left_s1": -0.55, "left_e0": 0.0, "left_e1": 0.75,
    "left_w0": 0.0, "left_w1": 1.26, "left_w2": 0.0,
    "right_s0": 0.0, "right_s1": -0.55, "right_e0": 0.0, "right_e1": 0.75,
    "right_w0": 0.0, "right_w1": 1.26, "right_w2": 0.0,
    "head_pan": 0.0,
}

STATE_RATE_HZ = 50.0
JOINT_STATE_RATE_HZ = 100.0


class MockRobot(Node):
    """Publishes safe robot state and echoes joint commands into joint_states."""

    def __init__(self) -> None:
        super().__init__("mock_baxter_robot")

        self.declare_parameter("unsafe", False)
        self._unsafe: bool = self.get_parameter("unsafe").value

        self._positions: dict = dict(NEUTRAL_POSITIONS)

        self._state_pub = self.create_publisher(AssemblyState, "/robot/state", 10)
        self._js_pub = self.create_publisher(JointState, "/robot/joint_states", 10)

        self.create_subscription(
            JointCommand, "/robot/limb/left/joint_command", self._cmd_cb, 10
        )
        self.create_subscription(
            JointCommand, "/robot/limb/right/joint_command", self._cmd_cb, 10
        )

        self.create_timer(1.0 / STATE_RATE_HZ, self._publish_state)
        self.create_timer(1.0 / JOINT_STATE_RATE_HZ, self._publish_joint_states)

        self.get_logger().info(
            f"Mock robot ready (unsafe={self._unsafe}). "
            f"Publishing /robot/state and /robot/joint_states."
        )

    def _publish_state(self) -> None:
        msg = AssemblyState()
        if not self._unsafe:
            msg.ready = True
            msg.enabled = True
            msg.stopped = False
            msg.error = False
            msg.estop_button = AssemblyState.ESTOP_BUTTON_UNPRESSED
            msg.estop_source = AssemblyState.ESTOP_SOURCE_NONE
        else:
            msg.ready = False
            msg.enabled = False
            msg.stopped = True
            msg.error = False
            msg.estop_button = AssemblyState.ESTOP_BUTTON_PRESSED
            msg.estop_source = AssemblyState.ESTOP_SOURCE_USER
        self._state_pub.publish(msg)

    def _publish_joint_states(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self._positions.keys())
        msg.position = [self._positions[n] for n in msg.name]
        self._js_pub.publish(msg)

    def _cmd_cb(self, cmd: JointCommand) -> None:
        for name, pos in zip(cmd.names, cmd.command):
            if name in self._positions:
                self._positions[name] = pos


def main() -> None:
    rclpy.init()
    node = MockRobot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
