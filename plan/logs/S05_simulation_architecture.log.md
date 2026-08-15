---
step: S05
title: "Simulation Stack Architecture"
agent_date: 2026-06-17
status: completed
previous_steps: [S01, S02, S03, S04]
---

# S05: Simulation Stack Architecture

## Task

Designed the Baxter simulation architecture for ROS 2 Jazzy on Ubuntu 24.04 Noble using Gazebo Harmonic, `ros_gz`, `gz_ros2_control`, `ros2_control`, and MoveIt 2. This was a planning step only. No ROS 2 packages, launch files, URDF files, or simulator code were implemented.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `logs/S04_bridge_architecture.log.md`
- `MASTER_PLAN.md`

Additional read-only checks used:

- Local Classic simulator reference under `baxter_noetic_ref/baxter_simulator/`
- Local model reference under `baxter_noetic_ref/baxter_common/baxter_description/` and `baxter_noetic_ref/baxter_common/rethink_ee_description/`
- Local MoveIt 1 controller references under `baxter_noetic_ref/baxter_moveit_config/config/`
- `angysof16/BaxterMotionPlanning` README and current public tree/config snippets
- `CentraleNantesRobotics/baxter_gz` README
- `CentraleNantesRobotics/baxter_common_ros2` README and package tree

## Findings

### Executive Summary

Default simulation should be a **standard ROS 2 manipulator stack**, not a Baxter Classic simulator port: Gazebo Harmonic + `gz_ros2_control` + `joint_trajectory_controller` + MoveIt 2. This matches Jazzy/Harmonic upstream support, keeps S06 simple, and avoids reimplementing the old ROS 1 `baxter_sim_controllers` stack.

The simulation should expose a small Baxter compatibility surface only where it reduces student confusion: `/robot/joint_states`, `/robot/state`, optional `/robot/limb/{side}/endpoint_state`, simple gripper state/properties, and optionally one camera stream under Baxter-like names. Direct `/robot/limb/{side}/joint_command` in sim is **not default**. If a course requires Baxter-native command homework, add a small compatibility shim that accepts safe `JointCommand` position commands and forwards them into the active trajectory controllers. Do not revive the old custom position/velocity/effort controller plugins.

| Area | Default Decision | Reason |
|---|---|---|
| Simulator | Gazebo Harmonic via `ros_gz_sim` | Jazzy-recommended Gazebo pairing from S01. Classic is EOL. |
| Control | `gz_ros2_control/GazeboSimSystem` + standard `ros2_controllers` | Mature Jazzy path; MoveIt 2 integrates cleanly. |
| Arms | `joint_trajectory_controller/JointTrajectoryController` for left and right arms | Same action type S04 chose for hardware shims: `control_msgs/action/FollowJointTrajectory`. |
| Head | `JointTrajectoryController` for `head_pan` | Boring and compatible with action-style control. |
| Grippers | Simple `position_controllers/GripperActionController` for electric gripper joints if modeled | Enough for open/close demos; full gripper physics is out of scope. |
| Baxter API parity | Two profiles: standard default, optional compatibility shim | Parity should not drive a custom simulator rewrite. |
| MoveIt 2 | Connect to sim controllers through ros2_control; details deferred to S06 | S05 defines controller layout; S06 owns SRDF/controllers/planning config. |

### Community Simulation Candidate Comparison

| Source | Relevant Evidence | Use In Blueprint | Reason |
|---|---|---|---|
| `angysof16/BaxterMotionPlanning` | README claims ROS 2 Jazzy + Gazebo Harmonic + `ros-jazzy-gz-ros2-control` + MoveIt 2. Current config uses `joint_state_broadcaster`, `right_arm_controller`, `left_arm_controller`, `head_controller`, and gripper action controllers. Latest S02 metadata: commit `2a0ed74`, 2026-06-07, no detected license, latest commit mentions IK uncertainty. | **Reference only** | Best modern architecture reference, but no license blocks copying. Also its controller examples use renamed joints like `torso_right_upper_shoulder` rather than Baxter's legacy names like `right_s0`, so it should not define the canonical model API. |
| `CentraleNantesRobotics/baxter_gz` | README says it controls Baxter in Ignition/Gazebo using the same topics as the real robot with `baxter_core_msgs/JointCommand`; custom bridge handles joint commands and range sensors while `ros_gz_bridge` handles joint states/images. MIT. | **Reference only for optional compatibility profile** | Useful proof that JointCommand parity can be done narrowly. Too custom and too small to become default. |
| `CentraleNantesRobotics/baxter_common_ros2` | BSD-3-Clause; includes `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, and `baxter_bridge`. README says ROS 2 common packages are ported and joint command/image topics have been heavily tested in classical Baxter use. | **Adopt for messages and base descriptions** | Strongest licensed source for Baxter interfaces and geometry. Simulation overlays should build on this rather than manually porting message packages. |
| `bornaparo/baxter_moveit_config` | S02 found it stale/partial, low adoption, and unlicensed; targets older Ignition-style work. | **Skip direct dependency** | Superseded by `BaxterMotionPlanning` as a reference and by regenerated MoveIt 2 config in S06. |
| `dabaspark/baxter_sdk_nvidia_any_os` | Dockerized ROS 1 Kinetic + Gazebo Classic fallback on modern Ubuntu host. | **Emergency legacy reference only** | Not a Jazzy simulator. Useful only for risk mitigation/docs if Harmonic sim is blocked. |

No stronger active Jazzy/Harmonic Baxter simulator was found beyond the S02 candidate set. The practical route is to adopt licensed common packages, regenerate local sim overlays, and use `BaxterMotionPlanning` only as a checklist for launch/controller wiring.

### Local Classic Simulator Replacement Findings

The local Noetic simulator should be replaced, not ported.

| Local Source | Finding | S05 Consequence |
|---|---|---|
| `baxter_noetic_ref/baxter_simulator/baxter_gazebo/launch/baxter_world.launch` | Starts Gazebo Classic through `gazebo_ros/empty_world.launch`, spawns URDF through `gazebo_ros spawn_model`, loads `baxter_sdk_control.launch`, and sets initial joint poses. | Replace with `ros_gz_sim` launch and Gazebo Sim entity spawn. Do not carry `/gazebo/spawn_urdf_model` workflows. |
| `baxter_noetic_ref/baxter_common/baxter_description/urdf/baxter_base/baxter_base.gazebo.xacro` | Loads `libbaxter_gazebo_ros_control.so`, Classic `libgazebo_ros_camera.so`, Classic laser/video plugins, and ROS 1 `EffortJointInterface` transmissions. | Preserve geometry and sensors conceptually, but replace plugins/tags with Gazebo Harmonic/SDF and ROS 2 `<ros2_control>` blocks. |
| `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/config/baxter_sim_controllers.yaml` | Defines ROS 1 `joint_state_controller`, custom `BaxterHeadController`, custom position/velocity/effort controllers subscribed to `/robot/limb/{side}/joint_command`, and many individual effort controllers. | Replace with standard `ros2_controllers`. Do not recreate velocity/effort/custom controller stack in first release. |
| `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/config/baxter_{left,right}_electric_gripper_controller.yaml` | Uses custom `BaxterGripperController` subscribed to `EndEffectorCommand` and properties topics. | Replace with simple gripper action/position controller plus optional state/properties shim. |
| `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/launch/baxter_sdk_control.launch` | Starts `baxter_sim_kinematics`, loads Classic controller YAML, starts `baxter_emulator`, starts `robot_state_publisher`, and optionally starts Qt `baxter_sim_io`. | Split into standard robot state publisher, controller manager, Gazebo spawn, and optional lightweight Baxter state shim. Drop Qt IO by default. |
| `baxter_noetic_ref/baxter_moveit_config/config/baxter_controllers.yaml` | MoveIt 1 used `/robot/limb/{right,left}/follow_joint_trajectory` with joints `right_s0`...`right_w2` and `left_s0`...`left_w2`. | Preserve Baxter joint names and controller intent. S06 decides whether sim exposes `/left_arm_controller/...`, `/robot/limb/{side}/...`, or both by remap/alias. |

### Default Simulation Architecture

Use one standard simulation profile as the supported default:

```text
ROS 2 Jazzy workspace
  baxter_description / rethink_ee_description from ECN common, with local sim overlay
  baxter_gz_sim launch/worlds/ros_gz_bridge/controller config
  Gazebo Harmonic world
  gz_ros2_control GazeboSimSystem
  controller_manager
  joint_state_broadcaster
  left_arm_controller/right_arm_controller/head_controller/gripper controllers
  robot_state_publisher
  optional baxter_sim_compat shim topics
  MoveIt 2 config from S06
```

Default launch shape for S07/S08 to encode later:

| Launch Profile | Purpose | Expected Components |
|---|---|---|
| `sim.launch.py` | Headless or GUI Gazebo sim without MoveIt | `ros_gz_sim`, spawn Baxter, `robot_state_publisher`, `controller_manager`, `joint_state_broadcaster`, arm/head/gripper controllers, optional camera bridge. |
| `sim_moveit.launch.py` or MoveIt S06 equivalent | Full planning demo | Includes `sim.launch.py`, `move_group`, RViz, MoveIt controller config. |
| `sim_compat.launch.py` | Optional Baxter API parity profile | Includes standard sim plus `/robot/state`, `/robot/joint_states` mirror, endpoint/gripper/camera shims, and optional `JointCommand` shim. |

The default simulator should use Baxter's legacy joint names (`right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`, and left equivalents) unless S06 proves the ECN ROS 2 description has already changed them. This keeps hardware, S03 API findings, old MoveIt group definitions, and student documentation aligned. `BaxterMotionPlanning` remains useful for architecture, but not for canonical joint naming.

### Future Simulation Package Layout

Keep package count small.

| Package | Source | Role | Decision |
|---|---|---|---|
| `baxter_core_msgs` | `CentraleNantesRobotics/baxter_common_ros2` | Baxter messages/services, including `JointCommand`, `AssemblyState`, `EndpointState`, `EndEffector*`, camera services, and IK service type. | Adopt pinned dependency. |
| `baxter_description` | `CentraleNantesRobotics/baxter_common_ros2`, fork/patch if needed | Robot URDF/xacro, meshes, inertials/collisions. | Adopt, with local ROS 2/Harmonic review before release. |
| `rethink_ee_description` | `CentraleNantesRobotics/baxter_common_ros2` | End-effector geometry and electric/null/pneumatic gripper variants. | Adopt, simplify gripper simulation first. |
| `baxter_gz_sim` | New local package | Gazebo Harmonic worlds, sim launch files, `ros_gz_bridge` config, controller YAML, and simulation-specific xacro overlays. | Create in future implementation. |
| `baxter_sim_compat` | New local package, optional | Lightweight compatibility publishers/shims for Baxter topic names and `JointCommand` if a course needs them. | Defer unless parity is required; do not make default. |
| `baxter_moveit_config` | New/regenerated in S06 | MoveIt 2 SRDF, kinematics, controller config, RViz. | S06 owns. |

Do not create ROS 2 equivalents of `baxter_sim_controllers`, `baxter_sim_hardware`, `baxter_sim_io`, or `baxter_sim_kinematics` as direct ports. If a future package needs an equivalent behavior, make the smallest node for that specific behavior.

### URDF, Xacro, SDF, And Gazebo Strategy

Preserve:

- Link and joint names used by hardware and MoveIt where possible, especially arm joints `left_s0`...`left_w2` and `right_s0`...`right_w2`.
- Meshes, visual geometry, collision geometry, inertial data, pedestal option, electric gripper geometry, and tool frames from `baxter_description` and `rethink_ee_description`.
- End-effector frame naming needed by MoveIt 2 and endpoint-state compatibility.

Replace:

- Classic `libbaxter_gazebo_ros_control.so` with `<ros2_control>` using `gz_ros2_control/GazeboSimSystem` and the Gazebo plugin `libgz_ros2_control-system.so`.
- ROS 1 `hardware_interface/EffortJointInterface` transmissions with ROS 2 command/state interface declarations.
- Classic camera/laser/video plugins with Gazebo Harmonic native sensor tags and `ros_gz_bridge` mappings.
- Classic spawn/delete services with Gazebo Sim entity creation through `ros_gz_sim` launch/actions.

Recommended model split:

| Model File Type | Content |
|---|---|
| Base description xacro | Pure robot model for RViz, MoveIt, and robot_state_publisher. No Gazebo plugin side effects. |
| Sim overlay xacro | Includes base model, adds `ros2_control` hardware plugin, simulation-only sensors, and Gazebo-specific material/friction/self-collision parameters. |
| World SDF | Empty lab/world scene, optional table later, physics defaults, lighting, ground plane. |
| Bridge YAML | `ros_gz_bridge` mappings for selected camera/range/IMU topics only. |

### ros2_control Hardware Interface Strategy

Use `gz_ros2_control/GazeboSimSystem` as the simulation hardware plugin. It should expose only the interfaces needed by first-release controllers:

| Joint Group | Command Interfaces | State Interfaces | Notes |
|---|---|---|---|
| Left arm 7 joints | `position` | `position`, `velocity` | Default MoveIt/JTC path. |
| Right arm 7 joints | `position` | `position`, `velocity` | Default MoveIt/JTC path. |
| Head pan | `position` | `position`, `velocity` | Optional head demos. |
| Electric gripper actuated joint(s) | `position` | `position`, `velocity` | Simple open/close only. Use mimic/passive joints where possible. |

Do not expose torque/effort command interfaces in first release. They invite unsafe API parity expectations and require tuning that does not help MoveIt 2 demos. Add effort/velocity control only if a later course specifically teaches low-level control and accepts separate validation work.

### Controller Layout

Default controllers for the sim:

| Controller | Type | Joints | Default State |
|---|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | All simulated joints | Active at launch. |
| `left_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2` | Active at launch. |
| `right_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2` | Active at launch. |
| `head_controller` | `joint_trajectory_controller/JointTrajectoryController` | `head_pan` | Active if head is modeled. |
| `left_gripper_controller` | `position_controllers/GripperActionController` | Left electric gripper actuated joint | Active if electric gripper is modeled. |
| `right_gripper_controller` | `position_controllers/GripperActionController` | Right electric gripper actuated joint | Active if electric gripper is modeled. |

Controller naming should stay boring and ros2_control-native. If S06 wants hardware-style action names for MoveIt parity, add remaps/aliases above this layer instead of renaming the underlying controller manager to match Baxter topic paths.

### Simulated ROS API Surface

The sim should have two explicit API layers.

Standard ROS 2 layer, default:

| Name | Type | Source |
|---|---|---|
| `/joint_states` | `sensor_msgs/msg/JointState` | `joint_state_broadcaster` |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | `robot_state_publisher` and Gazebo/ROS 2 TF setup |
| `/left_arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `left_arm_controller` |
| `/right_arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `right_arm_controller` |
| `/head_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `head_controller` |
| `/left_gripper_controller/gripper_cmd` or controller default action name | `control_msgs/action/GripperCommand` | gripper controller |
| `/right_gripper_controller/gripper_cmd` or controller default action name | `control_msgs/action/GripperCommand` | gripper controller |

Baxter compatibility layer, optional but recommended for student-facing consistency:

| Name | Type | Behavior |
|---|---|---|
| `/robot/joint_states` | `sensor_msgs/msg/JointState` | Mirror or remap of `/joint_states`; keeps Noetic examples/docs recognizable. |
| `/robot/state` | `baxter_core_msgs/msg/AssemblyState` | Sim shim publishes `ready=true`, `enabled=true`, `stopped=false`, `error=false`, and estop false by default. It may accept enable/reset commands but should not pretend to model real safety. |
| `/robot/limb/{left,right}/endpoint_state` | `baxter_core_msgs/msg/EndpointState` | Optional shim computes pose from TF for each end-effector link. Twist/wrench can be zero or omitted-equivalent; document limited fidelity. |
| `/robot/end_effector/{left,right}_gripper/state` | `baxter_core_msgs/msg/EndEffectorState` | Optional shim reflects gripper joint position/open-close state. |
| `/robot/end_effector/{left,right}_gripper/properties` | `baxter_core_msgs/msg/EndEffectorProperties` | Optional shim publishes static electric-gripper capability metadata. |
| `/cameras/head_camera/image` and `/cameras/head_camera/camera_info` | `sensor_msgs/msg/Image`, `sensor_msgs/msg/CameraInfo` | Optional `ros_gz_bridge` remap for one head camera. Hand cameras later only if needed. |
| `/ExternalTools/{left,right}/PositionKinematicsNode/IKService` | `baxter_core_msgs/srv/SolvePositionIK` | Not default. If old examples require it, provide a small wrapper over MoveIt 2 `compute_ik`; S06 should decide. |

### `JointCommand` In Simulation

Do **not** expose `/robot/limb/{side}/joint_command` in the default sim profile. The default teaching and MoveIt path should use `FollowJointTrajectory`, matching S04's beginner/hardware action decision.

If course parity requires `JointCommand` in simulation, add it only in `sim_compat.launch.py`:

| Mode | Sim Behavior |
|---|---|
| `POSITION_MODE` | Accept joint names/positions, validate complete limb joint set, send a short `FollowJointTrajectory` goal to the matching arm controller. |
| `RAW_POSITION_MODE` | Reject by default. Add only for instructor profile. |
| `VELOCITY_MODE` | Reject in default compatibility shim. If needed later, use a separate controller profile and document incompatibility with MoveIt/JTC. |
| `TORQUE_MODE` | Reject. Not part of first-release sim. |

This should be a minimal ROS 2 node, not a port of `baxter_sim_controllers/BaxterPositionController`, `BaxterVelocityController`, or `BaxterEffortController`. A `forward_command_controller` profile is possible later for low-level labs, but it conflicts with the always-active trajectory-controller model and should not be the default.

### MoveIt 2 Connection And S06 Boundary

S05 defines that MoveIt 2 should execute against the arm `JointTrajectoryController` instances in simulation. S06 should decide the exact MoveIt 2 controller config, SRDF, kinematics plugins, planning groups, action namespaces, and whether to expose hardware-style aliases.

S06 should start from these assumptions:

- Sim controllers are `left_arm_controller` and `right_arm_controller` with `control_msgs/action/FollowJointTrajectory`.
- Hardware controllers are ROS 2 action shims from S04, likely `/robot/limb/{left,right}/follow_joint_trajectory` unless S06 chooses remapped aliases.
- MoveIt 2 config should preserve legacy groups `left_arm`, `right_arm`, `both_arms`, optional `left_hand`, and optional `right_hand` from S03.
- `BaxterMotionPlanning` is a useful MoveIt 2/ros2_control reference, but S06 should regenerate or manually recreate config from licensed descriptions and local requirements instead of copying unlicensed files.
- A custom `MoveArm` action from `BaxterMotionPlanning` is not part of the core architecture. Standard MoveIt 2 and `FollowJointTrajectory` are enough.

### Out Of Scope For First Release

Explicitly defer:

- Maintenance, tare, calibration, robust controller, and software update workflows.
- Full digital IO, analog IO, cuff, navigator, and Qt-style IO simulation.
- Old Classic Gazebo spawn/delete demos and project-specific pick-and-place scripts.
- Old Kinect/Xtion sensor manager launch files and warehouse/mongo workflows.
- Full camera fidelity, all three Baxter cameras at once, camera services that truly open/close Gazebo sensors, and calibrated real-camera parity.
- Full gripper physics, suction/pneumatic gripper realism, grasp contact tuning, and payload modeling.
- Torque/effort and velocity Baxter controller parity.
- `/robot/xdisplay` face display simulation unless a course explicitly needs display demos.
- Sonar/range sensor parity except optional simple hand range bridge if needed for a lab.

### Simulation Smoke Tests

A usable first-release sim must pass these checks before S07/S08 call it supported:

1. `ros2 launch ... sim.launch.py headless:=true` starts Gazebo Harmonic without GUI and exits cleanly on shutdown.
2. Baxter entity spawns in the world with no missing mesh paths and no Classic Gazebo plugin load errors.
3. `ros2 control list_controllers` shows `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller` active.
4. `/joint_states` publishes all 14 arm joints plus any modeled head/gripper joints at a stable rate.
5. Compatibility profile, if enabled, publishes `/robot/joint_states` and `/robot/state`.
6. A tiny `FollowJointTrajectory` goal to one arm succeeds and returns the arm to a neutral/safe pose.
7. `robot_state_publisher` and RViz show a coherent TF tree from world/base through both wrist/end-effector frames.
8. MoveIt 2 can load the robot model, plan for one arm, and execute to the active sim controller. S06 owns exact MoveIt test content.
9. Optional camera profile publishes one frame on `/cameras/head_camera/image` or a documented standard camera topic.
10. No smoke test depends on `/gazebo/spawn_urdf_model`, `gazebo_ros_control`, `baxter_sim_controllers`, or any Gazebo Classic API.

## Decisions

1. **Default sim profile:** Use Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + `joint_trajectory_controller` + MoveIt 2. This is the supported path for students and CI.
2. **No Classic port:** Do not port `baxter_gazebo`, `baxter_sim_controllers`, `baxter_sim_hardware`, `baxter_sim_io`, or `baxter_sim_kinematics` line by line.
3. **Community reuse:** Adopt `CentraleNantesRobotics/baxter_common_ros2` for messages/descriptions where possible. Use `angysof16/BaxterMotionPlanning` and `CentraleNantesRobotics/baxter_gz` as references only.
4. **Joint naming:** Preserve Baxter legacy joint names if technically possible. Do not inherit `BaxterMotionPlanning` renamed joint names as the blueprint default without an explicit S06/S08 decision.
5. **ros2_control interfaces:** Start with position command interfaces and position/velocity state interfaces for arms, head, and simple electric grippers.
6. **Controller layout:** Use `joint_state_broadcaster`, one JTC per arm, one JTC for head, and simple gripper action controllers. Avoid effort/velocity controllers in first release.
7. **Baxter compatibility:** Provide `/robot/joint_states` and `/robot/state` compatibility in sim if practical. Endpoint/gripper/camera compatibility is optional but useful. Direct `JointCommand` is optional and disabled by default.
8. **`JointCommand` shim:** If required, implement a minimal ROS 2 shim over active trajectory controllers for safe position commands only. Do not switch the default sim to a custom controller stack.
9. **MoveIt 2 boundary:** S06 owns SRDF, kinematics, MoveIt controller config, controller aliases, and dual sim/hardware execution details. S05 only fixes the sim controller baseline.
10. **Scope control:** First release prioritizes arm motion, robot visualization, one optional camera stream, simple grippers, and smoke-testable launches over full Baxter hardware emulation.

## Open Questions

- Does the ECN ROS 2 `baxter_description` preserve original joint names exactly, or will the project need a local description fork/patch to keep `left_s0`/`right_s0` style names?
- Which grippers are installed or required for the target courses: electric, suction/pneumatic, passive, custom, or none?
- Do student assignments require publishing `/robot/limb/{side}/joint_command` in simulation, or can that remain hardware/advanced-only?
- Should S06 expose MoveIt controller action names as `/left_arm_controller/follow_joint_trajectory`, `/robot/limb/{side}/follow_joint_trajectory`, or both through aliases/remaps?
- Is one head camera enough for simulation demos, or do courses need hand cameras, depth, range, or image calibration parity?
- Should the optional `ExternalTools/{side}/PositionKinematicsNode/IKService` compatibility wrapper exist in the sim, or should old IK examples be rewritten to use MoveIt 2 directly?
- What level of Gazebo physics tuning is acceptable before calling the sim usable: visual/kinematic trajectory execution only, or stable object interaction/grasping?
- Should CI include Gazebo headless smoke tests by default, or only launch/controller tests if Harmonic is too flaky in GitHub Actions or university CI?

## Artifacts

- Updated this S05 simulation architecture log: `logs/S05_simulation_architecture.log.md`
- Updated S05 status in `MASTER_PLAN.md`
- Appended S06 handoff prompt to `PROMPTS.md`
- Read-only local source paths inspected:
  - `baxter_noetic_ref/baxter_common/baxter_description/urdf/baxter.urdf.xacro`
  - `baxter_noetic_ref/baxter_common/baxter_description/urdf/baxter_base/baxter_base.gazebo.xacro`
  - `baxter_noetic_ref/baxter_simulator/baxter_gazebo/launch/baxter_world.launch`
  - `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/launch/baxter_sdk_control.launch`
  - `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/config/baxter_sim_controllers.yaml`
  - `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/config/baxter_left_electric_gripper_controller.yaml`
  - `baxter_noetic_ref/baxter_simulator/baxter_sim_hardware/config/baxter_right_electric_gripper_controller.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/baxter_controllers.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/gazebo_controllers.yaml`
- Primary upstream references inspected:
  - https://github.com/angysof16/BaxterMotionPlanning
  - https://raw.githubusercontent.com/angysof16/BaxterMotionPlanning/main/README.md
  - https://raw.githubusercontent.com/angysof16/BaxterMotionPlanning/main/gazebo_baxter/config/controllers.yaml
  - https://raw.githubusercontent.com/angysof16/BaxterMotionPlanning/main/baxter_moveit_config/config/moveit_controllers.yaml
  - https://raw.githubusercontent.com/angysof16/BaxterMotionPlanning/main/gazebo_baxter/urdf/robots/baxter_gazebo.urdf.xacro
  - https://github.com/CentraleNantesRobotics/baxter_gz
  - https://raw.githubusercontent.com/CentraleNantesRobotics/baxter_gz/main/README.md
  - https://github.com/CentraleNantesRobotics/baxter_common_ros2
  - https://raw.githubusercontent.com/CentraleNantesRobotics/baxter_common_ros2/master/README.rst
