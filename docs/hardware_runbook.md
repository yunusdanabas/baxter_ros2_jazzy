# Baxter Hardware Runbook

Lab procedures for the hardware path. The bridge, the action shims and
supervised motion have all passed their gates on BR-01 `011412P0024` — I10/I11 on
2026-07-22, I12 on 2026-07-24 — under supervision, at low speed. That is a
starting point for a supervised session, not permission to run unattended.

## Prerequisites

- Laptop on the same subnet as Baxter, via the lab switch
- ROS 2 Jazzy workspace built: `colcon build --base-paths src --packages-skip baxter_bridge`
- Baxter powered on with ROS 1 master running

> **Set `BAXTER_HOST` and source `scripts/baxter_env.sh` before building, not
> just before running.** Scripts do not hardcode a lab serial or IP — export the
> robot's mDNS hostname first (for this lab BR-01: `export
> BAXTER_HOST=011412P0024.local`). An active conda/mamba env puts its `python3`
> first on `PATH`, and setuptools bakes that interpreter into the shebang of
> every installed entry point. The build succeeds, then every `ros2 run` and the
> shim launch fail at runtime with `No module named 'rclpy._rclpy_pybind11'`,
> because rclpy's C extension is built for the system python3.12.
> `baxter_env.sh` strips conda from `PATH`, which fixes both the build and the
> run. Check with
> `head -1 install/baxter_hardware_bridge/lib/baxter_hardware_bridge/dry_run_test` —
> it must say `/usr/bin/python3`.

## Network Setup (do this first — it is where sessions actually get stuck)

Baxter is addressed by its mDNS hostname (from the robot's serial). For the
supervised sessions documented here that was **`011412P0024.local`**. Its IP is
a DHCP lease and **moves between sessions** — do not hardcode it, and do not
rely on a script default. As observed on 2026-07-22 it was `192.168.1.232`, and
while the robot was still booting it briefly self-assigned the link-local
address `169.254.8.12`.

The laptop's ethernet (`enp4s0`) must hold an address **on the robot's
subnet**, obtained from the same DHCP server:

```bash
nmcli connection modify "Wired connection 1" ipv4.method auto
nmcli connection up "Wired connection 1"
```

Verify before going further — all three must succeed:

```bash
getent hosts 011412P0024.local          # resolves to the robot's current IP
ping -c3 $(getent hosts 011412P0024.local | awk '{print $1}')
ip route get $(getent hosts 011412P0024.local | awk '{print $1}')   # must say dev enp4s0
```

The route check is the one that matters. If it reports `via <wifi-gateway>
dev wlp0s20f3`, the laptop has no address on the robot's subnet and every
ROS connection will fail with confusing symptoms. `scripts/baxter_env.sh`
derives `ROS_IP` from this route, so it is correct automatically once the
route is.

## Pre-Lab Check (before leaving for the robot)

Run these hardware-free checks (any cwd is fine for the loopback script):

```bash
ros2 run baxter_hardware_bridge dry_run_test    # no extra prerequisites
bash scripts/test_bridge_loopback.sh            # needs the Docker image below
```

`dry_run_test` prints `OVERALL: PASS` over 25 cases and runs under the same
`MultiThreadedExecutor` as production shim `main()` — it covers mid-goal cancel,
unsafe abort, concurrent-goal rejection, the no-lurch seeding check, every
goal-validation rejection below, the step clamp, the cancel-hold duration, both
tolerance aborts, the MoveIt-shaped goals (leading `t=0` point, permuted joint
order), and the second-publisher safety gate.

For a closed-loop rehearsal — the shims commanding `mock_robot` for real, rather
than skipping the publish — use the launch file and the supported client:

```bash
ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states
```

Without `mock_mode:=false` the shims publish no `JointCommand` at all, so the
mock arm never moves and any trajectory fails its position check.

**Stop that stack before running `dry_run_test` again.** Both advertise the same
action names and `/robot/state`, and `dry_run_test` starts its own shim and mock
in-process; with two of each on the graph the client binds to whichever answers
first and the results are nonsense rather than an obvious error. `Ctrl-C` on the
launch does not always reap the nodes — check with
`pgrep -af "mock_robot|follow_joint_trajectory_shim"` and expect no output.

Two traps make "I stopped that" untrue, and both have cost real session time:

- **`ros2 run` starts the node as a child process.** Killing the PID you
  backgrounded kills the wrapper and leaves the node running, orphaned and still
  publishing — `ros2 node list` will keep showing it, correctly. Find the real
  one with `ps -eo pid,ppid,cmd | grep <node>` and kill that. Never use
  `pkill -f`: the pattern matches the shell running it, which is how a
  `ros2 launch` parent once died while its shims survived as orphans.
- **`baxter_examples` edits now take effect without a rebuild.** Both it and
  `baxter_hardware_bridge` are `ament_python`, so `--symlink-install` really
  symlinks and `ros2 run baxter_examples ...` runs the file you just edited.
  Until I21 it was `ament_cmake` with `install(PROGRAMS ...)`, which copies even
  under `--symlink-install`; that is how two I19 rehearsals silently tested
  stale code. If you are on a workspace built before I21, rebuild once.

`test_bridge_loopback.sh` negotiates real TCPROS against a genuine `roscore`, so
it needs a local ROS 1 Noetic image, `baxter-noetic:n07` by default (override
with `IMAGE=`). Nothing in this repo builds it — it comes from a separate ROS 1
workspace on the bridge host — so if `docker image inspect baxter-noetic:n07`
fails, rebuild it there or skip this check: it exercises the bridge protocol
layer only, not the shim. It must run on the **host** Docker daemon:
ROS 1 needs host networking, and a `docker system prune` has removed this image
before. Expected on success:
`OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy)`.

### What still needs the Noetic Docker image

`scripts/py_bridge.py`, the action shims, and most of a supervised session already
run without Docker. The ~5 GB `baxter-noetic` image is still required for:

| Capability | Why |
|---|---|
| `tuck_arms.py -u` | Untuck out of the enable force-field; tucked `s1` is outside the URDF limit table, so a shim-based untuck would command outside the safety envelope |
| `enable_robot.py` / `rosbag record` (ROS 1 side) | Convenience today; enable could be a small `py_bridge` publish later |
| `test_bridge_loopback.sh` | Desk protocol test against genuine `roscore` |

Publishing a new ROS 1 type from `py_bridge` needs an `ROS1_MSG_META` entry if
recordings must decode; subscribe-side negotiation still uses a wildcard md5sum.

## Quick Start (3 terminals)

### Terminal 1: Start the bridge

```bash
cd ~/baxter_ros2_jazzy
export BAXTER_HOST=011412P0024.local   # your robot's mDNS hostname
source scripts/baxter_env.sh
python3 scripts/py_bridge.py
```

This connects to Baxter's ROS 1 master, bridges `/robot/state` and `/robot/joint_states`
to ROS 2, and bridges `/robot/limb/{side}/joint_command` back to ROS 1.

Wait until you see: `Bridge started: master=http://<robot-ip>:11311 ip=<laptop-ip>`,
and confirm no `deserialize failed` warnings follow.

### Terminal 2: Verify robot state (I10 non-motion gate)

```bash
cd ~/baxter_ros2_jazzy
export BAXTER_HOST=011412P0024.local
source scripts/baxter_env.sh
ros2 topic echo /robot/state
ros2 topic hz /robot/joint_states
```

You should see:
- `/robot/state` messages with `ready=true enabled=true stopped=false error=false`
- `/robot/joint_states` at a stable rate with all 14 arm joints + head_pan

### Terminal 3: Start action shims

```bash
cd ~/baxter_ros2_jazzy
export BAXTER_HOST=011412P0024.local
source scripts/baxter_env.sh
ros2 launch baxter_hardware_bridge hardware_bringup.launch.py
```

This starts `FollowJointTrajectory` action servers on:
- `/robot/limb/left/follow_joint_trajectory`
- `/robot/limb/right/follow_joint_trajectory`

The launch checks the graph first and **aborts** if `mock_baxter_robot` is
running, because it publishes a permanently "safe" `/robot/state`:

```text
[ERROR] [launch]: ... mock_baxter_robot is running; it publishes a fake safe
/robot/state. Stop it (kill by PID) and confirm `ros2 node list` is clean
before bringing up the hardware shims.
```

Kill it by its **child** PID (see the two traps above), confirm `ros2 node list`
is clean, and relaunch.

## I10 Non-Motion Gate Checklist

Run these BEFORE any motion:

1. **Network**: robot pings and `ip route get <robot-ip>` shows `dev enp4s0`
2. **Bridge running**: Terminal 1 shows "Bridge started"
3. **Robot state**: `ros2 topic echo /robot/state` shows safe state
4. **Joint states**: `ros2 topic hz /robot/joint_states` is stable
5. **Action servers**: `ros2 action list` shows both follow_joint_trajectory actions
6. **Safety check**: `ros2 run baxter_hardware_bridge baxter_safety_check` prints safe=true

## Head Sonar — turn it OFF (required, non-motion)

**Disable the head sonar at bring-up, before the shims start.** This is a
standing requirement for sessions here, not an optional convenience.

The 12-transducer head sonar ring is on by default and is noisy in a lab. It
is controlled by a bitmask on `/robot/sonar/head_sonar/set_sonars_enabled`
(`std_msgs/UInt16`), with the live value echoed on `.../sonars_enabled`:

```bash
python3 scripts/sonar_ctl.py off     # disable all 12
python3 scripts/sonar_ctl.py on      # restore all 12 (0x0FFF)
python3 scripts/sonar_ctl.py status  # read current bitmask
```

This is a runtime setting on `/realtime_loop` — it **resets to all-on when
the robot reboots**, so re-run it each session. Note that disabling sonar
removes Baxter's proximity/approach sensing; the physical e-stop and human
supervision remain the primary safety controls for I12 motion.

## I11 Action Shim Gate (no motion yet)

```bash
# Verify shims reject unsafe goals:
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [bad_name], points: []}}" \
  --feedback
# Expected: REJECTED (bad joint names)
```

## I12 Supervised Hardware Motion

**REQUIRES physical supervision, clear workspace, e-stop reachable.**

See `hardware_test_commands.md` for the full copy-paste sequence, including
the `baxtool` wrapper used below.

> **`enable_robot.py -e` cannot enable a tucked robot — use `tuck_arms.py -u`.**
> Diagnosed 2026-07-22, confirmed 2026-07-24.
>
> From the tucked pose `enable_robot.py -e` returns `Failed to enable robot`
> with no e-stop, no fault and a clean state. The cause is the collision
> force-field: `Collision detected on jointleft_s1`, `impact torque -3.57737`
> against `scaled impact threshold 0`. The threshold scales with the
> velocity/acceleration commands, which are 0 while disabled — so the flag stays
> latched as long as the robot is disabled and tucked, and retrying can never
> clear it.
>
> Ruled out by measurement, so do not re-check them: connectivity
> (`/realtime_loop` attaches to a fresh enable publisher in 0.24 s), robot health
> (201 `/diagnostics` statuses, 200 at level 0; `Robot Config [OK]`, control loop
> at 100 Hz), calibration (slopes present for all 14 joints, software
> `1.2.0.57`).
>
> `tuck_arms.py -u` suppresses collision avoidance and republishes enable at
> 20 Hz; `enable_robot.py` does neither. It worked on the **first attempt**, in
> ~23 s. One documented expectation did not hold: the warning that a successful
> untuck can end `enabled: False` is a *possible* outcome, not the normal one —
> that run ended `ready=True enabled=True`. Check arm position (`s1 ≈ -1.0`),
> not the flag. Evidence: `logs/I18_hardware_day.log.md` (F5).

Enable and untuck with `tuck_arms.py`, which does both and handles the
collision force-field (never hand-publish `/robot/set_super_enable`):

```bash
baxtool tuck_arms.py -u
```

> **Do not hand-write trajectories.** The shim now rejects a `time_from_start`
> of 0 on the first point (that shape used to be commanded in a single step)
> and clamps every command to `max_step_rad_per_cycle`, but a goal that passes
> validation is still a goal you have to have gotten right.
>
> Use `sim_tiny_trajectory`, which reads the **measured** start position,
> picks a reversible target inside the joint limits, verifies the result
> within 0.02 rad, and returns to start:

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states
```

Add `-p cancel_after_sec:=1.0` for the cancel-and-hold check.

At session end:

```bash
baxtool tuck_arms.py -t
baxtool enable_robot.py -d
```

## If Baxter's ROS 1 Master Is Not Responding

SSH into Baxter and restart it:

```bash
ssh ruser@011412P0024.local
# On Baxter:
sudo service roscore stop
sudo service roscore start
# Or manually:
roscore &
```

## Safety Rules

- **Never** publish to `/robot/set_super_enable` from beginner examples
- **Never** publish to `/robot/set_super_stop` for routine cancellation
- On cancel, the shim holds the **last commanded** pose via `JointCommand`,
  republished for `hold_duration_sec`. A single publish would expire with the
  robot's own 0.2 s `joint_command_timeout` and the arm would then fall back to
  gravity compensation instead of holding
- On a safety violation (e-stop, disable, stale `/robot/state`) the shim
  **stops commanding entirely** — it does not try to hold through an e-stop.
  This applies during a hold too: a hold in progress is abandoned
- On a tolerance violation (arm lagging its setpoint, or still moving at goal
  end) the shim aborts but **holds**, not stops. A lagging arm is not an unsafe
  robot, and stopping commands would drop it into gravity compensation after the
  robot's 0.2 s `joint_command_timeout`
- A goal is rejected unless `/robot/joint_states` is present **and fresher than
  `joint_states_stale_sec`**, and the shim seeds from measured joint positions
  at each goal start, so the first command continues from where the arm actually
  is rather than jumping
- Only one goal executes per arm; a second goal is rejected while one runs
- Speed ratio defaults to 0.1 (10%) — keep it low for labs
- Physical e-stop is the primary emergency stop
- **Motion is refused unless exactly one node publishes `/robot/state`.** A
  second publisher — a leftover `mock_baxter_robot`, an orphaned shim — makes it
  unknowable whose state the gate just read, and a mock advertising "safe"
  alongside the real disabled robot is how a goal gets accepted that must be
  rejected. The rejection says
  `CONTESTED: N publishers on /robot/state, expected 1`
- `hardware_bringup.launch.py` refuses to start at all if `mock_baxter_robot` is
  in the node list

### Goal validation

Malformed goals are **rejected, not repaired** — a bad goal is a client bug and
should fail loudly. Every rejection logs its specific reason. A goal is rejected
when any of these hold:

| Check | Rejected when |
|---|---|
| Joint names | not exactly the arm's 7 names, in order |
| Point length | any point's `positions` is not 7 long |
| joint_states freshness | last `/robot/joint_states` older than `joint_states_stale_sec` |
| Finite values | any position is `NaN` or `inf` |
| Position limits | any position outside the URDF `lower`/`upper` for that joint |
| Timing | `time_from_start` not strictly increasing, including a 0 or negative first point |
| Velocity | any segment's average speed exceeds the URDF `velocity` limit for that joint, **or** the speed the per-cycle clamp can deliver (`max_step_rad_per_cycle` x `command_rate`, 2.0 rad/s by default). The rejection names which of the two bound |
| Robot state | `/robot/state` not safe, or stale |
| Concurrency | another goal is already executing on that arm |

Limits come from `baxter_description/urdf/baxter_base/baxter_base.urdf.xacro`
and are transcribed into `JOINT_LIMITS` in `follow_joint_trajectory_shim.py`.

### Aborts after acceptance

A goal that was accepted can still end early. Each abort carries a distinct
`error_code`, so a client never has to parse `error_string` to tell them apart:

| Abort | `error_code` | Raised when | Commanding |
|---|---:|---|---|
| Safety violation | `-101` | `/robot/state` becomes unsafe or stale mid-goal | **stops** |
| Cancel | `-100` | client cancels | holds |
| Path tolerance | `-4` (`PATH_TOLERANCE_VIOLATED`) | a joint lags the command actually sent by more than `path_tolerance_rad` | holds the **measured** pose |
| Stopped velocity | `-5` (`GOAL_TOLERANCE_VIOLATED`) | a joint is still moving faster than `stopped_velocity_tolerance` after the final point has been held for `goal_time_sec` | holds |

Path tolerance compares against the command the shim actually published, not the
raw interpolated setpoint, so an executor stall cannot blame the arm for a
setpoint it was never given. A path-tolerance abort holds where the arm **is**,
not where it was told to be — holding the unreachable setpoint would keep driving
a blocked arm into whatever is blocking it. It is skipped when `mock_mode` is
true: nothing is published, so the measured pose cannot track by construction. It is also a failure detector that
does **not** depend on `/robot/state` freshness — a feed that dies silently
still shows up as growing error.

### Shim parameters

Tuning knobs on `follow_joint_trajectory_shim`, all settable with `--ros-args -p`:

| Parameter | Default | Meaning |
|---|---|---|
| `max_step_rad_per_cycle` | `0.02` | Hard cap on how far one command may move a joint from the previous one. At 100 Hz that is 2 rad/s. The I12 move needs ~0.0012 rad/cycle, so it never binds normally. This is the backstop: every command passes through it, whatever the goal looked like |
| `path_tolerance_rad` | `0.2` | How far a joint may lag its commanded setpoint before the goal aborts and holds. **This is the speed limit.** Measured 2026-07-25 across three speeds: lag ≈ 0.4 s × commanded velocity, so 0.2 rad aborts at ~0.5 rad/s — confirmed, `left_s1 lags its setpoint by 0.202 rad` at exactly 0.50 rad/s. Raising it buys speed; lowering it costs speed (0.15 → ~0.37 rad/s, the once-proposed 0.05 → ~0.12 rad/s, barely the default move). It is not slack to be trimmed |
| `goal_time_sec` | `0.1` | How long the final point keeps being commanded before the stopped-velocity check runs. Rethink's `goal_time`. Interpolation is linear, so without it the check samples the arm's cruise speed rather than its stopped speed |
| `stopped_velocity_tolerance` | `0.25` | Speed above which a joint counts as still moving once the trajectory is done. Also from the legacy cfg. Needs the bridge's `velocity` array, which `deser_joint_state` unpacks. Never fired on hardware: every goal settled in ≤0.01 s |
| `hold_duration_sec` | `1.0` | How long a canceled or tolerance-aborted goal keeps republishing its hold pose |
| `joint_states_stale_sec` | `2.0` | Age at which `/robot/joint_states` is too old to accept a goal |
| `speed_ratio` | `0.1` | Published to the robot on startup and each accepted goal |
| `command_timeout` | `0.2` | Robot-side `joint_command_timeout` |
| `command_rate` | `100.0` | Interpolation/publish rate in Hz |

If the clamp binds you get a throttled `Command step clamped to ... rad/cycle`
warning — that means something upstream asked for a faster move than intended.
