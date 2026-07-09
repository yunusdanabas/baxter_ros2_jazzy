from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    headless = LaunchConfiguration("headless")
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

    return LaunchDescription(
        [
            DeclareLaunchArgument("headless", default_value="true"),
            sim_launch,
            TimerAction(period=8.0, actions=[move_group]),
        ]
    )
