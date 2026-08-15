#!/bin/bash
# Hardware-free proof that py_bridge.py's ROS 1 Slave API / TCPROS negotiation
# actually works against a real ROS 1 master (genuine rospy, not a mock).
#
# Uses the existing baxter-noetic Docker image for roscore + rostopic (native
# CLI, no custom ROS 1 test code needed). Tests the protocol layer with a
# plain std_msgs/Float64 topic. Baxter-specific message (de)serializers are
# not exercised here — use a dedicated unit test or lab smoke for those.
#
# Usage: bash scripts/test_bridge_loopback.sh
# Safe to run from any working directory.
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

IMAGE="${IMAGE:-baxter-noetic:n07}"
CONTAINER="baxter_loopback_test"
FROM_ROS1="/loopback_test/from_ros1"
FROM_ROS2="/loopback_test/from_ros2"
ECHO_OUT="/tmp/loopback_echo_out.txt"

cleanup() {
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "=== Starting roscore in $CONTAINER ==="
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" --network host "$IMAGE" \
    bash -lc "source /opt/ros/noetic/setup.bash; roscore" >/dev/null

for i in $(seq 1 20); do
    if (echo > /dev/tcp/127.0.0.1/11311) 2>/dev/null; then
        break
    fi
    sleep 0.5
done

echo "=== Publishing $FROM_ROS1 from genuine rostopic ==="
docker exec -d "$CONTAINER" bash -lc \
    "source /opt/ros/noetic/setup.bash; rostopic pub -r 5 $FROM_ROS1 std_msgs/Float64 '{data: 3.14}'"

rm -f "$ECHO_OUT"
docker exec "$CONTAINER" bash -lc \
    "source /opt/ros/noetic/setup.bash; timeout 15 rostopic echo -n1 $FROM_ROS2" \
    > "$ECHO_OUT" &
ECHO_PID=$!

echo "=== Running py_bridge negotiation (host side) ==="
# Via baxter_env.sh, not the ROS setup files directly: it also strips an active
# conda install from PATH, without which rclpy fails to import here exactly as it
# does on the robot. Desk loopback has no robot — use localhost (not a lab serial).
# shellcheck disable=SC1091
export BAXTER_HOST="${BAXTER_HOST:-127.0.0.1}"
source "$SCRIPT_DIR/baxter_env.sh" >/dev/null

PY_STATUS=0
# `|| PY_STATUS=$?` keeps set -e from killing us before the diagnostics below.
python3 - "$FROM_ROS1" "$FROM_ROS2" "$SCRIPT_DIR" <<'PYEOF' || PY_STATUS=$?
import struct
import sys
import time

sys.path.insert(0, sys.argv[3])
from py_bridge import ROS1Publisher, ROS1Subscriber, SlaveApi

from_ros1, from_ros2 = sys.argv[1], sys.argv[2]
master_uri = "http://127.0.0.1:11311"

slave = SlaveApi("127.0.0.1", master_uri)

received = []
sub = ROS1Subscriber(master_uri, from_ros1, "std_msgs/Float64", "/loopback_sub",
                      slave, received.append,
                      lambda data: struct.unpack("<d", data)[0])
sub.start()

pub = ROS1Publisher(master_uri, from_ros2, "std_msgs/Float64", "/loopback_pub",
                     slave, 31500, lambda v: struct.pack("<d", v))
pub.start()

deadline = time.time() + 10
while time.time() < deadline and not received:
    time.sleep(0.2)

if not received:
    print("FAIL: never received /loopback_test/from_ros1 from real rostopic pub")
    sys.exit(1)
print(f"PASS: ROS1->bridge received {received[0]}")

deadline = time.time() + 8
while time.time() < deadline:
    pub.publish(2.71828)
    time.sleep(0.3)
print("PASS: bridge->ROS1 publish loop done")
PYEOF

wait "$ECHO_PID" || true

echo "=== rostopic echo captured ==="
cat "$ECHO_OUT" || true

if [ "$PY_STATUS" -ne 0 ]; then
    echo "FAIL: subscribe direction (ROS1 -> bridge) did not pass"
    exit 1
fi
if ! grep -q "2.71828" "$ECHO_OUT"; then
    echo "FAIL: publish direction (bridge -> ROS1) — rostopic echo never saw our value"
    exit 1
fi

echo "=== OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy) ==="
