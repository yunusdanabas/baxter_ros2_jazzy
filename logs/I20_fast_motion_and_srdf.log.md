---
step: I20
title: "Fast-Motion Characterisation and the SRDF Re-run"
agent_date: 2026-07-25
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15, I17, I12, I18, I19]
---

# I20: Fast-Motion Characterisation and the SRDF Re-run

## Task

Two things in one sitting: the MoveIt Setup Assistant re-run left over from I18
(item 9), and — the robot being available and supervised — the fast-motion
question that gates every tolerance number in this repo.

Robot: BR-01 `011412P0024` at `192.168.1.232` via `enp4s0`, 0.29 ms RTT.
Supervised throughout, e-stop in hand, sonar off, workspace clear.

## Findings

### F-A. `path_tolerance_rad` is a speed limit, not slack

**The headline result.** Stepping `sim_tiny_trajectory` up in speed, with the
in-flight lag measured as `|command − measured|` from a ROS 1 capture:

| requested | max lag | outcome |
|---|---|---|
| 0.12 rad/s | 0.0369 rad | pass, settled error 0.004–0.006 |
| 0.23 rad/s | 0.0936 rad | pass, settled error 0.017–0.020 |
| 0.50 rad/s | 0.1979 rad | **abort** — `left_s1 lags its setpoint by 0.202 rad (limit 0.200)` |

Lag is linear in commanded velocity at ≈ **0.4 s** of it: the arm runs a constant
*time* behind its setpoint, not a constant distance. So the tolerance converts
directly into a speed ceiling:

- `path_tolerance_rad` 0.2 → ~0.5 rad/s (measured, aborts there)
- 0.15 → ~0.37 rad/s
- 0.05 (the value I18 F3 proposed and F22 withdrew) → ~0.12 rad/s, i.e. the
  default move itself

The 2.0 rad/s per-cycle clamp is therefore unreachable — the tolerance binds four
times sooner. Every "how much margin does 0.2 have" discussion in I18 was asking
the wrong question: there is no margin to reclaim, only a speed/abort trade.

After the abort the arm held to **0.0004 rad over 6 s**, so the abort-and-hold
path works on hardware exactly as designed.

### F-B. The Setup Assistant's sampling does not converge for this robot

`ros2 run moveit_setup_assistant collisions_updater` is the GUI's collision step
without the GUI, so item 9 could be measured instead of clicked. Against the same
URDF the MoveIt config uses:

| `--trials` | pairs disabled |
|---|---|
| 10 000 (GUI default) | 311 |
| 25 000 | 300 |
| 100 000 | 282 |
| 250 000 | 278 |
| 1 000 000 | 269 |
| 2 000 000 | 263 |

Every doubling finds more pairs that *can* collide, so every lower density had
disabled them wrongly. The pairs the low densities get wrong are the dangerous
class: at the GUI default, `head <-> l_gripper_l_finger`,
`l_gripper_l_finger_tip <-> screen` and 32 others are disabled — the planner
would be free to drive a gripper into Baxter's own head and screen.

**Decision: keep the existing 54-pair matrix.** It is conservative — fewer
disabled pairs means more checking, so it yields false positives (the untuck
pose, already fixed by hand) rather than false negatives. Nothing is blocked on
it today, and 200+ speculative disables from a non-converging sampler is not a
trade worth making on a robot that moves.

`--keep` does preserve the hand-added pairs, so if this is ever revisited: high
`--trials`, `--keep`, and re-enable every head/screen pair by hand afterwards.

### F-C. The multi-publisher fix broke the motion client (found on hardware)

The I12 gate failed at the first attempt with
`Missing joints in /joint_states: ['left_s0', ...]` while the bridge was
delivering all 19 joints correctly.

Baxter publishes `/robot/joint_states` from two nodes — `/realtime_loop`
(17 arm+head joints, ~100 Hz) and `/end_effector_publisher` (one gripper joint,
~40 Hz). Measured on the ROS 2 side: 139.5 Hz total, message shapes
`{17: 801, 1: 316}` over 8 s. So roughly a third of messages carry no arm at all,
and `sim_tiny_trajectory` kept only the *last* message.

This was invisible until now. Before I18's F13 fix the bridge delivered only the
realtime loop, so every message had the arm in it — fixing the bridge is what
exposed the client. Fixed by keeping a merged name→position view, the same shape
the action shim already uses.

### F-D. Everything I19 changed, confirmed on hardware

| I19 item | Hardware evidence |
|---|---|
| Publisher-count gate (F1) | `safe_for_motion=False` with **no** `CONTESTED` — exactly one publisher on the real graph, no false positive |
| Real md5sum (F23) | `1014 decoded` / `848 decoded` joint_command messages; first capture ever measurable as `\|command − measured\|` |
| Preserved `header.stamp` (F14) | Robot stamp arrives intact, skew **+0.014 s** against host clock. No clock-skew warning fired; MoveIt logged zero staleness complaints |
| Cancel-hold settle window (F2) | Sweep at 0.5 s and 2.0 s both pass, drift 0.0061 / 0.0065 rad, "settled in 2.06 s" — the *first* window exceeded tolerance and the retry caught it, which is precisely the false failure I18 F2 hit |
| `duration`/`offset` (F9) | The mechanism for F-A above |
| Clean shutdown (F17) | SIGINT, no traceback, log ends on its own last line |

### F-E. Untuck, again, ended enabled

`tuck_arms.py -u` succeeded first attempt in ~22 s and left the robot
`ready=true enabled=true`, matching I18 F5. The runbook's warning that a
successful untuck can end `enabled: False` has now failed to happen twice; it is
a possible outcome, not the normal one.

### F-F. MoveIt on hardware: the left arm aborts on its roll joints

Run from the RViz MotionPlanning panel at the end of the session, driven by the
human, planning mostly the `both_arms` group.

| Arm | Goals | Succeeded | Aborted |
|---|---|---|---|
| **left** | 11 | 3 | **8** |
| right | 11 | 9 | 2 |

Every abort was `PATH_TOLERANCE_VIOLATED` at exactly the limit — `-0.201`,
`-0.200`, `0.200`, `0.202` — never a large excursion, and always on the same two
joints:

| Joint | Aborts |
|---|---|
| `left_w0` (wrist roll) | 5 |
| `left_e0` (elbow roll) | 3 |
| `right_s0` | 1 |
| `right_w0` | 1 |

The right arm's two failures were both inside the first 40 s; afterwards it
completed nine in a row, **including the executions where the left arm aborted
on the same `both_arms` plan**. move_group logged 8 × `CONTROL_FAILED`: one
controller aborting takes the whole dual-arm execution down, so every failure was
the left arm ending the right arm's otherwise good trajectory.

This is the F-A coupling again — lag ≈ 0.4 s × velocity, and MoveIt plans the
wrists fast because `w0`'s URDF limit is 4.0 rad/s — but it is now *joint
specific*, and it refines I18 F10. F10 found the **right** arm tracking 1.4×
worse on `s1`; here the **left** is worse on `w0`/`e0`. Both can hold: which arm
tracks worse is a property of the joint, not of the arm.

Duration is not the explanation. One left goal ran 7 s and succeeded while others
aborted 3–6 s in.

**What this data cannot settle:** whether `left_w0` was *commanded* faster than
`right_w0` (asymmetric plan) or commanded the same and *tracked* worse
(asymmetric hardware). That needs the commanded velocity at each abort, and no
bag was recording during the RViz session — the recorder had been stopped after
the scripted speed steps. Recording through the MoveIt phase would have answered
it; that is the process lesson from this session.

**The test that settles it**, ~10 minutes with the recorder on: identical
single-joint moves on `left_w0` and `right_w0`, same `offset` and `duration`,
stepped up in speed until each aborts. Left aborting sooner means the joint is
genuinely slower and the answer is a per-joint tolerance or speed limit; both
aborting together means the plan was asymmetric and the answer is MoveIt-side
scaling. `sim_tiny_trajectory` gained a `joint` parameter for exactly this
(`a5b69b0`) — it could previously only move `s1`.

**Using MoveIt on this robot meanwhile:** Velocity Scaling 0.1 in the
MotionPlanning panel, and plan the single-arm `left_arm` / `right_arm` groups
rather than `both_arms`, so one arm's lag cannot abort the other's trajectory.

## Gate evidence

```text
P1 bring-up   bridge up, no clock-skew warning; 19 joints @ 139.5 Hz incl. grippers;
              sonar 4095 -> 0; both shims up; safe_for_motion=False (disabled), no CONTESTED
P2 interlocks 4/4 rejected with the robot disabled (valid goal, bad joints,
              short positions, over-clamp wrist)
P3 untuck     first attempt, ~22 s, ready=true enabled=true, s1 -1.035 / -1.046
P4 I12 gate   both arms out and back, max_error 0.0040 / 0.0043 / 0.0058 / 0.0061 rad
P4a speed     see F-A; stopped at the abort per the day plan's rule
P6 cancel     0.5 s and 2.0 s, drift 0.0061 / 0.0065 rad
P7 MoveIt     planning scene clean against the live robot: 0 staleness complaints,
              /check_state_validity answers. Plan+execute then run by the human
              from RViz: 3/11 left goals succeeded, 9/11 right — see F-F
P9 shutdown   tucked (-2.174 / -2.181), disabled, sonar 0, no stale ROS 1
              registrations, ROS 2 graph empty
```

Capture: `data/sessions/2026-07-25/ros1/full_120951_*.bag` (6.1 MB, gitignored).

## Decisions

| Decision | Why |
|---|---|
| Keep the 54-pair collision matrix | The regenerated one comes from a sampler that has not converged, and its errors are gripper-into-head. Conservative beats speculative on a robot that moves |
| Do not tighten `path_tolerance_rad` | It is the speed limit. Tightening trades speed for nothing; 0.15 would cap the arm at ~0.37 rad/s |
| Do not run MoveIt plan+execute | The runbook requires inspecting the preview before executing, and that needs a human at RViz. The specific risk from I19's stamp change was staleness, which was checked directly instead |
| Merge joint states in the client rather than filter by publisher | Same shape the shim already uses; a client should not need to know how many nodes publish a topic |

## Open Questions

- **What does *raising* `path_tolerance_rad` buy?** The curve below 0.5 rad/s is
  now known; the untested direction is 0.3–0.4 rad and whether tracking stays
  safe there. That is the experiment worth the next robot session.
- **Is `left_w0` slower than `right_w0`, or was the plan asymmetric?** (F-F.)
  The single decisive experiment, now that `sim_tiny_trajectory` can move an
  arbitrary joint. Record through it.
- **MoveIt's default velocity scaling is unusable here.** Anything that plans the
  wrists near their 4.0 rad/s URDF limit will abort against a 0.2 rad tolerance.
  Either scaling stays at 0.1 by convention, or the shim grows per-joint
  tolerances, or `path_tolerance_rad` goes up — the same trade as F-A.
- **`speed_ratio` remains inert** (I18 F9). Now that duration is the known knob,
  it may be worth removing the parameter rather than leaving a control that does
  nothing.
- Right arm was never taken past 0.23 rad/s — the left aborted first, and the
  client stops on the first failure. The right arm tracks ~1.4× worse (I18 F10),
  so its abort speed is probably lower.

## Artifacts

| Path | Change |
|---|---|
| `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py` | Merged joint-state view across publishers (F-C) |
| `scripts/check_srdf.py` | Negative-control pose: a matrix that disables everything now fails |
| `docs/moveit_guide.md` | The trials table, why the matrix was not adopted, and how to revisit it |
| `docs/hardware_runbook.md` | `path_tolerance_rad` row rewritten as a speed limit |
| `docs/hardware_day_plan.md` | P4a table with measured lag per step; next experiment redirected |
| `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py` | `joint` parameter and a per-suffix limit table, so the same joint can be compared across arms (F-F) |
| `docs/hardware_test_commands.md` | The ready-to-run `left_w0` vs `right_w0` comparison |
| `docs/i12_completion_plan.md` | The outlived caveat resolved |

Commits: `18d26dd` (F-C), `a1bb40d` (F-B), `f787a20` (F-A), `a5b69b0` (F-F tooling).
