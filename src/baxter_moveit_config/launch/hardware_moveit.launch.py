"""MoveIt against the hardware action shims (no Gazebo).

Assumes the bridge and shims are already running:
    python3 scripts/py_bridge.py
    ros2 launch baxter_hardware_bridge hardware_bringup.launch.py

Then:
    ros2 launch baxter_moveit_config hardware_moveit.launch.py

Planned trajectories go to /robot/limb/<side>/follow_joint_trajectory, i.e.
through the same validation, safety gate and clamp as every other goal. Test it
against mock_robot (dry_run.launch.py mock_mode:=false) before the robot.

Drive it from the RViz MotionPlanning panel (Plan, inspect, then Execute).
The `moveit_left_tiny` example cannot be used here: it asserts that move_group
runs with use_sim_time and refuses to move otherwise, deliberately, so that a
sim example can never command the real robot.
"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

JOINT_STATES = "/robot/joint_states"


def generate_launch_description():
    robot_xacro = (
        Path(get_package_share_directory("baxter_gz_sim"))
        / "urdf"
        / "baxter_gz_control.urdf.xacro"
    )
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", str(robot_xacro)]), value_type=str
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("baxter_moveit_config"), "config", "moveit.rviz"]
                ),
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
                remappings=[("joint_states", JOINT_STATES)],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("baxter_moveit_config"),
                            "launch",
                            "move_group.launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "use_sim_time": "false",
                    "controllers": "hardware",
                    "joint_states_topic": JOINT_STATES,
                }.items(),
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", LaunchConfiguration("rviz_config")],
                # ponytail: same LC_NUMERIC trap as sim_moveit.launch.py -- Qt resets
                # the locale before rclcpp::init and a comma-decimal locale turns
                # kinematics doubles into strings, leaving MotionPlanning empty.
                additional_env={"LC_NUMERIC": "C"},
                condition=IfCondition(LaunchConfiguration("rviz")),
            ),
        ]
    )
