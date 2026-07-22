# MoveIt Sim Guide

`baxter_moveit_config` is a MoveIt 2 simulation profile for the Gazebo `ros2_control` arm controllers. It is not a hardware profile.

## Scope

Passed I07/I08 evidence covers:

| Item | Status |
|---|---:|
| `move_group` loads | passed |
| `left_arm`, `right_arm`, `both_arms` groups | passed |
| `left_neutral`, `right_neutral` states | passed |
| fixed physical `world -> base` URDF joint | passed |
| `/move_action` visible | passed |
| left, right, and both-arm reversible plan/execute checks | manual/local |

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

The launch starts Gazebo, waits for both arm action servers and all 17 independent joint states, then starts `move_group` with `use_sim_time:=true`. A timeout shuts the launch down instead of starting MoveIt against a partial simulation.

`rviz` defaults to the inverse of `headless`, so `headless:=true` (the default, used by CI) runs without RViz and `headless:=false` brings RViz up too. Override explicitly with `rviz:=true` or `rviz:=false`.

## Launch MoveIt With RViz

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false
```

The checked-in launch passes the kinematics solvers and the OMPL pipeline to RViz and uses simulation time; URDF and SRDF reach RViz over the `/robot_description` and `/robot_description_semantic` topics. Bare `rviz2` is not a supported MoveIt launch.

The MotionPlanning display opens on the `both_arms` group with `Query Goal State` enabled and a 6-DOF interactive marker on each gripper; drag a marker to pose the arm through IK, then `Plan` and `Execute`. The Grid, RobotModel, and TF displays render alongside it.

> **Only `Execute` and `Plan & Execute` move Gazebo.** Dragging a marker moves the orange goal-state ghost, and `Plan` replays the planned path on a loop (`Loop Animation: true`) — both are RViz-side previews that send nothing to the controllers, and both look like a moving robot while Gazebo sits still. If Gazebo is not moving, check `move_group` for `MoveGroupMoveAction: Received request`; no such line means RViz never sent anything. Motion is also slow by default at `Velocity Scaling: 0.30`.

> The RViz node is launched with `LC_NUMERIC=C`. Do not remove it. Qt switches the process locale before rcl parses the parameter files, and in a comma-decimal locale every double is read as a string, which kills `loadRobotModel` and empties this panel. See `known_issues.md`.

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
MoveIt left_arm reversible plan+execute passed
```

Run the generic client for either arm or both arms:

```bash
ros2 run baxter_examples moveit_tiny --ros-args -p group:=right_arm
ros2 run baxter_examples moveit_tiny --ros-args -p group:=both_arms
```

Each run verifies a bounded target against fresh `/joint_states` and returns to its measured start. To exercise cancellation, add `-p cancel_after_sec:=1.0`.
The client refuses to command a `/move_group` that is not using simulation time.

## Cartesian Goals And IK Queries

Move a gripper to an absolute point, or nudge it relative to where it is now:

```bash
ros2 run baxter_examples moveit_pose --ros-args -p group:=left_arm -p x:=0.55 -p y:=0.25 -p z:=0.15
ros2 run baxter_examples moveit_pose --ros-args -p group:=left_arm -p delta_z:=0.05
```

Targets are position-only against a 3 cm tolerance sphere in `torso` by default (`-p frame:=`), so gripper orientation is whatever IK picks. Absolute `x`/`y`/`z` and relative `delta_*` are mutually exclusive.

Ask MoveIt for joint angles without moving anything — the ROS 2 stand-in for the ROS 1 `ik_service_client.py`, which used the robot-only `baxter_core_msgs/SolvePositionIK`:

```bash
ros2 run baxter_examples ik_service_client --ros-args -p limb:=left
ros2 run baxter_examples ik_service_client --ros-args -p limb:=right
```

It calls `/compute_ik` and defaults to the seed poses from the ROS 1 example, expressed in `base`. Override with `-p x:= -p y:= -p z:=`, the `-p qx:= -p qy:= -p qz:= -p qw:=` orientation, `-p frame:=`, `-p timeout:=`, and `-p avoid_collisions:=false`. An unreachable pose prints `INVALID POSE - No Valid Joint Solution Found` and exits non-zero.

## Diagnostic Scope

| Diagnostic | Classification |
|---|---|
| `No 3D sensor plugin(s) defined for octomap updates` | Expected only for this empty-world/explicit-scene profile; obstacle sensing is not supported. |
| Visual-only display and hand-sensor links lack collision geometry | Model-coverage limitation; do not claim exact collision coverage for those devices. |
| Supplied start state ignored during combined plan-and-execute | Expected because execution starts from the current monitored state, which must be complete and fresh. |
| Missing head/source-finger state or SRDF parse failure | Failure. |
| `NO PLANNING LIBRARY LOADED` in the RViz MotionPlanning panel | Failure. Check for `Exception caught while processing action 'loadRobotModel'` and for a comma-decimal `LC_NUMERIC` reaching the RViz node; see `known_issues.md`. |
| `No robot state or robot model loaded` from `rviz2.moveit.ros.trajectory_visualization` | Failure, same cause as the row above. |
| MoveIt 2.12.4 callback-group crash during process destruction | Upstream `moveit/moveit2#3721`; the local sim-only executable stops active execution, shuts down DDS, then exits without entering the known-bad teardown path. |

The default CI remains hardware-free and static. Full Gazebo, MoveIt, and RViz execution is a manual/local gate that must also tear down without a `move_group` crash.
