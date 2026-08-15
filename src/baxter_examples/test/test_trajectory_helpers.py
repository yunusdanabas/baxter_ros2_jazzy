"""Checks for the pure logic in trajectory_helpers.

Only the functions that decide *what to command* are covered here. The ROS
plumbing (`wait_for_future`, `cancel_active_goal`, `require_sim_move_group`)
needs a live node and action server, so the sim smoke in
`docs/sim_test_commands.md` is what exercises it.
"""

import math

import pytest
from sensor_msgs.msg import JointState

from baxter_examples.trajectory_helpers import (
    JOINT_LIMITS,
    choose_reversible_target,
    positions_for_joints_dict,
    positions_for_joints_list,
)

# s1 is the default motion joint and the asymmetric one: (-2.147, 1.047).
# Asymmetry is what makes the negative-direction fallback reachable at all.
S1_LOWER, S1_UPPER = JOINT_LIMITS["s1"]


def joint_state(names, positions):
    message = JointState()
    message.name = list(names)
    message.position = list(positions)
    return message


def test_moves_positive_when_the_target_fits():
    assert choose_reversible_target(0.0, delta=0.35, joint="s1") == pytest.approx(0.35)


def test_falls_back_to_negative_near_the_upper_limit():
    # 0.9 + 0.35 overshoots the 0.05 rad margin below 1.047, so it must reverse.
    assert choose_reversible_target(0.9, delta=0.35, joint="s1") == pytest.approx(0.55)


def test_reverses_rather_than_stopping_inside_the_margin():
    # The decisive case for the margin, and the only one that is: 0.68 + 0.35
    # = 1.03 rad is a *legal* s1 position, but it sits 0.017 rad short of the
    # limit — inside the 0.05 rad margin — so it must reverse instead. Starts
    # further from the limit pass whether or not the margin exists.
    start = 0.68
    assert start + 0.35 < S1_UPPER, "this start must be legal, or it tests nothing"
    assert choose_reversible_target(start, delta=0.35, joint="s1") == pytest.approx(0.33)


def test_keeps_the_margin_on_both_sides():
    for start in (0.0, 0.68, 0.9, -2.0, S1_LOWER, S1_UPPER):
        target = choose_reversible_target(start, delta=0.35, joint="s1")
        assert S1_LOWER + 0.05 <= target <= S1_UPPER - 0.05


def test_rejects_a_delta_that_fits_in_neither_direction():
    # 2.2 rad overshoots the margin above and below on a 3.194 rad joint.
    with pytest.raises(RuntimeError, match="No safe reversible"):
        choose_reversible_target(0.0, delta=2.2, joint="s1")


def test_rejects_a_start_outside_the_joint_limits():
    with pytest.raises(RuntimeError, match="outside"):
        choose_reversible_target(S1_UPPER + 0.1, joint="s1")


def test_rejects_an_unknown_joint():
    with pytest.raises(RuntimeError, match="Unknown joint"):
        choose_reversible_target(0.0, joint="elbow")


@pytest.mark.parametrize("read", [positions_for_joints_list, positions_for_joints_dict])
def test_reports_which_joints_are_missing(read):
    # Baxter publishes /robot/joint_states from two nodes and some messages
    # carry no arm joints at all (I20 F-C), so a partial view is normal input.
    with pytest.raises(RuntimeError, match="left_s1"):
        read(joint_state(["left_s0"], [0.0]), ["left_s0", "left_s1"])


@pytest.mark.parametrize("read", [positions_for_joints_list, positions_for_joints_dict])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_positions(read, bad):
    with pytest.raises(RuntimeError, match="Non-finite"):
        read(joint_state(["left_s0", "left_s1"], [0.0, bad]), ["left_s0", "left_s1"])


def test_reads_the_requested_joints_in_order():
    message = joint_state(["left_s1", "left_s0", "head_pan"], [0.2, 0.1, 0.3])
    assert positions_for_joints_list(message, ["left_s0", "left_s1"]) == [0.1, 0.2]
    assert positions_for_joints_dict(message, ["left_s0", "left_s1"]) == {
        "left_s0": 0.1,
        "left_s1": 0.2,
    }
