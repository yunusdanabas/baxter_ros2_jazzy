"""Shared helpers for the example smoke clients.

What is deliberately NOT here: `wait_for_fresh_joint_state` and the joint-state
callback. They look duplicated but are not. `sim_tiny_trajectory` merges a
name->position view across messages and tolerates that view being incomplete,
because Baxter publishes `/robot/joint_states` from two nodes and roughly a
third of messages carry no arm joints at all (I20 F-C). `moveit_left_tiny` is
sim-only by construction, where one publisher sends everything and keeping the
last message is correct. Unifying them would quietly undo the F-C fix.
"""

from __future__ import annotations

import math
import time
from typing import Dict, List

import rclpy
from rcl_interfaces.msg import ParameterType
from rclpy.parameter_client import AsyncParameterClient
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

DEFAULT_MOTION_JOINT = "s1"
JOINT_DELTA_RAD = 0.35
JOINT_LIMIT_MARGIN_RAD = 0.05

# Position limits per joint suffix, from the URDF. The action shim keeps its own
# copy and rejects any out-of-limit point; this only picks a reversible target.
JOINT_LIMITS = {
    "s0": (-1.70167993878, 1.70167993878),
    "s1": (-2.147, 1.047),
    "e0": (-3.05417993878, 3.05417993878),
    "e1": (-0.05, 2.618),
    "w0": (-3.059, 3.059),
    "w1": (-1.57079632679, 2.094),
    "w2": (-3.059, 3.059),
}


def wait_for_future(node, future, timeout_sec: float, description: str):
    """Spin `node` until `future` resolves, or raise with what was waited on."""
    deadline = time.monotonic() + timeout_sec
    while rclpy.ok() and not future.done():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(f"Timed out waiting for {description}")
        rclpy.spin_once(node, timeout_sec=min(0.1, remaining))
    if not future.done():
        raise RuntimeError(f"ROS shut down while waiting for {description}")
    return future.result()


def cancel_active_goal(node, goal_handle, server_label: str) -> bool:
    """Cancel `goal_handle` and confirm the server accepted it.

    `server_label` names the server in every message ("Controller" /
    "MoveGroup") — the only thing that differed between the three copies.
    """
    if goal_handle is None:
        return False
    cancel_future = goal_handle.cancel_goal_async()
    response = wait_for_future(
        node, cancel_future, 5.0, f"{server_label} goal cancellation"
    )
    if not response.goals_canceling:
        raise RuntimeError(f"{server_label} did not accept goal cancellation")
    node.get_logger().info(
        f"{server_label} goal canceled; holding position"
    )
    return True


def require_sim_move_group(node) -> None:
    """Refuse to command a `/move_group` that is not using simulation time."""
    client = AsyncParameterClient(node, "/move_group")
    if not client.wait_for_services(timeout_sec=15.0):
        raise RuntimeError("MoveGroup parameter service not available")
    response = wait_for_future(
        node, client.get_parameters(["use_sim_time"]), 15.0, "MoveGroup use_sim_time"
    )
    value = response.values[0]
    if value.type != ParameterType.PARAMETER_BOOL or not value.bool_value:
        raise RuntimeError("Refusing motion: /move_group is not using simulation time")


def positions_for_joints_list(
    joint_state: JointState, joint_names: List[str]
) -> List[float]:
    name_to_position = dict(zip(joint_state.name, joint_state.position))
    missing = [name for name in joint_names if name not in name_to_position]
    if missing:
        raise RuntimeError(f"Missing joints in /joint_states: {missing}")
    positions = [name_to_position[name] for name in joint_names]
    if not all(math.isfinite(position) for position in positions):
        raise RuntimeError(f"Non-finite positions in /joint_states for {joint_names}")
    return positions


def positions_for_joints_dict(
    joint_state: JointState, joint_names: List[str]
) -> Dict[str, float]:
    name_to_position = dict(zip(joint_state.name, joint_state.position))
    missing = [name for name in joint_names if name not in name_to_position]
    if missing:
        raise RuntimeError(f"Missing joints in /joint_states: {missing}")
    if not all(math.isfinite(name_to_position[name]) for name in joint_names):
        raise RuntimeError(f"Non-finite positions in /joint_states for {joint_names}")
    return {name: name_to_position[name] for name in joint_names}


def choose_reversible_target(
    start: float,
    delta: float = JOINT_DELTA_RAD,
    joint: str = DEFAULT_MOTION_JOINT,
) -> float:
    try:
        lower, upper = JOINT_LIMITS[joint]
    except KeyError as exc:
        raise RuntimeError(
            f"Unknown joint '{joint}'; expected one of {sorted(JOINT_LIMITS)}"
        ) from exc
    if not lower <= start <= upper:
        raise RuntimeError(
            f"{joint} start {start:.3f} rad is outside [{lower}, {upper}]"
        )
    if start + delta <= upper - JOINT_LIMIT_MARGIN_RAD:
        return start + delta
    if start - delta >= lower + JOINT_LIMIT_MARGIN_RAD:
        return start - delta
    raise RuntimeError(
        f"No safe reversible {joint} target {delta:.3f} rad from {start:.3f} rad"
    )
