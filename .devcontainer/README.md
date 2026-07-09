# Devcontainer

Default ROS 2 Jazzy environment for the hardware-free sim and MoveIt path.

It imports only `repos/baxter_core.repos` when needed and builds with:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
```

No ROS 1, bridge-host, hardware, or Zenoh dependencies belong in this default container.
