# Baxter Hardware Test — Command Sheet

Copy-paste sheet for a full hardware session. Every command here was run
against the real robot on 2026-07-22 unless marked **[not yet run]**.

Robot: `011412P0024.local` (mDNS). Its IP is a DHCP lease and **moves** — never
hardcode it.

**Safety, before anything:** clear workspace, e-stop within reach, nobody
inside arm reach. The physical e-stop is the primary emergency stop.

---

## 0. Pre-flight — network (do this first)

This is where sessions actually get stuck. All four must pass.

```bash
cd ~/baxter_ros2_jazzy

# 1. robot resolves
getent hosts 011412P0024.local

# 2. reachable
ping -c3 $(getent hosts 011412P0024.local | awk '{print $1}')

# 3. THE important one: route must go out ethernet, not wifi
ip route get $(getent hosts 011412P0024.local | awk '{print $1}')

# 4. ROS 1 master listening
timeout 3 bash -c "echo > /dev/tcp/$(getent hosts 011412P0024.local | awk '{print $1}')/11311" \
  && echo "11311 OPEN"
```

Expected on step 3: `... dev enp4s0 src 192.168.1.x`.

If it says `via 10.80.96.1 dev wlp0s20f3`, the laptop has no address on the
robot's subnet. Every ROS connection will then fail with unrelated-looking
symptoms. Fix:

```bash
nmcli connection modify "Wired connection 1" ipv4.method auto
nmcli connection up "Wired connection 1"
```

---

## 1. Environment (every terminal)

```bash
cd ~/baxter_ros2_jazzy
source scripts/baxter_env.sh
```

Prints the resolved robot IP, and `ROS_IP` derived from the route toward the
robot. Do **not** set `ROS_DOMAIN_ID`. `LC_NUMERIC=C` is set for you.

---

## 2. Terminal 1 — bridge (leave running)

```bash
cd ~/baxter_ros2_jazzy && source scripts/baxter_env.sh
python3 scripts/py_bridge.py
```

Expected: `Bridge started: master=http://<robot>:11311 ip=<laptop>` and
**no** `deserialize failed` warnings.

Verify in another terminal:

```bash
source scripts/baxter_env.sh
ros2 topic hz /robot/joint_states     # ~100 Hz, stable
ros2 topic echo --once /robot/state
```

---

## 3. Head sonar (optional)

```bash
python3 scripts/sonar_ctl.py status
python3 scripts/sonar_ctl.py off
python3 scripts/sonar_ctl.py on      # restore
```

Resets to all-on when the robot reboots. Disabling removes proximity sensing —
e-stop and supervision remain your safety controls.

---

## 4. Terminal 2 — action shims (leave running)

```bash
cd ~/baxter_ros2_jazzy && source scripts/baxter_env.sh
ros2 launch baxter_hardware_bridge hardware_bringup.launch.py
```

Expected, both arms:
`Action shim ready: /robot/limb/<side>/follow_joint_trajectory -> ... (mock_mode=False)`

```bash
ros2 action list
#   /robot/limb/left/follow_joint_trajectory
#   /robot/limb/right/follow_joint_trajectory
```

---

## 5. I11 gate — safety interlock, ZERO motion  ✅ PASSED

Run these **while the robot is still disabled**. All three must be rejected,
and the robot must not move. This is the real proof of the interlock.

```bash
# 5a. bad joint names -> REJECTED
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [bogus_a,bogus_b,bogus_c,bogus_d,bogus_e,bogus_f,bogus_g],
    points: [{positions: [0,0,0,0,0,0,0], time_from_start: {sec: 2}}]}}"

# 5b. right joints, wrong position count -> REJECTED
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [left_s0,left_s1,left_e0,left_e1,left_w0,left_w1,left_w2],
    points: [{positions: [0,0,0], time_from_start: {sec: 2}}]}}"

# 5c. fully valid goal, robot disabled -> REJECTED by safety gate
#     Positions are deliberately inside the joint limits: the tucked pose
#     itself (s1=-2.175, e0=3.056) is now rejected by the limits check first,
#     which would prove nothing about the safety gate.
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [left_s0,left_s1,left_e0,left_e1,left_w0,left_w1,left_w2],
    points: [{positions: [-0.986,-2.100,3.040,2.509,0.173,0.059,-0.073],
              time_from_start: {sec: 2}}]}}"
```

All three printed `Goal was rejected.`, with shim reasons:

```
Rejected: joint names mismatch. Expected ['left_s0', ...], got ['bogus_a', ...]
Rejected: point 0 has 3 positions, expected 7
Rejected: robot not safe for motion: ready=False enabled=False stopped=False
          error=False estop_button=0 estop_source=0
```

### 5d. Malformed goals — rejected regardless of robot state

These need no enable and cause no motion. Each was a shape the shim used to
accept and command straight through to the robot; all now reject at accept time
(verified against `mock_robot` 2026-07-23). The first one is the important one:
a `time_from_start` of 0 used to bypass interpolation entirely and command the
raw target in a single `JointCommand`.

```bash
# t=0 first point -> REJECTED ("time_from_start=0.000s must be greater than ...")
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [left_s0,left_s1,left_e0,left_e1,left_w0,left_w1,left_w2],
    points: [{positions: [1.5,0.95,1.5,2.25,1.5,2.76,1.5], time_from_start: {sec: 0}}]}}"

# position outside joint limits -> REJECTED (s1 lower limit is -2.147)
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [left_s0,left_s1,left_e0,left_e1,left_w0,left_w1,left_w2],
    points: [{positions: [0,-2.175,0,0.75,0,1.26,0], time_from_start: {sec: 5}}]}}"

# faster than the joint's velocity limit -> REJECTED (s0 limit is 1.5 rad/s)
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [left_s0,left_s1,left_e0,left_e1,left_w0,left_w1,left_w2],
    points: [{positions: [1.5,-0.55,0,0.75,0,1.26,0], time_from_start: {nanosec: 100000000}}]}}"
```

---

## 6. Enable and untuck — via `baxter_tools` from the laptop

Use the official SDK tools from `~/baxter_noetic_ws` in the Noetic container.
**No SSH needed** (SSH has no key installed and would prompt for a password).
Use these tools rather than hand-publishing `/robot/set_super_enable`.

Two flags matter:

- `--network host` so the container shares the robot-facing interface
- `--add-host=011412P0024.local:<robot-ip>` — **required**. The robot
  advertises its nodes as `http://011412P0024.local:PORT/`, and the container
  has no mDNS resolver. Without this you get
  `TimeoutError: Failed to get robot state on robot/state`.

Convenience wrapper:

```bash
baxrun() {
  local ip; ip=$(getent hosts 011412P0024.local | awk '{print $1}')
  docker run --rm -it --network host --add-host=011412P0024.local:"$ip" \
    -e ROS_MASTER_URI=http://"$ip":11311 -e ROS_IP="$(ip route get "$ip" | grep -oP 'src \K\S+')" \
    baxter-noetic:n07 bash -lc "source /root/baxter_ws/install/setup.bash && $*"
}
baxtool() { baxrun "rosrun baxter_tools $*"; }
```

`baxrun` runs any command in the Noetic container; `baxtool` is the
`baxter_tools` shortcut. Drop `-t` from `docker run` when redirecting output to
a file.

```bash
baxtool enable_robot.py -s     # status — read-only, safe  ✅ verified working
```

> ### ⚠ Known problem: `enable_robot.py -e` fails from the tucked pose
>
> ```
> [ERROR] Failed to enable robot
> ```
>
> Ruled out: e-stop (`estop_button=0`), faults (`error=false stopped=false`),
> connectivity (status query works), diagnostics (no ERROR entry).
> `ready=false` is *not* a separate fault — it just means "not enabled".
>
> Also ruled out by measurement (2026-07-22, zero motion), so **do not
> re-test these**:
>
> - *Slow TCPROS negotiation.* `/realtime_loop` attaches to a fresh
>   `robot/set_super_enable` publisher in **0.24 s**, well inside
>   `_toggle_enabled`'s 2.0 s budget. The enable requests reached the robot.
> - *Robot health.* 15 s of `/diagnostics` = 201 statuses, 200 at level 0:
>   `Robot Config [OK]`, `Realtime Control Loop` OK at 100 Hz with 0.00% recent
>   overruns, every joint OK on thermal/sds/sensor_consistency/voltage,
>   software version `1.2.0.57`, calibration slopes present for all 14 joints.
>
> The one abnormal signal is `/diagnostics`:
> `[WARN] Collision detection: Collision detected on jointleft_s1` — expected
> when tucked, because the arms sit inside the head/arm collision force-field.
> Its payload shows it cannot self-clear: `impact torque -3.57737` against
> `scaled impact threshold 0` (the threshold scales with the velocity and
> acceleration commands, both 0 while disabled). So the flag stays latched for
> as long as the robot is disabled and tucked.
>
> `tuck_arms.py` handles this and `enable_robot.py` does not:
> it publishes `suppress_collision_avoidance` *before and while* enabling, and
> republishes `set_super_enable` at 20 Hz until the state flips, where
> `enable_robot.py` gives up after a single 2.0 s `wait_for`.
>
> **So prefer `tuck_arms.py -u` — it does enable + untuck together.**

> **Untuck is a large whole-arm motion (head + both arms).** Clear workspace,
> e-stop in hand, nobody within reach.

```bash
baxtool tuck_arms.py -u        # enable + untuck  [NOT YET RUN]
```

If that hangs without ever enabling, the collision-suppression theory is wrong.
Do **not** go re-check homing or calibration — the health sweep above already
cleared those. The remaining lead is `rethink.log` on the robot itself, which
needs a shell we do not have.

Only then, as a supervised diagnostic with the e-stop in hand, is hand-driving
the enable justified — collision suppression **first**, enable last, 15 s cap:

```bash
# T-A and T-B, one per arm, started first
baxrun "rostopic pub -r 20 robot/limb/left/suppress_collision_avoidance std_msgs/Empty '{}'"
baxrun "rostopic pub -r 20 robot/limb/right/suppress_collision_avoidance std_msgs/Empty '{}'"
# T-C: watch state   |   T-D: started LAST
ros2 topic echo /robot/state
baxrun "rostopic pub -r 20 robot/set_super_enable std_msgs/Bool 'data: true'"
```

Enabled → Ctrl-C T-D, then T-A/T-B, then run `tuck_arms.py -u` normally.
Still disabled at 15 s → Ctrl-C all four, `baxtool enable_robot.py -d`, stop.
This is the documented exception to the "never hand-publish" rule; it is what
`tuck_arms.py` does internally.

`tuck_arms.py` is the tool to use — it disables collision avoidance while
leaving the shipping pose and drives both arms to the proper untuck targets:

| | s0 | s1 | e0 | e1 | w0 | w1 | w2 |
|---|---|---|---|---|---|---|---|
| left untuck | -0.08 | **-1.0** | -1.19 | 1.94 | 0.67 | 1.03 | -0.50 |
| right untuck | 0.08 | **-1.0** | 1.19 | 1.94 | -0.67 | 1.03 | 0.50 |

`s1 = -1.0` after untuck is what makes step 7 valid: the script's target
becomes `-0.65`, well inside the `[-2.147, 1.047]` limit.

> ### Expect `enabled: False` after a *successful* untuck
>
> `tuck_arms.py::_move_to` ends with:
>
> ```python
> if any(self._arm_state['collide'].values()):
>     self._rs.disable()
> ```
>
> So if either arm still reports a collision object when the move finishes,
> the script **disables the robot on its way out**. A successful untuck can
> therefore leave `enabled: False`. That is not a failure — check the arm
> positions, not the enable flag.
>
> By then `s1 ≈ -1.0`, above `tuck_arms.py`'s `_peak_angle = -1.6`, so the arms
> are **out** of the head/arm force-field that blocked enable from tucked. Plain
> enable should now work where it failed before:
>
> ```bash
> baxtool enable_robot.py -s     # if enabled: False after untuck
> baxtool enable_robot.py -e     # should now SUCCEED — arms are clear of the field
> ```
>
> If `-e` still fails with the arms untucked, the force-field theory is wrong
> and the connectivity/health results above are the ones to re-read.

Confirm before continuing — both must be true:

```bash
ros2 run baxter_hardware_bridge baxter_safety_check
# want: safe_for_motion=True  ready=True enabled=True stopped=False error=False
```

---

## 7. I12 gate — supervised motion, both arms [not yet run]

> **Do not hand-write trajectories.** The shim now rejects a `time_from_start`
> of 0 on the first point (§5d) and clamps every command to 0.02 rad/cycle, but
> use the script anyway — it reads the measured start position, picks a
> reversible target inside the joint limits, verifies the result within
> 0.02 rad, and returns to start.

```bash
cd ~/baxter_ros2_jazzy && source scripts/baxter_env.sh

ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states
```

Moves s1 by 0.35 rad over 3 s at speed ratio 0.1, left arm then right, each
outbound **and back**. Expected per arm:

```
/robot/limb/<side>/follow_joint_trajectory outbound feedback: NNN messages
/robot/limb/<side>/follow_joint_trajectory outbound verified: max_error=0.00xx rad
/robot/limb/<side>/follow_joint_trajectory return   feedback: NNN messages
/robot/limb/<side>/follow_joint_trajectory return   verified: max_error=0.00xx rad
Reversible trajectories verified for both arms
```

The feedback line is part of the I12 gate: the script now fails if a goal
succeeds without publishing feedback.

Two aborts are new here and have never run against a real arm — both stop the
goal but keep holding, so the arm does not sag:

```
Path tolerance violated: left_s1 lags its setpoint by 0.2xx rad (limit 0.200 rad)
Goal tolerance violated: left_s1 still moving at 0.xxx rad/s (limit 0.250 rad/s)
```

`path_tolerance_rad` (0.2) and `stopped_velocity_tolerance` (0.25) are Rethink's
own defaults but are desk-tuned here against a mock with no physics. If either
fires on a move the arm visibly completed, the tolerance is too tight rather than
the arm broken — re-run with `-p path_tolerance_rad:=0.3` on the shims and record
the value that worked.

Guard rail already proven: with the arms tucked (`s1=-2.175`, outside the
`[-2.147, 1.047]` limit table) the script refuses to move and exits 1 —

```
[ERROR] s1 start -2.175 rad is outside [-2.147, 1.047]
```

So if you see that, the arms are still tucked. Go back to step 6.

### 7b. Cancel-and-hold test [not yet run]

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states \
  -p cancel_after_sec:=1.0
```

Expected: `Active trajectory canceled; controller is holding position`, then a
drift check on two later joint states. The arm must stop and hold, not fall.

---

## 8. Shutdown / restore [not yet run]

```bash
baxtool tuck_arms.py -t        # back to shipping pose
baxtool enable_robot.py -d     # disable
```

Then Ctrl-C the shims (terminal 2) and the bridge (terminal 1), in that order.

---

## Abort procedures

| Situation | Do this |
|---|---|
| Anything unexpected during motion | **Hit the physical e-stop.** |
| Want to stop a running goal cleanly | Ctrl-C the `sim_tiny_trajectory` process — it cancels the active goal and the shim holds position |
| Shim misbehaving | Ctrl-C terminal 2; the robot stops receiving `joint_command` and times out after `command_timeout` (0.2 s) |
| Robot enabled but should not be | `baxtool enable_robot.py -d` |
| Robot in error state | `baxtool enable_robot.py -r` (reset), then re-check status |

Do **not** publish to `/robot/set_super_stop` for routine cancellation, and
do **not** publish to `/robot/set_super_enable` at all.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ip route get` shows `dev wlp0s20f3` | Laptop not on robot's subnet — see step 0 |
| Bridge logs `deserialize failed` | Message layout mismatch. ROS 1 `Header` = `uint32 seq` + `time` + `frame_id`; ROS 2 dropped `seq` |
| Goal rejected, `ready=False enabled=False` | Robot disabled — step 6 |
| `s1 start ... outside [...]` | Arms still tucked — step 6 |
| Phantom `/sonar_*` nodes in `rosnode list` | Stale registrations from killed scripts. Now auto-unregistered on exit; old ones need manual cleanup |
| Action server not found | Shims not running — step 4 |
| `Path tolerance violated` | Arm lagged its setpoint by >0.2 rad. Either the bridge is stalling (F8 backpressure) or the desk-tuned default is too tight for a real arm — see step 7 |
| `Goal tolerance violated` | Arm still moving >0.25 rad/s when the trajectory ended. Expected on a real arm only if it is oscillating or the bridge is behind |

---

## Gate status

| Gate | Status |
|---|---|
| I10 non-motion | **PASS** (2026-07-22) |
| I11 action shims / safety interlock | **PASS** (2026-07-22, zero motion) |
| I12 command-path hardening | **DONE** (2026-07-23, no hardware) — F1–F4 and F10 from `logs/I12_prep_command_path_audit.log.md` are fixed and covered by `dry_run_test` (16/16). Rehearsed against `mock_robot`: both arms verified with feedback, cancel-hold verified. |
| I17 pre-hardware hardening | **DONE** (2026-07-23, no hardware) — path tolerance and stopped-velocity monitoring added, `dry_run_test` now 20/20, closed-loop rehearsal re-run. See `logs/I17_pre_hardware_hardening.log.md`. |
| I12 supervised motion | **BLOCKED** — robot will not enable from the tucked pose (see step 6). Diagnosed 2026-07-22: not connectivity, not health, not calibration; only the latched `left_s1` collision remains. Next action is `tuck_arms.py -u` under supervision. |

## Robot identity

| Field | Value |
|---|---|
| S/N | `011412P0024` (= the mDNS hostname) |
| Model | **BR-01**, Baxter *Research* Robot |
| Manufactured | 12/2014 |

## Where the last session stopped

Robot left `enabled=false` and tucked, positions unchanged, no motion
performed. Head sonar OFF. Bridge and shims stopped. Resume at step 0, then
step 6.
