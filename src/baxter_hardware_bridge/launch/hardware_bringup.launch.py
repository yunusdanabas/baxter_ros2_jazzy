"""Hardware bringup launch for Baxter action shims.

Launches FollowJointTrajectory action shims for both arms.
Expects baxter_bridge or equivalent to be running and publishing
/robot/state and /robot/joint_states.

DO NOT use this until I10 hardware bridge non-motion gate has passed.
"""

import subprocess

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def refuse_if_mock_running(context, *args, **kwargs):
    """Abort the launch if mock_robot is up: it publishes a permanently "safe"
    /robot/state, which is exactly the state a hardware shim must not trust."""
    # ponytail: node-name match on `ros2 node list`, one ~2 s discovery pass at
    # bringup. The shim's own publisher-count gate (safety.py) is the real
    # backstop; this just fails loudly instead of arming against a mock.
    try:
        nodes = subprocess.run(
            ["ros2", "node", "list"], capture_output=True, text=True, timeout=15
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Could not check the ROS 2 graph before arming: {exc}")
    if "mock_baxter_robot" in nodes:
        raise RuntimeError(
            "mock_baxter_robot is running; it publishes a fake safe /robot/state. "
            "Stop it (kill by PID) and confirm `ros2 node list` is clean before "
            "bringing up the hardware shims."
        )
    return []


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

        OpaqueFunction(function=refuse_if_mock_running),

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
