# Agent Prompts

This file accumulates the prompt each agent would give to the next agent. Append-only: never edit prior entries.

---

## S01: Validate Research Assumptions

```
You are agent S01 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Re-validate and update the key claims made in the existing research report. Do NOT redo the full research. Only check whether the assumptions listed below are still correct, have changed, or are weaker/stronger than stated. Add any new developments discovered during validation.

## Context

This is Step S01 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project will produce a planning blueprint only, no code implementation. Your findings feed into all subsequent steps (S02–S11).

## Existing Research

Read the full existing research report at:
  ~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md

Read the Noetic reference repo for context (read-only, do not modify):
  ~/baxter_ros2_jazzy_plan/baxter_noetic_ref/

## Claims to Validate

Check each of these claims from the research report. For each, state whether it is CONFIRMED, CHANGED, or WEAKENED, and briefly explain:

1. ROS 2 Jazzy is an LTS release (supported to ~2029) on Ubuntu 24.04 Noble, Python 3.12, Fast DDS / Cyclone DDS.
2. ROS 1 Noetic is EOL (May 2025) and targets Ubuntu 20.04 Focal. Ubuntu 24.04 does not support ROS 1.
3. ros1_bridge is not supported on Ubuntu 24.04/Jazzy. It only bridges message/service types known at build time. Action bridging between ROS 1 and ROS 2 is not first-class.
4. Gazebo Classic (Gazebo 11) reached EOL January 2025. Jazzy's recommended simulation is Gazebo Harmonic via ros_gz.
5. MoveIt 2 is mature and supported on Jazzy (Jazzy branch, CI, tutorials recommend it).
6. ros2_control is mature on Jazzy with joint_trajectory_controller and gz_ros2_control for Harmonic.
7. Baxter's physical robot runs ROS 1 Kinetic internally and cannot be upgraded to ROS 2.
8. Rethink Robotics is defunct; HAHN Group acquired Sawyer/INTERA but not a Baxter ROS 2 support path.
9. Existing community ROS 2 Baxter work: CentraleNantesRobotics/baxter_common_ros2 (messages, bridge, most mature), RethoughtRobotics/BaxterSDK and baxter-zenoh (new, low adoption), angysof16/BaxterMotionPlanning (Jazzy + Harmonic + MoveIt 2 sim).
10. Baxter Noetic SDK has 17 packages, ~73 Python files, ~22 C++ files (all simulation), 33 custom messages, 6 services, zero custom actions, and uses control_msgs/FollowJointTrajectory.
11. The Noetic simulator uses custom Gazebo Classic C++ plugins (gazebo_ros_control, controller_interface, effort_controllers) that do not migrate cleanly to Gazebo Harmonic.
12. QoS mismatches in ROS 2 can silently break bridged topics. Python 3.12 on Jazzy may expose old SDK assumptions. Camera/high-rate topics may stress bridging.

For each claim:
- Search current ROS 2 Jazzy documentation, GitHub repos, and release notes.
- Check community repo activity (last commit date, open issues, stars) for the repos listed in claim 9.
- Note any NEW developments since the research was done (new repos, new releases, EOL changes, etc.).

## Output

Write your findings to:
  ~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md

Use the YAML+Markdown format already in that file. Fill in agent_date, set status to completed, and fill all sections (Task, Findings, Decisions, Open Questions, Artifacts).

Then update the step status in:
  ~/baxter_ros2_jazzy_plan/MASTER_PLAN.md

Change the S01 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:
  ~/baxter_ros2_jazzy_plan/PROMPTS.md

The next step is S02 (Audit Community Packages). Write a self-contained prompt for S02 that includes:
- What S02 should do
- Which repos to audit
- What scoring criteria to use (completeness, maintenance, licensing, Jazzy compatibility, code quality, adoption)
- That S02 should read the S01 log before starting
- The file paths it needs to read/write

## Rules

- Read-only on ~/baxter_ros2_jazzy_plan/baxter_noetic_ref/ — never modify it
- Only modify files inside ~/baxter_ros2_jazzy_plan/
- Be specific: cite URLs, commit dates, version numbers where possible
- If a claim is unchanged, say so briefly — don't repeat the full rationale
- Flag anything that is WEAKENED or CHANGED with emphasis, as these affect downstream design decisions
- For community repos, include: last commit date, open/closed issue counts, star count, and license if findable
```

---

## S02: Audit Community Packages

```
You are agent S02 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Audit candidate community Baxter packages and decide how each should influence the migration blueprint. Do not implement code. This is a research/design planning step.

## Context

This is Step S02 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no code implementation. Your output will feed later architecture steps, especially S04 bridge architecture, S05 simulation architecture, S06 MoveIt/ros2_control, and S08 package mapping.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repo only for context, read-only:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Repos To Audit

Audit at least these repositories:

- `CentraleNantesRobotics/baxter_common_ros2` - ROS 2 messages, description, ECN bridge; likely most established.
- `CentraleNantesRobotics/baxter_legacy` - ROS 1/Python 3 robot-side packages and Debian/package workflow.
- `CentraleNantesRobotics/baxter_gz` - Gazebo Sim / JointCommand-compatible bridge experiment.
- `Baxterminator/ECN_Baxter` - ECN lab wrappers and course packages.
- `RethoughtRobotics/BaxterSDK` - new ROS 2 SDK + MoveIt2 integration, low adoption.
- `RethoughtRobotics/baxter-zenoh` - new Docker/Zenoh bridge for Baxter ROS 1 to ROS 2.
- `RethoughtRobotics/ros1_bridge` - custom bridge fork used by `baxter-zenoh`.
- `angysof16/BaxterMotionPlanning` - ROS 2 Jazzy + Gazebo Harmonic + ros2_control + MoveIt2 sim.
- `bornaparo/baxter_moveit_config` - older/partial ROS 2 MoveIt/Gazebo config.
- `JuanCSUCoder/baxter_interface_2` - partial Humble C++ wrapper.
- `maxilar20/baxter_moveit_ros2` - older Galactic/bridge work.
- `dabaspark/baxter_sdk_nvidia_any_os` - Dockerized ROS 1/Kinetic/Classic Gazebo on modern Ubuntu, relevant as fallback/reference.

If you discover other active Baxter ROS 2/Jazzy/Harmonic repos, include them briefly and explain why they matter.

## Scoring Criteria

Score each repo from 0-5 on each criterion and give one short rationale per score:

- Completeness: packages/features covered, hardware support, sim support, messages/services/actions, MoveIt/config coverage.
- Maintenance: last commit date, recent issue/PR activity, maintainer responsiveness, release/deb/container evidence.
- Licensing: license present, compatibility with BSD-style Baxter SDK reuse, missing or ambiguous license risk.
- Jazzy compatibility: documented/tested Jazzy/Noble support, Harmonic support, build instructions, branch names, dependency freshness.
- Code quality: package structure, ROS 2 idioms, launch/config clarity, tests/CI, docs, minimal hacks.
- Adoption: stars, forks, open/closed issues, known lab/users, whether other repos depend on it.

Use this decision label for each repo:

- Adopt: likely base dependency with pinned SHA.
- Fork and customize: useful but needs project-specific fixes.
- Reference only: good ideas/configs but not safe to vendor directly.
- Skip: stale, incompatible, redundant, or too risky.

## Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S02 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S03 (Local Repo Detailed Analysis). Write a self-contained prompt for S03 that includes what S03 should do, the read-only Noetic repo path, the API surfaces to extract, the output file path, and the need to read S01 and S02 logs before starting.

## Rules

- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite URLs, commit dates, stars, forks, open/closed issue counts, detected license, and relevant version/branch names.
- Do not clone everything unless necessary; GitHub API and raw files are enough for most metadata.
- Flag missing licenses, untested Jazzy claims, and low-adoption repos clearly because they affect downstream design.
- Keep the result practical: later agents need adopt/fork/reference/skip decisions, not a full historical essay.
```

---

## S03: Local Repo Detailed Analysis

```
You are agent S03 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Perform a detailed read-only analysis of the local Noetic Baxter reference repository and extract the API surface that the ROS 2 Jazzy blueprint must preserve, replace, or deliberately drop. Do not implement code. This is a research/design planning step.

## Context

This is Step S03 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S04 bridge architecture, S05 simulation architecture, S06 MoveIt/ros2_control, S07 developer experience, and S08 package mapping.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Analyze

For every Noetic package in `baxter_noetic_ref/`, extract and summarize:

- Package name, path, build type, dependencies from `package.xml` / CMake / setup files.
- ROS topics published and subscribed, including message type and where found.
- ROS services provided and called, including service type and where found.
- ROS actions used or provided, especially `control_msgs/FollowJointTrajectory` usage and any actionlib patterns.
- Parameters read/written, dynamic reconfigure usage, launch arguments, environment variables, and namespace assumptions.
- Custom messages and services: full list by package, with fields summarized enough for S04/S08 mapping.
- Launch files, scripts, nodes, executables, and major user-facing commands.
- Hidden dependencies: `tf`, `tf2`, `cv_bridge`, OpenCV, Gazebo Classic plugins, controller APIs, MoveIt config files, robot enable/state assumptions, camera/gripper/head/navigator/IO assumptions.
- Simulation-only C++ and Gazebo Classic dependencies that should be replaced rather than ported.

For each package, decide:

- Preserve: required for minimum hardware or student workflows.
- Replace: better handled by community ROS 2 packages from S02 or by standard Jazzy packages.
- Simplify: keep only a smaller API/example subset.
- Drop: not worth carrying into the Jazzy plan.

Also estimate porting/planning effort per package as low, medium, or high, and give one short reason.

## Expected Package Coverage

Confirm and analyze all 17 Noetic packages, including at least:

- `baxter_common/baxter_common`
- `baxter_common/baxter_core_msgs`
- `baxter_common/baxter_description`
- `baxter_common/baxter_maintenance_msgs`
- `baxter_common/rethink_ee_description`
- `baxter/baxter_sdk`
- `baxter_interface`
- `baxter_tools`
- `baxter_examples`
- `baxter_moveit_config`
- `baxter_simulator/baxter_simulator`
- `baxter_simulator/baxter_gazebo`
- `baxter_simulator/baxter_sim_controllers`
- `baxter_simulator/baxter_sim_examples`
- `baxter_simulator/baxter_sim_hardware`
- `baxter_simulator/baxter_sim_io`
- `baxter_simulator/baxter_sim_kinematics`

## Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S03 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S04 (Bridge Architecture for Real Robot). Write a self-contained prompt for S04 that includes what S04 should do, the need to read S01-S03 logs first, bridge candidates from S02, API surfaces from S03, output file path, and safety/networking/action/QoS concerns.

## Rules

- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Do not implement ROS 2 code. This is planning only.
- Be specific: cite file paths and line/context where important.
- Use fast local search tools; do not manually inspect every file if grep/glob can extract the API surface.
- Keep the result practical: later agents need a package-by-package API map, effort estimates, and preserve/replace/simplify/drop decisions.
```

---

## S04: Bridge Architecture for Real Robot

```
You are agent S04 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Design the real-robot bridge architecture: how a ROS 2 Jazzy/Noble workstation communicates with Baxter's ROS 1 robot-side software while preserving the minimum hardware API needed by students. Do not implement code. This is a design/planning step only.

## Context

This is Step S04 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S07 developer experience, S08 package mapping, S09 risk register, S10 docs, and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify an API detail:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Bridge Candidates From S02

Evaluate and compare at least these bridge approaches:

- **ECN `CentraleNantesRobotics/baxter_common_ros2` / `baxter_bridge`**: mature BSD-3-Clause common stack with Baxter-specific bridge and publisher arbitration services. S03 found `BridgePublisher`, `BridgePublishersAuth`, and `BridgePublishersForce` in the local API surface.
- **ECN `CentraleNantesRobotics/baxter_legacy`**: ROS 1 Python 3 robot-side/debian workflow. Consider as robot-side packaging, not ROS 2 student API.
- **RethoughtRobotics `baxter-zenoh`**: new Docker/Zenoh bridge for Jazzy/Noble, low adoption but directly targets modern Ubuntu and high-rate topics.
- **RethoughtRobotics `BaxterSDK` / custom `ros1_bridge` fork**: reference for ROS 2 SDK/action choices, but verify before adopting.
- **Plain upstream `ros1_bridge`**: treat as unsupported on Ubuntu 24.04/Jazzy unless containerized or run on a separate supported machine; S01 confirmed upstream Noble/Jazzy is not supported.

## API Surface From S03 That The Bridge Must Address

Minimum hardware-critical API:

- Robot state/safety:
  - `robot/state` (`baxter_core_msgs/AssemblyState`)
  - `robot/set_super_enable` (`std_msgs/Bool`)
  - `robot/set_super_reset` (`std_msgs/Empty`)
  - `robot/set_super_stop` (`std_msgs/Empty`), safety-sensitive
- Arm state/control:
  - `/robot/joint_states` (`sensor_msgs/JointState`)
  - `/robot/limb/{left,right}/joint_command` (`baxter_core_msgs/JointCommand`)
  - `/robot/limb/{left,right}/set_speed_ratio` (`std_msgs/Float64`)
  - `/robot/limb/{left,right}/joint_command_timeout` (`std_msgs/Float64`)
  - `/robot/limb/{left,right}/endpoint_state` (`baxter_core_msgs/EndpointState`)
  - `ExternalTools/{left,right}/PositionKinematicsNode/IKService` (`baxter_core_msgs/SolvePositionIK`)
- Motion actions:
  - `/robot/limb/{left,right}/follow_joint_trajectory` (`control_msgs/FollowJointTrajectory`)
  - Decide whether to bridge ROS 1 actions directly, expose ROS 2 action shims, or command `JointCommand` topics directly.
- Grippers:
  - `robot/end_effector/{left,right}_gripper/command` (`baxter_core_msgs/EndEffectorCommand`)
  - `robot/end_effector/{left,right}_gripper/state` (`baxter_core_msgs/EndEffectorState`)
  - `robot/end_effector/{left,right}_gripper/properties` (`baxter_core_msgs/EndEffectorProperties`)
  - optional `/robot/end_effector/{side}_gripper/gripper_action` (`control_msgs/GripperCommand`)
- Cameras:
  - `/cameras/list`, `/cameras/open`, `/cameras/close` (`baxter_core_msgs` services)
  - at least one image stream such as `/cameras/head_camera/image` plus camera info if available
- Optional secondary API:
  - `/robot/head/command_head_pan`, `/robot/head/command_head_nod`, `/robot/head/head_state`, `/robot/head/head_action`
  - digital/analog IO, cuff/navigator, range sensors, `/robot/xdisplay`
  - maintenance/tare/calibration/update topics only if the target lab explicitly needs them

## Design Questions To Answer

For each bridge candidate, specify:

- What runs on the Baxter robot, bridge machine, student laptop, and/or Docker container.
- Which ROS 1 distro/environment is assumed on the robot side or bridge side.
- Whether students run one shared bridge, per-student bridge containers, or connect through a lab bridge host.
- Exact topic/service/action allowlist for minimum hardware mode.
- How `FollowJointTrajectory` works across the boundary.
- Whether `JointCommand` remains exposed to ROS 2 students or is hidden behind standard ROS 2 actions/classes.
- Whether camera streams are bridged raw, compressed, selectively enabled, or documented as optional due to bandwidth.
- Whether ECN bridge publisher arbitration is used for multi-student safety.
- How enable/reset/stop/estop flows are protected from accidental misuse.
- How QoS is assigned for latched/one-shot topics, high-rate joint states, actions, services, `/tf_static`, cameras, and command topics.
- How discovery/networking works with university IT constraints: host networking, firewall, multicast, DNS/`.local`, fixed IPs, Zenoh router if used, and Docker permissions.
- How bridge health is checked: required smoke tests before enabling robot motion.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S04 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S05 (Simulation Stack Architecture). Write a self-contained prompt for S05 that includes what S05 should do, the need to read S01-S04 logs first, community sim candidates from S02, local simulator replacement findings from S03, the bridge/hardware decisions from S04 that affect sim API parity, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite repository names, local file paths, topics/services/actions, and operational assumptions.
- Do not assume upstream `ros1_bridge` works on Jazzy/Noble.
- Treat robot enable/reset/stop and estop state as safety-critical.
- Keep the result practical: S07/S08 need a bridge architecture, allowlist, topology, and explicit default vs fallback choices.
```

---

## S05: Simulation Stack Architecture

```
You are agent S05 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Design the simulation stack architecture for Baxter on ROS 2 Jazzy, Ubuntu 24.04 Noble, Gazebo Harmonic, and ros2_control. Do not implement code. This is a design/planning step only.

## Context

This is Step S05 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S06 MoveIt 2 / ros2_control integration, S07 developer experience, S08 package mapping, S09 risk register, S10 docs, and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify simulator details:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Community Simulation Candidates From S02

Evaluate and compare at least these simulation-related sources:

- `angysof16/BaxterMotionPlanning`: primary modern reference for ROS 2 Jazzy + Gazebo Harmonic + ros2_control + MoveIt 2. S02 marked it reference-only because no license was detected and the latest commit mentioned IK uncertainty.
- `CentraleNantesRobotics/baxter_gz`: MIT-licensed Gazebo Sim / `ros_gz_bridge` experiment that preserves Baxter `JointCommand` semantics for joint commands and range sensors. Useful if sim/hardware API parity becomes more important than standard ROS 2 controller practice.
- `CentraleNantesRobotics/baxter_common_ros2`: source for ROS 2 Baxter messages, descriptions, end-effector descriptions, and ECN bridge context. Prefer its message/description packages over manual ports where possible.
- `bornaparo/baxter_moveit_config`: historical/partial ROS 2 MoveIt/Gazebo config; S02 said skip or reference only due stale/low-adoption/unlicensed status.
- `dabaspark/baxter_sdk_nvidia_any_os`: Dockerized ROS 1 Kinetic + Gazebo Classic fallback on modern Ubuntu. Treat only as emergency legacy reference, not the Jazzy simulation architecture.

If you discover a stronger active Jazzy/Harmonic Baxter simulator, include it briefly with evidence.

## Local Simulator Findings From S03

S03 found that the local Noetic simulator should be replaced, not line-by-line ported:

- All local C++ is under `baxter_noetic_ref/baxter_simulator/*` and depends on ROS 1 / Gazebo Classic APIs.
- `baxter_simulator/baxter_gazebo` builds `libbaxter_gazebo_ros_control.so` and uses Classic `gazebo_ros_control`.
- `baxter_simulator/baxter_sim_controllers` exports ROS 1 `controller_interface::ControllerBase` plugins: position, velocity, effort, head, and gripper controllers.
- `baxter_simulator/baxter_sim_hardware` provides a ROS 1 fake hardware emulator for state, display, grippers, IO, range, and enable/reset/stop behavior.
- `baxter_simulator/baxter_sim_kinematics` provides a KDL FK/IK node and `ExternalTools/{side}/PositionKinematicsNode/IKService` for the Classic simulator.
- `baxter_description` and `rethink_ee_description` geometry should be preserved, but Classic Gazebo tags, transmissions, and plugins need ROS 2 / Harmonic review.
- `baxter_sim_io`, old Qt IO simulator, Classic Gazebo spawn/delete demos, and project-specific pick-and-place scripts can be dropped or deferred unless the target course explicitly needs them.

## Bridge/Hardware Decisions From S04 That Affect Sim

S04 decided the real hardware path should use:

- ECN `baxter_bridge` as the default real-robot transport.
- ROS 2-side `control_msgs/action/FollowJointTrajectory` action shims above bridged `JointCommand` topics.
- Raw Baxter `JointCommand` still exposed in ROS 2 hardware mode for advanced/hardware-native labs.
- Standard ROS 2 actions/classes as the default beginner and MoveIt-facing path.
- Camera services plus one selective camera stream for hardware, not every stream by default.
- Safety/state topics such as `/robot/state` remain hardware-critical and should be represented in sim if practical.

For S05, decide how much simulation API parity is worth preserving:

- Default option likely: Gazebo Harmonic + `gz_ros2_control` + `joint_trajectory_controller` with standard `FollowJointTrajectory` controllers for arms.
- Optional compatibility option: a small ROS 2 shim that accepts Baxter `JointCommand` and forwards into ros2_control controllers, inspired by `CentraleNantesRobotics/baxter_gz`, only if course parity requires it.
- Do not let sim parity force a large rewrite of Baxter's old Classic controller stack.

## Design Questions To Answer

Specify:

- Which simulator architecture is the default: standard `ros2_control`/MoveIt 2, Baxter-native `JointCommand` compatibility, or two profiles.
- Which packages should exist in the future Jazzy workspace for simulation, and which community packages are adopted, forked, referenced, or skipped.
- How to preserve Baxter URDF/xacro geometry while replacing Classic Gazebo plugins/tags with Gazebo Harmonic/SDF/`ros_gz`/`gz_ros2_control` components.
- Which ros2_control hardware plugin/interface strategy to use in sim.
- Which controllers to use for arms, head, grippers, joint state broadcasting, and optional sensors.
- How `/robot/joint_states`, `/robot/state`, `/robot/limb/{side}/endpoint_state`, gripper state/properties, camera topics, and optional IK service should appear in sim.
- Whether the sim exposes `/robot/limb/{side}/joint_command`; if yes, whether it is a shim over `joint_trajectory_controller`, `forward_command_controller`, or a custom minimal node.
- How MoveIt 2 will connect to sim controllers and what should be deferred to S06.
- Which features are explicitly out of scope for first release: maintenance/tare/calibration/update, full IO/navigator simulation, old Classic spawn/delete demos, old Kinect/Xtion launch files, full camera fidelity, or full gripper physics.
- What smoke tests define a usable sim: launch Gazebo headless, robot spawned, joint states published, arm controller active, tiny trajectory succeeds, RViz/MoveIt sees robot, optional camera frame appears.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S05 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S06 (MoveIt 2 and ros2_control Integration). Write a self-contained prompt for S06 that includes what S06 should do, the need to read S01-S05 logs first, MoveIt/ros2_control decisions needed, bridge/hardware action decisions from S04, simulation decisions from S05, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite repository names, local paths, controllers, topics/services/actions, and operational assumptions.
- Do not plan a line-by-line Gazebo Classic port.
- Keep the result practical: S06/S07/S08 need a sim architecture, controller layout, package mapping influence, and explicit default vs optional compatibility choices.
```

---

## S06: MoveIt 2 and ros2_control Integration

```
You are agent S06 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Design the MoveIt 2 and ros2_control integration architecture for Baxter on ROS 2 Jazzy. Do not implement code. This is a design/planning step only.

## Context

This is Step S06 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S07 developer experience, S08 package mapping, S09 risk register, S10 docs, and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify MoveIt/controller details:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Prior Decisions To Carry Forward

From S04 hardware bridge architecture:

- Default real-robot transport is ECN `CentraleNantesRobotics/baxter_common_ros2` / `baxter_bridge` on one lab bridge host per Baxter.
- Hardware MoveIt-facing motion should use ROS 2-side `control_msgs/action/FollowJointTrajectory` action shims above bridged Baxter `/robot/limb/{side}/joint_command` topics.
- Raw Baxter `JointCommand` remains exposed in hardware mode for advanced/hardware-native labs, but standard ROS 2 actions/classes are the beginner and MoveIt-facing path.
- Hardware action names may be `/robot/limb/{left,right}/follow_joint_trajectory`, but S04 left open whether S06 should also expose MoveIt-style aliases.
- Hardware gripper/head actions are optional shims. Enable/reset/stop and `/robot/state` are safety-critical.

From S05 simulation architecture:

- Default sim is Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control`, not a line-by-line Gazebo Classic port.
- Sim arm controllers are `left_arm_controller` and `right_arm_controller`, both `joint_trajectory_controller/JointTrajectoryController` using `control_msgs/action/FollowJointTrajectory`.
- Sim also uses `joint_state_broadcaster`, optional `head_controller`, and simple `position_controllers/GripperActionController` for electric grippers if modeled.
- Sim should preserve Baxter legacy joint names (`left_s0`...`left_w2`, `right_s0`...`right_w2`) if technically possible. Do not inherit `angysof16/BaxterMotionPlanning` renamed joint names as the default without a deliberate decision.
- `/robot/joint_states` and `/robot/state` compatibility are useful in sim, but `/robot/limb/{side}/joint_command` is optional and disabled by default unless course parity requires it.
- `angysof16/BaxterMotionPlanning` is the best Jazzy/Harmonic/MoveIt 2 reference but is reference-only because no license was detected and latest work mentioned IK uncertainty.
- `CentraleNantesRobotics/baxter_common_ros2` is the adopted source for ROS 2 messages/descriptions where possible.

From S03 local repo analysis:

- Preserve MoveIt group concepts from the Noetic `baxter_moveit_config`: `left_arm`, `right_arm`, `both_arms`, `left_hand`, `right_hand`, neutral states, end effectors, and virtual world joint.
- Noetic MoveIt controller config used `/robot/limb/{right,left}/follow_joint_trajectory` with joints `right_s0`...`right_w2` and `left_s0`...`left_w2`.
- Noetic simulator and MoveIt 1 launch/plugin files should be replaced, not ported.

## Design Questions To Answer

Specify:

- Whether the project should regenerate a fresh MoveIt 2 config from the chosen ROS 2 Baxter description or adapt a community config by hand. Explain why.
- Which SRDF groups, end effectors, named states, passive/mimic joints, collision matrix assumptions, and virtual joints should exist.
- Which kinematics plugin(s) to use for Baxter's 7-DOF arms on Jazzy, and whether MoveIt Servo or custom IK services are in or out of first-release scope.
- How MoveIt 2 connects to simulation controllers from S05.
- How MoveIt 2 connects to hardware action shims from S04.
- Whether to use one controller config with launch-time substitutions/remaps or separate sim and hardware MoveIt controller YAML files.
- Exact proposed controller/action namespaces for sim and hardware, including whether aliases should make both profiles look the same to MoveIt.
- How `ros2_control` controller manager, controller spawner timing, lifecycle/activation ordering, and smoke tests should be represented in the plan.
- Whether grippers and head should be included in MoveIt 2 first release, and if so at what fidelity.
- Whether dual-arm planning/execution is first-release scope or documented as limited/experimental.
- How `/robot/joint_states` vs `/joint_states`, robot_state_publisher, TF frames, and planning scene updates should be handled.
- What should be deferred: custom `MoveArm` actions, torque/velocity controllers, full gripper physics, old Kinect/Xtion configs, warehouse/mongo, full object grasping, or hardware IK service parity.
- What smoke tests prove MoveIt/ros2_control is usable: load model, start controllers, plan one arm in RViz, execute tiny sim trajectory, connect to hardware action shim without moving, and validate joint names/controller names.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S06 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S07 (Developer Experience and Tooling). Write a self-contained prompt for S07 that includes what S07 should do, the need to read S01-S06 logs first, workspace/devcontainer/.repos decisions needed, launch profile naming, examples to prioritize, hardware/sim profiles, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, config files, controller names, action namespaces, MoveIt groups, joint names, and operational assumptions.
- Do not copy unlicensed community MoveIt config. Use unlicensed repos as references only.
- Do not plan a line-by-line MoveIt 1 port.
- Keep the result practical: S07/S08 need controller naming, launch profiles, sim/hardware differences, and explicit first-release vs deferred MoveIt scope.
```

---

## S07: Developer Experience and Tooling

```
You are agent S07 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Design the developer experience and tooling architecture for the future Baxter ROS 2 Jazzy workspace. Do not implement code. This is a design/planning step only.

## Context

This is Step S07 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S08 package mapping, S09 risk register, S10 docs, and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify old example/tool behavior:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Prior Decisions To Carry Forward

From S02:

- Adopt `CentraleNantesRobotics/baxter_common_ros2` as the likely pinned source for ROS 2 Baxter messages, descriptions, end-effector descriptions, and ECN bridge evaluation.
- Use `CentraleNantesRobotics/baxter_legacy` only as robot-side/bridge-host packaging reference if needed; verify licensing before vendoring.
- Keep `RethoughtRobotics/baxter-zenoh` as fallback/experimental, not default.
- Treat `angysof16/BaxterMotionPlanning` as reference-only because no license was detected.

From S04:

- Default real hardware topology is one ECN `baxter_bridge` lab bridge host per Baxter.
- Students should use standard ROS 2 actions/classes for beginner and MoveIt-facing workflows.
- Real hardware motion uses ROS 2 `control_msgs/action/FollowJointTrajectory` action shims above `/robot/limb/{side}/joint_command`.
- Hardware action names are canonical as `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory` per S06.
- Enable/reset/stop and `/robot/state` are safety-critical; bridge smoke tests are mandatory before motion.

From S05:

- Default sim is Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control`.
- Sim controllers are `left_arm_controller`, `right_arm_controller`, `joint_state_broadcaster`, optional `head_controller`, and optional electric gripper controllers.
- Sim should preserve Baxter legacy joint names if possible.
- `/robot/joint_states` and `/robot/state` compatibility are useful in sim; direct `JointCommand` sim support is optional and disabled by default.

From S06:

- Regenerate a fresh `baxter_moveit_config` for MoveIt 2.
- Use separate MoveIt controller YAMLs for sim and hardware.
- Sim MoveIt action names are `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
- Hardware MoveIt action names are `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- First-release MoveIt scope is one-arm planning/execution; `both_arms` exists but dual-arm execution is experimental.
- KDL is the first-release IK plugin; MoveIt Servo, IKFast/TRAC-IK, full grasping, and hardware IK-service parity are deferred.

## Design Questions To Answer

Specify the future developer experience architecture:

- Repository/workspace name recommendation and top-level layout.
- Colcon workspace layout: `src/`, `.repos` files, local packages, adopted community packages, bridge-host-only packages, and optional/fallback packages.
- `.repos` strategy: which repos are pinned by default, which are optional, whether to split into `baxter_core.repos`, `baxter_sim.repos`, `baxter_hardware.repos`, and `baxter_experimental.repos`, and how S08 should use those decisions.
- Devcontainer strategy for Ubuntu 24.04 Noble + ROS 2 Jazzy + Gazebo Harmonic + MoveIt 2 + ros2_control. Decide whether hardware bridge tooling belongs in the same devcontainer or a separate bridge-host setup.
- Docker/host-networking assumptions for sim, hardware bridge host, and fallback Zenoh path.
- rosdep/apt dependency groups to document conceptually, including `ros-jazzy-desktop`, MoveIt 2, `ros_gz`, `gz_ros2_control`, `ros2_controllers`, controller manager tools, RViz, xacro, and camera/CV utilities if needed.
- Launch profile naming and expected behavior. Include at least sim-only, sim+MoveIt, hardware bridge, hardware MoveIt, RViz/model-only, and smoke-test profiles.
- Environment setup strategy: avoid a ROS 1-style `baxter.sh` clone; prefer documented environment variables, launch args, `.env` examples, and clear bridge-host network setup.
- Hardware/sim profile naming that students can understand. Recommended names should distinguish `sim`, `sim_compat`, `hardware`, `hardware_moveit`, and fallback/experimental modes.
- Which 3-5 examples/tutorials to prioritize for first release. Include beginner-safe examples for sim and hardware.
- Smoke test command design for S08/S09/S10 to reference: build, model load, controller list, MoveIt plan, tiny sim trajectory, hardware bridge non-motion check, hardware action availability check.
- CI strategy: what can run in ordinary CI, what is allowed to be flaky/manual, and what requires real hardware.
- Developer quality tooling: formatting/linting/test policy, pre-commit or no pre-commit, minimal docs checks, and whether to keep it lightweight.
- How to present safety warnings and hardware enable flow without making examples dangerous.

## Launch Profile Names To Consider

Use or refine these names:

- `baxter_description.launch.py`: robot model + `robot_state_publisher`, no sim, no MoveIt.
- `sim.launch.py`: Gazebo Harmonic + ros2_control controllers, no MoveIt.
- `sim_moveit.launch.py`: Gazebo Harmonic + controllers + `move_group` + RViz.
- `sim_compat.launch.py`: optional Baxter `/robot/*` compatibility topics layered over standard sim.
- `hardware_bridge.launch.py`: ECN bridge-host profile and hardware allowlist, no MoveIt execution.
- `hardware_moveit.launch.py`: hardware bridge dependencies + action shims + MoveIt using hardware controller YAML.
- `moveit_rviz.launch.py`: model/MoveIt RViz only, fake or planning-only execution.
- `smoke_sim.launch.py` / CLI smoke script: headless sim/controller/model checks.
- `smoke_hardware.launch.py` / CLI smoke script: bridge non-motion checks.

## Examples To Prioritize

Pick 3-5 first-release examples. Suggested set:

- Sim: launch Baxter in Gazebo and move one arm through a tiny `FollowJointTrajectory` goal.
- Sim: plan and execute one arm in MoveIt/RViz to `left_neutral` or `right_neutral`.
- Hardware: bridge/state smoke test that reads `/robot/state`, `/robot/joint_states`, action availability, and camera/gripper availability without moving.
- Hardware: enable/disable or enable/status tool with explicit safety checks, not raw topic publishing.
- Hardware or sim: simple gripper open/close if electric grippers are confirmed.

Deprioritize broad Noetic example parity, raw torque/velocity demos, old joystick variants, full pick-place, full camera pipelines, and maintenance/tare/update tools unless the target course explicitly needs them.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S07_dev_experience_tooling.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S07 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S08 (Package Mapping and Dependency Graph). Write a self-contained prompt for S08 that includes what S08 should do, the need to read S01-S07 logs first, package mapping decisions needed, community package sources, sim/hardware/MoveIt package implications, dependency graph expectations, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, repo names, `.repos` files, launch names, controller/action names, example names, and operational assumptions.
- Do not vendor or copy unlicensed community code in the plan.
- Keep the result practical: S08 needs package names, source repos, workspace layout, launch profile names, and explicit default vs optional dependency choices.
```

---

## S08: Package Mapping and Dependency Graph

```
You are agent S08 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Finalize the package-by-package mapping and dependency graph for the future Baxter ROS 2 Jazzy workspace. Do not implement code. This is a design/planning step only.

## Context

This is Step S08 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S09 risk register, S10 documentation/distribution strategy, and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S07_dev_experience_tooling.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify package names, dependencies, topics, services, actions, launch files, or examples:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Prior Decisions To Carry Forward

From S02 community package audit:

- Adopt `CentraleNantesRobotics/baxter_common_ros2` as the likely pinned source for ROS 2 Baxter messages, descriptions, end-effector descriptions, and ECN bridge evaluation. Initial candidate SHA from S02: `678bfabea8c895b4134951a6c076217a90b9e0e6`, unless you justify a newer verified revision.
- Use `CentraleNantesRobotics/baxter_legacy` only as robot-side or bridge-host packaging reference if needed. Verify licensing before any vendoring/import recommendation.
- Keep `RethoughtRobotics/baxter-zenoh` and `RethoughtRobotics/BaxterSDK` as fallback/experimental/reference, not default.
- Treat `angysof16/BaxterMotionPlanning` as reference-only because no license was detected. Do not copy or vendor its code/config.
- Skip stale/partial direct dependencies such as `JuanCSUCoder/baxter_interface_2`, `maxilar20/baxter_moveit_ros2`, and `bornaparo/baxter_moveit_config`.

From S03 local Noetic analysis:

- Map all 17 Noetic packages explicitly:
  - `baxter_common/baxter_common`
  - `baxter_common/baxter_core_msgs`
  - `baxter_common/baxter_description`
  - `baxter_common/baxter_maintenance_msgs`
  - `baxter_common/rethink_ee_description`
  - `baxter/baxter_sdk`
  - `baxter_interface`
  - `baxter_tools`
  - `baxter_examples`
  - `baxter_moveit_config`
  - `baxter_simulator/baxter_simulator`
  - `baxter_simulator/baxter_gazebo`
  - `baxter_simulator/baxter_sim_controllers`
  - `baxter_simulator/baxter_sim_examples`
  - `baxter_simulator/baxter_sim_hardware`
  - `baxter_simulator/baxter_sim_io`
  - `baxter_simulator/baxter_sim_kinematics`
- Preserve Baxter custom messages/services, descriptions, key `/robot/*` hardware API, camera services, gripper interfaces, and `FollowJointTrajectory` intent.
- Replace the Gazebo Classic simulator and MoveIt 1 config rather than porting them line-by-line.
- Simplify `baxter_interface`, `baxter_tools`, and `baxter_examples` to the curated first-release subset.

From S04 bridge architecture:

- Default real-robot bridge is one ECN `baxter_bridge` lab bridge host per Baxter.
- Hardware motion uses ROS 2-side `control_msgs/action/FollowJointTrajectory` action shims above `/robot/limb/{side}/joint_command`.
- Hardware action names are canonical as `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- Hardware bridge should use a minimum allowlist. Do not bridge every Baxter topic by default.
- Enable/reset/stop and `/robot/state` are safety-critical; hardware smoke tests are mandatory before motion.

From S05 simulation architecture:

- Default sim is Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control`.
- Sim controllers are `joint_state_broadcaster`, `left_arm_controller`, `right_arm_controller`, optional `head_controller`, and optional electric gripper controllers.
- Preserve Baxter legacy joint names if possible: `left_s0`...`left_w2`, `right_s0`...`right_w2`.
- `/robot/joint_states` and `/robot/state` compatibility are useful in sim. Direct `JointCommand` sim support is optional and disabled by default.

From S06 MoveIt/ros2_control architecture:

- Regenerate a fresh `baxter_moveit_config` for MoveIt 2.
- Use separate MoveIt controller YAMLs for sim and hardware.
- Sim MoveIt action names are `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
- Hardware MoveIt action names are `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- First-release MoveIt scope is one-arm planning/execution. `both_arms` exists but dual-arm execution is experimental.
- KDL is the first-release IK plugin. MoveIt Servo, IKFast/TRAC-IK, full grasping, and hardware IK-service parity are deferred.

From S07 developer experience/tooling:

- Future repo/workspace name should be `baxter_ros2_jazzy`.
- Recommended layout includes `src/`, `repos/`, `.devcontainer/`, `docs/`, `examples/`, and smoke-test helpers.
- `.repos` files should be split as `repos/baxter_core.repos`, `repos/baxter_sim.repos`, `repos/baxter_hardware.repos`, and `repos/baxter_experimental.repos`.
- Default devcontainer is for Noble/Jazzy/Harmonic/MoveIt/sim/docs/builds. Hardware bridge tooling is a separate bridge-host setup.
- Launch profiles to map into packages include `baxter_description.launch.py`, `sim.launch.py`, `sim_moveit.launch.py`, `sim_compat.launch.py`, `hardware_bridge.launch.py`, `hardware_moveit.launch.py`, `moveit_rviz.launch.py`, `smoke_sim.launch.py`, and `smoke_hardware.launch.py`.
- First-release examples are `sim_tiny_trajectory`, `sim_moveit_neutral`, `hardware_bridge_smoke`, `hardware_enable_status`, and optional `gripper_open_close`.

## Design Questions To Answer

Produce a practical package map and dependency graph that S09/S10/S11 can consume. Specify:

- For each of the 17 Noetic packages, map it to one of: adopted ROS 2 package, new local ROS 2 package, simplified subset in another package, bridge-host-only package, reference-only source, dropped/deferred package, or external apt/rosdep dependency.
- For every future local package, state its package name, role, build type (`ament_cmake`, `ament_python`, config-only), source status, first-release priority, and main dependencies.
- For every adopted community package, state repo, package names, pinned source strategy, default vs optional profile, and licensing caveats.
- For every optional/fallback package, state why it is not in the default graph and which profile would pull it in.
- Define the dependency graph between local packages, adopted community packages, and external ROS/Gazebo/MoveIt/ros2_control packages.
- Separate dependency groups by profile: core/model, sim, sim compatibility, MoveIt, hardware bridge, hardware MoveIt, examples, smoke tests, experimental Zenoh.
- Map launch profiles from S07 to the packages that should own them.
- Map controller/action names from S05/S06 to the packages/config files that should define them.
- Map examples from S07 to their package home and dependencies.
- Identify packages that should be bridge-host-only and must not be required for ordinary sim CI.
- Identify packages that are intentionally not recreated: Classic Gazebo packages, Qt IO simulator, maintenance/tare/update workflows, broad Noetic example parity, old MoveIt 1 launch/plugin files.
- Provide S08-level guidance for `.repos` files: exact repo entries conceptually, which are default, optional, or experimental, and how they correspond to the dependency graph.
- Provide a text dependency graph and, if useful, a Mermaid graph. Keep it readable and profile-oriented.
- Define acceptance/smoke-test coverage per package group: build, model load, controller list, MoveIt plan, tiny sim trajectory, hardware non-motion check, hardware action availability check.

## Expected Future Package Names To Consider

Use or refine these names, but keep the graph small:

- Adopted from `CentraleNantesRobotics/baxter_common_ros2`:
  - `baxter_core_msgs`
  - `baxter_maintenance_msgs`
  - `baxter_description`
  - `rethink_ee_description`
  - `baxter_bridge` for hardware bridge profile
- New local packages likely needed:
  - `baxter_bringup`
  - `baxter_gz_sim`
  - `baxter_sim_compat` optional
  - `baxter_moveit_config`
  - `baxter_hardware_bridge`
  - `baxter_examples`
  - `baxter_smoke_tests` optional, or fold smoke tests into `baxter_bringup`/`baxter_examples` if that is simpler
- External ROS/Gazebo dependencies:
  - `ros_gz`, `gz_ros2_control`, `ros2_control`, `ros2_controllers`, `controller_manager`, `joint_state_broadcaster`, `joint_trajectory_controller`, `control_msgs`, `trajectory_msgs`, `sensor_msgs`, `diagnostic_msgs`, `tf2_ros`, `robot_state_publisher`, `xacro`, MoveIt 2 packages, RViz, `cv_bridge`, `image_transport` as needed.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S08_package_mapping.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S08 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S09 (Risk Register and Mitigation Strategies). Write a self-contained prompt for S09 that includes what S09 should do, the need to read S01-S08 logs first, risks to cover, dependency/package decisions from S08, acceptance criteria/go-no-go thresholds, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, repo names, `.repos` files, launch names, controller names, action names, and dependency edges.
- Do not vendor, copy, or recommend default imports of unlicensed community code.
- Keep the result practical: S09 needs package-specific risks, S10 needs documentation/package layout, and S11 needs a final dependency graph.
```

---

## S09: Risk Register and Mitigation Strategies

```
You are agent S09 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Create the project risk register and mitigation strategy for the future Baxter ROS 2 Jazzy workspace. Do not implement code. This is a design/planning step only.

## Context

This is Step S09 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S10 documentation/distribution strategy and S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S07_dev_experience_tooling.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S08_package_mapping.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify a risk detail:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Key S08 Package Decisions To Carry Forward

- Future repo/workspace name: `baxter_ros2_jazzy`.
- Default adopted community dependency: `CentraleNantesRobotics/baxter_common_ros2`, initially pinned to SHA `678bfabea8c895b4134951a6c076217a90b9e0e6` for `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, and hardware-profile `baxter_bridge`.
- First-release local packages: `baxter_bringup`, `baxter_gz_sim`, `baxter_moveit_config`, `baxter_hardware_bridge`, and `baxter_examples`.
- Optional local package: `baxter_sim_compat` for `/robot/*` sim compatibility and optional safe position-only `JointCommand` shim.
- Do not create `baxter_smoke_tests` by default; fold smoke checks into bringup/sim/hardware packages unless implementation grows.
- Bridge-host-only packages/sources: ECN `baxter_bridge`, local `baxter_hardware_bridge`, optional `baxter_legacy` after license verification, and experimental `baxter-zenoh`/`BaxterSDK`.
- Default sim: Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control` controllers.
- Sim action names: `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
- Hardware action names: `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- MoveIt 2 config is regenerated locally; first-release MoveIt scope is one-arm planning/execution with KDL and OMPL.
- Direct sim `JointCommand`, maintenance workflows, Classic Gazebo packages, Qt IO sim, broad Noetic example parity, old MoveIt 1 launch/plugin files, and native real-Baxter `ros2_control` hardware interface are deferred or intentionally not recreated.

## Risks To Cover

Build a practical risk register with likelihood, impact, owner/profile, mitigation, detection method, and go/no-go threshold. Cover at least:

- Hardware bridge risks: ECN `baxter_bridge` installability on the selected bridge host, ROS 1 dependency availability, target robot firmware mismatch, bridge topic/service gaps, ECN arbitration behavior, and broad allowlist mistakes.
- Hardware safety risks: enable/reset/stop misuse, stale commands, action-shim cancellation behavior, e-stop/error state handling, raw `JointCommand` exposure, speed ratio/timeout defaults, and multi-student command ownership.
- Motion/action risks: ROS 2 action shim correctness, `FollowJointTrajectory` timing/feedback, joint-name validation, MoveIt hardware controller YAML compatibility with `/robot/limb/{side}` names, and hardware motion go/no-go criteria.
- QoS/network risks: DDS discovery blocked by university networks, multicast/firewall issues, camera/high-rate joint-state bandwidth, `/tf_static` durability, QoS mismatch causing silent data loss, and Docker/host networking restrictions.
- Simulation risks: Gazebo Harmonic instability in CI, missing meshes, ECN description name mismatches, `gz_ros2_control` controller startup ordering, controller tuning, gripper/head optionality, camera sensor fragility, and sim/hardware API divergence.
- MoveIt risks: regenerated SRDF collision mistakes, KDL IK failures for Baxter's 7-DOF arms, stale or mismatched joint limits, `both_arms` overpromising, RViz/fake-controller vs executable sim differences, and deferred gripper/grasping expectations.
- Dependency/package risks: low adoption of all community repos, pinned SHA drift, `baxter_common_ros2` package/API gaps, Python 3.12 compatibility, ROS/Gazebo/MoveIt version churn, rosdep/apt availability, and local package split becoming too large.
- Licensing risks: unlicensed `angysof16/BaxterMotionPlanning`, `baxter_legacy`, `dabaspark/baxter_sdk_nvidia_any_os`, stale unlicensed MoveIt repos, and accidental copying/vendor recommendations.
- Documentation/distribution risks: users confusing sim support with safe hardware support, unclear bridge-host setup, stale `.repos` pins, missing compatibility matrix, and external labs assuming official vendor support.
- Maintenance risks: bus factor, hardware aging, no official Baxter ROS 2 support, CI maintenance, bridge-host ops knowledge, and university handoff after graduation.
- Fallback risks: Zenoh path low adoption, IT acceptance, restricted topic YAML requirement, and when to switch from ECN bridge to Zenoh.

## Acceptance Criteria And Go/No-Go Thresholds To Define

For each major profile, define concrete acceptance criteria and release gates:

- Core/model: build succeeds, model loads, meshes resolve, legacy joint names present.
- Sim: headless `sim.launch.py` starts, Baxter spawns, controllers active, `/joint_states` publishes all arm joints.
- MoveIt: SRDF loads, KDL plugin loads, one-arm plan succeeds, tiny sim execution succeeds.
- Sim compatibility: `/robot/joint_states` and `/robot/state` publish if enabled; optional `JointCommand` shim rejects unsafe modes.
- Hardware bridge non-motion: `/robot/state`, `/robot/joint_states`, camera/IK/gripper services, and both hardware action names are visible without enabling or moving the robot.
- Hardware safety: no launch auto-enables robot; enable/status tool prints state and requires explicit operator confirmation; action shims reject unsafe state.
- Hardware motion: decide whether first release requires only non-motion/action availability or one supervised tiny low-speed trajectory; define the threshold clearly.
- CI: default CI must not require hardware, ROS 1 master, `baxter_legacy`, Zenoh, or broad camera streams.
- Licensing: no default `.repos` entry or copied config from unlicensed sources unless license is added/verified.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S09_risk_register.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S09 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S10 (Documentation and Distribution Strategy). Write a self-contained prompt for S10 that includes what S10 should do, the need to read S01-S09 logs first, documentation audiences, package/profile decisions from S08, risk/acceptance decisions from S09, release/distribution strategy, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, repo names, `.repos` files, launch names, controller/action names, smoke tests, and risk thresholds.
- Do not recommend vendoring or copying unlicensed community code.
- Keep the result practical: S10 needs documentation requirements and S11 needs final go/no-go criteria.
```

---

## S10: Documentation and Distribution Strategy

```
You are agent S10 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Design the documentation and distribution strategy for the future Baxter ROS 2 Jazzy workspace. Do not implement code. This is a design/planning step only.

## Context

This is Step S10 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output feeds S11 final synthesis.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S07_dev_experience_tooling.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S08_package_mapping.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S09_risk_register.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify a documentation detail:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Documentation Audiences

Design documentation for these audiences:

- New students who need a 15-minute sim-first onboarding path.
- Instructors and lab admins who operate the real Baxter bridge host.
- External labs evaluating whether this stack fits their Baxter robot.
- Sim-only users who do not own hardware.
- Contributors and maintainers who need package layout, dependency pin, CI, release, and handoff guidance.

## Package And Profile Decisions To Carry Forward From S08

- Future repo/workspace name: `baxter_ros2_jazzy`.
- Default adopted community dependency: `CentraleNantesRobotics/baxter_common_ros2`, initially pinned to SHA `678bfabea8c895b4134951a6c076217a90b9e0e6` for `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, and hardware-profile `baxter_bridge`.
- First-release local packages: `baxter_bringup`, `baxter_gz_sim`, `baxter_moveit_config`, `baxter_hardware_bridge`, and `baxter_examples`.
- Optional local package: `baxter_sim_compat` for `/robot/*` sim compatibility and optional safe position-only `JointCommand` shim.
- Do not create `baxter_smoke_tests` by default; fold smoke checks into bringup/sim/hardware packages unless implementation grows.
- Bridge-host-only packages/sources: ECN `baxter_bridge`, local `baxter_hardware_bridge`, optional `baxter_legacy` after license verification, and experimental `baxter-zenoh`/`BaxterSDK`.
- Default sim: Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control` controllers.
- Sim action names: `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
- Hardware action names: `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- MoveIt 2 config is regenerated locally; first-release MoveIt scope is one-arm planning/execution with KDL and OMPL.
- Direct sim `JointCommand`, maintenance workflows, Classic Gazebo packages, Qt IO sim, broad Noetic example parity, old MoveIt 1 launch/plugin files, and native real-Baxter `ros2_control` hardware interface are deferred or intentionally not recreated.

## Risk And Acceptance Decisions To Carry Forward From S09

- Hardware bridge support and hardware motion support are separate release claims.
- A first release may support hardware bridge non-motion checks after the hardware bridge gate passes.
- Hardware motion must not be advertised until a supervised tiny low-speed trajectory passes for each advertised arm, with feedback, cancel/hold behavior, and safe `/robot/state` gating.
- Default CI must not require hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams.
- Default `.repos` files must not include unlicensed sources. `angysof16/BaxterMotionPlanning`, `baxter_legacy`, `dabaspark/baxter_sdk_nvidia_any_os`, and stale unlicensed MoveIt repos remain reference-only until license verification changes that status.
- S10 docs must make support levels visible: supported core/model, supported sim after smoke, supported MoveIt sim after smoke, optional sim compatibility, hardware bridge non-motion, supervised hardware motion, and experimental Zenoh fallback.
- Safety docs must not normalize raw `ros2 topic pub /robot/set_super_enable`, `/robot/set_super_reset`, or `/robot/set_super_stop` commands for beginners.
- S09 split unresolved items into an immediate/deferred validation backlog. S10 must carry the deferred items into the compatibility matrix, release notes, hardware setup guide, and maintainer handoff docs instead of presenting them as solved.

## Design Questions To Answer

Define the future documentation and distribution architecture:

- README structure, badges, and first-screen mode selector for `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, and `experimental_zenoh`.
- Documentation tree under `docs/`, including getting started, sim guide, MoveIt guide, hardware bridge-host setup, hardware safety, examples, troubleshooting, package map, compatibility matrix, licensing/third-party sources, CI/release checklist, and maintainer handoff.
- The 15-minute onboarding path for a new student using the default devcontainer and sim profile.
- Hardware bridge-host guide for instructors/lab admins, including robot LAN, `ROS_MASTER_URI`, `ROS_IP`, `ROS_DOMAIN_ID`, ECN arbitration, restricted allowlist, smoke checks, and no auto-enable rule.
- Hardware safety guide, including physical checklist, e-stop expectations, enable/status tool behavior, action-shim unsafe-state rejection, command timeout/speed ratio defaults, and multi-student ownership.
- Compatibility matrix format, including Ubuntu 24.04 Noble, ROS 2 Jazzy, Gazebo Harmonic, MoveIt 2, ECN `baxter_common_ros2` pinned SHA, tested RMW, bridge-host status, hardware robot status, camera/gripper support, and experimental Zenoh status.
- Validation backlog format for unresolved items: target Baxter ROS 1 graph, ECN bridge installability, DDS/IT policy, Zenoh acceptance, gripper/camera inventory, ECN description joint names, unlicensed repo status, headless Gazebo CI stability, MoveIt hardware action-name compatibility, course need for sim `JointCommand`, and maintainer ownership.
- `.repos` documentation for `repos/baxter_core.repos`, `repos/baxter_sim.repos`, `repos/baxter_hardware.repos`, and `repos/baxter_experimental.repos`, including pin update policy and license gates.
- Relationship to the Noetic repo and community sources: explain what is adopted, referenced, skipped, or intentionally not recreated.
- Release and distribution strategy: version tags, release notes, tested profile table, known risks/open questions, issue templates, contribution guide, support policy, security policy, and whether rosdistro inclusion is realistic.
- Decide whether to pursue rosdistro inclusion for message packages now, later, or not at all. Be explicit that first release should likely use source `.repos` rather than promising bloom/apt packages.
- Issue template design for sim bug, hardware bridge bug, docs issue, safety concern, dependency pin update, and feature request.
- How S11 should present final go/no-go criteria and documentation requirements.

## Required Output

Write your findings to:

- `~/baxter_ros2_jazzy_plan/logs/S10_docs_distribution.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S10 status line from `pending` to `completed`.

Then append your prompt-for-the-next-agent to:

- `~/baxter_ros2_jazzy_plan/PROMPTS.md`

The next step is S11 (Final Synthesis). Write a self-contained prompt for S11 that includes what S11 should do, the need to read S01-S10 logs first, final blueprint structure, architecture/package/profile decisions, risk/release gates, docs/distribution strategy, open questions, and the output file path.

## Rules

- Do not implement ROS 2 code. This is planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, repo names, `.repos` files, launch names, controller/action names, smoke tests, support labels, and release gates.
- Do not recommend vendoring or copying unlicensed community code.
- Do not imply official Baxter vendor support or native ROS 2 firmware migration.
- Keep the result practical: S11 needs a documentation/distribution plan it can fold directly into the final blueprint.
```

---

## S11: Final Synthesis

```
You are agent S11 for the Baxter ROS 2 Jazzy planning project.

## Your Task

Produce the final comprehensive migration blueprint for the future `baxter_ros2_jazzy` workspace. This is the synthesis step for the whole planning process. Do not implement code. Consolidate S01-S10 into one actionable reference document that can guide later implementation.

## Context

This is Step S11 of an 11-step planning process for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. The project produces a planning blueprint only, no implementation. Your output is the primary handoff artifact.

## Read First

Read these files before starting:

- `~/baxter_ros2_jazzy_plan/EXISTING_RESEARCH.md`
- `~/baxter_ros2_jazzy_plan/logs/S01_validate_assumptions.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S02_audit_community_packages.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S03_local_repo_analysis.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S04_bridge_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S05_simulation_architecture.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S06_moveit_ros2_control.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S07_dev_experience_tooling.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S08_package_mapping.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S09_risk_register.log.md`
- `~/baxter_ros2_jazzy_plan/logs/S10_docs_distribution.log.md`
- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Use the Noetic reference repository only as read-only source material if you need to verify a detail:

- `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`

## Final Blueprint Structure

Write the final blueprint as a single consolidated document with these sections:

1. Executive summary and scope boundary.
2. Final recommendation: hybrid Jazzy workspace, standard Harmonic sim, ECN bridge-host hardware path, no native ROS 2 Baxter firmware migration.
3. Architecture overview with a text or Mermaid diagram showing student workstation/devcontainer, sim stack, MoveIt 2, bridge host, Baxter ROS 1 robot, and experimental Zenoh fallback.
4. Profile definitions and support levels: `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, `sim_compat`, and `experimental_zenoh`.
5. Package map and dependency graph from S08.
6. Real hardware bridge architecture from S04.
7. Simulation architecture from S05.
8. MoveIt 2 and `ros2_control` architecture from S06.
9. Developer experience, launch profiles, examples, devcontainer, `.repos`, and CI from S07/S08.
10. Documentation and distribution strategy from S10.
11. Risk register summary and release gates from S09.
12. Phased implementation roadmap.
13. Compatibility matrix and deferred validation backlog.
14. Open questions requiring user/university decisions.
15. Final go/no-go criteria.

## Architecture And Package Decisions To Carry Forward

- Future repo/workspace name: `baxter_ros2_jazzy`.
- Default adopted community dependency: `CentraleNantesRobotics/baxter_common_ros2`, initially pinned to full SHA `678bfabea8c895b4134951a6c076217a90b9e0e6`.
- Adopted packages from ECN common: `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, and hardware-profile `baxter_bridge`.
- First-release local packages: `baxter_bringup`, `baxter_gz_sim`, `baxter_moveit_config`, `baxter_hardware_bridge`, and `baxter_examples`.
- Optional local package: `baxter_sim_compat` for `/robot/*` sim compatibility and optional safe position-only `JointCommand` shim.
- Do not create `baxter_smoke_tests` by default; fold smoke checks into bringup/sim/hardware packages unless implementation grows.
- Bridge-host-only sources: ECN `baxter_bridge`, local `baxter_hardware_bridge`, optional `baxter_legacy` after license verification, and experimental `baxter-zenoh`/`BaxterSDK`.
- Default sim: Gazebo Harmonic + `ros_gz` + `gz_ros2_control` + standard `ros2_control` controllers.
- Sim action names: `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`.
- Hardware action names: `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`.
- MoveIt 2 config is regenerated locally; first-release MoveIt scope is one-arm planning/execution with KDL and OMPL.
- Direct sim `JointCommand`, maintenance workflows, Classic Gazebo packages, Qt IO sim, broad Noetic example parity, old MoveIt 1 launch/plugin files, and native real-Baxter `ros2_control` hardware interface are deferred or intentionally not recreated.

## Risk And Release Gates To Carry Forward

- Hardware bridge support and hardware motion support are separate release claims.
- A first release may support hardware bridge non-motion checks after the hardware bridge gate passes.
- Hardware motion must not be advertised until a supervised tiny low-speed trajectory passes for each advertised arm, with feedback, cancel/hold behavior, and safe `/robot/state` gating.
- Default CI must not require hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams.
- Default `.repos` files must not include unlicensed sources. `angysof16/BaxterMotionPlanning`, `baxter_legacy`, `dabaspark/baxter_sdk_nvidia_any_os`, and stale unlicensed MoveIt repos remain reference-only until license verification changes that status.
- Safety docs must not normalize raw `ros2 topic pub /robot/set_super_enable`, `/robot/set_super_reset`, or `/robot/set_super_stop` commands for beginners.
- Support labels must remain visible: supported core/model, supported sim after smoke, supported MoveIt sim after smoke, optional sim compatibility, hardware bridge non-motion, supervised hardware motion, and experimental Zenoh fallback.

## Documentation And Distribution Strategy To Carry Forward

- README starts with badges, scope warning, and a mode selector for `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, and `experimental_zenoh`.
- Documentation tree includes `getting_started_sim`, `simulation`, `moveit_guide`, `hardware_bridge_setup`, `hardware_safety`, `examples`, `troubleshooting`, `package_map`, `compatibility_matrix`, `repos_and_pins`, `licensing_and_sources`, `ci_release_checklist`, `maintainer_handoff`, and `experimental_zenoh`.
- 15-minute onboarding is sim-first using the default devcontainer, `repos/baxter_core.repos`, `colcon build`, `sim.launch.py headless:=true`, and `sim_tiny_trajectory`.
- Hardware bridge-host docs must cover robot LAN, `ROS_MASTER_URI`, `ROS_IP`, `ROS_DOMAIN_ID`, ECN arbitration, restricted allowlist, smoke checks, and no auto-enable.
- Compatibility matrix must include Ubuntu 24.04 Noble, ROS 2 Jazzy, Gazebo Harmonic, MoveIt 2, ECN pinned SHA, tested RMW, bridge-host status, hardware robot status, camera/gripper support, and experimental Zenoh status.
- First release should use source `.repos`, not promise bloom/apt packages.
- Rosdistro inclusion is later only, likely message/description packages first, after CI, licensing, and maintainer ownership are stable.
- Issue templates should cover sim bug, hardware bridge bug, docs issue, safety concern, dependency pin update, and feature request.

## Open Questions To Preserve

Carry forward unresolved items explicitly rather than presenting them as solved:

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
- Docs hosting target and future repository license.

## Required Output

Write the final synthesis to:

- `~/baxter_ros2_jazzy_plan/logs/S11_final_synthesis.log.md`

Use the YAML+Markdown format already in that file. Fill in `agent_date`, set `status` to `completed`, and fill all sections: Task, Findings, Decisions, Open Questions, Artifacts.

Then update the step status in:

- `~/baxter_ros2_jazzy_plan/MASTER_PLAN.md`

Change the S11 status line from `pending` to `completed`.

No next-agent prompt is required after S11. Instead, in Artifacts, state that the planning sequence is complete.

## Rules

- Do not implement ROS 2 code. This is synthesis/planning only.
- Read-only on `~/baxter_ros2_jazzy_plan/baxter_noetic_ref/`; never modify it.
- Only modify files inside `~/baxter_ros2_jazzy_plan/`.
- Be specific: cite package names, repo names, `.repos` files, launch names, controller/action names, smoke tests, support labels, and release gates.
- Do not recommend vendoring or copying unlicensed community code.
- Do not imply official Baxter vendor support or native ROS 2 firmware migration.
- Keep the final blueprint practical and implementation-ready, not a historical essay.
```
