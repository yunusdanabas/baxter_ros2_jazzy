---
step: S01
title: "Validate Research Assumptions"
agent_date: 2026-06-16
status: completed
previous_steps: []
---

# S01: Validate Research Assumptions

## Task

Re-validated the key claims in `EXISTING_RESEARCH.md` without redoing full research. Checked current ROS 2 Jazzy documentation, ROS/Gazebo/MoveIt/ros2_control upstream docs, `ros1_bridge`, selected community Baxter repositories, and the read-only Noetic reference copy at `baxter_noetic_ref/`.

## Findings

### Claim Validation Summary

1. **CONFIRMED**: ROS 2 Jazzy is an LTS release targeting Ubuntu 24.04 Noble.
   - REP-2000 and Jazzy release docs list Jazzy Jalisco as May 2024-May 2029, with Ubuntu Noble 24.04 `amd64` and `arm64` as Tier 1.
   - Jazzy release docs list Ubuntu Noble Python 3.12.3, default `rmw_fastrtps_cpp` / Fast DDS 2.14.0, and Tier 1 `rmw_cyclonedds_cpp` / Cyclone DDS 0.10.4.
   - URLs: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-2000.rst, https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Releases/Release-Jazzy-Jalisco.rst

2. **CONFIRMED**: ROS 1 Noetic is EOL and targets Ubuntu 20.04 Focal.
   - REP-0003 lists Noetic Ninjemys as May 2020-May 2025 with required support for Ubuntu Focal Fossa 20.04.
   - Upstream `ros1_bridge` README now explicitly says ROS 1 Noetic reached EOL in May 2025 and Ubuntu 24.04 LTS does not support ROS 1.
   - URLs: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0003.rst, https://raw.githubusercontent.com/ros2/ros1_bridge/master/README.md

3. **CONFIRMED**: Upstream `ros1_bridge` is not supported on Ubuntu 24.04/Jazzy, bridges only compile-time-known message/service types, and actions are not first-class.
   - Current `ros1_bridge` README has an explicit compatibility table: Ubuntu 24.04 Noble + Jazzy/Kilted = not supported because ROS 1 is unavailable.
   - `ros1_bridge` docs still describe compile-time message/service mapping and custom mapping rules for messages/services, not generic ROS 1 action server/client bridging.
   - New development: RethoughtRobotics published a custom Docker/ROS-O/Zenoh bridge stack that vendors/forks `ros1_bridge`; this is a workaround, not upstream Jazzy support.
   - URLs: https://github.com/ros2/ros1_bridge, https://raw.githubusercontent.com/ros2/ros1_bridge/master/doc/index.rst, https://github.com/RethoughtRobotics/baxter-zenoh

4. **CONFIRMED**: Gazebo Classic 11 is EOL and Jazzy's recommended simulation pairing is Gazebo Harmonic via `ros_gz`.
   - Open Robotics announced Gazebo Classic 11 EOL on 2025-02-03; it states no new features, security updates, bug fixes, support, or updated binaries.
   - Gazebo Harmonic docs list Harmonic as supported Sep 2023-Sep 2028 and recommend Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic.
   - REP-2001 lists Jazzy `simulation` packages as `ros_gz_bridge`, `ros_gz_sim`, `ros_gz_image`, and `ros_gz_interfaces`.
   - URLs: https://discourse.openrobotics.org/t/gazebo-classic-11-has-reached-end-of-life/48458, https://gazebosim.org/docs/harmonic/ros_installation/, https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-2001.rst

5. **CONFIRMED**: MoveIt 2 is mature and supported on Jazzy.
   - MoveIt 2 has a `jazzy` branch, Jazzy CI badge, and Jazzy binary buildfarm badges in its README.
   - Current MoveIt tutorials recommend Jazzy on Ubuntu 24.04 as the latest stable ROS version for the most seamless experience.
   - URLs: https://github.com/moveit/moveit2/tree/jazzy, https://raw.githubusercontent.com/moveit/moveit2_tutorials/main/doc/tutorials/getting_started/getting_started.rst

6. **CONFIRMED**: `ros2_control` is mature on Jazzy, with `joint_trajectory_controller` and `gz_ros2_control` support for Harmonic.
   - `ros2_control` README lists a Jazzy branch, docs, CI, and buildfarm entries.
   - `gz_ros2_control` compatibility matrix lists Jazzy + Harmonic, branch `jazzy`, binary package `ros-jazzy-gz-ros2-control` hosted at `packages.ros.org`.
   - `joint_trajectory_controller` docs document the `control_msgs/action/FollowJointTrajectory` action interface and supported command/state interface combinations.
   - URLs: https://github.com/ros-controls/ros2_control/tree/jazzy, https://github.com/ros-controls/gz_ros2_control/tree/jazzy, https://raw.githubusercontent.com/ros-controls/ros2_controllers/jazzy/joint_trajectory_controller/doc/userdoc.rst

7. **CONFIRMED**: Baxter physical hardware remains a ROS 1 robot boundary and should not be planned as natively upgradeable to ROS 2.
   - The Open Robotics Discourse thread records Baxter as deprecated hardware running ROS 1, remembered as Kinetic, and ECN maintainers explicitly state they do not know how to upgrade the embedded computer to ROS 2 without breaking anything.
   - New development: RethoughtRobotics documentation says its bridge connects to Baxter's ROS 1 side and requires no robot changes. Its architecture text says "Noetic via ROS-O" on the onboard side, which conflicts slightly with older "Kinetic internally" wording. Treat exact internal distro as lab/firmware-specific until verified on the target robot; the architecture constraint remains unchanged.
   - URLs: https://discourse.openrobotics.org/t/using-baxter-after-2025/25272, https://raw.githubusercontent.com/RethoughtRobotics/baxter-zenoh/main/ARCHITECTURE.md

8. **CHANGED**: The old "Rethink Robotics is defunct" wording is now too simple, but the Baxter ROS 2 support conclusion is unchanged.
   - Original Rethink Robotics shut down in 2018; HAHN Group acquired patents/trademarks and Intera 5, and later corporate changes/revivals exist around the Rethink brand.
   - No official Baxter ROS 2 SDK, Jazzy release, or vendor-supported Baxter hardware upgrade path was found.
   - Impact: Downstream steps should say "no official Baxter ROS 2 support path" rather than relying only on "Rethink is defunct."
   - URLs: https://en.wikipedia.org/wiki/Rethink_Robotics, https://robotsguide.com/robots/baxter, https://robotsguide.com/robots/sawyer

9. **CHANGED**: Community ROS 2 Baxter work is broader and more active than the existing report implied.
   - `CentraleNantesRobotics/baxter_common_ros2`: still the most established ROS 2 Baxter common/bridge repo. Last commit 2026-05-27 (`678bfab`, "rosconsole dep for baxter_bridge"), 21 stars, 11 forks, 0 open issues, 3 closed issues, BSD-3-Clause.
   - `RethoughtRobotics/BaxterSDK`: new public ROS 2 SDK repo. Created 2026-05-18, last commit 2026-05-26 (`bcd50c1`, "update recording playback"), 1 star, 0 forks, 0 open/closed issues, MIT. README advertises Jazzy/Kilted/Lyrical + MoveIt2 and requires `baxter-zenoh`.
   - `RethoughtRobotics/baxter-zenoh`: new public Docker/Zenoh bridge repo. Created 2026-05-12, last commit 2026-06-03 (`3b22a05`, "update dockerfile"), 0 stars, 0 forks, 0 open/closed issues, MIT. README advertises ROS 2 Jazzy/Kilted/Lyrical compatibility and a Docker/Zenoh bridge to Baxter ROS 1.
   - `RethoughtRobotics/ros1_bridge`: new custom bridge fork. Created 2026-05-21, pushed 2026-06-03, 0 stars, 0 forks, 0 open issues, Apache-2.0, default branch `kilted`.
   - `angysof16/BaxterMotionPlanning`: active ROS 2 Jazzy + Gazebo Harmonic + MoveIt2 simulation repo. Created 2026-03-28, last commit 2026-06-07 (`2a0ed74`, "/move_server correctly receiving goal, IK not processed correctly"), 6 stars, 0 forks, 0 open/closed issues, no license detected. README says Phase 3 MoveIt2 complete and Phase 4 custom action in progress.
   - Additional repos worth S02 audit: `CentraleNantesRobotics/baxter_legacy` (pushed 2025-04-10, 2 stars, 2 forks, no license detected), `CentraleNantesRobotics/baxter_gz` (pushed 2026-01-20, 0 stars, 1 fork, MIT), `Baxterminator/ECN_Baxter` (pushed 2023-09-20, 2 stars, MIT), `bornaparo/baxter_moveit_config` (pushed 2025-02-05, 0 stars, no license detected), `dabaspark/baxter_sdk_nvidia_any_os` (pushed 2025-01-11, 7 stars, 2 forks, no license detected).
   - Impact: S02 should not dismiss RethoughtRobotics as merely hypothetical; audit it as a new low-adoption but potentially high-relevance bridge/SDK path.

10. **CONFIRMED**: The local Noetic reference copy matches the reported size/API counts.
   - `baxter_noetic_ref/` contains 17 `package.xml` files.
   - File counts: 73 Python files, 22 C++/header files, 33 `.msg`, 6 `.srv`, 0 `.action`.
   - All C++/header files are under `baxter_simulator/`.
   - `FollowJointTrajectory` appears in examples, `baxter_interface`, README, and MoveIt controller YAMLs.

11. **CONFIRMED**: The Noetic simulator uses Gazebo Classic and ROS 1 controller APIs that do not migrate cleanly to Gazebo Harmonic.
   - Local grep found `gazebo_ros_control`, `controller_interface`, `hardware_interface`, `effort_controllers`, and custom `PLUGINLIB_EXPORT_CLASS` controllers under `baxter_simulator/`.
   - `baxter_gazebo` builds `libbaxter_gazebo_ros_control.so`; `baxter_sim_controllers` depends on ROS 1 `controller_interface` and `effort_controllers`.
   - Harmonic/Jazzy path should be treated as a rewrite/adopt of `gz_ros2_control`, not a line-by-line plugin port.

12. **CONFIRMED**: QoS, Python 3.12, and high-rate/camera bridging remain real risks.
   - ROS 2 Jazzy QoS docs state incompatible requested/offered QoS prevents delivery; expired lifespan messages are silently dropped.
   - `ros1_bridge` parameter bridge supports per-topic QoS, including special handling for `/tf_static` transient-local durability.
   - Local Noetic Python contains legacy assumptions such as `xrange` in two example scripts; broader Python 3.12 behavior should be validated during any actual port.
   - Camera-related scripts use `cv_bridge`, `CameraController`, camera services, and image publishing. RethoughtRobotics explicitly chose Zenoh because high-frequency topics like joint states and camera images performed better than DDS in its bridge design.
   - URLs: https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst, https://raw.githubusercontent.com/ros2/ros1_bridge/master/README.md, https://raw.githubusercontent.com/RethoughtRobotics/baxter-zenoh/main/ARCHITECTURE.md

### New Developments Since Existing Research

- RethoughtRobotics has published a small but relevant Baxter ROS 2 ecosystem in May-June 2026: `BaxterSDK`, `baxter-zenoh`, and a custom `ros1_bridge` fork.
- `rmw_zenoh` is now an official ROS 2 org repository with binary-install guidance, Jazzy-supported branches, and active development. It is not the default RMW, but it is relevant because RethoughtRobotics uses Zenoh to reduce bridge/discovery/high-rate topic pain.
- `angysof16/BaxterMotionPlanning` is active through 2026-06-07 and claims MoveIt2/Gazebo/ros2_control phases complete, but latest commit message mentions IK still not processed correctly for `/move_server`; S02/S05 should inspect functionality before adopting.
- The ROS/Gazebo pairing story is stronger now: Jazzy docs and Gazebo docs both explicitly identify Harmonic as the recommended/default Jazzy Gazebo pairing.

## Decisions

- Keep the existing high-level architecture assumption: Jazzy workstation + bridge for physical robot + Harmonic/MoveIt2/ros2_control for simulation.
- Treat upstream `ros1_bridge` on Noble/Jazzy as unsupported. For hardware, evaluate ECN `baxter_bridge` and RethoughtRobotics Docker/Zenoh bridge as candidate workarounds.
- Treat the exact physical robot internal distro as an S03/S04 verification item. Do not promise native ROS 2 upgrade; plan around a ROS 1 boundary.
- S02 must include the new RethoughtRobotics repos in the audit, despite low adoption.
- S02/S05 should verify licenses before reuse where GitHub did not detect a license (`BaxterMotionPlanning`, `baxter_legacy`, `bornaparo/baxter_moveit_config`, `dabaspark/baxter_sdk_nvidia_any_os`).

## Open Questions

- Which ROS 1 distro and firmware version does the target university Baxter actually run internally: Kinetic, Noetic via wrapper, or lab-specific image?
- Does RethoughtRobotics `baxter-zenoh` bridge real actions, emulate action semantics, or only bridge the underlying topics/services needed by its ROS 2 SDK?
- Is Zenoh acceptable for the university network/IT policy, or should the plan prefer DDS-only/ECN bridge options despite possible performance tradeoffs?
- Can `BaxterMotionPlanning` be licensed for reuse, or must it remain reference-only until a license is added?
- Are ECN `baxter_legacy` Debian/package workflows still maintained after the 2025-04-10 push, or should the plan prefer containerized bridge images?

## Artifacts

- Updated this S01 validation log: `logs/S01_validate_assumptions.log.md`
- Updated S01 status in `MASTER_PLAN.md`
- Appended S02 handoff prompt to `PROMPTS.md`
- Read-only local reference inspected: `baxter_noetic_ref/`
- Primary upstream references:
  - ROS 2 REP-2000: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-2000.rst
  - ROS 1 REP-0003: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0003.rst
  - ROS 2 Jazzy release docs: https://raw.githubusercontent.com/ros2/ros2_documentation/jazzy/source/Releases/Release-Jazzy-Jalisco.rst
  - ROS variants REP-2001: https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-2001.rst
  - `ros1_bridge`: https://github.com/ros2/ros1_bridge
  - Gazebo Harmonic ROS pairing docs: https://gazebosim.org/docs/harmonic/ros_installation/
  - Gazebo Classic EOL announcement: https://discourse.openrobotics.org/t/gazebo-classic-11-has-reached-end-of-life/48458
  - MoveIt 2: https://github.com/moveit/moveit2/tree/jazzy
  - MoveIt 2 tutorials: https://raw.githubusercontent.com/moveit/moveit2_tutorials/main/doc/tutorials/getting_started/getting_started.rst
  - ros2_control: https://github.com/ros-controls/ros2_control/tree/jazzy
  - gz_ros2_control: https://github.com/ros-controls/gz_ros2_control/tree/jazzy
  - Baxter after 2025 Discourse: https://discourse.openrobotics.org/t/using-baxter-after-2025/25272
  - RethoughtRobotics BaxterSDK: https://github.com/RethoughtRobotics/BaxterSDK
  - RethoughtRobotics baxter-zenoh: https://github.com/RethoughtRobotics/baxter-zenoh
  - CentraleNantesRobotics baxter_common_ros2: https://github.com/CentraleNantesRobotics/baxter_common_ros2
  - angysof16 BaxterMotionPlanning: https://github.com/angysof16/BaxterMotionPlanning
