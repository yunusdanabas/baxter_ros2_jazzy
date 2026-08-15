---
step: I17
title: "Pre-Hardware Hardening and Polish"
agent_date: 2026-07-23
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09, I10-prep, I10-prep2, I10, I11, I14, I15]
---

# I17: Pre-Hardware Hardening and Polish

## Task

Phases A and B of `docs/i12_completion_plan.md`: land the last two safety
features the command path was missing (path tolerance, stopped velocity), remove
the `dry_run.launch.py` trap, add regression coverage, and make the docs, plan,
`MASTER_PLAN.md` and `CHANGELOG.md` agree. No hardware — the robot was not
available and the remaining I12 blocker needs a human with an e-stop.

Explicitly out of scope and not touched: the enable-from-tucked blocker
(diagnosed in `logs/I12_supervised_hardware_motion.log.md`), the F1–F4/F10
fixes already resolved on 2026-07-23, and the legacy features deliberately not
ported (velocity mode + PID, `position_w_id`, Bezier/minjerk, per-joint goal
position tolerance, shrinking `STATE_TIMEOUT_SEC`).

## Findings

### F-A. Path tolerance monitoring

`src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py`

New node parameter `path_tolerance_rad` (default **0.2**, Rethink's own default
from `plan/baxter_noetic_ref/baxter_interface/cfg/PositionJointTrajectoryActionServer.cfg`).
Checked once per interpolation cycle. As built after the review pass below
(R1, R3) it compares the command actually published against the measured pose,
and holds where the arm is:

```python
if not self._mock_mode:
    tracking = [self._last_commanded[k] - self._latest_positions[k] ...]
    lag = self._worst_tracking_error(tracking)
    if lag is not None:
        self._hold_position(self._latest_positions)
        goal_handle.abort()
        result.error_code = FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED
```

Two behaviours worth recording:

- **Holds, does not stop commanding.** This is the decision carried in from the
  plan. Stopping is right for an e-stop; a lagging arm is not an unsafe robot,
  and dropping the command stream lets it sag into gravity compensation once the
  robot's 0.2 s `joint_command_timeout` expires. The legacy holds too, via
  `_command_stop`.
- **Skipped when `mock_mode` is true.** In mock mode the shim publishes no
  `JointCommand` at all, so the measured pose cannot track the setpoint by
  construction and every goal would abort. This is why the two path-tolerance
  regression cases run with `mock_mode` flipped off.

### F-B. Stopped-velocity check

Same file, after the last point is commanded. New parameter
`stopped_velocity_tolerance` (default **0.25**, same cfg). Aborts and holds if
any joint still exceeds it.

As built after the review pass below (R4), the check runs after the final point
has been held for `goal_time_sec` (default 0.1, the legacy's `goal_time`), not at
the instant it is commanded.

This needed a velocity feed, which the shim was discarding. `_joint_state_cb`
now unpacks `msg.velocity` alongside `msg.position`, preserving the last known
value for any joint a message omits — the same rule position already used, and
the safer direction if a short velocity array ever arrives (R5).
`deser_joint_state` at `scripts/py_bridge.py:153` already unpacks the ROS 1
`velocity` array, so this is live on hardware.

### F-C. Result codes: used the standard ones, not a new `-10x`

The prompt suggested following the file's `RESULT_CANCELED = -100` /
`RESULT_ABORTED = -101` convention. `control_msgs` already defines exactly these
two cases:

```text
$ grep TOLERANCE /opt/ros/jazzy/share/control_msgs/action/FollowJointTrajectory.action
int32 PATH_TOLERANCE_VIOLATED = -4
int32 GOAL_TOLERANCE_VIOLATED = -5
```

Those are distinct from the safety abort, which is what the instruction was
protecting, and clients understand them without repo-specific knowledge. The
custom negatives stay where the standard has no code — cancel and safety abort.
The header comment in the shim now says so explicitly.

### F-D. `dry_run.launch.py` hardcoded `mock_mode: True`

Fixed with one `DeclareLaunchArgument("mock_mode", default_value="true")` wired
into both shims, matching `hardware_bringup.launch.py:17-36`. Default unchanged,
so the plain launch still comes up in mock mode:

```text
$ ros2 launch baxter_hardware_bridge dry_run.launch.py
[mock_robot-1] Mock robot ready (unsafe=False). ...
[follow_joint_trajectory_shim-2] Action shim ready: /robot/limb/left/... (mock_mode=True)
[follow_joint_trajectory_shim-3] Action shim ready: /robot/limb/right/... (mock_mode=True)
```

### F-E. Regression cases, 16 → 20

`dry_run_test.py`, reusing `make_goal` and adding a `send_and_wait` sibling to
the existing `expect_reject` (accept, then wait for the result). `MockRobot`
gained two flags in the same spirit as `joint_states_enabled`:
`command_feedthrough` (stop echoing commands into `joint_states`) and `velocity`
(report a constant non-zero speed; the mock has no physics, so a still-moving
arm has to be asserted).

- **Test 17** — closed loop, feedthrough on, tiny trajectory succeeds. This is
  the check that a too-tight default fails at the desk rather than on the robot.
  It also catches an implementation that compared against the goal endpoint
  instead of the current setpoint: the largest displacement in that goal is
  1.26 rad on `w1`, far past the 0.2 rad tolerance.
- **Test 18** — feedthrough off mid-trajectory, so the measured pose freezes.
  Asserts the `PATH_TOLERANCE_VIOLATED` code, that `_hold_position()` was called
  at all (the hold-vs-stop decision), and that the pose it held is the measured
  one rather than the unreachable setpoint (R3). Test 16 already proves
  `_hold_position()` republishes rather than publishing once, so the two compose
  instead of duplicating.
- **Test 19** — `mock.velocity = 0.5` against a 0.25 tolerance;
  `GOAL_TOLERANCE_VIOLATED` after the settle window, and two `_hold_position()`
  calls (the settle plus the post-abort hold). The positive case is Test 1,
  which succeeds with the mock reporting zero velocity.
- **Test 20** — a `left_w2` segment at 3.0 rad/s: inside the URDF limit of 4.0
  but above the 2.0 rad/s the per-cycle clamp can deliver. Must be rejected at
  accept time rather than accepted and aborted mid-move (R2).

## Evidence

```text
$ colcon build --base-paths src --symlink-install \
    --packages-select baxter_hardware_bridge baxter_examples
Summary: 2 packages finished [1.89s]

$ ros2 run baxter_hardware_bridge dry_run_test
PASS: Test 1 goal succeeded, 95 feedback messages
PASS: Test 2 bad joints rejected
PASS: Test 3 unsafe state rejected
PASS: Test 4 mid-goal cancel
PASS: Test 5 mid-goal unsafe abort
PASS: Test 6 short positions rejected
PASS: Test 7 no lurch (max deviation 0.0000 rad)
PASS: Test 8 concurrent goal rejected
PASS: Test 9 zero-duration point rejected
PASS: Test 10 NaN position rejected
PASS: Test 11 non-monotonic time rejected
PASS: Test 12 out-of-limits position rejected
PASS: Test 13 over-velocity segment rejected
PASS: Test 14 stale joint_states rejected
PASS: Test 15 clamp held command to 0.02 rad/cycle
PASS: Test 16 held with 98 commands over 0.99 s
PASS: Test 17 tracked within path tolerance
PASS: Test 18 Path tolerance violated: left_w1 lags its setpoint by 0.200 rad (limit 0.200 rad), held measured pose (gap 0.0000 rad)
PASS: Test 19 Goal tolerance violated: left_s0 still moving at 0.500 rad/s (limit 0.250 rad/s), held
PASS: Test 20 over-clamp segment rejected
OVERALL: PASS
EXIT=0
```

Closed-loop rehearsal, now a single launch:

```text
$ ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false
$ ros2 run baxter_examples sim_tiny_trajectory --ros-args \
    -p left_action:=/robot/limb/left/follow_joint_trajectory \
    -p right_action:=/robot/limb/right/follow_joint_trajectory \
    -p joint_states_topic:=/robot/joint_states
/robot/limb/left/...  outbound feedback: 269 messages
/robot/limb/left/...  outbound verified: max_error=0.0000 rad (settled in 0.01 s)
/robot/limb/left/...  return   feedback: 277 messages
/robot/limb/left/...  return   verified: max_error=0.0000 rad (settled in 0.00 s)
/robot/limb/right/... outbound feedback: 264 messages
/robot/limb/right/... outbound verified: max_error=0.0000 rad (settled in 0.00 s)
/robot/limb/right/... return   feedback: 277 messages
/robot/limb/right/... return   verified: max_error=0.0000 rad (settled in 0.00 s)
Reversible trajectories verified for both arms
EXIT=0

$ ros2 run baxter_examples sim_tiny_trajectory --ros-args ... -p cancel_after_sec:=1.0
Active trajectory canceled; controller is holding position
Cancellation hold verified: max_drift=0.0000 rad
EXIT=0
```

Path tolerance did not fire during either rehearsal, which is the desk-level
evidence that 0.2 rad is not obviously too tight. Against a mock that echoes
commands instantly, this proves very little about a real arm — see open
questions.

### F-F. `dry_run_test` is silently wrong if a launch stack is still up

Hit while verifying: a `dry_run.launch.py` stack orphaned by `timeout -s INT`
was still running when `dry_run_test` was re-run. The suite reported 8 failures
that had nothing to do with the code — unsafe goals accepted, valid goals
rejected, `error_code=0` where `-5` was expected. Both stacks advertise the same
action names and `/robot/state`, and `dry_run_test` starts its own shim and mock
in-process, so the client binds to whichever server answers first. `Ctrl-C` on
the launch did not reap the nodes.

```text
$ pgrep -af "mock_robot|follow_joint_trajectory_shim"
182206 .../mock_robot --ros-args -r __node:=mock_baxter_robot
182207 .../follow_joint_trajectory_shim --ros-args -r __node:=left_arm_shim
182208 .../follow_joint_trajectory_shim --ros-args -r __node:=right_arm_shim
```

Killed those three, re-ran on a clean graph, 19/19. Noted in the runbook next to
the rehearsal commands. Not worth code: no `ROS_DOMAIN_ID` isolation is a
deliberate project rule, and a `pgrep` line in the docs is cheaper than a
liveness check that could itself be wrong.

## Review pass (same day, three independent readings)

The user asked for a full check of the implementation plus verification from
Copilot. Three passes were run: this agent's own line-by-line reading, a
subagent review, and GitHub Copilot CLI (`copilot -p`, session
`1491315b`). All three independently reached the same four conclusions.
Five defects were found and fixed; one was left as a decision for the user.

### R1. Path tolerance was measured against the wrong reference — fixed

The check compared `interp`, the *unclamped* interpolated setpoint, against the
measured pose. `_publish_command` clamps to `max_step_rad_per_cycle` before it
goes on the wire, so whenever the clamp binds the arm was blamed for lagging a
setpoint it was never given. Now compared against `self._last_commanded`.
`feedback.error.positions` still reports `interp - actual`, which is the correct
action-feedback semantics — only the tolerance check changed.

### R2. A wrist segment could pass validation and then abort — fixed

Root cause of R1's practical case. `JOINT_LIMITS` allows 4.0 rad/s on
`w0`/`w1`/`w2`, but the clamp caps every joint at
`max_step_rad_per_cycle * command_rate` = 2.0 rad/s. Reproduced against the mock
*before* the fix — note the mock has zero lag and no physics, so the shim's own
clamp was the only error source:

```text
accepted=True
error_code=-4  'Path tolerance violated: left_w2 lags its setpoint by 0.210 rad (limit 0.200 rad)'
```

Fixed in validation rather than only in the error computation: measuring against
the clamped command alone would have turned a loud mid-move abort into a silent
divergence from the requested trajectory. `_validate_values` now rejects against
`min(vmax, max_step * command_rate)` and names which bound applied. After:

```text
Rejected: point 0 left_w2 needs 3.00 rad/s, limit is 2.00 rad/s (max_step_rad_per_cycle)
accepted=False
```

Regression: Test 20.

### R3. A path-tolerance abort held the pose the arm had just failed to reach — fixed

`_hold_position()` republished `_last_commanded`. If the arm lags because it is
blocked — a collision, a person, a jam — that keeps driving it into whatever is
blocking it for a full `hold_duration_sec`. The legacy calls
`_command_stop(joint_names, self._limb.joint_angles(), ...)` at
`plan/baxter_noetic_ref/.../joint_trajectory_action.py:279`, i.e. the **measured**
pose. `_hold_position()` now takes an optional pose and the path-tolerance abort
passes `self._latest_positions`. The clamp turns this into a controlled release
rather than a step. Test 18 now asserts the held pose is the measured one.

### R4. The stopped-velocity check had no settling window — fixed

It ran at the instant the final point was commanded. Interpolation is linear, so
commanded velocity steps from segment speed straight to zero while a real arm is
still catching up — the check measured the cruise, not the stop. The legacy
re-commands the last point for `goal_time` (0.1 s in the cfg) and only then runs
`check_goal_state()`, which is where its own stopped-velocity test lives
(`joint_trajectory_action.py:540-572`). Added `goal_time_sec` (default 0.1) and a
settle hold before the check.

The I12 move would probably have passed anyway — 0.35 rad over 3 s is
0.117 rad/s against a 0.25 tolerance — but at 2x margin, on a desk-tuned value,
against a mock with no physics. Not evidence.

### R5. Two smaller fixes

- `_hold_position()` never re-checked safety, so a hold kept publishing for up to
  a second after the robot went unsafe — contradicting the shim's own stated rule
  ("On safety violation: stop publishing commands"). It now abandons the hold.
- `_joint_state_cb` defaulted a joint missing from `msg.velocity` to `0.0`, which
  would report a moving joint as stopped if a short velocity array ever arrived.
  Now preserves the last known value, matching how position is handled. Defensive:
  `deser_joint_state` (`scripts/py_bridge.py:153-170`) reads three independent
  float64 arrays and a real Baxter sends all three at full length.

### R6. Interrupt lost to a failing cancellation in the example clients — fixed

Reported separately and confirmed. All three clients had the same shape:

```python
except BaseException:
    self._cancel_active_goal()   # raises -> the bare raise below never runs
    raise
```

`_cancel_active_goal()` raises `RuntimeError` on a cancel timeout or a refused
cancellation. When it does, the in-flight exception is replaced: `KeyboardInterrupt`
survives only as `__context__`, and `main()` dispatches to `except Exception`
instead of `except KeyboardInterrupt`, logging the cancellation error rather than
"Interrupted; canceling the active MoveGroup goal".

Reproduced against the real code, driving `send_trajectory` on a live mock stack
with a rigged cancel and a `KeyboardInterrupt` injected into the result-wait loop:

```text
BEFORE  escaped exception: RuntimeError: Controller did not accept goal cancellation
        __context__      : KeyboardInterrupt
AFTER   [ERROR] Cancellation also failed: Controller did not accept goal cancellation
        escaped exception: KeyboardInterrupt
```

Fixed in `sim_tiny_trajectory.py`, `moveit_pose.py` and `moveit_left_tiny.py` by
wrapping the cleanup and logging its failure. `main()`'s own handlers already
guarded their `_cancel_active_goal()` calls this way, so the fix matches the
file's existing style. `Exception` rather than `BaseException` is caught inside,
so a second Ctrl-C during the 5 s cancel wait still gets through.

`baxter_examples` is `ament_cmake` with no test harness and two of the three
clients need `move_group`, so the permanent guard is an AST check in
`.github/workflows/ci.yml` that rejects an unguarded `_cancel_active_goal()`
inside an `except BaseException` handler. Verified both ways: passes on the tree,
and on a tree with one file reverted reports
`src/baxter_examples/baxter_examples/moveit_pose.py:231`. It checks shape, not
behaviour — the behavioural proof above was manual.

### R7. Open, and deliberately not fixed — the success path stops commanding

Measured, and still true after the fixes above:

```text
error_code=0 (Goal reached)
commands published after SUCCESS: 0
robot joint_command_timeout is 0.2 s -> arm is uncommanded from t+0.200 s
```

All three reviews ranked this first. The legacy re-commands the last point for
`goal_time` and then holds via `_command_stop(end_angles)` until a new goal
arrives or the robot is disabled (`joint_trajectory_action.py:572`). Ours
publishes the final point, settles for `goal_time_sec`, and returns — after
which nothing commands the arm. It is the same defect class as audit finding F4,
which was fixed for cancel only.

This matters for the I12 gate specifically: `sim_tiny_trajectory` settles for up
to `SETTLE_TIMEOUT_SEC = 2.0` s checking `max_error <= 0.02 rad`
(`sim_tiny_trajectory.py:228-245`) with nothing commanding the arm for most of
that window. A failure there would say nothing about the trajectory.

**Left unfixed on purpose.** The legacy's behaviour is an indefinite hold until
the next goal, which makes the arm permanently stiff after its first trajectory —
it cannot be hand-guided, and it changes how the cuff and zero-G interact. That
is a design decision with real consequences, not a bug fix, and it belongs to the
user rather than to this step. The `goal_time_sec` settle window narrows the gap
slightly (the arm is commanded 0.1 s longer) but does not close it.

## Decisions

| Decision | Why |
|---|---|
| Fix the clamp/URDF velocity mismatch in validation, not only in the error computation | Copilot CLI suggested comparing against the clamped command. Doing only that converts a loud mid-move abort into a silent divergence: the arm tracks the throttled command perfectly while falling behind the requested trajectory. Rejecting at accept time makes the two references agree for every accepted goal |
| Leave the success-path hold to the user | The legacy holds indefinitely until the next goal, which makes the arm permanently stiff and unguidable. That is a design decision, not a bug fix |
| Path/goal tolerance violations **hold**, safety violations **stop** | A lagging arm is not an unsafe robot. Stopping the command stream lets it fall into gravity compensation after the robot's 0.2 s `joint_command_timeout`; the legacy holds too |
| A path-tolerance abort holds the **measured** pose | Holding the setpoint keeps driving a blocked arm into whatever is blocking it. Matches the legacy `_command_stop(..., joint_angles(), ...)` |
| Use `PATH_TOLERANCE_VIOLATED` (-4) and `GOAL_TOLERANCE_VIOLATED` (-5) | `control_msgs` already defines them, and they are distinct from the repo's `-101` safety abort, which is what the "distinct code" instruction was protecting |
| Skip the path check when `mock_mode` is true | Nothing is published, so the arm cannot track. Checking would abort every mock goal |
| Check path tolerance against `_last_commanded`, not `interp` | An executor stall makes `interp` jump past what the clamp let through. Feedback keeps reporting `interp - actual`, which is the correct action semantics |
| Stopped velocity checked after a `goal_time_sec` settle hold | Linear interpolation means the arm is at segment speed when the last point lands; an instantaneous check measures the cruise, not the stop. This is the legacy's shape and its default (0.1 s) |
| A hold abandons itself when the robot goes unsafe | Otherwise it publishes for up to a second after an e-stop, contradicting the shim's own stated rule |
| `dry_run_test` flips `mock_mode` for Tests 17-18 only | The rest of the suite stays non-publishing. Note this means the suite briefly publishes real `JointCommand` topic names — it already advertises the real action names, so it was never safe to run alongside a live bridge |

## Open questions

- **The success path still stops commanding** (R7). The user's call, not fixed here.
- **Both new defaults are desk-tuned.** 0.2 rad and 0.25 rad/s are Rethink's,
  but validated here only against a mock that echoes commands with zero lag and
  zero physics. A real series-elastic arm lags. If either fires on a move the
  arm visibly completed, the tolerance is too tight, not the arm broken —
  `docs/hardware_test_commands.md` §7 now says so and gives the override.
- **F8 (bridge backpressure) is now partly observable.** `ROS1Publisher.publish`
  can block up to 0.5 s inside the ROS 2 callback, which exceeds the robot's
  0.2 s `joint_command_timeout`. A stall like that now shows up as growing
  tracking error rather than only as visible stutter, so a path-tolerance abort
  on hardware is a possible F8 symptom and should be read as one before
  loosening the tolerance.
- **F5 (2.0 s blind window on `/robot/state`) is partly covered.** Path
  tolerance is independent of state freshness, so a feed that dies silently now
  produces growing error. Still not a substitute for the e-stop.
- The stopped-velocity check has never seen a non-zero velocity from the real
  bridge — only from `MockRobot.velocity`. The deserializer is verified, the
  end-to-end path is not.

## Artifacts

| Path | Change |
|---|---|
| `src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py` | `path_tolerance_rad`, `stopped_velocity_tolerance` and `goal_time_sec` parameters; velocity tracking in `_joint_state_cb`; `_worst_tracking_error()`, `_worst_moving_joint()`; two abort branches; `_hold_position(positions, duration)` with a safety check; clamp-aware velocity validation |
| `src/baxter_hardware_bridge/baxter_hardware_bridge/mock_robot.py` | `command_feedthrough` and `velocity` test hooks; `JointState.velocity` now populated |
| `src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py` | `send_and_wait()` helper; Tests 17, 18, 19, 20 |
| `src/baxter_hardware_bridge/launch/dry_run.launch.py` | `mock_mode` launch argument, default `true` |
| `src/baxter_examples/baxter_examples/{sim_tiny_trajectory,moveit_pose,moveit_left_tiny}.py` | guarded the `except BaseException` cancellation cleanup (R6) |
| `.github/workflows/ci.yml` | AST check rejecting an unguarded `_cancel_active_goal()` in an `except BaseException` handler |
| `docs/hardware_runbook.md` | 19-case count, closed-loop rehearsal commands, abort table, two new parameter rows, hold-vs-stop safety rule |
| `docs/hardware_test_commands.md` | §7 tolerance-abort expectations and override, two troubleshooting rows, I17 gate row |
| `docs/i12_completion_plan.md` | Phases A and B marked done; Phase C flagged as what remains |
| `MASTER_PLAN.md` | I17 entry; I12 "Second blocker" paragraph replaced with a resolved "Command path" line; dependency graph |
| `CHANGELOG.md` | Unreleased Added ×3, Fixed ×1 |

## Next

`docs/i12_completion_plan.md` Phase C — the robot day. Prompt appended to
`PROMPTS.md`. Nothing in the command path is known to be missing; what remains
is `tuck_arms.py -u` under supervision and the I12 gate itself.
