from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="baxter_examples",
                executable="sim_tiny_trajectory",
                name="sim_tiny_trajectory",
                output="screen",
                parameters=[{"use_sim_time": True}],
            ),
        ]
    )
