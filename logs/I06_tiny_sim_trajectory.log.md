---
step: I06
title: "Tiny Sim Trajectory Example"
agent_date: 2026-07-08
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05]
---

# I06: Tiny Sim Trajectory Example

## Task

Fixed the missing Gazebo Harmonic sim-clock bridge (prerequisite deferred from I05), then created the smallest `baxter_examples` package with one command: `sim_tiny_trajectory`. The command sends tiny `FollowJointTrajectory` goals to both arm controllers in sim.

## Findings

### Sim clock bridge fix

Updated `src/baxter_gz_sim/launch/sim.launch.py`:
- Added unidirectional `ros_gz_bridge` `parameter_bridge` for `/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock`
- Set `use_sim_time: True` on `robot_state_publisher`

Updated `src/baxter_gz_sim/package.xml` with `<exec_depend>ros_gz_bridge</exec_depend>`.

Clock verification (sim running headless):

```text
$ ros2 topic info /clock
Publisher count: 1
Subscription count: 5

$ ros2 topic echo /clock --once
clock:
  sec: 1
  nanosec: 225000000

$ ros2 topic echo /joint_states --once
header:
  stamp:
    sec: 1
    nanosec: 360000000
```

No `No clock received` warnings appeared in the launch log after the bridge was added.

### baxter_examples / sim_tiny_trajectory

Created `src/baxter_examples/` (ament_cmake) with `sim_tiny_trajectory`:
- Reads current positions from `/joint_states`
- Sends a 2 s trajectory with a +0.15 rad offset on `left_s1` / `right_s1`
- Targets `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory`

Build verification after packaging check:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_examples
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.46s]
Starting >>> baxter_description
Finished <<< baxter_description [0.64s]
Starting >>> baxter_bringup
Starting >>> baxter_gz_sim
Finished <<< baxter_gz_sim [0.27s]
Finished <<< baxter_bringup [0.30s]
Finished <<< baxter_maintenance_msgs [2.16s]
Finished <<< baxter_examples [2.37s]
Finished <<< baxter_core_msgs [3.38s]

Summary: 7 packages finished [3.53s]
```

Gate command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash
$ ros2 launch baxter_gz_sim sim.launch.py headless:=true   # separate terminal / process group
$ ros2 control list_controllers
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true
[INFO] [sim_tiny_trajectory]: /left_arm_controller/follow_joint_trajectory: moving left_s1 0.151 -> 0.301 rad
[INFO] [sim_tiny_trajectory]: /left_arm_controller/follow_joint_trajectory succeeded
[INFO] [sim_tiny_trajectory]: /right_arm_controller/follow_joint_trajectory: moving right_s1 0.145 -> 0.295 rad
[INFO] [sim_tiny_trajectory]: /right_arm_controller/follow_joint_trajectory succeeded
[INFO] [sim_tiny_trajectory]: Tiny trajectories completed for both arms
```

Numeric motion check: `left_s1` changed from `0.150786` to `0.300792`; `right_s1` changed from `0.145276` to `0.295283`.

Gate result: passed. Both arm controllers accepted and completed the tiny trajectories in sim.

## Decisions

- Implemented the clock bridge in `baxter_gz_sim` rather than a separate step; I06 trajectory timing depends on valid sim timestamps.
- Kept `baxter_examples` as a minimal `ament_cmake` package that installs one executable script. The first `ament_python` packaging path failed under the active conda Python because `setup.py develop --editable` was not accepted during `--symlink-install`; CMake script install avoids that editable-install path without adding another layer.
- Run `sim_tiny_trajectory` with `--ros-args -p use_sim_time:=true` because `use_sim_time` is a standard ROS parameter and must not be re-declared in node code.
- Trajectory motion: +0.15 rad on shoulder pitch (`s1`) only, 2 s duration — still sim-safe but visible in the GUI.

## Open Questions

- Gazebo gripper mimic-constraint warning remains non-blocking (from I04/I05).
- Controller update-period informational warning (100 Hz CM vs 1000 Hz physics) unchanged; not required for I06.
- Project license selection still unresolved (`TODO` in package manifests).

## Artifacts

- `src/baxter_gz_sim/launch/sim.launch.py` (clock bridge + use_sim_time)
- `src/baxter_gz_sim/package.xml` (ros_gz_bridge dependency)
- `src/baxter_examples/CMakeLists.txt`
- `src/baxter_examples/package.xml`
- `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py`
- `logs/I06_tiny_sim_trajectory.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`

## Post-completion cleanup (2026-07-08)

Correction recorded per AGENTS.md (do not rewrite prior logs):

- I04 guarded `gazebosim.urdf.xacro` by patching the vcs-imported `baxter.urdf.xacro`. **Applied fix:** moved the guard to workspace-owned `baxter_bringup/urdf/baxter_description.urdf.xacro`; bringup launch now uses that file; vendor `baxter.urdf.xacro` reverted to pinned ECN SHA (clean `git status`).
- `repos/baxter_hardware.repos` import key fixed to `baxter_common_ros2`.
- `MASTER_PLAN.md` I05 description updated to note grippers deferred to I13.
- README updated to reflect I00–I06 completion.
- Added `baxter_examples/launch/sim_tiny_trajectory.launch.py` with `use_sim_time:=true` default.

Cleanup verification (2026-07-08):

```text
$ cd src/baxter_common_ros2 && git status --short
(empty)

$ python3 # I03 xacro guard with gazebo:=false
I03 xacro guard OK
robot_description_length=43384

$ ros2 control list_controllers
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ ros2 launch baxter_examples sim_tiny_trajectory.launch.py
[INFO] ... /left_arm_controller/follow_joint_trajectory succeeded
[INFO] ... /right_arm_controller/follow_joint_trajectory succeeded
[INFO] ... Tiny trajectories completed for both arms
```
