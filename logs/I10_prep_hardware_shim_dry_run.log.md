---
step: I10-prep
title: "Hardware Action Shim Dry-Run Prep"
agent_date: 2026-07-09
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09, I14]
---

# I10-prep: Hardware Action Shim Dry-Run Prep

## Task

Created the `baxter_hardware_bridge` package with ROS 2 `FollowJointTrajectory` action shims, safety state checker, mock robot, and dry-run self-test. All code is hardware-free: no `baxter_bridge` build, no ROS 1 deps, no real robot access. This unblocks I11 implementation — when the bridge host is ready, only hardware integration and the I10 non-motion gate remain.

## Findings

Created `src/baxter_hardware_bridge/` as an ament_python package:

- `safety.py` — `SafetyStateChecker` subscribes to `/robot/state` (`baxter_core_msgs/AssemblyState`), provides `is_safe_for_motion()` (ready + enabled + not stopped + no error + no e-stop), `is_stale()`, `describe()`. CLI entry point `baxter_safety_check` prints state in a loop.
- `follow_joint_trajectory_shim.py` — `FollowJointTrajectoryShim` action server on `/robot/limb/{side}/follow_joint_trajectory` accepting `control_msgs/action/FollowJointTrajectory`:
  - Validates exact 7-joint Baxter names per arm (rejects mismatch).
  - Rejects goals when `/robot/state` is not safe for motion.
  - Publishes `baxter_core_msgs/JointCommand` (POSITION_MODE=1) to `/robot/limb/{side}/joint_command` at 100 Hz.
  - Publishes low `set_speed_ratio` (default 0.1) and `joint_command_timeout` (default 0.2s) on goal accept.
  - Linearly interpolates between trajectory points.
  - On cancel: holds current position via JointCommand (never calls `/robot/set_super_stop`).
  - On safety violation during execution: holds position and aborts.
  - `mock_mode` param skips JointCommand publishes for dry-run testing.
- `mock_robot.py` — publishes safe `/robot/state` and `/robot/joint_states` at 50/100 Hz. Echoes `JointCommand` into joint positions (feedthrough). `unsafe` param switches to stopped/e-stopped state for rejection testing.
- `dry_run_test.py` — in-process self-test using `MultiThreadedExecutor`:
  1. Safe state + correct joints → goal accepted + succeeded.
  2. Bad joint names → goal rejected.
  3. Unsafe state → goal rejected.
  Exit 0 on pass, 1 on fail.
- `launch/hardware_bringup.launch.py` — launches both arm shims with configurable speed_ratio, command_timeout, mock_mode.
- `launch/dry_run.launch.py` — launches mock_robot + both shims in mock_mode.

Build result:

```text
$ colcon build --base-paths src --packages-skip baxter_bridge
Summary: 9 packages finished [6.86s]
```

Dry-run gate evidence:

```text
$ source install/setup.bash && export ROS_DOMAIN_ID=99 && ros2 run baxter_hardware_bridge dry_run_test
[INFO] Test 1: safe state, correct joints
[INFO] Goal accepted
[INFO] Goal succeeded
[INFO] Test 2: bad joint names
[ERROR] Rejected: joint names mismatch. Expected ['left_s0', ...], got ['foo_s0', ...]
[INFO] Test 3: unsafe state
[ERROR] Rejected: robot not safe for motion: ready=False enabled=False stopped=True error=False estop_button=1 estop_source=1
[INFO] PASS: Test 1 goal succeeded
[INFO] PASS: Test 2 bad joints rejected
[INFO] PASS: Test 3 unsafe state rejected
[INFO] OVERALL: PASS
EXIT: 0
```

## Decisions

- Used ament_python (not ament_cmake) because the package has intra-package Python imports (`dry_run_test` imports `follow_joint_trajectory_shim` and `mock_robot`).
- Used `MultiThreadedExecutor` in the dry-run test to allow the action server's execute callback to run while subscriptions are still being processed.
- Kept `mock_mode` as a runtime parameter (not compile-time) so the same binary works for both dry-run and hardware.
- Default speed_ratio is 0.1 (10%) and command_timeout is 0.2s — conservative lab defaults from S04.
- The shim holds position on cancel by publishing a final JointCommand at current positions, per S04 rule: "Action shims should hold/cancel motion using JointCommand, not call /robot/set_super_stop for routine cancellation."
- Did not add `baxter_hardware_bridge` to the default CI workflow — it requires `baxter_core_msgs` which is available, but the package is hardware-scoped and should not be in the sim-first CI path.
- Sim baseline was committed as root commit `f150366` before this work to isolate hardware changes.

## Open Questions

- I10 still blocked: physical Baxter access, bridge host choice, university network policy.
- When the bridge host is ready, `baxter_bridge` must be built on that host (with ROS 1 deps from `baxter_legacy`), and the shim's `mock_mode` should be set to `false`.
- Bridge node namespace: ECN `baxter_bridge` forces `__ns:=/robot`, so its services are at `/robot/bridge_open` and `/robot/bridge_exists`, not `/bridge_open`.
- MoveIt hardware launch (`moveit_hardware.launch.py`) is deferred until I12 supervised motion passes.

## Artifacts

- `src/baxter_hardware_bridge/package.xml`
- `src/baxter_hardware_bridge/setup.py`
- `src/baxter_hardware_bridge/setup.cfg`
- `src/baxter_hardware_bridge/resource/baxter_hardware_bridge`
- `src/baxter_hardware_bridge/baxter_hardware_bridge/__init__.py`
- `src/baxter_hardware_bridge/baxter_hardware_bridge/safety.py`
- `src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py`
- `src/baxter_hardware_bridge/baxter_hardware_bridge/mock_robot.py`
- `src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py`
- `src/baxter_hardware_bridge/launch/hardware_bringup.launch.py`
- `src/baxter_hardware_bridge/launch/dry_run.launch.py`
- `logs/I10_prep_hardware_shim_dry_run.log.md`
- `MASTER_PLAN.md` (I10-prep status added)
- `PROMPTS.md` (I10-prep prompt and completion note appended)
