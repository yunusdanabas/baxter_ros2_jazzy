#!/bin/bash
# ROS 1 side session recorder — the FULL robot topic set, straight from the
# robot's own master. Runs `rosbag record` inside the existing Noetic container,
# so nothing here depends on py_bridge.py: topics the bridge does not carry
# (diagnostics, sonar, IR, gripper state, gravity-comp torques) are captured too.
#
# Also dumps a topic/node/param inventory first — that snapshot is the raw
# material for docs/noetic_native_notes.md.
#
# Usage:   bash scripts/record_ros1.sh          # Ctrl-C to stop (closes the bag)
# Env:     IMAGE, BAXTER_HOST, BAXTER_IP, SESSION_DIR, EXCLUDE, TOPICS_RE, MIN_FREE_GB
#
# Self-check (no robot needed) — record a throwaway master that is publishing:
#   docker run -d --rm --name rec_check --network host baxter-noetic:n07 \
#       bash -lc "source /opt/ros/noetic/setup.bash && roscore"
#   sleep 8
#   docker exec -d rec_check bash -lc "source /opt/ros/noetic/setup.bash && \
#       rostopic pub -r 10 /selfcheck std_msgs/Float64 '{data: 1.0}'"
#   BAXTER_IP=127.0.0.1 MIN_FREE_GB=1 timeout -s INT 12 bash scripts/record_ros1.sh
#   docker run --rm -v "$PWD/data/sessions/$(date +%F)/ros1:/data" baxter-noetic:n07 \
#       bash -lc "source /opt/ros/noetic/setup.bash && rosbag info /data/full_*.bag"
#   docker rm -f rec_check
# Expect: topics/nodes/params snapshots, and a bag reporting ~100 messages on
# /selfcheck. A bag with 0 messages means recording silently did nothing.
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

IMAGE="${IMAGE:-baxter-noetic:n07}"
BAXTER_HOST="${BAXTER_HOST:-011412P0024.local}"
BAXTER_IP="${BAXTER_IP:-$(getent hosts "$BAXTER_HOST" 2>/dev/null | awk '{print $1}' | head -1)}"
: "${BAXTER_IP:?cannot resolve $BAXTER_HOST — check the network (runbook step 0)}"
ROS_IP="${ROS_IP:-$(ip route get "$BAXTER_IP" 2>/dev/null | grep -oP 'src \K\S+')}"
# Cameras are the only real bandwidth hog and we are not studying vision.
EXCLUDE="${EXCLUDE:-/cameras/.*}"
# Set TOPICS_RE to capture only what a question needs instead of everything.
# The set worth recording around a motion run or an enable attempt:
#   TOPICS_RE='/robot/(joint_states|ref_joint_states|state)|/diagnostics|/robot/limb/.*/(joint_command|gravity_compensation_torques|collision_.*_state)'
# /robot/ref_joint_states is the robot's own commanded reference — better
# tracking-error ground truth than anything reconstructed from our side.
TOPICS_RE="${TOPICS_RE:-}"

SESSION="${SESSION_DIR:-data/sessions/$(date +%F)}/ros1"
mkdir -p "$SESSION"
# Absolute, so an absolute SESSION_DIR does not get pasted onto the repo root
# when it is handed to `docker -v`.
SESSION="$(cd "$SESSION" && pwd)"
STAMP="$(date +%H%M%S)"

# A full day of 100 Hz joint streams is tens of GB. Refuse to start rather than
# fill the disk mid-experiment and lose the session.
MIN_FREE_GB="${MIN_FREE_GB:-10}"
FREE_GB="$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc '0-9')"
if [ "$FREE_GB" -lt "$MIN_FREE_GB" ]; then
    echo "REFUSING: only ${FREE_GB} GB free on $SESSION (need ${MIN_FREE_GB})." >&2
    echo "Free space, or lower MIN_FREE_GB if you accept a short recording." >&2
    exit 1
fi

DOCKER=(docker run --rm --network host
        --add-host="${BAXTER_HOST}:${BAXTER_IP}"
        --user "$(id -u):$(id -g)" -e HOME=/tmp
        -e ROS_MASTER_URI="http://${BAXTER_IP}:11311" -e ROS_IP="$ROS_IP"
        -v "$SESSION:/data" "$IMAGE")

echo "=== ROS 1 inventory snapshot -> $SESSION (stamp $STAMP) ==="
"${DOCKER[@]}" bash -lc "source /opt/ros/noetic/setup.bash && \
    rostopic list -v > /data/topics_${STAMP}.txt && \
    rosnode  list    > /data/nodes_${STAMP}.txt && \
    rosparam dump    > /data/params_${STAMP}.yaml"

if [ -n "$TOPICS_RE" ]; then
    SELECT="-e '$TOPICS_RE'"
    echo "=== Recording ROS 1 topics matching '$TOPICS_RE' — Ctrl-C to stop ==="
else
    SELECT="-a -x '$EXCLUDE'"
    echo "=== Recording all ROS 1 topics except '$EXCLUDE' — Ctrl-C to stop ==="
fi

# `exec` twice: rosbag ends up as PID 1 so docker's proxied SIGINT reaches it
# directly and the bag is closed cleanly instead of truncated.
exec "${DOCKER[@]}" bash -lc "source /opt/ros/noetic/setup.bash && \
    exec rosbag record $SELECT --lz4 --split --size=1024 \
         -o /data/full_${STAMP}"
