# Running the hardware path without the Noetic container

## Why

The `baxter-noetic` image is ~5 GB and is easy to lose — a routine
`docker system prune` on 2026-07-24 removed it from both local engines, and a
rebuild from `~/baxter_noetic_ws/src/baxter_noetic` takes 20–40 minutes
(`catkin build --jobs 1`). Every capability we still take from that image is a
capability the future **native ROS 1 Noetic stack** has to implement anyway, so
replacing them is not throwaway work — see `noetic_native_notes.md`.

This document records what is actually container-bound, what is trivially
replaceable, and the one thing that genuinely is not.

## Already container-free

`scripts/py_bridge.py` is a pure-Python ROS 1 client: XML-RPC to the master,
raw TCPROS to peers, no rospy and no ROS 1 install. `scripts/sonar_ctl.py` and
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
| `roscore` + `rostopic` (`test_bridge_loopback.sh`) | desk-only protocol test | Not worth replacing; it is a desk test, irrelevant during a session |

## The key enabler: md5sums are wildcarded on the subscribe side

`ROS1Subscriber` negotiates TCPROS with `"md5sum": "*"`, so **receiving** a new
message type needs no md5 table and no message definition — only correct payload
bytes. This is what makes the replacements below small.

Publishing is no longer symmetric. Since 2026-07-25 `ROS1Publisher` answers the
handshake with the real md5sum and message definition from `ROS1_MSG_META`,
because `rosbag` stores whatever the publisher advertised and a wildcard made our
own recordings undecodable. Unlisted types still fall back to the wildcard and
still work on the wire — but **a new published type needs an `ROS1_MSG_META`
entry if its recordings must decode**. Both values come straight from
`rosmsg md5` and `rosmsg show -r` in the Noetic image.

## 1. Enable control — `scripts/enable_ctl.py`

Mirror `sonar_ctl.py`, which is the working template for a standalone ROS 1
publisher over `py_bridge` primitives.

Topics and wire formats:

| Topic | Type | Payload |
|---|---|---|
| `robot/set_super_enable` | `std_msgs/Bool` | 1 byte, `struct.pack("<B", 1)` |
| `robot/limb/<side>/suppress_collision_avoidance` | `std_msgs/Empty` | zero bytes, `b""` |
| `/robot/state` | `baxter_core_msgs/AssemblyState` | read back with the existing `deser_assembly_state` |

Behaviour that matters — this is exactly where the SDK's `enable_robot.py`
fails and `tuck_arms.py` succeeds:

- publish `suppress_collision_avoidance` for **both** limbs at 20 Hz, starting
  *before* the enable and continuing during it;
- republish `set_super_enable` at 20 Hz until `/robot/state` flips, rather than
  `enable_robot.py`'s single 2.0 s `wait_for`;
- cap the attempt (15 s) and report the final `AssemblyState` either way.

Suggested CLI, matching `sonar_ctl.py`: `status`, `enable`, `disable`, `reset`.

This alone would have unblocked the 2026-07-22 session, and it is a required
component of the native ROS 1 stack.

## 2. `/robot/ref_joint_states` over the bridge

`/robot/ref_joint_states` is `sensor_msgs/JointState` — the **same type**
`py_bridge.py` already deserialises for `/robot/joint_states` via
`deser_joint_state`. Bridging it is roughly a dozen lines: one more ROS 2
publisher and one more `ROS1Subscriber` entry alongside the existing two
(`py_bridge.py:655-684`).

Payoff out of proportion to the cost: it is the robot's **own commanded
reference**, i.e. better tracking-error ground truth than anything reconstructed
from our command side, and once bridged it is captured by `record_ros2.sh`,
which removes the main reason to run ROS 1-side recording at all. Measured at
**140 Hz** on hardware (2026-07-24).

> **Fix `ROS1Subscriber` first.** It negotiates TCPROS with only the *first*
> publisher the master lists, so on a topic with several publishers it silently
> receives a subset — `/robot/joint_states` arrives at 100 Hz instead of its real
> 138 Hz, and gripper joint states never cross at all. Anything added here
> inherits that bug. See `logs/I18_hardware_day.log.md` F13.

## 3. ROS 1-side recording (optional)

What `record_ros1.sh` still adds beyond a bridged `ref_joint_states`:
`/robot/limb/*/gravity_compensation_torques` (`SEAJointState`),
`/robot/limb/*/collision_{avoidance,detection}_state`, and `/diagnostics`
(`DiagnosticArray`). Each needs a hand-written deserialiser — `DiagnosticArray`
in particular is nested and variable-length, so it is real work for a signal we
only want around an enable failure.

Recommendation: leave `record_ros1.sh` as the container-based tool it is, and
only write deserialisers if the collision payload turns out to be needed
repeatedly. Do not port `/diagnostics` speculatively.

## 4. The exception: untucking

**Do not replace `tuck_arms.py` casually.** Tucked arms sit at `s1 = -2.175`,
outside our own URDF limit table `[-2.147, 1.047]`. Our shim rejects that pose by
design — the proven guard rail that makes `sim_tiny_trajectory` refuse while
tucked (`hardware_test_commands.md` §7). So a container-free untuck means
hand-publishing `joint_command` **outside our safety envelope**, with collision
avoidance suppressed, for a large whole-arm motion.

Options, worst risk first:

1. **Keep the container for `tuck_arms.py` only.** Recommended. Everything else
   above removes the dependency from the rest of the session.
2. **Relax the shim's limits behind an explicit opt-in parameter** so the tucked
   pose is commandable, then drive the untuck through our own validated path.
   This is the honest long-term answer, but it weakens a guard rail that has
   already proven useful and must not be the default.
3. **Hand-publish `joint_command` from a script**, as `tuck_arms.py` does
   internally. Smallest code, largest risk, no validation. Only with the e-stop
   in hand and a documented reason.

Option 2 is the one to design properly if the container dependency ever has to
go completely.

## Suggested order

1. `enable_ctl.py` — removes the container from the phase that actually blocked
   the last session, and is required for the native stack regardless.
2. `ref_joint_states` bridging — cheap, and improves the tracking analysis.
3. Revisit untucking (option 2) only once there is real motion experience.
