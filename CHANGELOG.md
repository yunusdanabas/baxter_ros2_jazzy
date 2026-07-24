# Changelog

All notable changes for this repository are tracked by release profile.

## Unreleased

### Added

- `ik_service_client`: ROS 2 port of the ROS 1 Baxter IK example, querying MoveIt `/compute_ik` instead of the robot-only `baxter_core_msgs/SolvePositionIK`.
- `docs/known_issues.md`: resolved defects with their root cause, and the benign log noise to ignore.
- Hardware-free `dry_run_test` mid-goal cancel and unsafe-abort coverage; CI now compiles and runs `baxter_hardware_bridge` dry-run.
- Trajectory shim path-tolerance monitoring (`path_tolerance_rad`, default 0.2) and a stopped-velocity check at goal end (`stopped_velocity_tolerance`, default 0.25, after a `goal_time_sec` settle window of 0.1), all three from Rethink's `PositionJointTrajectoryActionServer.cfg`. They abort with the standard `PATH_TOLERANCE_VIOLATED` / `GOAL_TOLERANCE_VIOLATED` codes and **hold**, unlike a safety abort which stops commanding. Path tolerance measures against the command actually published rather than the raw interpolated setpoint, and holds the *measured* pose so a blocked arm is not driven further into whatever is blocking it. It is skipped in `mock_mode`, where nothing is published and the arm cannot track by construction.
- `mock_mode` launch argument on `dry_run.launch.py`, so the closed-loop rehearsal against `mock_robot` is one launch instead of three hand-started nodes.
- `dry_run_test` cases for both tolerance branches and for the clamp-limited velocity rejection, plus `MockRobot.command_feedthrough` / `MockRobot.velocity` to drive them; the suite is now 20 cases.
- Session recorders `scripts/record_ros1.sh` and `scripts/record_ros2.sh`, writing to a gitignored `data/sessions/<date>/{ros1,ros2}/`. The ROS 1 side records the robot master's full topic set from inside the Noetic container (so topics the bridge does not carry are captured too) plus a topic/node/param inventory; the ROS 2 side records the bridged and shim view together with the git revision and the live node parameters, so a bag is always matched to the tolerances that produced it. Both refuse to start below `MIN_FREE_GB` rather than fill the disk mid-session. The ROS 2 recorder passes `--include-hidden-topics`: action feedback and status live under `.../_action/...` and a plain `-a` silently drops them. The ROS 1 recorder takes an optional `TOPICS_RE` regex so a run can capture just the topics a question needs instead of everything — including `/robot/ref_joint_states`, the robot's own commanded reference and better tracking-error ground truth than anything reconstructed from the command side.
- `docs/hardware_day_plan.md`: stage-by-stage plan for a full robot day, with abort criteria per stage and a documented pivot when the robot cannot be enabled.
- `docs/noetic_native_notes.md`: robot-side behavior notes for a future native ROS 1 Noetic stack, seeded with the enable-from-tucked deadlock, `JointCommand` timeout semantics and the ROS 1 `Header.seq` wire gotcha.
- `hardware_moveit.launch.py` and a `controllers` / `joint_states_topic` argument pair on `move_group.launch.py`, so MoveIt can plan against the hardware action shims (`moveit_controllers_hardware.yaml`) instead of Gazebo. Verified against `mock_robot`: move_group loads both shim action servers as its controllers. Execution is driven from the RViz MotionPlanning panel — `moveit_left_tiny` refuses to move unless move_group is on simulated time, deliberately, so a sim example can never command the robot. Not yet run on hardware.

### Changed

- `scripts/baxter_env.sh` drops an active conda/mamba install from `PATH`. Its `python3` shadows the system one, and rclpy's C extension is built for the system interpreter, so `python3 scripts/py_bridge.py` failed with `No module named 'rclpy._rclpy_pybind11'` in any shell where the env was active. The same shadowing also poisons a *build*: setuptools bakes the active interpreter into every installed entry point's shebang, so a workspace built from a conda-active shell compiles cleanly and then fails at runtime on every `ros2 run` and on the shim launch. `docs/hardware_runbook.md` now states that the environment script must be sourced before `colcon build`, with the one-line check for a poisoned shebang.
- `scripts/test_bridge_loopback.sh` takes `IMAGE` from the environment and defaults to the maintained `baxter-noetic:n07` instead of the hardcoded `baxter-noetic:audit`, which nothing in the repo builds.

### Fixed

- `sim_tiny_trajectory`, `moveit_pose` and `moveit_left_tiny` losing the original exception when an interrupt coincided with a failing cancellation. The `except BaseException` cleanup called `_cancel_active_goal()` unguarded, so a `RuntimeError` from the cancel replaced the in-flight `KeyboardInterrupt` before the bare `raise` was reached; `main()` then dispatched to `except Exception` and reported the cancellation error instead of the interrupt. The cleanup is now wrapped and its failure logged, and CI rejects the unguarded shape.
- Goal validation accepting a wrist segment the shim could never deliver. `JOINT_LIMITS` allows 4.0 rad/s on `w0`/`w1`/`w2` but `max_step_rad_per_cycle` caps every joint at 2.0 rad/s, so such a goal was accepted and then fell progressively behind its setpoint. Validation now rejects against `min(URDF limit, max_step_rad_per_cycle * command_rate)` and names which bound applied.
- `_hold_position()` republishing through a safety violation for up to `hold_duration_sec`, contradicting the shim's own "stop commanding on unsafe" rule. A hold in progress is now abandoned.
- The shim latching a velocity of `0.0` for any joint missing from a short `JointState.velocity` array, which could report a moving joint as stopped. It now preserves the last known value, matching how position is handled.
- `dry_run.launch.py` hardcoding `mock_mode: True` for both shims, so no `JointCommand` was ever published, the mock arm could never move, and every trajectory run against that launch file failed its position check.
- `moveit_pose` relative motion (`delta_x`/`delta_y`/`delta_z`), which aborted with `The parameter 'x' is not initialized` because `get_parameter()` raises on a declared-but-unset statically typed parameter.
- `sim_moveit.launch.py` starting no RViz under `headless:=false`; `rviz` now defaults to the inverse of `headless`.
- The RViz MotionPlanning display failing to load its robot model. Qt's `QApplication` calls `setlocale(LC_ALL, "")` before `rclcpp::init`, so in a comma-decimal locale rcl's YAML parser read every double as a string and `loadRobotModel` died on `InvalidParameterTypeException`. The RViz node now runs with `LC_NUMERIC=C`.
- Hardware trajectory shim production `main()` blocking cancel/safety mid-goal under single-threaded `spin()`; production and dry-run now share `MultiThreadedExecutor`.
- Safety abort no longer publishes hold commands; cancel holds last commanded pose; trajectory points with wrong position length are rejected.
- Shim commanding a large jump on the first goal after startup, because the hold/interpolation state started at all-zeros instead of the measured pose; it is now seeded from `/robot/joint_states` at each goal start, and goals are rejected until joint states have been seen.
- Shim executing two goals concurrently once it moved to `MultiThreadedExecutor`, letting two threads publish conflicting `JointCommand` values; a second goal is now rejected while one is running.
- `py_bridge` ROS 2 publishes from TCPROS threads, silent wrong-IP fallback, blocking `sendall`, incomplete unregister, and unbounded TCPROS frames. ROS 1 publishers now unregister on shutdown, and the inbound TCPROS handshake is time-bounded.
- `scripts/run_bridge.sh` and `docker/bridge_entrypoint.sh` forcing `ROS_DOMAIN_ID=42` after the documented workflow dropped domain isolation, which silently split the bridge and the action shim onto different domains.
- `sim.launch.py` starting controllers after a failed spawn; `wait_for_sim_ready` timeout now reports missing actions as well as joints.
- `moveit_pose` leaving an in-flight MoveGroup goal on interrupt.

### Changed

- Dropped `ROS_DOMAIN_ID`/`GZ_PARTITION` isolation from the documented workflow; run one simulation at a time.
- Stopped passing `joint_limits` to the RViz node and aligned `moveit.rviz` with the ROS 1 MoveIt layout.
- Added checked-in `sim_rviz` and `sim_moveit_rviz` profiles.
- Documented `baxter_hardware_bridge` as prep-only / unsupported until I10.

### Known Issues

- Fixed the physical and TF-consistent pedestal mount and completed all 17 independent joint states.
- Replaced timer-based MoveIt startup with controller/state readiness.
- Added finite controller tolerances, command-limit enforcement, reversible final-state checks, and clean cancellation.
- Qualified expected Gazebo/MoveIt warnings and support labels by profile.

## v0.1.0-sim - 2026-07-09

### Added

- Sim-first Baxter ROS 2 Jazzy workspace skeleton and pinned source import.
- Gazebo Harmonic `sim` profile with arm-only `ros2_control` controllers.
- `baxter_examples` tiny sim trajectory smoke command.
- MoveIt 2 `sim_moveit` profile with manual/local smoke evidence.
- Hardware-free devcontainer and CI workflow.
- Documentation baseline, support policy, security policy, issue templates, PR template, release notes, and maintainer handoff doc.
- BSD-3-Clause root project license for local project code.

### Support Labels

| Profile | Label |
|---|---:|
| `sim` | passed |
| `sim_moveit` | passed, manual/local smoke |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | blocked |
| supervised hardware motion | blocked |
| Zenoh/compatibility fallback | deferred |

### Pins

- `CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6`

### Not Included

- No hardware bridge tooling.
- No hardware action shims.
- No supervised hardware motion support.
- No gripper implementation.
- No Zenoh fallback.
