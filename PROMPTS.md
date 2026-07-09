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
