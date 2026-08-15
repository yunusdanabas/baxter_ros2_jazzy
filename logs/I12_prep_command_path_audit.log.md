---
step: I12-prep
title: "Command Path Audit Before First Hardware Motion"
agent_date: 2026-07-22
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15]
---

# I12-prep: Command Path Audit Before First Hardware Motion

Audit of the code that will command the physical robot, run **before** any
motion. Every finding below was **reproduced empirically** against `mock_robot`,
not merely read out of the source. No hardware was involved and the robot was
not touched.

Trigger: I12 is about to command a 74 kg robot for the first time. The shim had
passed `dry_run_test` (8/8) and the I11 interlock gate, but both exercise only
*well-formed* goals and a *disabled* robot. Nothing had ever tested what the
shim does with malformed input or a dying feed.

## Task

1. Line-by-line audit of `follow_joint_trajectory_shim.py`, `safety.py`,
   `executor_util.py`, and the `JointCommand` path in `scripts/py_bridge.py`.
2. Reproduce each finding against `mock_robot` so the severity is measured
   rather than argued.
3. Record results here before writing any fix.

## Findings

Severity is **physical risk on hardware**. "Reproduced" means the behaviour was
observed on a running system, with the numbers shown.

### F1 — HIGH — a zero-duration first point bypasses interpolation entirely

`src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py:307`

```python
            self._publish_command(list(point.positions))   # outside the while loop
```

The interpolation loop breaks the instant `now >= target_time` (`:281-283`), and
this publish sits **outside** it, running unconditionally afterwards. With
`time_from_start = 0`, `target_time == start_time` (set at `:241`), so the break
fires on the first iteration and the **raw target is commanded in one shot**. The
measured-position seeding at `:236` — the whole no-lurch mechanism — is bypassed.

Reproduced. Mock at neutral, goal = every joint +1.5 rad, `time_from_start=0`:

```text
measured start:  ['0.000', '-0.550', '0.000', '0.750', '0.000', '1.260', '0.000']
goal point0 t=0: ['1.500', '0.950', '1.500', '2.250', '1.500', '2.760', '1.500']
[F1] goal ACCEPTED
FIRST command published: ['1.500', '0.950', '1.500', '2.250', '1.500', '2.760', '1.500']
>>> jump from measured in ONE command: 1.500 rad
>>> total commands published: 1
```

One `JointCommand`, all seven joints 1.5 rad away, no ramp. Also reachable via
negative `time_from_start` (`sec` is int32), non-monotonic points, or any
segment shorter than one command period (~10 ms at 100 Hz).

The existing mitigation is **procedural only** — a prose warning in
`docs/hardware_runbook.md` and `docs/hardware_test_commands.md` saying not to
hand-write trajectories. That same command sheet's §5 has the operator hand-typing
`ros2 action send_goal` with explicit `time_from_start` fields. Nothing in
`_goal_callback` rejects this shape.

### F2 — HIGH — no value or shape validation anywhere

`_goal_callback:169-208` checks joint-name equality and per-point position count.
That is all. No `isfinite`, no joint limits, no monotonic time, no velocity bound.

Reproduced, both parts:

```text
=== FINDING 2a: NaN positions ===
  [F2a] goal ACCEPTED
  >>> non-finite value reached JointCommand: True

=== FINDING 2b: non-monotonic / negative time_from_start ===
  [F2b-nonmono] goal ACCEPTED
  >>> accepted a trajectory whose point 2 goes BACKWARD in time: True
```

A `NaN` propagates through `interp` (`:290-293`) into `_last_commanded` and out
onto the wire as a position command.

The shim's own header comment (`:22-23`) defers clamping to `SAFE_CMD` in
`baxter_bridge`. **That component does not exist in this repository** and its
behaviour was never verified. The assumption is unfounded here.

### F3 — MEDIUM — goal acceptance checks joint-state *presence*, never *freshness*

`:192-196` tests only `self._latest_joint_state is None`. `safety.py:52-56`
implements a real age check (`is_stale()`) for `/robot/state`, but there is **no
analog for `/robot/joint_states`**.

**Important nuance, found by reproduction — the first attempt did not reproduce
it.** Killing `mock_robot` stops *both* topics, and the `/robot/state` staleness
gate then correctly rejects the goal:

```text
/robot/joint_states last seen 5.01 s ago (feed is dead)
>>> goal accepted with 5.01 s-stale joint data: False
```

F3 is only reachable on a **partial** feed failure — joint_states dying while
state survives. That is a real mode, not a contrived one: `py_bridge.py` runs an
independent thread with its own reconnect loop per ROS 1 subscription, so one can
stall while the other keeps flowing. Reproduced with a fake publisher doing
exactly that:

```text
>>> /robot/joint_states STOPPED (state keeps flowing)
sending goal: /robot/state is FRESH, /robot/joint_states is ~6 s STALE
>>> goal accepted on ~6 s-stale joint_states: True
>>> FINDING 3 CONFIRMED: seeded from a stale position snapshot
```

So the exposure is narrower than a plain code read suggests, but real. The
consequence is that `_last_commanded` is seeded from a stale snapshot, and the
first "smooth" command is silently measured from where the arm *used to be*.

### F4 — MEDIUM — cancel-hold is a single publish, not a hold

`_hold_position()` (`:166-167`) publishes `_last_commanded` **once** (`:265-271`),
then all publishing stops.

Reproduced:

```text
commands during motion: 95
>>> commands published AFTER cancel, over 2.0 s: 1
>>> last command at cancel+0.008 s
```

One command, then silence. The robot's own `joint_command_timeout` (0.2 s) then
expires and the arm falls back to gravity compensation. The docs state "on cancel
the shim holds the **last commanded** pose via `JointCommand`" — that is true for
0.2 s, after which the arm floats.

This also puts the I12 cancel/hold gate at risk: the check measures drift over
1.0 s against a 0.02 rad bar. The mock passes only because it has no physics.

### F5 — MEDIUM — 2.0 s blind window after the state feed dies

`safety.py:20`, `STATE_TIMEOUT_SEC = 2.0`. The gate **is** correctly re-checked
every ~10 ms during execution (`:273-279`) — that part of the design is sound and
worth keeping on record as correct. But after a total loss of `/robot/state` the
shim keeps commanding toward its targets until staleness trips.

Reproduced by killing the feed 2 s into a 10 s trajectory:

```text
>>> commands published AFTER the feed died: 379
>>> last one at kill+1.99 s
>>> shim kept commanding a blind robot for 1.99 s
```

379 `JointCommand` messages sent to a robot whose state we could no longer see.
Shim log confirms the trip point:

```text
[ERROR] Safety violation: ready=True enabled=True stopped=False error=False
        estop_button=0 estop_source=0 (STALE)
```

### F6 / F7 — LOW — theoretical, not reproduced

- **F6, TOCTOU** between the safety check (`:273-279`) and the post-loop publish
  (`:307`). The window is sub-millisecond Python execution and self-corrects on
  the next loop entry. Not triggered in testing; recorded, not acted on.
- **F7, lock-free `_latest_positions`** — `_joint_state_cb:138-143` writes
  per-index without a lock while other executor threads read at `:236`/`:298`.
  The GIL prevents corruption; worst case is a torn read mixing two samples ~10 ms
  apart. Indices stay correctly mapped to joint names, so there is **no**
  wrong-joint-gets-wrong-value risk. Freshness nit only.

### F8 — SUSPECTED — bridge backpressure can drop interpolation samples

`scripts/py_bridge.py:544-565`: `ROS1Publisher.publish` runs synchronously inside
the ROS 2 subscription callback and can block up to `TCPROS_SEND_TIMEOUT_SEC`
(0.5 s, `:46`) per send. Both the shim publisher (`:103-108`) and the bridge
subscriber (`:583-587`) use QoS depth 1 `KEEP_LAST`, so during a stall intermediate
samples are dropped by DDS and only the newest survives. A 0.5 s stall also
exceeds the robot's own 0.2 s `joint_command_timeout`.

**Not reproduced** — depends on real TCP behaviour against the robot, which cannot
be produced statically or against a local mock. Carried as an open risk.

### F9 — NO DEFECT — ordering, units, and wire layouts are correct

Checked explicitly because a mismatch here would send a joint the wrong value:

- `_goal_callback:171` compares `joint_names` with **order-sensitive** equality,
  not a set comparison.
- `_joint_state_cb:138-143` does name-based dict lookup, so wire order does not
  matter.
- `_make_command`/`_publish_command` (`:149-159`) keep `names`/`command` index-paired.
- `JointCommand.msg` (`mode, command, names`, no header) matches
  `py_bridge.py:199-204` field-for-field.
- `AssemblyState.msg` (no header) matches `py_bridge.py:141-150`. The asymmetry
  with `deser_joint_state` (`:153-170`), which *does* skip a ROS 1 `Header`, is
  **correct** per the real message definitions — not a latent version of the I10
  header bug.

Threading: `_goal_active`/`_goal_lock` are held consistently on both the set
(`:200-204`) and reset (`:218-219`, in `finally`) paths, so one-goal-at-a-time
holds and `_last_commanded` is effectively single-threaded in practice.

### F10 — the I12 gate cannot currently be claimed

The gate in `MASTER_PLAN.md` reads "tiny trajectory, **feedback**, result, and
cancel/hold behavior pass for each advertised arm."

The shim publishes feedback (`:296-303`), but:

```text
$ grep -rn "feedback_callback" src/ scripts/
(no matches)
```

Nothing anywhere subscribes to it — not `sim_tiny_trajectory.py`, not
`dry_run_test.py`. Feedback is also published only *inside* the interpolation
loop, so an F1-shaped goal emits none at all.

## Decisions

- **Fix before motion, not after.** F1, F2, F3, F4 and F10 are all reachable from
  the desk and all bear directly on the first hardware motion. F5 is accepted
  as-is; shrinking the window risks false aborts mid-trajectory and the physical
  e-stop is the real mitigation.
- **Two layers for F1**, because they fail differently: reject the bad goal shape
  at accept time (policy), and clamp per-cycle step in `_publish_command`
  (backstop). Every command flows through that one choke point, so the clamp
  neutralises the defect regardless of how the goal was constructed.
- **Reject, do not clamp, for F2.** A malformed goal is a client bug and should
  fail loudly rather than be silently repaired into something adjacent.
- **Reuse `safety.py`'s `is_stale()` shape for F3** rather than inventing a
  second staleness mechanism.
- Sizing note for the clamp: the I12 move is 0.35 rad over 3 s at 100 Hz ≈
  **0.0012 rad/cycle**, so a 0.02 rad/cycle cap (2 rad/s) leaves ~16× headroom and
  never binds in normal operation. Values become node parameters — hardware needs
  a tuning knob, not a constant.

## Open Questions

- **F8** cannot be settled without the real robot. Watch for stutter during the
  I12 run.
- **F4's** replacement hold duration is a judgement call: long enough to be a real
  hold, short enough that the arm stays releasable. ~1.0 s proposed, to be
  confirmed against observed hardware behaviour.
- Whether Baxter's firmware gravity-compensation fallback after
  `joint_command_timeout` is benign in the untucked pose — assumed, not verified.

## Artifacts

- `logs/I12_prep_command_path_audit.log.md` (this file)
- Reproduction scripts are scratch, not committed. They are superseded by the
  permanent regression cases to be added to
  `src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py`, which
  already runs its 8 cases under the same `MultiThreadedExecutor` as production.

## Next

Implement the fixes (F1–F4, F10), extend `dry_run_test.py` with one case per new
rejection path, rebuild, and re-run the mock rehearsal before the supervised
session. Note `baxter_examples` uses `install(PROGRAMS ... RENAME ...)`, which
defeats `--symlink-install` — it is always a copy and **always needs a rebuild
after editing**.

---

# Resolution (2026-07-23, no hardware)

All of F1–F4 and F10 are fixed. `dry_run_test` now runs **16 cases, all PASS**
(exit 0), and the rehearsal against `mock_robot` with the shims publishing for
real (`mock_mode:=false`) verified both arms with feedback and the cancel-hold.

| Finding | Fix | Regression case |
|---|---|---|
| **F1** zero-duration point bypasses interpolation | Two layers, as decided. Policy: `_validate_values` rejects any `time_from_start` that is not strictly increasing, so a 0, negative or non-monotonic point never reaches execution. Backstop: `_publish_command` clamps every joint to `max_step_rad_per_cycle` (0.02 rad/cycle = 2 rad/s at 100 Hz) from the previous command, so no goal shape can produce a lurch | Tests 9, 11, 15 |
| **F2** no value or shape validation | `_validate_values` rejects non-finite positions, positions outside the URDF limits, and any segment whose average speed exceeds the URDF velocity limit. Rejected, not clamped. `JOINT_LIMITS` is transcribed from `baxter_base.urdf.xacro` | Tests 10, 12, 13 |
| **F3** joint_states presence but not freshness | `_joint_states_age_sec()` plus a `joint_states_stale_sec` parameter (default 2.0), mirroring `safety.py`'s `is_stale()` shape rather than inventing a second mechanism | Test 14, using a new `MockRobot.joint_states_enabled` flag to reproduce the partial-feed failure |
| **F4** cancel-hold was a single publish | `_hold_position()` republishes at command rate for `hold_duration_sec` (default 1.0). Measured: **97 commands over 0.99 s**, against exactly 1 before | Test 16 |
| **F10** feedback never subscribed anywhere | `sim_tiny_trajectory` passes a `feedback_callback`, counts messages, and now **fails** a goal that succeeds without publishing feedback. Measured 248–272 messages per 3 s trajectory | Test 1 also asserts feedback ≥ 1 |

Two things changed beyond the findings themselves:

- **`sim_tiny_trajectory` no longer sends a leading `t=0` point.** Its own goal
  had exactly the F1 shape. The point was redundant — the shim seeds
  `_last_commanded` from the measured pose at goal start — so dropping it leaves
  behaviour identical and makes the script conform to its own advice.
- **The stale `SAFE_CMD` comment is gone.** The shim header deferred clamping to
  a `baxter_bridge` component that does not exist in this repo; the clamp is now
  local and real.

Also verified over the wire (`ros2 action send_goal` against `mock_robot`, the
same commands now in `docs/hardware_test_commands.md` §5d): bad joint names,
wrong position count, and the audit's own F1 reproduction — every joint 1.5 rad
away at `time_from_start=0` — all print `Goal was rejected.`

## Still open

- **F5** (2.0 s blind window after the state feed dies) — accepted as-is, per the
  decision above. The physical e-stop is the mitigation.
- **F6 / F7** — theoretical, not acted on.
- **F8** (bridge backpressure dropping interpolation samples) — still cannot be
  settled without the real robot. Watch for stutter during the I12 run.
- **`hold_duration_sec = 1.0`** is still a judgement call. Confirm it against
  observed hardware behaviour during the supervised session.
- Whether Baxter's gravity-compensation fallback after `joint_command_timeout`
  is benign in the untucked pose remains assumed, not verified.
