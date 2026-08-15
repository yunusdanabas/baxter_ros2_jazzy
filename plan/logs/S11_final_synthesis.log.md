---
step: S11
title: "Final Synthesis"
agent_date: 2026-06-23
status: completed
previous_steps: [S01, S02, S03, S04, S05, S06, S07, S08, S09, S10]
---

# S11: Final Synthesis

## Task

Produced the final comprehensive migration blueprint for the future `baxter_ros2_jazzy` workspace. This is the synthesis and handoff artifact for the planning sequence. It consolidates S01-S10 into one actionable implementation reference and does not implement ROS 2 code.

Required source material read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `logs/S04_bridge_architecture.log.md`
- `logs/S05_simulation_architecture.log.md`
- `logs/S06_moveit_ros2_control.log.md`
- `logs/S07_dev_experience_tooling.log.md`
- `logs/S08_package_mapping.log.md`
- `logs/S09_risk_register.log.md`
- `logs/S10_docs_distribution.log.md`
- `MASTER_PLAN.md`

The read-only Noetic reference repository remains source material only: `baxter_noetic_ref/`.

## Findings

### 1. Executive Summary And Scope Boundary

The final recommendation is to build `baxter_ros2_jazzy` as a **hybrid ROS 2 Jazzy workspace**, not a native Baxter firmware migration and not a line-by-line port of the ROS 1 Noetic SDK.

The workspace should provide:

| Audience | First Useful Outcome | Support Boundary |
|---|---|---|
| Students without hardware | Gazebo Harmonic simulation, `ros2_control`, curated examples, MoveIt 2 one-arm planning/execution | Supported after sim and MoveIt smoke gates pass. |
| University users with a real Baxter | ROS 2 Jazzy student tooling connected to the existing ROS 1 Baxter through a bridge host | Hardware bridge non-motion and hardware motion are separate release claims. |
| External schools | Source-based workspace, pinned dependencies, docs, compatibility matrix, bridge-host setup guide | Best-effort community support, no official vendor support claim. |
| Maintainers | Small package graph, release gates, risk register, issue templates, handoff docs | No default dependence on unlicensed or low-adoption sources. |

Scope boundary:

- This plan creates a future implementation blueprint only.
- Do not modify or flash the Baxter embedded computer for native ROS 2.
- Do not depend on upstream `ros1_bridge` natively on Ubuntu 24.04 Noble/Jazzy.
- Do not port Gazebo Classic packages line-by-line.
- Do not promise apt/bloom/rosdistro packages for the first release.
- Do not vendor or copy unlicensed community code.
- Do not present raw safety-topic publishing as beginner hardware workflow.

### 2. Final Recommendation

Build `baxter_ros2_jazzy` as a **hybrid Jazzy workspace** with three primary paths:

| Path | Recommendation | Reason |
|---|---|---|
| Core/model | Adopt `CentraleNantesRobotics/baxter_common_ros2`, initially pinned to `678bfabea8c895b4134951a6c076217a90b9e0e6` | Licensed BSD-3-Clause, active, covers Baxter custom messages and descriptions. |
| Simulation | Use Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control` controllers | Jazzy/Harmonic is the supported modern simulation pairing; avoids Classic EOL and old ROS 1 controller plugins. |
| Real hardware | Use an ECN bridge-host hardware path with `baxter_bridge`, restricted allowlist, ROS 2 action shims, and safety gates | Baxter remains a ROS 1 robot boundary; bridge host centralizes networking and command ownership. |

Explicit non-goals:

- No native ROS 2 Baxter firmware migration.
- No first-release native real-Baxter `ros2_control` hardware interface.
- No direct Classic Gazebo migration.
- No broad Noetic example parity.
- No first-release maintenance/tare/update workflow recreation.
- No default Zenoh dependency.

### 3. Architecture Overview

```mermaid
flowchart TB
  subgraph Student[Student workstation or devcontainer]
    Dev[ROS 2 Jazzy workspace]
    Examples[baxter_examples]
    RViz[RViz / MoveIt clients]
  end

  subgraph Core[Core model and interfaces]
    ECN[CentraleNantesRobotics/baxter_common_ros2 pinned 678bfabea8c895b4134951a6c076217a90b9e0e6]
    Msgs[baxter_core_msgs / baxter_maintenance_msgs]
    Desc[baxter_description / rethink_ee_description]
  end

  subgraph Sim[Supported simulation stack]
    Gz[baxter_gz_sim]
    Harmonic[Gazebo Harmonic]
    RosGz[ros_gz]
    GzControl[gz_ros2_control]
    Controllers[left_arm_controller / right_arm_controller]
  end

  subgraph MoveIt[MoveIt 2 stack]
    MConfig[baxter_moveit_config regenerated]
    MoveGroup[move_group KDL OMPL]
    SimCtl[moveit_controllers_sim.yaml]
    HwCtl[moveit_controllers_hardware.yaml]
  end

  subgraph BridgeHost[Bridge host for real Baxter]
    ECNBridge[ECN baxter_bridge]
    HWBridge[baxter_hardware_bridge action shims and safety tools]
    RSP[robot_state_publisher]
  end

  subgraph Robot[Baxter real robot]
    ROS1[Baxter ROS 1 graph]
    State[/robot/state / /robot/joint_states]
    JointCmd[/robot/limb/*/joint_command]
  end

  subgraph Experimental[Experimental fallback]
    Zenoh[baxter-zenoh / BaxterSDK]
  end

  ECN --> Msgs
  ECN --> Desc
  Desc --> Dev
  Msgs --> Dev
  Dev --> Examples
  Dev --> RViz
  Dev --> Gz
  Gz --> Harmonic
  Gz --> RosGz
  Gz --> GzControl
  GzControl --> Controllers
  Controllers --> MConfig
  MConfig --> MoveGroup
  SimCtl --> MoveGroup
  HwCtl --> MoveGroup
  MoveGroup --> RViz
  Dev --> BridgeHost
  ECNBridge --> ROS1
  HWBridge --> ECNBridge
  RSP --> MoveGroup
  ROS1 --> State
  ECNBridge --> JointCmd
  Zenoh -. fallback only .-> ROS1
```

Text summary:

| Component | Runs Where | Primary Responsibility |
|---|---|---|
| Student workstation/devcontainer | Student machine or bridge-host devcontainer | Build, examples, sim, RViz, MoveIt clients, docs. |
| Core model/interfaces | Workspace source dependency | Baxter messages/services, URDF/Xacro, end-effector descriptions. |
| Sim stack | Student workstation/devcontainer | Gazebo Harmonic, `ros_gz`, `gz_ros2_control`, arm controllers. |
| MoveIt 2 | Student workstation for sim; bridge host or controlled lab domain for hardware | One-arm planning/execution with KDL and OMPL. |
| Bridge host | Lab-controlled machine wired to Baxter | ECN bridge, ROS 1 environment, action shims, safety tools, arbitration. |
| Baxter ROS 1 robot | Existing physical robot | Existing `/robot/*`, camera, IK, gripper, and joint command graph. |
| Experimental Zenoh fallback | Maintainer-only bridge experiment | Alternative transport if ECN bridge cannot satisfy install/runtime/throughput gates. |

### 4. Profile Definitions And Support Levels

| Profile | Launch Shape | Support Level | Included Packages | Required Gate |
|---|---|---|---|---|
| `sim` | `ros2 launch baxter_gz_sim sim.launch.py headless:=true` | Supported after smoke | `baxter_bringup`, `baxter_gz_sim`, ECN core packages | Baxter spawns, controllers active, `/joint_states` has all arm joints, tiny FJT succeeds. |
| `sim_moveit` | `ros2 launch baxter_bringup sim_moveit.launch.py` | Supported after smoke | `baxter_gz_sim`, `baxter_moveit_config`, MoveIt 2 | SRDF/KDL loads, one-arm plan and tiny sim execution succeed. |
| `hardware` | `ros2 launch baxter_hardware_bridge smoke_hardware.launch.py` | Hardware bridge non-motion | ECN `baxter_bridge`, `baxter_hardware_bridge`, ECN core packages | `/robot/state`, `/robot/joint_states`, IK/camera/gripper checks, hardware action names visible, no enable/motion. |
| `hardware_moveit` | `ros2 launch baxter_hardware_bridge hardware_moveit.launch.py allow_motion:=false` | Supervised hardware motion only after gate | `baxter_hardware_bridge`, `baxter_moveit_config`, MoveIt 2 | Tiny low-speed supervised trajectory per advertised arm, feedback, cancel/hold, safe state gating. |
| `sim_compat` | `ros2 launch baxter_sim_compat sim_compat.launch.py` | Optional | `baxter_sim_compat`, `baxter_gz_sim`, ECN core packages | `/robot/joint_states` and `/robot/state` publish; optional `JointCommand` shim rejects unsafe modes. |
| `experimental_zenoh` | Maintainer-specific | Experimental fallback | `baxter-zenoh`, optional `BaxterSDK`, restricted YAML | IT approval, restricted bridge YAML, target-robot smoke, measured reason to prefer over ECN. |

Support labels to use in README/docs/release notes:

| Label | Meaning |
|---|---|
| Supported core/model | Build/model gate passed. |
| Supported sim after smoke | Sim gate passed in documented environment. |
| Supported MoveIt sim after smoke | MoveIt sim gate passed. |
| Optional sim compatibility | Implemented and smoke-tested, but not default. |
| Hardware bridge non-motion | Real robot bridge checks pass without enable or motion. |
| Supervised hardware motion | Tiny trajectory gate passed under physical supervision. |
| Experimental Zenoh fallback | Maintainer-only, not default support. |
| Reference-only | Used for research, not imported or copied. |

### 5. Package Map And Dependency Graph

Adopted default community dependency:

| Repo | Initial Pin | Adopted Packages | Profile |
|---|---|---|---|
| `CentraleNantesRobotics/baxter_common_ros2` | `678bfabea8c895b4134951a6c076217a90b9e0e6` | `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, hardware-profile `baxter_bridge` | Core/model and hardware bridge |

First-release local packages:

| Package | Role | Build Type | First-Release Priority |
|---|---|---|---|
| `baxter_bringup` | Shared launch/profile entry points, model launch, combined profile launches, common args | Config-only `ament_cmake` | High |
| `baxter_gz_sim` | Gazebo Harmonic worlds, sim overlay Xacro, `ros_gz_bridge` mappings, controller YAML, sim smoke launch | Config-only `ament_cmake` | High for sim |
| `baxter_moveit_config` | Regenerated MoveIt 2 config, SRDF, KDL, OMPL, fake/sim/hardware controller YAMLs | Config-only `ament_cmake` | High for MoveIt |
| `baxter_hardware_bridge` | Bridge-host launch, ROS 2 FJT action shims, optional gripper/head shims, safe enable/status tools, hardware smoke checks | `ament_python` | High for hardware |
| `baxter_examples` | Curated student examples | `ament_python` | High |

Optional local package:

| Package | Role | Add Only If |
|---|---|---|
| `baxter_sim_compat` | `/robot/*` sim mirrors and optional safe position-only `JointCommand` shim | Courses require Baxter-native sim API parity. |

Do not create by default:

| Package | Reason |
|---|---|
| `baxter_smoke_tests` | Fold checks into `baxter_bringup`, `baxter_gz_sim`, and `baxter_hardware_bridge` until commands become bulky. |

Noetic package mapping:

| Noetic Package | Future Mapping | Decision |
|---|---|---|
| `baxter_common/baxter_common` | Covered by ECN common and docs | No local metapackage required first release. |
| `baxter_core_msgs` | ECN `baxter_core_msgs` | Adopt. |
| `baxter_description` | ECN `baxter_description` plus local sim overlays if needed | Adopt, verify legacy names. |
| `baxter_maintenance_msgs` | ECN `baxter_maintenance_msgs` | Build as interface package; defer maintenance workflows. |
| `rethink_ee_description` | ECN `rethink_ee_description` | Adopt. |
| `baxter_sdk` | Devcontainer, docs, `.repos`, launch profiles | Replace; no `baxter.sh` clone. |
| `baxter_interface` | Minimal behavior in `baxter_hardware_bridge`; optional future facade | Simplify. |
| `baxter_tools` | Safe tools and smoke checks in `baxter_hardware_bridge`; launch in `baxter_bringup` | Simplify. |
| `baxter_examples` | New `baxter_examples` | Rewrite curated examples only. |
| `baxter_moveit_config` | New regenerated `baxter_moveit_config` | Replace MoveIt 1 config. |
| `baxter_simulator/baxter_simulator` | `baxter_gz_sim` docs/profile | Drop metapackage. |
| `baxter_gazebo` | New `baxter_gz_sim` | Replace Classic stack. |
| `baxter_sim_controllers` | Standard `ros2_control` controllers | Replace; no custom controller port. |
| `baxter_sim_examples` | New `baxter_examples` | Simplify. |
| `baxter_sim_hardware` | `gz_ros2_control` plus optional `baxter_sim_compat` | Replace. |
| `baxter_sim_io` | Not recreated | Drop until concrete course need. |
| `baxter_sim_kinematics` | MoveIt 2 KDL and optional compatibility wrapper later | Replace/drop. |

Dependency graph:

```text
Core/model
  baxter_bringup
    -> baxter_description
    -> rethink_ee_description
    -> robot_state_publisher, xacro, tf2_ros
  baxter_core_msgs
    -> std_msgs, sensor_msgs, geometry_msgs

Sim
  baxter_gz_sim
    -> baxter_bringup
    -> baxter_description
    -> ros_gz_sim, ros_gz_bridge
    -> gz_ros2_control
    -> controller_manager
    -> joint_state_broadcaster
    -> joint_trajectory_controller

Sim compatibility optional
  baxter_sim_compat
    -> baxter_gz_sim
    -> baxter_core_msgs
    -> sensor_msgs, control_msgs, trajectory_msgs, tf2_ros

MoveIt
  baxter_moveit_config
    -> baxter_description
    -> rethink_ee_description
    -> MoveIt 2, KDL, OMPL, control_msgs

Hardware bridge
  baxter_hardware_bridge
    -> baxter_core_msgs
    -> baxter_description
    -> ECN baxter_bridge
    -> control_msgs, trajectory_msgs, sensor_msgs, std_msgs, std_srvs, diagnostic_msgs, tf2_ros
    -> bridge-host ROS 1 support deps outside ordinary sim CI

Hardware MoveIt
  hardware_moveit
    -> baxter_hardware_bridge
    -> baxter_moveit_config
    -> action shims at /robot/limb/{left,right}/follow_joint_trajectory

Examples
  baxter_examples
    -> baxter_core_msgs
    -> control_msgs, trajectory_msgs
    -> baxter_gz_sim for sim examples
    -> baxter_moveit_config for MoveIt examples
    -> baxter_hardware_bridge for hardware examples
```

`.repos` guidance:

| File | Default? | Contents |
|---|---:|---|
| `repos/baxter_core.repos` | Yes | ECN `baxter_common_ros2` pinned to `678bfabea8c895b4134951a6c076217a90b9e0e6`. |
| `repos/baxter_sim.repos` | Optional/no-op initially | No unlicensed sim repo by default. |
| `repos/baxter_hardware.repos` | Bridge-host only | ECN common if needed; optional `baxter_legacy` only after license verification. |
| `repos/baxter_experimental.repos` | Explicit opt-in | `baxter-zenoh`, `BaxterSDK`, optional `baxter_gz`, all pinned by full SHA after verification. |

### 6. Real Hardware Bridge Architecture

Default hardware topology:

```text
Baxter ROS 1 robot <-> wired robot LAN <-> lab bridge host <-> controlled ROS 2 lab domain or SSH/devcontainer <-> student clients
```

Default bridge decision:

| Decision | Carry Forward |
|---|---|
| Default bridge | ECN `baxter_bridge` from `CentraleNantesRobotics/baxter_common_ros2`. |
| Bridge host | One lab-controlled bridge host per Baxter, not per-student motion bridges. |
| ROS 1 support | Use ECN `baxter_legacy` only as bridge-host packaging reference until license is verified. |
| Arbitration | Keep ECN arbitration visible and enabled: `allow_multiple:=False`, `/bridge_auth`, `/bridge_force`, publisher display. |
| Action bridging | Do not bridge ROS 1 actionlib directly by default; provide ROS 2 action shims above bridged topics. |
| Safety | No auto-enable, no raw beginner safety-topic publishing, mandatory smoke checks. |

Minimum hardware allowlist:

| Direction | Name | Type | Required For |
|---|---|---|---|
| ROS 1 to ROS 2 | `/robot/state` | `baxter_core_msgs/msg/AssemblyState` | Enable/error/e-stop state. |
| ROS 1 to ROS 2 | `/robot/joint_states` | `sensor_msgs/msg/JointState` | MoveIt state, feedback, visualization. |
| ROS 1 to ROS 2 | `/robot/limb/{left,right}/endpoint_state` | `baxter_core_msgs/msg/EndpointState` | SDK facade and pose examples. |
| ROS 1 to ROS 2 | `/robot/limb/{left,right}/collision_avoidance_state` | `baxter_core_msgs/msg/CollisionAvoidanceState` | Tuck/untuck and diagnostics. |
| ROS 1 to ROS 2 | `/robot/end_effector/{left,right}_gripper/state` | `baxter_core_msgs/msg/EndEffectorState` | Gripper support if installed. |
| ROS 1 to ROS 2 | `/robot/end_effector/{left,right}_gripper/properties` | `baxter_core_msgs/msg/EndEffectorProperties` | Gripper capability detection. |
| ROS 1 to ROS 2 | `/cameras/head_camera/image` | `sensor_msgs/msg/Image` | One camera stream on demand. |
| ROS 1 to ROS 2 | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | Visualization and late subscribers. |
| ROS 2 to ROS 1 | `/robot/set_super_enable` | `std_msgs/msg/Bool` | Wrapped enable/disable tool only. |
| ROS 2 to ROS 1 | `/robot/set_super_reset` | `std_msgs/msg/Empty` | Explicit reset tool only. |
| ROS 2 to ROS 1 | `/robot/set_super_stop` | `std_msgs/msg/Empty` | Admin/software stop only; not routine cancel. |
| ROS 2 to ROS 1 | `/robot/limb/{left,right}/joint_command` | `baxter_core_msgs/msg/JointCommand` | Action-shim output and advanced labs. |
| ROS 2 to ROS 1 | `/robot/limb/{left,right}/set_speed_ratio` | `std_msgs/msg/Float64` | Conservative speed. |
| ROS 2 to ROS 1 | `/robot/limb/{left,right}/joint_command_timeout` | `std_msgs/msg/Float64` | Safety timeout. |
| ROS 2 client to ROS 1 service | `/ExternalTools/{left,right}/PositionKinematicsNode/IKService` | `baxter_core_msgs/srv/SolvePositionIK` | Hardware IK compatibility. |
| ROS 2 client to ROS 1 service | `/cameras/list`, `/cameras/open`, `/cameras/close` | Baxter camera services | Camera discovery and control. |

Hardware action shims:

| Action Name | Type | Output Topic | Required Behavior |
|---|---|---|---|
| `/robot/limb/left/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `/robot/limb/left/joint_command` | Validate left 7-joint goals, state-gate, low-speed position commands, feedback, cancel/hold. |
| `/robot/limb/right/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `/robot/limb/right/joint_command` | Validate right 7-joint goals, state-gate, low-speed position commands, feedback, cancel/hold. |

QoS defaults:

| API Class | QoS Default |
|---|---|
| State topics | Reliable, volatile, keep last 10. |
| Command topics | Reliable, volatile, keep last 1; no transient-local commands. |
| `/tf_static` | Reliable, transient local, keep last 100. |
| Cameras | Best effort, volatile, keep last 1 or 2. |
| Services | Reliable service defaults. |

Hardware bridge smoke checks before any motion:

1. Physical workspace clear and e-stop reachable.
2. Bridge host can reach robot IP and ROS 1 master on port `11311`.
3. ECN bridge starts and expected topics/services are visible.
4. `/robot/state` returns sane state.
5. `/robot/joint_states` is stable and includes all 14 arm joints.
6. IK services are visible for both arms.
7. Gripper state/properties arrive if grippers are installed.
8. `/cameras/list` works and one low-bandwidth camera can open/close if camera support is claimed.
9. Both hardware FJT action names are visible with no trajectory sent.
10. Only after explicit enable and physical supervision, run tiny low-speed motion if hardware motion support is being claimed.

### 7. Simulation Architecture

Default sim is a standard ROS 2 manipulator stack:

```text
baxter_gz_sim
  -> Gazebo Harmonic
  -> ros_gz_sim / ros_gz_bridge
  -> gz_ros2_control/GazeboSimSystem
  -> controller_manager
  -> joint_state_broadcaster
  -> left_arm_controller / right_arm_controller
  -> optional head and electric gripper controllers
```

Controller layout:

| Controller | Type | Joints | Action Name |
|---|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | All simulated joints | none |
| `left_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2` | `/left_arm_controller/follow_joint_trajectory` |
| `right_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2` | `/right_arm_controller/follow_joint_trajectory` |
| `head_controller` | `joint_trajectory_controller/JointTrajectoryController` | `head_pan` | Optional |
| `left_gripper_controller` | `position_controllers/GripperActionController` | Left electric gripper actuated joint | Optional |
| `right_gripper_controller` | `position_controllers/GripperActionController` | Right electric gripper actuated joint | Optional |

Model strategy:

| Layer | Content |
|---|---|
| Base Xacro | Pure Baxter model from licensed descriptions; no Gazebo side effects. |
| Sim overlay Xacro | Adds `ros2_control`, Harmonic sensors, simulation-specific material/friction/self-collision parameters. |
| World SDF | Empty lab/teaching scene, ground plane, lighting, optional table later. |
| Bridge YAML | `ros_gz_bridge` mappings for selected sensors only. |

Sim API:

| API | Default? | Notes |
|---|---:|---|
| `/joint_states` | Yes | From `joint_state_broadcaster`. |
| `/left_arm_controller/follow_joint_trajectory` | Yes | Canonical sim action name. |
| `/right_arm_controller/follow_joint_trajectory` | Yes | Canonical sim action name. |
| `/robot/joint_states` | Optional via `baxter_sim_compat` | Mirror for legacy familiarity. |
| `/robot/state` | Optional via `baxter_sim_compat` | Simple ready/enabled state, not real safety. |
| `/robot/limb/{side}/joint_command` | Optional only | Safe position-only shim if courses require it. |

Defer or intentionally omit:

- Gazebo Classic APIs and `/gazebo/spawn_*` workflows.
- Custom ROS 1 `baxter_sim_controllers` port.
- Torque/effort/velocity first-release controllers.
- Qt IO/navigator sim.
- Full camera parity and all three camera streams.
- Full gripper physics, suction realism, grasp contact tuning.
- Maintenance/tare/calibration/update workflows.

Simulation support gate:

| Check | Pass Criteria |
|---|---|
| Launch | `sim.launch.py headless:=true` starts and exits cleanly. |
| Model | Baxter entity spawns with meshes and no Classic plugin errors. |
| Controllers | `joint_state_broadcaster`, `left_arm_controller`, `right_arm_controller` active. |
| State | `/joint_states` publishes all 14 arm joints. |
| Motion | Tiny FJT goal succeeds for advertised arm(s). |
| TF | Coherent tree from world/base through end-effector frames. |

### 8. MoveIt 2 And `ros2_control` Architecture

MoveIt 2 config must be regenerated locally as `baxter_moveit_config`, using the selected ROS 2 Baxter description. Use the Noetic config as a semantic checklist, not as a file-level port.

First-release MoveIt scope:

| Feature | Scope |
|---|---|
| `left_arm` | Supported after sim execution gate. |
| `right_arm` | Supported after sim execution gate. |
| `both_arms` | Include in SRDF for planning-scene completeness, mark execution limited/experimental. |
| Gripper geometry | Include if modeled/installed. |
| Gripper action/open-close | Optional, low fidelity. |
| Head | Model and optionally control outside MoveIt. |
| Planning pipeline | OMPL only, default RRTConnect. |
| Kinematics | KDL first; TRAC-IK only if KDL fails smoke. |
| Servo, Pilz, CHOMP, STOMP, IKFast | Deferred. |

SRDF concepts to preserve:

| Item | Plan |
|---|---|
| `left_arm` | 7-DOF chain using legacy left arm joint names if possible. |
| `right_arm` | 7-DOF chain using legacy right arm joint names if possible. |
| `both_arms` | Present but not an execution claim. |
| `left_hand`, `right_hand` | Include only when gripper geometry/joints exist. |
| `left_neutral`, `right_neutral` | Preserve Noetic neutral values. |
| `world_joint` | Fixed virtual joint, parent `world`, child `base`. |

Canonical action names:

| Profile | Action Name |
|---|---|
| Sim left | `/left_arm_controller/follow_joint_trajectory` |
| Sim right | `/right_arm_controller/follow_joint_trajectory` |
| Hardware left | `/robot/limb/left/follow_joint_trajectory` |
| Hardware right | `/robot/limb/right/follow_joint_trajectory` |

MoveIt controller files:

| File | Purpose |
|---|---|
| `moveit_controllers_sim.yaml` | Targets sim `left_arm_controller` and `right_arm_controller`. |
| `moveit_controllers_hardware.yaml` | Targets hardware action shims under `/robot/limb/{side}`. |
| `moveit_controllers_fake.yaml` | Optional RViz/model-only checks. |

Hardware MoveIt path:

```text
MoveIt 2 -> /robot/limb/{side}/follow_joint_trajectory action shim -> /robot/limb/{side}/joint_command -> ECN baxter_bridge -> Baxter ROS 1 robot
```

Do not build a native hardware `ros2_control` driver in first release. It adds safety ambiguity and maintenance cost without improving the initial teaching path.

MoveIt support gate:

| Check | Pass Criteria |
|---|---|
| Model | `robot_description` and `robot_description_semantic` load. |
| Groups | `left_arm`, `right_arm`, `both_arms`, neutral states, fixed `world_joint` present. |
| Names | URDF, SRDF, controller YAML, and controller output agree on all 14 arm joints. |
| Planning | KDL and OMPL plan one-arm neutral/tiny goal. |
| Sim execution | Tiny trajectory executes through sim action names. |
| Hardware non-motion | MoveIt detects hardware action shims without sending goals. |

### 9. Developer Experience, Launch Profiles, Examples, Devcontainer, `.repos`, And CI

Future repository name: `baxter_ros2_jazzy`.

Recommended top-level layout:

```text
baxter_ros2_jazzy/
  README.md
  docs/
  repos/
  src/
  .devcontainer/
  examples/
  scripts/
  .github/workflows/
  LICENSE
  CONTRIBUTING.md
  SUPPORT.md
  SECURITY.md
  CHANGELOG.md
```

Launch profile ownership:

| Launch Profile | Owning Package | Purpose |
|---|---|---|
| `baxter_description.launch.py` | `baxter_bringup` | Model-only robot_state_publisher sanity check. |
| `moveit_rviz.launch.py` | `baxter_moveit_config` | MoveIt/RViz fake or planning-only profile. |
| `sim.launch.py` | `baxter_gz_sim` | Gazebo Harmonic + controllers, no MoveIt. |
| `sim_moveit.launch.py` | `baxter_bringup` | Combined sim + MoveIt executable profile. |
| `sim_compat.launch.py` | `baxter_sim_compat` | Optional `/robot/*` sim compatibility. |
| `hardware_bridge.launch.py` | `baxter_hardware_bridge` | Bridge-host profile, no MoveIt execution. |
| `hardware_moveit.launch.py` | `baxter_hardware_bridge` | Hardware action shims + MoveIt, no auto-enable. |
| `smoke_sim.launch.py` | `baxter_gz_sim` | Headless sim/controller smoke. |
| `smoke_hardware.launch.py` | `baxter_hardware_bridge` | Non-motion real robot bridge checks. |

Default launch arguments:

| Arg | Applies To | Meaning |
|---|---|---|
| `headless:=true|false` | sim | Run Gazebo without GUI. |
| `rviz:=true|false` | MoveIt/model | Start RViz. |
| `use_sim_time:=true|false` | sim | Use Gazebo clock. |
| `left_electric_gripper:=true|false` | model/sim/MoveIt | Select gripper geometry/controllers. |
| `right_electric_gripper:=true|false` | model/sim/MoveIt | Select gripper geometry/controllers. |
| `compat:=true|false` | sim | Enable optional compatibility nodes. |
| `ros_domain_id` | hardware/network docs | One domain per robot bench. |
| `allow_motion:=false` | hardware | Hardware launch defaults to no motion. |

Devcontainer:

| Area | Include |
|---|---|
| OS/ROS | Ubuntu 24.04 Noble, ROS 2 Jazzy. |
| Sim | Gazebo Harmonic, `ros_gz`, `gz_ros2_control`. |
| Control | `ros2_control`, `ros2_controllers`, controller manager. |
| Planning | MoveIt 2, RViz plugins, KDL/OMPL packages. |
| Tools | `colcon`, `vcstool`, `rosdep`, `xacro`, `robot_state_publisher`. |
| Camera optional | `cv_bridge`, `image_transport`, OpenCV utilities if examples ship. |

Do not put the ECN hardware bridge runtime into the default student devcontainer. Bridge-host setup is separate.

First-release examples:

| Example | Profile | Behavior |
|---|---|---|
| `sim_tiny_trajectory` | `sim` | Send tiny FJT goal to `/left_arm_controller/follow_joint_trajectory` or `/right_arm_controller/follow_joint_trajectory`. |
| `sim_moveit_neutral` | `sim_moveit` | Plan/execute one arm to `left_neutral` or `right_neutral`. |
| `hardware_bridge_smoke` | `hardware` | Read state/joint states/services/action availability with no enable and no motion. |
| `hardware_enable_status` | `hardware` | Print state fields and require explicit confirmation before enable/disable/reset. |
| `gripper_open_close` | `sim` or `hardware` | Optional after gripper inventory/model validation. |

Default CI:

| Check | Default CI? |
|---|---:|
| `vcs import` default `.repos` | Yes |
| `rosdep install` non-hardware deps | Yes |
| `colcon build --symlink-install` | Yes |
| Lint/import checks for local packages | Yes |
| Xacro/model loading | Yes |
| MoveIt model/fake config load | Yes |
| Headless Gazebo smoke | Yes only if runner proves stable; otherwise manual/allowed-flaky |
| Real hardware, ROS 1 master, `baxter_legacy`, Zenoh, broad cameras | No |

### 10. Documentation And Distribution Strategy

README first screen must include:

| Item | Requirement |
|---|---|
| Title | `baxter_ros2_jazzy`. |
| Scope warning | Community/university ROS 2 Jazzy workspace; no official vendor support; no native robot firmware migration. |
| Badges | ROS 2 Jazzy, Ubuntu Noble, Gazebo Harmonic, MoveIt 2, source `.repos` install, CI/docs when available. |
| Hardware warning | Bridge-host based; no launch auto-enables; motion supervised and gated. |
| Mode selector | `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, `experimental_zenoh`. |

Required docs tree:

| Path | Purpose |
|---|---|
| `docs/index.md` | Docs landing page and mode selector. |
| `docs/getting_started_sim.md` | 15-minute devcontainer + sim path. |
| `docs/simulation.md` | Gazebo Harmonic, controllers, optional camera/gripper. |
| `docs/moveit_guide.md` | MoveIt 2 one-arm scope, action names, smoke checks. |
| `docs/hardware_bridge_setup.md` | Bridge host, robot LAN, ROS 1 env, ECN arbitration, allowlist. |
| `docs/hardware_safety.md` | Physical checklist, enable/status tool, state gating, cancel/hold behavior. |
| `docs/examples.md` | Curated examples. |
| `docs/troubleshooting.md` | DDS, meshes, controllers, Gazebo, MoveIt names, bridge/camera/gripper failures. |
| `docs/package_map.md` | S08 package map and intentionally not recreated packages. |
| `docs/compatibility_matrix.md` | Tested versions, support labels, deferred validation backlog. |
| `docs/repos_and_pins.md` | `.repos`, full SHAs, pin update policy. |
| `docs/licensing_and_sources.md` | Adopted/reference/experimental/skipped sources and license status. |
| `docs/ci_release_checklist.md` | Build/lint/model/sim/MoveIt/hardware/licensing gates. |
| `docs/maintainer_handoff.md` | Bridge-host runbook, ownership, pin cadence, hardware inventory. |
| `docs/experimental_zenoh.md` | Maintainer-only fallback, IT/network constraints, restricted YAML. |

15-minute onboarding path:

| Step | Command Shape | Outcome |
|---|---|---|
| Clone/open devcontainer | Standard VS Code/devcontainer workflow | Noble/Jazzy/Harmonic deps available. |
| Import core | `vcs import src < repos/baxter_core.repos` | ECN common at full SHA. |
| Install/build | `rosdep install ...` and `colcon build --symlink-install` | Core/model/sim packages build. |
| Source | `source install/setup.bash` | Workspace active. |
| Launch sim | `ros2 launch baxter_gz_sim sim.launch.py headless:=true` | Baxter spawns and controllers active. |
| Tiny motion | `ros2 run baxter_examples sim_tiny_trajectory --arm left` | Tiny one-arm FJT succeeds. |

Distribution:

| Area | Decision |
|---|---|
| First release | Source checkout + pinned `.repos`. |
| Docker | Default devcontainer for sim/MoveIt/docs; bridge host documented separately. |
| Versioning | Semver with profile status in release notes, or capability tag such as `v0.1.0-sim`. Avoid `1.0` until handoff and hardware gates stabilize. |
| Rosdistro | Later only, likely message/description packages first, after CI/licensing/maintainer ownership. |
| Issue templates | Sim bug, hardware bridge bug, docs issue, safety concern, dependency pin update, feature request. |
| PR template | Profile changed, smoke checks, pin changes, hardware safety, copied/imported third-party code/license. |

### 11. Risk Register Summary And Release Gates

Highest risks:

| Risk Area | Summary | Mitigation |
|---|---|---|
| Hardware bridge | ECN bridge installability and target robot graph may differ. | Bridge-host-only setup, restricted allowlist, non-motion smoke gate. |
| Hardware safety | Auto-enable, stale commands, unsafe state acceptance, raw `JointCommand` exposure. | Safe tools, volatile command QoS, state-gated action shims, no raw beginner commands. |
| Motion/action | FJT shim timing/feedback/cancel may be wrong. | Exact joint validation, tiny supervised trajectory gate, cancel/hold test. |
| Network/QoS | DDS discovery/firewall/cameras/high-rate topics can fail. | Prefer SSH/devcontainer on bridge host, one domain per bench, one camera on demand, QoS policy. |
| Simulation | Gazebo CI flakiness, model/name mismatches, controller startup. | Model and fake MoveIt gates always; headless sim required only if stable; wait for controller manager. |
| MoveIt | SRDF collision matrix, KDL, joint limits, hardware controller names. | Regenerate config, one-arm gates, separate sim/hardware controller YAMLs. |
| Licensing | Unlicensed sim/legacy repos are tempting to copy. | Default `.repos` only licensed ECN common; unlicensed repos reference-only. |
| Documentation | Users may confuse sim support with hardware motion support. | Mode selector, compatibility matrix, profile labels, release-note gates. |
| Maintenance | Bus factor and bridge-host knowledge loss. | Small package graph, handoff docs, bridge-host runbook, named maintainer backlog. |
| Zenoh fallback | New, low adoption, IT and broad YAML risks. | Experimental only, restricted YAML, switch only after measured ECN limitation. |

Release gates:

| Gate | Required For | Go/No-Go Threshold |
|---|---|---|
| Core/model | Any release | Build succeeds, model loads, meshes resolve, `/tf_static` works, legacy arm joint names present. |
| Sim | Supported `sim` profile | Headless Harmonic launch, Baxter spawn, arm controllers active, all arm joint states, tiny FJT succeeds. |
| MoveIt sim | Supported `sim_moveit` profile | SRDF/KDL loads, one-arm plan, tiny sim execution through both advertised sim action names. |
| Sim compatibility | Optional `sim_compat` support | `/robot/joint_states` and `/robot/state` publish; optional `JointCommand` rejects unsafe modes. |
| Hardware bridge non-motion | `hardware` support | Target robot state/joint states/services/action names visible and message flow confirmed without enable/motion. |
| Hardware safety | Any hardware docs/support | No auto-enable; safe tool requires confirmation; shims reject unsafe state; command QoS not transient-local. |
| Hardware motion | `hardware_moveit` motion claim | Supervised tiny low-speed trajectory per advertised arm, feedback correct, cancel holds, safe state gating verified. |
| CI | Default repository CI | No hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams. |
| Licensing | Any public release | Default imports only licensed sources; no copied unlicensed code/config. |
| Docs | Any public release | README mode selector, compatibility matrix, safety docs, `.repos` docs, release checklist, handoff docs exist. |

### 12. Phased Implementation Roadmap

| Phase | Goal | Main Work | Exit Gate |
|---|---|---|---|
| Phase 0: Repository skeleton | Create `baxter_ros2_jazzy` implementation repo | README skeleton, docs skeleton, `.devcontainer`, `repos/baxter_core.repos`, local package stubs only when needed | `vcs import`, `rosdep`, `colcon build` for empty/minimal workspace. |
| Phase 1: Core/model | Adopt ECN common and validate model | Import pinned ECN common, model launch, mesh resolution, legacy joint-name verification | Core/model gate passes. |
| Phase 2: Simulation | Supported Harmonic sim | `baxter_gz_sim`, sim overlay, controller YAML, `sim.launch.py`, `smoke_sim.launch.py`, `sim_tiny_trajectory` | Sim gate passes. |
| Phase 3: MoveIt sim | Supported one-arm MoveIt in sim | Regenerate `baxter_moveit_config`, KDL/OMPL, sim controller YAML, `sim_moveit.launch.py`, neutral examples | MoveIt sim gate passes. |
| Phase 4: Documentation baseline | Public sim-first usability | README mode selector, `getting_started_sim`, simulation, MoveIt guide, compatibility matrix, repos/pins, license page | 15-minute onboarding works from docs. |
| Phase 5: Hardware bridge non-motion | Real robot visibility without motion | Bridge-host setup, ECN bridge, restricted allowlist, robot state/joint/camera/IK/gripper checks, action-shim availability | Hardware bridge non-motion gate passes on target robot. |
| Phase 6: Hardware action shims | Safe hardware trajectory boundary | FJT shims, safe enable/status, state gating, speed ratio/timeout, cancel/hold | Hardware safety gate passes; no motion claim yet. |
| Phase 7: Supervised hardware motion | Optional motion support claim | Tiny low-speed one-arm trajectories, feedback/cancel/hold validation, MoveIt hardware YAML | Hardware motion gate passes for each advertised arm. |
| Phase 8: Optional compatibility/features | Add only measured needs | `baxter_sim_compat`, grippers, camera examples, hardware IK wrapper, Zenoh fallback tests | Each optional feature has its own smoke gate and support label. |
| Phase 9: Release hardening | Handoff and distribution | CI, issue templates, changelog, release notes, maintainer handoff, pin review process | Release checklist and handoff drill pass. |

Implementation ordering rule: do not start hardware motion work before hardware bridge non-motion and hardware safety gates exist.

### 13. Compatibility Matrix And Deferred Validation Backlog

Compatibility matrix to publish:

| Component | Planned Version / Pin | Profile | Status Until Tested | Gate / Notes |
|---|---|---|---|---|
| Ubuntu | 24.04 Noble | all | Required | Jazzy Tier 1. |
| ROS 2 | Jazzy | all | Required | Student/devcontainer baseline. |
| Gazebo | Harmonic | `sim`, `sim_moveit` | Supported after smoke | Headless launch and controller gate. |
| MoveIt 2 | Jazzy apt/source as documented | `sim_moveit`, `hardware_moveit` | Supported/supervised by profile | KDL + OMPL one-arm scope. |
| `baxter_common_ros2` | `678bfabea8c895b4134951a6c076217a90b9e0e6` | core/hardware | Adopted | Pin update requires gates. |
| RMW | `rmw_fastrtps_cpp` first unless lab selects another; Cyclone DDS if tested | all | Tested field required | Record actual CI/lab RMW. |
| Bridge host | Noble/Jazzy + ECN bridge + ROS 1 support path | `hardware` | Deferred | Clean install and target robot smoke required. |
| Real Baxter robot | Target robot graph | `hardware` | Deferred | Validate `/robot/state`, `/robot/joint_states`, IK, cameras, grippers, actions. |
| Cameras | Head camera first | sim/hardware optional | Optional | One stream on demand. |
| Grippers | Electric if installed/modeled | sim/hardware optional | Optional | Inventory required. |
| Zenoh | Full pinned SHAs if used | `experimental_zenoh` | Experimental | IT approval and restricted YAML required. |

Deferred validation backlog:

| Backlog Item | Blocks | Future Check |
|---|---|---|
| Target Baxter ROS 1 distro, firmware, and graph | Hardware support | Run `hardware_bridge_smoke` on target robot. |
| ECN `baxter_bridge` installability | Hardware bridge docs/support | Clean bridge-host install rehearsal. |
| University DDS/multicast/firewall policy | Remote laptop hardware workflow | Test discovery or require SSH/devcontainer on bridge host. |
| Zenoh and Docker host-networking acceptance | `experimental_zenoh` | IT approval, restricted YAML, measured ECN comparison. |
| Physical gripper and camera inventory | Optional examples/support labels | Inspect hardware and run smoke checks. |
| ECN `baxter_description` legacy joint/link names | Core/model, sim, MoveIt, hardware shims | Verify `left_s0`...`right_w2` names in Xacro, controllers, MoveIt. |
| `baxter_legacy`, `BaxterMotionPlanning`, and other unlicensed sources | Reuse/import decisions | License review or keep reference-only. |
| Headless Gazebo Harmonic CI stability | Required sim CI gate | Repeated CI smoke. |
| MoveIt hardware action-name compatibility | `hardware_moveit` | Test `/robot/limb/{side}` actions; add aliases only if needed. |
| Course need for direct `JointCommand` in simulation | `baxter_sim_compat` scope | Instructor decision. |
| Maintainer ownership after graduation | Production/lab support claim | Named maintainer group and handoff drill. |
| Docs hosting target and future repo license | Public distribution | University decision. |

### 14. Open Questions Requiring User Or University Decisions

These are not solved by planning and must remain visible:

| Question | Decision Owner | Why It Matters |
|---|---|---|
| What target Baxter ROS 1 distro, firmware, and graph are actually present? | Lab admin / hardware owner | Determines bridge setup and expected API names. |
| Can ECN `baxter_bridge` install cleanly on the selected bridge host? | Maintainer / lab admin | Blocks hardware bridge support. |
| Will students run hardware nodes from laptops, or SSH/devcontainer into the bridge host? | University IT / course owner | Determines DDS/firewall docs and safety model. |
| Is Zenoh and Docker host-networking acceptable? | University IT | Determines whether `experimental_zenoh` can be tested. |
| Which physical grippers and cameras are installed? | Lab admin | Determines optional examples and support labels. |
| Does ECN `baxter_description` preserve required legacy joint/link names? | Implementer | Blocks core/model, sim, MoveIt, and hardware action shims. |
| Can `baxter_legacy`, `BaxterMotionPlanning`, and other unlicensed repos be reused? | Maintainer / legal / upstream authors | Determines `.repos` and source copying rules. |
| Is headless Gazebo Harmonic reliable in chosen CI? | Maintainer | Determines required vs manual sim CI gate. |
| Will MoveIt 2 accept `/robot/limb/{side}` hardware controller names? | Implementer | Determines whether action aliases are needed. |
| Does the course require direct `JointCommand` in sim? | Course owner | Determines whether `baxter_sim_compat` ships first release. |
| Who maintains the repo after graduation? | University / faculty | Determines whether production/lab support can be claimed. |
| What docs hosting target and project license should be used? | Repository owner / university | Blocks public release hygiene. |

### 15. Final Go/No-Go Criteria

Go for first public sim-focused release if:

- Default `.repos` contains only licensed sources, initially ECN `baxter_common_ros2` at the full SHA pin.
- `colcon build --symlink-install` passes in a clean Noble/Jazzy devcontainer.
- Core/model gate passes with meshes and legacy arm joint names.
- `sim.launch.py headless:=true` passes the sim smoke gate, or the release clearly labels Gazebo smoke as manually validated if CI is flaky.
- `sim_tiny_trajectory` works for at least one advertised arm.
- `baxter_moveit_config` loads and one-arm MoveIt sim planning/execution passes if `sim_moveit` is claimed.
- README mode selector, compatibility matrix, `.repos` docs, licensing/source docs, and release checklist exist.
- Hardware support is not implied unless hardware gates have actually passed.

Go for hardware bridge non-motion support if:

- Bridge host setup can be reproduced from docs.
- ECN `baxter_bridge` runs against the target robot.
- Restricted allowlist is used.
- `/robot/state`, `/robot/joint_states`, required services, gripper/camera checks where claimed, and both hardware FJT action names are visible.
- At least one state and one joint-state message are received, not just listed.
- No launch enables, resets, stops, or moves the robot automatically.

Go for supervised hardware motion support if:

- Hardware bridge non-motion gate passed.
- Hardware safety gate passed.
- Action shims validate exact joint names and reject unsafe `/robot/state`.
- Speed ratio and command timeout are explicitly set.
- One tiny low-speed trajectory passes for each advertised arm.
- Feedback, result, and cancel/hold behavior are verified.
- Physical e-stop and workspace checklist are part of the documented procedure.

No-go conditions:

- Any default import or copied source comes from an unlicensed repo.
- README or docs imply official Baxter vendor support or native ROS 2 firmware migration.
- Beginner docs normalize raw `ros2 topic pub /robot/set_super_enable`, `/robot/set_super_reset`, or `/robot/set_super_stop`.
- Default CI requires real hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams.
- Hardware motion is advertised after action availability only, without a supervised tiny trajectory and cancel/hold gate.
- Legacy arm joint names are missing or inconsistent and no explicit compatibility decision has been made.

## Decisions

1. **Proceed with `baxter_ros2_jazzy` as a hybrid Jazzy workspace.** The project should be a teaching/distribution stack with sim, MoveIt 2, and bridge-host hardware operation.
2. **Adopt ECN `baxter_common_ros2` by default.** Initial pin: `678bfabea8c895b4134951a6c076217a90b9e0e6`.
3. **Use Gazebo Harmonic as the default simulator.** Standard `ros_gz`, `gz_ros2_control`, and `ros2_control` controllers are the supported sim baseline.
4. **Use ECN bridge-host hardware architecture.** Real Baxter remains ROS 1; no native firmware migration is planned.
5. **Use ROS 2 action shims for hardware motion.** Hardware action names are `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
6. **Keep sim and hardware controller/action names explicit.** Sim uses `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`; hardware uses `/robot/limb/{side}` action names.
7. **Regenerate MoveIt 2 config locally.** Do not copy unlicensed community MoveIt configs or port MoveIt 1 launch/plugin files.
8. **Keep the local package graph small.** First-release local packages are `baxter_bringup`, `baxter_gz_sim`, `baxter_moveit_config`, `baxter_hardware_bridge`, and `baxter_examples`; `baxter_sim_compat` is optional.
9. **Do not create `baxter_smoke_tests` by default.** Fold smoke checks into existing packages until size justifies a split.
10. **Keep Zenoh experimental.** `baxter-zenoh` and `BaxterSDK` remain fallback/reference paths, not default support.
11. **Separate hardware bridge and hardware motion claims.** Hardware bridge non-motion may release before supervised hardware motion.
12. **Keep default CI hardware-free.** No default CI dependency on ROS 1, real robot, Zenoh, bridge-host networking, or cameras.
13. **Use source `.repos` distribution first.** Rosdistro/bloom is later, likely message/description packages first.
14. **Make documentation a release gate.** README mode selector, hardware safety docs, compatibility matrix, `.repos`/license docs, release checklist, and maintainer handoff are required.

## Open Questions

- Target Baxter ROS 1 distro, firmware, and graph.
- ECN `baxter_bridge` installability on the selected bridge host.
- University DDS/multicast/firewall policy and whether hardware users must SSH into the bridge host.
- Zenoh and Docker host-networking acceptance.
- Physical gripper and camera inventory.
- ECN `baxter_description` legacy joint/link names.
- `baxter_legacy`, `BaxterMotionPlanning`, and other unlicensed repo status.
- Headless Gazebo Harmonic CI stability.
- MoveIt hardware action-name compatibility with `/robot/limb/{side}` names.
- Course need for direct `JointCommand` in simulation.
- Maintainer ownership after graduation.
- Docs hosting target.
- Future repository license.

## Artifacts

- Completed final synthesis blueprint: `logs/S11_final_synthesis.log.md`
- Updated S11 status in `MASTER_PLAN.md`
- Planning sequence S01-S11 is complete.
- No next-agent prompt is required after S11.
