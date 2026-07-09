# Release Notes: v0.1.0-sim

Date: 2026-07-09

This is the first public sim-first baseline for `baxter_ros2_jazzy`.

## Support Labels

| Profile | Support label | Evidence |
|---|---:|---|
| `sim` | passed | I04-I06 and I09: Gazebo starts, Baxter spawns, arm controllers are active, `/joint_states` has all 14 arm joints, `sim_tiny_trajectory` succeeds for both arms. |
| `sim_moveit` | passed, manual/local smoke | I07/I08: MoveIt loads groups/states/world joint, `/move_action` is visible, tiny left-arm plan+execute passed locally. |
| default CI/devcontainer | passed, hardware-free | I08: devcontainer build and CI-equivalent build/import/model/MoveIt static checks passed. |
| `hardware_bridge` | blocked | I10 has not run; no hardware support claim. |
| supervised hardware motion | blocked | I12 has not run; no hardware motion support claim. |
| Zenoh/compatibility fallback | deferred | Not in default install/devcontainer/CI. |

## Default Source Pin

Default source import remains:

```text
CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6
```

Default `.repos` must not include other external imports.

## Default Build

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

`baxter_bridge` remains bridge-host-only and is skipped in default sim/devcontainer/CI builds.

## Known Non-Blockers

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`; I05/I07 expose only arm joints for default sim motion.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensors are in first CI scope.
- Full Gazebo plus MoveIt runtime is manual/local smoke for now because I07 observed possible `move_group` SIGINT teardown segfault after successful execution. Default CI uses build/import/model/MoveIt static checks.

## Release No-Go Checks

- No unlicensed external imports in the default `.repos` path.
- No official vendor support or native ROS 2 firmware migration claim.
- No hardware bridge or hardware motion support claim.
- No hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera stream requirement in default CI.
- Beginner and release docs do not teach raw safety-topic publishing.
