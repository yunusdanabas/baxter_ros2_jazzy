# Changelog

All notable changes for this repository are tracked by release profile.

## Unreleased

### Added

- **Supervised hardware motion, on a real Baxter.** On 2026-07-24 the I12 gate passed on BR-01 `011412P0024`: a tiny low-speed trajectory per arm, out and back, every goal returning `error_code: 0` with action feedback, worst tracking error 0.0078 rad. The I10 non-motion and I11 safety-interlock gates passed on 2026-07-22. MoveIt planned *and executed* on the robot through the same shims (31 waypoints, all 7 joints). This is one supervised session on one robot, not a general support claim — see Support Labels below.
- Trajectory shim safety gate on the `/robot/state` publisher count: motion is refused unless exactly one node publishes the state being read, and `hardware_bringup.launch.py` aborts if `mock_baxter_robot` is running. A stale mock publishing a fake "safe" state alongside the real disabled robot went unnoticed for ~15 minutes during the hardware session, and a safety gate that samples "the latest" message cannot tell which robot it is reading. `dry_run_test` grew a case for it; the suite is 25.
- Real ROS 1 md5sum and message definition on the four types `py_bridge.py` publishes. `rosbag` stores whatever the publisher advertised, so the previous `md5sum "*"` recorded our `joint_command` with an empty schema and the payload could not be deserialised afterwards. The wildcard remains on the subscribe side, where it is what lets the bridge carry any type with no schema table.
- `duration` and `offset` parameters on `sim_tiny_trajectory`, so a run can approach the shim's 2.0 rad/s per-cycle clamp. Distance and duration were hardcoded at 0.12 rad/s, which is why every tolerance figure in this repo describes gentle motion only. The per-move log line now reports the resulting rad/s.
- `ik_service_client`: ROS 2 port of the ROS 1 Baxter IK example, querying MoveIt `/compute_ik` instead of the robot-only `baxter_core_msgs/SolvePositionIK`.
- `docs/known_issues.md`: resolved defects with their root cause, and the benign log noise to ignore.
- Hardware-free `dry_run_test` mid-goal cancel and unsafe-abort coverage; CI now compiles and runs `baxter_hardware_bridge` dry-run.
- Trajectory shim path-tolerance monitoring (`path_tolerance_rad`, default 0.2) and a stopped-velocity check at goal end (`stopped_velocity_tolerance`, default 0.25, after a `goal_time_sec` settle window of 0.1), all three from Rethink's `PositionJointTrajectoryActionServer.cfg`. They abort with the standard `PATH_TOLERANCE_VIOLATED` / `GOAL_TOLERANCE_VIOLATED` codes and **hold**, unlike a safety abort which stops commanding. Path tolerance measures against the command actually published rather than the raw interpolated setpoint, and holds the *measured* pose so a blocked arm is not driven further into whatever is blocking it. It is skipped in `mock_mode`, where nothing is published and the arm cannot track by construction.
- `mock_mode` launch argument on `dry_run.launch.py`, so the closed-loop rehearsal against `mock_robot` is one launch instead of three hand-started nodes.
- `dry_run_test` cases for both tolerance branches and for the clamp-limited velocity rejection, plus `MockRobot.command_feedthrough` / `MockRobot.velocity` to drive them; the suite is now 25 cases.
- Session recorders `scripts/record_ros1.sh` and `scripts/record_ros2.sh`, writing to a gitignored `data/sessions/<date>/{ros1,ros2}/`. The ROS 1 side records the robot master's full topic set from inside the Noetic container (so topics the bridge does not carry are captured too) plus a topic/node/param inventory; the ROS 2 side records the bridged and shim view together with the git revision and the live node parameters, so a bag is always matched to the tolerances that produced it. Both refuse to start below `MIN_FREE_GB` rather than fill the disk mid-session. The ROS 2 recorder passes `--include-hidden-topics`: action feedback and status live under `.../_action/...` and a plain `-a` silently drops them. The ROS 1 recorder takes an optional `TOPICS_RE` regex so a run can capture just the topics a question needs instead of everything — including `/robot/ref_joint_states`, the robot's own commanded reference and better tracking-error ground truth than anything reconstructed from the command side.
- `docs/hardware_day_plan.md`: stage-by-stage plan for a full robot day, with abort criteria per stage and a documented pivot when the robot cannot be enabled.
- `docs/noetic_native_notes.md`: robot-side behavior notes for a future native ROS 1 Noetic stack, seeded with the enable-from-tucked deadlock, `JointCommand` timeout semantics, the ROS 1 `Header.seq` wire gotcha, and the robot's measured topic inventory (202 published topics across 23 nodes).
- `docs/container_free_path.md`: what still requires the ~5 GB `baxter-noetic` image and what does not. Because `py_bridge.py` negotiates TCPROS with a wildcard md5sum when it *subscribes*, receiving a new message type needs no md5 table and no message definition, only correct payload bytes — so enable/disable (`std_msgs/Bool` plus `std_msgs/Empty` collision suppression at 20 Hz) and `/robot/ref_joint_states` (already-supported `sensor_msgs/JointState`) are both small additions over the existing pure-Python primitives. Untucking is documented as the one real exception: tucked arms sit at `s1 = -2.175`, outside the URDF limit table, so the shim rejects the pose by design and a container-free untuck would command outside the safety envelope.
- `hardware_moveit.launch.py` and a `controllers` / `joint_states_topic` argument pair on `move_group.launch.py`, so MoveIt can plan against the hardware action shims (`moveit_controllers_hardware.yaml`) instead of Gazebo. Verified against `mock_robot`: move_group loads both shim action servers as its controllers. Execution is driven from the RViz MotionPlanning panel — `moveit_left_tiny` refuses to move unless move_group is on simulated time, deliberately, so a sim example can never command the robot. Run on hardware 2026-07-24: planner SUCCESS over 31 waypoints, executed through the shims with no tolerance abort, settling 0.0128 rad from target (against 0.0043–0.0078 rad for a single-joint scripted move). Getting there took three fixes — MoveIt's leading `t=0` start point, its alphabetical joint ordering, and an SRDF false-positive self-collision of 1.7 mm that made the planner refuse the robot's own untuck pose.

### Changed

- `scripts/baxter_env.sh` drops an active conda/mamba install from `PATH`. Its `python3` shadows the system one, and rclpy's C extension is built for the system interpreter, so `python3 scripts/py_bridge.py` failed with `No module named 'rclpy._rclpy_pybind11'` in any shell where the env was active. The same shadowing also poisons a *build*: setuptools bakes the active interpreter into every installed entry point's shebang, so a workspace built from a conda-active shell compiles cleanly and then fails at runtime on every `ros2 run` and on the shim launch. `docs/hardware_runbook.md` now states that the environment script must be sourced before `colcon build`, with the one-line check for a poisoned shebang.
- `scripts/test_bridge_loopback.sh` takes `IMAGE` from the environment and defaults to the maintained `baxter-noetic:n07` instead of the hardcoded `baxter-noetic:audit`, which nothing in the repo builds.

### Fixed

- `py_bridge` overwriting `header.stamp` on every bridged `/robot/joint_states` message with the moment it happened to dequeue it. The robot's own sample time never reached ROS 2, which made cross-bag latency measurement impossible. The stamp is now published as received; bridge receive time is used only when the incoming stamp is exactly 0, and a stamp more than 0.5 s from this host's clock raises one throttled warning, because a robot and a workstation that disagree about the time make MoveIt discard states as stale without saying why.
- The cancel-hold check in `sim_tiny_trajectory` judging the arm before it had settled. It compared two joint states taken the instant the cancel returned, so on a real arm it measured the deceleration transient — about 0.02 rad, right at the 0.02 rad threshold — and reported a hold failure for an arm that was in fact holding to 0.0004 rad over 6 s. It now retries a one-second window until the arm is quiet, bounded by the same settle timeout the goal check uses.
- `py_bridge` exiting 1 with an `RCLError: rcl_shutdown already called` traceback on every clean stop. rclpy's SIGINT handler shuts the context down before `spin()` returns, so the `shutdown()` in the `finally` was always the second one, and a guaranteed failure on the normal path leaves a real shutdown error nowhere to show.
- `scripts/baxter_env.sh` killing any caller running under `set -e` whenever the robot was off the network: `getent hosts` and `ip route get <hostname>` both fail, and their command substitutions were unguarded. This had silently made `scripts/test_bridge_loopback.sh` unrunnable on any desk day — it sets `set -eo pipefail` and sources the environment before it can test anything.
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
- Documented `baxter_hardware_bridge` as prep-only / unsupported until I10. The I10, I11 and I12 gates have since passed; the package and its documentation are no longer prep-only, and the labels below record what the gates actually cover.

### Support Labels

Supersedes the `v0.1.0-sim` table for the next release. Hardware labels name the
session that earned them, per this project's rule that a claim points at a gate.

| Profile | Label |
|---|---:|
| `sim` | passed |
| `sim_moveit` | passed, manual/local smoke |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | passed — 2026-07-22, BR-01 `011412P0024` |
| supervised hardware motion | passed — supervised, 2026-07-24, BR-01 `011412P0024`, both arms |
| MoveIt on hardware | passed — supervised, 2026-07-24, single session |
| grippers | not implemented; gripper joint *states* bridge since 2026-07-24 |
| Zenoh/compatibility fallback | deferred |

These cover one supervised session on one BR-01. Tracking figures were measured
at low speed — worst in-flight lag 0.0352 rad, a 5.7× margin under the 0.2 rad
path tolerance — and nothing here characterises fast motion, sustained duty, or
a second robot.

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
