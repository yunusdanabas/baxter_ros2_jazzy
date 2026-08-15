---
step: I12
title: "Supervised Hardware Motion"
agent_date: 2026-07-22
status: blocked
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15]
---

# I12: Supervised Hardware Motion — BLOCKED

**No motion was performed.** The robot was left `enabled=false` and tucked,
positions unchanged from the start of the session. I12 is blocked on the
open problem below.

## Robot Identity (confirmed from the ID plate)

| Field | Value |
|---|---|
| S/N | `011412P0024` — the mDNS hostname is exactly the serial |
| P/N | `00012541` |
| Model | **BR-01** (Baxter *Research* Robot — SDK-compatible) |
| Manufactured | 12/2014 |
| Weight | 74.84 kg |

This confirms `011412P0024.local` is correct, and that the SDK path
(`baxter_interface` / `baxter_tools`) is the right one for this unit.

## BLOCKER: `enable_robot.py -e` fails

```text
$ rosrun baxter_tools enable_robot.py -e
[ERROR] Failed to enable robot
```

State immediately before and after is clean and unchanged — nothing obviously
faulted:

```text
ready: false      enabled: false    stopped: false
error: false      estop_button: 0   estop_source: 0
```

Ruled out during investigation:

- **Not an e-stop.** `estop_button=0` (`UNPRESSED`), `estop_source=0` (`NONE`).
- **Not a fault.** `error=false`, `stopped=false`.
- **Not `ready=false`.** Per `AssemblyState.msg`, `ready` means *"true if
  enabled and ready to operate, e.g. not homing"* — so `ready=false` is simply
  a consequence of `enabled=false`, not an independent problem.
- **Not connectivity.** The same container run reports state correctly with
  `enable_robot.py -s`, and `/realtime_loop` is a live subscriber of
  `/robot/set_super_enable`. Our own bridge publishes to the robot
  successfully (proven by the sonar write in I10).
- **Not a diagnostics error.** `/diagnostics` carried exactly one status,
  `[WARN] Collision detection: Collision detected on jointleft_s1` — no
  ERROR-level entry.

### RULED OUT (later the same day): slow TCPROS negotiation

`RobotEnable._toggle_enabled` creates a **fresh** `rospy.Publisher` and wraps it
in `baxter_dataflow.wait_for(..., timeout=2.0)`. If `/realtime_loop` took longer
than 2 s to attach, every publish would land on a publisher with zero
connections and be silently dropped — the robot would never see the request.
`scripts/sonar_ctl.py:74` carries `time.sleep(3)  # let /realtime_loop negotiate
TCPROS with us`, measured against this robot, which made this look likely.

**Measured, and it is wrong.** A probe that creates the publisher on
`robot/set_super_enable` and publishes *nothing*, timing only
`get_num_connections()`:

```text
RESULT: subscribers connected: 1 after 0.24 s
```

0.24 s is well inside the 2.0 s budget. The enable requests **did** reach
`/realtime_loop`. The robot received them and refused. Do not re-test this.

(`sonar_ctl.py`'s 3 s is a different path — our hand-rolled slave API in
`py_bridge.py`, not rospy — so it is not evidence about `enable_robot.py`.)

### Robot health sweep: everything OK except the collision

15 s of `/diagnostics`, 201 status entries, **200 at level 0**:

| Status | Result |
|---|---|
| `Robot Config` | `[OK]` |
| `Realtime Control Loop` | OK — 100.00 Hz state publisher, recent overruns `0; 0.00%` |
| Every joint: `thermal` / `sds` / `sensor_consistency` / `process_sense` / `voltage` | `[OK]` |
| `RC-{left,right}: Tare`, `RC-{left,right}: CalibrateArm` | present, idle (`complete=0`), joints + endpoint interfaces `OK` |
| `rosparam /rethink/software_version` | `1.2.0.57` |
| `SDSCalibrationSlope` for all 14 arm joints | present under `/robot_config/jcb_hal_config/` |

So it is **not** a fault, not thermal, not a missing calibration, not the
control loop. The single level-1 entry is the collision.

### Leading hypothesis (now the only one left): collision force-field

`/diagnostics` reports `Collision detected on jointleft_s1`, which is expected
in the tucked pose — the arms rest inside the head/arm collision field.

The full status payload shows *why* it cannot clear itself while disabled:

```text
level: 1   name: "Collision detection"   message: "Collision detected on jointleft_s1"
  joint name                -> left_s1
  impact torque             -> -3.57737
  scaled impact threshold   -> 0
  velocity command          -> 0
  acceleration command      -> 0
```

The threshold **scales with the commanded velocity/acceleration**. Disabled,
both commands are 0, so the threshold is 0, and the static gravity torque of
the tucked arm (-3.58 N·m) exceeds it unconditionally. The collision flag is
therefore *latched for as long as the robot is disabled and tucked* — it cannot
clear on its own, and no amount of retrying `enable_robot.py` will help.

Only `left_s1` trips; the right arm stayed below threshold in the same window.
Caveat: this is one sample taken while disabled, so "threshold scales with
command" is inference from the field names, not something measured in both
states.

That is exactly the condition `robot/limb/{side}/suppress_collision_avoidance`
exists to bypass, and exactly what `enable_robot.py` never publishes.

`baxter_tools/scripts/tuck_arms.py::_prepare_to_tuck` documents this directly:

```python
# If arms are in "tucked" state, disable collision avoidance
# before enabling robot, to avoid arm jerking from "force-field".
while not at_goal() and not rospy.is_shutdown():
    if start_disabled:
        [pub.publish(Empty()) for pub in self._disable_pub.values()]
    if not self._rs.state().enabled:
        self._enable_pub.publish(True)
    head.set_pan(0.0, 0.5, timeout=0)
    self._tuck_rate.sleep()      # 20 Hz
```

Two differences from `enable_robot.py`, either of which could explain the
failure:

1. `tuck_arms.py` publishes `robot/limb/{side}/suppress_collision_avoidance`
   **before and while** enabling; `enable_robot.py` does not.
2. `tuck_arms.py` republishes `set_super_enable` at 20 Hz until the state
   actually flips. `enable_robot.py`'s `_toggle_enabled` publishes inside a
   `wait_for` with only a **2.0 s** timeout, which is also a plausible
   first-connection race for a freshly created `rospy.Publisher`.

### Next step to try (not yet run — requires supervision)

`rosrun baxter_tools tuck_arms.py -u` is the tool designed for exactly this
state: it suppresses collision avoidance, enables with sustained publishing,
moves the head to neutral, then drives both arms to the untuck targets. It
does enable **and** untuck in one supervised motion.

This was prepared but **deliberately not run** — deferred to a supervised
session.

If it hangs without enabling, the collision-suppression hypothesis is wrong.
Note that the usual next suspects are now **already eliminated** by the health
sweep above: software version, per-joint calibration slopes, thermal, control
loop, and `Robot Config` are all fine, so there is no point re-checking homing
or calibration. What would remain is `rethink.log` on the robot itself, which
needs a shell we do not currently have (no SSH key installed, password
unknown).

## Untuck Targets (from `tuck_arms.py`, for reference)

| | s0 | s1 | e0 | e1 | w0 | w1 | w2 |
|---|---|---|---|---|---|---|---|
| left | -0.08 | **-1.0** | -1.19 | 1.94 | 0.67 | 1.03 | -0.50 |
| right | 0.08 | **-1.0** | 1.19 | 1.94 | -0.67 | 1.03 | 0.50 |

`s1 = -1.0` after untuck is what makes the I12 trajectory valid: the script's
reversible target becomes `-0.65`, well inside `[-2.147, 1.047]`. From the
current tucked `s1 = -2.175` the script correctly refuses to move.

## Second Blocker Found Before Motion (2026-07-22, no hardware)

The enable problem is not the only thing standing between here and I12. An audit
of the command path — run at the desk, before any motion — found that the shim
is unsafe for malformed goals, and that the I12 gate's **feedback** clause is
untestable as the repo stands. All findings were reproduced against `mock_robot`,
including a single `JointCommand` moving all 7 joints 1.5 rad with no ramp.

Full evidence and severities: `logs/I12_prep_command_path_audit.log.md`.

I12 stayed `blocked` on **two** independent items: enable-from-tucked (diagnosed
above, remedy is `tuck_arms.py -u`) and the command-path hardening.

**The second is now cleared** (2026-07-23, no hardware): F1–F4 and F10 are fixed,
`dry_run_test` passes 16/16, and the mock rehearsal verified both arms with
feedback plus the cancel-hold. See the Resolution section of the audit log.
I12 is therefore blocked on **enable-from-tucked alone**, which needs the robot.

## Session End State

| Item | State |
|---|---|
| Robot | `enabled=false`, tucked, unchanged (`left s1=-2.175`, `right s1=-2.181`) |
| Head sonar | OFF (set in I10; resets to all-on at robot reboot) |
| Bridge / shims | stopped |
| Motion performed | **none** |

---

## Resolution — 2026-07-24 session (appended; the diagnosis above stands)

**I12 PASSED.** The blocker diagnosed above was correct and the prescribed remedy
worked on the first attempt. Full evidence: `logs/I18_hardware_day.log.md`.

| Item | Result |
|---|---|
| Enable from tucked | **RESOLVED** — `tuck_arms.py -u` succeeded first attempt, ~23 s (I18 F5) |
| I12 gate | **PASS** — both arms, out and back, feedback on every goal |
| Cancel-and-hold | Behaviour correct; the *test* false-failed on the settle transient (I18 F2, fixed 2026-07-25 in `41cd5f7`) |
| Motion performed | tiny trajectories both arms, plus a 7-joint restore and MoveIt execution |

The collision force-field hypothesis is confirmed in practice: `tuck_arms.py -u`
suppresses collision avoidance and republishes enable at 20 Hz, and that is the
difference. One documented expectation did not hold — the runbook warns that a
successful untuck can end `enabled: False`, but this run ended
`ready=True enabled=True` (I18 F5). Treat "expect disabled" as a possible
outcome, not the normal one.

Two figures in this log are superseded:

- "`dry_run_test` passes 16/16" (Second Blocker section) — the suite is **25**
  cases as of 2026-07-25.
- The frontmatter `status: blocked` and the title's `— BLOCKED` describe the
  2026-07-22 session, which is what this log is. The **step** status is
  `completed` in `MASTER_PLAN.md`, with its gate evidence in the I18 log.
