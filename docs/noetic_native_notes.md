# Notes for a Native ROS 1 Noetic Baxter Stack

Working notes for a future control stack that runs **directly on ROS 1 Noetic
against Baxter's own master** — no ROS 2, no bridge. Everything here is
robot-side behavior: what the hardware actually does, as opposed to what the
SDK documents.

Seeded from the ROS 2 port's hardware sessions. Sections marked _(to fill)_ get
filled during a robot day — see `docs/hardware_day_plan.md` stage S6.

`docs/container_free_path.md` is the practical head start: the enable sequence and
the reference-joint-state plumbing described there are components this native stack
needs anyway, written against `py_bridge.py`'s pure-Python ROS 1 primitives.

## Robot identity

| Field | Value |
|---|---|
| S/N / mDNS hostname | `011412P0024` → `011412P0024.local` |
| Model | BR-01 Baxter **Research** Robot |
| Manufactured | 12/2014 |
| Software version | `1.2.0.57` (from `/diagnostics`) |
| Master | `http://<robot-ip>:11311` — DHCP lease moves, address by hostname |

The robot advertises its nodes as `http://011412P0024.local:PORT/`. Any client
that cannot resolve that hostname will connect to the master and then time out
fetching state. In a container this means `--add-host`; on a bare Noetic machine
it means working mDNS or an `/etc/hosts` entry.

## Enabling the robot

This is the single hardest-won piece of knowledge here, and a native stack must
reimplement it correctly or it will fail exactly as `enable_robot.py` does.

- **`enable_robot.py -e` fails from the tucked pose.** Not connectivity, not
  health, not calibration — all ruled out by measurement on 2026-07-22.
- **Cause:** tucked arms sit inside the head/arm collision force-field, so
  `/diagnostics` latches `Collision detected on joint left_s1` with
  `impact torque -3.57737` against `scaled impact threshold 0`. The threshold
  scales with the commanded velocity and acceleration, which are both zero while
  the robot is disabled — so the flag **cannot self-clear while tucked and
  disabled**. Deadlock.
- **What works:** publish `robot/limb/<side>/suppress_collision_avoidance`
  (`std_msgs/Empty`, ~20 Hz) *before and during* the enable, and republish
  `robot/set_super_enable` (`std_msgs/Bool`) at 20 Hz until the state flips.
  `tuck_arms.py` does this; `enable_robot.py` gives up after a single 2.0 s
  `wait_for`, which is the whole difference.
- **`ready=false` is not a fault.** It only means "not enabled". Do not chase it.
- **A successful untuck can leave `enabled: False`**: `tuck_arms.py::_move_to`
  calls `self._rs.disable()` on exit if any arm still reports a collision
  object. Verify the outcome by arm **position**, not the enable flag.
- Force-field boundary: `tuck_arms.py`'s `_peak_angle = -1.6`. After untuck
  `s1 ≈ -1.0`, i.e. clear of the field, and plain enable works from there.

Untuck targets:

| | s0 | s1 | e0 | e1 | w0 | w1 | w2 |
|---|---|---|---|---|---|---|---|
| left | -0.08 | **-1.0** | -1.19 | 1.94 | 0.67 | 1.03 | -0.50 |
| right | 0.08 | **-1.0** | 1.19 | 1.94 | -0.67 | 1.03 | 0.50 |

## Commanding motion

- Per-limb topic `robot/limb/<side>/joint_command`
  (`baxter_core_msgs/JointCommand`), POSITION_MODE for position control.
- **`robot/limb/<side>/joint_command_timeout`** (`std_msgs/Float64`): if no
  command arrives within this window the robot falls back to gravity
  compensation and the arm sags. Commands must be **continuously republished**,
  not sent once. The ROS 2 shim publishes at 100 Hz with a 0.2 s timeout.
- **`robot/limb/<side>/set_speed_ratio`** (`std_msgs/Float64`): per-limb. All
  hardware work so far has run at 0.1.
- **`/robot/ref_joint_states`** (`sensor_msgs/JointState`) is the robot's own
  commanded reference, published alongside the measured `/robot/joint_states`.
  For tracking error this is better ground truth than anything reconstructed
  from the command side, and a native stack gets it for free.
- Rate-limiting is the caller's job. The shim clamps each command to
  0.02 rad/cycle at 100 Hz (≈2 rad/s) as a backstop independent of the URDF
  velocity limits, and rejects any trajectory segment it could not deliver
  under that clamp.
- `/realtime_loop` attaches to a freshly registered publisher in ~0.24 s. Budget
  for it; do not assume a just-created publisher is connected.

## Wire-format gotchas

- ROS 1 `Header` is `uint32 seq` + `time stamp` + `string frame_id`. ROS 2
  dropped `seq`. Any hand-written (de)serializer that forgets this misaligns
  every following field — the symptom is a plausible-looking but wrong message,
  not a clean parse error.

## Misc robot behavior

- **Head sonar** powers back on after a robot reboot; it is not persistent
  state. See `scripts/sonar_ctl.py` for the topic used to toggle it.
- Killed scripts leave **stale node registrations** on the master (phantom nodes
  in `rosnode list`). A native stack should unregister on exit rather than rely
  on the master noticing.
- `/diagnostics` is rich and worth mining: per-joint thermal, sds, sensor
  consistency and voltage, plus `Realtime Control Loop` at 100 Hz with an
  overrun percentage.
- SSH to the robot needs a key that is **not** installed on this laptop. Nothing
  in the current workflow requires a robot shell; `rethink.log` on the robot is
  the one thing that would.

---

## Topic / node / service inventory

Measured 2026-07-24 by read-only XML-RPC query against the robot's master
(`getSystemState` / `getTopicTypes` — no node registration):

**202 published topics, 123 subscribed, 89 services, 23 nodes.**

Published topics by prefix — the shape a native stack has to deal with:

| Count | Prefix |
|---|---|
| 58 | `/robot/digital_io` |
| 34 | `/robot/limb` |
| 20 | `/robot/analog_io` |
| 10 | `/robot/end_effector` (gripper state) |
| 5 | `/robot/sonar` |
| 9 | `/cameras/*` (image + camera_info, both hands) |
| 4 each | `/robot/navigators`, `/robot/head`, `/robot/assembly` |

Types worth knowing up front: `/robot/limb/*/gravity_compensation_torques` is
`baxter_core_msgs/SEAJointState` (the largest non-camera payload),
`/robot/sonar/head_sonar/state` is `sensor_msgs/PointCloud`,
`/robot/accelerometer/*/state` is `sensor_msgs/Imu`,
`/robot/range/*_hand_range/state` is `sensor_msgs/Range`, and the force-field
signals behind the enable deadlock are
`/robot/limb/*/collision_{avoidance,detection}_state` plus
`/collision/*/collision_detection` (`MotorControlMsgs/CollisionDetection`).

_(to fill on a session: which of these actually publish at rate vs. sit latched)_

## _(to fill)_ Parameters

Highlights from `params_*.yaml` — the robot's own rosparam tree.

## Observed rates and behaviour (measured 2026-07-24)

- `/robot/state` **101 Hz**, `/robot/joint_states` **100 Hz**.
- `/robot/joint_states` has **two publishers**, `/realtime_loop` and
  `/end_effector_publisher`, and consecutive messages **alternate** between a
  17-joint set (`head_nod`, `head_pan`, + arms) and a 15-joint set (arms +
  gripper). Both carry all 14 arm joints, so name lookups resolve either way —
  but anything differencing consecutive samples for velocity is differencing
  across two independent sources. A native stack should filter to one publisher
  or key on the joints it needs.
- Tracking on a real arm is **much better than the Rethink defaults assume**:
  worst error 0.0043–0.0077 rad across four `s1` moves of 0.35 rad over 3 s at
  `speed_ratio` 0.1, i.e. a 26× margin under a 0.2 rad path tolerance.
- After a cancel mid-trajectory the arm settles into the hold setpoint over
  roughly 0.02 rad, then holds to within 0.0015 rad peak-to-peak. Budget a
  settle window before judging a hold; do not compare two adjacent samples.

## Enable and untuck, confirmed on hardware (2026-07-24)

`tuck_arms.py -u` succeeded on the first attempt in ~23 s, from tucked
(`left_s1 = -2.174`) to untucked (`left_s1 = -1.042`). This confirms the
diagnosis that the difference from `enable_robot.py -e` is collision suppression
plus a 20 Hz enable republish, not robot health.

The documented warning that a successful untuck can end `enabled: False` did
**not** occur — the robot ended `ready=True enabled=True` on both the bridged and
the direct path. Treat that as a possible outcome, not the normal one, and always
verify by arm position rather than by the flag.

## _(to fill)_ Diagnostics catalog

Which statuses appear, at what level, in normal operation vs. faults.

## _(to fill)_ Tolerances that worked on the real arm

The values that held on hardware, replacing the desk-tuned
`path_tolerance_rad=0.2` / `stopped_velocity_tolerance=0.25` defaults.

## _(to fill)_ Grippers, sonar, IR, cameras

Observed only this session — state topics, message types, resting values.

## _(to fill)_ Quirks log

Anything surprising. Date each entry.
