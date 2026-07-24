from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def _move_group(context, *_args, **_kwargs):
    # MoveItConfigsBuilder needs a concrete path, not a substitution, so the
    # controller profile is resolved here instead of at description build time.
    controllers = LaunchConfiguration("controllers").perform(context)
    joint_states_topic = LaunchConfiguration("joint_states_topic").perform(context)

    # ponytail: the Gazebo xacro is reused on hardware too -- its <ros2_control>
    # and world-link tags are inert for move_group, and it is the exact model the
    # SRDF and kinematics config were validated against.
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
            file_path=f"config/moveit_controllers_{controllers}.yaml",
            moveit_manage_controllers=False,
        )
        .planning_pipelines(default_planning_pipeline="ompl", pipelines=["ompl"])
        .to_moveit_configs()
    )

    return [
        Node(
            package="baxter_moveit_config",
            executable="baxter_move_group",
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "publish_robot_description_semantic": True,
                },
            ],
            remappings=[("joint_states", joint_states_topic)],
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            # sim -> Gazebo's controllers; hardware -> the bridge action shims.
            DeclareLaunchArgument(
                "controllers", default_value="sim", choices=["sim", "hardware"]
            ),
            # The hardware bridge publishes /robot/joint_states, not /joint_states.
            DeclareLaunchArgument("joint_states_topic", default_value="/joint_states"),
            OpaqueFunction(function=_move_group),
        ]
    )
