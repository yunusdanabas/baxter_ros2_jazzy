# Licensing And Sources

## Adopted Source

The default imported source is `CentraleNantesRobotics/baxter_common_ros2` at SHA `678bfabea8c895b4134951a6c076217a90b9e0e6`.

The imported repository includes `src/baxter_common_ros2/LICENSE`, a BSD-style Rethink Robotics license. Keep that license with the imported source.

## Local Project License

Local project code is licensed under BSD-3-Clause. The root `LICENSE` file covers workspace-owned code and docs, including these local packages:

| Package | License field |
|---|---|
| `baxter_bringup` | `BSD-3-Clause` |
| `baxter_gz_sim` | `BSD-3-Clause` |
| `baxter_examples` | `BSD-3-Clause` |
| `baxter_moveit_config` | `BSD-3-Clause` |

Imported sources keep their upstream license files and package metadata.

`src/baxter_moveit_config/src/baxter_move_group.cpp` is adapted from MoveIt
2.12.4's BSD-3-Clause `move_group.cpp`; its upstream copyright and license
notice are retained in the file. The local shutdown path works around
`moveit/moveit2#3721` and should be removed when the packaged Jazzy bug is fixed.

## Reference-Only Sources

The `plan/` directory is a read-only planning archive and is git-ignored. It may contain reference material used during planning, but it is not part of the implementation source tree and must not be modified by step agents.

Unlicensed or license-unclear external repositories stay reference-only or absent from default `.repos` until their license and support status are resolved.

## Default Source Boundary

Default install/devcontainer/CI may import only:

```text
CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6
```

No hardware bridge source, ROS 1 dependency source, Zenoh fallback, or unlicensed external import belongs in the default path.

## Legacy references

`docs/reference/baxter_legacy/README.md` records citations for third-party Baxter
manuals and academic material used as background. The documents themselves are not
redistributed by this repository and are not covered by the root BSD-3-Clause license.
