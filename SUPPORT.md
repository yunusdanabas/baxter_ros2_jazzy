# Support

This is a community/university ROS 2 Jazzy workspace. It is not official Baxter vendor support and it does not migrate Baxter firmware to ROS 2.

## Supported Profiles

| Profile | Support label | What is covered |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, arm controllers, `/joint_states`, `sim_tiny_trajectory`. |
| `sim_moveit` | passed, manual/local smoke | MoveIt 2 sim config and left-arm tiny plan+execute. Full Gazebo+MoveIt runtime remains manual/local smoke. |
| default CI/devcontainer | passed, hardware-free | Build, import/model checks, static MoveIt checks. |
| `hardware_bridge` | blocked | No support claim. I10 has not run. |
| supervised hardware motion | blocked | No support claim. I12 has not run. |
| Zenoh/compatibility fallback | deferred | Not in default install/devcontainer/CI. |

## Known Non-Blockers

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`; the default sim profile controls only arm joints.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensor pipeline is in the first CI scope.
- Full Gazebo plus MoveIt runtime is manual/local smoke because I07 observed a possible `move_group` SIGINT teardown segfault after successful execution.

## How To Ask For Help

Use the issue template matching the affected profile. Include the default build command, source pin, logs, and whether hardware was involved.

Do not use this repo to move real hardware until I10-I12 gates pass under supervision.
