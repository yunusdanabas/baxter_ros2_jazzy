# Baxter ROS 2 Jazzy Implementation — Master Plan

## Overview

Implementation workspace for the future `baxter_ros2_jazzy` stack. This plan starts from the completed planning blueprint at `plan/logs/S11_final_synthesis.log.md`.

Goal: build the smallest useful ROS 2 Jazzy workspace first: core Baxter model/messages, then Gazebo Harmonic simulation, then MoveIt 2 simulation, then real-hardware bridge checks, then supervised hardware motion only if all gates pass.

**Scope boundary:** keep implementation step-by-step. Do not touch real hardware before the hardware bridge smoke gates. Do not add unlicensed repos to default `.repos`. Do not attempt native ROS 2 firmware migration.

## Workflow

Every step runs under the **Baton** workflow: one agent per step, strictly in order. A step is done only when its gate has passed with evidence, its log exists in `logs/`, its status line here is updated, and a self-contained prompt for the next step has been appended to `PROMPTS.md`. Rules and file duties: `AGENTS.md`. Reusable template: `WORKFLOW.md`.

---

## Steps

### I00: Workspace Skeleton

- **Status:** `completed`
- **Type:** Setup
- **Description:** Create the implementation workspace shell: `src/`, `repos/`, `docs/`, `logs/`, `.devcontainer/`, README, `.gitignore`, `.env.example`, default `.repos`, and this master plan.
- **Log:** `logs/I00_workspace_prepared.log.md`

### I01: Import Core Dependency

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Import `CentraleNantesRobotics/baxter_common_ros2` using `repos/baxter_core.repos`, pinned to `678bfabea8c895b4134951a6c076217a90b9e0e6`. Build only the 4 non-bridge packages: `baxter_core_msgs`, `baxter_description`, `baxter_maintenance_msgs`, `rethink_ee_description`. **Skip `baxter_bridge`** — it requires ROS 1 `.so` libraries (`roscpp`, `rosconsole`, `rostime`, `xmlrpcpp`) that are not available on Ubuntu 24.04 Noble. Bridge build belongs in I10 on the bridge host.
- **Gate:** `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` succeeds for the 4 core packages.
- **Log:** `logs/I01_import_core_dependency.log.md`

### I02: Core Model Validation

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Verify the adopted `baxter_description` and `rethink_ee_description`: mesh paths resolve, Xacro loads, and legacy arm joint names exist: `left_s0`...`left_w2` and `right_s0`...`right_w2`.
- **Gate:** model can be loaded by ROS 2 tooling and legacy arm joint names are confirmed.
- **Log:** `logs/I02_core_model_validation.log.md`

### I03: Minimal Bringup Package

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Create the smallest `baxter_bringup` package needed for model launch and shared launch arguments. Avoid broader launch scaffolding until sim/MoveIt need it.
- **Gate:** `ros2 launch baxter_bringup baxter_description.launch.py` publishes a usable `robot_description` and TF from `robot_state_publisher`.
- **Log:** `logs/I03_minimal_bringup.log.md`

### I04: Gazebo Harmonic Sim Skeleton

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Create `baxter_gz_sim` with:
  - Use built-in `empty.sdf` world (no custom SDF needed initially)
  - Launch via `ros_gz_sim`'s `gz_sim.launch.py` with `gz_args` for headless (`-r -s empty.sdf`) or GUI (`-r empty.sdf`)
  - Spawn Baxter via `ros_gz_sim create` node reading `robot_description` topic
  - Accept camera-less headless mode for CI (cameras need rendering/Xvfb)
  - Use `gz_*` prefixes everywhere (not `ign_*` — deprecated in Jazzy)
- **Gate:** `ros2 launch baxter_gz_sim sim.launch.py headless:=true` starts Gazebo and spawns Baxter without missing meshes or Classic plugin errors.
- **Log:** `logs/I04_gazebo_sim_skeleton.log.md`

### I05: ros2_control Arm Controllers

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Add `gz_ros2_control` with:
  - URDF overlay: `<ros2_control>` block with `gz_ros2_control/GazeboSimSystem` hardware plugin
  - Position command + position/velocity state interfaces for all 14 arm joints
  - Controller YAML with `controller_manager` section and per-controller configs
  - Explicit `spawner` calls with `OnProcessExit` event handler sequencing:
    1. `joint_state_broadcaster` (after entity spawn)
    2. `left_arm_controller` (after broadcaster active)
    3. `right_arm_controller` (after broadcaster active)
  - Grippers: deferred to I13 (optional); not required for the I05 gate
  - Gazebo plugin: `libgz_ros2_control-system.so` / `gz_ros2_control::GazeboSimROS2ControlPlugin`
- **Gate:** `ros2 control list_controllers` shows the broadcaster and both arm controllers active; `/joint_states` includes all 14 arm joints.
- **Log:** `logs/I05_ros2_control_arm_controllers.log.md`

### I06: Tiny Sim Trajectory Example

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Create the first `baxter_examples` command: `sim_tiny_trajectory`, sending a tiny `FollowJointTrajectory` goal to one arm controller.
- **Gate:** tiny trajectory succeeds for `left_arm_controller` and `right_arm_controller` in sim.
- **Log:** `logs/I06_tiny_sim_trajectory.log.md`

### I07: MoveIt 2 Sim Profile

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Regenerate `baxter_moveit_config` using MoveIt Setup Assistant (`ros2 launch moveit_setup_assistant setup_assistant.launch.py`) or manual creation:
  - SRDF: same format as MoveIt 1 (groups, named states, end effectors, collision matrix)
  - KDL: `kdl_kinematics_plugin/KDLKinematicsPlugin` per arm
  - OMPL: **new Jazzy format** with `planning_plugins`/`request_adapters`/`response_adapters` (not old pipeline format)
  - Controller YAML: `MoveItSimpleControllerManager` with `controller_names` list, `type: FollowJointTrajectory`, `action_ns: follow_joint_trajectory`
  - Separate sim/hardware controller YAML files
  - Use `MoveItConfigsBuilder` from `moveit_configs_utils` for launch files
- **Gate:** MoveIt loads `left_arm`, `right_arm`, `both_arms`, neutral states, and fixed `world_joint`; one-arm sim planning and tiny execution pass.
- **Log:** `logs/I07_moveit2_sim_profile.log.md`

### I08: Devcontainer And Default CI

- **Status:** `completed`
- **Type:** Tooling
- **Description:** Add the default devcontainer and first CI workflow for build, lint/import checks, model load, and MoveIt fake/model checks. Keep hardware and Zenoh out of default CI.
- **Gate:** clean devcontainer build path and CI-equivalent local commands pass without hardware.
- **Log:** `logs/I08_devcontainer_ci.log.md`

### I09: Documentation Baseline

- **Status:** `completed`
- **Type:** Documentation
- **Description:** Fill README mode selector and minimum docs: getting started sim, simulation, MoveIt guide, package map, repos/pins, licensing/sources, compatibility matrix, and CI/release checklist.
- **Gate:** a new user can follow the documented sim path through `sim_tiny_trajectory`.
- **Log:** `logs/I09_docs_baseline.log.md`

### I10: Hardware Bridge Non-Motion

- **Status:** `blocked`
- **Type:** Hardware
- **Blocked By:** physical Baxter access, bridge host choice, university network policy.
- **Description:** Add `baxter_hardware_bridge` only after bridge-host setup is known. Start with non-motion checks: `/robot/state`, `/robot/joint_states`, IK services, camera services, gripper state/properties if installed, and action server visibility.
- **Gate:** hardware bridge non-motion gate passes on the target robot without enabling or moving.
- **Log:** `logs/I10_hardware_bridge_non_motion.log.md`

### I10-prep: Hardware Action Shim Dry-Run Prep

- **Status:** `completed`
- **Type:** Implementation (hardware-free)
- **Description:** Created `baxter_hardware_bridge` package with `FollowJointTrajectory` action shims, safety state checker, mock robot, and dry-run self-test. All safety logic (state validation, joint name validation, hold-on-cancel) is implemented and dry-run tested without a real robot. This unblocks I11 implementation work — when the bridge host is ready, only the hardware-specific integration and I10 non-motion gate remain.
- **Gate:** `ros2 run baxter_hardware_bridge dry_run_test` passes: safe-state goal accepted+succeeded, bad joints rejected, unsafe state rejected.
- **Log:** `logs/I10_prep_hardware_shim_dry_run.log.md`

### I11: Hardware Action Shims And Safety Tools

- **Status:** `blocked`
- **Type:** Hardware
- **Blocked By:** I10 hardware bridge non-motion gate.
- **Description:** Validate the pre-built `FollowJointTrajectory` action shims against a real robot via `baxter_bridge`. The shim code is already implemented and dry-run tested (I10-prep); this step runs the I11 gate on hardware: reject unsafe `/robot/state`, validate exact joint names, set speed ratio/timeouts, and cancel by holding position.
- **Gate:** action shims reject unsafe `/robot/state`, validate exact joint names, set speed ratio/timeouts, and cancel by holding position — on the real robot, not just mock.
- **Log:** `logs/I11_hardware_action_shims.log.md`

### I12: Supervised Hardware Motion

- **Status:** `blocked`
- **Type:** Hardware
- **Blocked By:** I11 safety/action-shim gate and supervised robot access.
- **Description:** Run one tiny low-speed trajectory per advertised arm under physical supervision. Do not claim hardware motion before this passes.
- **Gate:** tiny trajectory, feedback, result, and cancel/hold behavior pass for each advertised arm.
- **Log:** `logs/I12_supervised_hardware_motion.log.md`

### I13: Optional Compatibility And Fallbacks

- **Status:** `deferred`
- **Type:** Optional
- **Description:** Add only if needed: `baxter_sim_compat`, direct safe position-only sim `JointCommand`, gripper/camera examples, hardware IK wrapper, or `experimental_zenoh` fallback.
- **Gate:** each optional feature gets its own smoke test and support label.
- **Log:** `logs/I13_optional_compatibility_fallbacks.log.md`

### I14: Release Hardening

- **Status:** `completed`
- **Type:** Release
- **Description:** Prepare the public sim-first release per blueprint Phase 9 (`plan/logs/S11_final_synthesis.log.md` §12, §15): decide LICENSE, add CONTRIBUTING/SUPPORT/SECURITY, issue templates (sim bug, hardware bridge bug, docs, safety concern, pin update, feature request), PR template, CHANGELOG, release notes with per-profile support labels, maintainer handoff doc, and pin-update policy. Claim hardware support only for gates that actually passed.
- **Gate:** `docs/ci_release_checklist.md` passes for the sim-first release scope; no S11 §15 no-go condition is violated (no unlicensed default imports, no implied vendor support, no unearned hardware claims).
- **Log:** `logs/I14_release_hardening.log.md`

---

## Dependencies Between Steps

```text
I00 -> I01 -> I02 -> I03 -> I04 -> I05 -> I06 -> I07 -> I08 -> I09 -> I14
                                   \
                                    -> I10-prep (completed, hardware-free)
                                    -> I10 -> I11 -> I12

I13 is deferred and depends on a concrete course, hardware, or transport need.
I14 covers the sim-first release after I09; hardware claims in I14 additionally require I12.
```

## Rules

- Default external dependency is only `CentraleNantesRobotics/baxter_common_ros2` at the pinned SHA.
- Keep hardware bridge support separate from hardware motion support.
- Keep default CI hardware-free.
- Do not add unlicensed repos to default `.repos`.
- Do not teach raw safety-topic publishing in beginner docs.
- Add the smallest working package only when a step needs it.
- `baxter_bridge` is bridge-host-only — skip from default sim builds (`--packages-skip baxter_bridge`).
- Use `forward_command_controller` for grippers, not deprecated `GripperActionController`.
- Accept camera-less headless Gazebo for CI; cameras need rendering/Xvfb.

---

## Research Reference

See `RESEARCH_FINDINGS.md` for exact apt packages, YAML format examples, launch patterns, and critical implementation details discovered during pre-implementation research.
