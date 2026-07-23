# I12 Completion Plan — hardening, checking, robot day

Working plan for finishing I12 (supervised hardware motion). Written 2026-07-23.
Retire this file once the I12 gate passes and its findings are folded into
`logs/` and `MASTER_PLAN.md`.

## Context

I12 was blocked on two independent items. The command-path hardening (F1–F4,
F10 from `logs/I12_prep_command_path_audit.log.md`) is **done** as of
2026-07-23: goals are validated at accept time, every command is clamped to
`max_step_rad_per_cycle`, cancel holds for a real duration, and feedback is
verified end to end. `dry_run_test` covers it with 16 cases and CI already runs
it (`.github/workflows/ci.yml:92`). I17 took that to 20.

What remains is one blocker that needs the robot (enable-from-tucked), plus a
short list of gaps found by comparing our shim against the legacy ROS 1
`JointTrajectoryActionServer` in `plan/baxter_noetic_ref/baxter_interface/`.

The comparison produced one finding worth acting on. Rethink shipped
`PositionJointTrajectoryActionServer.cfg` with **path tolerance enabled at
0.2 rad** and stopped-velocity at 0.25, but per-joint **goal position tolerance
disabled** (`-1.0`, and the code skips the check when it is not positive). Our
shim has none of the three. So the one they relied on in practice — path
tolerance — is the one we should add.

> **Phases A and B are done** (I17, 2026-07-23, no hardware). `dry_run_test` is
> 20/20 and the closed-loop rehearsal passes for both arms plus cancel-hold. The
> sections below are kept as the record of what was decided and why; the
> as-built result is in `logs/I17_pre_hardware_hardening.log.md`. **Phase C, the
> robot day, is what remains.**

## Phase A — desk work, before the robot day  ✅ done

### A1. Path tolerance monitoring (highest value)  ✅ done

`src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py`

Inside the existing interpolation loop, compare the commanded setpoint against
`self._latest_positions` each cycle and abort when any joint exceeds
`path_tolerance_rad` (new parameter, default **0.2**, from the legacy cfg).
Both values are already in scope, so this is roughly fifteen lines.

Beyond parity with the legacy, this is a failure detector **independent of
`/robot/state` freshness**, so it partially covers the F5 blind window that was
accepted as-is: a feed that dies silently still shows up as growing error.

**Decide before writing: hold or stop commanding on violation.** Our safety
path deliberately stops commanding (correct for an e-stop). A path-tolerance
violation is different — the arm is lagging, not unsafe — and stopping commands
lets it sag into gravity compensation after the robot's 0.2 s timeout. The
legacy holds, via `_command_stop`. **Recommend: hold**, reusing the existing
`_hold_position()`. Use a distinct result code so it is not confused with a
safety abort.

### A2. Stopped-velocity check at goal end  ✅ done

Same file. After the trajectory completes, verify no joint is still moving
faster than `stopped_velocity_tolerance` (new parameter, default **0.25**, from
the legacy cfg).

Feasible because `deser_joint_state` in `scripts/py_bridge.py:153` already
unpacks the ROS 1 `velocity` and `effort` arrays into the ROS 2 `JointState` —
verified, since this item is dead if the bridge dropped velocity.

Skip per-joint **goal position** tolerance: Rethink shipped it disabled, and
`sim_tiny_trajectory` already checks final error client-side at 0.02 rad.

### A3. `mock_mode` launch argument for the dry-run launch  ✅ done

`src/baxter_hardware_bridge/launch/dry_run.launch.py`

Both shims currently hardcode `"mock_mode": True`, so the shims never publish
`JointCommand`, the mock arm can never move, and any trajectory run against this
launch file fails its position check. This cost a confusing test cycle on
2026-07-23; the rehearsal had to be done by hand-starting `mock_robot` plus two
shims with `mock_mode:=false`.

Add one `DeclareLaunchArgument("mock_mode", default_value="true")` and wire it to
both nodes, matching the pattern already in `hardware_bringup.launch.py:22`.
Default stays `true`, so existing behaviour is unchanged.

### A4. Regression cases for A1 and A2  ✅ done

`src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py`

Extend the existing 16-case suite, reusing the `expect_reject` helper and the
`make_goal(joints, [(positions, seconds)])` builder:

- **Path tolerance trips.** Freeze the mock's command feedthrough mid-trajectory
  (same technique as `MockRobot.joint_states_enabled`, added for Test 14) so the
  measured position stops following the setpoint, then assert the goal aborts
  with the path-tolerance code and that the shim keeps publishing a hold.
- **Path tolerance does not trip in normal operation.** The existing happy-path
  Test 1 already covers this implicitly; assert it explicitly so a too-tight
  default fails at the desk rather than on the robot.
- **Stopped-velocity check.** The mock has no physics and reports zero velocity,
  so a positive case is trivial; drive a non-zero velocity into the mock's
  `JointState` to exercise the failure branch.

## Phase B — checking and polishing  ✅ done

Run after Phase A, before the robot day. This is a review pass over everything
touched on 2026-07-22 and 2026-07-23, not new features.

### B1. Review the uncommitted diff

There are roughly 1100 uncommitted lines spanning `scripts/py_bridge.py`, the
shim, the examples, and the docs. Read it as one changeset. Decide the commit
boundaries — the hardware-session work and the F1–F4/F10 hardening are two
separate reviewable commits.

### B2. Documentation consistency sweep

The same facts are now stated in several places and must agree:

| File | Must say |
|---|---|
| `docs/hardware_runbook.md` | validation table, abort table, parameter table, 20 dry-run cases |
| `docs/hardware_test_commands.md` | §5c in-limit positions, §5d malformed goals, gate table |
| `logs/I12_prep_command_path_audit.log.md` | Resolution section, per-finding |
| `logs/I12_supervised_hardware_motion.log.md` | second blocker cleared |
| `MASTER_PLAN.md` | **stale — still describes the command-path blocker as open** |
| `CHANGELOG.md` | Unreleased/Added + Fixed entries for the hardening |

Any parameter added in Phase A must land in the runbook's parameter table with
its default, and any new rejection reason in its validation table.

### B3. `MASTER_PLAN.md` and the Baton bookkeeping

`AGENTS.md` and `WORKFLOW.md` require that a step's status line be updated and a
log exist before it counts as done. The I12 entry still carries a "Second
blocker" paragraph telling a future agent to fix what is already fixed. The gate
itself has **not** passed — that needs the robot — so update the blocker list to
name only enable-from-tucked, and leave the status `blocked`.

`PROMPTS.md` is append-only; if the robot-day session runs as a fresh Baton leg,
it needs a self-contained prompt appended, containing every path and prior
decision it must not rediscover.

### B4. Verify nothing regressed

```bash
colcon build --base-paths src --symlink-install --packages-select \
  baxter_hardware_bridge baxter_examples
source install/setup.bash
ros2 run baxter_hardware_bridge dry_run_test        # expect OVERALL: PASS, exit 0
```

Then the closed-loop rehearsal, which needs the shims actually publishing —
after A3 this becomes a single launch:

```bash
ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states
# and again with -p cancel_after_sec:=1.0
```

Expect both arms verified with a feedback count, and the cancellation hold
verified. Confirm CI is green — it already runs `dry_run_test`.

## Phase C — robot day  ← next

Follow `docs/hardware_test_commands.md` from §0. The delta versus the last
session:

1. §0–§4 pre-flight, bridge, shims. Confirm the route goes out ethernet, not
   wifi — that is where sessions actually get stuck.
2. §5 interlock gate, then **§5d malformed goals**. Both are zero-motion and can
   run while still disabled. §5d has so far been verified against the mock only;
   this confirms the validation behaves the same with a real bridge in the path.
3. §6 `baxtool tuck_arms.py -u` **under supervision** — the remaining blocker.
   `enabled: False` after a successful untuck is normal; check arm positions,
   not the flag. If it hangs without enabling, the force-field theory is wrong;
   do not re-check health or calibration, those were already cleared. The only
   remaining lead is `rethink.log` on the robot, which needs a shell we do not
   have.
4. §7 I12 gate, both arms, now with a testable feedback clause.
5. §7b cancel-and-hold.
6. §8 shutdown: tuck, disable, stop shims then bridge.

### Values to confirm on hardware

These are desk-tuned guesses that a real series-elastic arm can invalidate:

| Parameter | Default | Risk if wrong |
|---|---|---|
| `path_tolerance_rad` | 0.2 | Too tight false-aborts mid-trajectory; a real joint lags in a way the mock never does |
| `stopped_velocity_tolerance` | 0.25 | Too tight fails a goal the arm actually completed, if the arm settles slowly |
| `hold_duration_sec` | 1.0 | Too short and the arm floats after cancel |
| `max_step_rad_per_cycle` | 0.02 | Should never bind on the I12 move (~0.0012 rad/cycle); a clamp warning means something upstream is wrong |

### Watch for

**F8 — bridge backpressure.** `ROS1Publisher.publish` runs synchronously inside
the ROS 2 callback and can block up to 0.5 s, which exceeds the robot's 0.2 s
`joint_command_timeout`; with depth-1 QoS on both sides, intermediate samples are
dropped. Not reproducible against a mock. Stutter during the I12 run is the
symptom. This is the only audit finding that can be settled only on hardware.

## Deferred, with reasons

| Item | Why not now |
|---|---|
| Bezier / minjerk interpolation | ~620 lines to maintain. Portable (BSD, pure numpy, no ROS deps), but MoveIt time-parameterizes densely enough that linear tracks it closely. Revisit only if jerk appears at waypoint boundaries |
| Cuff / zero-G button | Needs a third bridged topic; `DigitalIOState.msg` exists but a deserializer does not. Cost is in the bridge, not the shim |
| Live parameter tuning | `add_on_set_parameters_callback`. Only matters if retuning on the robot means restarting nodes |
| Per-joint goal position tolerance | Rethink shipped it disabled |
| Velocity mode + PID | **Do not port.** Closes a 100 Hz loop across a bridge with a 0.5 s worst-case stall (F8). The robot runs its own joint controllers |
| Inverse-dynamics feedforward | **Do not port.** Requires `RAW_POSITION_MODE`, which bypasses collision avoidance — the subsystem currently latching `left_s1`, and one we deliberately kept |
| F5 blind window | Accepted; shrinking it risks false aborts mid-trajectory and the e-stop is the real mitigation. A1 partially covers it |
| F6 / F7 | Theoretical, sub-millisecond TOCTOU and a GIL-protected torn read |

## Definition of done

- ~~`dry_run_test` passes with the Phase A cases added, and CI is green.~~ 20/20.
- ~~The closed-loop mock rehearsal passes for both arms, with feedback and a
  verified cancellation hold.~~ Done, `mock_mode:=false`.
- ~~Docs, logs, `MASTER_PLAN.md` and `CHANGELOG.md` agree with each other.~~ Done.
- The I12 gate passes on hardware: tiny trajectory, feedback, result, and
  cancel/hold for each advertised arm — with evidence in
  `logs/I12_supervised_hardware_motion.log.md`.
