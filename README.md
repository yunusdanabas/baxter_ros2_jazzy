# baxter_ros2_jazzy

ROS 2 Jazzy workspace for Baxter simulation first: Gazebo Harmonic, `ros2_control`, MoveIt 2 in simulation, then hardware work only after later gates pass.

## Mode Selector

| Mode | Status | Start here |
|---|---:|---|
| Gazebo sim | passed | `docs/getting_started_sim.md` |
| MoveIt sim | passed, manual/local smoke | `docs/moveit_guide.md` |
| Default CI/devcontainer | passed, hardware-free | `docs/ci_release_checklist.md` |
| Hardware bridge | blocked | I10 is not started; no beginner docs yet |
| Supervised hardware motion | blocked | I12 is not started; no support claim |
| Zenoh/compatibility fallbacks | deferred | Not in the default path |

## Current Status

Implementation steps **I00-I09** plus the **I14 sim-first release baseline** are complete. The supported default path is hardware-free simulation through `sim_tiny_trajectory`, plus a MoveIt sim profile that has planned and executed a tiny left-arm motion locally.

Implemented local packages:

| Package | Purpose |
|---|---|
| `baxter_bringup` | Minimal model launch and `robot_state_publisher` path. |
| `baxter_gz_sim` | Gazebo Harmonic launch, `/clock` bridge, `gz_ros2_control`, two arm controllers. |
| `baxter_examples` | Tiny sim trajectory command and MoveIt sim smoke command. |
| `baxter_moveit_config` | MoveIt 2 config for the sim arm controllers. |

Imported dependency:

| Source | Pin | Default build |
|---|---|---|
| `CentraleNantesRobotics/baxter_common_ros2` | `678bfabea8c895b4134951a6c076217a90b9e0e6` | Build non-bridge packages; skip `baxter_bridge`. |

## Default Sim Build

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p src
vcs import src < repos/baxter_core.repos
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

If `src/baxter_common_ros2` already exists, do not re-import over local changes; verify the pin instead:

```bash
git -C src/baxter_common_ros2 rev-parse HEAD
```

Expected SHA: `678bfabea8c895b4134951a6c076217a90b9e0e6`.

## Quick Sim Smoke

Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim.launch.py headless:=true
```

Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Expected result: both `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory` succeed.

## Devcontainer And CI

The default devcontainer and GitHub Actions workflow install only the sim/MoveIt dependencies. They do not install ROS 1, hardware bridge packages, robot-network tooling, or Zenoh.

CI checks the pinned SHA, runs `rosdep install`, builds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`, compiles/imports local Python files, loads the Gazebo Xacro/URDF, and statically checks MoveIt config.

## Support Boundary

No hardware support is claimed yet. `baxter_bridge` is bridge-host-only and is intentionally skipped in default sim/devcontainer/CI builds because it links ROS 1 libraries unavailable on clean Ubuntu 24.04/Jazzy machines.

Do not use this repo to move real hardware until I10-I12 gates pass under supervision. Beginner docs intentionally do not include raw safety-topic publishing or hardware enable commands.

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.

## Docs

Start at `docs/index.md`. Release support files: `SUPPORT.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `docs/release_notes_v0.1.0-sim.md`.
