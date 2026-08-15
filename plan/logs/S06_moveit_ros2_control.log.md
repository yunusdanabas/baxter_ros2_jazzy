---
step: S06
title: "MoveIt 2 and ros2_control Integration"
agent_date: 2026-06-17
status: completed
previous_steps: [S01, S02, S03, S04, S05]
---

# S06: MoveIt 2 and ros2_control Integration

## Task

Designed the MoveIt 2 and `ros2_control` integration architecture for Baxter on ROS 2 Jazzy. This was a planning step only. No ROS 2 code, launch files, controller YAML, or MoveIt configuration files were implemented.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `logs/S04_bridge_architecture.log.md`
- `logs/S05_simulation_architecture.log.md`
- `MASTER_PLAN.md`

Read-only Noetic references inspected for exact MoveIt/controller details:

- `baxter_noetic_ref/baxter_moveit_config/config/baxter.srdf`
- `baxter_noetic_ref/baxter_moveit_config/config/baxter.srdf.xacro`
- `baxter_noetic_ref/baxter_moveit_config/config/baxter_base.srdf.xacro`
- `baxter_noetic_ref/baxter_moveit_config/config/default_gripper.srdf.xacro`
- `baxter_noetic_ref/baxter_moveit_config/config/rethink_electric_gripper.srdf.xacro`
- `baxter_noetic_ref/baxter_moveit_config/config/kinematics.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/joint_limits.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/baxter_controllers.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/simple_moveit_controllers.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/ros_controllers.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/fake_controllers.yaml`
- `baxter_noetic_ref/baxter_moveit_config/config/ompl_planning.yaml`

## Findings

### Executive Summary

The first-release MoveIt 2 path should be **regenerated from the selected ROS 2 Baxter description**, not copied from any community MoveIt package and not line-by-line ported from MoveIt 1. The Noetic config is useful as a semantic checklist, but the Jazzy package should be produced with the MoveIt 2 Setup Assistant or an equivalent generated baseline using the licensed ROS 2 description from `CentraleNantesRobotics/baxter_common_ros2` plus local description fixes if needed.

MoveIt should see two explicit execution profiles:

| Profile | Execution Backend | MoveIt Controller Actions | Default Scope |
|---|---|---|---|
| `sim` | Gazebo Harmonic + `gz_ros2_control` + active `joint_trajectory_controller` instances | `/left_arm_controller/follow_joint_trajectory`, `/right_arm_controller/follow_joint_trajectory` | Supported first-release demo path. |
| `hardware` | ECN bridge host + ROS 2 `FollowJointTrajectory` action shims over Baxter `JointCommand` topics | `/robot/limb/left/follow_joint_trajectory`, `/robot/limb/right/follow_joint_trajectory` | Supported only after bridge/action-shim smoke tests pass. |

Use **separate MoveIt controller YAML files** for sim and hardware. Do not hide the hardware/sim difference behind clever remap layers unless a later implementation proves MoveIt 2 cannot address the legacy-style hardware action names. This keeps S07/S08 docs and launch profiles honest.

Do **not** create a native `ros2_control` hardware interface for the real Baxter in first release. For hardware, the action shims are the controller boundary. A fake ros2_control controller manager for bridged hardware would add maintenance cost and safety ambiguity without improving student workflows.

### MoveIt 2 Config Source Strategy

| Option | Decision | Reason |
|---|---|---|
| Regenerate fresh MoveIt 2 config from the chosen ROS 2 URDF/Xacro | **Use this** | Avoids unlicensed community config copying, avoids stale MoveIt 1 plugin/launch assumptions, and catches real link/joint names from the final ROS 2 description. |
| Adapt `angysof16/BaxterMotionPlanning` by hand | **Reference only** | Best modern Jazzy/Harmonic/MoveIt 2 reference, but S02 found no detected license and S05 found renamed joints should not become canonical by accident. |
| Port local Noetic `baxter_moveit_config` line by line | **Do not do this** | MoveIt 1 launch/plugin layout, warehouse, sensor managers, and controller configs are obsolete. Preserve semantics only. |
| Use old `bornaparo/baxter_moveit_config` | **Skip direct reuse** | S02 found it stale, partial, low-adoption, and unlicensed. |

The future package should still be named `baxter_moveit_config` for discoverability and continuity, but its contents should be a new MoveIt 2 package.

Recommended future config file roles:

| Future File | Purpose |
|---|---|
| `baxter_moveit_config/config/baxter.srdf` or generated `.srdf.xacro` | Semantic groups, end effectors, named states, virtual joint, collision matrix. |
| `baxter_moveit_config/config/kinematics.yaml` | KDL solver settings for `left_arm` and `right_arm`. |
| `baxter_moveit_config/config/joint_limits.yaml` | Conservative MoveIt velocity/acceleration limits, starting from Noetic values and final URDF limits. |
| `baxter_moveit_config/config/ompl_planning.yaml` | OMPL-only first-release planning pipeline, defaulting to RRTConnect for arms. |
| `baxter_moveit_config/config/moveit_controllers_sim.yaml` | MoveIt Simple Controller Manager entries for sim controllers. |
| `baxter_moveit_config/config/moveit_controllers_hardware.yaml` | MoveIt Simple Controller Manager entries for hardware action shims. |
| `baxter_moveit_config/config/moveit_controllers_fake.yaml` | Optional RViz-only fake execution profile for docs and CI if Gazebo is unavailable. |
| `baxter_moveit_config/config/pilz_cartesian_limits.yaml` or `cartesian_limits.yaml` | Optional only if Pilz/cartesian planning is enabled later. |

Do not carry CHOMP, STOMP, warehouse/mongo, Kinect/Xtion sensor manager, or old MoveIt 1 launch files into first release.

### SRDF Groups And Semantic Model

Preserve these Noetic group concepts from `baxter.srdf`:

| SRDF Item | First-Release Plan | Notes |
|---|---|---|
| `left_arm` | Include | 7-DOF chain from `torso` to final left tool/tip link. Joint names must remain `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2` if the ROS 2 description permits. |
| `right_arm` | Include | 7-DOF chain from `torso` to final right tool/tip link. Joint names must remain `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2` if possible. |
| `both_arms` | Include, but mark execution limited | Useful for collision-aware planning and future bimanual work. First-release smoke tests should not require synchronized dual-arm execution. |
| `left_hand` | Include only if left electric gripper geometry/joints are present | Use as end-effector collision geometry and optional gripper motion group, not full grasp planning. |
| `right_hand` | Include only if right electric gripper geometry/joints are present | Same as `left_hand`. |
| `left_hand_eef` | Include when `left_hand` exists | Parent group `left_arm`; parent link should match the final left tip link from the chosen description, likely `left_gripper`. |
| `right_hand_eef` | Include when `right_hand` exists | Parent group `right_arm`; parent link should match the final right tip link, likely `right_gripper`. |
| `world_joint` | Include as fixed virtual joint | Parent frame `world`, child link `base`. Baxter is pedestal-mounted; a floating virtual joint is not a first-release need. |

Named states to preserve:

| State | Group | Joint Values From Noetic Reference |
|---|---|---|
| `left_neutral` | `left_arm` | `left_s0=0`, `left_s1=-0.55`, `left_e0=0`, `left_e1=0.75`, `left_w0=0`, `left_w1=1.26`, `left_w2=0`. |
| `right_neutral` | `right_arm` | `right_s0=0`, `right_s1=-0.55`, `right_e0=0`, `right_e1=0.75`, `right_w0=0`, `right_w1=1.26`, `right_w2=0`. |

Optional named states after hardware validation:

| State | Reason To Defer |
|---|---|
| `left_tucked`, `right_tucked`, `both_tucked` | Tuck/untuck on real hardware has collision-avoidance and safety semantics outside MoveIt. Add only after the ROS 2 tuck tool is designed. |
| `open`, `closed` for grippers | Useful if electric grippers are definitely modeled; not required for first arm-planning smoke tests. |

Passive and mimic joint assumptions:

- Do not mark Baxter arm joints passive.
- Do not manually carry the Noetic `passive_joint name="world_joint"` unless MoveIt 2 generation produces an equivalent valid entry. The virtual joint itself is enough for first release.
- Keep gripper mimic behavior in URDF/Xacro if the selected `rethink_ee_description` models opposing fingers with mimic joints.
- If gripper mimic joints are not controllable, expose only the actuated finger joint to controllers and let URDF mimic propagate the other finger.
- Head pan is not a MoveIt planning group in first release; it remains in the robot model and TF tree.

Collision matrix assumptions:

- Generate the allowed collision matrix with MoveIt 2 Setup Assistant using the final ROS 2 URDF/SRDF, then compare conceptually against Noetic's adjacent/never collision disables.
- Keep adjacent-link and impossible self-collision disables for the torso, head, arms, wrist, hands, sensors, pedestal, and gripper base/fingers.
- Do not blanket-disable left-arm vs right-arm collisions; `both_arms` planning only helps if inter-arm collision checking remains meaningful.
- Do not over-disable pedestal collisions for links that can reach the pedestal. The Noetic matrix has many `Default`/`Never` entries around the pedestal; validate with sampled self-collision and RViz before release.
- Treat gripper finger/object contact tuning as out of scope. First release only needs sane self-collision behavior for planning visualization and simple open/close.

### Kinematics And Planning Plugins

Default kinematics plugin:

| Group | Plugin | Initial Settings | Reason |
|---|---|---|---|
| `left_arm` | `kdl_kinematics_plugin/KDLKinematicsPlugin` | Timeout around `0.05` seconds, attempts `3`, search resolution `0.005` to `0.01` | KDL is standard, available with MoveIt 2, and avoids adding a dependency before proof it is needed. |
| `right_arm` | `kdl_kinematics_plugin/KDLKinematicsPlugin` | Same as `left_arm` | Same reason. |

Notes:

- The Noetic config used KDL with an extremely short `0.005` second timeout. Use a less brittle initial value in Jazzy, then tune only if smoke tests are slow.
- Do not configure a solver for `both_arms` initially. Plan both arms in joint space or leave dual-arm IK unsupported until bimanual demos are required.
- Do not add IKFast in first release. Baxter's 7-DOF arms make IKFast generation/maintenance more work than it is worth for a planning blueprint.
- Do not add TRAC-IK by default. Evaluate `trac_ik_kinematics_plugin` only if KDL fails practical one-arm planning/pose-goal smoke tests.
- Hardware Baxter's `ExternalTools/{side}/PositionKinematicsNode/IKService` remains a bridge/API compatibility item from S04, not MoveIt's default IK backend.

Planning pipeline:

- First release should use OMPL only.
- Default planner should be `RRTConnect` for `left_arm` and `right_arm`, matching the Noetic intent.
- `both_arms` may use OMPL/RRTConnect for planning experiments but should not be part of acceptance tests.
- CHOMP, STOMP, Pilz, and Servo should be deferred unless a course has a concrete need.

MoveIt Servo:

- Out of first-release scope.
- Add only after bridge latency, command ownership, collision checking, and hardware stop behavior are measured.
- Servo on real hardware must never bypass S04's enable/state checks and action-shim safety behavior.

Custom IK services:

- Do not recreate the old `baxter_sim_kinematics` service for sim first release.
- Old IK examples should be rewritten to use MoveIt 2 `compute_ik` or `MoveGroupInterface` in sim.
- A ROS 2 wrapper for hardware `SolvePositionIK` can remain a later compatibility feature for labs that teach the original Baxter SDK API.

### MoveIt Controller Integration: Simulation

Simulation controller baseline from S05:

| Controller | Type | Action Namespace | Joints |
|---|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | none | All simulated joints. |
| `left_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `/left_arm_controller/follow_joint_trajectory` | `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2`. |
| `right_arm_controller` | `joint_trajectory_controller/JointTrajectoryController` | `/right_arm_controller/follow_joint_trajectory` | `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`. |
| `head_controller` | `joint_trajectory_controller/JointTrajectoryController` | `/head_controller/follow_joint_trajectory` | `head_pan`; optional and not in MoveIt first release. |
| `left_gripper_controller` | `position_controllers/GripperActionController` | `/left_gripper_controller/gripper_cmd` or controller default | Left electric gripper actuated joint; optional. |
| `right_gripper_controller` | `position_controllers/GripperActionController` | `/right_gripper_controller/gripper_cmd` or controller default | Right electric gripper actuated joint; optional. |

MoveIt sim controller config should include only the two arm controllers by default:

| MoveIt Controller Entry | Action | Default | Joints |
|---|---|---|---|
| `left_arm_controller` | `/left_arm_controller/follow_joint_trajectory` | true | Left 7 arm joints. |
| `right_arm_controller` | `/right_arm_controller/follow_joint_trajectory` | true | Right 7 arm joints. |

Do not define `both_arms_controller` unless the sim actually spawns a combined 14-joint trajectory controller. Splitting `both_arms` execution across two independent JTCs can be explored later, but it should not be the first-release acceptance path.

Gripper execution in MoveIt sim:

- Include gripper geometry in the SRDF when modeled.
- Do not require gripper controllers for arm planning demos.
- If included, use the gripper controller action directly from examples or simple MoveIt gripper group commands; do not claim full object grasping.

### MoveIt Controller Integration: Hardware

Hardware execution path from S04:

```text
MoveIt 2 -> ROS 2 FollowJointTrajectory action shim -> /robot/limb/{side}/joint_command -> ECN baxter_bridge -> Baxter ROS 1 robot
```

Hardware action shims should expose these canonical action names:

| Hardware Shim | Action Namespace | Joints | Output Topic |
|---|---|---|---|
| Left arm trajectory shim | `/robot/limb/left/follow_joint_trajectory` | `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2` | `/robot/limb/left/joint_command`. |
| Right arm trajectory shim | `/robot/limb/right/follow_joint_trajectory` | `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2` | `/robot/limb/right/joint_command`. |

MoveIt hardware controller config should target those legacy-compatible action names. The closest MoveIt controller entries are:

| MoveIt Controller Entry | Action | Default | Joints |
|---|---|---|---|
| `/robot/limb/left` | `/robot/limb/left/follow_joint_trajectory` | true | Left 7 arm joints. |
| `/robot/limb/right` | `/robot/limb/right/follow_joint_trajectory` | true | Right 7 arm joints. |

Implementation note for later: if MoveIt 2's simple controller manager rejects controller names with leading slashes or legacy-style paths, keep the canonical hardware actions above and add shim aliases:

| Optional Alias | Target |
|---|---|
| `/left_arm_controller/follow_joint_trajectory` | Forwards to or is served by the same left hardware shim. |
| `/right_arm_controller/follow_joint_trajectory` | Forwards to or is served by the same right hardware shim. |

Do not make aliases the default architecture. Separate sim/hardware controller YAML files are clearer, and the legacy `/robot/limb/{side}` names preserve continuity with Noetic and S04.

Hardware controller/action constraints:

- No hardware MoveIt execution before `/robot/state` reports ready, enabled, not stopped, not errored, and not e-stopped.
- Action shims must validate exact joint names and reject partial/renamed joint lists.
- Action shims should publish low speed ratios and command timeouts as S04 described.
- Cancel should hold current position, not call `/robot/set_super_stop` for routine action cancellation.
- Hardware `JointCommand` topics stay available for advanced labs, but MoveIt should never publish them directly.

### One Controller Config Or Separate YAML Files

Use separate files:

| File | Used By | Why |
|---|---|---|
| `moveit_controllers_sim.yaml` | `moveit_sim.launch.py` / `sim_moveit.launch.py` | Matches real ros2_control controller names and lets smoke tests use `ros2 control list_controllers`. |
| `moveit_controllers_hardware.yaml` | `moveit_hardware.launch.py` | Matches hardware action-shim namespaces and keeps bridge-specific safety assumptions visible. |
| `moveit_controllers_fake.yaml` | Optional RViz-only launch | Enables docs/CI model loading without Gazebo or hardware. |

Avoid one highly parameterized controller YAML with substitutions. It saves one file but makes launch behavior harder to audit, especially for hardware safety.

### ros2_control Controller Manager And Startup Ordering

Simulation startup order should be represented explicitly in S07/S08 launch plans:

1. Generate/load `robot_description` from the sim overlay Xacro.
2. Start `robot_state_publisher` with `use_sim_time:=true`.
3. Start Gazebo Harmonic through `ros_gz_sim` and spawn the Baxter entity.
4. Wait for `/controller_manager` from `gz_ros2_control` to exist.
5. Spawn and activate `joint_state_broadcaster` first.
6. Spawn and activate `left_arm_controller` and `right_arm_controller`.
7. Optionally spawn `head_controller`, `left_gripper_controller`, and `right_gripper_controller`.
8. Verify controller state is `active` before starting `move_group` with execution enabled.
9. Start RViz after `move_group` has loaded robot model and controller config.

Planning rule: `move_group` may start before controllers for pure planning demos, but any launch profile named as executable/supported must block or clearly warn until arm controllers are active.

Hardware startup order:

1. Start ECN `baxter_bridge` and confirm hardware allowlist topics/services.
2. Start or confirm `robot_state_publisher` on the bridge host with the same ROS 2 Baxter description used by MoveIt.
3. Remap or relay `/robot/joint_states` to `/joint_states` for MoveIt, with exactly one joint-state source active.
4. Start left/right ROS 2 `FollowJointTrajectory` action shims.
5. Run S04 hardware smoke tests through action availability without sending a motion goal.
6. Start `move_group` with `moveit_controllers_hardware.yaml` only after joint states, TF, `/robot/state`, and action servers are visible.
7. Require explicit user/instructor enable and clear workspace before any execution test.

Do not require a `ros2_control` controller manager on hardware first release. The real Baxter path is not native ros2_control.

### Grippers And Head In First Release

| Feature | MoveIt First-Release Scope | Reason |
|---|---|---|
| Arm planning and execution | **In scope** | Core MoveIt value and smoke-testable in sim/hardware. |
| Electric gripper geometry | **In scope if modeled** | Needed for collision geometry and end-effector continuity. |
| Gripper open/close action | **Optional low fidelity** | Useful for demos, but not required for arm planning. Use `GripperActionController` in sim or ROS 2 shim over `EndEffectorCommand` in hardware. |
| MoveIt grasp pipeline/object grasping | **Deferred** | Requires contact, perception, object modeling, and gripper physics beyond minimum usable MoveIt. |
| Head pan controller | **Outside MoveIt** | Keep in robot model and optional ros2_control controller, but do not include in MoveIt groups for first release. |
| Head action shim | **Optional outside MoveIt** | Useful for old examples, not needed for planning. |

### Dual-Arm Planning And Execution

`both_arms` should exist in SRDF for planning-scene completeness and future bimanual demos, but first-release support should be documented as **limited/experimental**.

Supported first release:

- Plan and execute `left_arm` alone.
- Plan and execute `right_arm` alone.
- Load `both_arms` in RViz and test collision-aware planning manually if desired.

Not first-release acceptance criteria:

- Synchronized dual-arm execution.
- A combined 14-joint `both_arms_controller`.
- Bimanual Cartesian tasks.
- Dual-arm Servo.
- Collision-aware object handoff or grasping.

Add a real `both_arms_controller` only if a course or demo requires synchronized dual-arm trajectories and the sim/hardware action-shim timing is validated.

### Joint States, TF, And Planning Scene

Joint state policy:

| Profile | Source For MoveIt | Compatibility Topic |
|---|---|---|
| Sim | `/joint_states` from `joint_state_broadcaster` | Optional mirror `/robot/joint_states` from S05 compatibility layer. |
| Hardware | Real `/robot/joint_states` bridged from Baxter, remapped/relayed to `/joint_states` for MoveIt | Keep `/robot/joint_states` visible for Baxter SDK compatibility. |

Rules:

- MoveIt should use `/joint_states` in both profiles.
- Do not run a fake `joint_state_publisher` when real sim/hardware joint states are available.
- In hardware, use one remap/relay path from `/robot/joint_states` to `/joint_states`; avoid duplicate publishers that create unstable planning-scene state.
- Validate joint names exactly before loading MoveIt. Reject or fail fast if renamed joints from a community model appear unexpectedly.

TF and robot state publisher:

- Use one `robot_state_publisher` per profile with the same `robot_description` family that MoveIt loads.
- Sim uses `use_sim_time:=true`; hardware uses wall time unless the bridge policy says otherwise.
- Publish or define fixed `world -> base` transform consistent with SRDF `world_joint`.
- Ensure `/tf_static` uses transient-local durability for late RViz/MoveIt subscribers as S04 noted.
- Do not depend on Baxter hardware publishing a complete TF tree; generate TF from the ROS 2 description and bridged joint states.

Planning scene updates:

- First release uses MoveIt's standard planning scene monitor, robot state monitor, and RViz planning scene tools.
- No Kinect/Xtion occupancy map, point cloud sensor manager, or warehouse database in first release.
- Gazebo object spawning and full pick/place scene synchronization are deferred.

### Deferred Scope

Explicitly defer:

- Custom `MoveArm` actions from community demos.
- Native ros2_control hardware interface for the real Baxter.
- Torque, raw-position, effort, and velocity controllers for MoveIt execution.
- MoveIt Servo.
- IKFast generation and hardware IK-service parity for MoveIt.
- Full gripper physics, suction/pneumatic gripper realism, grasp contact tuning, and MoveIt grasp pipeline.
- Old Kinect/Xtion sensor manager configs, occupancy map monitoring, and warehouse/mongo.
- Full object pick-and-place and bimanual manipulation demos.
- Line-by-line migration of MoveIt 1 launch files, CHOMP/STOMP configs, and old fake controller layouts.

### MoveIt / ros2_control Smoke Tests

These smoke tests define when the MoveIt/ros2_control layer is usable enough for S07/S08 to advertise it.

Model and configuration tests:

1. `robot_description` loads from the selected ROS 2 Baxter Xacro without missing meshes.
2. `robot_description_semantic` loads and includes `left_arm`, `right_arm`, `both_arms`, optional `left_hand`, optional `right_hand`, `left_neutral`, `right_neutral`, and fixed `world_joint`.
3. Joint names in URDF, SRDF, MoveIt controller YAML, and controller manager output match exactly for all 14 arm joints.
4. MoveIt RViz starts with no missing kinematics plugin or controller-manager errors.

Simulation execution tests:

1. Launch Gazebo Harmonic headless with Baxter spawned.
2. `ros2 control list_controllers` shows `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller` active.
3. `/joint_states` publishes all 14 arm joints plus optional modeled head/gripper joints.
4. MoveIt plans `left_arm` from current state to `left_neutral` or a tiny safe delta.
5. MoveIt executes a tiny `left_arm` trajectory through `/left_arm_controller/follow_joint_trajectory`.
6. Repeat plan/execute for `right_arm` through `/right_arm_controller/follow_joint_trajectory`.
7. RViz TF tree is coherent from `world`/`base` through both wrist/end-effector frames.

Hardware non-motion tests:

1. ECN bridge is running and `/robot/state`, `/robot/joint_states`, and both action-shim names are visible.
2. `/robot/joint_states` can be remapped/relayed to `/joint_states` without duplicate joint-state sources.
3. `robot_state_publisher` produces TF from bridged joint states and the same description MoveIt uses.
4. MoveIt loads `moveit_controllers_hardware.yaml` and detects `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory` without sending a trajectory.
5. A dry-run/action availability check validates joint names and controller names.

Hardware motion test, only after S04 safety checks:

1. Physical workspace is clear and e-stop reachable.
2. `/robot/state` reports ready/enabled/not stopped/not errored/not e-stopped.
3. Send one tiny, low-speed single-arm trajectory through MoveIt to the action shim.
4. Verify feedback, completion, and cancel/hold behavior.
5. Disable robot or return to neutral according to lab procedure.

## Decisions

1. **Regenerate `baxter_moveit_config` for MoveIt 2.** Use the final ROS 2 Baxter description, not copied community configs and not a line-by-line MoveIt 1 port.
2. **Adopt separate execution profiles.** Use `moveit_controllers_sim.yaml` for ros2_control sim controllers and `moveit_controllers_hardware.yaml` for hardware action shims.
3. **Canonical sim action names:** `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
4. **Canonical hardware action names:** `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
5. **No default alias unification.** Do not make sim and hardware look identical to MoveIt unless later implementation proves MoveIt 2 cannot use the hardware names directly.
6. **No native hardware ros2_control first release.** Hardware action shims are the controller boundary; native ros2_control for real Baxter is deferred.
7. **Preserve Baxter legacy arm joint names.** `left_s0`...`left_w2` and `right_s0`...`right_w2` are required unless the final description makes this impossible and the decision is revisited.
8. **Use KDL first.** Configure KDL for `left_arm` and `right_arm`; defer TRAC-IK/IKFast unless smoke tests fail.
9. **Include `both_arms` but mark it experimental.** First-release acceptance is one-arm planning and execution only.
10. **Keep grippers low fidelity.** Include gripper geometry/end-effectors if modeled; optional open/close actions are fine; full grasping is deferred.
11. **Keep head outside MoveIt.** Model it and optionally control it through ros2_control/examples, but do not include it in first-release MoveIt groups.
12. **MoveIt uses `/joint_states`.** Sim publishes it directly; hardware remaps/relays `/robot/joint_states` to it with one authoritative source.
13. **Use fixed `world_joint`.** Baxter is pedestal-mounted; floating base semantics are not first-release scope.
14. **OMPL only first release.** Default RRTConnect for arms; defer CHOMP/STOMP/Pilz/Servo.

## Open Questions

- Does the adopted ECN ROS 2 `baxter_description` preserve all legacy joint and link names needed by Noetic SRDF concepts, especially `left_s0`...`left_w2`, `right_s0`...`right_w2`, `left_gripper`, and `right_gripper`?
- Which exact grippers are installed on the target Baxter, and should first-release MoveIt ship with electric gripper SRDF groups enabled by default or behind launch arguments?
- Will MoveIt 2's simple controller manager accept controller entries named `/robot/limb/left` and `/robot/limb/right`, or will the hardware shim need optional `/left_arm_controller` and `/right_arm_controller` aliases?
- Should the sim eventually add a real `both_arms_controller`, or is separate one-arm execution enough for target courses?
- Should S07 make Gazebo-based MoveIt execution required in CI, or provide a lighter RViz/fake-controller smoke test if Harmonic is too flaky for the chosen CI environment?
- Does the target lab need old `ExternalTools/{side}/PositionKinematicsNode/IKService` compatibility in ROS 2, or can old IK examples be rewritten to MoveIt 2 APIs?
- What hardware motion threshold is acceptable for first release: action availability only, or one tiny supervised MoveIt execution on a real Baxter?

## Artifacts

- Updated this S06 MoveIt 2 and ros2_control integration log: `logs/S06_moveit_ros2_control.log.md`
- Updated S06 status in `MASTER_PLAN.md`
- Appended S07 handoff prompt to `PROMPTS.md`
- Read-only local source paths inspected:
  - `baxter_noetic_ref/baxter_moveit_config/config/baxter.srdf`
  - `baxter_noetic_ref/baxter_moveit_config/config/baxter.srdf.xacro`
  - `baxter_noetic_ref/baxter_moveit_config/config/baxter_base.srdf.xacro`
  - `baxter_noetic_ref/baxter_moveit_config/config/default_gripper.srdf.xacro`
  - `baxter_noetic_ref/baxter_moveit_config/config/rethink_electric_gripper.srdf.xacro`
  - `baxter_noetic_ref/baxter_moveit_config/config/kinematics.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/joint_limits.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/baxter_controllers.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/simple_moveit_controllers.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/ros_controllers.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/fake_controllers.yaml`
  - `baxter_noetic_ref/baxter_moveit_config/config/ompl_planning.yaml`
- Prior architecture logs used as source decisions:
  - `logs/S04_bridge_architecture.log.md`
  - `logs/S05_simulation_architecture.log.md`
