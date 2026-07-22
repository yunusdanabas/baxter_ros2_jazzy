from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, NotSubstitution, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    headless = LaunchConfiguration("headless")
    launch_rviz = LaunchConfiguration("rviz")
    readiness_timeout = LaunchConfiguration("readiness_timeout")
    rviz_config = LaunchConfiguration("rviz_config")

    robot_xacro = (
        Path(get_package_share_directory("baxter_gz_sim"))
        / "urdf"
        / "baxter_gz_control.urdf.xacro"
    )
    moveit_config = (
        MoveItConfigsBuilder("baxter", package_name="baxter_moveit_config")
        .robot_description(file_path=str(robot_xacro))
        .robot_description_semantic(file_path="config/baxter.srdf")
        .trajectory_execution(
            file_path="config/moveit_controllers_sim.yaml",
            moveit_manage_controllers=False,
        )
        .planning_pipelines(default_planning_pipeline="ompl", pipelines=["ompl"])
        .to_moveit_configs()
    )

    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("baxter_gz_sim"), "launch", "sim.launch.py"])
        ),
        launch_arguments={"headless": headless}.items(),
    )
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("baxter_moveit_config"), "launch", "move_group.launch.py"]
            )
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
    )
    readiness = Node(
        package="baxter_moveit_config",
        executable="wait_for_sim_ready",
        output="screen",
        parameters=[
            {"timeout_sec": ParameterValue(readiness_timeout, value_type=float)},
        ],
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        # ponytail: QApplication calls setlocale(LC_ALL,"") before rclcpp::init, so rcl's
        # YAML parser reads --params-file under LC_NUMERIC. In a comma-decimal locale
        # strtod stops at the '.', "0.005" is stored as a string, and the statically
        # typed declare in MoveIt's kinematics ParamListener throws
        # InvalidParameterTypeException -- which RobotModelLoader does not catch, so
        # loadRobotModel dies and MotionPlanning stays empty.
        # ponytail: LC_NUMERIC only; an explicit LC_ALL in the environment would win.
        additional_env={"LC_NUMERIC": "C"},
        # ponytail: RViz does not need robot_description_planning.joint_limits --
        # move_group owns the limits and RViz just replays its trajectories.
        # URDF/SRDF reach RViz via the /robot_description(_semantic) topics.
        parameters=[
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": True},
        ],
        condition=IfCondition(launch_rviz),
        on_exit=[EmitEvent(event=Shutdown(reason="MoveIt RViz exited"))],
    )

    def start_moveit(event, _context):
        if event.returncode == 0:
            return [move_group, rviz]
        return [
            EmitEvent(event=Shutdown(reason="Simulation readiness failed")),
        ]

    return LaunchDescription(
        [
            DeclareLaunchArgument("headless", default_value="true"),
            # ponytail: headless:=false means "I want to see things", so it implies RViz.
            # CI keeps headless:=true and stays RViz-free.
            DeclareLaunchArgument("rviz", default_value=NotSubstitution(headless)),
            DeclareLaunchArgument("readiness_timeout", default_value="60.0"),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("baxter_moveit_config"), "config", "moveit.rviz"]
                ),
            ),
            sim_launch,
            readiness,
            RegisterEventHandler(
                OnProcessExit(target_action=readiness, on_exit=start_moveit)
            ),
        ]
    )
