---
step: I11
title: "Hardware Action Shims And Safety Tools"
agent_date: 2026-07-22
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I14, I15]
---

# I11: Hardware Action Shims And Safety Tools

Gate **PASSED** on the real robot with **zero motion**. The robot was left
disabled (`ready=false enabled=false`) and tucked for the whole test, which is
precisely what makes the safety-interlock proof meaningful.

## Gate Evidence

Shims launched against the live bridge:

```text
left_arm_shim:  Action shim ready: /robot/limb/left/follow_joint_trajectory
                -> /robot/limb/left/joint_command (mock_mode=False)
right_arm_shim: Action shim ready: /robot/limb/right/follow_joint_trajectory
                -> /robot/limb/right/joint_command (mock_mode=False)

$ ros2 action list
/robot/limb/left/follow_joint_trajectory
/robot/limb/right/follow_joint_trajectory
```

Three rejection paths, all `Goal was rejected.`:

| Test | Goal | Shim reason |
|---|---|---|
| 1 | 7 bogus joint names | `joint names mismatch. Expected ['left_s0', ...], got ['bogus_a', ...]` |
| 2 | correct names, 3 positions | `point 0 has 3 positions, expected 7` |
| 3 | fully valid goal | `robot not safe for motion: ready=False enabled=False stopped=False error=False estop_button=0 estop_source=0` |

Test 3 is the one that could not be proven in I10-prep's mock: a
well-formed, in-range goal refused purely because the real robot reports
itself disabled.

No motion — joint positions before and after were identical within encoder
noise (`left s1=-2.175` both times, s0 drifted 0.002).

## Cross-Validation Of The Bridge

`baxter_tools`' own `enable_robot.py -s`, running as a native ROS 1 node
against the robot, reports exactly what our bridge reports
(`ready: False enabled: False stopped: False error: False estop_button: 0`).
Two independent paths agreeing is good evidence the bridge's `AssemblyState`
deserialization is correct.

## Blocking Finding For I12: Do Not Hand-Write Trajectories

The I12 procedure previously documented in the runbook was **unsafe**. In
`follow_joint_trajectory_shim.py::_run_trajectory`, a point whose
`time_from_start` is 0 makes the interpolation loop exit immediately
(`if now >= target_time: break`) and fall through to
`self._publish_command(list(point.positions))` — point 0 is commanded
**directly**, from wherever the arm actually is.

The old example's first point was a hardcoded pose. From the measured tucked
pose that is a ~1.6 rad sweep on s1, ~1.8 on e1 and ~3.0 on e0, as the
first-ever hardware motion.

Replaced with `sim_tiny_trajectory`, which already implemented the correct
pattern for sim: measured start position, `choose_reversible_target()` inside
the joint limits with margin, 0.02 rad verification, and a return leg. Its
only sim-specific parts were the hardcoded controller action names and the
`/joint_states` topic; those are now the parameters `left_action`,
`right_action`, `joint_states_topic`, all defaulting to the previous sim
values (verified unchanged, so sim is unaffected).

Its guard also fires correctly on hardware — with the arms tucked
(`s1=-2.175`, outside its `[-2.147, 1.047]` table) it refuses to move:

```text
[ERROR] s1 start -2.175 rad is outside [-2.147, 1.047]
[ros2run]: Process exited with failure 1
```

## Enable/Untuck Path (from the legacy Noetic workspace)

`~/baxter_noetic_ws/src/baxter_noetic/baxter_tools` runs fine from the laptop
in the `baxter-noetic:n07` container — **no SSH needed** (SSH has no key and
prompts for a password). Two flags are required:

- `--network host`
- `--add-host=011412P0024.local:<ip>` — the robot advertises its nodes as
  `http://011412P0024.local:PORT/` and the container has no mDNS resolver.
  Without it: `TimeoutError: Failed to get robot state on robot/state`.

Untuck targets read from `baxter_tools/scripts/tuck_arms.py`:

| | s0 | s1 | e0 | e1 | w0 | w1 | w2 |
|---|---|---|---|---|---|---|---|
| left | -0.08 | **-1.0** | -1.19 | 1.94 | 0.67 | 1.03 | -0.50 |
| right | 0.08 | **-1.0** | 1.19 | 1.94 | -0.67 | 1.03 | 0.50 |

`s1 = -1.0` after untuck makes the I12 target `-0.65`, well inside limits.
`tuck_arms.py` is also the right tool because it disables collision avoidance
while leaving the shipping pose.

## Master Hygiene Fix

Last session's one-shot scripts left five dead nodes registered on the
robot's master (`/sonar_ctl`, `/sonar_ctl_read`, `/sonar_probe_en`,
`/sonar_verify`, `/sonar_watch`), because `ROS1Publisher`/`ROS1Subscriber`
only unregistered on a clean receive-loop exit. Added `SlaveApi.track()` +
`unregister_all()` on an `atexit` hook, and made `ROS1Subscriber.stop()`
unregister. Verified: a fresh `sonar_ctl.py status` run now leaves nothing
behind. The four older dead entries were cleared via the master's
`unregisterSubscriber`/`unregisterPublisher` API after confirming their
XML-RPC endpoints were dead.

## Artifacts

- `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py` — action/topic params
- `scripts/py_bridge.py` — unregister on exit
- `docs/hardware_test_commands.md` — **new**, full session command sheet
- `docs/hardware_runbook.md` — unsafe I12 block replaced
- `logs/I11_hardware_action_shims.log.md` (this file)

## Next

I12 is unblocked but **not started**: it needs enable + untuck, a clear
workspace, and a reachable e-stop, all under supervision.
