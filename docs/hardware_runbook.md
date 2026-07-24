# Baxter Hardware Runbook

Prep-only lab procedures. Hardware bridge support is **blocked** until the I10
gate passes; this runbook is not a support claim.

## Prerequisites

- Laptop on the same subnet as Baxter, via the lab switch
- ROS 2 Jazzy workspace built: `colcon build --base-paths src --packages-skip baxter_bridge`
- Baxter powered on with ROS 1 master running

> **Source `scripts/baxter_env.sh` before building, not just before running.**
> An active conda/mamba env puts its `python3` first on `PATH`, and setuptools
> bakes that interpreter into the shebang of every installed entry point. The
> build succeeds, then every `ros2 run` and the shim launch fail at runtime with
> `No module named 'rclpy._rclpy_pybind11'`, because rclpy's C extension is built
> for the system python3.12. `baxter_env.sh` strips conda from `PATH`, which fixes
> both the build and the run. Check with
> `head -1 install/baxter_hardware_bridge/lib/baxter_hardware_bridge/dry_run_test` —
> it must say `/usr/bin/python3`.

## Network Setup (do this first — it is where sessions actually get stuck)

Baxter is addressed by its mDNS hostname **`011412P0024.local`** (from the
robot's serial). Its IP is a DHCP lease and **moves between sessions** — do
not hardcode it. As observed on 2026-07-22 it was `192.168.1.232`, and while
the robot was still booting it briefly self-assigned the link-local address
`169.254.8.12`.

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

`dry_run_test` prints `OVERALL: PASS` over 20 cases and runs under the same
`MultiThreadedExecutor` as production shim `main()` — it covers mid-goal cancel,
unsafe abort, concurrent-goal rejection, the no-lurch seeding check, every
goal-validation rejection below, the step clamp, the cancel-hold duration, and
both tolerance aborts.

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

`test_bridge_loopback.sh` negotiates real TCPROS against a genuine `roscore`, so
it needs a local ROS 1 Noetic image tagged `baxter-noetic:audit`. Nothing in this
repo builds it; if `docker image inspect baxter-noetic:audit` fails, build one
from any `ros:noetic-ros-base` and tag it, or skip this check — it exercises the
bridge protocol layer only, not the shim. Expected on success:
`OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy)`.

## Quick Start (3 terminals)

### Terminal 1: Start the bridge

```bash
cd ~/baxter_ros2_jazzy
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
source scripts/baxter_env.sh
ros2 launch baxter_hardware_bridge hardware_bringup.launch.py
```

This starts `FollowJointTrajectory` action servers on:
- `/robot/limb/left/follow_joint_trajectory`
- `/robot/limb/right/follow_joint_trajectory`

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

> **Open problem (2026-07-22):** `enable_robot.py -e` fails with
> `Failed to enable robot` from the tucked pose, with no e-stop, no fault and
> a clean state.
>
> Diagnosed the same day with zero motion. **Not** connectivity
> (`/realtime_loop` attaches to a fresh enable publisher in 0.24 s, so the
> requests arrived), **not** robot health (201 `/diagnostics` statuses, 200 at
> level 0; `Robot Config [OK]`, control loop OK at 100 Hz), **not** calibration
> (slopes present for all 14 joints, software `1.2.0.57`).
>
> What remains is the collision force-field: `Collision detected on
> jointleft_s1` with `impact torque -3.57737` against `scaled impact threshold
> 0`. The threshold scales with the velocity/acceleration commands, which are 0
> while disabled — so the flag stays latched as long as the robot is disabled
> and tucked, and retrying `enable_robot.py` can never clear it. `tuck_arms.py`
> suppresses collision avoidance and republishes enable at 20 Hz;
> `enable_robot.py` does neither. See
> `logs/I12_supervised_hardware_motion.log.md`.

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
- No motion until I10 gate passes

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
| `path_tolerance_rad` | `0.2` | How far a joint may lag its commanded setpoint before the goal aborts and holds. Rethink's `PositionJointTrajectoryActionServer.cfg` default; **desk-tuned only** — a real series-elastic arm lags in ways the mock never does, so watch for false aborts on the first hardware run |
| `goal_time_sec` | `0.1` | How long the final point keeps being commanded before the stopped-velocity check runs. Rethink's `goal_time`. Interpolation is linear, so without it the check samples the arm's cruise speed rather than its stopped speed |
| `stopped_velocity_tolerance` | `0.25` | Speed above which a joint counts as still moving once the trajectory is done. Also from the legacy cfg. Needs the bridge's `velocity` array, which `deser_joint_state` does unpack |
| `hold_duration_sec` | `1.0` | How long a canceled or tolerance-aborted goal keeps republishing its hold pose |
| `joint_states_stale_sec` | `2.0` | Age at which `/robot/joint_states` is too old to accept a goal |
| `speed_ratio` | `0.1` | Published to the robot on startup and each accepted goal |
| `command_timeout` | `0.2` | Robot-side `joint_command_timeout` |
| `command_rate` | `100.0` | Interpolation/publish rate in Hz |

If the clamp binds you get a throttled `Command step clamped to ... rad/cycle`
warning — that means something upstream asked for a faster move than intended.
