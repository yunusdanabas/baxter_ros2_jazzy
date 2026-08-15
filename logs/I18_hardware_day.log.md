---
step: I18
title: "Hardware Session — First Supervised Motion"
agent_date: 2026-07-24
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15, I17, I12]
---

# I18 — Hardware session, 2026-07-24

> Frontmatter added 2026-07-25 to match the `WORKFLOW.md` log template; no
> finding in this log was altered. Backlog items 1, 3, 5, 6, 7 and 10 in the
> table below are now **done** — see `logs/I19_post_hardware_backlog.log.md`,
> which also records the corrections to F3, F14 and the two "Not done" entries.

Status: **COMPLETE**. First real motion through the ROS 2 command path. I12
supervised motion gate **PASSED**. Robot shut down clean: tucked, disabled,
sonar off, no stale registrations on the master.

**Improvement backlog produced by this session**, most important first:

| # | Item | Where | Status |
|---|---|---|---|
| 1 | Reject a second `/robot/state` publisher before arming | `safety.py`, `hardware_bringup.launch.py` (F1) | open |
| 2 | Subscribe to *all* publishers of a ROS 1 topic | `py_bridge.py` `ROS1Subscriber` (F13) | **done** |
| 3 | Stop destroying `header.stamp`; preserve the robot's sample time | `py_bridge.py` (F14) | open |
| 4 | ~~Tighten `path_tolerance_rad` 0.2 → ~0.05~~ — **measured; leave at 0.2** | shim defaults (F3 → **F22**) | **closed** |
| 10 | Advertise real md5sum + msgdef on ROS 1 publishers; recordings are undecodable | `py_bridge.py` `ROS1Publisher` (F23) | open |
| 5 | Give the cancel-hold check a settle window | `sim_tiny_trajectory.py:133-142` (F2) | open |
| 6 | Add a `duration` parameter to `sim_tiny_trajectory` | needed to stress tracking at all (F9) | open |
| 7 | Guard the double `rclpy.shutdown()` | `py_bridge.py` (F17) | open |
| 8 | MoveIt on hardware: `t=0` start point, joint order, SRDF pair | shim + `baxter.srdf` (F18) | **done** |
| 9 | Full Setup Assistant re-run — 52 collision pairs is sparse | `baxter.srdf` (F18) | open |

Robot: BR-01 `011412P0024` at `192.168.1.232` via `enp4s0`, 0.36 ms RTT.
Branch `i17-pre-hardware-hardening` at `d2190eb`.

---

## Gate results

| Gate | Result |
|---|---|
| Network pre-flight | PASS — resolves, reachable, route on `enp4s0`, master open |
| I10 non-motion | **PASS**, 0 warnings |
| I11 safety interlock | **PASS** — 6/6 goals rejected, each for the correct distinct reason |
| Enable + untuck (was BLOCKED since 2026-07-22) | **RESOLVED** — `tuck_arms.py -u` worked first attempt |
| I12 supervised motion | **PASS** — both arms, out and back, feedback on every goal |
| Cancel-and-hold | Behaviour **correct**; the *test* fails (see F2) |

---

## F1 — A second `/robot/state` publisher silently defeats the safety gate

**Severity: high (safety).** Found by accident, and it is the most important
finding of the session.

A `mock_baxter_robot` left over from an earlier desk verification survived its
cleanup (wrong process group; `pkill` matched nothing) and published a fake
**"safe"** `/robot/state` plus a fake neutral joint pose into the same ROS 2
graph as the real robot for ~15 minutes.

Observed consequences:

- The first P1 baseline read `ready=True enabled=True` with `left_s1=-0.550`
  while the robot was in fact **disabled and tucked at `left_s1=-2.174`**.
- Topic rates read 150 Hz / 200 Hz; the real rates are 101 Hz / 100 Hz.
- Detection required comparing our bridged view against `baxter_tools` talking
  to the master directly. A single path is not self-checking.

Why it matters beyond the accident: `SafetyStateChecker` samples the latest
`/robot/state`. With a mock advertising safe at 100 Hz alongside the real
disabled state, the gate can accept a goal it must reject. Worse, the shim seeds
`_last_commanded` from measured joint positions — with two poses interleaving,
the first real trajectory could have commanded a jump of ~1.6 rad.

**Fix:** assert exactly one publisher on `/robot/state` (and on
`/robot/joint_states`) before arming. `baxter_safety_check` should report the
publisher count and refuse `safe_for_motion` when it is not 1;
`hardware_bringup.launch.py` should abort if a `mock_baxter_robot` node exists.
Files: `src/baxter_hardware_bridge/baxter_hardware_bridge/safety.py`,
`launch/hardware_bringup.launch.py`.

## F2 — Cancel-hold check measures the settle transient

**Severity: low (test defect, not a robot or shim defect).**

`sim_tiny_trajectory ... -p cancel_after_sec:=1.0` reported
`Canceled trajectory did not hold: drift=0.0222 rad` against a 0.02 threshold.

The cancel was actually correct. The arm stopped at `-0.925`, exactly where a
cancel 1.1 s into a 3 s move from `-1.041` toward `-0.691` should stop it, and
independent measurement afterwards showed it **rock stable**: 0.0004 rad total
drift over 6 s, 0.0015 rad peak-to-peak.

The check at `sim_tiny_trajectory.py:133-142` compares two *consecutive* joint
states taken immediately after cancel, so on real hardware it measures the arm
settling into the hold setpoint. A physics-less mock settles instantly; a real
series-elastic arm needs ~0.02 rad, landing just over the limit.

**Fix:** reuse the settle-window pattern the same file already implements for
goal completion (`sim_tiny_trajectory.py:226-254`, the `SETTLE_TIMEOUT_SEC`
loop) instead of two adjacent samples.

## F3 — The tolerance worry was backwards: they are too loose, not too tight

Pre-session expectation (runbook, `hardware_test_commands.md` §7) was that
`path_tolerance_rad=0.2` and `stopped_velocity_tolerance=0.25`, desk-tuned
against a mock with no physics, would **false-trip** on a real arm.

Nothing tripped. Measured worst tracking error across four trajectories at
`speed_ratio` 0.1:

| Run | max_error |
|---|---|
| left outbound | 0.0043 rad |
| left return | 0.0054 rad |
| right outbound | 0.0055 rad |
| right return | 0.0077 rad |

That is a **26× margin** under the 0.2 rad path tolerance. A limit with that much
headroom cannot detect a genuine fault. The action item is to tighten it against
measured behaviour across the speed sweep, not to loosen it. Remove the
"retry with `-p path_tolerance_rad:=0.3`" advice from the runbook and command
sheet once the speed sweep gives a defensible number.

## F4 — CORRECTED — the bridge receives only one of two publishers

**This entry originally claimed the real robot alternates between a 17-joint and
a 15-joint message. That was wrong — it was the F1 mock contamination.** With the
mock gone, the bridged stream is a single consistent 17-joint set (`head_nod`,
`head_pan`, + 14 arm joints) at 100 Hz. Recorded here rather than deleted,
because it is a good example of how far one stale publisher propagated into the
conclusions.

The real finding is F13.

## F13 — `ROS1Subscriber` connects to only one publisher of a multi-publisher topic

**Severity: medium.** Measured simultaneously on both sides:

| Path | `/robot/joint_states` rate |
|---|---|
| ROS 1, direct (`rostopic hz`) | **138.8 Hz** |
| ROS 2, via `py_bridge` | **99.7 Hz** |

The bridge delivers **72%** of the stream. `/robot/joint_states` has two ROS 1
publishers — `/realtime_loop` (~100 Hz, head + 14 arm joints) and
`/end_effector_publisher` (~38 Hz, gripper joints). `ROS1Subscriber` negotiates
TCPROS with a single publisher and never connects to the second, so the bridged
topic carries `/realtime_loop` only.

Not a throttling bug: `_flush_ros2_queue` drains the whole queue every tick and
there is no rate limit in the enqueue path. It is purely the missing second
connection.

Consequences: **gripper joint states never reach ROS 2 at all.** Arm control is
unaffected, since `/realtime_loop` carries every joint the shims use, which is
why this went unnoticed through I10/I11. Any future gripper work, and any ROS 2
consumer of a multi-publisher ROS 1 topic, hits this silently.

**Fix:** `ROS1Subscriber` should call `requestTopic` on *every* publisher the
master lists for the topic, and handle `publisherUpdate` adding new ones, rather
than binding to the first. Files: `scripts/py_bridge.py` (`ROS1Subscriber`,
`SlaveApi.publisherUpdate`).

## F14 — The bridge overwrites `header.stamp` on `/robot/joint_states`

`_flush_ros2_queue` (`scripts/py_bridge.py:712-721`) does
`msg.header.stamp = self.get_clock().now().to_msg()` for every JointState before
republishing. The robot's own sample time is discarded and replaced with bridge
**receive** time.

Two consequences:

1. **The planned latency measurement does not work.** Matching the same message
   across the ROS 1 and ROS 2 bags by `header.stamp` was the documented method
   for measuring bridge latency — but the ROS 2 stamp is rewritten, so the two
   are not comparable. Latency has to come from a monotonic sequence field or
   from correlating position values instead.
2. Any consumer computing velocity or staleness from `header.stamp` is measuring
   the **bridge's** timing, not the robot's — including the shim's
   `joint_states_stale_sec` check and anything feeding
   `stopped_velocity_tolerance`.

The rewrite is presumably deliberate (ROS 1 and ROS 2 clocks need not agree), but
it should preserve the original stamp somewhere rather than destroy it.

## F15 — Phantom-node cleanup works on hardware

Explicit check of a previously suspected defect. After `sonar_ctl.py` ran and
exited mid-session, `rosnode list` showed **no** stale `/sonar_ctl_*`
registrations — only the eight live `/py_bridge_*` nodes of the running bridge.
Re-checked after full shutdown: **no** `py_bridge` or `sonar_ctl` registrations
remain on the master. The `atexit` unregister path works against real hardware,
including on an abrupt stop. No action needed; the troubleshooting entry about
phantom `/sonar_*` nodes can be marked resolved.

## F17 — `py_bridge.py` throws a double-shutdown traceback on exit

**Severity: low (cosmetic, but it hides real errors).** Stopping the bridge ends
with:

```
rclpy._rclpy_pybind11.RCLError: failed to shutdown: rcl_shutdown already called
on the given context, at ./src/rcl/init.c:333
```

and exit code 1. `rclpy.shutdown()` is reached twice — once on the normal
signal/`finally` path and again from the `atexit` handler. Functionally harmless
(F15 confirms cleanup still completes), but a guaranteed traceback on every clean
stop trains the operator to ignore shutdown output, which is exactly where a real
failure would appear. Guard it with `if rclpy.ok():` or a shutdown flag.

## F16 — A large multi-joint move tracks better than the gate test

Restoring the untuck pose after the arms were moved by hand exercised a much
harder trajectory than the I12 gate: **all 7 joints per arm**, largest single
joint 1.559 rad (`left_w0`), over 8 s. Both goals accepted and returned
`error_code: 0`, final worst error **0.0023 rad** — better than the 0.0078 rad
seen on the small single-joint gate move.

Reinforces F3: tracking is excellent and the 0.2 rad path tolerance has no
diagnostic value. Also a useful proof that the shim handles full 7-joint goals
from an arbitrary starting pose, not just the scripted one-joint case.

## F5 — `enable_robot.py -e` vs `tuck_arms.py -u`, confirmed on hardware

`tuck_arms.py -u` succeeded on the **first attempt**, taking ~23 s
(`Untucking: One or more arms Tucked; Disabling Collision Avoidance and
untucking.` → `Finished tuck`). This confirms the 2026-07-22 diagnosis: the
difference is collision suppression plus a 20 Hz enable republish, not robot
health.

Deviation from the documented expectation: the runbook warns that a *successful*
untuck can end `enabled: False`, because `tuck_arms.py::_move_to` disables on
exit if a collision flag remains. That did **not** happen here — the robot ended
`ready=True enabled=True`, confirmed on both the bridged and the direct path.
So the "expect disabled" note is a *possible* outcome, not the normal one.

Final untuck pose matched the documented table closely (target in brackets):

| | s0 | s1 | e0 | e1 | w0 | w1 | w2 |
|---|---|---|---|---|---|---|---|
| left | -0.114 [-0.08] | **-1.042** [-1.0] | -1.030 [-1.19] | 1.962 [1.94] | 0.651 [0.67] | 0.992 [1.03] | -0.483 [-0.50] |
| right | 0.110 [0.08] | **-1.041** [-1.0] | 1.040 [1.19] | 1.961 [1.94] | -0.646 [-0.67] | 0.990 [1.03] | 0.489 [0.50] |

## F9 — `speed_ratio` has no measurable effect on these trajectories

Speed sweep, `s1` by 0.35 rad over 3 s, both arms out and back at each setting:

| `speed_ratio` | left out | left return | right out | right return |
|---|---|---|---|---|
| 0.1 | 0.0043 | 0.0054 | 0.0055 | 0.0077 |
| 0.2 | 0.0051 | 0.0042 | 0.0078 | 0.0065 |
| 0.3 | 0.0055 | 0.0050 | 0.0078 | 0.0077 |

(max_error in rad.) **Flat** — tripling the ratio changes nothing.

Explanation: `set_speed_ratio` caps the robot-side maximum joint speed, but the
shim interpolates its own motion at ~0.117 rad/s (0.35 rad over 3 s), far below
the cap at any of these settings. The binding constraint is the **trajectory
duration**, not `speed_ratio`.

Consequences: raising `speed_ratio` is not a way to make motion faster or to
stress tracking — shortening `time_from_start` is. And a real tracking-stress
test needs a trajectory that approaches the clamp (`max_step_rad_per_cycle` ×
`command_rate` = 2.0 rad/s), which `sim_tiny_trajectory` cannot generate since
its distance and duration are fixed. Worth a `duration` parameter on that client.

## F10 — Consistent left/right asymmetry

Across all 12 trajectories the **right arm tracks worse than the left**, without
overlap: left 0.0042–0.0055 rad, right 0.0065–0.0078 rad, roughly 1.4×. Stable
across all three speed settings, so it is a property of the arm rather than
noise — plausibly calibration or gravity loading at this pose. Not a defect at
these magnitudes, but any per-joint tolerance should be set from the **right**
arm's numbers, not an average.

## F11 — Gravity compensation holds position; the arm does not sag

With the shims stopped for ~20 s — so no `joint_command` at all, well past the
0.2 s `joint_command_timeout` — the arms drifted **0.001 rad**. The mental model
that the arm "sags to gravity comp" when commands stop is wrong at this pose:
Baxter's gravity compensation holds it near-perfectly. Useful for the native
stack: losing the command stream is not immediately dangerous, though it is
still not a substitute for holding position deliberately.

## F12 — `pkill -f` is unsafe in this workflow (process hygiene)

`pkill -f "hardware_bringup.launch.py"` killed the very shell running it, because
`pkill -f` matches against full command lines and the pattern appeared in the
command itself. The `ros2 launch` parent died while its **shim children survived
as orphans**, leaving a half-torn-down stack that still looked healthy.

This is the same class of failure as F1 (stale process still publishing).
Always kill by explicit PID here, and verify with
`ps -eo pid,args | grep follow_joint_trajectory_shim` afterwards. Changing shim
parameters requires a relaunch, so this teardown happens often.

## F18 — MoveIt on hardware: three separate blockers, all now fixed

MoveIt had never executed against the shims. Bringing it up took three distinct
fixes; the first two were found at the desk against `mock_robot`, the third only
appeared on the robot.

**1. Leading `t=0` start point.** MoveIt's time parameterisation emits the current
state as point 0 at `time_from_start=0` (confirmed: 33 waypoints, point 0 exactly
on the measured pose). `_validate_values` started at `prev_t=0.0` and rejected
`t <= prev_t`, so every planned trajectory died on its first point. Now a leading
`t=0` point is dropped when it matches the measured pose, which keeps the rule
guarding what it was written for — a `t=0` point that is *not* where the arm is.

**2. Joint ordering.** MoveIt sends joints alphabetically
(`e0, e1, s0, s1, w0, w1, w2`); the shim compared `goal.joint_names` to its own
order with `==`. The action defines the mapping by **name**, so any permutation is
legal. Positions are now remapped.

**3. SRDF false-positive self-collision — the hardware-only one.** With both fixed,
the planner still returned `-10 START_STATE_IN_COLLISION` **from the pose
`tuck_arms.py -u` leaves the robot in**. `/check_state_validity` named the pair:

```
left_upper_shoulder <-> left_upper_elbow   depth=0.00173
```

1.7 mm of mesh interference between two links that are *two* apart in the chain,
so the Setup Assistant never marked them `Adjacent`, and its sampling evidently
never hit the folded untuck configuration. The result: MoveIt refused to plan from
the robot's own canonical operating pose. Disabled for both arms in
`config/baxter.srdf` with the measurement recorded in a comment.

Confirmed by a zero-motion diagnosis first — `MotionPlanRequest.start_state` lets
you plan from a hypothetical pose without moving anything: the untuck pose failed
while the neutral pose returned SUCCESS, which isolated it to the pose before any
SRDF edit.

**Result on hardware:** planner SUCCESS, 31 waypoints, shim `Goal accepted` →
`Goal succeeded`, no tolerance abort, arm `-1.0040` → `-0.8168` against a `-0.8040`
target.

> The SRDF holds only 52 `disable_collisions` pairs, which is sparse for Baxter.
> The two added here are the ones that actually bit; a full Setup Assistant re-run
> is the proper long-term fix and would likely find more.

## F19 — MoveIt trajectories land ~0.013 rad off, scripted ones ~0.005

The MoveIt-executed goal settled 0.0128 rad from target, against 0.0043–0.0078 rad
for `sim_tiny_trajectory`. Expected — 31 waypoints across all 7 joints versus a
single-joint move — and still far inside tolerance, but it is the number to use
when setting a goal tolerance for planned motion rather than the scripted figure.

## F20 — F13 had a second victim: MoveIt's planning scene

Before the F13 fix, move_group logged continuously:

```
The complete state of the robot is not yet known.
Missing l_gripper_l_finger_joint, r_gripper_l_finger_joint
```

Those joints come from `/end_effector_publisher`, the publisher the bridge was
never connecting to. After the fix the warning is gone and the bridged topic
carries **19 joints at 123.6 Hz**, up from 17 at 99.7 Hz.

Worth noting for honesty: this was *not* what caused the `-10` (F18.3 was), but it
would have blocked any gripper work and left the planning scene permanently
incomplete.

## F21 — An unknown joint name in a RobotState aborts move_group

Sending `/check_state_validity` a `RobotState` containing `head_nod` — a joint not
in MoveIt's model — threw `moveit::Exception: Variable 'head_nod' is not known to
model 'baxter'` **uncaught**, and the process died with exit -6. Any client can
therefore kill move_group with a malformed request. Upstream behaviour rather than
ours, but worth knowing: if move_group vanishes mid-session, check the last request
before blaming the robot.

## F22 — CORRECTS F3: the tolerance is not 26× too loose, and 0.05 would have been dangerous

Measured from `data/sessions/2026-07-24/ros1/full_163540_*.bag`, using
`/robot/ref_joint_states` (the robot's own commanded reference) against
`/robot/joint_states`, restricted to the windows where `joint_command` was
actually streaming:

| Arm | goal windows | p50 | p95 | p99 | **max** |
|---|---|---|---|---|---|
| left | 4 (20.7 s, 10374 samples) | 0.0007 | 0.0135 | 0.0268 | **0.0340** |
| right | 3 (18.7 s, 8547 samples) | 0.0009 | 0.0107 | 0.0291 | **0.0352** |

**Worst in-flight lag: 0.0352 rad.** The 0.0078 rad figure F3 was built on is the
client's `max_error`, measured *after* the arm settles — a different and 4.5×
smaller quantity than the one `path_tolerance_rad` actually governs.

Two conclusions, both reversing what F3 said:

1. **The proposed 0.05 rad was wrong and would have false-tripped.** Against a
   measured worst of 0.0352 it leaves a 1.42× margin — on gentle motion, with no
   fast-motion data at all. It would have produced nuisance aborts on exactly the
   moves that currently succeed.
2. **The current 0.2 rad is not egregious.** 0.2 / 0.0352 = **5.7×**, an ordinary
   engineering margin. The "26× headroom" claim came from dividing by the settled
   error and is withdrawn.

**Recommendation: leave `path_tolerance_rad` at 0.2 for now.** If it is tightened
later, 0.15 (4.3×) is the most aggressive defensible value from this data, and
only after backlog item 6 gives fast-motion numbers — lag grows with speed and
every trajectory here ran far below the clamp.

`s1` dominates on both arms (0.0340 / 0.0352) with every other joint ≤ 0.0116 —
expected, since it is the joint being moved and carries the most gravity load. A
per-joint tolerance would be tighter everywhere except the shoulder pitch.

> **Caveat.** `ref_joint_states` is the robot's *internal* reference, which may
> itself lag the `joint_command` we publish, so the true
> |our command − measured| could be slightly larger still. That only strengthens
> the conclusion against 0.05. A direct measurement needs F23 fixed.

For contrast, across *all* samples including idle, robot-internal tracking is
p50 = 0.0003, p95 = 0.0020 rad — the arm sits essentially exactly on its reference
when not being asked to move.

## F23 — The bridge publishes an empty message definition, so recordings are undecodable

Reading the bag back raised, for every bridge-published topic:

```
WARNING: For type [baxter_core_msgs/JointCommand] stored md5sum [*] does not
match message definition [d41d8cd98f00b204e9800998ecf8427e]
```

`d41d8cd98f00b204e9800998ecf8427e` is the md5 of the **empty string**:
`py_bridge.py` advertises its ROS 1 publishers with `md5sum "*"` and no message
definition. Wildcarding the md5 is what makes the bridge able to publish any type
without a definition table (and is genuinely useful — see
`docs/container_free_path.md`), but rosbag stores whatever the publisher
advertised, so `/robot/limb/*/joint_command` was recorded with **no schema** and
cannot be deserialised afterwards. The 1918 left / 1743 right messages are in the
bag as opaque bytes.

Impact: any ROS 1-side recording of a topic *we* publish is undecodable. It forced
this analysis onto `ref_joint_states` instead of the commands themselves. Message
timestamps survive, which is why the goal windows could still be recovered.

**Fix:** have `ROS1Publisher` advertise the real md5sum and message definition for
the handful of types it publishes, rather than `*`. Keep the wildcard on the
*subscribe* side, where it is what lets the bridge take any type without a schema.
Files: `scripts/py_bridge.py` (`ROS1Publisher`, `_build_tcpros_header`).

## F6 — Build environment traps (found pre-session, fixed)

An active conda env shadows the system `python3`. Two distinct failures:

1. At runtime, `python3 scripts/py_bridge.py` dies with
   `No module named 'rclpy._rclpy_pybind11'`.
2. **Worse**, at *build* time setuptools bakes the conda interpreter into every
   installed entry point's shebang, so the workspace compiles cleanly and then
   fails on every `ros2 run` **and the shim launch**. The workspace was in this
   broken state before the session.

Fixed by `scripts/baxter_env.sh` stripping conda from `PATH`, and documented in
the runbook prerequisites with the check
`head -1 install/baxter_hardware_bridge/lib/baxter_hardware_bridge/dry_run_test`
→ must be `/usr/bin/python3`.

## F7 — Head sonar does not persist

Confirmed: sonar read `4095 (0x0fff)`, all 12 transducers active, at session
start — despite being turned off at the end of 2026-07-22. Turning it off and
reading back gives `0 (0x0000)`. The "resets on reboot" warning is real and the
read-back check is worth keeping.

## F8 — Docker images are a fragile dependency

A routine `docker system prune` removed `baxter-noetic` from **both** local
engines (host `dockerd` and Docker Desktop). Rebuilt on the host daemon from
`~/baxter_noetic_ws/src/baxter_noetic` in ~14 min. Docker Desktop was not
running and its VM networking would not suit ROS 1 host networking anyway, so
the **host** daemon is the correct engine for robot work.

See `docs/container_free_path.md` — `enable_ctl.py` and bridging
`/robot/ref_joint_states` would remove the container from everything except the
untuck.

---

## Captures

Under `data/sessions/2026-07-24/` (gitignored):

- `ros1/full_163334_*.bag` (7.1 MB, closed) — `/robot/state`, `/diagnostics`,
  collision states across the enable + untuck attempt.
- `ros1/full_163540_*` — joint states, `ref_joint_states`, joint commands and
  state across the I12 motion gate.
- `ros2/full_*` — bridged and shim view including action feedback/status.
- Inventory snapshots (`topics_*.txt`, `nodes_*.txt`, `params_*.yaml`) alongside.

## Recommended tolerance values (from measurement)

Worst observed tracking error across **12 trajectories at three speed settings**
is **0.0078 rad** (right arm). Current `path_tolerance_rad` is 0.2 — a 26× margin
that cannot detect a genuine fault.

Proposal: **`path_tolerance_rad = 0.05`**, a 6.4× margin over the worst observed
value. Tight enough to catch a blocked or stalled arm within a few control
cycles, loose enough to absorb the asymmetry in F10 and a pose-dependent increase
we have not yet sampled. Do not go below 0.03 without data from poses under
higher gravity load.

`stopped_velocity_tolerance` (0.25) is untested — every goal settled in ≤0.01 s,
so the check never came close to firing. Leave it until a trajectory ends with
the arm genuinely still moving. Note F4: it differences samples that alternate
between two publishers, which should be fixed before tightening it.

## Not done, and why

**Cancel sweep** (`cancel_after_sec` 0.5 / 2.0) skipped deliberately. F2 shows the
cancel-hold *check* is broken, so further cancels would re-fail the same way and
prove nothing. Re-run the sweep once the settle window is implemented.

## Session end state

`tuck_arms.py -t` returned the arms to the shipping pose and disabled the robot
on its way out (`Robot Disabled` — the documented `_move_to` behaviour, which did
*not* fire after the untuck in F5). Verified afterwards:

- `enabled=False ready=False stopped=False error=False estop=0`
- `left_s1=-2.175`, `right_s1=-2.180` — tucked
- head sonar `0 (0x0000)` — still off
- shims stopped, then bridge stopped; no `py_bridge`/`sonar_ctl` nodes left on
  the master

## Not done

- **P7 MoveIt-on-hardware.** Still untested on the robot; only the wiring is
  verified (move_group loads both shim action servers against `mock_robot`).
- **Cancel sweep**, blocked on F2 as described above.
- **Tracking under real load.** Every trajectory ran far below the clamp, so the
  tolerance numbers describe gentle motion only. Item 6 in the backlog is the
  prerequisite for saying anything about fast motion.
