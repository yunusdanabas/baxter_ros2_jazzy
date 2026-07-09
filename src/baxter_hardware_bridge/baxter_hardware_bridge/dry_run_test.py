#!/usr/bin/env python3
"""Dry-run self-test for the hardware action shim.

Launches mock_robot + follow_joint_trajectory_shim in-process,
sends a tiny FollowJointTrajectory goal, and verifies:
  1. Safe state: goal accepted and succeeds.
  2. Unsafe state: goal rejected.
  3. Bad joint names: goal rejected.

Exit code 0 on pass, 1 on fail.
"""

import threading
import time
from typing import List

import rclpy
from baxter_core_msgs.msg import AssemblyState, JointCommand
from baxter_hardware_bridge.follow_joint_trajectory_shim import (
    FollowJointTrajectoryShim,
    LEFT_JOINTS,
)
from baxter_hardware_bridge.mock_robot import MockRobot
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from trajectory_msgs.msg import JointTrajectoryPoint


def make_tiny_goal(joints: List[str], offset: float = 0.1) -> FollowJointTrajectory.Goal:
    goal = FollowJointTrajectory.Goal()
    goal.trajectory.joint_names = list(joints)
    p0 = JointTrajectoryPoint()
    p0.positions = [0.0] * len(joints)
    p0.time_from_start.sec = 0
    p1 = JointTrajectoryPoint()
    p1.positions = [0.0] * len(joints)
    p1.positions[1] = offset
    p1.time_from_start.sec = 1
    goal.trajectory.points = [p0, p1]
    return goal


def wait_future(node, future, timeout_sec: float):
    """Spin node until future completes or timeout."""
    deadline = time.monotonic() + timeout_sec
    while not future.done() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
    return future.done()


def run_test() -> bool:
    rclpy.init()
    executor = MultiThreadedExecutor(num_threads=4)

    mock = MockRobot()
    shim = FollowJointTrajectoryShim()
    # Override mock_mode so we don't publish to real robot topics
    shim._mock_mode = True

    executor.add_node(mock)
    executor.add_node(shim)

    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    # Test node is spun separately to avoid executor conflicts
    test_node = rclpy.create_node("dry_run_test")
    client = ActionClient(test_node, FollowJointTrajectory, "/robot/limb/left/follow_joint_trajectory")

    # Wait for action server
    for _ in range(100):
        if client.wait_for_server(timeout_sec=0.1):
            break
    else:
        test_node.get_logger().error("FAIL: action server not available")
        return False

    results: List[str] = []

    # --- Test 1: safe state, correct joints -> accept + succeed ---
    test_node.get_logger().info("Test 1: safe state, correct joints")
    goal_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS))
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
                if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL:
                    results.append("PASS: Test 1 goal succeeded")
                else:
                    results.append(
                        f"FAIL: Test 1 error_code={result.error_code} {result.error_string}"
                    )

    # --- Test 2: bad joint names -> reject ---
    test_node.get_logger().info("Test 2: bad joint names")
    bad_joints = ["foo_s0", "foo_s1", "foo_e0", "foo_e1", "foo_w0", "foo_w1", "foo_w2"]
    goal_future = client.send_goal_async(make_tiny_goal(bad_joints))
    if not wait_future(test_node, goal_future, 5.0):
        results.append("FAIL: Test 2 goal response timeout")
    else:
        gh = goal_future.result()
        if not gh.accepted:
            results.append("PASS: Test 2 bad joints rejected")
        else:
            gh.cancel_goal_async()
            results.append("FAIL: Test 2 bad joints accepted (expected reject)")

    # --- Test 3: unsafe state -> reject ---
    test_node.get_logger().info("Test 3: unsafe state")
    mock._unsafe = True
    time.sleep(1.0)  # wait for several unsafe state messages to propagate
    goal_future = client.send_goal_async(make_tiny_goal(LEFT_JOINTS))
    if not wait_future(test_node, goal_future, 5.0):
        results.append("FAIL: Test 3 goal response timeout")
    else:
        gh = goal_future.result()
        if not gh.accepted:
            results.append("PASS: Test 3 unsafe state rejected")
        else:
            gh.cancel_goal_async()
            results.append("FAIL: Test 3 unsafe state accepted (expected reject)")
    mock._unsafe = False

    passed = all(r.startswith("PASS") for r in results)
    for r in results:
        test_node.get_logger().info(r)
    test_node.get_logger().info(f"OVERALL: {'PASS' if passed else 'FAIL'}")

    executor.shutdown()
    test_node.destroy_node()
    mock.destroy_node()
    shim.destroy_node()
    rclpy.shutdown()
    return passed


def main() -> None:
    import sys
    ok = run_test()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
