"""Dry-run test launch for hardware action shims.

Launches mock_robot + both action shims in mock_mode for testing
without a real robot or baxter_bridge.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="baxter_hardware_bridge",
            executable="mock_robot",
            name="mock_baxter_robot",
            output="screen",
        ),
        Node(
            package="baxter_hardware_bridge",
            executable="follow_joint_trajectory_shim",
            name="left_arm_shim",
            output="screen",
            parameters=[{
                "side": "left",
                "mock_mode": True,
            }],
        ),
        Node(
            package="baxter_hardware_bridge",
            executable="follow_joint_trajectory_shim",
            name="right_arm_shim",
            output="screen",
            parameters=[{
                "side": "right",
                "mock_mode": True,
            }],
        ),
    ])
