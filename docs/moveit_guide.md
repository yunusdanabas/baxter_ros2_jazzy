# MoveIt Sim Guide

`baxter_moveit_config` is a MoveIt 2 simulation profile for the Gazebo `ros2_control` arm controllers. It is not a hardware profile.

## Scope

Passed I07/I08 evidence covers:

| Item | Status |
|---|---:|
| `move_group` loads | passed |
| `left_arm`, `right_arm`, `both_arms` groups | passed |
| `left_neutral`, `right_neutral` states | passed |
| fixed `world_joint` | passed |
| `/move_action` visible | passed |
| left-arm tiny plan and execute in sim | passed |

Hardware controllers, action shims, gripper motion, and supervised robot motion have not passed gates.

## Groups And States

Configured groups:

| Group | Contents |
|---|---|
| `left_arm` | `torso` to `left_gripper` chain |
| `right_arm` | `torso` to `right_gripper` chain |
| `both_arms` | `left_arm` plus `right_arm` |
| `left_hand` | left gripper links only; no controller yet |
| `right_hand` | right gripper links only; no controller yet |

Named states:

| State | Group |
|---|---|
| `left_neutral` | `left_arm` |
| `right_neutral` | `right_arm` |

Kinematics uses `kdl_kinematics_plugin/KDLKinematicsPlugin` for both arms. Planning uses OMPL with Jazzy-style `planning_plugins`, `request_adapters`, and `response_adapters` in `config/ompl_planning.yaml`.

## Controller Actions

MoveIt sim uses `MoveItSimpleControllerManager` and these controller actions:

| MoveIt controller | Action namespace | Full action |
|---|---|---|
| `left_arm_controller` | `follow_joint_trajectory` | `/left_arm_controller/follow_joint_trajectory` |
| `right_arm_controller` | `follow_joint_trajectory` | `/right_arm_controller/follow_joint_trajectory` |

MoveIt action:

```text
/move_action
```

## Launch MoveIt With Sim

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=true
```

The launch starts Gazebo first, waits briefly, then starts `move_group` with `use_sim_time:=true`.

Check actions after startup:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 action list
```

Expected relevant actions:

```text
/execute_trajectory
/left_arm_controller/follow_joint_trajectory
/move_action
/right_arm_controller/follow_joint_trajectory
```

Run the passed MoveIt smoke command:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 run baxter_examples moveit_left_tiny
```

Expected result:

```text
MoveIt left-arm plan+execute passed
```

## Known Non-Blockers

`move_group` warns that `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint` are missing from `/joint_states`. The default sim controllers intentionally expose only the 14 arm joints.

`move_group` logs `No 3D sensor plugin(s) defined for octomap updates`. No 3D sensor pipeline is in the first CI scope.

Full Gazebo plus MoveIt runtime is a manual/local smoke for now. I07 observed a possible `move_group` SIGINT teardown segfault after successful execution, so default CI uses build/import/model/MoveIt static checks instead of a full runtime teardown gate.
