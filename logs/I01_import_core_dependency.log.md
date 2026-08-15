---
step: I01
title: "Import Core Dependency"
agent_date: 2026-07-08
status: completed
previous_steps: [I00]
---

# I01: Import Core Dependency

## Task

Imported the pinned ECN `baxter_common_ros2` dependency, ran rosdep for the imported sources, and built the non-bridge core packages. No local ROS 2 packages were created.

## Findings

- `repos/baxter_core.repos` was pinned to `678bfabea8c895b4134951a6c076217a90b9e0e6` as required.
- First import attempt with `vcs import src < repos/baxter_core.repos` created `src/src/baxter_common_ros2` because the repository key included `src/`. The key was corrected to `baxter_common_ros2`; the nested import created during this step was removed and the import was rerun.
- Verified imported SHA:

```text
$ git -C src/baxter_common_ros2 rev-parse HEAD
678bfabea8c895b4134951a6c076217a90b9e0e6
```

- Verified imported package inventory:

```text
$ colcon list --base-paths src
baxter_bridge	src/baxter_common_ros2/baxter_bridge	(ros.ament_cmake)
baxter_core_msgs	src/baxter_common_ros2/baxter_core_msgs	(ros.ament_cmake)
baxter_description	src/baxter_common_ros2/baxter_description	(ros.ament_cmake)
baxter_maintenance_msgs	src/baxter_common_ros2/baxter_maintenance_msgs	(ros.ament_cmake)
rethink_ee_description	src/baxter_common_ros2/rethink_ee_description	(ros.ament_cmake)
```

- rosdep completed without requiring sudo:

```text
$ source /opt/ros/jazzy/setup.bash && rosdep install --from-paths src --ignore-src -r -y
#All required rosdeps installed successfully
```

- The exact original build command was attempted, but `colcon` also discovered archived ROS 1 packages under read-only `plan/`, causing duplicate package names before any build started:

```text
$ source /opt/ros/jazzy/setup.bash && colcon build --symlink-install --packages-skip baxter_bridge
colcon ERROR colcon build: Duplicate package names not supported:
- baxter_core_msgs:
  - plan/baxter_noetic_ref/baxter_common/baxter_core_msgs
  - src/baxter_common_ros2/baxter_core_msgs
- baxter_description:
  - plan/baxter_noetic_ref/baxter_common/baxter_description
  - src/baxter_common_ros2/baxter_description
- baxter_maintenance_msgs:
  - plan/baxter_noetic_ref/baxter_common/baxter_maintenance_msgs
  - src/baxter_common_ros2/baxter_maintenance_msgs
- rethink_ee_description:
  - plan/baxter_noetic_ref/baxter_common/rethink_ee_description
  - src/baxter_common_ros2/rethink_ee_description
```

- Because `plan/` is read-only, the build gate was corrected to constrain `colcon` to implementation sources with `--base-paths src`. The corrected gate passed and built only the four non-bridge packages:

```text
$ source /opt/ros/jazzy/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [2.92s]
Starting >>> baxter_description
Finished <<< baxter_description [2.38s]
Finished <<< baxter_maintenance_msgs [24.6s]
Finished <<< baxter_core_msgs [1min 25s]

Summary: 4 packages finished [1min 26s]
```

## Decisions

- Keep `plan/` untouched and use `--base-paths src` for workspace builds while the read-only planning archive is present.
- Keep `baxter_bridge` imported but skipped from default builds; it remains bridge-host-only for I10.
- Correct `repos/baxter_core.repos` so the documented `vcs import src < repos/baxter_core.repos` command imports to `src/baxter_common_ros2`.

## Open Questions

- None for I01.

## Artifacts

- `src/baxter_common_ros2/`
- `repos/baxter_core.repos`
- `build/`
- `install/`
- `log/`
- `logs/I01_import_core_dependency.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
