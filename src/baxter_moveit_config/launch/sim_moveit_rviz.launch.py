from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    headless = LaunchConfiguration("headless")
    return LaunchDescription(
        [
            DeclareLaunchArgument("headless", default_value="false"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("baxter_moveit_config"),
                            "launch",
                            "sim_moveit.launch.py",
                        ]
                    )
                ),
                launch_arguments={"headless": headless, "rviz": "true"}.items(),
            ),
        ]
    )
