# baxter_ros2_jazzy

[![CI](https://github.com/yunusdanabas/baxter_ros2_jazzy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yunusdanabas/baxter_ros2_jazzy/actions/workflows/ci.yml)

ROS 2 Jazzy workspace for Baxter simulation first: Gazebo Harmonic, `ros2_control`, MoveIt 2 in simulation, then hardware work only after later gates pass.

## Mode Selector

| Mode | Status | Start here |
|---|---:|---|
| Gazebo sim | passed | `docs/getting_started_sim.md` |
| Gazebo + RViz | manual/local GUI | `docs/simulation.md` |
| MoveIt sim | passed, manual/local smoke | `docs/moveit_guide.md` |
| Gazebo + MoveIt RViz | manual/local GUI | `docs/moveit_guide.md` |
| Default CI/devcontainer | passed, hardware-free | `docs/ci_release_checklist.md` |
| Hardware bridge | passed, supervised | 2026-07-22 on BR-01 `011412P0024`; `docs/hardware_runbook.md` |
| Supervised hardware motion | passed, supervised | I12 2026-07-24; further supervised characterisation 2026-07-25 (I20); one BR-01; `docs/hardware_runbook.md` |
| MoveIt on hardware | passed **with limits**, supervised | 2026-07-24/25; the left arm aborts on `left_w0`/`left_e0` at default speeds — use Velocity Scaling 0.1 and single-arm groups; `docs/moveit_guide.md` |
| Zenoh/compatibility fallbacks | deferred | Not in the default path |

## Current Status

The default path is hardware-free simulation through a measured, reversible `sim_tiny_trajectory`. Both RViz profiles work: the plain RobotModel/TF one and the MoveIt MotionPlanning one, the latter with interactive-marker IK on each gripper.

The hardware path also works, under supervision. On 2026-07-24 a real Baxter (BR-01 `011412P0024`) executed tiny trajectories on both arms through the ROS 2 command path, and MoveIt planned and executed on it. A further supervised session on 2026-07-25 (I20) showed that default `path_tolerance_rad` 0.2 aborts near ~0.5 rad/s — that is the practical speed ceiling, not the shim's 2.0 rad/s per-cycle clamp. The same session found MoveIt unusable at its *default* planning speed: the left arm aborted 8 of 11 goals on `left_w0`/`left_e0`, so drive it at Velocity Scaling 0.1 and plan single-arm groups (`docs/known_issues.md`). This is still one BR-01 under supervision, not general product support — read `docs/hardware_runbook.md` before going near it.

Implemented local packages:

| Package | Purpose |
|---|---|
| `baxter_bringup` | Minimal model launch and `robot_state_publisher` path. |
| `baxter_gz_sim` | Gazebo Harmonic, fixed pedestal mount, 17-joint state, two arm controllers, plain RViz profile. |
| `baxter_examples` | Reversible direct and MoveIt motion/cancellation checks. |
| `baxter_moveit_config` | Readiness-gated MoveIt 2, IK/pose clients, and a MotionPlanning RViz profile. |
| `baxter_hardware_bridge` | FollowJointTrajectory action shims, safety gate, mock robot, and a 25-case dry-run self-test. Proven on hardware under supervision. |

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

The default devcontainer and GitHub Actions workflow install only the sim/MoveIt dependencies. They do not install ROS 1, robot-network tooling, or Zenoh. The local `baxter_hardware_bridge` package builds in the default `colcon` path and CI runs its dry-run suite; talking to a real Baxter needs the robot network and the ROS 1 side, which CI deliberately does not have.

CI checks the pinned SHA, runs `rosdep install`, builds with `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`, compiles/imports local Python files, loads the Gazebo Xacro/URDF, and statically checks MoveIt config.

## Support Boundary

Hardware support is claimed only as far as the gates go: supervised sessions on one BR-01 (I12 on 2026-07-24; I20 on 2026-07-25). I20 characterised speed up to the ~0.5 rad/s path-tolerance abort; the 2.0 rad/s clamp was not reached. Sustained duty, grippers, and a second robot remain unmeasured. `baxter_bridge` is bridge-host-only and is intentionally skipped in default sim/devcontainer/CI builds because it links ROS 1 libraries unavailable on clean Ubuntu 24.04/Jazzy machines.

Never move a real Baxter with this unsupervised or without the e-stop in hand; follow `docs/hardware_runbook.md`. Beginner docs intentionally do not include raw safety-topic publishing or hardware enable commands.

Local project code is BSD-3-Clause. Imported sources keep their upstream licenses; see `docs/licensing_and_sources.md`.

## Docs

Start at [docs/index.md](docs/index.md). Canonical support levels for every profile: [docs/support_matrix.md](docs/support_matrix.md). Verify a build without a robot: [docs/sim_test_commands.md](docs/sim_test_commands.md).

Release support files: [SUPPORT.md](SUPPORT.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and current notes in [docs/release_notes_v0.2.0.md](docs/release_notes_v0.2.0.md) (superseded notes are in [docs/archive/](docs/archive/)).
