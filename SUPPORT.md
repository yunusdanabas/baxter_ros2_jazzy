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
| `hardware_bridge` | blocked | No support claim. I10 has not run. |
| supervised hardware motion | blocked | No support claim. I12 has not run. |
| Zenoh/compatibility fallback | deferred | Not in default install/devcontainer/CI. |

## Scoped Limitations

- Gripper source state and mimic TF are available, but gripper commands and DART mimic-contact fidelity are not supported.
- The empty-world MoveIt profile has no 3D octomap sensor. Sensed-obstacle avoidance is not a support claim.
- Display and hand-sensor links with visual-only geometry are not exact collision volumes.
- Full Gazebo plus MoveIt runtime remains a manual/local gate; a teardown crash or leftover process is a failure.
- The Jazzy MoveIt 2.12.4 profile carries a sim-only shutdown workaround for upstream `moveit/moveit2#3721`.

## How To Ask For Help

Use the issue template matching the affected profile. Include the default build command, source pin, logs, and whether hardware was involved.

Do not use this repo to move real hardware until I10-I12 gates pass under supervision.
