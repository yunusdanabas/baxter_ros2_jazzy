# Experimental hardware bring-up

> **Unsupported on `main`.** This document describes the boundary around the
> experimental bridge and action-shim code. It is not a real-robot quick start,
> and this revision must not be used to command physical motion.

## Why the hardware layer is separate

Baxter's controller still exposes a ROS 1 interface. The supported ROS 2
simulation talks to standard `FollowJointTrajectory` actions, while the
experimental hardware path is split into two adapters:

1. `scripts/py_bridge.py` translates selected robot state and joint-command
   topics between Baxter's ROS 1 master and ROS 2.
2. `baxter_hardware_bridge` exposes left- and right-arm
   `FollowJointTrajectory` action shims with robot-state safety checks.

This separation lets MoveIt-facing clients keep the same ROS 2 action shape in
simulation and in a future hardware profile. It does not prove hardware parity:
network behavior, timing, cancellation, safety state, and physical motion still
require supervised validation.

## Hardware-free dry run

The action shims can be exercised against the included mock robot without a
physical Baxter or a ROS 1 installation:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run baxter_hardware_bridge dry_run_test
```

The test accepts a bounded goal in a safe mock state, rejects invalid joint
names, and rejects goals in an unsafe state. Passing it is useful software
evidence, not permission to operate hardware.

## Configuration boundary

Hardware sessions must provide all network values explicitly. The repository
does not ship a robot address or workstation address.

```bash
export BAXTER_ROBOT_IP=<robot-ip>
export ROS_IP=<workstation-ip-on-robot-network>
source scripts/baxter_env.sh
```

The pure-Python bridge likewise requires the ROS 1 master URI:

```bash
python3 scripts/py_bridge.py \
  --master http://<robot-ip>:11311 \
  --ip <workstation-ip-on-robot-network>
```

## Required validation before support

- Confirm the bridge carries complete, fresh robot and joint state without motion.
- Verify e-stop, enabled, stopped, and error-state handling with supervision.
- Review action-shim limits, timeout behavior, rejection paths, and cancellation.
- Validate one arm at a time at conservative speed with the workspace clear and
  the physical e-stop reachable.
- Record the exact source revision and results without committing robot serials,
  MAC addresses, LAN topology, raw bags, or operator-session data.

Until those checks are reviewed on `main`, hardware operation remains unsupported.
