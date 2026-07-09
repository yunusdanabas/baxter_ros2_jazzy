from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, IfElseSubstitution, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    headless = LaunchConfiguration("headless")
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

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={
            "gz_args": IfElseSubstitution(
                headless,
                if_value="-r -s empty.sdf",
                else_value="-r empty.sdf",
            )
        }.items(),
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
        arguments=["-topic", "/robot_description", "-name", "baxter", "-z", "2.0"],
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
            gazebo,
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
