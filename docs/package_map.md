# Package Map

## Local Implemented Packages

| Package | Step | Purpose | Support level |
|---|---:|---|---:|
| `baxter_bringup` | I03 | Minimal model launch and `robot_state_publisher`. | passed |
| `baxter_gz_sim` | I04-I06, I15 | Gazebo Harmonic, deterministic mount, arm controllers, 17-joint state, plain RViz. | passed |
| `baxter_examples` | I06-I07, I15 | Reversible direct and MoveIt motion/cancellation checks. | passed |
| `baxter_moveit_config` | I07, I15 | Readiness-gated MoveIt 2, IK/pose clients, MotionPlanning RViz. | passed |
| `baxter_hardware_bridge` | I10-I12, I17, I19 | FollowJointTrajectory shims, safety gate, mock robot, 25-case dry-run self-test. | passed on hardware, supervised |

## Imported ECN Packages

Default source: `CentraleNantesRobotics/baxter_common_ros2` at `678bfabea8c895b4134951a6c076217a90b9e0e6`.

| Package | Default status | Notes |
|---|---:|---|
| `baxter_core_msgs` | built | ROS 2 messages. |
| `baxter_description` | built | Baxter model and meshes. |
| `baxter_maintenance_msgs` | built | ROS 2 maintenance messages. |
| `rethink_ee_description` | built | End-effector model assets. |
| `baxter_bridge` | skipped | Bridge-host-only; links ROS 1 libraries unavailable on clean Jazzy/Noble. |

## Intentionally Skipped Or Deferred

| Package/work | Status | Reason |
|---|---:|---|
| Gripper commands | deferred | Gripper joint states bridge since 2026-07-24; commanding them is not implemented. |
| Fast-motion characterisation | open | Every hardware figure so far is low-speed; nothing measured near the shim's 2.0 rad/s clamp. |
| Gripper controllers | deferred | Not required for arm sim gates. |
| Camera/rendering examples | deferred | Pure headless Gazebo is camera-less in current scope. |
| Zenoh fallback | deferred | Not in default install/devcontainer/CI. |
| Compatibility layers | deferred | No passed gate requires them yet. |

Default builds must keep using:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
```
