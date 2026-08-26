[![CI](https://github.com/yunusdanabas/baxter_ros2_jazzy/actions/workflows/ci.yml/badge.svg)](https://github.com/yunusdanabas/baxter_ros2_jazzy/actions/workflows/ci.yml)

# Baxter ROS 2 Jazzy

Simulation-first ROS 2 Jazzy workspace for the Baxter Research Robot, built around
Gazebo Harmonic, `ros2_control`, and MoveIt 2. It is intended for developers who
want a reproducible modern Baxter simulation and a conservative starting point for
future hardware integration.

For the ROS Noetic/Python 3 SDK, operational tools, and Gazebo Classic sibling,
see [`baxter_noetic`](https://github.com/yunusdanabas/baxter_noetic).

## Mode Selector

| Mode | Status | Start here |
|---|---:|---|
| Gazebo sim | manually validated | `docs/getting_started_sim.md` |
| Gazebo + RViz | manually validated GUI | `docs/simulation.md` |
| MoveIt sim | manually validated | `docs/moveit_guide.md` |
| Gazebo + MoveIt RViz | manually validated GUI | `docs/moveit_guide.md` |
| Default CI/devcontainer | passing, hardware-free | `docs/ci_release_checklist.md` |
| Hardware bridge | experimental | Code is present but unvalidated on `main` |
| Supervised hardware motion | unsupported | No support claim |
| Cameras, grippers, tuck/untuck | not implemented | Outside the current ROS 2 profile |
| Zenoh/compatibility fallbacks | deferred | Not in the default path |

## Current Status

The supported default path is hardware-free simulation through a measured,
reversible `sim_tiny_trajectory`. Both RViz profiles work: the plain RobotModel/TF
view and the MoveIt MotionPlanning view with interactive-marker IK at each gripper
frame. Public CI builds the workspace and checks the robot and MoveIt
configuration; full Gazebo and GUI execution remain local runtime checks.

Implemented local packages:

| Package | Purpose |
|---|---|
| `baxter_bringup` | Minimal model launch and `robot_state_publisher` path. |
| `baxter_gz_sim` | Gazebo Harmonic, fixed pedestal mount, 17-joint state, two arm controllers, plain RViz profile. |
| `baxter_examples` | Reversible direct and MoveIt motion/cancellation checks. |
| `baxter_moveit_config` | Readiness-gated MoveIt 2, IK/pose clients, and a MotionPlanning RViz profile. |
| `baxter_hardware_bridge` | Experimental action-shim and mock-test scaffolding; not a supported hardware profile. |

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

Run one simulation at a time. If this workspace or its underlay changes, remove
generated `build/`, `install/`, and `log/` before rebuilding; never hand-edit
generated setup files.

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

The default devcontainer and GitHub Actions workflow install only the dependencies
needed for the hardware-free build. They do not install ROS 1, connect to a robot,
or start the experimental hardware bridge.

CI checks the pinned SHA, runs `rosdep install`, builds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`, compiles/imports local Python files, loads the Gazebo Xacro/URDF, and statically checks MoveIt config.

## Common pitfalls

- Use Ubuntu 24.04 with ROS 2 Jazzy, or the included devcontainer.
- Import `repos/baxter_core.repos` before building; the Baxter description is pinned
  rather than vendored.
- Build with `--packages-skip baxter_bridge`; that imported package links ROS 1
  libraries unavailable on a clean Jazzy host.
- Source both `/opt/ros/jazzy/setup.bash` and `install/setup.bash` in every new
  terminal.
- Use the checked-in launch files for RViz. Bare `rviz2` does not receive the full
  MoveIt configuration.

## Support boundary

No hardware support is claimed. `baxter_bridge` is bridge-host-only and is
intentionally skipped in default builds because it links ROS 1 libraries unavailable
on clean Ubuntu 24.04/Jazzy machines. The local `baxter_hardware_bridge` package can
be built and exercised against its mock robot, but its real-robot path has not been
validated on `main`.

Do not use this revision to move real hardware. Cameras, gripper commands, and
tuck/untuck are also outside the supported ROS 2 profile; use the Noetic sibling
when those legacy SDK tools are required.

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.

## Docs

Start at `docs/index.md`. Project support files include `SUPPORT.md`, `SECURITY.md`,
`CONTRIBUTING.md`, `CHANGELOG.md`, and `docs/simulation_baseline.md`.
