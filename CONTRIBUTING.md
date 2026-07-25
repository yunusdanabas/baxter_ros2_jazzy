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
| `hardware_bridge` | passed, supervised (2026-07-22) |
| supervised hardware motion | passed, supervised (2026-07-24, both arms) |
| MoveIt on hardware | passed, supervised (2026-07-24) |
| Zenoh/compatibility fallback | deferred |

Do not claim hardware support from sim evidence, and do not widen a hardware claim past the session that earned it. The gates passed on one BR-01 at low speed; fast motion, sustained duty, grippers and a second robot are all unmeasured.

## Default Checks

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Run the smallest smoke check that covers your change. Run one simulation at a time (do not rely on `ROS_DOMAIN_ID` / `GZ_PARTITION` isolation in the documented workflow). For runtime changes, require numeric final-state evidence and clean teardown as described in `docs/ci_release_checklist.md`.

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

The I10–I12 hardware gates have passed under supervision on a single BR-01. Any change to `baxter_hardware_bridge`, `scripts/py_bridge.py` or the shim safety path can move a real robot, so it needs the hardware-free evidence first: `ros2 run baxter_hardware_bridge dry_run_test` (25 cases) and, for bridge changes, `bash scripts/test_bridge_loopback.sh`. Do not add grippers, compatibility layers, or Zenoh fallback under the current release scope.

Beginner and release docs must not teach raw safety-topic publishing. The hardware runbook may document Baxter-side enable/tuck commands for supervised lab use only.

## License

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.
