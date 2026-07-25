# Support

This is a community/university ROS 2 Jazzy workspace. It is not official Baxter vendor support and it does not migrate Baxter firmware to ROS 2.

## Supported Profiles

| Profile | Support label | What is covered |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, arm controllers, `/joint_states`, `sim_tiny_trajectory`. |
| `sim_rviz` | passed, manual/local GUI | Checked-in RobotModel/TF profile with complete independent state. |
| `sim_moveit` | passed, manual/local smoke | Readiness-gated MoveIt 2 with reversible left/right/both-arm execution. |
| `sim_moveit_rviz` | passed, manual/local GUI | Checked-in MotionPlanning profile with OMPL/RRTConnect. |
| default CI/devcontainer | passed, hardware-free | Build, import/model checks, static MoveIt checks. |
| `hardware_bridge` | passed, supervised | I10 non-motion and I11 interlock gates, 2026-07-22, BR-01 `011412P0024`. |
| supervised hardware motion | passed, supervised | I12 gate, 2026-07-24, both arms, low speed. One session on one robot. |
| MoveIt on hardware | passed, supervised | 2026-07-24, planned and executed through the shims. Single session. |
| Zenoh/compatibility fallback | deferred | Not in default install/devcontainer/CI. |

## Scoped Limitations

- Gripper source state and mimic TF are available, but gripper commands and DART mimic-contact fidelity are not supported.
- The empty-world MoveIt profile has no 3D octomap sensor. Sensed-obstacle avoidance is not a support claim.
- Display and hand-sensor links with visual-only geometry are not exact collision volumes.
- Full Gazebo plus MoveIt runtime remains a manual/local gate; a teardown crash or leftover process is a failure.
- Hardware figures come from one supervised session at low speed: worst in-flight tracking lag 0.0352 rad, a 5.7× margin under the 0.2 rad path tolerance. Fast motion near the shim's 2.0 rad/s clamp is uncharacterised, and so is sustained duty.
- Gripper joint *states* reach ROS 2 since 2026-07-24; gripper *commands* are still not implemented.
- The Jazzy MoveIt 2.12.4 profile carries a sim-only shutdown workaround for upstream `moveit/moveit2#3721`.

## How To Ask For Help

Use the issue template matching the affected profile. Include the default build command, source pin, logs, and whether hardware was involved.

Never move a real Baxter with this unsupervised or without the e-stop in hand. The I10–I12 gates have passed, on one robot; that is a starting point for a supervised session, not permission to run it unattended. Follow `docs/hardware_runbook.md`.
