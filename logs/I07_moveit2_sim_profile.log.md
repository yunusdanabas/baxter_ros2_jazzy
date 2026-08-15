---
step: I07
title: "MoveIt 2 Sim Profile"
agent_date: 2026-07-08
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06]
---

# I07: MoveIt 2 Sim Profile

## Task

Created the minimal MoveIt 2 simulation profile for Baxter's Gazebo Harmonic `ros2_control` stack. The work added one local config-only package, `baxter_moveit_config`, with SRDF, KDL, OMPL, MoveIt controller YAMLs, and launch integration for the existing `baxter_gz_sim` sim profile.

## Findings

Added `src/baxter_moveit_config` with:

- `config/baxter.srdf`: `left_arm`, `right_arm`, `both_arms`, `left_hand`, `right_hand`, left/right end effectors, `left_neutral`, `right_neutral`, fixed `world_joint`, and a minimal allowed-collision matrix.
- `config/kinematics.yaml`: KDL for `left_arm` and `right_arm`.
- `config/ompl_planning.yaml`: Jazzy format with top-level `planning_plugins`, `request_adapters`, `response_adapters`, and RRTConnect configs.
- `config/moveit_controllers_sim.yaml`: `MoveItSimpleControllerManager` entries for `left_arm_controller/follow_joint_trajectory` and `right_arm_controller/follow_joint_trajectory`.
- `config/moveit_controllers_hardware.yaml`: separate future hardware action-shim profile targeting `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`; not hardware-tested in I07.
- `launch/move_group.launch.py`: `MoveItConfigsBuilder` launch for `move_group`.
- `launch/sim_moveit.launch.py`: includes `baxter_gz_sim/launch/sim.launch.py`, then starts `move_group` with `use_sim_time:=true`.

Build command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_examples
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.38s]
Starting >>> baxter_description
Finished <<< baxter_description [0.39s]
Starting >>> baxter_gz_sim
Starting >>> baxter_bringup
Finished <<< baxter_gz_sim [0.31s]
Starting >>> baxter_moveit_config
Finished <<< baxter_examples [1.18s]
Finished <<< baxter_moveit_config [0.34s]
Finished <<< baxter_bringup [0.99s]
Finished <<< baxter_maintenance_msgs [2.14s]
Finished <<< baxter_core_msgs [3.53s]

Summary: 8 packages finished [3.67s]
```

Static SRDF/config check:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3  # parse SRDF and load MoveItConfigsBuilder
groups=['both_arms', 'left_arm', 'left_hand', 'right_arm', 'right_hand']
neutral_states=[('left_arm', 'left_neutral'), ('right_arm', 'right_neutral')]
world_joint={'name': 'world_joint', 'type': 'fixed', 'parent_frame': 'world', 'child_link': 'base'}
disable_collisions=52
```

The first MoveIt execution attempt loaded `move_group` and active controllers, but failed with `START_STATE_IN_COLLISION` on 19 exact contacts. I added only those missing contact pairs to the SRDF collision matrix. The second run passed.

Gate command and result:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash
$ ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=true   # launched in background for the gate
$ ros2 control list_controllers
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ ros2 action list
/execute_trajectory
/left_arm_controller/follow_joint_trajectory
/move_action
/right_arm_controller/follow_joint_trajectory

$ python3  # rclpy MoveGroup action client, left_arm tiny joint-space goal, plan_only=false
moveit_goal=left_s1:0.150786->0.200786
moveit_error_code=1
planned_points=9
executed_points=0
moveit_plan_execute=passed
```

Launch log evidence from the same passing run:

```text
[move_group-8] [INFO] [move_group.moveit.moveit.ros.planning_pipeline]: Successfully loaded planner 'OMPL'
[move_group-8] [INFO] [move_group.moveit.moveit.planners.ompl.model_based_planning_context]: Planner configuration 'left_arm[RRTConnectkConfigDefault]' will use planner 'geometric::RRTConnect'.
[move_group-8] [INFO] [move_group.moveit.moveit.plugins.simple_controller_manager]: Added FollowJointTrajectory controller for left_arm_controller
[move_group-8] [INFO] [move_group.moveit.moveit.plugins.simple_controller_manager]: Added FollowJointTrajectory controller for right_arm_controller
[move_group-8] [INFO] [move_group.moveit.moveit.ros.move_group.move_action]: MoveGroupMoveAction: Received request
[gazebo-1] [INFO] [left_arm_controller]: Received new action goal
[gazebo-1] [INFO] [left_arm_controller]: Goal reached, success!
```

Gate result: passed. MoveIt loads `left_arm`, `right_arm`, `both_arms`, neutral states, and fixed `world_joint`; one-arm OMPL planning and tiny sim execution through `left_arm_controller` passed.

## Decisions

- Used the existing sim overlay `baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro` as MoveIt's `robot_description` source so MoveIt and Gazebo use the same arm joint/controller model.
- Kept I07 to one config package and one sim MoveIt launch. No CI, docs, bridge, hardware, gripper controllers, aliases, or extra examples were added.
- Included hand groups and end-effectors because the current sim URDF already includes electric gripper geometry, but did not add gripper controllers.
- Added `.setup_assistant` metadata only so `MoveItConfigsBuilder` can infer the URDF/SRDF cleanly.
- Kept the hardware controller YAML separate but unlaunched. It is only a future profile placeholder for I10-I12 action shims.

## Open Questions

- `move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states` because I05 only exposes the 14 arm joints through `ros2_control`. This did not block one-arm planning/execution.
- `move_group` logs `No 3D sensor plugin(s) defined for octomap updates`; no 3D sensor pipeline is in I07 scope.
- `move_group` can segfault during SIGINT teardown after the gate completes. It did not affect planning/execution, but I08 should avoid making full Gazebo+MoveIt shutdown a default CI requirement unless this is handled.
- Project license selection remains unresolved (`TODO` in package manifests).

## Artifacts

- `src/baxter_moveit_config/CMakeLists.txt`
- `src/baxter_moveit_config/package.xml`
- `src/baxter_moveit_config/.setup_assistant`
- `src/baxter_moveit_config/config/baxter.srdf`
- `src/baxter_moveit_config/config/kinematics.yaml`
- `src/baxter_moveit_config/config/joint_limits.yaml`
- `src/baxter_moveit_config/config/ompl_planning.yaml`
- `src/baxter_moveit_config/config/moveit_controllers_sim.yaml`
- `src/baxter_moveit_config/config/moveit_controllers_hardware.yaml`
- `src/baxter_moveit_config/launch/move_group.launch.py`
- `src/baxter_moveit_config/launch/sim_moveit.launch.py`
- `logs/I07_moveit2_sim_profile.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
