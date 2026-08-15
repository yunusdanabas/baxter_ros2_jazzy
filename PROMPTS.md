# Implementation Prompts

Use `MASTER_PLAN.md` as the source of truth. Each step should update its log under `logs/` and only mark the step completed after its gate passes.

## I01 Prompt

You are implementing step I01 for `baxter_ros2_jazzy`.

Task:

- Import `CentraleNantesRobotics/baxter_common_ros2` using `repos/baxter_core.repos`.
- Run rosdep for imported source packages.
- Build the core dependency with `colcon build --symlink-install`.
- Do not implement local ROS 2 packages yet.
- Record results in `logs/I01_import_core_dependency.log.md`.
- Update `MASTER_PLAN.md` I01 status to `completed` only if the build gate passes.

Gate:

- `colcon build --symlink-install` succeeds for imported core packages.

Reference:

- Planning blueprint: `plan/logs/S11_final_synthesis.log.md`

---

## I01 Prompt (v2 — supersedes the I01 prompt above)

You are agent I01 for the `baxter_ros2_jazzy` implementation project.

### Task

Import the pinned core dependency and build the four non-bridge packages.

- Import `CentraleNantesRobotics/baxter_common_ros2` via
  `vcs import src < repos/baxter_core.repos` (pinned to
  `678bfabea8c895b4134951a6c076217a90b9e0e6`).
- Run `rosdep install --from-paths src --ignore-src -r -y` for the imported sources.
- Build only the 4 core packages: `baxter_core_msgs`, `baxter_description`,
  `baxter_maintenance_msgs`, `rethink_ee_description`.
- **Skip `baxter_bridge`.** It links ROS 1 `.so` libraries (`roscpp`,
  `rosconsole`, `rostime`, `xmlrpcpp`) that do not exist on Ubuntu 24.04 Noble
  and that rosdep cannot resolve (see `RESEARCH_FINDINGS.md` §1). It is built
  only on the bridge host in step I10.
- Do not create local ROS 2 packages yet — that starts in I03.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` — your step I01
- `logs/I00_workspace_prepared.log.md`
- `RESEARCH_FINDINGS.md` (§1: package inventory, baxter_bridge constraint, joint names)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`

### Gate

`colcon build --symlink-install --packages-skip baxter_bridge` succeeds for the
4 core packages.

### Finish — Baton handoff (required)

1. Verify the gate; record the build command and its result in your log.
2. Write `logs/I01_import_core_dependency.log.md` in the log format from `WORKFLOW.md`
   (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00]`;
   sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I01 status line in `MASTER_PLAN.md` — `completed` only if the gate passed.
4. Append a self-contained prompt for **I02 (Core Model Validation)** to `PROMPTS.md`
   (append-only). It must include: what I02 does (verify mesh paths resolve, Xacro
   loads, legacy arm joint names `left_s0`…`left_w2` / `right_s0`…`right_w2` exist),
   the I02 gate from `MASTER_PLAN.md`, the read-first list, and this same
   four-part finish checklist.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- If the gate fails, keep I01 status not-completed, log the failure evidence and
  blocker, and append a retry prompt for I01 instead of the I02 prompt.

---

## I02 Prompt

You are agent I02 for the `baxter_ros2_jazzy` implementation project.

### Task

Validate the imported core model packages from I01.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Verify `baxter_description` and `rethink_ee_description` mesh paths resolve.
- Verify the Baxter Xacro/URDF loads with ROS 2 tooling.
- Confirm the legacy Baxter arm joint names exist in the generated model:
  `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2`,
  `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`.
- Do not create local ROS 2 packages yet; that starts in I03.
- Do not modify `plan/`. I01 found that the read-only planning archive contains
  duplicate ROS 1 package names, so build commands in this workspace should use
  `--base-paths src` when invoking `colcon` from the repository root.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I02
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (section 1: package inventory, mesh/model context, joint names)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

model can be loaded by ROS 2 tooling and legacy arm joint names are confirmed.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I02_core_model_validation.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I02 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I03 to `PROMPTS.md` (append-only). It must include the I03 task, read-first list, gate, and this four-part finish checklist. If the I02 gate fails, keep I02 not-completed, log the blocker, and append an I02 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No implementation beyond I02 model validation; do not create `baxter_bringup` yet.

---

## I03 Prompt

You are agent I03 for the `baxter_ros2_jazzy` implementation project.

### Task

Create the smallest `baxter_bringup` package needed to launch the validated Baxter model from I02.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Create a local ROS 2 package `baxter_bringup` under `src/`.
- Add only the minimal launch needed for this step: `launch/baxter_description.launch.py`.
- The launch file should expand the installed `baxter_description/urdf/baxter.urdf.xacro` and start `robot_state_publisher` with `robot_description`.
- Include only launch arguments that are useful now for the shared model path, such as `pedestal` and `gazebo`, matching the upstream Xacro arguments. Do not add Gazebo, controller, MoveIt, or hardware launch scaffolding yet.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.

I02 gate evidence: `check_urdf` successfully parsed the generated Baxter model, all 14 legacy arm joints were present, and 61 mesh references across generated/source model files resolved with zero missing meshes.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I03
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (section 1: package inventory, mesh/model context, joint names)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

`ros2 launch baxter_bringup baxter_description.launch.py` publishes a usable `robot_description` and TF from `robot_state_publisher`.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I03_minimal_bringup.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I03 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I04 to `PROMPTS.md` (append-only). It must include the I04 task, read-first list, gate, and this four-part finish checklist. If the I03 gate fails, keep I03 not-completed, log the blocker, and append an I03 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No Gazebo, ros2_control, MoveIt, examples, CI, docs, or hardware implementation beyond the minimal I03 bringup package.

---

## I04 Prompt

You are agent I04 for the `baxter_ros2_jazzy` implementation project.

### Task

Create the smallest `baxter_gz_sim` package needed to start Gazebo Harmonic and spawn the Baxter model from the I03 bringup path.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Create a local ROS 2 package `baxter_gz_sim` under `src/`.
- Use Gazebo Harmonic / `ros_gz` naming everywhere (`gz_*`, not deprecated `ign_*`).
- Add only the minimal launch needed for this step: `launch/sim.launch.py`.
- Use the built-in Gazebo empty world; do not add a custom world file yet.
- Launch Gazebo through `ros_gz_sim`'s `gz_sim.launch.py` with `gz_args`:
  - headless: `-r -s empty.sdf`
  - GUI: `-r empty.sdf`
- Start `robot_state_publisher` with the Baxter model by including or matching the I03 `baxter_bringup` model launch path.
- Spawn Baxter with the `ros_gz_sim create` executable reading the `robot_description` topic.
- Accept camera-less headless mode for this step; cameras need rendering/Xvfb and are not part of I04.
- Do not add ros2_control, controller YAML, MoveIt, examples, CI, docs, hardware, bridge, or compatibility scaffolding yet.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.

I03 gate evidence: `ros2 launch baxter_bringup baxter_description.launch.py` started `robot_state_publisher`, produced a Baxter `robot_description` of length 58862 with required Baxter tokens present, and `/tf_static` published one latched message containing 39 transforms.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I04
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (sections 1 and Gazebo/ros2_control notes as needed)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

`ros2 launch baxter_gz_sim sim.launch.py headless:=true` starts Gazebo and spawns Baxter without missing meshes or Classic plugin errors.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I04_gazebo_sim_skeleton.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I04 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I05 to `PROMPTS.md` (append-only). It must include the I05 task, read-first list, gate, and this four-part finish checklist. If the I04 gate fails, keep I04 not-completed, log the blocker, and append an I04 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No ros2_control, controller YAML, MoveIt, examples, CI, docs, hardware, bridge, or compatibility implementation beyond the minimal I04 Gazebo spawn package.

---

## I05 Prompt

You are agent I05 for the `baxter_ros2_jazzy` implementation project.

### Task

Add the smallest `ros2_control` arm controller support needed for Baxter in Gazebo Harmonic.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Continue using Gazebo Harmonic / `ros_gz` / `gz_ros2_control` naming; do not use deprecated `ign_*` names.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Add only what I05 needs for arm controllers; do not add MoveIt, examples, CI, docs, hardware, bridge, or compatibility scaffolding.
- Build on I04's minimal `baxter_gz_sim` launch package.
- I04 created `src/baxter_gz_sim/launch/sim.launch.py`, which launches Gazebo with built-in `empty.sdf`, includes `baxter_bringup/launch/baxter_description.launch.py`, and spawns Baxter via `ros_gz_sim create -topic /robot_description -name baxter`.
- I04 also guarded `src/baxter_common_ros2/baxter_description/urdf/baxter.urdf.xacro` so the upstream legacy `gazebosim.urdf.xacro` include only loads when `gazebo:=true`. Keep avoiding that old include for default Harmonic sim work; add an explicit I05 overlay or launch-time robot description path for `gz_ros2_control` instead.
- Add a URDF/Xacro overlay or equivalent model path containing:
  - `<ros2_control name="GazeboSimSystem" type="system">`
  - hardware plugin `gz_ros2_control/GazeboSimSystem`
  - position command interfaces and position/velocity state interfaces for all 14 arm joints:
    `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2`,
    `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`.
- Add the Gazebo plugin tag using `filename="libgz_ros2_control-system.so"` and `name="gz_ros2_control::GazeboSimROS2ControlPlugin"`.
- Add the minimal controller YAML with:
  - `controller_manager` and `update_rate`
  - `joint_state_broadcaster`
  - `left_arm_controller`
  - `right_arm_controller`
  - `joint_trajectory_controller/JointTrajectoryController` configs for each 7-joint arm.
- Explicitly spawn controllers with `controller_manager` `spawner` calls sequenced with launch event handlers:
  1. `joint_state_broadcaster` after Baxter entity spawn
  2. `left_arm_controller` after broadcaster activation
  3. `right_arm_controller` after broadcaster activation
- Gripper support is not required for I05. If adding grippers becomes unavoidable later, use `forward_command_controller/ForwardCommandController`, not deprecated `GripperActionController`.

I04 gate evidence: `ros2 launch baxter_gz_sim sim.launch.py headless:=true` started Gazebo, started `robot_state_publisher`, and `ros_gz_sim create` reported `Entity creation successful` from `/robot_description`. No missing mesh errors or Classic Gazebo plugin errors appeared; only a non-blocking mimic-joint physics warning for `l_gripper_r_finger_joint` was printed.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I05
- `logs/I04_gazebo_sim_skeleton.log.md`
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (sections 2, 3, and 6: ros2_control config, Gazebo Harmonic setup, controller spawning order)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

`ros2 control list_controllers` shows the broadcaster and both arm controllers active; `/joint_states` includes all 14 arm joints.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I05_ros2_control_arm_controllers.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I05 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I06 to `PROMPTS.md` (append-only). It must include the I06 task, read-first list, gate, and this four-part finish checklist. If the I05 gate fails, keep I05 not-completed, log the blocker, and append an I05 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No MoveIt, examples, CI, docs, hardware, bridge, or compatibility implementation beyond the minimal I05 Gazebo `ros2_control` arm-controller support.

---

## I06 Prompt

You are agent I06 for the `baxter_ros2_jazzy` implementation project.

### Task

Create the first tiny simulation trajectory example for Baxter's Gazebo Harmonic `ros2_control` arm controllers.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Continue using Gazebo Harmonic / `ros_gz` / `gz_ros2_control` naming; do not use deprecated `ign_*` names.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Add only what I06 needs for a tiny sim trajectory example; do not add MoveIt, CI, docs, hardware, bridge, grippers, or compatibility scaffolding.
- Create the smallest `baxter_examples` package or equivalent local package needed to provide one command: `sim_tiny_trajectory`.
- The command should send a tiny `control_msgs/action/FollowJointTrajectory` goal to the standard ros2_control action servers:
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`
- Use the exact 7-joint lists from I05 for each arm:
  - left: `left_s0`, `left_s1`, `left_e0`, `left_e1`, `left_w0`, `left_w1`, `left_w2`
  - right: `right_s0`, `right_s1`, `right_e0`, `right_e1`, `right_w0`, `right_w1`, `right_w2`
- Keep the motion tiny and simulation-safe: a small offset on one joint per arm and a short duration is enough. No real hardware path is allowed.
- Build on I05's `baxter_gz_sim` launch package. I05 added:
  - `src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro`
  - `src/baxter_gz_sim/config/ros2_controllers.yaml`
  - `src/baxter_gz_sim/launch/sim.launch.py` with sequenced spawners for `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller`.

I05 gate evidence: `ros2 control list_controllers` showed `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller` active, and a `/joint_states` subscriber saw all 14 required arm joints. Known non-blockers: Gazebo gripper mimic warning and controller-manager clock fallback warnings after startup.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I06
- `logs/I05_ros2_control_arm_controllers.log.md`
- `logs/I04_gazebo_sim_skeleton.log.md`
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (sections 2, 3, and 6: controller names, Gazebo Harmonic setup, controller startup notes)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

tiny trajectory succeeds for `left_arm_controller` and `right_arm_controller` in sim.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I06_tiny_sim_trajectory.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04, I05]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I06 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I07 to `PROMPTS.md` (append-only). It must include the I07 task, read-first list, gate, and this four-part finish checklist. If the I06 gate fails, keep I06 not-completed, log the blocker, and append an I06 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No MoveIt, CI, docs, hardware, bridge, gripper, or compatibility implementation beyond the minimal I06 tiny sim trajectory example.

---

## I07 Prompt

You are agent I07 for the `baxter_ros2_jazzy` implementation project.

### Task

Create the MoveIt 2 simulation profile for Baxter's Gazebo Harmonic `ros2_control` stack.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Continue using Gazebo Harmonic / `ros_gz` / `gz_ros2_control` naming; do not use deprecated `ign_*` names.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Add only what I07 needs for a sim MoveIt profile; do not add CI, docs, hardware, bridge, grippers, or compatibility scaffolding beyond the MoveIt config package and minimal launch integration.
- Regenerate or manually create `baxter_moveit_config` using MoveIt Setup Assistant (`ros2 launch moveit_setup_assistant setup_assistant.launch.py`) or equivalent manual creation:
  - SRDF: same format as MoveIt 1 (groups, named states, end effectors, collision matrix)
  - KDL: `kdl_kinematics_plugin/KDLKinematicsPlugin` per arm
  - OMPL: **new Jazzy format** with `planning_plugins` / `request_adapters` / `response_adapters` (not old pipeline format)
  - Controller YAML: `MoveItSimpleControllerManager` with `controller_names` list, `type: FollowJointTrajectory`, `action_ns: follow_joint_trajectory`
  - Separate sim/hardware controller YAML files
  - Use `MoveItConfigsBuilder` from `moveit_configs_utils` for launch files
- Build on I05/I06 sim stack:
  - `src/baxter_gz_sim/launch/sim.launch.py` (includes clock bridge and `use_sim_time`)
  - `src/baxter_gz_sim/config/ros2_controllers.yaml` with `left_arm_controller` and `right_arm_controller`
  - `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py` as reference for controller action names

I06 gate evidence: `ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true` succeeded for both `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory` with sim running. Clock bridge fix confirmed: `/clock` has one publisher and `/joint_states` stamps are non-zero.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I07
- `logs/I06_tiny_sim_trajectory.log.md`
- `logs/I05_ros2_control_arm_controllers.log.md`
- `logs/I04_gazebo_sim_skeleton.log.md`
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (section 4: MoveIt 2 Configuration for Jazzy)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- `WORKFLOW.md` for the log format

### Gate

MoveIt loads `left_arm`, `right_arm`, `both_arms`, neutral states, and fixed `world_joint`; one-arm sim planning and tiny execution pass.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I07_moveit2_sim_profile.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04, I05, I06]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I07 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I08 to `PROMPTS.md` (append-only). It must include the I08 task, read-first list, gate, and this four-part finish checklist. If the I07 gate fails, keep I07 not-completed, log the blocker, and append an I07 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- No CI, docs, hardware, bridge, gripper, or compatibility implementation beyond the minimal I07 MoveIt sim profile.

---

## I08 Prompt

You are agent I08 for the `baxter_ros2_jazzy` implementation project.

### Task

Add the default devcontainer and first hardware-free CI workflow for the sim-first workspace.

- Source the ROS 2 Jazzy environment and this workspace install before checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Build from the repository root with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` because the read-only `plan/` archive contains duplicate ROS 1 package names.
- Keep hardware and Zenoh out of the default devcontainer/CI path.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Add only what I08 needs for the devcontainer and default CI. Do not add docs baseline, hardware bridge tooling, action shims, grippers, compatibility layers, or optional examples.
- Default CI should cover hardware-free checks only: build, basic lint/import checks if already available without adding heavy scaffolding, model load, and MoveIt config/model checks. Full Gazebo+MoveIt execution can remain a manual smoke if teardown remains flaky.
- Preserve the pinned ECN SHA rule: only `CentraleNantesRobotics/baxter_common_ros2` at `678bfabea8c895b4134951a6c076217a90b9e0e6` in default `.repos`; no unlicensed external imports.

I07 gate evidence:

- `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge` completed 8 packages, including `baxter_moveit_config`.
- Static SRDF/config check found groups `left_arm`, `right_arm`, `both_arms`, `left_hand`, `right_hand`, neutral states `left_neutral`/`right_neutral`, and fixed `world_joint` from `world` to `base`.
- `ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=true` brought up Gazebo, active arm controllers, and `move_group`.
- `ros2 control list_controllers` showed `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller` active.
- `/move_action` was available, a left-arm MoveGroup goal planned with OMPL/RRTConnect and `plan_only=false`, returned `moveit_error_code=1`, and the sim `left_arm_controller` log reported `Received new action goal` and `Goal reached, success!`.

Known I07 non-blockers for I08:

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`; I05/I07 only expose arm joints for default sim motion.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensors are in first CI scope.
- `move_group` can segfault during SIGINT teardown after successful execution. Do not make full Gazebo+MoveIt shutdown a hard default CI gate unless I08 handles this explicitly.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I08
- `logs/I07_moveit2_sim_profile.log.md`
- `logs/I06_tiny_sim_trajectory.log.md`
- `logs/I05_ros2_control_arm_controllers.log.md`
- `logs/I04_gazebo_sim_skeleton.log.md`
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md` (sections 5 and 6: exact apt package names and critical implementation notes)
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- Dev-experience plan if needed: `plan/logs/S07_dev_experience_tooling.log.md`
- `WORKFLOW.md` for the log format

### Gate

clean devcontainer build path and CI-equivalent local commands pass without hardware.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I08_devcontainer_ci.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I08 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I09 to `PROMPTS.md` (append-only). It must include the I09 task, read-first list, gate, and this four-part finish checklist. If the I08 gate fails, keep I08 not-completed, log the blocker, and append an I08 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Keep default CI hardware-free.
- Do not add unlicensed repos to default `.repos`.
- `baxter_bridge` is bridge-host-only; skip it from default sim/devcontainer/CI builds.
- No docs baseline, hardware bridge, action shims, gripper implementation, or optional compatibility work beyond the minimal I08 devcontainer/CI deliverable.

---

## I09 Prompt

You are agent I09 for the `baxter_ros2_jazzy` implementation project.

### Task

Add the documentation baseline for the sim-first workspace. This is a documentation step only.

- Fill the README mode selector and minimum docs so a new user can follow the sim path through `sim_tiny_trajectory`.
- Document only the gates and support levels that have actually passed. Do not imply hardware support or supervised hardware motion has passed.
- Keep the default path sim-first and hardware-free.
- Preserve the pinned ECN SHA rule: only `CentraleNantesRobotics/baxter_common_ros2` at `678bfabea8c895b4134951a6c076217a90b9e0e6` in default `.repos`; no unlicensed external imports.
- Use the required build command from the repository root:
  `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
- Source ROS 2 Jazzy and the workspace install before documented checks:
  `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Keep hardware and Zenoh out of the default install/devcontainer/CI path.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Do not add hardware bridge tooling, action shims, grippers, compatibility layers, or optional examples in I09.
- Do not teach raw safety-topic publishing in beginner docs.

Minimum docs to fill:

- `README.md`: first-screen mode selector, current status, default sim install/build, CI/devcontainer note, and support boundary.
- `docs/index.md`: docs landing page and mode selector.
- `docs/getting_started_sim.md`: 15-minute devcontainer/native sim path from clone/import through `sim_tiny_trajectory`.
- `docs/simulation.md`: Gazebo Harmonic launch, headless mode, controllers, `/joint_states`, tiny trajectory smoke.
- `docs/moveit_guide.md`: MoveIt sim scope, groups, neutral states, action names, and `sim_moveit.launch.py` usage; note known non-blockers from I07.
- `docs/package_map.md`: implemented packages, imported ECN packages, intentionally skipped/deferred packages.
- `docs/repos_and_pins.md`: default `.repos`, pin, update rule, optional/no-op `.repos` files.
- `docs/licensing_and_sources.md`: adopted ECN source, reference-only/unlicensed sources, unresolved project license.
- `docs/compatibility_matrix.md`: tested Ubuntu/ROS/Gazebo/MoveIt/source pin profile status based on I01-I08 evidence.
- `docs/ci_release_checklist.md`: default CI checks, manual sim smoke, hardware gates not yet run.

I08 gate evidence:

- `.devcontainer/Dockerfile`, `.devcontainer/devcontainer.json`, `.devcontainer/README.md`, `.dockerignore`, and `.github/workflows/ci.yml` were added.
- Devcontainer image build passed: `docker build -f .devcontainer/Dockerfile -t baxter_ros2_jazzy-devcontainer .`.
- In-container read-only mounted workspace build passed with temp build/install dirs: `Summary: 8 packages finished [1min 8s]` and `ros2 pkg prefix baxter_moveit_config` resolved from `/tmp/baxter_install/baxter_moveit_config`.
- Two local CI-equivalent rounds passed: pinned SHA check, `rosdep install`, `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`, Python compile/import checks, Xacro/URDF load, and static SRDF/MoveIt config checks.
- Prior-step regression checks passed: I01 pin, I02 model/joint/mesh checks, I03 bringup `robot_description` and `/tf_static`, I04/I05 active sim controllers and 14 arm joints, I06 tiny trajectories, and I07 `/move_action` plus `moveit_left_tiny` plan+execute.

Known current non-blockers to document carefully:

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`; I05/I07 expose only arm joints for default sim motion.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensors are in first CI scope.
- Full Gazebo+MoveIt runtime is manual/local smoke for now because I07 observed possible `move_group` SIGINT teardown segfault after successful execution. Default CI uses build/import/model/MoveIt static checks.
- Project license selection remains unresolved (`TODO` in local `package.xml` files); document this as unresolved, do not invent a license.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I09
- `logs/I08_devcontainer_ci.log.md`
- `logs/I07_moveit2_sim_profile.log.md`
- `logs/I06_tiny_sim_trajectory.log.md`
- `logs/I05_ros2_control_arm_controllers.log.md`
- `logs/I04_gazebo_sim_skeleton.log.md`
- `logs/I03_minimal_bringup.log.md`
- `logs/I02_core_model_validation.log.md`
- `logs/I01_import_core_dependency.log.md`
- `RESEARCH_FINDINGS.md`
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md`
- Docs/distribution plan if needed: `plan/logs/S10_docs_distribution.log.md`
- `WORKFLOW.md` for the log format

### Gate

a new user can follow the documented sim path through `sim_tiny_trajectory`.

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I09_docs_baseline.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I09 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained prompt for I14 to `PROMPTS.md` (append-only). It must include the I14 task, read-first list, gate, and this four-part finish checklist. If the I09 gate fails, keep I09 not-completed, log the blocker, and append an I09 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Keep default docs and CI hardware-free.
- Do not add unlicensed repos to default `.repos`.
- `baxter_bridge` is bridge-host-only; skip it from default sim/devcontainer/CI builds.
- Do not teach raw safety-topic publishing in beginner docs.
- No hardware bridge, action shims, gripper implementation, optional compatibility work, or optional examples beyond the I09 docs baseline.

---

## I14 Prompt

You are agent I14 for the `baxter_ros2_jazzy` implementation project.

### Task

Prepare the public sim-first release hardening baseline. This is the release step after I09 documentation, not a hardware implementation step.

- Decide and add the root project `LICENSE`; update local package `package.xml` license fields consistently. I09 documented that local packages still use `TODO` and the project license is unresolved.
- Add `CONTRIBUTING.md`, `SUPPORT.md`, `SECURITY.md`, issue templates, PR template, `CHANGELOG.md`, release notes, and maintainer handoff documentation needed for the sim-first release.
- Issue templates must cover at least: sim bug, hardware bridge bug, docs, safety concern, pin update, and feature request.
- Release notes and support docs must use per-profile support labels based only on passed gates: `sim` passed, `sim_moveit` passed as manual/local smoke, default CI/devcontainer passed hardware-free checks, hardware bridge blocked, supervised hardware motion blocked, Zenoh/compatibility deferred.
- Preserve the pinned ECN SHA rule: the default `.repos` path may include only `CentraleNantesRobotics/baxter_common_ros2` at `678bfabea8c895b4134951a6c076217a90b9e0e6`; no unlicensed external imports.
- Keep the default build command from the repository root: `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
- Keep hardware and Zenoh out of the default install/devcontainer/CI path.
- Do not modify `plan/`.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Do not add hardware bridge tooling, action shims, grippers, compatibility layers, Zenoh fallback, or optional examples in I14.
- Do not teach raw safety-topic publishing in beginner docs or release docs.
- Claim hardware support only for gates that actually passed. At I09 handoff, I10-I12 are still blocked and no hardware support or supervised hardware motion has passed.

Known current non-blockers to carry into release notes/support docs:

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`; I05/I07 expose only arm joints for default sim motion.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensors are in first CI scope.
- Full Gazebo+MoveIt runtime is manual/local smoke for now because I07 observed possible `move_group` SIGINT teardown segfault after successful execution. Default CI uses build/import/model/MoveIt static checks.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - your step I14
- `logs/I09_docs_baseline.log.md`
- `logs/I08_devcontainer_ci.log.md`
- `logs/I07_moveit2_sim_profile.log.md`
- `logs/I06_tiny_sim_trajectory.log.md`
- `README.md`
- `docs/index.md`
- `docs/getting_started_sim.md`
- `docs/simulation.md`
- `docs/moveit_guide.md`
- `docs/package_map.md`
- `docs/repos_and_pins.md`
- `docs/licensing_and_sources.md`
- `docs/compatibility_matrix.md`
- `docs/ci_release_checklist.md`
- `RESEARCH_FINDINGS.md`
- Blueprint if needed: `plan/logs/S11_final_synthesis.log.md` sections 12 and 15
- Docs/distribution plan if needed: `plan/logs/S10_docs_distribution.log.md`
- `WORKFLOW.md` for the log format

### Gate

`docs/ci_release_checklist.md` passes for the sim-first release scope; no S11 §15 no-go condition is violated (no unlicensed default imports, no implied vendor support, no unearned hardware claims).

### Finish - Baton handoff (required)

1. Verify the gate; record the commands and evidence in your log.
2. Write `logs/I14_release_hardening.log.md` in the log format from `WORKFLOW.md` (frontmatter: `step`, `title`, `agent_date`, `status`, `previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09]`; sections: Task, Findings, Decisions, Open Questions, Artifacts).
3. Update the I14 status line in `MASTER_PLAN.md` - `completed` only if the gate passed.
4. Append a self-contained next-step prompt to `PROMPTS.md` if another step is needed; otherwise append a short release-complete handoff note. If the I14 gate fails, keep I14 not-completed, log the blocker, and append an I14 retry prompt instead.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- Only the pinned ECN SHA in default `.repos`; no other external imports.
- No hardware, no bridge build, no ROS 1 dependencies on this machine.
- Keep default docs and CI hardware-free.
- Do not add unlicensed repos to default `.repos`.
- `baxter_bridge` is bridge-host-only; skip it from default sim/devcontainer/CI builds.
- Do not teach raw safety-topic publishing in beginner or release docs.
- No hardware bridge, action shims, gripper implementation, optional compatibility work, Zenoh fallback, or optional examples in I14.
- Hardware claims require I10-I12 evidence; at this handoff those steps are still blocked.

---

## Release-Complete Handoff

I14 completed the sim-first release hardening baseline on 2026-07-09.

Gate evidence is in `logs/I14_release_hardening.log.md`. The default release scope remains sim-first only:

- `sim`: passed.
- `sim_moveit`: passed as manual/local smoke.
- default CI/devcontainer: passed hardware-free checks.
- `hardware_bridge`: blocked until I10.
- supervised hardware motion: blocked until I12.
- Zenoh/compatibility fallback: deferred.

No next implementation step is needed in the current I00-I14 plan. Future work should open a new gated plan or unblock I10 explicitly with physical Baxter access, bridge host choice, and university network policy.

---

## I10-prep Prompt (hardware-free action shim dry-run)

You are agent I10-prep for the `baxter_ros2_jazzy` implementation project.

### Task

Create the `baxter_hardware_bridge` package with ROS 2 `FollowJointTrajectory` action shims, safety state checker, mock robot, and dry-run self-test — all testable without a real robot or `baxter_bridge`.

This is hardware-free implementation: no `baxter_bridge` build, no ROS 1 deps, no real robot access.

- Create `src/baxter_hardware_bridge/` (ament_python package).
- Implement `safety.py`: `SafetyStateChecker` that subscribes to `/robot/state` (`baxter_core_msgs/AssemblyState`), provides `is_safe_for_motion()` (ready + enabled + not stopped + no error + no e-stop), and a CLI `baxter_safety_check` entry point.
- Implement `follow_joint_trajectory_shim.py`: `FollowJointTrajectoryShim` action server on `/robot/limb/{side}/follow_joint_trajectory` accepting `control_msgs/action/FollowJointTrajectory`. Validates exact 7-joint Baxter names, rejects unsafe state, publishes `baxter_core_msgs/JointCommand` (POSITION_MODE) to `/robot/limb/{side}/joint_command` at bounded rate, publishes low `set_speed_ratio` and `joint_command_timeout`, holds position on cancel (never calls `/robot/set_super_stop`). Has `mock_mode` param to skip JointCommand publishes.
- Implement `mock_robot.py`: publishes safe `/robot/state` and `/robot/joint_states`, echoes `JointCommand` into joint positions (feedthrough), has `unsafe` parameter for testing rejection.
- Implement `dry_run_test.py`: in-process test that starts mock + shim, sends a tiny goal (expect accept + succeed), sends bad joint names (expect reject), sets unsafe state and sends goal (expect reject). Exit 0 on pass, 1 on fail.
- Create `launch/hardware_bringup.launch.py` and `launch/dry_run.launch.py`.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` — I10, I10-prep, I11
- `plan/logs/S04_bridge_architecture.log.md` — FollowJointTrajectory boundary design, minimum hardware mode topic list, safety rules
- `plan/logs/S06_moveit_ros2_control.log.md` — hardware controller action names
- `RESEARCH_FINDINGS.md` — JointCommand message, Joint names
- `src/baxter_moveit_config/config/moveit_controllers_hardware.yaml` — existing hardware controller config
- `src/baxter_common_ros2/baxter_core_msgs/msg/AssemblyState.msg`
- `src/baxter_common_ros2/baxter_core_msgs/msg/JointCommand.msg`
- `WORKFLOW.md` for the log format

### Gate

`ros2 run baxter_hardware_bridge dry_run_test` passes:
1. Safe state + correct joints → goal accepted and succeeded.
2. Bad joint names → goal rejected.
3. Unsafe state → goal rejected.

### Finish — Baton handoff (required)

1. Verify the gate; record the dry-run test output in your log.
2. Write `logs/I10_prep_hardware_shim_dry_run.log.md` (frontmatter: `step: I10-prep`, `title`, `agent_date`, `status`, `previous_steps: [I00-I09, I14]`).
3. Update `MASTER_PLAN.md` I10-prep status to `completed`.
4. Append a self-contained prompt for I10 (hardware bridge non-motion on real robot) to `PROMPTS.md`.

### Rules

- `plan/` is a read-only archive; never modify it.
- `PROMPTS.md` is append-only; never edit prior entries.
- No `baxter_bridge` build, no ROS 1 deps, no real robot access.
- `baxter_hardware_bridge` must build with `colcon build --base-paths src --packages-skip baxter_bridge`.
- Keep default CI hardware-free: do not add `baxter_hardware_bridge` to the default CI workflow.
- Do not teach raw safety-topic publishing in any docs.

---

## I10-prep Completion Note

I10-prep completed on 2026-07-09.

Created `src/baxter_hardware_bridge/` (ament_python) with:
- `safety.py` — SafetyStateChecker + `baxter_safety_check` CLI
- `follow_joint_trajectory_shim.py` — FollowJointTrajectory action server → JointCommand
- `mock_robot.py` — mock /robot/state + /robot/joint_states for dry-run
- `dry_run_test.py` — in-process self-test (3 tests, all pass)

Gate evidence: `ros2 run baxter_hardware_bridge dry_run_test` → PASS (3/3 tests).

Full build: `colcon build --base-paths src --packages-skip baxter_bridge` → 9 packages finished.

Next step: I10 (hardware bridge non-motion) requires physical Baxter access, bridge host, and network policy. When ready, run `baxter_bridge` on the bridge host, verify non-motion topics, then run `hardware_bringup.launch.py` with `mock_mode:=false` to exercise the shims against the real robot.

---

## I15 Prompt (RViz simulation launch profiles)

You are agent I15 for the `baxter_ros2_jazzy` implementation project.

### Task

Add two proper, supported RViz launch profiles for the existing simulation stack:

1. Normal simulation plus a plain Baxter RobotModel/TF RViz view.
2. Simulation plus MoveIt `move_group` and a configured MotionPlanning RViz view.

This step implements only the RViz launch/configuration scope recorded in `logs/sim_gui_testing_problems.log.md`. Do not implement unrelated P1-P7 or P13-P20 fixes.

### Read First

- `AGENTS.md`
- `MASTER_PLAN.md` - I15
- `logs/sim_gui_testing_problems.log.md` - especially P8-P10, P11, and the requested RViz follow-up
- `docs/simulation.md`
- `docs/moveit_guide.md`
- `src/baxter_gz_sim/launch/sim.launch.py`
- `src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro`
- `src/baxter_gz_sim/config/ros2_controllers.yaml`
- `src/baxter_moveit_config/launch/move_group.launch.py`
- `src/baxter_moveit_config/launch/sim_moveit.launch.py`
- `src/baxter_moveit_config/config/`
- Installed Jazzy `moveit_configs_utils` RViz/move-group launch helpers

### Deliverables

- Add a `baxter_gz_sim` launch entry point for normal simulation plus RViz, with a checked-in plain RobotModel/TF `.rviz` configuration.
- Add a `baxter_moveit_config` launch entry point for simulation plus `move_group` plus RViz, with a checked-in MotionPlanning `.rviz` configuration.
- Forward the existing `headless` launch option and set RViz `use_sim_time:=true`.
- Ensure plain RViz receives the Baxter description and TF needed for RobotModel display.
- Ensure MoveIt RViz receives or can retrieve the URDF, SRDF, kinematics, joint limits, planning pipeline, and OMPL configuration. It must not depend on running bare `rviz2`.
- Complete state publication for the independent `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` so RobotModel does not start with the P8/P9 TF errors. Do not add gripper command controllers.
- Add only the runtime dependencies required by the two RViz profiles.
- Document the two supported launch commands in `docs/simulation.md` and `docs/moveit_guide.md`.

### Gate

1. Default build succeeds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
2. Normal RViz profile starts from a clean graph, loads the Baxter RobotModel, reports a complete expected TF tree, and reflects arm movement from `/joint_states`.
3. MoveIt RViz profile starts from a clean graph, parses URDF/SRDF, connects to `move_group`, and shows OMPL plus the configured planner without `NO PLANNING LIBRARY LOADED`.
4. `/joint_states` contains all 17 independent joints and MoveIt no longer repeats the missing head/source-finger warning.
5. Existing `sim_tiny_trajectory` and `moveit_left_tiny` smoke commands still pass.

### Finish - Baton handoff

1. Record commands and gate evidence in `logs/I15_rviz_launch_profiles.log.md` using the `WORKFLOW.md` log format.
2. Mark I15 `completed` in `MASTER_PLAN.md` only if every gate passes.
3. Append a correction/follow-up prompt to `PROMPTS.md` if any I15 work remains; never edit this prompt in place.

### Rules

- `plan/` is read-only.
- Do not implement other sim GUI review fixes in this step.
- Keep default CI hardware-free and continue using `--packages-skip baxter_bridge`.
- Do not add gripper command support, cameras, octomap sensing, compatibility layers, hardware behavior, or safety-topic instructions.

---

## I15 Completion Note

I15 completed on 2026-07-20. The user superseded the original RViz-only scope
and authorized remediation of all actionable P1-P20 simulation findings.

Delivered supported `sim_rviz` and `sim_moveit_rviz` profiles, deterministic
world mounting and neutral state, 17 independent joint states, truthful
reversible direct/MoveIt motion checks, cancellation/hold, readiness gating,
an audited collision matrix, and process-empty teardown. The clean default
build and CI-equivalent static checks pass. Full gate evidence and exact
runtime artifacts are recorded in `logs/I15_rviz_launch_profiles.log.md`.

No further unblocked implementation step is scheduled. I10-I12 remain blocked
on physical Baxter access and supervision; I13 remains deferred pending a
concrete need.

---

## I16 Prompt — Fix the RViz MoveIt MotionPlanning Display

**Goal:** make the MotionPlanning display load its robot model, so the planner list
populates and the interactive end-effector markers appear. Everything else already works.

**Symptom and error:** see `docs/known_issues.md` — read it first. In short, RViz launches
and renders the robot, but `loadRobotModel` aborts with
`InvalidParameterTypeException: ... is of type {double}, setting it to {string} is not
allowed`, currently naming
`robot_description_kinematics.left_arm.kinematics_solver_search_resolution`.

**Do not re-investigate** the four hypotheses already tested and falsified in
`known_issues.md` (Turkish `LC_NUMERIC`, launch_ros serialisation, `moveit_configs_utils`
types, the `.rviz` config as such). Also note: the error previously named a
`joint_limits` parameter and moved here after that one was removed, so *removing more
parameters is not the fix* — it only shifts the failure to the next double.

### Leads, in order

1. **`Move Group Namespace`.** `src/baxter_moveit_config/config/moveit.rviz:53` sets
   `Move Group Namespace: ""`. Neither the ROS 1 config nor
   `/opt/ros/jazzy/share/moveit_setup_app_plugins/templates/config/moveit.rviz` has this
   key at all. The log line immediately before the throw is
   `[rviz2.moveit.ros.motion_planning_frame]: MoveGroup namespace changed: / -> . Reloading params.`
   Try deleting the key and re-running before anything else.
2. **The reload path.** `MotionPlanningFrame` re-reads MoveIt parameters at that point
   rather than using the launch-supplied ones. Read
   `moveit_ros_visualization/motion_planning_rviz_plugin` (`motion_planning_frame.cpp`,
   `initFromMoveGroupNS` / `changePlanningGroupHelper`) for MoveIt 2.12.4 and find what it
   copies from `/move_group` onto the `rviz2` node and with which types.
3. **Compare against the working ROS 1 setup.** It works there, so diff the parameter
   plumbing, not the display config:
   - `~/baxter_noetic_ws/src/baxter_noetic/baxter_moveit_config/launch/planning_context.launch`
     — which of `robot_description`, `_semantic`, `_planning`, `_kinematics` are loaded and
     into which namespace.
   - `.../launch/moveit_rviz.launch` and `.../launch/move_group.launch` — what namespace
     RViz and `move_group` each run in.
   - `.../launch/moveit.rviz` — the ROS 1 display block, for what it does *not* set.
   ROS 1 had one untyped global parameter server; ROS 2 requires each node to declare its
   own typed parameters. The fix likely lies in that difference.

### Verify

```bash
ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=false
```

Pass: no `loadRobotModel` exception and no `No robot state or robot model loaded` in the
rviz2 output; Context tab shows OMPL instead of `NO PLANNING LIBRARY LOADED`; a 6-DOF
marker on each gripper that drags via IK; Plan and Execute move the arm in Gazebo.
Regression: bare `ros2 launch baxter_moveit_config sim_moveit.launch.py` must still start
without RViz.

### Rules

- `plan/` is read-only; corrections go in the current log, never in completed ones.
- No `ROS_DOMAIN_ID` or `GZ_PARTITION` — one user, one machine, one sim at a time.
- Build with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
- Hardware I10-I12 stay blocked. Do not add gripper controllers, cameras, or octomap sensing.
- Do not commit unless the user asks.
- On success, update `docs/known_issues.md`, the `sim_moveit_rviz` status rows in
  `README.md` / `docs/index.md` / `compatibility_matrix.md` / `maintainer_handoff.md` /
  `package_map.md`, restore the MotionPlanning pass criterion in
  `docs/ci_release_checklist.md`, and add a `CHANGELOG.md` entry.

## I17 Prompt — Pre-Hardware Hardening and Polish

**Goal:** land the last two safety features the command path is missing (path tolerance,
stopped-velocity), remove one launch-file trap, and leave the repo internally consistent —
so the next session can go straight to the robot. **No hardware in this step.** The robot
is not available and the remaining I12 blocker needs a human with an e-stop in hand.

**Read first, in this order:**

1. `docs/i12_completion_plan.md` — the plan this prompt executes. Phases A and B are yours;
   Phase C is the robot day and is *not* yours.
2. `logs/I12_prep_command_path_audit.log.md` — especially the **Resolution** section at the
   bottom, which records what was already fixed on 2026-07-23 and what stays open.
3. `docs/hardware_runbook.md` — the validation table and parameter table you must keep current.

### Already done — do not redo, do not re-investigate

Findings **F1, F2, F3, F4 and F10** from the audit are fixed and covered by
`dry_run_test` (16 cases, all passing, and CI already runs it at
`.github/workflows/ci.yml:92`). Goals are validated at accept time, every command is
clamped to `max_step_rad_per_cycle`, cancel holds for `hold_duration_sec`, and
`sim_tiny_trajectory` fails a goal that succeeds without publishing feedback. Do not
re-derive or re-fix any of it.

Deliberately **not** being ported from the legacy ROS 1 server in
`plan/baxter_noetic_ref/baxter_interface/`, each for a stated reason — do not add them:

- **Velocity mode + PID.** Would close a 100 Hz loop across a bridge whose worst-case send
  stall is 0.5 s (audit finding F8). The robot runs its own joint controllers.
- **Inverse-dynamics feedforward (`position_w_id`).** Requires `RAW_POSITION_MODE` (4),
  which per `baxter_interface/src/baxter_interface/limb.py` "bypasses the safety system
  modifications (e.g. collision avoidance)". We use `POSITION_MODE` (1) on purpose.
- **Bezier / minjerk interpolation.** ~620 lines; MoveIt time-parameterizes densely enough
  that linear interpolation tracks it closely. Revisit only if jerk appears at waypoints.
- **Per-joint goal position tolerance.** Rethink shipped it *disabled*
  (`plan/baxter_noetic_ref/baxter_interface/cfg/PositionJointTrajectoryActionServer.cfg`,
  default `-1.0`, and the code skips the check when it is not positive).
- **Shrinking `STATE_TIMEOUT_SEC`** (audit F5). Accepted as-is; tightening it risks false
  aborts mid-trajectory and the physical e-stop is the real mitigation.

Also do not investigate the **enable-from-tucked** blocker (`enable_robot.py -e` fails).
It is fully diagnosed in `logs/I12_supervised_hardware_motion.log.md`: a latched
`left_s1` collision force-field while tucked and disabled. Connectivity, robot health,
calibration, thermal and TCPROS negotiation are all **already ruled out by measurement**.
The remedy is `tuck_arms.py -u` under supervision, which needs the robot.

### Tasks

1. **Path tolerance monitoring** in
   `src/baxter_hardware_bridge/baxter_hardware_bridge/follow_joint_trajectory_shim.py`.
   Inside the existing interpolation loop, compare the commanded setpoint against
   `self._latest_positions` each cycle; abort when any joint exceeds `path_tolerance_rad`
   (new node parameter, default **0.2**, the legacy per-joint default from the cfg above).
   Both values are already in scope, so this should be small.

   **Decision already made — implement it this way:** on violation the shim **holds** via
   the existing `_hold_position()`, it does *not* stop commanding. Stopping commands is
   correct for an e-stop (a lagging arm is not an unsafe robot) but would let the arm sag
   into gravity compensation after the robot's 0.2 s `joint_command_timeout`. The legacy
   holds too, via `_command_stop`. Use a **distinct result code** so this is not confused
   with a safety abort; the file already defines `RESULT_CANCELED = -100` and
   `RESULT_ABORTED = -101`, so follow that convention.

2. **Stopped-velocity check** in the same file. After the trajectory completes, verify no
   joint still moves faster than `stopped_velocity_tolerance` (new node parameter, default
   **0.25**, again from the legacy cfg). This is feasible because `deser_joint_state` at
   `scripts/py_bridge.py:153` already unpacks the ROS 1 `velocity` and `effort` arrays into
   the ROS 2 `JointState` — verified, do not re-check.

3. **Add a `mock_mode` launch argument** to
   `src/baxter_hardware_bridge/launch/dry_run.launch.py`. It currently hardcodes
   `"mock_mode": True` for both shims, so the shims never publish `JointCommand`, the mock
   arm can never move, and any trajectory run against this launch file fails its position
   check. Follow the pattern already in `hardware_bringup.launch.py:17-36`
   (`LaunchConfiguration` + `DeclareLaunchArgument`). Keep the default `true` so existing
   behaviour is unchanged.

4. **Regression cases** in
   `src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py`. Reuse the helpers
   that are already there: `expect_reject(node, client, goal, label, results)` and
   `make_goal(joints, [(positions, seconds), ...])`. Add cases for path tolerance tripping,
   path tolerance *not* tripping in normal operation (so a too-tight default fails at the
   desk rather than on the robot), and the stopped-velocity branch. To make the measured
   position stop following the setpoint, use the same technique as the existing Test 14 —
   `MockRobot.joint_states_enabled` in `mock_robot.py` was added for exactly this kind of
   partial-failure simulation; add a comparable flag for command feedthrough if needed.

5. **Polish pass (Phase B of the plan).** Make these agree with each other and with the
   code: `docs/hardware_runbook.md` (validation table, parameter table, dry-run case count),
   `docs/hardware_test_commands.md`, `docs/i12_completion_plan.md`, `MASTER_PLAN.md`, and
   `CHANGELOG.md` (Unreleased). **`MASTER_PLAN.md` is currently stale** — its I12 entry still
   carries a "Second blocker" paragraph instructing a future agent to fix the command path
   that is already fixed. Update the blocker list to name only enable-from-tucked and leave
   the status `blocked`, because the gate itself still needs the robot. Every parameter you
   add must appear in the runbook's parameter table with its default, and every new
   rejection or abort reason in its validation table.

### Verify

```bash
colcon build --base-paths src --symlink-install \
  --packages-select baxter_hardware_bridge baxter_examples
source install/setup.bash
ros2 run baxter_hardware_bridge dry_run_test        # OVERALL: PASS, exit 0
```

Then the closed-loop rehearsal, which task 3 makes a single launch:

```bash
ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p left_action:=/robot/limb/left/follow_joint_trajectory \
  -p right_action:=/robot/limb/right/follow_joint_trajectory \
  -p joint_states_topic:=/robot/joint_states
# and again with -p cancel_after_sec:=1.0
```

Pass: every `dry_run_test` case reports PASS including the new ones; both arms report a
feedback count and `verified: max_error=...`; `Reversible trajectories verified for both
arms`; the cancel run reports `Cancellation hold verified`. Regression: the plain
`ros2 launch baxter_hardware_bridge dry_run.launch.py` (no argument) must still come up in
mock mode.

### Rules

- Build with `colcon build --base-paths src --symlink-install`. **Plain `colcon build`
  fails** with `Duplicate package names not supported` because
  `plan/baxter_noetic_ref/baxter_examples` shadows `src/baxter_examples`.
- `baxter_examples` uses `install(PROGRAMS ... RENAME ...)`, which defeats
  `--symlink-install` — it is always a copy and **always needs a rebuild after editing**.
- `plan/` is read-only reference. Corrections go in the current log, never in completed ones.
- No `ROS_DOMAIN_ID` or `GZ_PARTITION` — one user, one machine.
- Do not commit unless the user asks. There is already a large uncommitted working tree.
- Do not touch hardware. Do not hand-write trajectories to test the shim; it now rejects a
  `time_from_start` of 0 on the first point, and `sim_tiny_trajectory` is the supported path.
- On success write `logs/I17_pre_hardware_hardening.log.md` in the format used by the other
  logs (front-matter with `step`, `title`, `agent_date`, `status`, `previous_steps`;
  findings with evidence, decisions, open questions, artifacts), update `MASTER_PLAN.md`,
  and append a self-contained robot-day prompt to `PROMPTS.md`.

---

## I12 Prompt — Robot Day: Supervised Hardware Motion

**Goal:** pass the I12 gate on the physical robot — one tiny, reversible, low-speed
trajectory per arm with feedback, result, and cancel/hold. This is the **only**
remaining item in `docs/i12_completion_plan.md` (Phase C). Everything desk-side is done.

**This step touches hardware.** It requires a human physically present with the e-stop in
hand, a clear workspace, and nobody within arm reach. If you are running without that,
stop and say so — do not run anything past §5 of the command sheet.

**Read first, in this order:**

1. `docs/hardware_test_commands.md` — the copy-paste sheet. Follow it from §0. It is the
   authority on commands; this prompt only tells you what is different.
2. `logs/I12_supervised_hardware_motion.log.md` — the enable-from-tucked diagnosis.
3. `logs/I17_pre_hardware_hardening.log.md` — what the command path now does, and the two
   desk-tuned tolerances that hardware can invalidate.

### Already settled — do not re-investigate

**The command path is done.** Goals are validated at accept time (joint names, position
count, finite values, URDF position and velocity limits, strictly increasing
`time_from_start`, `/robot/joint_states` freshness); every command is clamped to
`max_step_rad_per_cycle`; cancel and both tolerance aborts hold for `hold_duration_sec`;
safety aborts stop commanding. `dry_run_test` covers it in 19 cases and CI runs it. Do not
re-derive, re-audit or re-fix any of it.

**The enable failure is diagnosed.** `enable_robot.py -e` fails from the tucked pose
because of a latched `left_s1` collision force-field: `impact torque -3.57737` against
`scaled impact threshold 0`, and the threshold scales with velocity/acceleration commands
that are 0 while disabled, so it cannot self-clear. Already ruled out **by measurement** —
do not re-test: connectivity (`/realtime_loop` attaches to a fresh enable publisher in
0.24 s), robot health (201 `/diagnostics` statuses, 200 at level 0, control loop OK at
100 Hz, 0.00% overruns), calibration (slopes present for all 14 joints, software
`1.2.0.57`), thermal, and TCPROS negotiation. The remedy is `tuck_arms.py -u`, which
suppresses collision avoidance and republishes enable at 20 Hz where `enable_robot.py`
publishes once with a 2 s timeout.

**Deliberately not ported** from `plan/baxter_noetic_ref/baxter_interface/`, each for a
stated reason in `docs/i12_completion_plan.md` — do not add them: velocity mode + PID,
`position_w_id` inverse-dynamics feedforward (needs `RAW_POSITION_MODE`, which bypasses
collision avoidance), Bezier/minjerk interpolation, per-joint goal position tolerance
(Rethink shipped it disabled), and shrinking `STATE_TIMEOUT_SEC`.

### Sequence

Follow `docs/hardware_test_commands.md`. The deltas versus the last session:

1. **§0 pre-flight.** The route check is the one that matters:
   `ip route get $(getent hosts 011412P0024.local | awk '{print $1}')` must say
   `dev enp4s0`, not `dev wlp0s20f3`. The robot's IP is a DHCP lease and moves — never
   hardcode it. No `ROS_DOMAIN_ID`, no `GZ_PARTITION`.
2. **§2 bridge, §4 shims.** `hardware_bringup.launch.py` defaults to `mock_mode:=false`,
   which is what you want. Confirm both shims log `(mock_mode=False)`.
3. **§5 interlock gate and §5d malformed goals.** Zero motion, run while still disabled.
   §5d has so far only been verified against `mock_robot`; this confirms the same
   validation with a real bridge in the path.
4. **§6 `baxtool tuck_arms.py -u` under supervision** — the blocker. This is a large
   whole-arm motion. `enabled: False` after a *successful* untuck is normal
   (`tuck_arms.py::_move_to` disables on its way out if either arm still reports a
   collision object) — check arm positions, not the flag. If it hangs without ever
   enabling, the force-field theory is wrong; do **not** go re-check health or
   calibration, they are cleared. The only remaining lead is `rethink.log` on the robot,
   which needs a shell we do not have.
5. **§7 the I12 gate**, both arms, then **§7b cancel-and-hold**. Use
   `sim_tiny_trajectory` — do **not** hand-write trajectories.
6. **§8 shutdown:** tuck, disable, then stop shims before the bridge.

### What is new since the last hardware session

Two aborts have never run against a real arm. Both stop the goal but keep holding, so the
arm does not sag:

```
Path tolerance violated: left_s1 lags its setpoint by 0.2xx rad (limit 0.200 rad)
Goal tolerance violated: left_s1 still moving at 0.xxx rad/s (limit 0.250 rad/s)
```

`path_tolerance_rad` (0.2) and `stopped_velocity_tolerance` (0.25) are Rethink's own
defaults but were validated here only against a mock with no physics and zero lag. **If
either fires on a move the arm visibly completed, the tolerance is too tight, not the arm
broken.** Re-run with `-p path_tolerance_rad:=0.3` on the shims and record the value that
worked. Before loosening, consider F8 first:

**F8 — bridge backpressure.** `ROS1Publisher.publish` runs synchronously inside the ROS 2
callback and can block up to 0.5 s, exceeding the robot's 0.2 s `joint_command_timeout`;
with depth-1 QoS on both sides intermediate samples are dropped. Not reproducible against
a mock. Symptoms are visible stutter during the move **and now** a path-tolerance abort.
This is the only audit finding that can be settled only on hardware. A path-tolerance
abort should be read as a possible F8 symptom before it is read as a bad tolerance.

Also unconfirmed on hardware: whether `hold_duration_sec = 1.0` is long enough that the
arm does not float after a cancel, whether Baxter's gravity-compensation fallback after
`joint_command_timeout` is benign in the untucked pose, and whether the bridge's velocity
array reaches the stopped-velocity check at all (the deserializer is verified, the
end-to-end path is not).

### Gate

Per arm, from `sim_tiny_trajectory` with the hardware action names:

```
/robot/limb/<side>/follow_joint_trajectory outbound feedback: NNN messages
/robot/limb/<side>/follow_joint_trajectory outbound verified: max_error=0.00xx rad
/robot/limb/<side>/follow_joint_trajectory return   feedback: NNN messages
/robot/limb/<side>/follow_joint_trajectory return   verified: max_error=0.00xx rad
Reversible trajectories verified for both arms
```

and from the `-p cancel_after_sec:=1.0` run: `Active trajectory canceled; controller is
holding position` followed by `Cancellation hold verified`. The arm must stop and hold,
not fall.

### Rules

- Build with `colcon build --base-paths src --symlink-install`. **Plain `colcon build`
  fails** with `Duplicate package names not supported` because
  `plan/baxter_noetic_ref/baxter_examples` shadows `src/baxter_examples`.
- `baxter_examples` uses `install(PROGRAMS ... RENAME ...)`, which defeats
  `--symlink-install` — always a copy, **always needs a rebuild after editing**.
- Never publish to `/robot/set_super_enable` or `/robot/set_super_stop`. The single
  documented exception is the supervised hand-driven enable in §6, collision suppression
  first, 15 s cap, and only after `tuck_arms.py -u` has failed.
- Do not hand-write trajectories. `sim_tiny_trajectory` is the supported path.
- `plan/` is read-only reference. Corrections go in the current log, never in completed ones.
- Do not commit unless the user asks.
- **Abort at any point by hitting the physical e-stop.** To stop a goal cleanly, Ctrl-C
  `sim_tiny_trajectory` — it cancels and the shim holds.

### On completion

Record results in `logs/I12_supervised_hardware_motion.log.md` (append a dated session
section; do not rewrite the existing diagnosis), set the I12 status in `MASTER_PLAN.md`,
update the gate table in `docs/hardware_test_commands.md`, add the observed tolerance
values to `docs/hardware_runbook.md`, add a CHANGELOG entry, and retire
`docs/i12_completion_plan.md` once its findings are folded in — that is what its header
says to do. If the gate does **not** pass, leave the status `blocked`, record what was
measured, and name the single remaining blocker.

---

## I20 Prompt — Robot Day: Fast-Motion Characterisation

**Goal:** answer the one question the command path cannot answer from a desk —
what happens to tracking as trajectory speed rises toward the shim's 2.0 rad/s
clamp — and decide `path_tolerance_rad` from that data.

### Read first, in this order

1. `docs/hardware_day_plan.md` — the phase order, standing rules, abort criteria.
   P4a is the reason for this session.
2. `docs/hardware_test_commands.md` — the copy-paste sheet. §7 now documents
   `duration` / `offset`.
3. `logs/I18_hardware_day.log.md` — what the robot did on 2026-07-24,
   particularly F9 (`speed_ratio` does nothing), F22 (the real tolerance
   numbers), F1 (the stale-mock accident) and F12 (process hygiene).
4. `logs/I19_post_hardware_backlog.log.md` — the six fixes since, and the two
   `ros2 run` traps that will otherwise cost you an hour.

### Already settled — do not re-investigate

- **`speed_ratio` has no measurable effect.** Tripling it changed nothing (F9).
  Duration is the binding constraint. Do not run another speed-ratio sweep.
- **`path_tolerance_rad = 0.2` is not egregiously loose.** F22 measured a worst
  in-flight lag of 0.0352 rad — a 5.7× margin, not the 26× that F3 claimed and
  withdrew. Do not tighten to 0.05; it would false-trip.
- **Enable-from-tucked is solved.** `tuck_arms.py -u`, first attempt, ~23 s. Do
  not re-check robot health, calibration, thermal or the control loop — the
  2026-07-22 sweep cleared all of them.
- **The success path deliberately stops commanding** after a goal completes.
  I17's R7 was closed on 2026-07-25 with F11's evidence (0.001 rad drift over
  ~20 s uncommanded). Not a defect; do not "fix" it.

### Sequence

`docs/hardware_day_plan.md` P1 → P2 → P3 → P4 → **P4a** → P5 → P6 → P7 → P9.
P4a and P5 are the session; P6 and P7 are droppable if time runs short.

### What is new since the last robot session

All desk-verified only — this session is where each meets a real robot:

| Change | What to watch for |
|---|---|
| `/robot/state` publisher-count gate | Bring-up should be silent. `CONTESTED: N publishers` means a stale mock or an orphaned shim is on the graph — fix the graph, do not bypass the gate |
| `hardware_bringup.launch.py` mock guard | Aborts the launch if `mock_baxter_robot` is running |
| Robot's own `header.stamp` is preserved | **Watch for the clock-skew warning at bring-up.** If `py_bridge` warns that stamps are more than 0.5 s from this host's clock, MoveIt will discard states as stale in P7 — deal with it then, not after |
| Real md5sum on published topics | A ROS 1 capture of `joint_command` now decodes; `scripts/analyze_tracking_lag.py` will say `|command - measured|` rather than `|ref_joint_states - measured|` |
| `duration` / `offset` on `sim_tiny_trajectory` | The mechanism for P4a |
| Cancel-hold settle window | The cancel sweep in P6 is worth running again; it was skipped last time because the check was broken |

### Gate

1. P4 reproduces the I12 result — both arms, feedback, no tolerance abort. A
   regression here outranks everything below; stop and diagnose.
2. P4a produces a tracking figure at **at least 0.5 rad/s**, with the escalation
   step that broke it (or the top step reached) recorded.
3. `analyze_tracking_lag.py` reports `|command - measured|` against a capture
   from this session.
4. A defensible `path_tolerance_rad`: keep 0.2, or tighten with the fast-motion
   numbers behind it. 0.15 is the floor F22 allows.

### Rules

- Supervised, e-stop in hand, workspace clear, sonar off and re-checked.
- Escalate speed one step at a time, checking the arm between runs. Stop on the
  first abort, stutter or unexpected sound.
- Kill by explicit PID — and remember `ros2 run` spawns the node as a child, so
  the PID you backgrounded is the wrapper.
- `colcon build` before trusting any `ros2 run baxter_examples` output.
- Source `scripts/baxter_env.sh` in every terminal, before `colcon build` too.

### On completion

Write `logs/I20_<name>.log.md` with the frontmatter template from `WORKFLOW.md`,
add the I20 entry and status line to `MASTER_PLAN.md`, update the tolerance rows
in `docs/hardware_runbook.md` and the gate table in
`docs/hardware_test_commands.md` if the numbers moved, add a CHANGELOG entry, and
append the next prompt here. If a tolerance changes, the shim default changes
with it and `dry_run_test` must still pass 25/25.
