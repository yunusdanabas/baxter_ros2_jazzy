# Baxter Session Plan — run the tests, read the results, harvest improvements

Ordered phases for a supervised session with the real robot. Commands are **not**
duplicated here — `docs/hardware_test_commands.md` is the copy-paste sheet and this
document says which section to run, in what order, and what to do when it goes wrong.
Background and safety: `docs/hardware_runbook.md`.

**Goal:** validate the command path on hardware, get real motion, and come away with a
list of concrete code improvements. Not a data archive — recordings are short and
topic-scoped, taken only where a number is needed that cannot be read off the console.

**Where we resume:** I12 and I20 are done on BR-01 `011412P0024`. Open supervised
experiments: raising `path_tolerance_rad` (0.3–0.4), and the left/right `w0`
abort compare (see `hardware_test_commands.md`). P3 untuck is routine.

## Standing rules

- **`export BAXTER_HOST=<robot-serial>.local` then source `scripts/baxter_env.sh`
  in every terminal.** Scripts have no lab serial/IP default. The env script
  strips an active conda install from `PATH`; without it `py_bridge.py` dies on
  `rclpy._rclpy_pybind11`. Source it before `colcon build` too — see the runbook.
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
`baxter-noetic` image on the **host** daemon — if a prune removed it again, rebuild it
from the separate ROS 1 workspace that owns it. What still needs that image (and why
untuck does) is summarised in `docs/hardware_runbook.md`.

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

## P3 — Enable and untuck (~30 min; was the blocker, now routine)

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
`docs/hardware_runbook.md` (Noetic image section).

## P4 — Supervised motion gate, I12 (~45 min)

Sheet §7, then §7b. Scoped recording on — this is where the tracking numbers come from.

1. `sim_tiny_trajectory`, both arms, out and back (`s1` by 0.35 rad over 3 s at
   `speed_ratio` 0.1).
2. Cancel-and-hold: same client with `cancel_after_sec:=1.0`.

**Pass:** goals succeed *with feedback*; small `max_error`; on cancel the arm stops and
**holds**, does not sag. A tolerance abort is not a failure — it routes to P5.
**Abort:** anything unexpected → e-stop.

## P4a — Fast motion — **characterised, do not re-run blind** (~45 min)

Measured 2026-07-25 (I20). Kept because the escalation procedure is the reusable
part; the answer itself is now settled.

| Step | `offset` | `duration` | rad/s | measured max lag |
|---|---|---|---|---|
| 1 | 0.35 | 3.0 | 0.12 | 0.037 rad |
| 2 | 0.35 | 1.5 | 0.23 | 0.094 rad |
| 3 | 0.50 | 1.0 | 0.50 | **0.198 rad → ABORT** |
| 4 | 0.50 | 0.5 | 1.00 | not reached |
| 5 | 0.50 | 0.35 | 1.43 | not reached |

It stopped at step 3 with `Path tolerance violated: left_s1 lags its setpoint by
0.202 rad (limit 0.200)`, then held to 0.0004 rad over 6 s — the abort-and-hold
path works.

The result is a straight line: **lag ≈ 0.4 s × commanded velocity.** The arm runs
a constant time behind its setpoint, so `path_tolerance_rad` is a speed limit in
disguise: 0.2 rad ÷ 0.4 s ≈ 0.5 rad/s. The 2.0 rad/s per-cycle clamp is
unreachable — the tolerance binds four times sooner.

**Re-run this ladder only** if something changed that should move that line:
control rate, `speed_ratio` semantics, or a stiffer hold. Otherwise spend the
time on the open experiment at the other end — what raising `path_tolerance_rad`
to 0.3-0.4 buys, and whether tracking is still safe there.

If you do escalate: one step at a time, recorder on, checking the arm between
runs. **Stop** on the first path-tolerance abort, visible stutter, or audible
change in the arm. **Abort to e-stop** on anything unexpected.

## P5 — Tolerance characterisation (~45 min)

`path_tolerance_rad=0.2` and `stopped_velocity_tolerance=0.25` are Rethink defaults,
desk-tuned here against a mock with no physics. Rather than only reacting to a trip,
**measure** from the P4 capture: worst lag between `joint_command` and `joint_states`
(cross-checked against `/robot/ref_joint_states`), and joint velocity at goal end.

**Do not tighten `path_tolerance_rad`.** I20 showed it *is* the speed limit
(~0.5 rad/s at 0.2). Raising it to 0.3–0.4 is the open experiment for a future
supervised session, not a desk default. A trip at low speed is still more likely
bridge backpressure (F8) — `ROS1Publisher.publish` can block up to 0.5 s inside
the ROS 2 callback, which exceeds the robot's 0.2 s `joint_command_timeout`.

**Abort:** a trip on a move the arm visibly completed → stop commanding motion and
capture for desk analysis rather than loosening the limit.

## P6 — Motion experiments, as far as they teach something

Escalate, checking the arm between steps, recording only the runs being compared:

1. **Cancel sweep** — `cancel_after_sec` 0.5, 1.0, 2.0. Skipped on 2026-07-24
   because the check itself was broken (F2); fixed 2026-07-25, so this is now
   worth running.
2. **Gravity-comp observation** — enabled but uncommanded; how far does the arm drift?
3. **`joint_command_timeout` transition**, supervised, once: stop the shims and watch
   the arm go from held to gravity-comp.

A `speed_ratio` sweep is *closed*: 0.1 → 0.2 → 0.3 had no measurable effect (F9).
Duration is the binding constraint — that is what P4a measured.

Log one line per run: time, speed ratio, params, what the arm looked like.

**Improvement hooks:** does the 100 Hz command rate hold under load? Does the per-cycle
clamp ever bind? Is `speed_ratio` 0.1 unnecessarily slow for real work?

## P7 — MoveIt on hardware (re-run; first passed 2026-07-24)

`ros2 launch baxter_moveit_config hardware_moveit.launch.py`, plan in the RViz
MotionPlanning panel, **inspect the preview**, then Execute. Trajectories go through
the same shims, so validation, safety gate and clamp still apply.

`moveit_left_tiny` cannot drive this — it refuses unless move_group is on simulated
time, deliberately.

Executed on hardware 2026-07-24: planner SUCCESS, 31 waypoints, no tolerance abort,
settling 0.0128 rad from target. Re-run it this session because the bridge now
publishes the robot's own `header.stamp` rather than bridge receive time — if the
robot's clock and this laptop's disagree, MoveIt will discard states as stale.
`py_bridge` warns when the skew exceeds 0.5 s; watch for that at bring-up.

**Result 2026-07-25 (I20 F-F):** the staleness check passed — zero staleness
complaints. The *motion* did not. Across 11 goals per arm the left arm aborted 8,
all `PATH_TOLERANCE_VIOLATED` at exactly the limit on `left_w0`/`left_e0`, while
the right completed 9 of 11 on the same `both_arms` plans. Use
`Velocity Scaling: 0.1` and single-arm groups on this robot. The next session's
job is the `left_w0` vs `right_w0` compare below, **with the recorder running** —
it was not, which is why this is still undecided.

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
| P4 | Does the gate still pass after the 2026-07-25 changes? | Stop; a regression in the command path outranks every experiment below |
| P4a | Does tracking hold as speed rises? | Record the step that broke it and stop escalating — that number is the point of the session |
| — | Time running short? | Protect P4a and P9; P6 is the droppable one. P7 is no longer droppable — it is where the open left-arm defect shows up, and it needs the recorder on |

## Reading the results

Python `rosbags` reads ROS 1 `.bag` and ROS 2 mcap through one API. Tracking error:
`joint_command` against `joint_states`, cross-checked against `/robot/ref_joint_states`.
Bridge latency: match the same `/robot/joint_states` message across the two
captures by `header.stamp` — this works again now that the bridge preserves the
robot's stamp instead of overwriting it — then take the difference of the two bags'
**receive** times. The stamps themselves are now identical on both sides by
construction, so they identify the message; they no longer measure the delay. Drops: compare
message counts for the same topic across the two sides.
