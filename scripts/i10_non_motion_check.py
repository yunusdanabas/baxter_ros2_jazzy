#!/usr/bin/env python3
"""I10 non-motion bridge check — no ROS 1 install needed.

Queries Baxter's ROS 1 master directly via XML-RPC to verify:
  1. Network connectivity (ping + port 11311)
  2. ROS 1 master is alive
  3. Robot publishes /robot/state (AssemblyState)
  4. Robot publishes /robot/joint_states (JointState)
  5. IK services are visible
  6. Gripper state/properties topics exist
  7. Camera services exist

No motion, no enable, no bridge binary. Just discovery.

Usage:
  python3 i10_non_motion_check.py <robot_ip>

Example:
  python3 i10_non_motion_check.py 10.42.0.2
"""

import socket
import sys
import xmlrpc.client
from typing import Optional


def check_ping(ip: str) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((ip, 11311))
        sock.close()
        return True
    except Exception as e:
        print(f"  FAIL: cannot reach {ip}:11311 — {e}")
        return False


def get_master_uri(ip: str) -> str:
    return f"http://{ip}:11311"


def query_master(master_uri: str, code: int, *args) -> Optional[tuple]:
    master = xmlrpc.client.ServerProxy(master_uri)
    try:
        return master.getSystemState("/i10_check")
    except Exception as e:
        print(f"  FAIL: XML-RPC query failed — {e}")
        return None


def get_topics(master_uri: str) -> Optional[dict]:
    master = xmlrpc.client.ServerProxy(master_uri)
    try:
        code, msg, topics = master.getTopicTypes("/i10_check")
        if code != 1:
            print(f"  FAIL: getTopicTypes returned code={code} msg={msg}")
            return None
        return {name: msg_type for name, msg_type in topics}
    except Exception as e:
        print(f"  FAIL: getTopicTypes failed — {e}")
        return None


def get_system_state(master_uri: str) -> Optional[tuple]:
    master = xmlrpc.client.ServerProxy(master_uri)
    try:
        code, msg, state = master.getSystemState("/i10_check")
        if code != 1:
            print(f"  FAIL: getSystemState returned code={code} msg={msg}")
            return None
        return state  # [publishers, subscribers, services]
    except Exception as e:
        print(f"  FAIL: getSystemState failed — {e}")
        return None


REQUIRED_TOPICS = {
    "/robot/state": "baxter_core_msgs/AssemblyState",
    "/robot/joint_states": "sensor_msgs/JointState",
}

IMPORTANT_TOPICS = {
    "/robot/limb/left/state": "baxter_core_msgs/AssemblyState",
    "/robot/limb/right/state": "baxter_core_msgs/AssemblyState",
    "/robot/limb/left/endpoint_state": "baxter_core_msgs/EndpointState",
    "/robot/limb/right/endpoint_state": "baxter_core_msgs/EndpointState",
    "/robot/end_effector/left_gripper/state": "baxter_core_msgs/EndEffectorState",
    "/robot/end_effector/right_gripper/state": "baxter_core_msgs/EndEffectorState",
    "/robot/end_effector/left_gripper/properties": "baxter_core_msgs/EndEffectorProperties",
    "/robot/end_effector/right_gripper/properties": "baxter_core_msgs/EndEffectorProperties",
    "/robot/limb/left/joint_command": "baxter_core_msgs/JointCommand",
    "/robot/limb/right/joint_command": "baxter_core_msgs/JointCommand",
    "/robot/limb/left/set_speed_ratio": "std_msgs/Float64",
    "/robot/limb/right/set_speed_ratio": "std_msgs/Float64",
    "/robot/set_super_enable": "std_msgs/Bool",
    "/robot/set_super_stop": "std_msgs/Empty",
}

EXPECTED_SERVICES = [
    "/ExternalTools/left/PositionKinematicsNode/IKService",
    "/ExternalTools/right/PositionKinematicsNode/IKService",
    "/cameras/list",
    "/cameras/open",
    "/cameras/close",
]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <robot_ip>")
        print(f"Example: {sys.argv[0]} 10.42.0.2")
        sys.exit(1)

    ip = sys.argv[1]
    master_uri = get_master_uri(ip)
    print("\n=== I10 Non-Motion Bridge Check ===")
    print(f"Robot IP: {ip}")
    print(f"ROS 1 Master URI: {master_uri}\n")

    results: list[str] = []

    # 1. Network check
    print("--- 1. Network Check ---")
    if check_ping(ip):
        print(f"  OK: port 11311 reachable on {ip}")
        results.append("PASS: network")
    else:
        results.append("FAIL: network")
        print("\nCannot proceed without network. Check cable/WiFi, IP, and that Baxter is powered on.")
        sys.exit(1)
    print()

    # 2. ROS 1 master alive
    print("--- 2. ROS 1 Master Alive ---")
    state = get_system_state(master_uri)
    if state is None:
        results.append("FAIL: master")
        sys.exit(1)
    publishers, subscribers, services = state
    print(f"  OK: master alive. {len(publishers)} publishers, {len(subscribers)} subscribers, {len(services)} services")
    results.append("PASS: master")
    print()

    # 3. Get topic types
    print("--- 3. Topic Types ---")
    topics = get_topics(master_uri)
    if topics is None:
        results.append("FAIL: topics")
        sys.exit(1)
    print(f"  OK: {len(topics)} topics advertised")
    print()

    # 4. Required topics
    print("--- 4. Required Topics (non-motion) ---")
    for topic, expected_type in REQUIRED_TOPICS.items():
        if topic in topics:
            actual = topics[topic]
            if actual == expected_type:
                print(f"  OK: {topic} ({actual})")
                results.append(f"PASS: {topic}")
            else:
                print(f"  WARN: {topic} exists but type mismatch: {actual} != {expected_type}")
                results.append(f"WARN: {topic} type mismatch")
        else:
            print(f"  FAIL: {topic} NOT FOUND")
            results.append(f"FAIL: {topic}")
    print()

    # 5. Important topics
    print("--- 5. Important Topics (motion/gripper/safety) ---")
    for topic, expected_type in IMPORTANT_TOPICS.items():
        if topic in topics:
            print(f"  OK: {topic} ({topics[topic]})")
        else:
            print(f"  MISSING: {topic} (may not be installed)")
    print()

    # 6. Services
    print("--- 6. Services ---")
    service_names = {s[0] for s in services}
    for svc in EXPECTED_SERVICES:
        if svc in service_names:
            print(f"  OK: {svc}")
            results.append(f"PASS: {svc}")
        else:
            print(f"  MISSING: {svc}")
            results.append(f"WARN: {svc} not found")
    print()

    # 7. Joint state publishers
    print("--- 7. Joint State Publishers ---")
    js_pubs = [p for p in publishers if p[0] == "/robot/joint_states"]
    if js_pubs:
        for _, pubs in js_pubs:
            print(f"  OK: /robot/joint_states has {len(pubs)} publisher(s): {pubs}")
        results.append("PASS: joint_states publisher")
    else:
        print("  FAIL: /robot/joint_states has no publishers")
        results.append("FAIL: joint_states publisher")
    print()

    # Summary
    print("=== SUMMARY ===")
    for r in results:
        print(f"  {r}")

    failures = [r for r in results if r.startswith("FAIL")]
    warnings = [r for r in results if r.startswith("WARN")]
    if not failures:
        print(f"\nGATE: PASS ({len(warnings)} warnings)")
        print("\nNext: set up baxter_bridge on a host with ROS 1, then run the action shims.")
        sys.exit(0)
    else:
        print(f"\nGATE: FAIL ({len(failures)} failures, {len(warnings)} warnings)")
        sys.exit(1)


if __name__ == "__main__":
    main()
