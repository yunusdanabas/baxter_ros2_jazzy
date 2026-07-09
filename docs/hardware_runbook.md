# Baxter Hardware Runbook

## Prerequisites

- Laptop on the same network as Baxter (192.168.1.x)
- ROS 2 Jazzy workspace built: `colcon build --base-paths src --packages-skip baxter_bridge`
- Baxter powered on with ROS 1 master running

## Quick Start (3 terminals)

### Terminal 1: Start the bridge

```bash
cd ~/baxter_ros2_jazzy
source scripts/baxter_env.sh
python3 scripts/py_bridge.py
```

This connects to Baxter's ROS 1 master, bridges `/robot/state` and `/robot/joint_states`
to ROS 2, and bridges `/robot/limb/{side}/joint_command` back to ROS 1.

Wait until you see: `Bridge started: master=http://192.168.1.224:11311`

### Terminal 2: Verify robot state (I10 non-motion gate)

```bash
cd ~/baxter_ros2_jazzy
source scripts/baxter_env.sh
ros2 topic echo /robot/state
ros2 topic hz /robot/joint_states
```

You should see:
- `/robot/state` messages with `ready=true enabled=true stopped=false error=false`
- `/robot/joint_states` at a stable rate with all 14 arm joints + head_pan

### Terminal 3: Start action shims

```bash
cd ~/baxter_ros2_jazzy
source scripts/baxter_env.sh
ros2 launch baxter_hardware_bridge hardware_bringup.launch.py
```

This starts `FollowJointTrajectory` action servers on:
- `/robot/limb/left/follow_joint_trajectory`
- `/robot/limb/right/follow_joint_trajectory`

## I10 Non-Motion Gate Checklist

Run these BEFORE any motion:

1. **Network**: `ping 192.168.1.224` works
2. **Bridge running**: Terminal 1 shows "Bridge started"
3. **Robot state**: `ros2 topic echo /robot/state` shows safe state
4. **Joint states**: `ros2 topic hz /robot/joint_states` is stable
5. **Action servers**: `ros2 action list` shows both follow_joint_trajectory actions
6. **Safety check**: `ros2 run baxter_hardware_bridge baxter_safety_check` prints safe=true

## I11 Action Shim Gate (no motion yet)

```bash
# Verify shims reject unsafe goals:
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [bad_name], points: []}}" \
  --feedback
# Expected: REJECTED (bad joint names)
```

## I12 Supervised Hardware Motion

**REQUIRES physical supervision, clear workspace, e-stop reachable.**

```bash
# Tiny left-arm trajectory (0.15 rad on left_s1, 2 sec)
ros2 action send_goal /robot/limb/left/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {
    joint_names: [left_s0, left_s1, left_e0, left_e1, left_w0, left_w1, left_w2],
    points: [{positions: [0, -0.55, 0, 0.75, 0, 1.26, 0], time_from_start: {sec: 0}},
             {positions: [0, -0.40, 0, 0.75, 0, 1.26, 0], time_from_start: {sec: 2}}]
  }}" --feedback
```

## If Baxter's ROS 1 Master Is Not Responding

SSH into Baxter and restart it:

```bash
ssh rethink@192.168.1.224
# On Baxter:
sudo service roscore stop
sudo service roscore start
# Or manually:
roscore &
```

## Safety Rules

- **Never** publish to `/robot/set_super_enable` from beginner examples
- **Never** publish to `/robot/set_super_stop` for routine cancellation
- Action shims hold position on cancel (publish current positions via JointCommand)
- Speed ratio defaults to 0.1 (10%) — keep it low for labs
- Physical e-stop is the primary emergency stop
- No motion until I10 gate passes
