# Sim Test — Command Sheet

Copy-paste sheet for verifying this workspace **without a robot**. Sections 1-2
need no GPU and are exactly what CI runs; sections 3-5 need a local Gazebo/RViz
session but still no Baxter.

The hardware counterpart is [hardware_test_commands.md](hardware_test_commands.md).
Do not run anything from that sheet to test a change — it commands a real arm.

## Run it all at once

`scripts/sim_smoke.sh` automates §2–§5, asserts the numbers rather than just the
exit codes, and fails if teardown leaves a process behind:

```bash
bash scripts/sim_smoke.sh          # gates + gazebo + moveit, ~4 min
bash scripts/sim_smoke.sh gates    # no Gazebo needed
```

Exit 0 only if every check passed; on failure it prints the log directory. The
sheet below stays the reference for what each check *means* and for the RViz
panel checks, which need eyes and are not automated.

## 0. Standing rules

- **Run one simulation at a time.** Do not set `ROS_DOMAIN_ID` or `GZ_PARTITION`
  to work around that; forcing a domain is what silently split the bridge from
  the shim in an earlier session.
- **`LC_NUMERIC` must be `C` for anything that starts `rviz2`.** Qt calls
  `setlocale(LC_ALL, "")` before `rclcpp::init`, so under a comma-decimal locale
  rcl parses every double parameter as a string and `loadRobotModel` dies. The
  MoveIt launch pins it; check yours with `locale` if RViz misbehaves. See
  [known_issues.md](known_issues.md).
- Source the underlay in **every** terminal:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
export ROS2CLI_NO_DAEMON=1
```

## 1. Build

From the repository root. Remove the generated directories first if the
workspace or its underlay changed — never hand-edit generated setup files.

```bash
rm -rf build install log
conda deactivate 2>/dev/null            # see below
source /opt/ros/jazzy/setup.bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

**Check `python3` before building.** An active conda/mamba environment puts its
own interpreter first, and `rclpy`'s C extension is built for the system
python3.12 — so the generated console scripts get a conda shebang and die on
`No module named 'rclpy._rclpy_pybind11'`. A build that succeeds does not rule
this out; the failure appears at run time.

```bash
which python3
# want: /usr/bin/python3   (not .../mambaforge/bin/python3 or any env)
```

`conda deactivate` is enough. Do **not** use `scripts/baxter_env.sh` for this —
it is a hardware-session script and refuses to run without `BAXTER_HOST`.

Verify the pin rather than re-importing over local changes:

```bash
git -C src/baxter_common_ros2 rev-parse HEAD
# expect: 678bfabea8c895b4134951a6c076217a90b9e0e6
```

## 2. Hardware-free gates

Everything here mirrors a step in `.github/workflows/ci.yml`. Each line's
expected token is what CI prints on success.

### 2a. Publish hygiene

```bash
grep -RIn '@example\.com' src --include='package.xml' SECURITY.md CODE_OF_CONDUCT.md
# expect: no output (grep exits 1)
```

### 2b. Compile, lint, unit tests

```bash
python3 -m compileall -q src/baxter_bringup src/baxter_gz_sim \
    src/baxter_moveit_config src/baxter_examples src/baxter_hardware_bridge

ruff check --select F src scripts --exclude src/baxter_common_ros2
# expect: All checks passed!

colcon test --base-paths src --packages-select baxter_examples
colcon test-result --verbose
# expect: Summary: 16 tests, 0 errors, 0 failures, 0 skipped
```

`ruff` is restricted to the `F` rules on purpose: `F401` unused import and `F821`
undefined name. `compileall` and the import checks below both pass happily on an
unused import, which is how nine orphaned imports once survived a refactor.

`ruff` is not a ROS package and is not installed by `rosdep` — get it with
`pipx install ruff` (which is what CI does). It is a standalone binary that needs
neither the ROS environment nor the system python3, so if yours lives inside a
conda env it is fine to call it by its full path after deactivating.

### 2c. Import and cleanup-handler checks

These are two inline `python3` blocks in `ci.yml` ("Python compile and import
checks"). Run them from there rather than keeping a second copy in sync:

```bash
python3 - <<'PY'
import importlib
for name in ('baxter_examples.trajectory_helpers', 'baxter_examples.sim_tiny_trajectory',
             'baxter_examples.moveit_left_tiny', 'baxter_examples.moveit_pose',
             'baxter_examples.ik_service_client'):
    importlib.import_module(name)
print('python_import_checks=passed (package imports)')
PY
```

The AST guard checks that no `except BaseException` handler calls
`_cancel_active_goal()` unguarded — a failing cancel there would replace the
exception `main()` dispatches on, turning Ctrl-C into a misleading "Exception"
path. It inspects 3 handlers and prints `cleanup_handler_checks=passed`.

### 2d. Hardware bridge dry-run

The 25-case self-test for the action shim, safety gate and mock robot. No robot,
no bridge, no ROS 1.

```bash
ros2 run baxter_hardware_bridge dry_run_test
# expect the last line: OVERALL PASS 25/25
```

Anything other than 25/25 is a stop.

### 2e. Model and MoveIt config

```bash
ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro > /tmp/baxter_gz_control.urdf
check_urdf /tmp/baxter_gz_control.urdf
# expect: "Successfully Parsed XML", root link world, 17 independent joints
```

The SRDF collision matrix is the one number worth checking by hand — three docs
promise it:

```bash
python3 - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

srdf = Path(get_package_share_directory('baxter_moveit_config')) / 'config' / 'baxter.srdf'
pairs = {tuple(sorted((c.attrib['link1'], c.attrib['link2'])))
         for c in ET.parse(srdf).getroot().findall('disable_collisions')}
for required in (('left_upper_elbow', 'left_upper_shoulder'),
                 ('right_upper_elbow', 'right_upper_shoulder')):
    assert required in pairs, f'hand-added pair lost: {required}'
print(f'acm_pairs={len(pairs)}')
PY
# expect: acm_pairs=54
```

Those two hand-added pairs must stay disabled. Links two apart in the chain graze
by 1.7 mm at the pose `tuck_arms.py -u` leaves the robot in, which made
`move_group` return `-10 START_STATE_IN_COLLISION` on hardware. The Setup
Assistant cannot rediscover them — its sampling does not converge for this robot
— so a regenerated matrix drops them and the planner then refuses the robot's own
untuck pose. `scripts/check_srdf.py diff OLD NEW` is the same guard for comparing
two SRDF files; `scripts/check_srdf.py poses` asks a running `move_group` whether
the known-good poses are collision-free.

## 3. Gazebo smoke

Terminal 1 — leave running:

```bash
ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false
```

Use `ros2 launch baxter_gz_sim sim.launch.py headless:=true` instead if you have
no GPU; everything in this section except the RViz check still applies.

Terminal 2:

```bash
ros2 control list_controllers
# expect 3 active: joint_state_broadcaster, left_arm_controller, right_arm_controller

ros2 topic echo /joint_states --once
# expect 17 joints with advancing stamps: 14 arm + head_pan + 2 gripper fingers
```

### 3a. Reversible motion, both arms

```bash
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Pass: each arm takes a fresh start position, makes a visible limit-safe move, and
returns, with outbound and return `max_error <= 0.02 rad`. Action success without
the fresh final-state check is a failure.

### 3b. A joint other than the default

`joint` selects which joint moves (default `s1`). Comparing the *same* joint on
both arms is what distinguishes an asymmetric plan from an asymmetric arm.

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true -p joint:=e1
```

`duration` (default 3.0 s) and `offset` (default 0.35 rad) set how far and how
fast; the per-move log line reports the resulting rad/s.

### 3c. Cancel and hold

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
    -p use_sim_time:=true -p cancel_after_sec:=1.0
```

Pass: `Controller goal canceled; holding position`, a bounded exit, no traceback,
and the arm holds rather than sagging.

## 4. MoveIt smoke

Terminal 1 — leave running. Stop the section 3 launch first:

```bash
ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false
```

Wait for `You can start planning now!` with pipeline `ompl`.

Terminal 2:

```bash
ros2 action list                                    # expect /move_action
ros2 run baxter_examples moveit_left_tiny
ros2 run baxter_examples moveit_tiny --ros-args -p group:=right_arm
ros2 run baxter_examples moveit_tiny --ros-args -p group:=both_arms
ros2 run baxter_examples moveit_pose --ros-args -p group:=left_arm -p delta_z:=0.05
ros2 run baxter_examples ik_service_client --ros-args -p limb:=left
ros2 run baxter_examples ik_service_client --ros-args -p limb:=left -p x:=9.0   # expect exit 1
```

`moveit_tiny` is the same entry point as `moveit_left_tiny`, kept because the
guides name it. `moveit_pose` also takes `plan_only:=true`, which plans and
reports the result without executing — the safe way to check a pose is reachable.

Pass criteria:

```text
left, right and both-arm outbound/return max_error <= 0.02 rad
moveit_pose reaches both absolute and delta targets
ik_service_client solves left/right and exits non-zero on an unreachable pose
no missing head/source-finger state warning
motion visible in Gazebo, robot visible in RViz via RobotModel/TF
OMPL and RRTConnectkConfigDefault available in MotionPlanning
```

The MotionPlanning panel must load: no `Exception caught while processing action
'loadRobotModel'`, a populated planner dropdown instead of `NO PLANNING LIBRARY
LOADED`, a 6-DOF interactive marker on each gripper, and no `No robot state or
robot model loaded`. A comma-decimal `LC_NUMERIC` triggers all four at once.

Cancellation:

```bash
ros2 run baxter_examples moveit_tiny --ros-args -p cancel_after_sec:=1.0
# expect: MoveGroup goal canceled; holding position
```

## 5. Teardown

Send **one** Ctrl+C to the owning launch, wait, then confirm nothing survived:

```bash
pgrep -a -f 'gz sim|ros_gz_bridge|move_group|rviz2|robot_state_publisher|ros2_control_node'
# expect: no output
```

Gazebo exiting `-2` after one SIGINT is expected. A hang, a leftover process, or
a `move_group` crash is a **gate failure** — do not `pkill -9` and call it clean.
If you do have to kill something, re-check for orphans before the next launch;
leftovers from a previous run look exactly like a teardown failure in the next
one.

## What this sheet does not cover

The hardware bridge against a real robot, ROS 1 / Noetic anything, grippers,
cameras, and the Zenoh fallback. `baxter_bridge` is deliberately skipped in the
default build — it links ROS 1 libraries that do not exist on a clean
Jazzy/Noble machine. See [support_matrix.md](support_matrix.md).
