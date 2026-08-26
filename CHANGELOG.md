# Changelog

All notable changes for this repository are tracked by release profile.

## Unreleased

### Added

- `ik_service_client`: ROS 2 port of the ROS 1 Baxter IK example, querying MoveIt `/compute_ik` instead of the robot-only `baxter_core_msgs/SolvePositionIK`.
- `docs/known_issues.md`: resolved defects with their root cause, and the benign log noise to ignore.
- Added package metadata and a collected import smoke test for the experimental
  `baxter_hardware_bridge` package.
- Added bag, MCAP, and session-data exclusions to the Git and Docker ignore rules.

### Fixed

- `moveit_pose` relative motion (`delta_x`/`delta_y`/`delta_z`), which aborted with `The parameter 'x' is not initialized` because `get_parameter()` raises on a declared-but-unset statically typed parameter.
- `sim_moveit.launch.py` starting no RViz under `headless:=false`; `rviz` now defaults to the inverse of `headless`.
- The RViz MotionPlanning display failing to load its robot model. Qt's `QApplication` calls `setlocale(LC_ALL, "")` before `rclcpp::init`, so in a comma-decimal locale rcl's YAML parser read every double as a string and `loadRobotModel` died on `InvalidParameterTypeException`. The RViz node now runs with `LC_NUMERIC=C`.

### Changed

- Dropped `ROS_DOMAIN_ID`/`GZ_PARTITION` isolation from the documented workflow; run one simulation at a time.
- Stopped passing `joint_limits` to the RViz node and aligned `moveit.rviz` with the ROS 1 MoveIt layout.
- Added checked-in `sim_rviz` and `sim_moveit_rviz` profiles.
- Removed embedded robot-network defaults from the environment, bridge container,
  Python bridge, and bridge launcher. Hardware sessions must now provide the robot
  master and bridge-host addresses explicitly.
- Updated the Python bridge to derive its local route from the supplied ROS 1
  master and fail with an actionable error instead of using a private-address
  fallback.
- Documented the hardware bridge as experimental and real-hardware motion as
  unsupported. Cameras, gripper commands, and tuck/untuck remain outside the ROS 2
  profile.
- Replaced placeholder maintainer metadata and removed internal comment markers.
- Renamed the first-release notes to `docs/simulation_baseline.md` so the document
  describes evidence rather than implying a tagged release.

### Removed

- Removed redistributed third-party Baxter PDFs while retaining their citations
  and original-source guidance.
- Removed private robot and workstation addresses from tracked examples and
  documentation.

### Validation

- Built all nine applicable packages with the imported ROS 1-linked
  `baxter_bridge` package skipped.
- Passed URDF loading, the hardware-free dry-run checks, and the collected test
  suite with zero failures.
- Started all three Gazebo controllers and ran the reversible two-arm tiny
  trajectory to within approximately `0.01 rad` of both measured start states.
- Verified Gazebo Harmonic with the MoveIt 2 RViz profile and both arm trajectory
  action interfaces.

### Known Issues

- Fixed the physical and TF-consistent pedestal mount and completed all 17 independent joint states.
- Replaced timer-based MoveIt startup with controller/state readiness.
- Added finite controller tolerances, command-limit enforcement, reversible final-state checks, and clean cancellation.
- Qualified expected Gazebo/MoveIt warnings and support labels by profile.

## Initial simulation baseline - 2026-07-09

### Added

- Sim-first Baxter ROS 2 Jazzy workspace skeleton and pinned source import.
- Gazebo Harmonic `sim` profile with arm-only `ros2_control` controllers.
- `baxter_examples` tiny sim trajectory smoke command.
- MoveIt 2 `sim_moveit` profile with manual/local smoke evidence.
- Hardware-free devcontainer and CI workflow.
- Documentation baseline, support policy, security policy, issue templates, PR template, release notes, and maintainer handoff doc.
- BSD-3-Clause root project license for local project code.

### Support Labels

| Profile | Label |
|---|---:|
| `sim` | passed |
| `sim_moveit` | passed, manual/local smoke |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | experimental and unsupported |
| supervised hardware motion | unsupported |
| Zenoh/compatibility fallback | deferred |

### Pins

- `CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6`

### Not Included

- No supported hardware bridge profile.
- No validated hardware action shims.
- No supervised hardware motion support.
- No gripper implementation.
- No Zenoh fallback.
