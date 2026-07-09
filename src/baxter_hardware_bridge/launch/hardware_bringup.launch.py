"""Hardware bringup launch for Baxter action shims.

Launches FollowJointTrajectory action shims for both arms.
Expects baxter_bridge or equivalent to be running and publishing
/robot/state and /robot/joint_states.

DO NOT use this until I10 hardware bridge non-motion gate has passed.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    mock_mode = LaunchConfiguration("mock_mode")
    speed_ratio = LaunchConfiguration("speed_ratio")
    command_timeout = LaunchConfiguration("command_timeout")

    return LaunchDescription([
        DeclareLaunchArgument("mock_mode", default_value="false",
                              description="If true, skip JointCommand publishes (dry-run)"),
        DeclareLaunchArgument("speed_ratio", default_value="0.1",
                              description="Baxter speed ratio 0.0-1.0 (low for labs)"),
        DeclareLaunchArgument("command_timeout", default_value="0.2",
                              description="JointCommand timeout in seconds"),

        Node(
            package="baxter_hardware_bridge",
            executable="follow_joint_trajectory_shim",
            name="left_arm_shim",
            output="screen",
            parameters=[{
                "side": "left",
                "mock_mode": mock_mode,
                "speed_ratio": speed_ratio,
                "command_timeout": command_timeout,
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
                "speed_ratio": speed_ratio,
                "command_timeout": command_timeout,
            }],
        ),
    ])
