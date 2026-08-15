---
step: S07
title: "Developer Experience and Tooling"
agent_date: 2026-06-18
status: completed
previous_steps: [S04, S05, S06]
---

# S07: Developer Experience and Tooling

## Task

Designed the developer experience and tooling architecture for the future Baxter ROS 2 Jazzy workspace. This step is design-only: no ROS 2 packages, launch files, devcontainer files, or scripts were implemented.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `logs/S04_bridge_architecture.log.md`
- `logs/S05_simulation_architecture.log.md`
- `logs/S06_moveit_ros2_control.log.md`
- `MASTER_PLAN.md`

No changes were made to `baxter_noetic_ref/`.

## Findings

### Executive Summary

The future implementation should be a small, clearly profiled ROS 2 workspace named **`baxter_ros2_jazzy`**. The student default should be a standard Jazzy development environment for simulation, MoveIt 2, examples, and documentation. Real hardware tooling should be treated as a separate bridge-host profile because the ECN `baxter_bridge` path owns robot networking, ROS 1 dependencies, command arbitration, and safety checks.

The developer experience should not recreate the ROS 1 `baxter.sh` model. Use documented launch arguments, `.env` examples, per-profile `.repos` files, and explicit bridge-host network setup. The first release should optimize for a 15-minute sim onboarding path and a supervised hardware checklist, not broad Noetic example parity.

| Area | Recommended Default | Reason |
|---|---|---|
| Repository name | `baxter_ros2_jazzy` | Searchable, distro-specific, honest about scope. |
| Default workspace | Colcon workspace with `src/`, `repos/`, `.devcontainer/`, `docs/`, `examples/`, `smoke_tests/` | Familiar ROS 2 layout with clear planning for S08 package mapping. |
| Core dependency source | Pinned `CentraleNantesRobotics/baxter_common_ros2` | S02 default for messages, descriptions, end-effector descriptions, and ECN bridge evaluation. |
| Default devcontainer | Ubuntu 24.04 Noble + ROS 2 Jazzy + Gazebo Harmonic + MoveIt 2 + ros2_control | Supports sim, MoveIt, docs, and ordinary CI. |
| Hardware bridge setup | Separate bridge-host setup, not the default student devcontainer | Hardware bridge needs robot LAN, ROS 1 support deps, arbitration, and safety procedures. |
| Fallback bridge | Experimental Zenoh profile only | Useful if ECN bridge/high-rate transport fails, but low adoption and extra IT risk. |
| Examples | 3-5 curated safe examples | Better than porting every old Noetic example. |

### Repository And Top-Level Layout

Recommended repository name: **`baxter_ros2_jazzy`**.

Reasoning:

- It is explicit enough for external users searching for Baxter + ROS 2 + Jazzy.
- It avoids implying official vendor support or native robot firmware migration.
- It leaves room for a future `baxter_ros2_kilted` or generic `baxter_ros2` after the Jazzy stack is proven.

Recommended top-level layout for the future implementation repo:

| Path | Purpose |
|---|---|
| `README.md` | Short mode selector: sim, sim+MoveIt, real hardware, bridge host, experimental Zenoh. |
| `docs/` | Getting started, sim guide, hardware guide, bridge-host setup, safety, troubleshooting, package map. |
| `.devcontainer/` | Standard student/sim development container for Noble/Jazzy/Harmonic. |
| `repos/` | Version-control import files: core, sim, hardware, experimental. |
| `src/` | Local packages and imported source repos after `vcs import`. |
| `examples/` | First-release student examples and tutorial packages/scripts. |
| `smoke_tests/` or `scripts/smoke/` | CLI smoke checks for build/model/sim/controller/MoveIt/hardware non-motion checks. |
| `scripts/` | Thin helper commands for workspace setup and smoke orchestration only. |
| `.github/workflows/` | Future CI for build/lint/docs/model/fake or headless checks. |
| `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md` | Distribution hygiene; S10 owns final docs strategy. |

Do not create a top-level shell equivalent of ROS 1 `baxter.sh`. If helper scripts exist, they should call documented ROS 2 commands, not hide network state or mutate global shell behavior.

### Colcon Workspace Layout

Recommended workspace structure:

```text
baxter_ros2_jazzy/
  repos/
    baxter_core.repos
    baxter_sim.repos
    baxter_hardware.repos
    baxter_experimental.repos
  src/
    baxter_common_ros2/              # imported, default core dependency
    baxter_bringup/                  # local future package: shared launch/profile entry points
    baxter_gz_sim/                   # local future package: Harmonic sim launch/world/controllers
    baxter_sim_compat/               # local optional future package: /robot/* sim compatibility
    baxter_moveit_config/            # local regenerated MoveIt 2 config
    baxter_hardware_bridge/          # local future package: action shims, bridge-host launch, safe tools
    baxter_examples/                 # local curated ROS 2 examples
    baxter_smoke_tests/              # local smoke test commands, if kept as a package
```

S08 should treat this as a planning layout, not a mandate to create all packages immediately. The minimum first implementation can collapse `baxter_smoke_tests` into `baxter_examples` or `baxter_bringup` if that keeps the tree smaller.

Package role guidance for S08:

| Future Package | Source | Default? | Role |
|---|---|---:|---|
| `baxter_core_msgs` | `CentraleNantesRobotics/baxter_common_ros2` | Yes | Baxter custom messages/services. |
| `baxter_maintenance_msgs` | `CentraleNantesRobotics/baxter_common_ros2` | Yes as dependency, low student priority | Required if adopted common repo includes it; maintenance workflows remain out of beginner docs. |
| `baxter_description` | `CentraleNantesRobotics/baxter_common_ros2` plus local patches if needed | Yes | Robot model for RViz, MoveIt, sim, bridge host. |
| `rethink_ee_description` | `CentraleNantesRobotics/baxter_common_ros2` | Yes | End-effector geometry. |
| `baxter_bridge` | `CentraleNantesRobotics/baxter_common_ros2` | Hardware profile only | ECN bridge host. |
| `baxter_bringup` | New local | Yes | Launch profile aggregation and shared params. |
| `baxter_gz_sim` | New local | Sim profile | Gazebo Harmonic, ros_gz, controller YAML, worlds. |
| `baxter_sim_compat` | New local, optional | Optional | `/robot/joint_states`, `/robot/state`, optional safe `JointCommand` shim. |
| `baxter_moveit_config` | New regenerated local | MoveIt profiles | MoveIt 2 config with separate sim/hardware controller YAMLs. |
| `baxter_hardware_bridge` | New local | Hardware profile | ROS 2 action shims, safe enable/status tools, hardware smoke checks. |
| `baxter_examples` | New local | Yes | Curated beginner-safe tutorials. |

### `.repos` Strategy

Use split `.repos` files under `repos/` so S08 can express default vs optional dependency graphs without inventing package groups later.

Recommended files:

| File | Included Repos | Default Use |
|---|---|---|
| `repos/baxter_core.repos` | `CentraleNantesRobotics/baxter_common_ros2` pinned to a known SHA; future local repo itself is already checked out and not listed. | Always imported for sim, MoveIt, and hardware. |
| `repos/baxter_sim.repos` | No unlicensed sim repo by default. May include only licensed helper repos if future validation finds any. | Optional after core; primarily documents that sim packages are local. |
| `repos/baxter_hardware.repos` | `CentraleNantesRobotics/baxter_common_ros2` if not already imported; optionally `CentraleNantesRobotics/baxter_legacy` only as bridge-host packaging reference after license verification. | Bridge-host setup only. |
| `repos/baxter_experimental.repos` | `RethoughtRobotics/baxter-zenoh`, `RethoughtRobotics/BaxterSDK`, possibly `CentraleNantesRobotics/baxter_gz`; do not import by default. | Experimental/fallback only. |

Pinning rules:

- Pin all external repos to explicit SHAs, not branch names.
- Use S02's likely `baxter_common_ros2` SHA `678bfabea8c895b4134951a6c076217a90b9e0e6` as the initial candidate unless S08/S11 chooses a newer verified revision.
- Do not vendor or copy `angysof16/BaxterMotionPlanning` unless an explicit license is added. It remains reference-only.
- Do not import unlicensed `dabaspark/baxter_sdk_nvidia_any_os` or `bornaparo/baxter_moveit_config` into any default `.repos` file.
- Keep `baxter_legacy` out of the student default until license and bridge-host packaging decisions are resolved.

Expected user flows:

```bash
vcs import src < repos/baxter_core.repos
vcs import src < repos/baxter_sim.repos          # optional; likely small/no-op initially
vcs import src < repos/baxter_hardware.repos     # bridge host only
vcs import src < repos/baxter_experimental.repos # explicit fallback experiments only
```

### Devcontainer Strategy

Use one default devcontainer for student development, simulation, MoveIt, docs, and CI parity:

| Layer | Recommendation |
|---|---|
| Base OS | Ubuntu 24.04 Noble. |
| ROS | ROS 2 Jazzy, prefer `ros-jazzy-desktop` or a project image derived from it. |
| Gazebo | Gazebo Harmonic with ROS integration packages. |
| Planning/control | MoveIt 2, `ros2_control`, `ros2_controllers`, `gz_ros2_control`. |
| Graphics | RViz, Gazebo GUI support through host X11/Wayland/GPU docs, but headless mode must work. |
| Build tools | `colcon`, `vcstool`, `rosdep`, `ament_lint` tools, Python tooling already used by ROS 2. |
| Camera/CV | `cv_bridge`, `image_transport`, OpenCV utilities if camera examples are included. |

Do **not** put the default hardware bridge stack inside the ordinary student devcontainer. The ECN bridge-host profile needs robot LAN access, ROS 1 support dependencies, bridge arbitration, and instructor-controlled safety procedures. Mixing that into the default devcontainer makes onboarding easier for the wrong thing.

Recommended split:

| Environment | Intended User | Includes |
|---|---|---|
| Default devcontainer | Students and contributors | Core messages/descriptions, sim, MoveIt, examples, smoke tests, docs tooling. |
| Bridge-host setup | Instructor/lab machine | ECN `baxter_bridge`, ROS 1 support packages/debs/container as needed, hardware action shims, safe enable/status tools, bridge smoke checks. |
| Experimental Zenoh setup | Advanced maintainer only | `baxter-zenoh`, `rmw_zenoh_cpp`, host networking, Zenoh router, restricted topic YAML. |

### Docker And Networking Assumptions

Simulation:

- Default devcontainer can run sim with `--network=host` if needed for ROS 2 discovery between host GUI tools and container nodes.
- Headless CI should not require GPU, Gazebo GUI, or host display forwarding.
- Students should be able to run `sim.launch.py headless:=true` inside the devcontainer.

Hardware ECN bridge:

- Prefer a bridge host installed/configured by the lab, not per-student containers.
- Bridge host has wired robot LAN access, fixed robot-facing IP, explicit `ROS_MASTER_URI`/`ROS_IP` for the ROS 1 side, and one `ROS_DOMAIN_ID` per Baxter bench for the ROS 2 side.
- Student laptops either SSH into the bridge host/devcontainer or join a controlled lab ROS 2 network. Do not promise arbitrary campus Wi-Fi DDS discovery.
- `hardware_bridge.launch.py` and `hardware_moveit.launch.py` should be described as bridge-host launches unless the lab explicitly validates remote student execution.

Fallback Zenoh:

- Requires Docker host networking or equivalent network privileges, `rmw_zenoh_cpp`, a Zenoh router, and IT approval for ports such as `7447`.
- Keep it behind names like `experimental_zenoh` or `hardware_zenoh`, never `hardware`.
- Restrict broad bridge topic YAMLs before student use.

### rosdep And apt Dependency Groups

S10 should document dependency groups conceptually; S08 should map these to package dependencies where relevant.

Recommended groups:

| Group | Representative Packages |
|---|---|
| Base ROS 2 | `ros-jazzy-desktop`, `python3-colcon-common-extensions`, `python3-vcstool`, `python3-rosdep`, `python3-argcomplete`. |
| Model and launch | `ros-jazzy-xacro`, `ros-jazzy-robot-state-publisher`, `ros-jazzy-joint-state-publisher-gui`, `ros-jazzy-tf2-ros`. |
| Gazebo Harmonic sim | `ros-jazzy-ros-gz`, `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-bridge`, `ros-jazzy-gz-ros2-control`. |
| ros2_control | `ros-jazzy-ros2-control`, `ros-jazzy-ros2-controllers`, `ros-jazzy-controller-manager`, `ros-jazzy-joint-state-broadcaster`, `ros-jazzy-joint-trajectory-controller`, gripper/position controller packages as needed. |
| MoveIt 2 | `ros-jazzy-moveit`, MoveIt Setup Assistant if used during regeneration, RViz MoveIt plugins. |
| Interfaces | `ros-jazzy-control-msgs`, `ros-jazzy-trajectory-msgs`, `ros-jazzy-sensor-msgs`, `ros-jazzy-diagnostic-msgs`, `ros-jazzy-std-srvs`. |
| Camera/CV | `ros-jazzy-cv-bridge`, `ros-jazzy-image-transport`, `ros-jazzy-image-tools`, OpenCV Python packages if examples need them. |
| Lint/test/docs | `ros-jazzy-ament-cmake-clang-format`, `ros-jazzy-ament-cmake-ruff`, `ros-jazzy-ament-lint-auto`, `markdownlint` or a lightweight docs check if S10 wants it. |
| Bridge-host only | ECN bridge ROS 1 support deps or `baxter_legacy` deb/container path after license/packaging validation. |
| Experimental Zenoh | `ros-jazzy-rmw-zenoh-cpp` or source install if needed by the selected Rethought flow. |

Do not require every optional package for the 15-minute sim path. The default path should build and run sim+MoveIt without hardware or Zenoh packages.

### Launch Profile Naming And Behavior

Use the proposed launch names with clear semantics. Avoid clever unification that hides hardware/sim differences.

| Launch Profile | Mode | Expected Behavior |
|---|---|---|
| `baxter_description.launch.py` | `model` | Starts `robot_state_publisher` from the selected Baxter ROS 2 description. No Gazebo, no MoveIt, no hardware bridge. Good for model/RViz sanity checks. |
| `moveit_rviz.launch.py` | `model_moveit` | Loads robot model, `robot_description_semantic`, MoveIt RViz, and fake/planning-only execution. No Gazebo or hardware motion. |
| `sim.launch.py` | `sim` | Starts Gazebo Harmonic, spawns Baxter, starts `robot_state_publisher`, controller manager, `joint_state_broadcaster`, `left_arm_controller`, `right_arm_controller`, optional head/gripper controllers. No MoveIt. |
| `sim_moveit.launch.py` | `sim_moveit` | Includes sim, waits for active controllers, starts `move_group` with `moveit_controllers_sim.yaml`, starts RViz by default unless `rviz:=false`. |
| `sim_compat.launch.py` | `sim_compat` | Includes standard sim plus `/robot/joint_states`, `/robot/state`, optional endpoint/gripper/camera compatibility, optional safe position-only `JointCommand` shim if implemented. |
| `hardware_bridge.launch.py` | `hardware` | Bridge-host profile: starts ECN bridge allowlist, `robot_state_publisher`, hardware non-motion monitors, and safe tools. No MoveIt execution. |
| `hardware_moveit.launch.py` | `hardware_moveit` | Requires bridge smoke checks; starts hardware action shims and MoveIt using `moveit_controllers_hardware.yaml`. Does not enable robot automatically. |
| `smoke_sim.launch.py` | `smoke_sim` | Headless model/controller/sim smoke profile for local/CI checks. |
| `smoke_hardware.launch.py` | `smoke_hardware` | Non-motion bridge checks: `/robot/state`, `/robot/joint_states`, services, action availability. No enable and no trajectory goal. |

Recommended launch arguments:

| Arg | Applies To | Meaning |
|---|---|---|
| `headless:=true|false` | sim/smoke | Run Gazebo without GUI. |
| `rviz:=true|false` | MoveIt/model | Start RViz. |
| `use_sim_time:=true|false` | sim | Use Gazebo clock. |
| `left_electric_gripper:=true|false`, `right_electric_gripper:=true|false` | model/sim/MoveIt | Select gripper geometry/controllers. |
| `compat:=true|false` | sim | Enable optional Baxter `/robot/*` compatibility. |
| `robot_ip`, `robot_hostname`, `bridge_host_ip` | hardware docs/setup | Documented for bridge host, not required for sim. |
| `ros_domain_id` | all multi-machine docs | Keep one domain per robot bench. |
| `allow_motion:=false` | hardware smoke/moveit | Hardware launches should default to non-motion checks unless a supervised command explicitly enables motion. |

### Environment Setup Strategy

Replace `baxter.sh` with documented setup layers:

| Setup Layer | Recommendation |
|---|---|
| ROS 2 workspace | `source /opt/ros/jazzy/setup.bash`, `colcon build`, `source install/setup.bash`. |
| Devcontainer | Bake base dependencies into image; leave project source mounted. |
| `.env.example` | Include `ROS_DOMAIN_ID`, optional `RMW_IMPLEMENTATION`, `BAXTER_ROBOT_HOSTNAME`, `BAXTER_ROBOT_IP`, `BAXTER_BRIDGE_HOST_IP`, `BAXTER_PROFILE=sim|hardware|experimental_zenoh`. |
| Hardware bridge host | Separate `docs/hardware_bridge_setup.md` with robot LAN IP, `ROS_MASTER_URI`, `ROS_IP`, firewall, DDS discovery, and bridge launch. |
| Fallback Zenoh | Separate experimental doc with Docker host networking, Zenoh router, `rmw_zenoh_cpp`, and restricted YAML. |

Do not set `ROS_MASTER_URI` in student sim shells. That belongs only to bridge-host ROS 1 setup.

Student-friendly profile names:

| Profile Name | Meaning |
|---|---|
| `sim` | Standard Gazebo + ros2_control. Best first command. |
| `sim_moveit` | Gazebo + MoveIt planning/execution. |
| `sim_compat` | Sim plus selected legacy Baxter topic names. Optional. |
| `hardware` | Real robot bridge, non-MoveIt, non-motion by default. |
| `hardware_moveit` | Real robot MoveIt through action shims, supervised only. |
| `model` | RViz/model only. |
| `experimental_zenoh` | Fallback bridge path, not default. |

### First-Release Examples And Tutorials

Prioritize five examples only:

| Example | Profile | Description | Safety Scope |
|---|---|---|---|
| `sim_tiny_trajectory` | `sim` | Launch sim and send a tiny one-arm `control_msgs/action/FollowJointTrajectory` goal to `/left_arm_controller/follow_joint_trajectory` or `/right_arm_controller/follow_joint_trajectory`. | Safe default; headless-capable. |
| `sim_moveit_neutral` | `sim_moveit` | Plan and execute `left_arm` or `right_arm` to `left_neutral` or `right_neutral` in MoveIt/RViz. | Sim only. |
| `hardware_bridge_smoke` | `hardware` | Read `/robot/state`, `/robot/joint_states`, camera/gripper service availability, and `/robot/limb/{left,right}/follow_joint_trajectory` action availability without moving. | No enable, no motion. |
| `hardware_enable_status` | `hardware` | Safe status/enable/disable wrapper that prints state fields and requires explicit user confirmation/flag for enable. | No raw topic publishing in docs. |
| `gripper_open_close` | `sim` or `hardware` | Simple electric gripper open/close through the selected gripper controller/action or safe hardware shim if electric grippers are confirmed. | Optional until gripper hardware/model is verified. |

Deprioritize for first release:

- Broad Noetic example parity.
- Raw torque, velocity, and raw-position demos.
- Old joystick/keyboard variants beyond maybe one later teleop.
- Full pick-place and object manipulation.
- Full camera pipelines and image processing labs.
- Maintenance, tare, calibration, update, and robust controller tools.
- Multi-user simultaneous motion examples.

### Smoke Test Command Design

S08/S09/S10 should reference smoke checks as named commands, even if the exact implementation later uses Python, launch tests, or shell wrappers.

Recommended smoke checks:

| Check | Intended Command Shape | Pass Criteria |
|---|---|---|
| Build | `colcon build --symlink-install` | Core workspace builds with default deps. |
| Lint | `colcon test --packages-select ...` or `ament_lint_auto` | Formatting/import/lint checks pass for local packages. |
| Model load | `ros2 launch baxter_bringup baxter_description.launch.py` | `robot_description` loads, meshes resolve, TF publishes. |
| MoveIt model | `ros2 launch baxter_moveit_config moveit_rviz.launch.py` | SRDF loads with `left_arm`, `right_arm`, `both_arms`, neutral states, no missing kinematics plugin. |
| Sim controllers | `ros2 launch baxter_gz_sim smoke_sim.launch.py headless:=true` plus `ros2 control list_controllers` | `joint_state_broadcaster`, `left_arm_controller`, `right_arm_controller` active. |
| Tiny sim trajectory | `ros2 run baxter_examples sim_tiny_trajectory --arm left` | One tiny FJT goal succeeds in sim. |
| MoveIt plan | `ros2 run baxter_smoke_tests moveit_plan --group left_arm --target left_neutral --execute false` | Planning succeeds without execution. |
| MoveIt sim execute | Same command with `--execute true` under `sim_moveit` | Tiny one-arm execution succeeds. |
| Hardware bridge non-motion | `ros2 run baxter_smoke_tests hardware_bridge_check` | `/robot/state`, `/robot/joint_states`, key services, and bridge topics visible. |
| Hardware action availability | `ros2 run baxter_smoke_tests hardware_action_check` | `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory` action servers visible; no goal sent. |

Hardware motion smoke is not ordinary CI and not beginner self-service. It should be a supervised lab procedure after the S04 physical checklist.

### CI Strategy

Ordinary CI can run:

- `vcs import` from default `baxter_core.repos` and local packages.
- `rosdep install` for non-hardware dependencies.
- `colcon build --symlink-install`.
- Lightweight lint tests.
- Python unit tests or launch tests that do not require hardware.
- Xacro/model loading.
- MoveIt config loading with fake/planning-only execution.
- Optional headless Gazebo smoke if the CI runner supports it reliably.

Manual or allowed-to-be-flaky checks:

- Gazebo Harmonic GUI tests.
- Full `sim_moveit.launch.py` with RViz.
- Camera rendering tests.
- Headless Gazebo tests on shared CI if runner graphics/physics timing is unstable.

Real hardware only:

- ECN bridge connectivity to Baxter.
- `/robot/state` and `/robot/joint_states` against real robot.
- Camera open/list/close on real robot.
- Gripper state/command on real robot.
- Any enable/reset/stop operation.
- Any `FollowJointTrajectory` motion test.

CI should not require `baxter_legacy`, Docker host networking, Zenoh, or a ROS 1 master for the default student path.

### Developer Quality Tooling

Keep tooling lightweight:

| Tooling Area | Recommendation |
|---|---|
| Formatting | Use ROS 2/ament defaults: `ament_cmake_clang_format` for C++ if any, `ruff` or `ament_flake8` for Python, standard YAML/Markdown checks only if cheap. |
| Linting | Run through `colcon test`; do not require a large custom pre-commit setup for first release. |
| Pre-commit | Optional maintainer convenience, not required for student onboarding. If used, mirror the same commands CI runs. |
| Tests | One small smoke or launch test per non-trivial local package; no broad fixtures unless implementation proves they pay for themselves. |
| Docs checks | Minimal link/path sanity and Markdown formatting if S10 wants it; do not block releases on exhaustive docs tooling. |
| Dependency updates | Manual pinned-SHA review, not floating branches. |

This project already has enough complexity at the ROS 1/ROS 2/hardware boundary. Do not add a heavyweight meta-build or custom task runner unless the first implementation proves plain `colcon`, `vcs`, and `rosdep` are insufficient.

### Safety Presentation And Enable Flow

Hardware docs and examples should make safety visible without normalizing dangerous commands.

Rules for first release:

- Put a hardware warning box at the top of hardware docs and examples.
- Require the physical checklist before any motion: clear workspace, e-stop reachable, correct user/robot bench, bridge smoke checks passed.
- Do not show raw `ros2 topic pub /robot/set_super_enable` in beginner docs.
- Provide a safe status/enable tool that prints `ready`, `enabled`, `stopped`, `error`, `estop_button`, and `estop_source` before acting.
- Never enable automatically from `hardware_moveit.launch.py`.
- Never auto-reset errors in a loop.
- Keep `/robot/set_super_stop` documented as an explicit software stop/admin tool, not routine cancel behavior.
- Tiny trajectory examples must be low-speed, single-arm, and require explicit `--i-understand-this-moves-the-real-robot`-style confirmation if run on hardware.
- Raw torque/velocity/raw-position examples are out of first-release beginner docs.

## Decisions

1. **Name the future implementation repo `baxter_ros2_jazzy`.** It is explicit, searchable, and avoids implying a native robot firmware port.
2. **Use a normal colcon workspace layout.** Keep `src/`, `repos/`, `.devcontainer/`, `docs/`, `examples/`, and smoke-test helpers. Do not invent a custom workspace manager.
3. **Split `.repos` files by profile.** Use `baxter_core.repos`, `baxter_sim.repos`, `baxter_hardware.repos`, and `baxter_experimental.repos`.
4. **Pin `CentraleNantesRobotics/baxter_common_ros2` by default.** Use it for messages, descriptions, end-effector descriptions, and ECN bridge evaluation.
5. **Keep unlicensed or low-adoption repos out of default imports.** `angysof16/BaxterMotionPlanning` remains reference-only; `baxter_legacy` needs license verification before vendoring; Zenoh remains experimental.
6. **Use one default devcontainer for sim/MoveIt/docs/builds.** Hardware bridge tooling belongs in a separate bridge-host setup.
7. **Use explicit launch profiles.** Keep `sim`, `sim_compat`, `hardware`, and `hardware_moveit` visibly distinct.
8. **Avoid a ROS 1-style `baxter.sh` clone.** Use `.env.example`, launch args, bridge-host docs, and ordinary ROS 2 workspace setup.
9. **Prioritize five examples:** tiny sim trajectory, sim MoveIt neutral, hardware bridge smoke, safe hardware enable/status, optional gripper open/close.
10. **Make smoke tests first-class.** S08/S09/S10 should reference build, model, controller, MoveIt, sim trajectory, hardware non-motion, and action-availability checks by name.
11. **Keep CI lightweight.** Ordinary CI covers build/lint/model/MoveIt config and maybe headless sim; real hardware is manual only.
12. **Keep safety warnings in tools, not just prose.** Hardware examples must refuse motion until state/smoke checks and explicit user intent are present.

## Open Questions

- Should the first implementation keep smoke checks as a package (`baxter_smoke_tests`) or as scripts under `baxter_bringup`/`baxter_examples` to reduce package count?
- Will the target lab allow students to run ROS 2 nodes from laptops over DDS, or should the official hardware workflow require SSH/devcontainer on the bridge host?
- Can `CentraleNantesRobotics/baxter_legacy` be legally redistributed or imported in `baxter_hardware.repos`, or should bridge-host docs reference external installation only?
- Does the target course require `sim_compat` direct `JointCommand` support in first release, or can compatibility stop at `/robot/joint_states` and `/robot/state`?
- Which electric grippers and cameras are physically installed, and should the optional gripper/camera examples be enabled by default?
- Is headless Gazebo reliable enough in the chosen CI runner, or should CI use model/MoveIt fake checks and leave Gazebo smoke manual?
- Should S10 present the repo as Jazzy-only, or define a compatibility matrix that leaves room for Kilted/Lyrical experiments later?

## Artifacts

- Updated this S07 developer experience/tooling log: `logs/S07_dev_experience_tooling.log.md`
- Updated S07 status in `MASTER_PLAN.md`
- Appended S08 handoff prompt to `PROMPTS.md`
- Prior architecture logs used as source decisions:
  - `logs/S01_validate_assumptions.log.md`
  - `logs/S02_audit_community_packages.log.md`
  - `logs/S03_local_repo_analysis.log.md`
  - `logs/S04_bridge_architecture.log.md`
  - `logs/S05_simulation_architecture.log.md`
  - `logs/S06_moveit_ros2_control.log.md`
