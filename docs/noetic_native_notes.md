# Notes for a Native ROS 1 Noetic Baxter Stack

Working notes for a future control stack that runs **directly on ROS 1 Noetic
against Baxter's own master** — no ROS 2, no bridge. Everything here is
robot-side behavior: what the hardware actually does, as opposed to what the
SDK documents.

Seeded from the ROS 2 port's hardware sessions. Sections marked _(to fill)_ get
filled during a robot day — see [hardware_day_plan.md](hardware_day_plan.md)
phase P8.

[hardware_runbook.md](hardware_runbook.md) notes what still needs the Noetic
image versus what `py_bridge.py` already covers; those pure-Python ROS 1
primitives are the head start for this native stack. The plan for removing that
last dependency is the final section of this document.

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
- **`robot/limb/<side>/set_speed_ratio`** (`std_msgs/Float64`): per-limb.
  **Measured 2026-07-24: raising it 0.1 → 0.2 → 0.3 changed tracking error not at
  all.** It caps the robot-side maximum joint speed, and a trajectory of 0.35 rad
  over 3 s (~0.117 rad/s) sits far below that cap at any of those settings. To move
  faster, shorten the trajectory duration — the speed ratio is a ceiling, not a
  throttle.
- **Gravity compensation holds position.** With no `joint_command` for ~20 s, well
  past the 0.2 s timeout, the arms drifted 0.001 rad. Losing the command stream is
  not immediately dangerous at a moderate pose, though still not a substitute for
  holding deliberately.
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

Measured directly on the ROS 1 side (`rostopic hz`, 2026-07-24):

| Topic | Rate |
|---|---|
| `/robot/joint_states` | 138.8 Hz (aggregate of two publishers) |
| `/robot/ref_joint_states` | 140.1 Hz |
| `/robot/state` | 99.9 Hz |
| `/robot/limb/*/gravity_compensation_torques` | 94.3 Hz |
| `/robot/limb/*/joint_command` | 0 Hz when no goal is active |

- `/robot/joint_states` has **two publishers**: `/realtime_loop` (~100 Hz, head +
  all 14 arm joints, a 17-joint message) and `/end_effector_publisher` (~38 Hz,
  gripper joints). A native stack subscribing normally through rospy gets both
  merged; anything hand-rolling TCPROS must connect to **every** publisher the
  master lists, or it silently receives only one. `py_bridge.py` did exactly that
  until 2026-07-24 — it saw 100 Hz of the 138 Hz stream and never received
  gripper joint states, which also left MoveIt's planning scene permanently
  incomplete (`Missing l_gripper_l_finger_joint`). Fixed by keeping one receive
  thread per publisher: 19 joints at 123.6 Hz, up from 17 at 99.7 Hz.
- 89 services are advertised, including
  `/ExternalTools/<side>/PositionKinematicsNode/IKService` and the
  `/cameras/{list,open,close,reset}` set.
- Tracking on a real arm is good, but mind which number you use: **settled**
  error at goal end is 0.0043–0.0077 rad, while **in-flight** lag (what a path
  tolerance actually governs) grows with speed. At ~0.12 rad/s lag was ~0.035 rad;
  I20 showed lag ≈ 0.4 s × velocity, so `path_tolerance_rad` 0.2 is a ~0.5 rad/s
  speed ceiling — see `docs/hardware_runbook.md` and `logs/I20_fast_motion_and_srdf.log.md`.
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

## Tolerances that worked on the real arm (I12 2026-07-24; I20 2026-07-25)

Two different quantities that are easy to confuse, and the confusion matters:

| Quantity | Value | What it is |
|---|---|---|
| Settled error at goal end | 0.0043–0.0078 rad | how close the arm parks; what a client's `max_error` reports |
| **In-flight lag during motion** | ≈ 0.4 s × commanded velocity (I20) | how far the arm trails its reference *while moving* |

A path-tolerance-style limit governs the **second**. At ~0.12 rad/s (I12) lag was
~0.035 rad; at 0.50 rad/s (I20) it aborted at 0.202 rad against a 0.200 limit.

`path_tolerance_rad = 0.2` is therefore a ~0.5 rad/s speed ceiling, not slack to
trim. The 2.0 rad/s per-cycle clamp is unreachable under that default. See
`docs/hardware_runbook.md`. `stopped_velocity_tolerance = 0.25` never came close
to firing at I12 speeds — every goal settled within 0.01 s.

`s1` dominates the lag on both arms at low speed; I20 MoveIt aborts concentrated
on `left_w0` / `left_e0` when plans drove the wrists near the URDF velocity limit.

## _(to fill)_ Grippers, sonar, IR, cameras

Observed only this session — state topics, message types, resting values.

## _(to fill)_ Quirks log

Anything surprising. Date each entry.

---

# Removing the Noetic container dependency

Merged in for v0.2.0 from what used to be a separate container-free-path
document. Every capability still taken
from the `baxter-noetic` image is one this native stack has to implement anyway,
so replacing them is not throwaway work.

The image is ~5 GB and easy to lose — a routine `docker system prune` on
2026-07-24 removed it from both local engines, and a rebuild from
`~/baxter_noetic_ws/src/baxter_noetic` takes 20-40 minutes
(`catkin build --jobs 1`).

## Already container-free

`scripts/py_bridge.py` is a pure-Python ROS 1 client: XML-RPC to the master, raw
TCPROS to peers, no rospy and no ROS 1 install. `scripts/sonar_ctl.py` and
`scripts/i10_non_motion_check.py` are built on the same primitives, and the whole
ROS 2 side — action shims, `baxter_safety_check`, `sim_tiny_trajectory`, MoveIt,
`scripts/record_ros2.sh` — never touched Docker.

So bring-up, the I11 interlock tests, the supervised motion gate, tolerance work,
MoveIt and shutdown all already run without a container.

## What still needs it

| Capability | Used for | Replaceable? |
|---|---|---|
| `enable_robot.py` (`baxtool`) | enable / disable / reset | **Yes** — trivial, see below |
| `tuck_arms.py` (`baxtool`) | untuck out of the force field | **No** — the real exception |
| `rosbag record` (`record_ros1.sh`) | ROS 1-side topics the bridge does not carry | **Partly** — the important one is trivial |
| `roscore` + `rostopic` (`test_bridge_loopback.sh`) | desk-only protocol test | Not worth replacing; irrelevant during a session |

## The key enabler: md5sums are wildcarded on the subscribe side

`ROS1Subscriber` negotiates TCPROS with `"md5sum": "*"`, so **receiving** a new
message type needs no md5 table and no message definition — only correct payload
bytes. This is what makes the replacements below small.

Publishing is no longer symmetric. Since 2026-07-25 `ROS1Publisher` answers the
handshake with the real md5sum and message definition from `ROS1_MSG_META`,
because `rosbag` stores whatever the publisher advertised and a wildcard made our
own recordings undecodable. Unlisted types still fall back to the wildcard and
still work on the wire — but **a new published type needs an `ROS1_MSG_META`
entry if its recordings must decode**. Both values come straight from `rosmsg
md5` and `rosmsg show -r` in the Noetic image.

## 1. Enable control — `scripts/enable_ctl.py`

Mirror `sonar_ctl.py`, the working template for a standalone ROS 1 publisher over
`py_bridge` primitives.

| Topic | Type | Payload |
|---|---|---|
| `robot/set_super_enable` | `std_msgs/Bool` | 1 byte, `struct.pack("<B", 1)` |
| `robot/limb/<side>/suppress_collision_avoidance` | `std_msgs/Empty` | zero bytes, `b""` |
| `/robot/state` | `baxter_core_msgs/AssemblyState` | read back with the existing `deser_assembly_state` |

Behaviour that matters — exactly where the SDK's `enable_robot.py` fails and
`tuck_arms.py` succeeds:

- publish `suppress_collision_avoidance` for **both** limbs at 20 Hz, starting
  *before* the enable and continuing during it;
- republish `set_super_enable` at 20 Hz until `/robot/state` flips, rather than
  `enable_robot.py`'s single 2.0 s `wait_for`;
- cap the attempt (15 s) and report the final `AssemblyState` either way.

Suggested CLI, matching `sonar_ctl.py`: `status`, `enable`, `disable`, `reset`.
This alone would have unblocked the 2026-07-22 session.

## 2. `/robot/ref_joint_states` over the bridge

`/robot/ref_joint_states` is `sensor_msgs/JointState` — the **same type**
`py_bridge.py` already deserialises for `/robot/joint_states` via
`deser_joint_state`. Bridging it is roughly a dozen lines: one more ROS 2
publisher and one more `ROS1Subscriber` entry alongside the existing two
(`py_bridge.py:655-684`).

Payoff out of proportion to the cost: it is the robot's **own commanded
reference**, i.e. better tracking-error ground truth than anything reconstructed
from our command side, and once bridged it is captured by `record_ros2.sh`, which
removes the main reason to run ROS 1-side recording at all. Measured at **140 Hz**
on hardware (2026-07-24).

> **Fix `ROS1Subscriber` first.** It negotiates TCPROS with only the *first*
> publisher the master lists, so on a topic with several publishers it silently
> receives a subset — `/robot/joint_states` arrives at 100 Hz instead of its real
> 138 Hz, and gripper joint states never cross at all. Anything added here
> inherits that bug.

## 3. ROS 1-side recording (optional)

What `record_ros1.sh` still adds beyond a bridged `ref_joint_states`:
`/robot/limb/*/gravity_compensation_torques` (`SEAJointState`),
`/robot/limb/*/collision_{avoidance,detection}_state`, and `/diagnostics`
(`DiagnosticArray`). Each needs a hand-written deserialiser — `DiagnosticArray`
in particular is nested and variable-length, so it is real work for a signal we
only want around an enable failure.

Leave `record_ros1.sh` as the container-based tool it is, and only write
deserialisers if the collision payload turns out to be needed repeatedly. Do not
port `/diagnostics` speculatively.

## 4. The exception: untucking

**Do not replace `tuck_arms.py` casually.** Tucked arms sit at `s1 = -2.175`,
outside our own URDF limit table `[-2.147, 1.047]`. Our shim rejects that pose by
design — the proven guard rail that makes `sim_tiny_trajectory` refuse while
tucked ([hardware_test_commands.md](hardware_test_commands.md) §7). So a
container-free untuck means hand-publishing `joint_command` **outside our safety
envelope**, with collision avoidance suppressed, for a large whole-arm motion.

Options, worst risk first:

1. **Keep the container for `tuck_arms.py` only.** Recommended. Everything above
   removes the dependency from the rest of the session.
2. **Relax the shim's limits behind an explicit opt-in parameter** so the tucked
   pose is commandable, then drive the untuck through our own validated path. The
   honest long-term answer, but it weakens a guard rail that has already proven
   useful and must not be the default.
3. **Hand-publish `joint_command` from a script**, as `tuck_arms.py` does
   internally. Smallest code, largest risk, no validation. Only with the e-stop in
   hand and a documented reason.

## Suggested order

1. `enable_ctl.py` — removes the container from the phase that actually blocked
   the 2026-07-22 session, and is required for the native stack regardless.
2. `ref_joint_states` bridging — cheap, and improves the tracking analysis.
3. Revisit untucking (option 2) only once there is real motion experience.
