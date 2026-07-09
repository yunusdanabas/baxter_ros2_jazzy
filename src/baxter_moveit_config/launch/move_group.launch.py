from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
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

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            Node(
                package="moveit_ros_move_group",
                executable="move_group",
                output="screen",
                parameters=[moveit_config.to_dict(), {"use_sim_time": use_sim_time}],
            ),
        ]
    )
