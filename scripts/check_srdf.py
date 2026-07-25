#!/usr/bin/env python3
"""Guard the SRDF's collision matrix against the failure that bit us.

Two modes, both hardware-free:

  poses            Ask move_group whether the robot's known-good poses are
                   collision-free. Needs move_group running (see below).
  diff OLD NEW     Compare two SRDFs' disable_collisions sets and confirm the
                   hand-added pairs survived. Pure text, nothing running.

Why this exists: `baxter.srdf` carries only ~54 disable_collisions pairs, and one
missing pair made move_group return -10 START_STATE_IN_COLLISION from the pose
`tuck_arms.py -u` leaves the robot in — 1.7 mm of mesh interference between
left_upper_shoulder and left_upper_elbow, two links apart, so the Setup Assistant
never marked them Adjacent (logs/I18_hardware_day.log.md F18.3). A full Setup
Assistant re-run would regenerate that matrix from scratch, and there is nothing
in the regeneration that knows about those two pairs.

Run this before and after any Setup Assistant re-run.

Desk setup for `poses`, no robot:

    ros2 run baxter_hardware_bridge mock_robot                    # joint states
    ros2 launch baxter_moveit_config hardware_moveit.launch.py rviz:=false
    python3 scripts/check_srdf.py poses

Exit code 0 if every pose is valid and every required pair is present, 1 if not.
"""

import re
import sys

# The pairs that are not derivable from the model — each one cost a hardware
# session to find, and a regenerated matrix will not contain them.
REQUIRED_PAIRS = {
    frozenset(("left_upper_shoulder", "left_upper_elbow")),
    frozenset(("right_upper_shoulder", "right_upper_elbow")),
}

ARM_JOINTS = [
    f"{side}_{j}"
    for side in ("left", "right")
    for j in ("s0", "s1", "e0", "e1", "w0", "w1", "w2")
]

# Poses that must plan. Untuck is measured, not nominal: it is where
# `tuck_arms.py -u` actually left the robot on 2026-07-24 (I18 F5), which is the
# pose that exposed the missing pair. Neutral is the SRDF's own group_state.
POSES = {
    "untuck (measured 2026-07-24)": [
        -0.114, -1.042, -1.030, 1.962, 0.651, 0.992, -0.483,
        0.110, -1.041, 1.040, 1.961, -0.646, 0.990, 0.489,
    ],
    "neutral (SRDF group_state)": [
        0.0, -0.55, 0.0, 0.75, 0.0, 1.26, 0.0,
        0.0, -0.55, 0.0, 0.75, 0.0, 1.26, 0.0,
    ],
}

# Negative control. Without this a matrix that disabled *everything* would pass
# the checks above, which is the failure mode a regenerated collision matrix
# actually has. This pose folds the left forearm back onto its own upper arm:
# 5 cm of interpenetration across 13 contacts, nothing subtle about it.
MUST_COLLIDE = {
    "left forearm folded onto upper arm": [
        0.0, 0.0, 0.0, 2.6, 0.0, 0.0, 0.0,
        0.0, -0.55, 0.0, 0.75, 0.0, 1.26, 0.0,
    ],
}

PAIR_RE = re.compile(r'disable_collisions\s+link1="([^"]+)"\s+link2="([^"]+)"')


def read_pairs(path: str) -> set:
    with open(path) as handle:
        return {frozenset(m) for m in PAIR_RE.findall(handle.read())}


def diff(old_path: str, new_path: str) -> bool:
    old, new = read_pairs(old_path), read_pairs(new_path)
    added, removed = new - old, old - new

    print(f"{old_path}: {len(old)} pairs")
    print(f"{new_path}: {len(new)} pairs")
    for label, pairs in (("added", added), ("removed", removed)):
        print(f"\n=== {label} ({len(pairs)}) ===")
        for pair in sorted(tuple(sorted(p)) for p in pairs):
            print(f"  {pair[0]} <-> {pair[1]}")

    missing = REQUIRED_PAIRS - new
    if missing:
        print("\nFAIL: required pairs absent from the new SRDF:")
        for pair in sorted(tuple(sorted(p)) for p in missing):
            print(f"  {pair[0]} <-> {pair[1]}")
        print(
            "\nRe-add them by hand with their measurement comment. A regenerated\n"
            "matrix cannot rediscover them: the interference is 1.7 mm at one\n"
            "specific pose, and the Setup Assistant's sampling missed it."
        )
        return False
    print(f"\nOK: all {len(REQUIRED_PAIRS)} required pairs present.")
    return True


def poses() -> bool:
    import rclpy
    from moveit_msgs.msg import RobotState
    from moveit_msgs.srv import GetStateValidity
    from sensor_msgs.msg import JointState

    rclpy.init()
    node = rclpy.create_node("check_srdf")
    client = node.create_client(GetStateValidity, "/check_state_validity")
    ok = True
    try:
        if not client.wait_for_service(timeout_sec=15.0):
            print("FAIL: /check_state_validity not available — is move_group up?")
            return False

        for label, positions in list(POSES.items()) + list(MUST_COLLIDE.items()):
            must_collide = label in MUST_COLLIDE
            state = RobotState()
            # Only joints move_group's model knows. Sending one it does not --
            # head_nod, say -- throws an uncaught moveit::Exception and kills
            # move_group with exit -6 (I18 F21). Do not widen this list.
            state.joint_state = JointState(name=ARM_JOINTS, position=positions)
            request = GetStateValidity.Request(
                robot_state=state, group_name="both_arms"
            )
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=15.0)
            result = future.result()
            if result is None:
                print(f"FAIL: {label}: no response from /check_state_validity")
                ok = False
                continue
            if must_collide:
                if result.valid:
                    ok = False
                    print(
                        f"FAIL: {label} reports collision-free — the matrix "
                        f"disables a pair it must check"
                    )
                else:
                    worst = max(c.depth for c in result.contacts) if result.contacts else 0.0
                    print(
                        f"PASS: {label} correctly reports a collision "
                        f"(worst depth {worst:.5f})"
                    )
                continue
            if result.valid:
                print(f"PASS: {label} is collision-free")
                continue
            ok = False
            print(f"FAIL: {label} is in collision")
            for contact in result.contacts:
                print(
                    f"    {contact.contact_body_1} <-> {contact.contact_body_2}"
                    f"  depth={contact.depth:.5f}"
                )
            print(
                "    ^ add these as disable_collisions if the depth is a sub-mm\n"
                "      graze between links that genuinely cannot hit each other."
            )
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return ok


def main() -> None:
    args = sys.argv[1:]
    if args[:1] == ["diff"] and len(args) == 3:
        ok = diff(args[1], args[2])
    elif args in ([], ["poses"]):
        ok = poses()
    else:
        print(__doc__)
        sys.exit(2)
    print("\nOVERALL:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
