# Release Notes: v0.1.0-sim

Date: 2026-07-09

This is the first public sim-first baseline for `baxter_ros2_jazzy`.

## Support Labels

| Profile | Support label | Evidence |
|---|---:|---|
| `sim` | passed at release | I04-I06 and I09 action-level gate; this did not include later GUI acceptance. |
| `sim_moveit` | passed at release, manual/local smoke | I07/I08 left-arm action-level gate; this did not include later configured RViz acceptance. |
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

## Post-Release Qualification

- I15 adds separate `sim_rviz` and `sim_moveit_rviz` gates, full independent joint state, numeric final-state checks, and teardown acceptance. See `CHANGELOG.md` and the I15 log.
- Gripper physics fidelity, visual-only sensor collision geometry, and sensed-obstacle planning remain scoped limitations rather than suppressed warnings.

## Release No-Go Checks

- No unlicensed external imports in the default `.repos` path.
- No official vendor support or native ROS 2 firmware migration claim.
- No hardware bridge or hardware motion support claim.
- No hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera stream requirement in default CI.
- Beginner and release docs do not teach raw safety-topic publishing.
