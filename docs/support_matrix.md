# Support Matrix

What is tested, what is imported, what is pinned, and what is deferred. This is
the canonical support table; `README.md` carries a short version of it for the
landing page and nothing else should restate it.

Statuses come from I01-I09, I14 and I15 gate evidence for simulation; I10-I12
for hardware; and I20 for speed / path-tolerance and the SRDF re-run. **Anything
not listed as passed is not a support claim.**

## Tested Profile

| Layer | Version/profile | Status | Evidence |
|---|---|---:|---|
| OS | Ubuntu 24.04 Noble | passed | Local and CI-equivalent checks in I08. |
| ROS 2 | Jazzy | passed | All build/check commands source `/opt/ros/jazzy/setup.bash`. |
| Gazebo | Harmonic via `ros-jazzy-ros-gz` | passed | Fixed pedestal, numeric/GUI reversible arm motion. |
| ros2_control | Jazzy `gz_ros2_control` and controllers | passed | 14 commanded arm joints, 17 independent states, enforced limits. |
| MoveIt 2 | `2.12.4` from `ros-jazzy-moveit` | passed, manual/local smoke | OMPL plus reversible left/right/both-arm checks; local shutdown workaround for `moveit/moveit2#3721`. |
| Source pin | ECN `678bfabea8c895b4134951a6c076217a90b9e0e6` | passed | I01/I08 SHA checks. |
| Devcontainer | `.devcontainer/Dockerfile` | passed | I08 image build and read-only mounted workspace build. |
| Default CI | GitHub Actions Ubuntu 24.04 | passed | I08 CI-equivalent build/import/model/MoveIt static checks. |

## Support Profiles

| Profile | Status | Notes |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, active arm controllers, `sim_tiny_trajectory`. |
| `sim_rviz` | passed, manual/local GUI | Complete RobotModel/TF and live arm-state display. |
| `sim_moveit` | passed, manual/local smoke | Readiness-gated OMPL planning and execution. |
| `sim_moveit_rviz` | passed, manual/local GUI | MotionPlanning on `both_arms`, OMPL planner list, and a 6-DOF marker on each gripper. |
| `hardware_bridge` | passed, supervised | I10/I11, 2026-07-22, one BR-01. |
| Supervised hardware motion | passed, supervised | I12, 2026-07-24, both arms; I20 speed characterisation 2026-07-25. |
| MoveIt on hardware | passed **with limits**, supervised | I20, 2026-07-25 from RViz: left 3/11 goals, right 9/11. Use Velocity Scaling 0.1 and single-arm groups — see [moveit_guide.md](moveit_guide.md). |
| `experimental_zenoh` | deferred | Not in default install/devcontainer/CI. |

Hardware rows are one BR-01 under supervision, in dated sessions. That is not
general product support. Read [hardware_runbook.md](hardware_runbook.md) first.

## Local Packages

| Package | Step | Purpose | Support level |
|---|---:|---|---:|
| `baxter_bringup` | I03 | Minimal model launch and `robot_state_publisher`. | passed |
| `baxter_gz_sim` | I04-I06, I15 | Gazebo Harmonic, deterministic mount, arm controllers, 17-joint state, plain RViz. | passed |
| `baxter_examples` | I06-I07, I15 | Reversible direct and MoveIt motion/cancellation checks. | passed |
| `baxter_moveit_config` | I07, I15 | Readiness-gated MoveIt 2, IK/pose clients, MotionPlanning RViz. | passed |
| `baxter_hardware_bridge` | I10-I12, I17, I19 | FollowJointTrajectory shims, safety gate, mock robot, 25-case dry-run self-test. | passed on hardware, supervised |

## Imported ECN Packages

Default source: `CentraleNantesRobotics/baxter_common_ros2` at
`678bfabea8c895b4134951a6c076217a90b9e0e6`.

| Package | Default status | Notes |
|---|---:|---|
| `baxter_core_msgs` | built | ROS 2 messages. |
| `baxter_description` | built | Baxter model and meshes. |
| `baxter_maintenance_msgs` | built | ROS 2 maintenance messages. |
| `rethink_ee_description` | built | End-effector model assets. |
| `baxter_bridge` | skipped | Bridge-host-only; links ROS 1 libraries unavailable on clean Jazzy/Noble. |

Default builds must keep using:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
```

## Repos And Pins

The default source import is `repos/baxter_core.repos`:

```yaml
repositories:
  baxter_common_ros2:
    type: git
    url: https://github.com/CentraleNantesRobotics/baxter_common_ros2.git
    version: 678bfabea8c895b4134951a6c076217a90b9e0e6
```

Import from the repository root, then verify the checkout:

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p src
vcs import src < repos/baxter_core.repos
git -C src/baxter_common_ros2 rev-parse HEAD
# expect: 678bfabea8c895b4134951a6c076217a90b9e0e6
```

If `src/baxter_common_ros2` already exists, do not re-import over local changes —
verify the pin instead.

### Pin rule

Default `.repos` may include only `CentraleNantesRobotics/baxter_common_ros2` at
the full pinned SHA above. Do not add unlicensed external imports to the default
path.

1. Use a full commit SHA, not a branch or tag.
2. Update `repos/baxter_core.repos` only after re-running the default build and sim smoke.
3. Record the new SHA, commands, and evidence in the relevant step log.
4. Do not update pins as part of unrelated docs or feature work.
5. Use the `Dependency pin update` issue template, and update release notes when a public support label or compatibility row changes.

### Optional `.repos` files

| File | Current role | Default path? |
|---|---|---:|
| `repos/baxter_core.repos` | Default ECN source pin. | yes |
| `repos/baxter_sim.repos` | Empty placeholder; no external sim repos. | no-op |
| `repos/baxter_hardware.repos` | Bridge-host-only import, same ECN pin. | no |
| `repos/baxter_experimental.repos` | Empty opt-in placeholder for future fallback work. | no-op |

Hardware and experimental `.repos` files are not part of the default install,
devcontainer, or CI path.

## Scoped Limitations

| Item | Status |
|---|---|
| Gripper mimic physics | State/TF only; DART mimic contact fidelity and gripper commands are unsupported. |
| Gripper commands | Deferred. Gripper joint states bridge since 2026-07-24; commanding them is not implemented. |
| Gripper controllers | Deferred; not required for arm sim gates. |
| `No 3D sensor plugin(s) defined for octomap updates` | Expected only for empty-world/explicit-scene operation; sensed-obstacle support is not claimed. |
| Visual-only sensor/display links | Their exact geometry is not part of collision checking. |
| Camera/rendering examples | Deferred; pure headless Gazebo is camera-less in current scope. |
| Full Gazebo+MoveIt runtime in CI | Manual/local, because default CI stays hardware-free and static. |
| Zenoh fallback and compatibility layers | Deferred; no passed gate requires them. |

## Not Tested

ROS 1 bridge-host builds, gripper commands, cameras, and the Zenoh fallback have
not passed gates.

Fast motion is characterised through **~0.5 rad/s** only. Default
`path_tolerance_rad` 0.2 aborts around there, so the shim's 2.0 rad/s per-cycle
clamp is unreachable in practice (I20). Still unmeasured: sustained duty, a
second robot, and whether raising `path_tolerance_rad` to 0.3-0.4 lifts the
ceiling.
