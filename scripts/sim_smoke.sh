#!/bin/bash
# One-command sim verification — no robot, no GUI.
#
# Runs what docs/sim_test_commands.md §2-§5 does by hand and *asserts the
# numbers*, not just the exit codes: a client can exit 0 having moved the wrong
# joint, or having printed nothing at all. Teardown is part of the test.
#
# Usage:   bash scripts/sim_smoke.sh [gates|gazebo|moveit|all]   (default: all)
# Env:     MAX_ERROR_RAD (0.02), MAX_DRIFT_RAD (0.01), READY_TIMEOUT (90)
#
# Exit 0 only if every check passed. Logs land in a per-run directory, printed
# on failure.
#
# The RViz MotionPlanning panel checks stay manual in sim_test_commands.md —
# they need eyes. This covers everything that can be read off a log line.
set -uo pipefail
# Job control on. Without it bash sets SIGINT to SIG_IGN in every asynchronous
# command, so `kill -INT` on a backgrounded `ros2 launch` is silently a no-op and
# the teardown gate fails for a reason that has nothing to do with the launch.
# Signal the launch PID only, never the process group: the group form kills
# `ros2 launch` outright and it never gets to shut its own children down.
set -m

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-all}"
MAX_ERROR_RAD="${MAX_ERROR_RAD:-0.02}"
MAX_DRIFT_RAD="${MAX_DRIFT_RAD:-0.01}"
READY_TIMEOUT="${READY_TIMEOUT:-90}"
LOGDIR="$(mktemp -d "${TMPDIR:-/tmp}/sim_smoke.XXXXXX")"
ORPHAN_RE='gz sim|ros_gz_bridge|move_group|rviz2|robot_state_publisher|ros2_control_node'

export ROS2CLI_NO_DAEMON=1

PASSED=0
FAILED=0
declare -a RESULTS

pass() { RESULTS+=("PASS  $1"); PASSED=$((PASSED + 1)); }
fail() { RESULTS+=("FAIL  $1${2:+ -- $2}"); FAILED=$((FAILED + 1)); }

# --------------------------------------------------------------------------
# Preconditions. Both of these produce failures that look like something else.
# --------------------------------------------------------------------------

# A conda python3 gets baked into every console-script shebang at build time, so
# the build succeeds and every `ros2 run` then dies on rclpy._rclpy_pybind11.
if [ "$(command -v python3)" != "/usr/bin/python3" ]; then
    echo "REFUSING: python3 is $(command -v python3), not /usr/bin/python3." >&2
    echo "Run 'conda deactivate' and rebuild; entry-point shebangs are baked at build time." >&2
    exit 1
fi

if [ ! -f install/setup.bash ]; then
    echo "REFUSING: no install/setup.bash. Build first (docs/sim_test_commands.md §1)." >&2
    exit 1
fi

# The name has to be matched against the command line, because Gazebo runs as
# `ruby` (`gz sim -r -s empty.sdf`) and comm is truncated to 15 characters
# elsewhere (`parameter_bridg`, `robot_state_pub`). That makes any *shell* whose
# arguments merely mention these names — a CI wrapper, an editor task, the
# terminal that invoked this script — look like a running simulation, so shells
# are excluded by comm. No real simulation process is a shell.
orphans() {
    local pid comm
    pgrep -f "$ORPHAN_RE" 2>/dev/null | while read -r pid; do
        comm="$(cat "/proc/$pid/comm" 2>/dev/null)" || continue
        case "$comm" in bash | sh | dash | zsh | ksh | fish) continue ;; esac
        echo "$pid"
    done
}

orphans_detail() {
    local pid
    orphans | while read -r pid; do
        printf '  %s %s\n' "$pid" "$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | cut -c1-70)"
    done
}

# Leftovers from a previous run are indistinguishable from a teardown failure in
# this one, so refuse rather than report a false negative later.
if [ -n "$(orphans)" ]; then
    echo "REFUSING: simulation processes already running:" >&2
    orphans_detail >&2
    exit 1
fi

# ROS setup scripts read unset variables (AMENT_TRACE_SETUP_FILES and friends),
# so -u has to come off around them. It stays on for our own code.
set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
# shellcheck disable=SC1091
source install/setup.bash
set -u

echo "=== sim smoke: mode=$MODE, logs in $LOGDIR ==="

# --------------------------------------------------------------------------
# Assertions
# --------------------------------------------------------------------------

# `min_count` is the point of this: without it, a client that printed no
# verified lines at all would pass the threshold check vacuously.
assert_motion() {
    local log="$1" min_count="$2" over
    local n
    n=$(grep -c 'max_error=' "$log" 2>/dev/null || true)
    if [ "${n:-0}" -lt "$min_count" ]; then
        echo "$n max_error lines, expected >= $min_count"
        return 1
    fi
    over=$(grep -o 'max_error=[0-9.]*' "$log" | cut -d= -f2 \
           | awk -v t="$MAX_ERROR_RAD" '$1 > t' | paste -sd, -)
    if [ -n "$over" ]; then
        echo "max_error over ${MAX_ERROR_RAD}: $over"
        return 1
    fi
    return 0
}

assert_drift() {
    local log="$1" over
    if ! grep -q 'max_drift=' "$log"; then
        echo "no max_drift line — hold was never verified"
        return 1
    fi
    over=$(grep -o 'max_drift=[0-9.]*' "$log" | cut -d= -f2 \
           | awk -v t="$MAX_DRIFT_RAD" '$1 > t' | paste -sd, -)
    if [ -n "$over" ]; then
        echo "max_drift over ${MAX_DRIFT_RAD}: $over"
        return 1
    fi
    return 0
}

# run <label> <expected_exit> <logname> -- <command...>
run() {
    local label="$1" want="$2" logname="$3"; shift 4
    local log="$LOGDIR/$logname.log" got
    timeout 240 "$@" >"$log" 2>&1
    got=$?
    if [ "$got" -ne "$want" ]; then
        fail "$label" "exit $got, expected $want (see $log)"
        return 1
    fi
    return 0
}

# --------------------------------------------------------------------------
# Launch management
# --------------------------------------------------------------------------

LAUNCH_PID=""
LAUNCH_LABEL=""

stop_launch() {
    [ -n "$LAUNCH_PID" ] || return 0
    kill -INT "$LAUNCH_PID" 2>/dev/null || true
    for _ in $(seq 1 30); do
        kill -0 "$LAUNCH_PID" 2>/dev/null || break
        sleep 1
    done
    # Only escalate after the graceful path has been given its chance and
    # already recorded as a failure — otherwise SIGKILL hides the defect.
    if kill -0 "$LAUNCH_PID" 2>/dev/null; then
        fail "$LAUNCH_LABEL teardown" "still alive 30 s after one SIGINT"
        kill -9 "$LAUNCH_PID" 2>/dev/null || true
        sleep 3
    fi
    LAUNCH_PID=""
}

cleanup() {
    stop_launch
    local pid
    if [ -n "$(orphans)" ]; then
        echo "WARNING: killing leftover processes on exit" >&2
        # By PID, not `pkill -f`: the pattern would also match innocent shells.
        for pid in $(orphans); do kill -9 "$pid" 2>/dev/null || true; done
    fi
}
trap cleanup EXIT INT TERM

start_launch() {
    LAUNCH_LABEL="$1"; shift
    local logname="$1"; shift
    ros2 launch "$@" >"$LOGDIR/$logname.log" 2>&1 &
    LAUNCH_PID=$!
    # Give the launch a moment to install its own SIGINT handler; signalling it
    # mid-startup is not the teardown path the docs describe.
    sleep 2
}

# wait_ready <label> <shell-predicate>
wait_ready() {
    local label="$1" predicate="$2" i
    for i in $(seq 1 "$READY_TIMEOUT"); do
        if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then
            fail "$label ready" "launch exited early"
            return 1
        fi
        if eval "$predicate" >/dev/null 2>&1; then
            pass "$label ready (${i}s)"
            return 0
        fi
        sleep 1
    done
    fail "$label ready" "timed out after ${READY_TIMEOUT}s"
    return 1
}

teardown_check() {
    local label="$1" left
    stop_launch
    sleep 3
    left="$(orphans | paste -sd, -)"
    if [ -n "$left" ]; then
        fail "$label teardown" "orphans: $left"
    else
        pass "$label teardown (no orphans after one SIGINT)"
    fi
}

# --------------------------------------------------------------------------
# gates — no Gazebo, no GPU. Mirrors the CI job.
# --------------------------------------------------------------------------
run_gates() {
    echo "--- gates ---"

    if grep -RIq '@example\.com' src --include='package.xml' SECURITY.md CODE_OF_CONDUCT.md 2>/dev/null; then
        fail "publish hygiene" "placeholder contact still present"
    else
        pass "publish hygiene"
    fi

    if python3 -m compileall -q src/baxter_bringup src/baxter_gz_sim \
            src/baxter_moveit_config src/baxter_examples src/baxter_hardware_bridge \
            >"$LOGDIR/compileall.log" 2>&1; then
        pass "compileall"
    else
        fail "compileall" "see $LOGDIR/compileall.log"
    fi

    # ruff is not a ROS dependency and rosdep will not install it; a missing
    # linter must not masquerade as a clean one.
    if command -v ruff >/dev/null; then
        if ruff check --select F src scripts --exclude src/baxter_common_ros2 \
                >"$LOGDIR/ruff.log" 2>&1; then
            pass "ruff --select F"
        else
            fail "ruff --select F" "see $LOGDIR/ruff.log"
        fi
    else
        RESULTS+=("SKIP  ruff --select F -- not installed (pipx install ruff)")
    fi

    if colcon test --base-paths src --packages-select baxter_examples \
            >"$LOGDIR/colcon_test.log" 2>&1 \
            && colcon test-result --verbose >>"$LOGDIR/colcon_test.log" 2>&1; then
        pass "colcon test baxter_examples"
    else
        fail "colcon test baxter_examples" "see $LOGDIR/colcon_test.log"
    fi

    if ros2 run baxter_hardware_bridge dry_run_test >"$LOGDIR/dry_run.log" 2>&1 \
            && grep -q 'OVERALL: PASS' "$LOGDIR/dry_run.log"; then
        pass "dry_run_test ($(grep -c 'PASS: Test' "$LOGDIR/dry_run.log") cases)"
    else
        fail "dry_run_test" "see $LOGDIR/dry_run.log"
    fi

    if ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro \
            >"$LOGDIR/model.urdf" 2>"$LOGDIR/xacro.log" \
            && check_urdf "$LOGDIR/model.urdf" >"$LOGDIR/check_urdf.log" 2>&1; then
        pass "xacro + check_urdf"
    else
        fail "xacro + check_urdf" "see $LOGDIR/xacro.log"
    fi

    if python3 - <<'PY' >"$LOGDIR/srdf.log" 2>&1
import xml.etree.ElementTree as ET
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

srdf = Path(get_package_share_directory('baxter_moveit_config')) / 'config' / 'baxter.srdf'
pairs = {tuple(sorted((c.attrib['link1'], c.attrib['link2'])))
         for c in ET.parse(srdf).getroot().findall('disable_collisions')}
for required in (('left_upper_elbow', 'left_upper_shoulder'),
                 ('right_upper_elbow', 'right_upper_shoulder')):
    assert required in pairs, f'hand-added pair lost: {required}'
assert len(pairs) == 54, len(pairs)
print(f'acm_pairs={len(pairs)}')
PY
    then
        pass "SRDF $(cat "$LOGDIR/srdf.log")"
    else
        fail "SRDF collision matrix" "see $LOGDIR/srdf.log"
    fi
}

# --------------------------------------------------------------------------
# gazebo
# --------------------------------------------------------------------------
run_gazebo() {
    echo "--- gazebo ---"
    start_launch "gazebo" "gazebo_launch" baxter_gz_sim sim.launch.py headless:=true
    wait_ready "gazebo" '[ "$(ros2 control list_controllers 2>/dev/null | grep -c active)" -ge 3 ]' || {
        teardown_check "gazebo"; return
    }

    if [ "$(ros2 topic echo /joint_states --once 2>/dev/null | grep -c '^- ')" -ge 17 ]; then
        pass "joint_states 17 independent joints"
    else
        fail "joint_states" "fewer than 17 joints"
    fi

    local msg
    if run "tiny trajectory both arms" 0 tiny_default -- \
            ros2 launch baxter_examples sim_tiny_trajectory.launch.py; then
        # 2 arms x outbound + return
        if msg=$(assert_motion "$LOGDIR/tiny_default.log" 4); then
            pass "tiny trajectory both arms (<= ${MAX_ERROR_RAD} rad)"
        else
            fail "tiny trajectory both arms" "$msg"
        fi
    fi

    if run "tiny trajectory joint:=e1" 0 tiny_e1 -- \
            ros2 run baxter_examples sim_tiny_trajectory --ros-args \
            -p use_sim_time:=true -p joint:=e1; then
        if msg=$(assert_motion "$LOGDIR/tiny_e1.log" 4); then
            pass "tiny trajectory joint:=e1"
        else
            fail "tiny trajectory joint:=e1" "$msg"
        fi
    fi

    # An unknown joint must be refused, or the limit table is not being consulted.
    if run "unknown joint refused" 1 tiny_bad -- \
            ros2 run baxter_examples sim_tiny_trajectory --ros-args \
            -p use_sim_time:=true -p joint:=elbow; then
        if grep -q "Unknown joint 'elbow'" "$LOGDIR/tiny_bad.log"; then
            pass "unknown joint refused"
        else
            fail "unknown joint refused" "exited 1 but not with the limit-table error"
        fi
    fi

    if run "cancel and hold" 0 tiny_cancel -- \
            ros2 run baxter_examples sim_tiny_trajectory --ros-args \
            -p use_sim_time:=true -p cancel_after_sec:=1.0; then
        if ! grep -q 'Controller goal canceled; holding position' "$LOGDIR/tiny_cancel.log"; then
            fail "cancel and hold" "expected cancel log line absent"
        elif msg=$(assert_drift "$LOGDIR/tiny_cancel.log"); then
            pass "cancel and hold"
        else
            fail "cancel and hold" "$msg"
        fi
    fi

    teardown_check "gazebo"
}

# --------------------------------------------------------------------------
# moveit
# --------------------------------------------------------------------------
run_moveit() {
    echo "--- moveit ---"
    start_launch "moveit" "moveit_launch" baxter_moveit_config sim_moveit.launch.py headless:=true
    wait_ready "moveit" 'ros2 action list 2>/dev/null | grep -q "^/move_action$"' || {
        teardown_check "moveit"; return
    }

    local msg group
    for group in left_arm right_arm both_arms; do
        if run "moveit $group" 0 "moveit_$group" -- \
                ros2 run baxter_examples moveit_tiny --ros-args -p group:="$group"; then
            if msg=$(assert_motion "$LOGDIR/moveit_$group.log" 2); then
                pass "moveit $group (<= ${MAX_ERROR_RAD} rad)"
            else
                fail "moveit $group" "$msg"
            fi
        fi
    done

    if run "moveit_pose delta_z" 0 moveit_pose -- \
            ros2 run baxter_examples moveit_pose --ros-args \
            -p group:=left_arm -p delta_z:=0.05; then
        if grep -q 'pose goal reached' "$LOGDIR/moveit_pose.log"; then
            pass "moveit_pose delta_z"
        else
            fail "moveit_pose delta_z" "no 'pose goal reached' line"
        fi
    fi

    # plan_only must plan and stop. If it reports execution, the flag is dead.
    if run "moveit_pose plan_only" 0 moveit_plan_only -- \
            ros2 run baxter_examples moveit_pose --ros-args \
            -p group:=left_arm -p delta_z:=0.05 -p plan_only:=true; then
        if grep -q 'pose plan succeeded' "$LOGDIR/moveit_plan_only.log" \
                && ! grep -q 'pose goal reached' "$LOGDIR/moveit_plan_only.log"; then
            pass "moveit_pose plan_only (planned, did not execute)"
        else
            fail "moveit_pose plan_only" "planned-only run reported execution"
        fi
    fi

    run "ik reachable" 0 ik_ok -- \
        ros2 run baxter_examples ik_service_client --ros-args -p limb:=left \
        && pass "ik reachable"

    # A solver that never fails is not a solver.
    if run "ik unreachable rejected" 1 ik_bad -- \
            ros2 run baxter_examples ik_service_client --ros-args \
            -p limb:=left -p x:=9.0; then
        if grep -q 'INVALID POSE' "$LOGDIR/ik_bad.log"; then
            pass "ik unreachable rejected"
        else
            fail "ik unreachable rejected" "exited 1 without the invalid-pose message"
        fi
    fi

    if run "moveit cancel and hold" 0 moveit_cancel -- \
            ros2 run baxter_examples moveit_tiny --ros-args -p cancel_after_sec:=1.0; then
        if ! grep -q 'MoveGroup goal canceled; holding position' "$LOGDIR/moveit_cancel.log"; then
            fail "moveit cancel and hold" "expected cancel log line absent"
        elif msg=$(assert_drift "$LOGDIR/moveit_cancel.log"); then
            pass "moveit cancel and hold"
        else
            fail "moveit cancel and hold" "$msg"
        fi
    fi

    teardown_check "moveit"
}

# --------------------------------------------------------------------------

case "$MODE" in
    gates)  run_gates ;;
    gazebo) run_gazebo ;;
    moveit) run_moveit ;;
    all)    run_gates; run_gazebo; run_moveit ;;
    *) echo "usage: $0 [gates|gazebo|moveit|all]" >&2; exit 2 ;;
esac

echo
echo "=== summary ==="
printf '%s\n' "${RESULTS[@]}"
echo "--- $PASSED passed, $FAILED failed ---"

if [ "$FAILED" -gt 0 ]; then
    echo "logs: $LOGDIR" >&2
    exit 1
fi
rm -rf "$LOGDIR"
exit 0
