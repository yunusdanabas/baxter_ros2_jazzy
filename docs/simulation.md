# Simulation

`baxter_gz_sim` launches Baxter in Gazebo Harmonic with 14 commanded arm joints and state for all 17 independent joints.

## Launch Gazebo

Headless server mode, used by default docs:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim.launch.py headless:=true
```

GUI mode:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim.launch.py headless:=false
```

The launch uses Gazebo Harmonic through `ros_gz_sim` with the built-in `empty.sdf` world. Headless mode passes `-r -s empty.sdf`; GUI mode passes `-r empty.sdf`.

The simulation URDF fixes `world -> base` at `z=0.92418`, placing the bottom of the pedestal on the floor without a drop-and-settle phase. Both arms start at the SRDF neutral state.

## Launch Gazebo With RViz

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false
```

This is the supported plain RViz path. It loads the checked-in RobotModel/TF configuration, uses `world` as its fixed frame, and uses simulation time.

## Controllers

The sim overlay exposes position commands for 14 arm joints. `head_pan` and the two source-finger joints are state-only; no head or gripper command controller is added.

| Controller | Action |
|---|---|
| `left_arm_controller` | `/left_arm_controller/follow_joint_trajectory` |
| `right_arm_controller` | `/right_arm_controller/follow_joint_trajectory` |
| `joint_state_broadcaster` | Publishes `/joint_states` |

Check controller state:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 control list_controllers
```

Expected result:

```text
joint_state_broadcaster active
left_arm_controller active
right_arm_controller active
```

## Joint States

Check one `/joint_states` message:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 topic echo /joint_states --once
```

The complete independent-state gate requires:

```text
left_s0 left_s1 left_e0 left_e1 left_w0 left_w1 left_w2
right_s0 right_s1 right_e0 right_e1 right_w0 right_w1 right_w2
head_pan l_gripper_l_finger_joint r_gripper_l_finger_joint
```

## Tiny Trajectory Smoke

With Gazebo still running:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 launch baxter_examples sim_tiny_trajectory.launch.py
```

Equivalent direct command:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true
```

The command takes a fresh state for each arm, performs a visible limit-safe move, verifies final error at `0.02 rad` or less, and returns to the measured start position. Action success without the fresh final-state check is a failure.

`duration` (default 3.0 s) and `offset` (default 0.35 rad) set how far and how
fast the move is; the per-move log line reports the resulting rad/s. Shortening
`duration` is the way to make motion faster — on hardware, `speed_ratio` was
measured to have no effect, because the client's own interpolation is the binding
constraint.

`joint` (default `s1`) picks which arm joint moves; any of `s0 s1 e0 e1 w0 w1 w2`
works, and the client refuses a joint it has no limit table for. Both arms always
move the same joint, which is the point: on hardware, comparing the same joint
left against right is what distinguishes an asymmetric *plan* from an asymmetric
*arm*.

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args -p use_sim_time:=true -p joint:=e1
```

Cancellation check:

```bash
ros2 run baxter_examples sim_tiny_trajectory --ros-args \
  -p use_sim_time:=true -p cancel_after_sec:=1.0
```

The client must report accepted cancellation and a held state without a traceback.

## Expected Diagnostics

| Diagnostic | Classification |
|---|---|
| DART cannot create the gripper mimic physics constraint | Expected arm-only limitation. Source/mimic TF is available, but gripper contact fidelity is not supported. |
| Controller period 100 Hz is slower than Gazebo physics at 1 kHz | Expected; controllers need not run every physics step. |
| Executor unavailable during hardware initialization | Expected only when successful initialization immediately follows. |
| Hardware read/write statistics unavailable | Expected instrumentation gap. |
| Gazebo exit code `-2` after one Ctrl+C | Expected SIGINT status if no process remains. |

Missing joints, disabled command limits, controller failure, TF gaps, hangs, or leftover processes are not expected diagnostics.

## Current Sim Limits

Only arm joints are controlled. Grippers, cameras, obstacle sensing, hardware bridge behavior, and compatibility fallbacks are outside this profile.

Pure headless Gazebo is accepted for this scope. Camera/rendering tests need a later dedicated path.
