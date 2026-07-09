from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    baxter_xacro = PathJoinSubstitution(
        [FindPackageShare("baxter_bringup"), "urdf", "baxter_description.urdf.xacro"]
    )

    robot_description = ParameterValue(
        Command(
            [
                FindExecutable(name="xacro"),
                " ",
                baxter_xacro,
                " pedestal:=",
                LaunchConfiguration("pedestal"),
                " gazebo:=",
                LaunchConfiguration("gazebo"),
            ]
        ),
        value_type=str,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("pedestal", default_value="true"),
            DeclareLaunchArgument("gazebo", default_value="false"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
        ]
    )
