# Changelog

All notable changes for this repository are tracked by release profile.

## v0.1.0-sim - 2026-07-09

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
| `hardware_bridge` | blocked |
| supervised hardware motion | blocked |
| Zenoh/compatibility fallback | deferred |

### Pins

- `CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6`

### Not Included

- No hardware bridge tooling.
- No hardware action shims.
- No supervised hardware motion support.
- No gripper implementation.
- No Zenoh fallback.
