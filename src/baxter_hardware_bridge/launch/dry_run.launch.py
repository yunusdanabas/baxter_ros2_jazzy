"""Dry-run test launch for hardware action shims.

Launches mock_robot + both action shims for testing without a real robot or
baxter_bridge.

mock_mode:=true (the default) keeps the shims from publishing JointCommand at
all, so the mock arm never moves. Pass mock_mode:=false for the closed-loop
rehearsal, where the shims command the mock and it echoes back into
/robot/joint_states.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    mock_mode = LaunchConfiguration("mock_mode")

    return LaunchDescription([
        DeclareLaunchArgument("mock_mode", default_value="true",
                              description="If true, skip JointCommand publishes; "
                                          "false closes the loop through mock_robot"),

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
                "mock_mode": mock_mode,
            }],
        ),
        Node(
            package="baxter_hardware_bridge",
            executable="follow_joint_trajectory_shim",
            name="right_arm_shim",
            output="screen",
            parameters=[{
                "side": "right",
                "mock_mode": mock_mode,
            }],
        ),
    ])
