# I19 — Backlog plan (post-2026-07-24 hardware session)

Persistent handoff for the improvement backlog produced by the I18 hardware
session. All items here are **desk work — no robot needed**. Full evidence for
each is in `logs/I18_hardware_day.log.md` under the cited F-number.

Branch `i17-pre-hardware-hardening`, currently at `7748197`. `dry_run_test` 25/25.
Robot is idle: disabled, tucked, sonar off, powered on.

**2026-07-25 desk session:** items 1, 10, 3, 5, 6, 7 all landed, one commit each,
plus `b4a3e5a` (sourcing `baxter_env.sh` under `set -e` killed the caller
whenever the robot was offline, which blocked `test_bridge_loopback.sh` on any
desk day). Only item 9 is left here; everything else now needs the robot.

**2026-07-25 robot session (I20):** items 1, 2 and 3 of the queue below are
**done** — fast-motion tracking measured to the abort point, a fresh capture
analysed as `|command − measured|`, and MoveIt's planning scene verified against
the live robot. Item 9 is **closed**: the re-run was done headlessly and the
matrix deliberately not adopted. See `logs/I20_fast_motion_and_srdf.log.md`.

Original queue, kept for the record:
1. Fast-motion tracking: `sim_tiny_trajectory -p duration:=… -p offset:=…`
   walked up toward the 2.0 rad/s clamp. This is what gates any tightening of
   `path_tolerance_rad` (item 4 was closed on gentle-motion data only).
2. Short capture with the fixed bridge, then switch `analyze_tracking_lag.py`
   to `|command − measured|` — the I12 bag still has the empty schema baked in.
3. MoveIt against hardware after item 3. Watch for the new clock-skew warning
   from `py_bridge`: if the robot and the workstation disagree by more than
   0.5 s, MoveIt will discard states as stale and the warning says so.

## Backlog status

| # | Item | Where | Status |
|---|---|---|---|
| 1 | Reject a second `/robot/state` publisher before arming | `safety.py`, `hardware_bringup.launch.py` (F1) | **done** — `dry_run_test` 25/25 |
| 10 | Advertise real md5sum + msgdef on ROS 1 publishers | `py_bridge.py` `ROS1Publisher` (F23) | **done** (d801a7a) — rosbag decodes |
| 3 | Preserve the robot's `header.stamp` | `py_bridge.py` (F14) | **done** (3c802b8) |
| 5 | Cancel-hold check needs a settle window | `sim_tiny_trajectory.py:133-142` (F2) | **done** (41cd5f7) |
| 6 | `duration` parameter on `sim_tiny_trajectory` | (F9) | **done** (d445baa) — `duration`, `offset` |
| 7 | Guard the double `rclpy.shutdown()` | `py_bridge.py` (F17) | **done** (7748197) |
| 9 | Full MoveIt Setup Assistant re-run | `baxter.srdf` (F18) | open — needs its own session |
| 2 | Subscribe to all publishers of a ROS 1 topic | `py_bridge.py` | **done** (e543449) |
| 4 | Tighten `path_tolerance_rad` | — | **closed** — measured 0.0352 rad in-flight; leave at 0.2 (F22) |
| 8 | MoveIt on hardware | shim + SRDF | **done** (fae0a22, e543449) |

## Recommended order and detail

### 1 — Second-publisher guard (SAFETY, do first) — F1

We hit this failure twice in one session: a stale `mock_baxter_robot`, then
orphaned shims, each publishing a competing `/robot/state` while the graph looked
healthy. A mock advertising "safe" alongside the real disabled state can make the
safety gate accept a goal it must reject.

- `src/baxter_hardware_bridge/baxter_hardware_bridge/safety.py`: in
  `SafetyStateChecker`, count publishers on `/robot/state`
  (`node.count_publishers("/robot/state")`) and make `is_safe_for_motion()`
  return False (and `describe()` say so) when the count is not exactly 1.
- `src/baxter_hardware_bridge/launch/hardware_bringup.launch.py`: refuse to start
  if a `mock_baxter_robot` node is present. Simplest: an `OpaqueFunction` that
  checks the node list, or a one-shot check node that shuts the launch down.
- `dry_run_test`: the mock *is* the single publisher there, so add a case that
  spins up a second AssemblyState publisher and asserts `safe_for_motion` flips
  to False. Suite → 25.

### 10 — Real md5sum + message definition on publish — F23

`ROS1Publisher` advertises `md5sum "*"` with no message definition, so rosbag
records our `joint_command` (and the other published topics) with an empty schema
that cannot be deserialised afterwards — it forced the N2 analysis onto
`ref_joint_states`. The wildcard is correct and useful on the *subscribe* side
(lets the bridge take any type with no schema); only the publish side needs real
metadata.

- `scripts/py_bridge.py` `ROS1Publisher` / `_build_tcpros_header`: for the handful
  of published types (`baxter_core_msgs/JointCommand`, `std_msgs/Float64`,
  `std_msgs/Bool`, `std_msgs/Empty`), send the real md5sum and `message_definition`
  in the connection header. Hardcode the four; do not build a general msgdef
  system.
- Verify by re-running `scripts/analyze_tracking_lag.py` against a fresh short
  capture and confirming `joint_command` now decodes, then switch that script to
  read `|command − measured|` directly (its header notes this).
- `scripts/test_bridge_loopback.sh` still passes.

### 3 — Preserve `header.stamp` — F14

`_flush_ros2_queue` overwrites every JointState stamp with bridge receive time,
destroying the robot's sample time and breaking cross-bag latency work. Keep the
original: publish the robot's stamp, and if a receive-time signal is wanted, add
it elsewhere rather than clobbering. Check the shim's `joint_states_stale_sec`
logic still behaves (it currently measures bridge timing).

### 5 — Cancel-hold settle window — F2

`sim_tiny_trajectory.py:133-142` compares two consecutive joint states right after
cancel, so on a real arm it measures the settle transient (~0.02 rad) and
false-fails. Reuse the settle-window loop the same file already has for goal
completion (around `sim_tiny_trajectory.py:226-254`, `SETTLE_TIMEOUT_SEC`).

### 6 — `duration` parameter on `sim_tiny_trajectory` — F9

Distance and duration are hardcoded, so no run approaches the 2.0 rad/s clamp and
all tolerance numbers describe gentle motion only. Add a `duration` (and/or
`offset`) ros-param so a future session can stress tracking near the clamp. This
gates any claim about fast motion and any tightening of `path_tolerance_rad`.

### 7 — Guard the double `rclpy.shutdown()` — F17

`py_bridge.py` calls `rclpy.shutdown()` on both the signal path and the `atexit`
handler, throwing `RCLError: rcl_shutdown already called` and exit 1 on every
clean stop. Guard with `if rclpy.ok():` or a shutdown flag, so a real shutdown
error is not buried under a guaranteed traceback.

### 9 — Full MoveIt Setup Assistant re-run — F18 (own session)

The SRDF has only 52 `disable_collisions` pairs; we hand-added the one that bit
(`left/right_upper_shoulder ↔ upper_elbow`, 1.7 mm false positive). A full Setup
Assistant re-run against the current model would likely find more. Larger, GUI,
verify against known-good poses afterwards — schedule separately.

## Verification (whole batch)

1. `ros2 run baxter_hardware_bridge dry_run_test` → `OVERALL: PASS`, 25/25 after
   item 1.
2. `bash scripts/test_bridge_loopback.sh` → PASS after any `py_bridge.py` change.
3. `scripts/analyze_tracking_lag.py` decodes `joint_command` after item 10.
4. Colcon build clean: `colcon build --base-paths src --symlink-install
   --packages-skip baxter_bridge` (source `scripts/baxter_env.sh` FIRST — the
   conda-shebang trap, F6).
5. Mock rehearsal unaffected: `dry_run.launch.py mock_mode:=false` +
   `sim_tiny_trajectory` still verifies both arms.

## Watch-outs carried from I18

- **Always `source scripts/baxter_env.sh` before build and run** — conda shadows
  the system python3 and poisons entry-point shebangs (F6).
- **Kill by explicit PID, never `pkill -f`** — it matches its own shell (F12).
- **After stopping anything, confirm the ROS 2 graph is clean** (`ros2 node list`)
  before trusting a state reading — stale publishers lie convincingly (F1).
- **`baxter-noetic:n07` on the HOST docker daemon** is what the robot path needs;
  a `docker prune` removed it once, rebuilt per `docker/local_image_inventory.md`.
