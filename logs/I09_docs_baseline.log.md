---
step: I09
title: "Documentation Baseline"
agent_date: 2026-07-09
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08]
---

# I09: Documentation Baseline

## Task

Added the documentation baseline for the sim-first workspace. This was documentation-only: no hardware bridge tooling, ROS 1 dependencies, action shims, grippers, compatibility layers, optional examples, or `plan/` edits were added.

## Findings

Updated the first-screen README and docs landing page with mode selectors that mark only passed or blocked/deferred support levels:

- Gazebo sim: passed through `sim_tiny_trajectory`.
- MoveIt sim: passed as manual/local smoke from I07/I08 evidence.
- Default CI/devcontainer: passed hardware-free checks from I08.
- Hardware bridge and hardware motion: blocked, no support claim.
- Zenoh/compatibility fallbacks: deferred, not in default path.

Added the requested minimum docs:

- `docs/getting_started_sim.md`
- `docs/simulation.md`
- `docs/moveit_guide.md`
- `docs/package_map.md`
- `docs/repos_and_pins.md`
- `docs/licensing_and_sources.md`
- `docs/compatibility_matrix.md`
- `docs/ci_release_checklist.md`

Default build verification from the repository root:

```text
$ source /opt/ros/jazzy/setup.bash && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge && source install/setup.bash && test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_examples
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.32s]
Starting >>> baxter_description
Finished <<< baxter_examples [0.34s]
Finished <<< baxter_description [0.24s]
Starting >>> baxter_gz_sim
Starting >>> baxter_bringup
Finished <<< baxter_gz_sim [0.19s]
Starting >>> baxter_moveit_config
Finished <<< baxter_bringup [0.19s]
Finished <<< baxter_moveit_config [0.18s]
Finished <<< baxter_maintenance_msgs [1.36s]
Finished <<< baxter_core_msgs [2.55s]

Summary: 8 packages finished [2.70s]
```

Gate verification used the documented source sequence and sim smoke path. A first wrapper produced successful trajectory output but timed out during launch teardown; the final bounded wrapper below exited successfully.

```text
$ export ROS_DOMAIN_ID=113
$ source /opt/ros/jazzy/setup.bash
$ source /home/yunusdanabas/baxter_ros2_jazzy/install/setup.bash
$ timeout --kill-after=5s 50s bash -c "source /opt/ros/jazzy/setup.bash && source /home/yunusdanabas/baxter_ros2_jazzy/install/setup.bash && export ROS_DOMAIN_ID=113 && ros2 launch baxter_gz_sim sim.launch.py headless:=true" >/tmp/i09_sim_launch4.log 2>&1 &
$ ros2 control list_controllers
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ ros2 launch baxter_examples sim_tiny_trajectory.launch.py
[sim_tiny_trajectory-1] [INFO] [sim_tiny_trajectory]: /left_arm_controller/follow_joint_trajectory: moving left_s1 0.151 -> 0.301 rad
[sim_tiny_trajectory-1] [INFO] [sim_tiny_trajectory]: /left_arm_controller/follow_joint_trajectory succeeded
[sim_tiny_trajectory-1] [INFO] [sim_tiny_trajectory]: /right_arm_controller/follow_joint_trajectory: moving right_s1 0.145 -> 0.295 rad
[sim_tiny_trajectory-1] [INFO] [sim_tiny_trajectory]: /right_arm_controller/follow_joint_trajectory succeeded
[sim_tiny_trajectory-1] [INFO] [sim_tiny_trajectory]: Tiny trajectories completed for both arms
[INFO] [sim_tiny_trajectory-1]: process has finished cleanly [pid 810931]
```

Gate result: passed. A new user can follow the documented sim path through `sim_tiny_trajectory` using the default hardware-free build.

Boundary checks performed while writing docs:

- Default docs use `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`.
- Docs source ROS 2 Jazzy and the workspace install before runtime checks: `source /opt/ros/jazzy/setup.bash && source install/setup.bash`.
- Default source pin remains `CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6`.
- Hardware and Zenoh are documented as out of the default install/devcontainer/CI path.
- Beginner docs do not provide hardware enable commands or raw safety-topic publishing instructions.
- Project license remains documented as unresolved; no license was invented.

## Decisions

- Kept I09 docs to the minimum requested set. Future hardware setup, safety docs, troubleshooting expansion, maintainer handoff, issue templates, and release notes belong to later gated work.
- Listed `moveit_left_tiny` only in the MoveIt sim guide because it already exists and passed I07/I08 smoke evidence; no new example was added.
- Documented full Gazebo+MoveIt runtime as manual/local smoke because I07 observed possible `move_group` SIGINT teardown segfault after successful execution. Default CI remains static/build/model/MoveIt-config focused.
- Kept `baxter_bridge` documented as imported but skipped by default because it links ROS 1 libraries unavailable on clean Ubuntu 24.04/Jazzy machines.

## Open Questions

- Project license selection remains unresolved for I14.
- Whether full Gazebo+MoveIt runtime should become a default CI gate remains deferred until teardown stability is handled.
- Hardware bridge host, physical robot access, and network policy remain unresolved blockers for I10.

## Artifacts

- `README.md`
- `docs/index.md`
- `docs/getting_started_sim.md`
- `docs/simulation.md`
- `docs/moveit_guide.md`
- `docs/package_map.md`
- `docs/repos_and_pins.md`
- `docs/licensing_and_sources.md`
- `docs/compatibility_matrix.md`
- `docs/ci_release_checklist.md`
- `logs/I09_docs_baseline.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
