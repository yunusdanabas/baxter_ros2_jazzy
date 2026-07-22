import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
    Shutdown,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_gazebo(context):
    headless = LaunchConfiguration("headless").perform(context).lower() == "true"
    command = ["gz", "sim", "-r"]
    if headless:
        command.append("-s")
    command.append("empty.sdf")
    if not headless:
        gui_config = PathJoinSubstitution(
            [FindPackageShare("baxter_gz_sim"), "config", "gz_gui.config"]
        ).perform(context)
        command.extend(["--gui-config", gui_config])
    command.extend(["--force-version", "8"])
    plugin_path = ":".join(
        path
        for path in (
            os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH"),
            os.environ.get("LD_LIBRARY_PATH"),
        )
        if path
    )
    return [
        ExecuteProcess(
            cmd=command,
            name="gazebo",
            output="screen",
            additional_env={
                "GZ_SIM_SYSTEM_PLUGIN_PATH": plugin_path,
            },
            on_exit=Shutdown(),
        )
    ]


def generate_launch_description():
    controllers_yaml = PathJoinSubstitution(
        [FindPackageShare("baxter_gz_sim"), "config", "ros2_controllers.yaml"]
    )
    baxter_xacro = PathJoinSubstitution(
        [FindPackageShare("baxter_gz_sim"), "urdf", "baxter_gz_control.urdf.xacro"]
    )
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", baxter_xacro]),
        value_type=str,
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}, {"use_sim_time": True}],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "/robot_description", "-name", "baxter"],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--param-file", controllers_yaml],
        output="screen",
    )

    left_arm_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_arm_controller", "--param-file", controllers_yaml],
        output="screen",
    )

    right_arm_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_arm_controller", "--param-file", controllers_yaml],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("headless", default_value="true"),
            OpaqueFunction(function=launch_gazebo),
            clock_bridge,
            robot_state_publisher,
            spawn,
            RegisterEventHandler(
                OnProcessExit(
                    target_action=spawn,
                    on_exit=[joint_state_broadcaster_spawner],
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=joint_state_broadcaster_spawner,
                    on_exit=[left_arm_spawner, right_arm_spawner],
                )
            ),
        ]
    )
