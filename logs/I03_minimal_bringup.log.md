---
step: I03
title: "Minimal Bringup Package"
agent_date: 2026-07-08
status: completed
previous_steps: [I00, I01, I02]
---

# I03: Minimal Bringup Package

## Task

Created the smallest local `baxter_bringup` package needed to launch the Baxter model validated in I02. The package adds only a model launch file for `robot_state_publisher`; no Gazebo, controller, MoveIt, example, CI, documentation, hardware, or bridge scaffolding was added.

## Findings

- Added config-only `ament_cmake` package `src/baxter_bringup` with one launch file: `launch/baxter_description.launch.py`.
- The launch file expands the installed `baxter_description/urdf/baxter.urdf.xacro` using `xacro` and passes it to `robot_state_publisher` as `robot_description`.
- The only launch arguments are the upstream Xacro arguments useful at this step: `pedestal` and `gazebo`, defaulting to `true` and `false`.
- Built from the repository root with `plan/` excluded from package discovery and `baxter_bridge` skipped:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.39s]
Starting >>> baxter_description
Finished <<< baxter_description [0.46s]
Starting >>> baxter_bringup
Finished <<< baxter_maintenance_msgs [1.94s]
Finished <<< baxter_bringup [1.82s]
Finished <<< baxter_core_msgs [3.75s]

Summary: 5 packages finished [3.93s]
```

- Gate verification launched `baxter_bringup` and checked `robot_state_publisher` through ROS 2 APIs. The check requested the `robot_description` parameter and subscribed to latched `/tf_static` with transient-local QoS:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash
$ ros2 launch baxter_bringup baxter_description.launch.py
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [robot_state_publisher-1]: process started with pid [301075]
[robot_state_publisher-1] [INFO] [1783506589.479526973] [robot_state_publisher]: Robot initialized
robot_description_length=58862
robot_description_required_tokens_missing=[]
tf_static_messages=1
tf_static_transforms_first_message=39
gate=passed
```

- Gate result: passed. The launch publishes a usable Baxter `robot_description` and TF from `robot_state_publisher`.

## Decisions

- Kept `baxter_bringup` config-only and limited to one model launch file for I03.
- Did not namespace `robot_state_publisher`, so the model sanity launch exposes the standard top-level `robot_description` and TF topics.
- Used launch substitutions to evaluate `pedestal` and `gazebo` at launch time instead of expanding the model when the launch file is imported.
- Left project license selection unresolved; `package.xml` uses a temporary `TODO` license marker until the repository license is decided.

## Open Questions

- Which license should local packages use before release hardening?

## Artifacts

- `src/baxter_bringup/CMakeLists.txt`
- `src/baxter_bringup/package.xml`
- `src/baxter_bringup/launch/baxter_description.launch.py`
- `logs/I03_minimal_bringup.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
