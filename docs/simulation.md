# Simulation

`baxter_gz_sim` launches Baxter in Gazebo Harmonic with arm-only `ros2_control` controllers.

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

## Controllers

The sim overlay in `baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro` exposes the 14 arm joints to `gz_ros2_control`:

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

The default sim gate requires these arm joints:

```text
left_s0 left_s1 left_e0 left_e1 left_w0 left_w1 left_w2
right_s0 right_s1 right_e0 right_e1 right_w0 right_w1 right_w2
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

Expected result:

```text
/left_arm_controller/follow_joint_trajectory succeeded
/right_arm_controller/follow_joint_trajectory succeeded
Tiny trajectories completed for both arms
```

## Current Sim Limits

Only arm joints are controlled in the default sim profile. Grippers, cameras, hardware bridge behavior, and compatibility fallbacks are not part of the passed I09 baseline.

Pure headless Gazebo is accepted for this scope. Camera/rendering tests need a later dedicated path.
