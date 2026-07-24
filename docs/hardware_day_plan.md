# Baxter Robot Day — Full-Day Plan

Schedule and decision points for a full day with the real robot. Commands are
**not** duplicated here — `docs/hardware_test_commands.md` is the copy-paste
sheet and this document tells you which section to run, when, and what to do
when it goes wrong. Background and safety rules: `docs/hardware_runbook.md`.

**Where we resume:** last session (2026-07-22) left the robot disabled, tucked,
sonar off, no motion performed. The I12 supervised-motion gate is **blocked** on
`enable_robot.py -e` failing from the tucked pose. Stage S2 is the crux of the
day — everything after it depends on the robot enabling.

## Standing rules

- E-stop in hand for every stage from S2 onward. Workspace clear.
- Recorders (`scripts/record_ros1.sh`, `scripts/record_ros2.sh`) run all day in
  their own terminals. Stop them at lunch and at shutdown with Ctrl-C so the
  bags close cleanly rather than being killed mid-write.
- Grippers are **observe-only** this session. Nothing commands them; their state
  is captured by the ROS 1 bag.
- **Disk space first.** Both recorders refuse to start below 10 GB free
  (`MIN_FREE_GB`). Check `df -h /` the day before — a full day of dual bags does
  not fit in a few GB, and running out mid-session loses the session.
- If a recorder is ever killed hard (SIGKILL, crash, power) instead of Ctrl-C,
  the ROS 2 bag is left without its `metadata.yaml` and `ros2 bag info` fails.
  The data is **not** lost: `ros2 bag reindex <bag_dir>` rebuilds it. Verified.
- Anything unexpected during motion → hit the physical e-stop. Full abort table
  in `hardware_test_commands.md` § "Abort procedures".

## Terminal layout

| # | What | Command |
|---|---|---|
| 1 | Bridge | `python3 scripts/py_bridge.py` |
| 2 | Shims | `ros2 launch baxter_hardware_bridge hardware_bringup.launch.py` |
| 3 | Working terminal (clients, `baxrun`/`baxtool`) | — |
| 4 | ROS 1 recorder | `bash scripts/record_ros1.sh` |
| 5 | ROS 2 recorder | `source scripts/baxter_env.sh && bash scripts/record_ros2.sh` |

Every terminal: `cd ~/baxter_ros2_jazzy && source scripts/baxter_env.sh` first.
Define `baxrun`/`baxtool` in terminal 3 (`hardware_test_commands.md` §6).

---

## S0 — Bring-up (09:00–09:30)

**Purpose:** get from cold laptop to a live, verified, recording session.

Run sheet §0 (network pre-flight — the route check is the one that actually
catches problems), §1 (env), §2 (bridge), §3 (sonar off), §4 (shims). Then start
both recorders (terminals 4 and 5) and confirm each printed its snapshot files.

**Abort criteria:** any pre-flight step fails → stop and fix the network. Do not
proceed with a half-working bridge; every later result becomes untrustworthy.

**Record:** the recorders' inventory snapshots (`topics_*.txt`, `nodes_*.txt`,
`params_*.yaml`) land automatically — this is the first Noetic-notes input.

**Noetic notes:** paste the topic/node counts and anything surprising in the
inventory into `docs/noetic_native_notes.md` § Inventory.

---

## S1 — I11 interlock re-verify (09:30–09:45)

**Purpose:** re-prove the safety gate on today's build before the robot can
move. Cheap, zero motion, and it catches a broken deploy early.

Run sheet §5 (5a–5c) and §5d, robot still disabled.

**Abort criteria:** any goal **accepted** while the robot is disabled → stop the
day and debug at the desk. This is the interlock that makes everything else safe.

**Record:** copy the rejection reasons verbatim into the day log.

---

## S2 — The enable fix (09:45–10:30)

**Purpose:** clear the latched `left_s1` collision force-field that blocked the
last session. This is the gate the whole day hangs on.

Primary: `baxtool tuck_arms.py -u` (sheet §6). **Untuck is a large whole-arm
motion** — clear the workspace first.

Decision tree:

1. **Untuck completes** → check arm positions, not the enable flag (a successful
   untuck can end `enabled: False` by design). If disabled, `baxtool
   enable_robot.py -e` should now succeed with the arms clear of the field.
   Confirm `baxter_safety_check` shows `safe_for_motion=True`. → S3.
2. **Hangs without enabling** → the collision-suppression theory is wrong. Do
   the supervised manual suppression procedure (sheet §6, four terminals, 15 s
   cap). Do **not** re-check homing, calibration or health — the 2026-07-22
   sweep already cleared those.
3. **Still disabled after both** → **pivot the day.** Do not burn hours on it.
   Go to S6 extended: harvest inventory, rates, params, diagnostics, sonar/IR
   and gripper-state bags. A full non-motion dataset plus complete Noetic notes
   is still a productive day, and it is exactly what the native ROS 1 stack
   needs. Skip S3–S5.

**Abort criteria:** untuck motion looks abnormal → e-stop.

**Record:** `/diagnostics` during the enable attempts is already in the ROS 1
bag. Note the wall-clock time of each attempt so it can be found in the bag.

**Noetic notes:** exact enable sequence and timing that worked — the native
stack has to reimplement this, and `enable_robot.py`'s single 2 s wait is
demonstrably not enough.

---

## S3 — I12 supervised motion gate (10:30–11:15)

**Purpose:** first real motion through the ROS 2 command path. Closes the gate
that has been blocked since 2026-07-22.

Run sheet §7 (`sim_tiny_trajectory`, both arms, out and back), then §7b
(`cancel_after_sec:=1.0`, cancel-and-hold).

**Abort criteria:** anything unexpected → e-stop. A path/goal **tolerance abort
is not a failure** — it routes to S4.

**Record:** per-arm `max_error` values; whether feedback messages appeared; on
cancel, whether the arm held or sagged.

**Noetic notes:** observed lag between command and motion; how the arm behaves
when a goal is cancelled.

---

## S4 — Tolerance tuning (11:15–12:00)

**Purpose:** `path_tolerance_rad=0.2` and `stopped_velocity_tolerance=0.25` were
tuned against a mock with no physics. A real series-elastic arm lags. Find the
values that hold on real hardware.

Only needed if S3 aborted on a move the arm visibly completed. Relaunch the
shims with `-p path_tolerance_rad:=0.3` (and `-p stopped_velocity_tolerance:=…`
if the goal check is what fired), then re-run §7. Converge on the **loosest
value that still passes**, not the first one that works.

**Abort criteria:** still tripping at 0.3 with visible arm lag → this is not a
tolerance problem, suspect bridge backpressure. Stop commanding motion, keep the
recorders running, and capture the state for desk analysis.

**Record:** every value tried and its result. The winning values go into the
shim defaults after the day — `record_ros2.sh` captures the live params with
each bag, so a recording is always matched to the tolerances that produced it.

---

## Lunch (12:00–12:45)

`baxtool enable_robot.py -d`. Ctrl-C both recorders and verify the bags closed
(`rosbag info` in the container / `ros2 bag info`). Restart recorders and
re-enable afterwards. This is deliberate crash-proofing: half the day's data is
now safely on disk.

---

## S5 — Motion experiments (12:45–15:30)

**Purpose:** generate the dataset that drives post-day code improvement. The
bags *are* the deliverable — command-vs-actual tracking and bridge latency both
fall out of data already being recorded on both sides.

Escalate, checking the arm after each step:

1. `sim_tiny_trajectory` repeated at `speed_ratio` 0.1, then 0.2, then 0.3
   (shim param). Several runs at each — repeats are what make tracking error
   measurable rather than anecdotal.
2. Cancels at varied times into the trajectory (0.5 s, 1.0 s, 2.0 s).
3. Single-arm runs, both arms, to see whether load or bridge traffic changes
   tracking.
4. A quiet period enabled but uncommanded, to record gravity-comp behavior.
5. **Stretch — MoveIt on hardware**, only if S3/S4 were clean and time allows:
   `ros2 launch baxter_moveit_config hardware_moveit.launch.py`, then plan a
   small motion in the RViz MotionPlanning panel, **inspect the preview**, and
   only then Execute. Planned trajectories go through the same shims, so goal
   validation, the safety gate and the clamp all still apply.
   `moveit_left_tiny` cannot drive this — it refuses to move unless move_group
   is on simulated time, by design. Rehearse the RViz flow against `mock_robot`
   before the day; only the wiring has been verified so far, not execution.

**Abort criteria:** e-stop rule stands. A tolerance abort at a higher speed →
back off one speed step and note the ceiling.

**Record:** a one-line note per run — time, speed ratio, params, what the arm
looked like. Without the timestamps the bags are much harder to segment later.

---

## S6 — Noetic API harvest (15:30–16:15)

**Purpose:** the native ROS 1 stack needs to know how the robot actually
behaves, not how the SDK documents it. No motion commands in this stage.

From `baxrun`: `rostopic hz` on the key topics (joint_states, robot/state,
joint_command), `rosservice list`, `rosmsg show` on the messages the native
stack will implement. One supervised observation of the
`joint_command_timeout` transition: stop the shims briefly and watch the arm go
from held to gravity-comp once.

Fill in `docs/noetic_native_notes.md` while the robot is in front of you.

---

## S7 — Shutdown and restore (16:15–16:45)

`baxtool tuck_arms.py -t`, `baxtool enable_robot.py -d` (sheet §8). Ctrl-C the
recorders and verify the bags closed. Ctrl-C shims, then the bridge, in that
order.

Then, before leaving: update the sheet's "Where the last session stopped",
update the gate-status table, and write `logs/I18_hardware_day.log.md`.

---

## Hard decision points

| When | Question | If no |
|---|---|---|
| End of S2 | Can the robot be enabled at all? | Pivot to non-motion harvest, skip S3–S5 |
| End of S3 | Do the tolerances hold on a real arm? | S4 tuning; if that fails, stop motion and analyse |
| 15:30 | — | No new experiments regardless of progress. Protect S6 and S7. |

## After the day

Bags and snapshots are in `data/sessions/<date>/{ros1,ros2}/` (gitignored). The
python `rosbags` library reads both ROS 1 `.bag` and ROS 2 files with one API:

- **Bridge latency:** match the same `/robot/joint_states` message across the two
  bags by `header.stamp` and diff the receive times. Both recorders run on this
  laptop, so the clocks are the same and the deltas mean something.
- **Tracking error:** join the ROS 1 side `joint_command` against
  `joint_states` — that is the command as actually delivered on the wire, not
  the setpoint we intended to send.
