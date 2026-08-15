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

- **Status:** `completed` (2026-07-22, first session on the physical robot)
- **Type:** Hardware
- **Description:** Non-motion checks against the real robot: `/robot/state`, `/robot/joint_states`, IK services, camera services, gripper state/properties, publisher visibility. No enable, no motion.
- **Gate:** PASS. `i10_non_motion_check.py` reports `GATE: PASS (0 warnings)`; `/robot/joint_states` bridges at a stable 100.0 Hz with all 17 joints; `baxter_safety_check` correctly reports `safe_for_motion=False` while the robot is disabled.
- **Findings:** Robot is addressed by mDNS `011412P0024.local`; its DHCP lease moves (`192.168.1.232` this session), so the repo's hardcoded `192.168.1.224` was wrong. Laptop ethernet held a stale manual `192.168.2.100/24`, routing robot traffic out the WiFi gateway — fixed by switching the NM profile to DHCP. Found and fixed a real bridge bug: `deser_joint_state()` did not account for ROS 1 `std_msgs/Header` carrying `uint32 seq` (dropped in ROS 2) and `frame_id`, misaligning every later field. Head sonar disabled on request via new `scripts/sonar_ctl.py`.
- **Log:** `logs/I10_hardware_bridge_non_motion.log.md`

### I10-prep: Hardware Action Shim Dry-Run Prep

- **Status:** `completed`
- **Type:** Implementation (hardware-free)
- **Description:** Created `baxter_hardware_bridge` package with `FollowJointTrajectory` action shims, safety state checker, mock robot, and dry-run self-test. All safety logic (state validation, joint name validation, hold-on-cancel) is implemented and dry-run tested without a real robot. This unblocks I11 implementation work — when the bridge host is ready, only the hardware-specific integration and I10 non-motion gate remain.
- **Gate:** `ros2 run baxter_hardware_bridge dry_run_test` passes: safe-state goal accepted+succeeded, bad joints rejected, unsafe state rejected.
- **Log:** `logs/I10_prep_hardware_shim_dry_run.log.md`

### I10-prep2: py_bridge.py ROS 1 Negotiation Fix And Loopback Proof

- **Status:** `completed`
- **Type:** Implementation (hardware-free)
- **Description:** Auditing `scripts/py_bridge.py` ahead of the first lab session found it skipped ROS 1 Slave API (XML-RPC) negotiation in both directions — it would have failed against a real `roscore` in both the subscribe path (`/robot/state`, `/robot/joint_states`) and the publish/motion-command path (`/robot/limb/*/joint_command`). Fixed with a minimal stdlib `SlaveApi` (`xmlrpc.server`) implementing `requestTopic`/`publisherUpdate`/`getPid`/`getMasterUri`, used as the shared `caller_api` for every register call. Proved against genuine `rospy`/`roscore` (not a mock) via Docker, both directions.
- **Gate:** `bash scripts/test_bridge_loopback.sh` passes: `OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy)`. `ros2 run baxter_hardware_bridge dry_run_test` still 3/3 PASS (no regression).
- **Log:** `logs/I10_prep2_py_bridge_loopback.log.md`

### I11: Hardware Action Shims And Safety Tools

- **Status:** `completed` (2026-07-22, zero motion)
- **Type:** Hardware
- **Gate:** PASS. On the real robot with the arm disabled: bad joint names rejected, wrong position count rejected, and a fully valid goal rejected by the safety interlock (`ready=False enabled=False`). Joint positions unchanged — no motion. `baxter_tools enable_robot.py -s` independently confirms the same state the bridge reports.
- **Findings:** The previously documented I12 command was unsafe — the shim commands trajectory point 0 directly when `time_from_start=0`, so a hardcoded first point sweeps the arm from its actual pose (~1.6 rad on s1, ~3.0 on e0 from tucked). Replaced with parameterized `sim_tiny_trajectory` (measured start, reversible target, 0.02 rad verification); sim defaults verified unchanged. Also fixed stale ROS 1 registrations leaking onto the robot's master.
- **Description:** Validate the pre-built `FollowJointTrajectory` action shims against a real robot via `baxter_bridge`. The shim code is already implemented and dry-run tested (I10-prep); this step runs the I11 gate on hardware: reject unsafe `/robot/state`, validate exact joint names, set speed ratio/timeouts, and cancel by holding position.
- **Gate:** action shims reject unsafe `/robot/state`, validate exact joint names, set speed ratio/timeouts, and cancel by holding position — on the real robot, not just mock.
- **Log:** `logs/I11_hardware_action_shims.log.md`

### I12: Supervised Hardware Motion

- **Status:** `completed` (2026-07-24, supervised, both arms)
- **Type:** Hardware
- **Description:** Run one tiny low-speed trajectory per advertised arm under physical supervision. Do not claim hardware motion before this passes.
- **Gate:** PASS. Both arms, out and back, every goal returning `error_code: 0` with feedback. Worst tracking error 0.0078 rad (right arm) against a 0.2 rad path tolerance; nothing tripped. Cancel-and-hold behaved correctly — the arm stopped where a cancel 1.1 s into a 3 s move should stop it and held to 0.0004 rad over 6 s; the *test* false-failed on the settle transient (I18 F2, fixed 2026-07-25). Evidence: `logs/I18_hardware_day.log.md`.
- **Robot:** S/N `011412P0024`, model BR-01 (Research Robot), mfd 12/2014.
- **Former blocker (resolved 2026-07-24):** the robot would not enable from the tucked pose — `enable_robot.py -e` returned `Failed to enable robot` with a clean state. The 2026-07-22 diagnosis was correct: a latched `left_s1` collision force-field that cannot self-clear while disabled and tucked. `tuck_arms.py -u`, which suppresses collision avoidance and republishes enable at 20 Hz, succeeded on the first attempt in ~23 s (I18 F5).
- **Command path:** hardened before the robot day. F1–F4 and F10 from the audit were fixed on 2026-07-23; path tolerance and stopped-velocity monitoring followed in I17. Covered hardware-free by `dry_run_test` (25 cases) and a closed-loop `mock_robot` rehearsal. See `logs/I12_prep_command_path_audit.log.md` (Resolution) and `logs/I17_pre_hardware_hardening.log.md`.
- **Log:** `logs/I12_supervised_hardware_motion.log.md` (2026-07-22 diagnosis, with a Resolution section appended), gate evidence in `logs/I18_hardware_day.log.md`, audit in `logs/I12_prep_command_path_audit.log.md`

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

### I15: RViz Simulation Launch Profiles

- **Status:** `completed`
- **Type:** Implementation
- **Description:** Add two supported RViz entry points with checked-in configurations and complete the user-authorized remediation of actionable findings P1-P20 from `logs/sim_gui_testing_problems.log.md`:
  - A normal simulation profile owned by `baxter_gz_sim` that launches the existing Gazebo/ros2_control stack plus a plain Baxter RobotModel/TF view.
  - A MoveIt simulation profile owned by `baxter_moveit_config` that launches the existing sim and `move_group` plus a configured MotionPlanning view with URDF, SRDF, kinematics, OMPL parameters, and simulation time. Joint limits are deliberately not passed to the RViz node; `move_group` owns them and RViz only replays its trajectories.
  - Complete the independent head and source-finger state needed to remove the known P8/P9 RobotModel TF errors, without adding gripper command support.
  - Make simulated motion evidence numeric and reversible, enforce finite limits/tolerances, gate MoveIt readiness on live controllers/state, use a deterministic world mount/neutral pose, audit the collision matrix, and require cancellation/teardown checks.
  - Keep bare `rviz2` unsupported for MoveIt; the checked-in launch/config is the documented path.
  - Preserve existing headless and CLI smoke paths; keep hardware, gripper commands, cameras, octomap sensing, and compatibility layers out of scope.
- **Gate:** a clean default build passes; both RViz profiles launch from isolated clean graphs; normal RobotModel has complete TF and follows all 17 independent states; MoveIt MotionPlanning loads SRDF and OMPL without `NO PLANNING LIBRARY LOADED`; direct left/right and MoveIt left/right/both-arm reversible numeric checks stay within `0.02 rad`; cancellation holds; one-interrupt teardown leaves no related process or `move_group` crash.
- **Gate note (2026-07-22):** the MotionPlanning clause of this gate was **not** actually satisfied when the step was first marked `completed` — the display failed to load its robot model and the defect was documented in `docs/known_issues.md` instead. Root-caused and fixed on 2026-07-22 (Qt's `setlocale(LC_ALL, "")` runs before `rclcpp::init` in `rviz2`, so under a comma-decimal `LC_NUMERIC` rcl parsed every double as a string; the RViz node now runs with `LC_NUMERIC=C`). The gate now passes as written.
- **Log:** `logs/I15_rviz_launch_profiles.log.md`, with the defect investigation and its resolution in `logs/sim_gui_testing_problems.log.md` (final section).

### I17: Pre-Hardware Hardening And Polish

- **Status:** `completed` (2026-07-23, no hardware)
- **Type:** Implementation (hardware-free)
- **Description:** Phases A and B of `docs/i12_completion_plan.md`, closing the last command-path gaps against the legacy ROS 1 `JointTrajectoryActionServer` before the robot day:
  - Path tolerance monitoring in the shim's interpolation loop (`path_tolerance_rad`, default 0.2 from Rethink's `PositionJointTrajectoryActionServer.cfg`). On violation the shim aborts with `PATH_TOLERANCE_VIOLATED` but **holds** via `_hold_position()` rather than stopping commands, because a lagging arm is not an unsafe robot and stopping would drop it into gravity compensation.
  - Stopped-velocity check after the last point (`stopped_velocity_tolerance`, default 0.25, same source), aborting with `GOAL_TOLERANCE_VIOLATED` and holding.
  - A `mock_mode` launch argument on `dry_run.launch.py`, which previously hardcoded `True` for both shims so the mock arm could never move.
  - Deliberately **not** ported from the legacy: velocity mode + PID, `position_w_id` inverse-dynamics feedforward (needs `RAW_POSITION_MODE`, which bypasses collision avoidance), Bezier/minjerk interpolation, and per-joint goal position tolerance (Rethink shipped it disabled).
- **Gate:** PASS. `ros2 run baxter_hardware_bridge dry_run_test` reports `OVERALL: PASS` over 20 cases, exit 0. Closed-loop rehearsal via `ros2 launch baxter_hardware_bridge dry_run.launch.py mock_mode:=false`: both arms verified outbound and return with feedback (264–277 messages, `max_error=0.0000 rad`), `Reversible trajectories verified for both arms`, and `Cancellation hold verified: max_drift=0.0000 rad`. The no-argument launch still comes up with `mock_mode=True`.
- **Log:** `logs/I17_pre_hardware_hardening.log.md`

### I18: Hardware Session — First Supervised Motion

- **Status:** `completed` (2026-07-24, supervised)
- **Type:** Hardware
- **Description:** The robot day. Clear the I12 blocker, run the supervised motion gate on both arms, characterise the tolerances against a real arm rather than a mock, and come away with a concrete improvement backlog. Followed `docs/hardware_day_plan.md`.
- **Gate:** PASS on every stage attempted. Network pre-flight; I10 non-motion re-check (0 warnings); I11 safety interlock (6/6 goals rejected, each for the correct distinct reason); enable + untuck via `tuck_arms.py -u`; **I12 supervised motion, both arms**; a speed sweep at `speed_ratio` 0.1/0.2/0.3; and MoveIt planning *and executing* on hardware (31 waypoints, `error_code: 0`). Robot shut down clean — tucked, disabled, sonar off, no stale registrations on the master.
- **Findings:** 23 numbered findings, of which four matter beyond the session. **F1**: a stale `mock_baxter_robot` published a fake "safe" `/robot/state` alongside the real disabled robot for ~15 minutes, defeating the safety gate and contaminating one finding badly enough that it had to be retracted (F4). **F22**: corrects F3 — worst *in-flight* tracking lag is 0.0352 rad, so `path_tolerance_rad = 0.2` is a 5.7× margin, and the 0.05 rad proposed earlier would have caused nuisance aborts. **F18**: MoveIt needed three separate fixes, the last being a 1.7 mm SRDF false positive that made the planner refuse the robot's own untuck pose. **F9**: `speed_ratio` has no measurable effect — trajectory duration is the binding constraint.
- **Log:** `logs/I18_hardware_day.log.md`, improvement backlog in `logs/I19_backlog_plan.md`

### I19: Post-Hardware Backlog — Desk Work

- **Status:** `completed` (2026-07-25, no hardware)
- **Type:** Implementation (hardware-free)
- **Description:** Work the I18 improvement backlog in its recommended order, one commit per item: the second-publisher safety guard (F1), real md5sum and message definition on ROS 1 publishers so recordings decode (F23), preserving the robot's `header.stamp` (F14), a settle window for the cancel-hold check (F2), `duration`/`offset` parameters so a trajectory can approach the 2.0 rad/s clamp (F9), and a quiet shutdown path (F17). Item 9, the full MoveIt Setup Assistant re-run, is GUI work left for its own sitting.
- **Gate:** PASS. `dry_run_test` `OVERALL: PASS` over **25** cases (Test 25 covers the new publisher-count gate), `scripts/test_bridge_loopback.sh` PASS, clean build, and the mock rehearsal verified both arms at the defaults and with `duration:=1.0 offset:=0.5` (0.12 → 0.50 rad/s). F23 proven by a rosbag round-trip in the Noetic image: a `JointCommand` published by the bridge now records as `baxter_core_msgs/JointCommand [19bfec8434dd568ab3c633d187c36f2e]` and deserialises.
- **Findings:** two traps cost real time and are worth carrying forward. `scripts/baxter_env.sh` killed any `set -e` caller whenever the robot was offline, which had silently made `test_bridge_loopback.sh` unrunnable on every desk day. And `ros2 run baxter_examples` executes a build-time copy — `install(PROGRAMS)` copies even under `--symlink-install` — so two rehearsals silently tested stale code.
- **Log:** `logs/I19_post_hardware_backlog.log.md`

### I20: Fast-Motion Characterisation And The SRDF Re-run

- **Status:** `completed` (2026-07-25, supervised)
- **Type:** Hardware + Implementation
- **Description:** Answer the speed question every tolerance figure depended on, and settle item 9 (the MoveIt Setup Assistant re-run) with measurement rather than a GUI session.
- **Gate:** PASS. Bring-up, interlocks (4/4 rejected while disabled), untuck, I12 gate re-confirmed on both arms (max_error 0.0040-0.0061 rad), speed escalation to the abort point, cancel sweep at 0.5 s and 2.0 s, MoveIt planning scene clean against the live robot, clean shutdown with no stale registrations.
- **Findings:** **`path_tolerance_rad` is a speed limit.** In-flight lag is linear in commanded velocity at ~0.4 s of it (0.037 rad at 0.12 rad/s, 0.094 at 0.23, 0.198 at 0.50, aborting at 0.202), so 0.2 rad *is* ~0.5 rad/s and the 2.0 rad/s clamp is unreachable. The **Setup Assistant's sampling does not converge** for this robot — 10k trials disables 34 pairs that 250k proves can collide, including gripper-into-screen — so the 54-pair matrix stays. The multi-publisher bridge fix had **broken the motion client**, which kept only the last joint-state message on a topic with two publishers. MoveIt was then driven from RViz on hardware: the left arm aborted 8 of 11 goals on `left_w0`/`left_e0` while the right completed the same `both_arms` plans, which is either an asymmetric plan or an asymmetric arm — undecided, and the experiment that settles it is specified in the log.
- **Log:** `logs/I20_fast_motion_and_srdf.log.md`

---

### I21: Publish Prep For The Public Repository

- **Status:** `completed` (2026-07-25, hardware-free) — desk-side prep only; the merge, tag and GitHub settings are human actions and are **not** part of this gate.
- **Type:** Implementation + Docs
- **Description:** Bring the 32 unpushed commits on `i17-pre-hardware-hardening` to `main`-readiness for the already-public repository: sanitise lab defaults out of `scripts/`/`docker/`, give the packages a real maintainer and version, fix the CI that had been red-in-waiting since `e543449`, sync every public claim surface with I20 (including F-F, which had reached no user-facing doc), and cut `v0.2.0` notes.
- **Gate:** PASS, all hardware-free. Clean `colcon build` of 9 packages; `dry_run_test` **OVERALL: PASS, 25/25**; `moveit_static_check=passed independent_joints=17 acm_pairs=54`; `python_import_checks=passed`; `cleanup_handler_checks=passed` with 3 handlers inspected and a negative control confirming the guard can still fail; `test_bridge_loopback.sh` **OVERALL: PASS**; full manual sim smoke (both arms reversible, max_error 0.0061–0.0105 rad; MoveIt left/right/both-arms 0.0078–0.0115 rad; `moveit_pose` and `ik_service_client` including its non-zero exit on an unreachable pose; cancel-and-hold drift 0.0012/0.0015 rad; SIGINT teardown with no orphaned process and an empty graph).
- **Findings:** **CI had been red since `e543449`.** A guard written in I15 asserted the two `upper_shoulder`↔`upper_elbow` pairs were *not* disabled; I18 F18.3 disabled them on hardware to clear `START_STATE_IN_COLLISION`, and nobody reconciled the two. The assertions are now inverted to require the hand-added pairs, and the 54-pair count that three documents promise is asserted rather than merely printed. **The largest overclaim was an omission:** I20 F-F (left arm 3 of 11 goals from RViz) had reached no user-facing document, while six status surfaces still read "passed, supervised" and four of them pointed the reader at `moveit_guide.md`, which contained nothing about it. `baxter_examples` became `ament_python`, removing the `install(PROGRAMS)` copy-under-`--symlink-install` trap that silently invalidated two I19 rehearsals — verified empirically, not just by build.
- **Log:** `logs/I21_publish_prep.log.md`

---

## Dependencies Between Steps

```text
I00 -> I01 -> I02 -> I03 -> I04 -> I05 -> I06 -> I07 -> I08 -> I09 -> I14 -> I15
                                   \
                                    -> I10-prep -> I10-prep2 (completed, hardware-free)
                                    -> I10 -> I11 -> I17 -> I12 -> I18 -> I19 -> I20 -> I21

I13 is deferred and depends on a concrete course, hardware, or transport need.
I14 covers the sim-first release after I09; hardware claims in I14 additionally require I12.
I15 follows the sim-first release baseline and addresses the user-authorized actionable simulation findings from P1-P20.
I17 is hardware-free command-path hardening that must land before the I12 robot day.
I18 is the robot day itself: it cleared the I12 blocker and passed the I12 gate.
I19 is hardware-free work on the backlog I18 produced.
I21 is hardware-free publish prep; it depends on I20 because it publishes I20's findings, and it stops short of the merge/tag/GitHub-settings actions that only the human owner can take.
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
