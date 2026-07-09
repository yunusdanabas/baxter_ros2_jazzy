# Package Map

## Local Implemented Packages

| Package | Step | Purpose | Support level |
|---|---:|---|---:|
| `baxter_bringup` | I03 | Minimal model launch and `robot_state_publisher`. | passed |
| `baxter_gz_sim` | I04-I06 | Gazebo Harmonic launch, clock bridge, arm controllers. | passed |
| `baxter_examples` | I06-I07 | `sim_tiny_trajectory` and MoveIt left-arm smoke command. | passed |
| `baxter_moveit_config` | I07 | MoveIt 2 sim config for the arm controllers. | passed, manual/local smoke |

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
| Hardware bridge package | blocked until I10 | Requires physical Baxter access, bridge host choice, and network policy. |
| Hardware action shims | blocked until I11 | Requires I10 non-motion gate first. |
| Supervised hardware motion | blocked until I12 | Requires I11 safety/action-shim gate and supervision. |
| Gripper controllers | deferred | Not required for arm sim gates. |
| Camera/rendering examples | deferred | Pure headless Gazebo is camera-less in current scope. |
| Zenoh fallback | deferred | Not in default install/devcontainer/CI. |
| Compatibility layers | deferred | No passed gate requires them yet. |

Default builds must keep using:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
```
