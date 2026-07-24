# Baxter Session Plan — run the tests, read the results, harvest improvements

Ordered phases for a supervised session with the real robot. Commands are **not**
duplicated here — `docs/hardware_test_commands.md` is the copy-paste sheet and this
document says which section to run, in what order, and what to do when it goes wrong.
Background and safety: `docs/hardware_runbook.md`.

**Goal:** validate the command path on hardware, get real motion, and come away with a
list of concrete code improvements. Not a data archive — recordings are short and
topic-scoped, taken only where a number is needed that cannot be read off the console.

**Where we resume:** the 2026-07-22 session ended blocked — `enable_robot.py -e` fails
from the tucked pose because a latched `left_s1` collision force-field cannot
self-clear while the robot is disabled. P3 is the crux; everything after it depends
on it.

## Verified before this session (2026-07-24)

| Check | Result |
|---|---|
| Robot reachable | `011412P0024.local` → `192.168.1.232`, via `enp4s0`, 0.36 ms RTT |
| Robot baseline | `ready/enabled/stopped/error` all `False`, `estop_button: 0` — disabled, fault-free |
| `dry_run_test` | 20/20 PASS |
| Shims under launch | all nodes up, no rclpy errors |
| Recorders | both paths proven (full, and `TOPICS_RE`-scoped) |
| `baxter-noetic:n07` | rebuilt on the **host** daemon; `enable_robot.py -s` works through it |

## Standing rules

- **Source `scripts/baxter_env.sh` in every terminal.** It strips an active conda
  install from `PATH`; without it `py_bridge.py` dies on `rclpy._rclpy_pybind11`.
  Source it before `colcon build` too — see the runbook prerequisites.
- **Head sonar off for the whole session** (P1), re-checked after any robot reboot.
  With it off there is no proximity sensing, so the e-stop and human supervision are
  the only backstops.
- **E-stop in hand from P3 onward.** Workspace clear, nobody within arm reach.
  Anything unexpected during motion → hit the physical e-stop.
- Never publish to `/robot/set_super_enable` outside the documented P3 exception, nor
  to `/robot/set_super_stop` for routine cancellation.
- Grippers are observe-only.

## Terminal layout

| # | Purpose | Command |
|---|---|---|
| 1 | Bridge (leave running) | `python3 scripts/py_bridge.py` |
| 2 | Shims (leave running) | `ros2 launch baxter_hardware_bridge hardware_bringup.launch.py` |
| 3 | Working terminal — clients, `baxrun`/`baxtool` | — |
| 4 | Scoped recorder, started per phase | `bash scripts/record_ros1.sh` / `record_ros2.sh` |

Define `baxrun`/`baxtool` in terminal 3 (`hardware_test_commands.md` §6). They need the
`baxter-noetic` image on the **host** daemon — if a prune removed it again, rebuild per
`docker/local_image_inventory.md`; `docs/container_free_path.md` records what could
replace the container and why the untuck currently cannot.

---

## P1 — Bring-up (~15 min)

Sheet §0–4, in this order: network pre-flight → bridge → **sonar off** → non-motion
check → shims.

```bash
python3 scripts/sonar_ctl.py off
python3 scripts/sonar_ctl.py status   # confirm the bitmask landed (0)
```

**Pass:** bridged topics arrive at a steady rate; both `follow_joint_trajectory`
action servers advertise. **Abort** on `deserialize failed` — that is a wire-layout
mismatch, not a transient.

Capture the baseline: initial `/robot/state` and the tucked joint positions.

## P2 — Safety interlocks, zero motion (~15 min)

Sheet §5 (5a–5c) and §5d, robot still disabled: bad joint names, wrong position count,
valid goal blocked by the safety gate, `t=0` first point, out-of-limits position,
over-velocity segment, over-clamp segment, stale joint states.

No recording — the console is the result.

**Pass:** every goal rejected with the expected reason.
**Abort the session** if any goal is *accepted* while the robot is disabled; that is
the interlock every later phase depends on.
**Improvement hook:** any rejection message that would not tell you what to fix.

## P3 — Enable and untuck (the blocker) (~45 min)

**Large whole-arm motion. Clear workspace, e-stop in hand.** Sheet §6.

Start a scoped ROS 1 capture *before* the attempt — `/robot/state`, the collision-state
topics and `/diagnostics`. The force-field payload is the evidence either outcome
depends on:

```bash
TOPICS_RE='/robot/state|/diagnostics|/robot/limb/.*/collision_.*_state' bash scripts/record_ros1.sh
```

Primary: `baxtool tuck_arms.py -u`.

1. **Untuck completes** → verify by arm **position** (`s1 ≈ -1.0`), *not* the enable
   flag: `tuck_arms.py` disables on exit if a collision flag remains, so a successful
   untuck can end `enabled: False`. Re-enable, then confirm
   `ros2 run baxter_hardware_bridge baxter_safety_check` → `safe_for_motion=True`. → P4.
2. **Hangs without enabling** → supervised manual collision-suppression procedure
   (sheet §6, four terminals, 15 s cap). Do **not** re-check homing, calibration or
   health — the 2026-07-22 sweep cleared all three.
3. **Still disabled** → **pivot**: skip P4–P7 and go to P8. Understanding *why* it will
   not enable is the most valuable thing this session can produce.

**Improvement hook:** if `tuck_arms.py -u` works where `enable_robot.py -e` fails, that
20 Hz republish plus collision suppression belongs in our own enable path — see
`container_free_path.md`.

## P4 — Supervised motion gate, I12 (~45 min)

Sheet §7, then §7b. Scoped recording on — this is where the tracking numbers come from.

1. `sim_tiny_trajectory`, both arms, out and back (`s1` by 0.35 rad over 3 s at
   `speed_ratio` 0.1).
2. Cancel-and-hold: same client with `cancel_after_sec:=1.0`.

**Pass:** goals succeed *with feedback*; small `max_error`; on cancel the arm stops and
**holds**, does not sag. A tolerance abort is not a failure — it routes to P5.
**Abort:** anything unexpected → e-stop.

## P5 — Tolerance characterisation (~45 min)

`path_tolerance_rad=0.2` and `stopped_velocity_tolerance=0.25` are Rethink defaults,
desk-tuned here against a mock with no physics. Rather than only reacting to a trip,
**measure** from the P4 capture: worst lag between `joint_command` and `joint_states`
(cross-checked against `/robot/ref_joint_states`), and joint velocity at goal end.

If P4 tripped on a move the arm visibly completed, relaunch the shims with
`-p path_tolerance_rad:=0.3` and converge on the **loosest value that still passes**.

**Abort:** still tripping at 0.3 with visible lag → not a tolerance problem, suspect
bridge backpressure; stop commanding motion and capture for desk analysis.
**Improvement:** the winning values become the new shim defaults.

## P6 — Motion experiments, as far as they teach something

Escalate, checking the arm between steps, recording only the runs being compared:

1. **Speed sweep** — `speed_ratio` 0.1 → 0.2 → 0.3 (a shim parameter; relaunch to
   change it). A few runs each: does tracking error grow with speed?
2. **Cancel sweep** — `cancel_after_sec` 0.5, 1.0, 2.0.
3. **Gravity-comp observation** — enabled but uncommanded; how far does the arm drift?
4. **`joint_command_timeout` transition**, supervised, once: stop the shims and watch
   the arm go from held to gravity-comp.

Log one line per run: time, speed ratio, params, what the arm looked like.

**Improvement hooks:** does the 100 Hz command rate hold under load? Does the per-cycle
clamp ever bind? Is `speed_ratio` 0.1 unnecessarily slow for real work?

## P7 — MoveIt on hardware (stretch, only if P4/P5 were clean)

`ros2 launch baxter_moveit_config hardware_moveit.launch.py`, plan in the RViz
MotionPlanning panel, **inspect the preview**, then Execute. Trajectories go through
the same shims, so validation, safety gate and clamp still apply.

`moveit_left_tiny` cannot drive this — it refuses unless move_group is on simulated
time, deliberately. Only the wiring is verified (move_group loads both shim action
servers), never execution.

## P8 — Noetic harvest and bridge hygiene, no motion (~45 min)

1. `rostopic hz` on `/robot/joint_states`, `/robot/ref_joint_states`, `/robot/state`,
   `joint_command`; `rosservice list`; `rosmsg show` for the messages a native stack
   must implement.
2. **Phantom-node check** — killed scripts historically left stale registrations. After
   stopping a bridge-side script, confirm `rosnode list` is clean.
3. Fill `docs/noetic_native_notes.md` while the robot is in front of you.

## P9 — Shutdown and write-up

`baxtool tuck_arms.py -t`, `baxtool enable_robot.py -d` (sheet §8). Close any recording
and verify the bags closed, then Ctrl-C the shims, then the bridge, in that order.

If a recorder was killed hard, the ROS 2 bag has no `metadata.yaml` and `ros2 bag info`
fails — `ros2 bag reindex <dir>` rebuilds it.

Then the actual deliverable: **the improvement list**, in `logs/I18_hardware_day.log.md`,
each item naming the observation behind it and the file it would change. Update the
sheet's "Where the last session stopped" (including sonar left off) and the gate-status
table.

## Decision points

| After | Question | If no |
|---|---|---|
| P3 | Can the robot be enabled at all? | Pivot to P8, skip motion entirely |
| P4 | Do the tolerances hold on a real arm? | P5 tuning; if that fails, stop motion and analyse |
| — | Time running short? | Stop new experiments and protect P8 and P9 |

## Reading the results

Python `rosbags` reads ROS 1 `.bag` and ROS 2 mcap through one API. Tracking error:
`joint_command` against `joint_states`, cross-checked against `/robot/ref_joint_states`.
Bridge latency: the same `/robot/joint_states` message in both captures matched by
`header.stamp` — both recorders run on this laptop, so the clocks agree. Drops: compare
message counts for the same topic across the two sides.
