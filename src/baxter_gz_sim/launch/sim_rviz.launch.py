from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    headless = LaunchConfiguration("headless")
    return LaunchDescription(
        [
            DeclareLaunchArgument("headless", default_value="false"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare("baxter_gz_sim"), "launch", "sim.launch.py"]
                    )
                ),
                launch_arguments={"headless": headless}.items(),
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=[
                    "-d",
                    PathJoinSubstitution(
                        [FindPackageShare("baxter_gz_sim"), "config", "sim.rviz"]
                    ),
                ],
                parameters=[{"use_sim_time": True}],
                on_exit=[EmitEvent(event=Shutdown(reason="Simulation RViz exited"))],
            ),
        ]
    )
