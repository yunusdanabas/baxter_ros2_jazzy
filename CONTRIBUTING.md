# Contributing

This repo is sim-first. Keep changes inside the profile they actually affect.

## Supported Profiles

| Profile | Current support label |
|---|---:|
| `sim` | passed |
| `sim_rviz` | passed, manual/local GUI |
| `sim_moveit` | passed, manual/local smoke |
| `sim_moveit_rviz` | passed, manual/local GUI |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | blocked |
| supervised hardware motion | blocked |
| Zenoh/compatibility fallback | deferred |

Do not claim hardware support from sim evidence. Hardware bridge and motion claims require I10-I12 gate logs.

## Default Checks

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Run the smallest smoke check that covers your change. Use an isolated `ROS_DOMAIN_ID` and `GZ_PARTITION`; for runtime changes, require numeric final-state evidence and clean teardown as described in `docs/ci_release_checklist.md`.

## Pin And Source Rules

The default `.repos` path may include only `CentraleNantesRobotics/baxter_common_ros2` at `678bfabea8c895b4134951a6c076217a90b9e0e6`.

Pin updates must include:

1. Full proposed SHA.
2. License status.
3. Default build evidence.
4. Sim smoke evidence when the source affects sim or MoveIt.
5. Release-note impact.

Do not copy or import code/config from unlicensed repositories.

## Hardware Safety Review

Hardware bridge, safety, or motion changes are blocked until the named hardware gates reopen. Do not add hardware bridge tooling, action shims, grippers, compatibility layers, or Zenoh fallback under the sim-first release scope.

Beginner and release docs must not teach raw safety-topic publishing or hardware enable commands.

## License

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.
