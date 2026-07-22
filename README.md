# baxter_ros2_jazzy

ROS 2 Jazzy workspace for Baxter simulation first: Gazebo Harmonic, `ros2_control`, MoveIt 2 in simulation, then hardware work only after later gates pass.

## Mode Selector

| Mode | Status | Start here |
|---|---:|---|
| Gazebo sim | passed | `docs/getting_started_sim.md` |
| Gazebo + RViz | manual/local GUI | `docs/simulation.md` |
| MoveIt sim | passed, manual/local smoke | `docs/moveit_guide.md` |
| Gazebo + MoveIt RViz | manual/local GUI | `docs/moveit_guide.md` |
| Default CI/devcontainer | passed, hardware-free | `docs/ci_release_checklist.md` |
| Hardware bridge | blocked | I10 is not started; no beginner docs yet |
| Supervised hardware motion | blocked | I12 is not started; no support claim |
| Zenoh/compatibility fallbacks | deferred | Not in the default path |

## Current Status

The supported default path is hardware-free simulation through a measured, reversible `sim_tiny_trajectory`. Both RViz profiles work: the plain RobotModel/TF one and the MoveIt MotionPlanning one, the latter with interactive-marker IK on each gripper. Hardware remains blocked.

Implemented local packages:

| Package | Purpose |
|---|---|
| `baxter_bringup` | Minimal model launch and `robot_state_publisher` path. |
| `baxter_gz_sim` | Gazebo Harmonic, fixed pedestal mount, 17-joint state, two arm controllers, plain RViz profile. |
| `baxter_examples` | Reversible direct and MoveIt motion/cancellation checks. |
| `baxter_moveit_config` | Readiness-gated MoveIt 2, IK/pose clients, and a MotionPlanning RViz profile. |

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

Run one simulation at a time. If this workspace or its underlay changes, remove generated `build/`, `install/`, and `log/` before rebuilding; never hand-edit generated setup files.

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

Expected result: both arms reach a bounded target within `0.02 rad` and return to their measured start positions.

## Devcontainer And CI

The default devcontainer and GitHub Actions workflow install only the sim/MoveIt dependencies. They do not install ROS 1, hardware bridge packages, robot-network tooling, or Zenoh.

CI checks the pinned SHA, runs `rosdep install`, builds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`, compiles/imports local Python files, loads the Gazebo Xacro/URDF, and statically checks MoveIt config.

## Support Boundary

No hardware support is claimed yet. `baxter_bridge` is bridge-host-only and is intentionally skipped in default sim/devcontainer/CI builds because it links ROS 1 libraries unavailable on clean Ubuntu 24.04/Jazzy machines.

Do not use this repo to move real hardware until I10-I12 gates pass under supervision. Beginner docs intentionally do not include raw safety-topic publishing or hardware enable commands.

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.

## Docs

Start at `docs/index.md`. Release support files: `SUPPORT.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and `docs/release_notes_v0.1.0-sim.md`.
