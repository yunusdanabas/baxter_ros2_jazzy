---
step: I05
title: "ros2_control Arm Controllers"
agent_date: 2026-07-08
status: completed
previous_steps: [I00, I01, I02, I03, I04]
---

# I05: ros2_control Arm Controllers

## Task

Added the smallest Gazebo Harmonic `ros2_control` support needed for Baxter arm controllers. The work stayed inside `baxter_gz_sim`: one sim Xacro overlay, one controller YAML, and controller spawner sequencing in the existing sim launch. No MoveIt, examples, CI, docs, hardware, bridge, gripper, or compatibility scaffolding was added.

## Findings

- Added `src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro` as the explicit Harmonic sim overlay. It includes the existing Baxter model pieces without the guarded legacy `gazebosim.urdf.xacro`, then adds:
  - `<ros2_control name="GazeboSimSystem" type="system">`
  - hardware plugin `gz_ros2_control/GazeboSimSystem`
  - position command interfaces and position/velocity state interfaces for all 14 arm joints
  - Gazebo plugin `libgz_ros2_control-system.so` / `gz_ros2_control::GazeboSimROS2ControlPlugin`
- Added `src/baxter_gz_sim/config/ros2_controllers.yaml` with `controller_manager`, `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller`.
- Updated `src/baxter_gz_sim/launch/sim.launch.py` to publish `robot_description` from the I05 overlay and sequence controller spawners with launch event handlers:
  1. `joint_state_broadcaster` after Baxter entity spawn
  2. `left_arm_controller` and `right_arm_controller` after broadcaster activation
- Updated `baxter_gz_sim` install metadata and runtime package dependencies for the new config/URDF and controller tools.

Xacro/URDF sanity check:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro >/tmp/opencode/baxter_gz_control.urdf && check_urdf /tmp/opencode/baxter_gz_control.urdf
robot name is: baxter
---------- Successfully Parsed XML ---------------
root Link: base has 3 child(ren)
```

Build command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.50s]
Starting >>> baxter_description
Finished <<< baxter_description [0.39s]
Starting >>> baxter_bringup
Starting >>> baxter_gz_sim
Finished <<< baxter_bringup [0.24s]
Finished <<< baxter_gz_sim [0.89s]
Finished <<< baxter_maintenance_msgs [1.99s]
Finished <<< baxter_core_msgs [3.47s]

Summary: 6 packages finished [3.69s]
```

Launch evidence from the gate run:

```text
[create-3] [INFO] [ros_gz_sim]: Entity creation successful.
[INFO] [spawner-4]: process started with pid [119158]
[gz_ros_control]: Loading joint: left_s0 ... right_w2
[spawner_joint_state_broadcaster]: Configured and activated joint_state_broadcaster
[spawner_right_arm_controller]: Configured and activated right_arm_controller
[spawner_left_arm_controller]: Configured and activated left_arm_controller
```

Gate command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 launch baxter_gz_sim sim.launch.py headless:=true
$ ros2 control list_controllers
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ python3 # subscribe to /joint_states and require all 14 arm joints
controller_gate=passed
joint_states_required_present=14/14
joint_states_missing=
```

- Gate result: passed. `ros2 control list_controllers` showed the broadcaster and both arm controllers active, and `/joint_states` contained all 14 required arm joints.
- The combined shell gate helper timed out while the long-running Gazebo launch was being torn down, after printing the passing evidence above. The leftover launch process group was stopped manually with `kill -INT`; this did not affect the gate result.
- Non-blocking runtime warnings remained: the known gripper mimic-constraint warning from I04, a controller update-period warning, and repeated controller-manager clock fallback warnings after startup. The controllers still activated and `/joint_states` published the required arm joints.

## Decisions

- Kept all I05 additions in `baxter_gz_sim` instead of modifying the imported `baxter_description` again.
- Recreated the top-level Baxter model include path in the I05 overlay to avoid loading the upstream legacy Gazebo include while still adding Harmonic-specific `gz_ros2_control` tags.
- Did not add command interface min/max tags because the imported URDF already carries joint limits and the I05 gate only requires position command/state interfaces for arm controllers.
- Did not add gripper controllers; gripper support is outside I05.

## Open Questions

- The controller manager prints clock fallback warnings after startup even though controllers activate and the gate passes. If later trajectory timing is flaky, I06 should decide whether a `/clock` bridge or launch timing tweak is needed.
- Gazebo still reports the known gripper mimic-constraint warning. This remains non-blocking until a later gripper-specific step.
- Project license selection remains unresolved; local package `package.xml` files still use `TODO`.

## Artifacts

- `src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro`
- `src/baxter_gz_sim/config/ros2_controllers.yaml`
- `src/baxter_gz_sim/launch/sim.launch.py`
- `src/baxter_gz_sim/CMakeLists.txt`
- `src/baxter_gz_sim/package.xml`
- `logs/I05_ros2_control_arm_controllers.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
