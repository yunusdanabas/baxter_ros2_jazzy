#!/usr/bin/env python3

import math
import time
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import Pose, TransformStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint
from rcl_interfaces.msg import ParameterType
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter_client import AsyncParameterClient
from rclpy.signals import SignalHandlerOptions
from shape_msgs.msg import SolidPrimitive
from tf2_ros import Buffer, TransformListener


GROUP_TIP = {
    "left_arm": "left_gripper",
    "right_arm": "right_gripper",
}
POSITION_TOLERANCE_M = 0.03


def _parameter_is_unset(node: Node, name: str) -> bool:
    # ponytail: get_parameter() raises ParameterUninitializedException on a declared-but-
    # unset statically typed parameter; get_parameter_or() returns NOT_SET instead.
    return node.get_parameter_or(name).value is None


class MoveItPose(Node):
    def __init__(self) -> None:
        super().__init__("moveit_pose")
        self.declare_parameter("group", "left_arm")
        self.declare_parameter("frame", "torso")
        self.declare_parameter("x", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("y", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("z", rclpy.Parameter.Type.DOUBLE)
        self.declare_parameter("delta_x", 0.0)
        self.declare_parameter("delta_y", 0.0)
        self.declare_parameter("delta_z", 0.0)
        self.declare_parameter("position_tolerance", POSITION_TOLERANCE_M)
        self.declare_parameter("plan_only", False)

        self._group = self.get_parameter("group").value
        if self._group not in GROUP_TIP:
            raise RuntimeError(
                f"Unsupported group {self._group!r}; choose from {sorted(GROUP_TIP)}"
            )

        self._frame = self.get_parameter("frame").value
        self._tip_link = GROUP_TIP[self._group]
        self._position_tolerance = self.get_parameter("position_tolerance").value
        self._plan_only = self.get_parameter("plan_only").value

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._client = ActionClient(self, MoveGroup, "/move_action")

    def _wait_for_future(self, future, timeout_sec: float, description: str):
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and not future.done():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(f"Timed out waiting for {description}")
            rclpy.spin_once(self, timeout_sec=min(0.1, remaining))
        if not future.done():
            raise RuntimeError(f"ROS shut down while waiting for {description}")
        return future.result()

    def _require_sim_move_group(self) -> None:
        client = AsyncParameterClient(self, "/move_group")
        if not client.wait_for_services(timeout_sec=15.0):
            raise RuntimeError("MoveGroup parameter service not available")
        response = self._wait_for_future(
            client.get_parameters(["use_sim_time"]), 15.0, "MoveGroup use_sim_time"
        )
        value = response.values[0]
        if value.type != ParameterType.PARAMETER_BOOL or not value.bool_value:
            raise RuntimeError("Refusing motion: /move_group is not using simulation time")

    def _lookup_tip_pose(self) -> Tuple[float, float, float]:
        deadline = time.monotonic() + 10.0
        while rclpy.ok():
            try:
                transform: TransformStamped = self._tf_buffer.lookup_transform(
                    self._frame,
                    self._tip_link,
                    rclpy.time.Time(),
                )
                position = transform.transform.translation
                return position.x, position.y, position.z
            except Exception:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError(
                        f"Could not look up transform {self._frame} -> {self._tip_link}"
                    )
                rclpy.spin_once(self, timeout_sec=min(0.1, remaining))
        raise RuntimeError("ROS shut down while waiting for TF")

    def _resolve_target(self) -> Tuple[float, float, float]:
        use_absolute = not (
            _parameter_is_unset(self, "x")
            or _parameter_is_unset(self, "y")
            or _parameter_is_unset(self, "z")
        )
        delta_x = self.get_parameter("delta_x").value
        delta_y = self.get_parameter("delta_y").value
        delta_z = self.get_parameter("delta_z").value
        has_delta = any(abs(value) > 1e-9 for value in (delta_x, delta_y, delta_z))

        current_x, current_y, current_z = self._lookup_tip_pose()
        self.get_logger().info(
            f"Current {self._tip_link} in {self._frame}: "
            f"x={current_x:.3f}, y={current_y:.3f}, z={current_z:.3f}"
        )

        if use_absolute and has_delta:
            raise RuntimeError("Set either absolute x/y/z or delta_x/delta_y/delta_z, not both")

        if use_absolute:
            return (
                self.get_parameter("x").value,
                self.get_parameter("y").value,
                self.get_parameter("z").value,
            )

        if has_delta:
            return current_x + delta_x, current_y + delta_y, current_z + delta_z

        raise RuntimeError(
            "No target specified. Pass absolute coordinates, for example:\n"
            "  ros2 run baxter_examples moveit_pose --ros-args "
            "-p group:=left_arm -p x:=0.55 -p y:=0.25 -p z:=0.15\n"
            "or a relative nudge:\n"
            "  ros2 run baxter_examples moveit_pose --ros-args "
            "-p group:=left_arm -p delta_z:=0.05"
        )

    def _make_position_constraint(self, x: float, y: float, z: float) -> PositionConstraint:
        constraint = PositionConstraint()
        constraint.header.frame_id = self._frame
        constraint.link_name = self._tip_link
        constraint.target_point_offset.x = 0.0
        constraint.target_point_offset.y = 0.0
        constraint.target_point_offset.z = 0.0

        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [self._position_tolerance]

        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.w = 1.0

        constraint.constraint_region.primitives.append(sphere)
        constraint.constraint_region.primitive_poses.append(pose)
        constraint.weight = 1.0
        return constraint

    def run(self) -> None:
        self._require_sim_move_group()
        target_x, target_y, target_z = self._resolve_target()
        self.get_logger().info(
            f"MoveIt {self._group} IK target in {self._frame}: "
            f"x={target_x:.3f}, y={target_y:.3f}, z={target_z:.3f}"
        )

        if not self._client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError("MoveGroup action server not available: /move_action")

        goal = MoveGroup.Goal()
        goal.request.group_name = self._group
        goal.request.pipeline_id = "ompl"
        goal.request.planner_id = "RRTConnectkConfigDefault"
        goal.request.allowed_planning_time = 10.0
        goal.request.num_planning_attempts = 5
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2
        goal.request.workspace_parameters.header.frame_id = "world"
        goal.request.workspace_parameters.min_corner.x = -2.0
        goal.request.workspace_parameters.min_corner.y = -2.0
        goal.request.workspace_parameters.min_corner.z = 0.0
        goal.request.workspace_parameters.max_corner.x = 2.0
        goal.request.workspace_parameters.max_corner.y = 2.0
        goal.request.workspace_parameters.max_corner.z = 3.0

        constraints = Constraints()
        constraints.name = f"{self._group}_pose_goal"
        constraints.position_constraints.append(
            self._make_position_constraint(target_x, target_y, target_z)
        )
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = self._plan_only
        goal.planning_options.planning_scene_diff.is_diff = True

        send_future = self._client.send_goal_async(goal)
        goal_handle = self._wait_for_future(send_future, 5.0, "MoveGroup goal response")
        if not goal_handle.accepted:
            raise RuntimeError("MoveGroup goal rejected")

        result_future = goal_handle.get_result_async()
        deadline = time.monotonic() + 120.0
        while rclpy.ok() and not result_future.done():
            if time.monotonic() >= deadline:
                raise RuntimeError("Timed out waiting for MoveGroup result")
            rclpy.spin_once(self, timeout_sec=0.1)
        if not result_future.done():
            raise RuntimeError("ROS shut down while waiting for MoveGroup result")

        result = result_future.result().result
        if result.error_code.val != 1:
            raise RuntimeError(f"MoveGroup failed with error code {result.error_code.val}")

        final_x, final_y, final_z = self._lookup_tip_pose()
        error = math.sqrt(
            (final_x - target_x) ** 2
            + (final_y - target_y) ** 2
            + (final_z - target_z) ** 2
        )
        if error > self._position_tolerance * 2.0:
            raise RuntimeError(
                f"Tip position error {error:.4f} m exceeds {self._position_tolerance * 2.0:.4f} m"
            )

        points = len(result.planned_trajectory.joint_trajectory.points)
        self.get_logger().info(
            f"MoveIt {self._group} pose goal reached: points={points}, position_error={error:.4f} m"
        )


def main() -> None:
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = MoveItPose()
    exit_code = 0
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().warning("Interrupted")
        exit_code = 1
    except Exception as error:
        node.get_logger().error(str(error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
