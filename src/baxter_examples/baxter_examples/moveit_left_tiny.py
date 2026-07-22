#!/usr/bin/env python3

import math
import time
from typing import Dict, List, Optional

import rclpy
from rcl_interfaces.msg import ParameterType
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter_client import AsyncParameterClient
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import JointState


LEFT_JOINTS = [
    "left_s0",
    "left_s1",
    "left_e0",
    "left_e1",
    "left_w0",
    "left_w1",
    "left_w2",
]
RIGHT_JOINTS = [
    "right_s0",
    "right_s1",
    "right_e0",
    "right_e1",
    "right_w0",
    "right_w1",
    "right_w2",
]
GROUP_JOINTS = {
    "left_arm": LEFT_JOINTS,
    "right_arm": RIGHT_JOINTS,
    "both_arms": LEFT_JOINTS + RIGHT_JOINTS,
}
GROUP_MOTION_JOINTS = {
    "left_arm": ["left_s1"],
    "right_arm": ["right_s1"],
    "both_arms": ["left_s1", "right_s1"],
}
JOINT_LIMIT = (-2.147, 1.047)
JOINT_DELTA_RAD = 0.25
JOINT_LIMIT_MARGIN_RAD = 0.05
FINAL_TOLERANCE_RAD = 0.02


def positions_for_joints(joint_state: JointState, joint_names: List[str]) -> Dict[str, float]:
    positions = dict(zip(joint_state.name, joint_state.position))
    missing = [joint for joint in joint_names if joint not in positions]
    if missing:
        raise RuntimeError(f"Missing joints in /joint_states: {missing}")
    if not all(math.isfinite(positions[joint]) for joint in joint_names):
        raise RuntimeError(f"Non-finite positions in /joint_states for {joint_names}")
    return {joint: positions[joint] for joint in joint_names}


def choose_reversible_target(start: float) -> float:
    lower, upper = JOINT_LIMIT
    if not lower <= start <= upper:
        raise RuntimeError(f"s1 start {start:.3f} rad is outside [{lower}, {upper}]")
    if start + JOINT_DELTA_RAD <= upper - JOINT_LIMIT_MARGIN_RAD:
        return start + JOINT_DELTA_RAD
    if start - JOINT_DELTA_RAD >= lower + JOINT_LIMIT_MARGIN_RAD:
        return start - JOINT_DELTA_RAD
    raise RuntimeError(f"No safe reversible s1 target from {start:.3f} rad")


class MoveItTiny(Node):
    def __init__(self) -> None:
        super().__init__("moveit_tiny")
        self.declare_parameter("group", "left_arm")
        self.declare_parameter("cancel_after_sec", 0.0)
        self._group = self.get_parameter("group").value
        self._cancel_after_sec = self.get_parameter("cancel_after_sec").value
        if self._group not in GROUP_JOINTS:
            raise RuntimeError(
                f"Unsupported group {self._group!r}; choose from {sorted(GROUP_JOINTS)}"
            )
        self._joint_state: Optional[JointState] = None
        self._joint_state_sequence = 0
        self._active_goal = None
        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 1)
        self._client = ActionClient(self, MoveGroup, "/move_action")

    def _joint_state_cb(self, msg: JointState) -> None:
        self._joint_state = msg
        self._joint_state_sequence += 1

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

    def wait_for_fresh_joint_state(
        self, joint_names: List[str], after_sequence: Optional[int] = None, timeout_sec: float = 10.0
    ) -> JointState:
        if after_sequence is None:
            after_sequence = self._joint_state_sequence
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok():
            if self._joint_state_sequence > after_sequence and self._joint_state is not None:
                positions_for_joints(self._joint_state, joint_names)
                return self._joint_state
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Timed out waiting for a fresh /joint_states sample")
            rclpy.spin_once(self, timeout_sec=min(0.1, remaining))
        raise RuntimeError("ROS shut down while waiting for /joint_states")

    def _cancel_active_goal(self) -> bool:
        if self._active_goal is None:
            return False
        cancel_future = self._active_goal.cancel_goal_async()
        response = self._wait_for_future(cancel_future, 5.0, "MoveGroup cancellation")
        if not response.goals_canceling:
            raise RuntimeError("MoveGroup did not accept goal cancellation")
        self.get_logger().info("MoveGroup goal canceled; controllers are holding position")
        self._active_goal = None
        return True

    def _check_hold(self, joint_names: List[str]) -> None:
        first = self.wait_for_fresh_joint_state(joint_names)
        first_positions = positions_for_joints(first, joint_names)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        second = self.wait_for_fresh_joint_state(joint_names)
        second_positions = positions_for_joints(second, joint_names)
        drift = max(
            abs(second_positions[joint] - first_positions[joint]) for joint in joint_names
        )
        if drift > FINAL_TOLERANCE_RAD:
            raise RuntimeError(f"Canceled MoveGroup goal did not hold: drift={drift:.4f} rad")
        self.get_logger().info(f"Cancellation hold verified: max_drift={drift:.4f} rad")

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

    def send_goal(
        self,
        joint_names: List[str],
        start_positions: Dict[str, float],
        target_positions: Dict[str, float],
        label: str,
    ) -> bool:
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
        constraints.name = f"{self._group}_{label}"
        for joint in joint_names:
            constraint = JointConstraint()
            constraint.joint_name = joint
            constraint.position = target_positions[joint]
            constraint.tolerance_above = 0.01
            constraint.tolerance_below = 0.01
            constraint.weight = 1.0
            constraints.joint_constraints.append(constraint)
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False
        goal.planning_options.planning_scene_diff.is_diff = True

        changes = ", ".join(
            f"{joint} {start_positions[joint]:.3f}->{target_positions[joint]:.3f}"
            for joint in GROUP_MOTION_JOINTS[self._group]
        )
        self.get_logger().info(f"MoveIt {self._group} {label}: {changes} rad")

        send_future = self._client.send_goal_async(goal)
        goal_handle = self._wait_for_future(send_future, 5.0, "MoveGroup goal response")
        if not goal_handle.accepted:
            raise RuntimeError("MoveGroup goal rejected")

        self._active_goal = goal_handle
        result_future = goal_handle.get_result_async()
        result_started = time.monotonic()
        try:
            while rclpy.ok() and not result_future.done():
                if self._cancel_after_sec > 0 and time.monotonic() - result_started >= self._cancel_after_sec:
                    self._cancel_active_goal()
                    self._check_hold(joint_names)
                    return False
                if time.monotonic() - result_started >= 120.0:
                    raise RuntimeError("Timed out waiting for MoveGroup result")
                rclpy.spin_once(self, timeout_sec=0.1)
            if not result_future.done():
                raise RuntimeError("ROS shut down while waiting for MoveGroup result")
            result = result_future.result().result
        except BaseException:
            self._cancel_active_goal()
            raise
        finally:
            self._active_goal = None

        if result.error_code.val != 1:
            raise RuntimeError(f"MoveGroup failed with error code {result.error_code.val}")

        sequence = self._joint_state_sequence
        final_state = self.wait_for_fresh_joint_state(joint_names, after_sequence=sequence)
        actual_positions = positions_for_joints(final_state, joint_names)
        error = max(
            abs(actual_positions[joint] - target_positions[joint]) for joint in joint_names
        )
        if error > FINAL_TOLERANCE_RAD:
            raise RuntimeError(f"MoveIt {label} final error {error:.4f} rad exceeds 0.02 rad")
        points = len(result.planned_trajectory.joint_trajectory.points)
        self.get_logger().info(
            f"MoveIt {self._group} {label} verified: points={points}, max_error={error:.4f} rad"
        )
        return True

    def run(self) -> None:
        self._require_sim_move_group()
        joint_names = GROUP_JOINTS[self._group]
        start_state = self.wait_for_fresh_joint_state(joint_names)
        start_positions = positions_for_joints(start_state, joint_names)
        target_positions = start_positions.copy()
        for joint in GROUP_MOTION_JOINTS[self._group]:
            target_positions[joint] = choose_reversible_target(start_positions[joint])
        if not self.send_goal(joint_names, start_positions, target_positions, "outbound"):
            return

        return_state = self.wait_for_fresh_joint_state(joint_names)
        return_positions = positions_for_joints(return_state, joint_names)
        if not self.send_goal(joint_names, return_positions, start_positions, "return"):
            return
        self.get_logger().info(f"MoveIt {self._group} reversible plan+execute passed")


def main() -> None:
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = MoveItTiny()
    exit_code = 0
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().warning("Interrupted; canceling the active MoveGroup goal")
        try:
            node._cancel_active_goal()
        except RuntimeError as error:
            node.get_logger().error(str(error))
            exit_code = 1
    except Exception as error:
        node.get_logger().error(str(error))
        try:
            node._cancel_active_goal()
        except RuntimeError as cancel_error:
            node.get_logger().error(str(cancel_error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
