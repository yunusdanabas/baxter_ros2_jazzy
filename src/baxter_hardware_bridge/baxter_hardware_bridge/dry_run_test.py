#!/usr/bin/env python3
"""Dry-run self-test for the hardware action shim.

Launches mock_robot + follow_joint_trajectory_shim in-process under the same
MultiThreadedExecutor used by production main(), then verifies:
   1. Safe state: goal accepted, succeeds, and publishes feedback.
   2. Bad joint names: goal rejected.
   3. Unsafe state at accept: goal rejected.
   4. Mid-goal cancel: GoalStatus canceled, non-SUCCESSFUL error_code.
   5. Mid-goal unsafe: goal aborted with safety error, non-SUCCESSFUL code.
   6. Short point positions: goal rejected.
   7. First command continues from the measured pose, not from all-zeros.
   8. A second goal is rejected while one is executing.
   9. Zero-duration first point: goal rejected (would command in one step).
  10. Non-finite position: goal rejected.
  11. Non-monotonic time_from_start: goal rejected.
  12. Position outside the URDF joint limits: goal rejected.
  13. Segment faster than the URDF velocity limit: goal rejected.
  14. Stale /robot/joint_states with a live /robot/state: goal rejected.
  15. Per-cycle step clamp binds on an oversized command.
  16. Cancel holds by republishing, not by a single publish.
  17. Path tolerance does not trip when the arm follows normally.
  18. Path tolerance trips when it stops following, and the shim holds.
  19. A joint still moving at goal end fails the stopped-velocity check,
      and that abort holds too.
  20. A wrist segment inside the URDF limit but above what the per-cycle
      clamp can deliver is rejected at accept time.

Exit code 0 on pass, 1 on fail.
"""

import math
import threading
import time
from typing import List, Optional, Sequence, Tuple

import rclpy
from baxter_hardware_bridge.executor_util import make_shim_executor
from baxter_hardware_bridge.follow_joint_trajectory_shim import (
    RESULT_ABORTED,
    RESULT_CANCELED,
    FollowJointTrajectoryShim,
    LEFT_JOINTS,
)
from baxter_hardware_bridge.mock_robot import MockRobot
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectoryPoint


def make_goal(
    joints: Sequence[str], points: Sequence[Tuple[Sequence[float], float]]
) -> FollowJointTrajectory.Goal:
    """Build a goal from (positions, seconds_from_start) pairs."""
    goal = FollowJointTrajectory.Goal()
    goal.trajectory.joint_names = list(joints)
    for positions, seconds in points:
        point = JointTrajectoryPoint()
        point.positions = list(positions)
        point.time_from_start.sec = int(seconds)
        point.time_from_start.nanosec = int(abs(seconds - int(seconds)) * 1e9)
        goal.trajectory.points.append(point)
    return goal


def make_tiny_goal(
    joints: Sequence[str], offset: float = 0.1, duration_sec: float = 1.0
) -> FollowJointTrajectory.Goal:
    """A small well-formed move on the second joint, reached at duration_sec."""
    positions = [0.0] * len(joints)
    positions[1] = offset
    return make_goal(joints, [(positions, duration_sec)])


def wait_future(node, future, timeout_sec: float) -> bool:
    """Spin node until future completes or timeout."""
    deadline = time.monotonic() + timeout_sec
    while not future.done() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
    return future.done()


def expect_reject(node, client, goal, label: str, results: List[str]) -> None:
    """Send a goal that must be rejected at accept time."""
    future = client.send_goal_async(goal)
    if not wait_future(node, future, 5.0):
        results.append(f"FAIL: {label} goal response timeout")
        return
    handle = future.result()
    if handle.accepted:
        handle.cancel_goal_async()
        results.append(f"FAIL: {label} accepted (expected reject)")
    else:
        results.append(f"PASS: {label} rejected")


def send_and_wait(node, client, goal, label: str, results: List[str]):
    """Send a goal that must be accepted; return its result, or None on failure."""
    future = client.send_goal_async(goal)
    if not wait_future(node, future, 5.0):
        results.append(f"FAIL: {label} goal response timeout")
        return None
    handle = future.result()
    if not handle.accepted:
        results.append(f"FAIL: {label} goal rejected (expected accept)")
        return None
    result_future = handle.get_result_async()
    if not wait_future(node, result_future, 15.0):
        results.append(f"FAIL: {label} result timeout")
        return None
    return result_future.result().result


def run_test() -> bool:
    rclpy.init()
    executor = make_shim_executor()
    mock: Optional[MockRobot] = None
    shim: Optional[FollowJointTrajectoryShim] = None
    test_node = None
    spin_thread: Optional[threading.Thread] = None
    results: List[str] = []

    try:
        mock = MockRobot()
        shim = FollowJointTrajectoryShim()
        # Override mock_mode so we don't publish to real robot topics
        shim._mock_mode = True

        executor.add_node(mock)
        executor.add_node(shim)

        spin_thread = threading.Thread(target=executor.spin, daemon=True)
        spin_thread.start()

        test_node = rclpy.create_node("dry_run_test")
        client = ActionClient(
            test_node, FollowJointTrajectory, "/robot/limb/left/follow_joint_trajectory"
        )

        for _ in range(100):
            if client.wait_for_server(timeout_sec=0.1):
                break
        else:
            test_node.get_logger().error("FAIL: action server not available")
            results.append("FAIL: action server not available")
            return False

        # --- Test 1: safe state, correct joints -> accept, succeed, feedback ---
        test_node.get_logger().info("Test 1: safe state, correct joints")
        feedback_count = 0

        def on_feedback(_msg) -> None:
            nonlocal feedback_count
            feedback_count += 1

        goal_future = client.send_goal_async(
            make_tiny_goal(LEFT_JOINTS), feedback_callback=on_feedback
        )
        if not wait_future(test_node, goal_future, 5.0):
            results.append("FAIL: Test 1 goal response timeout")
        else:
            gh = goal_future.result()
            if not gh.accepted:
                results.append("FAIL: Test 1 goal rejected (expected accept)")
            else:
                result_future = gh.get_result_async()
                if not wait_future(test_node, result_future, 10.0):
                    results.append("FAIL: Test 1 result timeout")
                else:
                    result = result_future.result().result
                    if result.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
                        results.append(
                            f"FAIL: Test 1 error_code={result.error_code} {result.error_string}"
                        )
                    elif feedback_count == 0:
                        results.append("FAIL: Test 1 goal succeeded but published no feedback")
                    else:
                        results.append(
                            f"PASS: Test 1 goal succeeded, {feedback_count} feedback messages"
                        )

        # --- Test 2: bad joint names -> reject ---
        test_node.get_logger().info("Test 2: bad joint names")
        bad_joints = [
            "foo_s0", "foo_s1", "foo_e0", "foo_e1", "foo_w0", "foo_w1", "foo_w2",
        ]
        expect_reject(
            test_node, client, make_tiny_goal(bad_joints), "Test 2 bad joints", results
        )

        # --- Test 3: unsafe state at accept -> reject ---
        test_node.get_logger().info("Test 3: unsafe state")
        mock._unsafe = True
        time.sleep(1.0)
        expect_reject(
            test_node, client, make_tiny_goal(LEFT_JOINTS), "Test 3 unsafe state", results
        )
        mock._unsafe = False
        time.sleep(0.5)

        # --- Test 4: mid-goal cancel ---
        test_node.get_logger().info("Test 4: mid-goal cancel")
        goal_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS, duration_sec=3))
        if not wait_future(test_node, goal_future, 5.0):
            results.append("FAIL: Test 4 goal response timeout")
        else:
            gh = goal_future.result()
            if not gh.accepted:
                results.append("FAIL: Test 4 goal rejected (expected accept)")
            else:
                time.sleep(0.4)
                cancel_future = gh.cancel_goal_async()
                wait_future(test_node, cancel_future, 5.0)
                result_future = gh.get_result_async()
                if not wait_future(test_node, result_future, 10.0):
                    results.append("FAIL: Test 4 result timeout")
                else:
                    wrapped = result_future.result()
                    result = wrapped.result
                    status = wrapped.status
                    # GoalStatus.STATUS_CANCELED == 5
                    if status == 5 and result.error_code == RESULT_CANCELED:
                        results.append("PASS: Test 4 mid-goal cancel")
                    else:
                        results.append(
                            f"FAIL: Test 4 status={status} error_code={result.error_code} "
                            f"{result.error_string}"
                        )

        # --- Test 5: mid-goal unsafe abort ---
        test_node.get_logger().info("Test 5: mid-goal unsafe abort")
        goal_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS, duration_sec=3))
        if not wait_future(test_node, goal_future, 5.0):
            results.append("FAIL: Test 5 goal response timeout")
        else:
            gh = goal_future.result()
            if not gh.accepted:
                results.append("FAIL: Test 5 goal rejected (expected accept)")
            else:
                time.sleep(0.3)
                mock._unsafe = True
                result_future = gh.get_result_async()
                if not wait_future(test_node, result_future, 10.0):
                    results.append("FAIL: Test 5 result timeout")
                else:
                    result = result_future.result().result
                    if (
                        result.error_code == RESULT_ABORTED
                        and "Safety violation" in result.error_string
                    ):
                        results.append("PASS: Test 5 mid-goal unsafe abort")
                    else:
                        results.append(
                            f"FAIL: Test 5 error_code={result.error_code} "
                            f"{result.error_string}"
                        )
        mock._unsafe = False
        time.sleep(0.3)

        # --- Test 6: short positions -> reject ---
        test_node.get_logger().info("Test 6: short point positions")
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [([0.0, 0.0], 1.0)]),
            "Test 6 short positions",
            results,
        )

        # --- Test 7: first command continues from measured pose, no lurch ---
        # Commanding the arm to stay exactly where it is: every command must
        # stay on that pose. If the shim seeded from all-zeros instead of the
        # encoders, it would ramp away from it and this fails.
        test_node.get_logger().info("Test 7: no lurch from stale command state")
        measured = list(shim._latest_positions)
        goal_future = client.send_goal_async(make_goal(LEFT_JOINTS, [(measured, 2.0)]))
        if not wait_future(test_node, goal_future, 5.0):
            results.append("FAIL: Test 7 goal response timeout")
        else:
            gh = goal_future.result()
            if not gh.accepted:
                results.append("FAIL: Test 7 goal rejected (expected accept)")
            else:
                time.sleep(0.3)
                commanded = list(shim._last_commanded)
                gh.cancel_goal_async()
                wait_future(test_node, gh.get_result_async(), 10.0)
                jump = max(abs(a - b) for a, b in zip(commanded, measured))
                if jump < 0.01:
                    results.append(f"PASS: Test 7 no lurch (max deviation {jump:.4f} rad)")
                else:
                    results.append(
                        f"FAIL: Test 7 commanded {jump:.4f} rad away from measured pose"
                    )
        time.sleep(0.3)

        # --- Test 8: second goal rejected while one is executing ---
        test_node.get_logger().info("Test 8: concurrent goal rejected")
        first_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS, duration_sec=3))
        if not wait_future(test_node, first_future, 5.0):
            results.append("FAIL: Test 8 first goal response timeout")
        else:
            first_gh = first_future.result()
            if not first_gh.accepted:
                results.append("FAIL: Test 8 first goal rejected (expected accept)")
            else:
                expect_reject(
                    test_node,
                    client,
                    make_tiny_goal(LEFT_JOINTS, duration_sec=3),
                    "Test 8 concurrent goal",
                    results,
                )
                cancel_future = first_gh.cancel_goal_async()
                wait_future(test_node, cancel_future, 5.0)
                wait_future(test_node, first_gh.get_result_async(), 10.0)
        time.sleep(0.3)

        # --- Tests 9-13: malformed goals rejected at accept time ---
        # Each is a shape the shim used to accept and command straight through.
        measured = list(shim._latest_positions)

        test_node.get_logger().info("Test 9: zero-duration first point")
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [([0.0] * 7, 0.0)]),
            "Test 9 zero-duration point",
            results,
        )

        test_node.get_logger().info("Test 10: non-finite position")
        nan_positions = list(measured)
        nan_positions[0] = math.nan
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(nan_positions, 2.0)]),
            "Test 10 NaN position",
            results,
        )

        test_node.get_logger().info("Test 11: non-monotonic time_from_start")
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(measured, 2.0), (measured, 1.0)]),
            "Test 11 non-monotonic time",
            results,
        )

        test_node.get_logger().info("Test 12: position outside joint limits")
        tucked = list(measured)
        tucked[1] = -2.175  # real tucked s1, just past the -2.147 lower limit
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(tucked, 5.0)]),
            "Test 12 out-of-limits position",
            results,
        )

        test_node.get_logger().info("Test 13: segment over the velocity limit")
        fast = list(measured)
        fast[0] = 1.5  # inside s0's +-1.7017 limit, but 1.5 rad in 0.1 s
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(fast, 0.1)]),
            "Test 13 over-velocity segment",
            results,
        )

        # --- Test 14: stale joint_states while /robot/state stays live ---
        # The partial-feed failure mode: py_bridge reconnects each ROS 1
        # subscription independently, so joint_states can stall while state flows.
        test_node.get_logger().info("Test 14: stale joint_states")
        shim._joint_states_stale_sec = 0.5
        mock.joint_states_enabled = False
        time.sleep(1.0)
        expect_reject(
            test_node,
            client,
            make_tiny_goal(LEFT_JOINTS),
            "Test 14 stale joint_states",
            results,
        )
        mock.joint_states_enabled = True
        shim._joint_states_stale_sec = 2.0
        time.sleep(0.3)

        # --- Test 15: per-cycle step clamp ---
        test_node.get_logger().info("Test 15: per-cycle step clamp")
        shim._last_commanded = [0.0] * len(LEFT_JOINTS)
        shim._publish_command([1.0] * len(LEFT_JOINTS))
        step = shim._max_step
        worst = max(abs(c - step) for c in shim._last_commanded)
        if worst < 1e-9:
            results.append(f"PASS: Test 15 clamp held command to {step} rad/cycle")
        else:
            results.append(
                f"FAIL: Test 15 clamp let a command through at {shim._last_commanded[0]:.4f} rad "
                f"(expected {step})"
            )

        # --- Test 16: cancel holds by republishing, not one publish ---
        test_node.get_logger().info("Test 16: cancel-hold republishes")
        publish_times: List[float] = []
        original_publish = shim._publish_command

        def counting_publish(positions):
            publish_times.append(time.monotonic())
            original_publish(positions)

        shim._publish_command = counting_publish
        try:
            goal_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS, duration_sec=3))
            if not wait_future(test_node, goal_future, 5.0):
                results.append("FAIL: Test 16 goal response timeout")
            else:
                gh = goal_future.result()
                if not gh.accepted:
                    results.append("FAIL: Test 16 goal rejected (expected accept)")
                else:
                    time.sleep(0.4)
                    cancel_at = time.monotonic()
                    gh.cancel_goal_async()
                    if not wait_future(test_node, gh.get_result_async(), 10.0):
                        results.append("FAIL: Test 16 result timeout")
                    else:
                        after_cancel = [t for t in publish_times if t > cancel_at]
                        # Was exactly 1 before the fix; the robot's own 0.2 s
                        # joint_command_timeout then expired and the arm floated.
                        if len(after_cancel) >= 10:
                            results.append(
                                f"PASS: Test 16 held with {len(after_cancel)} commands "
                                f"over {after_cancel[-1] - after_cancel[0]:.2f} s"
                            )
                        else:
                            results.append(
                                f"FAIL: Test 16 only {len(after_cancel)} commands after cancel"
                            )
        finally:
            shim._publish_command = original_publish

        # --- Tests 17-18: path tolerance ---
        # These need the loop closed, so the shim publishes for real and the
        # mock echoes back. Same topics a real shim would use, which is why
        # dry_run_test must not run alongside a live bridge.
        shim._mock_mode = False
        time.sleep(0.3)

        test_node.get_logger().info("Test 17: path tolerance quiet in normal operation")
        result = send_and_wait(
            test_node,
            client,
            make_tiny_goal(LEFT_JOINTS, duration_sec=2),
            "Test 17 closed-loop trajectory",
            results,
        )
        if result is not None:
            if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
                results.append("PASS: Test 17 tracked within path tolerance")
            else:
                results.append(
                    f"FAIL: Test 17 error_code={result.error_code} {result.error_string} "
                    f"(path_tolerance_rad={shim._path_tolerance} may be too tight)"
                )
        time.sleep(0.3)

        test_node.get_logger().info("Test 18: path tolerance trips when tracking stops")
        held_poses: List[Optional[List[float]]] = []
        original_hold = shim._hold_position

        def recording_hold(positions=None, duration=None):
            held_poses.append(None if positions is None else list(positions))
            original_hold(positions, duration)

        shim._hold_position = recording_hold
        mock.command_feedthrough = False
        try:
            target = list(shim._latest_positions)
            target[5] = target[5] + 1.0  # left_w1, limit [-1.571, 2.094]
            result = send_and_wait(
                test_node,
                client,
                make_goal(LEFT_JOINTS, [(target, 3.0)]),
                "Test 18 frozen arm",
                results,
            )
            if result is not None:
                expected = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
                if result.error_code != expected:
                    results.append(
                        f"FAIL: Test 18 error_code={result.error_code} "
                        f"(expected {expected}) {result.error_string}"
                    )
                elif not held_poses:
                    results.append(
                        "FAIL: Test 18 aborted without holding; the arm would sag "
                        "into gravity compensation"
                    )
                elif held_poses[0] is None:
                    # Holding _last_commanded would keep driving a blocked arm
                    # toward the very setpoint it just failed to reach.
                    results.append(
                        "FAIL: Test 18 held the commanded pose, not the measured one"
                    )
                else:
                    measured_gap = max(
                        abs(a - b)
                        for a, b in zip(held_poses[0], shim._latest_positions)
                    )
                    results.append(
                        f"PASS: Test 18 {result.error_string}, held measured pose "
                        f"(gap {measured_gap:.4f} rad)"
                    )
        finally:
            shim._hold_position = original_hold
            mock.command_feedthrough = True
            shim._mock_mode = True
        time.sleep(0.3)

        # --- Test 19: stopped-velocity check at goal end ---
        # The mock has no physics, so a still-moving arm has to be asserted.
        test_node.get_logger().info("Test 19: stopped-velocity check")
        mock.velocity = 0.5  # > stopped_velocity_tolerance (0.25)
        hold_calls = []
        original_hold = shim._hold_position

        def counting_hold(positions=None, duration=None):
            hold_calls.append(time.monotonic())
            original_hold(positions, duration)

        shim._hold_position = counting_hold
        time.sleep(0.3)
        try:
            result = send_and_wait(
                test_node,
                client,
                make_tiny_goal(LEFT_JOINTS, duration_sec=1),
                "Test 19 still moving at goal end",
                results,
            )
            if result is not None:
                expected = FollowJointTrajectory.Result.GOAL_TOLERANCE_VIOLATED
                if result.error_code != expected:
                    results.append(
                        f"FAIL: Test 19 error_code={result.error_code} "
                        f"(expected {expected}) {result.error_string}"
                    )
                elif len(hold_calls) < 2:
                    # One call is the goal_time_sec settle window, the second is
                    # the hold that keeps the arm from sagging after the abort.
                    results.append(
                        f"FAIL: Test 19 only {len(hold_calls)} hold(s); expected a "
                        f"settle window and a hold"
                    )
                else:
                    results.append(f"PASS: Test 19 {result.error_string}, held")
        finally:
            shim._hold_position = original_hold
            mock.velocity = 0.0
        time.sleep(0.3)

        # --- Test 20: segment the per-cycle clamp cannot deliver ---
        # w2's URDF limit is 4.0 rad/s but the clamp caps every joint at
        # max_step_rad_per_cycle * command_rate (2.0 rad/s). Such a goal used to
        # be accepted and then abort on path tolerance mid-move, blaming the arm
        # for the shim's own throttle.
        test_node.get_logger().info("Test 20: segment above the clamp rejected")
        over_clamp = list(shim._latest_positions)
        over_clamp[6] = over_clamp[6] + 0.9  # left_w2: 0.9 rad in 0.3 s = 3.0 rad/s
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(over_clamp, 0.3)]),
            "Test 20 over-clamp segment",
            results,
        )

        # --- Test 21: MoveIt's leading start-state point is accepted ---
        # MoveIt emits the current state as point 0 at time_from_start=0 and
        # expects the controller to treat it as "start here". Confirmed against
        # a real planner: 33 waypoints, point 0 at t=0 exactly on the measured
        # pose. Rejecting it made MoveIt unusable on hardware.
        test_node.get_logger().info("Test 21: leading t=0 start state accepted")
        start = list(shim._latest_positions)
        moveit_target = list(start)
        moveit_target[1] = moveit_target[1] + 0.1  # left_s1
        result = send_and_wait(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(start, 0.0), (moveit_target, 1.0)]),
            "Test 21 MoveIt-style trajectory",
            results,
        )
        if result is not None:
            if result.error_code != 0:
                results.append(
                    f"FAIL: Test 21 error_code={result.error_code} "
                    f"({result.error_string})"
                )
            else:
                results.append("PASS: Test 21 leading t=0 start state accepted")
        time.sleep(0.3)

        # --- Test 22: a t=0 point that is NOT the start state still rejects ---
        # This is the case the strictly-increasing-time rule exists for: it would
        # exit the interpolation loop immediately and command the raw target in a
        # single jump. Test 21 must not have weakened it.
        test_node.get_logger().info("Test 22: t=0 far from measured still rejected")
        jump = list(shim._latest_positions)
        jump[1] = jump[1] + 0.9  # well beyond path_tolerance_rad
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(jump, 0.0), (jump, 1.0)]),
            "Test 22 t=0 jump",
            results,
        )

        # --- Test 23: a trajectory that is only a start state has nothing to do ---
        test_node.get_logger().info("Test 23: start state alone rejected")
        expect_reject(
            test_node,
            client,
            make_goal(LEFT_JOINTS, [(list(shim._latest_positions), 0.0)]),
            "Test 23 start state only",
            results,
        )

        # --- Test 24: planner joint order is honoured, not rejected ---
        # MoveIt sends joints alphabetically (e0, e1, s0, s1, w0, w1, w2). The
        # action defines the mapping by name, so any permutation is legal and the
        # shim must reorder. Verified by moving exactly one joint and checking the
        # arm went where the *names* said, not where the positions sat.
        test_node.get_logger().info("Test 24: permuted joint order honoured")
        permuted = sorted(LEFT_JOINTS)
        base = dict(zip(LEFT_JOINTS, shim._latest_positions))
        target = dict(base)
        target["left_s1"] = base["left_s1"] + 0.1
        result = send_and_wait(
            test_node,
            client,
            make_goal(permuted, [([target[j] for j in permuted], 1.0)]),
            "Test 24 permuted joint order",
            results,
        )
        if result is not None:
            if result.error_code != 0:
                results.append(
                    f"FAIL: Test 24 error_code={result.error_code} "
                    f"({result.error_string})"
                )
            else:
                # The arm never moves here (mock_mode skips publishing), so check
                # what was *commanded*. Comparing the whole vector is what catches
                # a wrong permutation: a bad mapping puts the delta on some other
                # joint rather than simply failing to move.
                expected = [target[j] for j in LEFT_JOINTS]
                worst = max(
                    abs(c - e) for c, e in zip(shim._last_commanded, expected)
                )
                if worst > 0.01:
                    results.append(
                        f"FAIL: Test 24 commanded {[round(c, 3) for c in shim._last_commanded]}, "
                        f"expected {[round(e, 3) for e in expected]} — positions "
                        f"were not remapped to the goal's joint names"
                    )
                else:
                    results.append("PASS: Test 24 permuted joint order honoured")
        time.sleep(0.3)

        passed = bool(results) and all(r.startswith("PASS") for r in results)
        for r in results:
            test_node.get_logger().info(r)
        test_node.get_logger().info(f"OVERALL: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        try:
            executor.shutdown()
        except Exception:
            pass
        if test_node is not None:
            test_node.destroy_node()
        if mock is not None:
            mock.destroy_node()
        if shim is not None:
            shim.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main() -> None:
    import sys

    ok = run_test()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
