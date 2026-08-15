---
step: S04
title: "Bridge Architecture for Real Robot"
agent_date: 2026-06-17
status: completed
previous_steps: [S01, S02, S03]
---

# S04: Bridge Architecture for Real Robot

## Task

Designed the real-robot bridge architecture for a ROS 2 Jazzy/Noble student environment talking to Baxter's ROS 1 robot-side software. This step is design-only; no ROS 2 code or launch files were implemented.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `MASTER_PLAN.md`

Additional read-only source checks:

- `CentraleNantesRobotics/baxter_common_ros2` README and `baxter_bridge` package docs/source map.
- `RethoughtRobotics/baxter-zenoh` README, `ARCHITECTURE.md`, and `bridge_topics.yaml`.
- `RethoughtRobotics/BaxterSDK` README and package tree for ROS 2-side action server references.

## Findings

### Executive Summary

Default real-robot architecture should be a **single lab bridge host running ECN `baxter_bridge`**, not per-student bridges. The host owns the robot-side ROS 1 connection, exposes a restricted ROS 2 hardware API to students, and uses ECN publisher arbitration so one user owns a command topic or limb at a time.

`FollowJointTrajectory` should **not** be bridged as raw ROS 1 actionlib traffic by default. The practical architecture is a ROS 2-side action shim, modeled after the Noetic `baxter_interface` action server and the new `RethoughtRobotics/BaxterSDK` pattern, that accepts ROS 2 `control_msgs/action/FollowJointTrajectory` goals and publishes bridged Baxter `JointCommand` topics.

`JointCommand` remains exposed in ROS 2 hardware mode for Baxter-native labs and a thin `baxter_interface.Limb`-style facade, but beginner examples and MoveIt 2 should use standard ROS 2 actions/classes where possible.

### Candidate Comparison

| Candidate | What Runs Where | ROS 1 Assumption | Strengths | Limits | Decision |
|---|---|---|---|---|---|
| ECN `CentraleNantesRobotics/baxter_common_ros2` / `baxter_bridge` | Baxter keeps ROS 1 master/controllers. One lab bridge host runs ROS 2 Jazzy workspace with `baxter_bridge`, ROS 1 compile/runtime deps, and optional ROS 2 action shims. Student laptops run ROS 2 only and connect to bridge host. | Robot remains Baxter ROS 1. Bridge host needs ROS 1 client libraries/debs, preferably from ECN `baxter_legacy` or a pinned bridge image. | Mature BSD-3-Clause common stack. Precompiled Baxter message conversions. Bridges IK services. Embeds ROS 2 `robot_state_publisher`. Dynamic topic forwarding. ECN arbitration displays publishers on Baxter's screen and uses `/bridge_auth` / `/bridge_force`. `SAFE_CMD` default limits `JointCommand` to position/velocity. | Generated topic maps include Baxter topics/services but not direct actionlib action bridging. Needs ROS 1 deps on the bridge host. Must be validated on target robot firmware. | **Default hardware bridge.** Use one lab bridge host and minimum allowlist. |
| ECN `CentraleNantesRobotics/baxter_legacy` | Robot-side or bridge-host ROS 1 packages/debs. Not installed in student ROS 2 workspaces except as build/runtime support for bridge host. | Provides Python 3 ROS 1 packages/debian workflow for Focal/Jammy/Noble-like paths. Exact target robot distro still lab-specific. | Best known robot-side packaging reference. Supplies ROS 1 deps expected by ECN bridge. Can preserve original ROS 1 action servers if a lab wants them on the ROS 1 side. | Missing top-level license signal from S02. It is not a ROS 2 student API. | **Use as robot-side packaging reference/support**, not as the ROS 2 SDK surface. |
| RethoughtRobotics `baxter-zenoh` | Docker container on bridge host or laptop runs custom `ros1_bridge` parameter bridge, ROS-O Noetic on Noble, and local `rmw_zenohd`. Student shell sources ROS 2 Baxter messages and uses `rmw_zenoh_cpp`. | README/architecture says Baxter ROS 1 side is reached with no robot changes; container uses ROS-O Noetic on Ubuntu 24.04 Noble. | Directly targets Ubuntu 24.04 and Jazzy/Kilted/Lyrical. `bridge_topics.yaml` is explicit and broad. Zenoh router mode is intended for high-rate joint states and camera images. Simple setup story for a single laptop. MIT license. | Very new and low adoption. Current allowlist is too broad for a teaching lab, including maintenance, homing, old arm_navigation services, many IO topics, and `set_super_stop`. No ECN-style multi-user arbitration. Bridge docs say services are ROS 2 clients to ROS 1 servers; actions are not first-class. Requires Docker host networking/permissions, NetworkManager profile, and Zenoh acceptance by IT. | **Fallback/experimental bridge.** Consider if ECN bridge fails on Noble/Jazzy or camera/high-rate transport is poor. Restrict its YAML before student use. |
| RethoughtRobotics `BaxterSDK` / custom `ros1_bridge` fork | `BaxterSDK` is a ROS 2 SDK layer above `baxter-zenoh`. Its `baxter_interface` package includes ROS 2 `joint_trajectory_action_server`, `gripper_action_server`, and `head_action_server` console entries. | Depends on `baxter-zenoh` for ROS 1 connectivity. | Confirms a modern ROS 2-side action-shim approach is viable. Has MoveIt 2-oriented workflows and familiar Baxter SDK package names. | Low adoption, young repo, bridge dependency is Zenoh-specific, and S02 marked it reference-only. | **Reference only for API/action choices.** Do not adopt as the default base until target-hardware smoke tests pass. |
| Plain upstream `ros1_bridge` | Only on a separate supported/containerized bridge environment, not natively on Noble/Jazzy. | S01 confirmed upstream Noble/Jazzy is unsupported because ROS 1 is unavailable on Ubuntu 24.04. | Familiar generic bridge for known message/service types. | Not supported on Jazzy/Noble. Custom Baxter messages require build-time mappings. ROS 1 actionlib to ROS 2 action bridging is not first-class. Adds a fragile extra distro matrix. | **Last-resort diagnostic path only.** Do not make it the project architecture. |

### Default Topology

| Location | Runs | Notes |
|---|---|---|
| Baxter robot | Existing ROS 1 robot master, low-level controllers, `robot/state`, `JointCommand` consumers, gripper/camera/IK services. | No ROS 2 install and no embedded OS upgrade in this plan. Exact internal distro remains a hardware verification item; architecture assumes only a ROS 1 graph is reachable. |
| Lab bridge host | Ubuntu 24.04 Noble + ROS 2 Jazzy workspace; ECN `baxter_common_ros2` pinned from S02; ECN `baxter_bridge`; ROS 1 support deps from `baxter_legacy` debs/container; ROS 2 hardware action shims; bridge smoke-test tools. | Wired to Baxter. Owns `ROS_MASTER_URI`, `ROS_IP`, and robot network profile. Default `allow_multiple:=False`. Instructor can run `/bridge_force` to reserve left/right limbs. |
| Student laptop | ROS 2 Jazzy workspace/devcontainer with Baxter ROS 2 message packages, examples, MoveIt 2 clients, and docs. | Students do not need ROS 1. For labs, they either SSH/devcontainer into the bridge host or join the bridge host's ROS 2 network on an isolated lab VLAN/domain. |
| Docker container | Not required for the ECN default unless S07 chooses to package the bridge host. Required for `baxter-zenoh` fallback. | Per-student bridge containers are discouraged for motion because command ownership and safety become harder. |

Default connection pattern:

```text
Baxter ROS 1 robot <-> wired robot LAN <-> lab bridge host ECN baxter_bridge <-> ROS 2 lab domain <-> student ROS 2 clients
```

Fallback connection pattern for Rethought:

```text
Baxter ROS 1 robot <-> Docker baxter-zenoh parameter_bridge + local zenoh router <-> rmw_zenoh_cpp ROS 2 clients
```

### Minimum Hardware Allowlist

This is the default **minimum hardware mode**. Do not forward every Baxter topic by default.

ROS 1 to ROS 2 topics:

| Name | Type | Required For |
|---|---|---|
| `/robot/state` | `baxter_core_msgs/msg/AssemblyState` | enable/error/estop state, all motion gating |
| `/robot/joint_states` | `sensor_msgs/msg/JointState` | state display, action shim feedback, MoveIt 2 robot state |
| `/robot/limb/{left,right}/endpoint_state` | `baxter_core_msgs/msg/EndpointState` | SDK facade, IK/pose examples |
| `/robot/limb/{left,right}/collision_avoidance_state` | `baxter_core_msgs/msg/CollisionAvoidanceState` | tuck/untuck and safety diagnostics |
| `/robot/end_effector/{left,right}_gripper/state` | `baxter_core_msgs/msg/EndEffectorState` | gripper tools/actions |
| `/robot/end_effector/{left,right}_gripper/properties` | `baxter_core_msgs/msg/EndEffectorProperties` | gripper capability detection |
| `/cameras/head_camera/image` | `sensor_msgs/msg/Image` | one default camera stream, optional per lab |
| `/cameras/head_camera/camera_info` or `/cameras/head_camera/camera_info_std` | `sensor_msgs/msg/CameraInfo` | camera calibration if available |
| `/tf` | `tf2_msgs/msg/TFMessage` | visualization and robot model if robot publishes TF |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | static transforms, if available |
| `/diagnostics` | `diagnostic_msgs/msg/DiagnosticArray` | optional instructor diagnostics |

ROS 2 to ROS 1 topics:

| Name | Type | Required For |
|---|---|---|
| `/robot/set_super_enable` | `std_msgs/msg/Bool` | enable/disable wrapper only |
| `/robot/set_super_reset` | `std_msgs/msg/Empty` | reset wrapper only |
| `/robot/set_super_stop` | `std_msgs/msg/Empty` | safety/admin tool only, not beginner examples |
| `/robot/limb/{left,right}/joint_command` | `baxter_core_msgs/msg/JointCommand` | Baxter-native limb control and action shim output |
| `/robot/limb/{left,right}/set_speed_ratio` | `std_msgs/msg/Float64` | low-speed lab operation |
| `/robot/limb/{left,right}/joint_command_timeout` | `std_msgs/msg/Float64` | command timeout safety |
| `/robot/limb/{left,right}/suppress_collision_avoidance` | `std_msgs/msg/Empty` | tuck/untuck only; do not expose casually |
| `/robot/end_effector/{left,right}_gripper/command` | `baxter_core_msgs/msg/EndEffectorCommand` | gripper open/close/calibrate/reset |
| `/robot/head/command_head_pan` | `baxter_core_msgs/msg/HeadPanCommand` | optional head demos |
| `/robot/head/command_head_nod` | `std_msgs/msg/Bool` | optional head demos |
| `/robot/xdisplay` | `sensor_msgs/msg/Image` | optional display demos |

ROS 2 clients to ROS 1 services:

| Name | Type | Required For |
|---|---|---|
| `/ExternalTools/{left,right}/PositionKinematicsNode/IKService` | `baxter_core_msgs/srv/SolvePositionIK` | hardware IK compatibility |
| `/cameras/list` | `baxter_core_msgs/srv/ListCameras` | camera discovery |
| `/cameras/open` | `baxter_core_msgs/srv/OpenCamera` | selective camera enable |
| `/cameras/close` | `baxter_core_msgs/srv/CloseCamera` | camera shutdown |
| `/cameras/reset` | `std_srvs/srv/Empty` | optional camera recovery |

ROS 2 local actions above the bridge:

| Name | Type | Implementation |
|---|---|---|
| `/robot/limb/{left,right}/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | ROS 2 action shim publishes `/robot/limb/{side}/joint_command` and monitors `/robot/joint_states` + `/robot/state`. |
| `/robot/end_effector/{left,right}_gripper/gripper_action` | `control_msgs/action/GripperCommand` | Optional ROS 2 action shim over `EndEffectorCommand` and gripper state/properties. |
| `/robot/head/head_action` | `control_msgs/action/SingleJointPosition` if available in the target `control_msgs` version | Optional only; topic commands are enough for minimum hardware mode. |

Explicitly **exclude by default**:

- Maintenance/update/tare/calibration topics under `/robustcontroller/*`, `/update/*`, `/usb/*` unless an instructor enables an admin profile.
- Homing, motor voltage, stiffness, contact-safety suppression, gravity-compensation suppression, and old `arm_navigation_msgs` services from broad bridge configs.
- All camera streams at once; bridge only the selected camera(s).
- Raw torque and raw-position labs unless the instructor rebuilds ECN bridge without `SAFE_CMD` and accepts the risk.

### `FollowJointTrajectory` Boundary Design

Direct ROS 1 action bridging is not the default. The bridge should forward topics/services only, then provide ROS 2 action servers on the bridge host or hardware workspace.

The ROS 2 action shim should:

- Accept `control_msgs/action/FollowJointTrajectory` goals for left and right arms.
- Validate joint names against Baxter's 7 joints per limb.
- Refuse goals unless `/robot/state` reports the robot is ready, enabled, not stopped, not in error, and not e-stopped.
- Use position mode by default and publish `baxter_core_msgs/msg/JointCommand` to `/robot/limb/{side}/joint_command` at a bounded rate.
- Publish `/robot/limb/{side}/joint_command_timeout` and low `/robot/limb/{side}/set_speed_ratio` during lab operation.
- On cancel or failure, send a final hold-position command rather than `set_super_stop`.
- Report ROS 2 action feedback from `/robot/joint_states`.
- Leave `position_w_id` / `/robot/limb/{side}/inverse_dynamics_command` as an advanced option, not minimum hardware mode.

This keeps MoveIt 2 and standard ROS 2 examples on familiar action APIs while preserving Baxter's real `JointCommand` control path underneath. `RethoughtRobotics/BaxterSDK` is useful as reference because it already has ROS 2 console entry points for `joint_trajectory_action_server`, `gripper_action_server`, and `head_action_server`, but S02's low-adoption warning still applies.

### `JointCommand` Exposure

`JointCommand` stays exposed in ROS 2 hardware mode because S03 identified it as the core Baxter hardware control API and because some student labs may teach Baxter-native control directly.

Default student path:

- MoveIt 2 and planned motion use `FollowJointTrajectory`.
- Basic SDK examples use a thin `Limb` class or curated helper that publishes position/velocity `JointCommand` safely.
- Beginner docs avoid torque/raw-position modes.

Instructor/advanced path:

- Direct `/robot/limb/{side}/joint_command` publishing is allowed on the lab bridge host or an authorized ROS 2 client.
- ECN bridge should keep `SAFE_CMD=True` unless a lab explicitly requires torque/raw-position behavior.
- Command ownership is controlled by ECN arbitration and lab procedure, not by hiding the topic completely.

### Cameras

Cameras are optional-by-bandwidth, not always-on.

Default camera mode:

- Bridge `/cameras/list`, `/cameras/open`, and `/cameras/close`.
- Open only one stream by default, preferably `/cameras/head_camera/image` with matching camera info.
- Use low resolution/FPS via `OpenCamera` settings where the robot supports it.
- Use `sensor_msgs/Image` raw only for the selected stream unless the robot already publishes compressed images.

If a course needs multiple cameras or sustained vision workloads:

- Prefer running vision nodes on the bridge host to avoid Wi-Fi/lab multicast issues.
- Consider an `image_transport` republisher or compressed transport on the bridge host.
- Consider the Rethought Zenoh fallback only after ECN bridge camera throughput is measured.

### Multi-Student Safety

Use ECN publisher arbitration by default.

Operational policy:

- One shared bridge host per physical Baxter.
- `allow_multiple:=False` for motion labs.
- `/bridge_auth` records which user publishes each command topic.
- `/bridge_force` lets an instructor reserve `left`, `right`, or both limbs for one user and clear reservations after the lab.
- Baxter screen publisher display remains enabled so students can see who owns command topics.
- Per-student bridge containers are only acceptable for read-only observation or simulation, not for simultaneous real motion.

### Enable, Reset, Stop, And E-Stop Protection

Treat enable/reset/stop as safety-critical.

Design rules:

- Students should not be taught raw one-line publishing to `/robot/set_super_enable` as the normal workflow.
- Provide a wrapped ROS 2 tool that reads `/robot/state`, prints `ready`, `enabled`, `stopped`, `error`, `estop_button`, and `estop_source`, then enables only when safe.
- Do not auto-reset faults in a loop. `/robot/set_super_reset` should be an explicit instructor/student action after checking state and physical scene.
- `/robot/set_super_stop` should be present for an explicit software stop tool but omitted from beginner motion examples. Physical e-stop remains the primary emergency stop.
- Action shims should hold/cancel motion using `JointCommand`, not call `/robot/set_super_stop` for routine cancellation.
- No motion command is allowed until the bridge smoke tests pass.

### QoS Policy

These are design defaults for S07/S08 to encode in launch/config. Validate on hardware because ROS 2 QoS incompatibility can silently prevent delivery.

| API Class | QoS Default | Notes |
|---|---|---|
| `/robot/state`, gripper state/properties, endpoint state | Reliable, volatile, keep last 10 | State must not be missed during enable/motion checks. |
| `/robot/joint_states` | Reliable, volatile, keep last 10 for MoveIt/robot state; allow best-effort override for high-rate monitoring | Start reliable for correctness on wired lab LAN. If latency/drop issues appear, provide a measured best-effort profile. |
| Command topics: `JointCommand`, enable/reset/stop, gripper command, head command | Reliable, volatile, keep last 1 | Do not use transient-local for safety or motion commands; stale commands must not replay to a restarted bridge. |
| Speed ratio and command timeout | Reliable, volatile, keep last 1 | Send on tool/action-shim startup rather than relying on latched replay. |
| ROS 2 local actions | ROS 2 action defaults unless S06 requires overrides | Actions terminate at the ROS 2 shim and do not cross the ROS 1 bridge as actionlib. |
| Services: IK and cameras | Reliable services QoS | Calls are low-rate and should fail loudly if unavailable. |
| `/tf` | tf2 defaults, volatile | Do not over-customize unless robot TF proves unreliable. |
| `/tf_static` | Reliable, transient local, keep last 100 | Required for late RViz/MoveIt subscribers. |
| Cameras | Best effort, volatile, keep last 1 or 2 | Prefer fresh frames over backlog. Use reliable only for debugging low-rate snapshots. |
| Diagnostics | Reliable, volatile, keep last 10 | Optional instructor profile. |

### Discovery And Networking

Default network assumptions:

- Baxter is wired to the lab bridge host on the robot LAN.
- Bridge host has fixed robot-facing IP and explicit `ROS_MASTER_URI` / `ROS_IP`; do not rely on `.local` or DNS in the robot control path.
- Student ROS 2 traffic stays on an isolated lab VLAN or runs inside devcontainers on the bridge host via SSH.
- Use one `ROS_DOMAIN_ID` per physical robot/lab bench.
- Prefer wired Ethernet for motion labs. Wi-Fi is acceptable for read-only RViz/camera only after testing.

University IT constraints:

- DDS multicast may be blocked. If students must run nodes on their own laptops, S07 should document either allowed firewall/multicast rules, a DDS discovery server/static peer setup, or the simpler SSH-into-bridge-host workflow.
- Firewalls must allow the selected DDS traffic between student subnet and bridge host, or no cross-machine ROS 2 should be promised.
- Docker host networking and access to `/var/run/docker.sock` are often restricted. This is another reason not to make per-student `baxter-zenoh` containers the default.
- For `baxter-zenoh`, document `rmw_zenoh_cpp`, local `rmw_zenohd` router, TCP port `7447`, NetworkManager robot profile, unset/controlled `ROS_DOMAIN_ID`, and Docker permissions.

### Required Bridge Smoke Tests Before Motion

Run these before enabling robot motion in every hardware session:

1. Physical check: robot workspace clear, physical e-stop reachable, grippers/cameras installed as expected.
2. Network check: bridge host can ping the robot IP and reach ROS 1 master on port `11311`.
3. Bridge process check: ECN bridge running; `/bridge_exists` reports key topics or `/bridge_open` can open them. For Zenoh fallback, `bridge_topics.yaml` is loaded and ROS 2 topics are visible.
4. State check: `ros2 topic echo --once /robot/state` returns sane state; e-stop is not engaged; no unresolved `error`/`stopped` condition.
5. Joint state check: `ros2 topic hz /robot/joint_states` is stable and joint names include all 14 Baxter arm joints.
6. IK check: both `ExternalTools/{left,right}/PositionKinematicsNode/IKService` service names are visible; call a known safe pose or at least verify service availability.
7. Gripper check: state and properties arrive for installed grippers; command only after enable policy permits it.
8. Camera check: `/cameras/list` works; open one low-bandwidth camera; verify one image and camera info; close it if not needed.
9. Action shim check: ROS 2 `FollowJointTrajectory` action servers are available, but no trajectory is sent until robot state is safe.
10. Motion check: after explicit enable, run a tiny low-speed one-arm trajectory in a clear workspace, verify feedback, cancel/hold behavior, then disable if the lab does not need continued motion.

## Decisions

1. **Default bridge:** Use ECN `CentraleNantesRobotics/baxter_common_ros2` / `baxter_bridge` on one lab bridge host per Baxter.
2. **Robot-side packaging:** Use ECN `baxter_legacy` as the ROS 1 packaging/dependency reference for the bridge host or robot-side support, not as student-facing ROS 2 code.
3. **Fallback bridge:** Keep `RethoughtRobotics/baxter-zenoh` as an experimental fallback for Noble/Jazzy Docker workflows or high-rate camera/joint-state problems, but restrict its broad `bridge_topics.yaml` before student labs.
4. **Do not depend on upstream `ros1_bridge` natively on Jazzy/Noble.** It is unsupported there and does not solve action bridging cleanly.
5. **Action strategy:** Provide ROS 2-side `FollowJointTrajectory` and optional gripper/head action shims above bridged topics. Do not bridge ROS 1 actionlib channels by default.
6. **Hardware API personality:** Preserve Baxter-native `JointCommand` in ROS 2 hardware mode, but make standard ROS 2 actions/classes the default teaching path.
7. **Safety:** Keep ECN arbitration enabled with `allow_multiple:=False`; protect enable/reset/stop behind wrapped tools and mandatory smoke tests.
8. **Cameras:** Bridge camera services always, but image streams only on demand and preferably one camera at a time.
9. **QoS:** Use reliable volatile QoS for state/commands/services, transient-local only for `/tf_static`, and best-effort shallow queues for camera streams.
10. **Networking:** Prefer students running on the bridge host or a controlled lab ROS 2 domain. Do not promise arbitrary campus-network DDS discovery.

## Open Questions

- What ROS 1 distro/image does the target Baxter actually expose on the robot or lab-side ROS 1 graph: original Kinetic, Noetic wrapper, ECN legacy debs, or a lab-specific image?
- Can ECN `baxter_bridge` and its ROS 1 dependencies be installed cleanly on the chosen Noble/Jazzy bridge host, or should S07 package it in a bridge container?
- Will university IT allow ROS 2 DDS multicast/firewall rules between student laptops and the bridge host, or should official labs require SSH/devcontainer on the bridge host?
- Is Zenoh acceptable under university IT policy if the fallback bridge is needed?
- Which physical grippers are installed on the target Baxter, and do both sides expose the same `EndEffector*` state/properties as the Noetic reference?
- Which camera(s) are required for courses, and what frame rate/resolution is acceptable on the lab network?
- Should S06 expose hardware action names as `/robot/limb/{side}/follow_joint_trajectory`, MoveIt-style `{side}_arm/follow_joint_trajectory`, or both through remaps?
- Does the course require direct `JointCommand` homework, or can direct publishing remain an advanced/instructor profile?
- Are maintenance/tare/calibration/update workflows allowed from ROS 2 at all, or should they remain ROS 1 admin-only?

## Artifacts

- Updated this S04 bridge architecture log: `logs/S04_bridge_architecture.log.md`
- Updated S04 status in `MASTER_PLAN.md`
- Appended S05 handoff prompt to `PROMPTS.md`
- Read-only local context used:
  - `baxter_noetic_ref/baxter_interface/src/joint_trajectory_action/joint_trajectory_action.py`
  - `baxter_noetic_ref/baxter_interface/src/gripper_action/gripper_action.py`
  - `baxter_noetic_ref/baxter_interface/src/head_action/head_action.py`
  - `baxter_noetic_ref/baxter_interface/src/baxter_interface/robot_enable.py`
  - `baxter_noetic_ref/baxter_interface/src/baxter_interface/limb.py`
  - `baxter_noetic_ref/baxter_tools/scripts/smoke_test.py`
- Primary upstream references inspected:
  - https://github.com/CentraleNantesRobotics/baxter_common_ros2
  - https://github.com/CentraleNantesRobotics/baxter_common_ros2/tree/master/baxter_bridge
  - https://github.com/CentraleNantesRobotics/baxter_legacy
  - https://github.com/RethoughtRobotics/baxter-zenoh
  - https://raw.githubusercontent.com/RethoughtRobotics/baxter-zenoh/main/ARCHITECTURE.md
  - https://raw.githubusercontent.com/RethoughtRobotics/baxter-zenoh/main/bridge_topics.yaml
  - https://github.com/RethoughtRobotics/BaxterSDK
  - https://github.com/ros2/ros1_bridge
