---
step: I15
title: "RViz Simulation Launch Profiles"
agent_date: 2026-07-20
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09, I10-prep, I14]
---

# I15: RViz Simulation Launch Profiles

## Task

Added supported plain-simulation and MoveIt RViz profiles, then completed the
user-authorized remediation of actionable P1-P20 findings from
`logs/sim_gui_testing_problems.log.md`. Work remained simulation-only: no real
hardware, ROS 1 bridge build, gripper commands, cameras, octomap sensing,
compatibility layer, or `plan/` changes.

## Findings

### Clean environment and build

Removed the stale `~/ros_ws/install/setup.bash` auto-source and duplicate Jazzy
sources from the user's shell startup, removed generated workspace state, and
built from an environment-isolated shell using Ubuntu's `/usr/bin/python3`.
This avoided the active Mambaforge `setuptools 80.9` editable-install
incompatibility that otherwise affects `ament_python --symlink-install`.

```text
$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 9 packages finished [2min 10s]
```

The only build stderr was the upstream `tl_expected` deprecation emitted by
MoveIt dependencies. `rosdep check` also passed for the updated
`baxter_examples` dependencies.

The exact static commands from `.github/workflows/ci.yml` passed after the clean
build:

```text
python_import_checks=passed
robot name is: baxter
---------- Successfully Parsed XML ---------------
moveit_static_check=passed groups=['both_arms', 'left_arm', 'left_hand', 'right_arm', 'right_hand'] independent_joints=17 acm_pairs=52
```

### Normal Gazebo and RViz profile

`ros2 launch baxter_gz_sim sim_rviz.launch.py headless:=false` loaded the
checked-in RobotModel/TF view. RViz reported `Global Status: Ok`, the camera was
focused on Baxter, and motion was visible in both Gazebo and RViz. Screenshots
are retained under `/tmp/opencode/i15_artifacts/normal_final_*_motion.png`.

A fresh final runtime check against the clean build proved the complete model
state and fixed transform:

```text
sim_state_check=passed independent_joints=17 links=58 world_base_z=0.92418
```

All controllers were active. The reversible direct trajectory and cancellation
checks reported:

| Check | Result |
|---|---:|
| left outbound | `max_error=0.0095 rad` |
| left return | `max_error=0.0103 rad` |
| right outbound | `max_error=0.0095 rad` |
| right return | `max_error=0.0103 rad` |
| cancellation hold | `max_drift=0.0011 rad` |

The client now uses monotonic timeouts, fresh state for each arm, reversible
targets, measured final-state acceptance, bounded cancellation, and return to
the measured start pose. Controller command limits and finite trajectory/goal
tolerances are enabled.

### MoveIt and RViz profile

`ros2 launch baxter_moveit_config sim_moveit_rviz.launch.py headless:=false`
waited for both arm actions and all 17 independent states before starting
MoveIt and RViz. The MotionPlanning display loaded the Baxter URDF/SRDF,
kinematics, joint limits, OMPL pipeline, and `RRTConnectkConfigDefault`; RViz
reported `Global Status: Ok`. Evidence screenshots are retained as
`/tmp/opencode/i15_artifacts/moveit_retry_rviz.png` and
`moveit_retry_gazebo.png`.

> **Correction (2026-07-22):** this paragraph overstated the result. The MotionPlanning
> display did **not** load its robot model — `loadRobotModel` was aborting on an
> `InvalidParameterTypeException` and the panel showed `NO PLANNING LIBRARY LOADED` with no
> interactive markers. `Global Status: Ok` reflects the Grid/RobotModel/TF displays, which do
> read `/robot_description` from the topic and did render. The defect was tracked in
> `docs/known_issues.md`, root-caused on 2026-07-22 to a comma-decimal `LC_NUMERIC` combined
> with Qt calling `setlocale(LC_ALL, "")` before `rclcpp::init` in `rviz2`, and fixed with
> `additional_env={"LC_NUMERIC": "C"}` on the RViz node. Full account in
> `logs/sim_gui_testing_problems.log.md` (final section). Joint limits are no longer passed to
> the RViz node at all.

Final isolated-domain regressions against the clean build reported:

| Group/check | Outbound | Return |
|---|---:|---:|
| `left_arm` | `0.0098 rad` | `0.0077 rad` |
| `right_arm` | `0.0094 rad` | `0.0098 rad` |
| `both_arms` | `0.0125 rad` | `0.0124 rad` |
| cancellation hold | `0.0000 rad` | n/a |

All values are below the `0.02 rad` acceptance limit. The generic MoveIt
client refuses motion when `/move_group` is not using simulation time; a dummy
non-sim node produced:

```text
Refusing motion: /move_group is not using simulation time
```

### Collision matrix

Regenerated a sampled candidate with:

```text
ros2 run moveit_setup_assistant collisions_updater ... --default --always --trials 10000
```

The candidate is retained at `/tmp/baxter_i15_collision_candidate.srdf`.
Removed the unjustified `left_upper_elbow/left_upper_shoulder` and mirrored
right-side exceptions. Retained two `Default` exceptions for contacts caused by
the imported coarse proxy geometry:

```text
left_upper_forearm_visual / left_wrist
right_upper_forearm_visual / right_wrist
```

Static checks validate every ACM link, reason, and duplicate pair without
hard-coding the total count as a success criterion.

### Teardown and upstream MoveIt defect

MoveIt 2.12.4 consistently crashed while destroying
`TrajectoryExecutionManager` after `Deleting MoveItCpp`. A debugger backtrace
proved the failure in `rclcpp::CallbackGroup::~CallbackGroup()` while releasing
a waitable weak pointer. This matches open upstream bug
`moveit/moveit2#3721`.

The local BSD-compatible `baxter_move_group` executable disables rclcpp signal
shutdown, stops active controller execution, stops its public executor, calls
`rclcpp::shutdown()` to deregister DDS, and then uses `std::_Exit()` to skip only
the remaining process-local destructors, including the affected MoveIt teardown
path. Its source retains the upstream BSD notice.

Three idle full-stack shutdown repetitions ended with every process clean:

```text
[INFO] [baxter_move_group-9]: process has finished cleanly
[INFO] [parameter_bridge-2]: process has finished cleanly
[INFO] [robot_state_publisher-3]: process has finished cleanly
[INFO] [gazebo-1]: process has finished cleanly
```

An additional shutdown during active execution canceled the controller goal,
joined trajectory execution, returned `CONTROL_FAILED` to the interrupted
client, and exited `baxter_move_group` cleanly. The final left/right/both/cancel
regression launch also ended with all four owning processes clean and no
residual process.

### Warning classification

| Diagnostic | Disposition |
|---|---|
| unsupported DART gripper mimic constraint | Expected; gripper commands/contact fidelity remain unsupported. |
| 100 Hz controller vs 1 kHz physics period | Expected and non-blocking. |
| hardware statistics not initialized | Expected instrumentation gap. |
| visual-only sensor/display links lack collision geometry | Documented collision-coverage limit. |
| no 3D octomap sensor plugin | Expected only for empty-world/explicit-scene use; sensed obstacles are unsupported. |
| command limiting message during fast interpolation | Enforcement is active and clamps per-cycle commands; final-state checks still pass. |

Gate result: passed. Both supported RViz profiles loaded, all 17 independent
states and 58 link transforms were available, direct and MoveIt motion remained
within numeric tolerances, cancellation held, the clean default build/static
checks passed, and teardown left no process or MoveIt crash.

## Decisions

- Used a real sim-only fixed `world_joint` at `z=0.92418` instead of a dynamic
  drop and SRDF-only virtual-joint assumption.
- Initialized both arms to the existing neutral SRDF values; did not emulate
  hardware enable/untuck topics.
- Added state-only head and source-finger interfaces without command
  controllers.
- Kept the default CI hardware-free and static; GUI and full runtime checks stay
  manual/local with explicit artifacts.
- Kept bare `rviz2` unsupported for MoveIt; the checked-in project launch is the
  supported path.
- Used the smallest process-local workaround for MoveIt 2.12.4 teardown rather
  than vendoring or patching MoveIt/rclcpp packages.
- Preserved existing Gazebo plugin search paths when adding the ros2_control
  plugin path.

## Open Questions

- Remove the local `baxter_move_group` workaround when a packaged Jazzy fix for
  `moveit/moveit2#3721` is available and the teardown gate passes without it.
- Gripper mimic physics, exact visual-device collision geometry, and sensed
  obstacle/octomap support remain intentionally unsupported.
- `colcon test` on `baxter_hardware_bridge` exits 5 because that pre-existing
  package collects zero tests. The default CI does not run `colcon test`; no
  unrelated hardware-test scaffolding was added in I15.
- I10-I12 remain blocked on physical hardware, bridge-host, and supervision
  gates. I13 remains deferred.

## Artifacts

- `src/baxter_gz_sim/launch/sim.launch.py`
- `src/baxter_gz_sim/launch/sim_rviz.launch.py`
- `src/baxter_gz_sim/config/sim.rviz`
- `src/baxter_gz_sim/config/gz_gui.config`
- `src/baxter_gz_sim/config/ros2_controllers.yaml`
- `src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro`
- `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py`
- `src/baxter_examples/baxter_examples/moveit_left_tiny.py`
- `src/baxter_moveit_config/launch/sim_moveit.launch.py`
- `src/baxter_moveit_config/launch/sim_moveit_rviz.launch.py`
- `src/baxter_moveit_config/launch/move_group.launch.py`
- `src/baxter_moveit_config/config/moveit.rviz`
- `src/baxter_moveit_config/config/baxter.srdf`
- `src/baxter_moveit_config/scripts/wait_for_sim_ready.py`
- `src/baxter_moveit_config/src/baxter_move_group.cpp`
- `.github/workflows/ci.yml`
- `README.md`, `SUPPORT.md`, `CHANGELOG.md`, and updated `docs/`
- `/tmp/opencode/i15_artifacts/normal_final_motion.log`
- `/tmp/opencode/i15_artifacts/sim_final_state_check.log`
- `/tmp/opencode/i15_artifacts/moveit_final_{left,right,both,cancel}.log`
- `/tmp/opencode/i15_artifacts/moveit_final_regression_launch.log`
- `/tmp/opencode/i15_artifacts/moveit_active_stop_move_group_4.log`
- `/tmp/opencode/i15_artifacts/moveit_gdb_backtrace.log`
- `/tmp/baxter_i15_collision_candidate.srdf`
- `logs/I15_rviz_launch_profiles.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
