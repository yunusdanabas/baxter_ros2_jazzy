# Changelog

All notable changes for this repository are tracked by release profile.

## v0.2.0 - 2026-07-25

### Added

- `scripts/sim_smoke.sh`: one command that runs the whole no-robot verification — gates, Gazebo, MoveIt — and **asserts the numbers** rather than the exit codes. A client can exit 0 having moved the wrong joint or printed nothing at all, so every `max_error` is parsed and compared against 0.02 rad, a minimum count of verified lines is required, and the exact cancellation log strings must appear. Teardown is part of the test: one SIGINT, then failure if any simulation process survives, never escalating to SIGKILL to make the check pass. Verified by mutation — tightening the threshold, leaving a stray process, and feeding it a log with no verified lines each make it exit non-zero.
- `docs/manual/`: LaTeX sources for a 31-page printable workspace manual, assembled from `docs/` with original figures only (TikZ architecture, safety-gate and kinematic-chain diagrams, a pgfplots chart of the measured I20 lag points, a graphviz TF tree, and two RViz screenshots). Sources tracked, PDF gitignored. Every number in it is cross-checked against `docs/support_matrix.md`, and the joint-limit and shim-parameter tables against the shim source.
- `docs/publish_checklist.md`: the human-only steps between "code is ready" and "repository is presentable" — description, topics, private vulnerability reporting, merge, tag, branch protection, release — with the ordering trap that branch protection must come after the first green CI run on `main`.
- `docs/sim_test_commands.md`: a copy-paste sheet for verifying the workspace with **no robot** — build, every hardware-free CI gate with its expected output token, the Gazebo and MoveIt smokes, and the teardown orphan check. The sim counterpart to `docs/hardware_test_commands.md`, and now the single source for runnable sim commands.
- `docs/support_matrix.md`: one canonical place for support levels, tested profile, local and imported packages, the ECN pin and its update rule, and what is deferred. Merged from `compatibility_matrix.md`, `package_map.md` and `repos_and_pins.md`, which stated the pin and the support labels three times over — and support labels are exactly what must not drift, since over-broad hardware claims are a release no-go.
- First real `colcon test` surface: `src/baxter_examples/test/test_trajectory_helpers.py` covers the limit-selection logic (`choose_reversible_target`) and the joint-state readers. 16 tests. Previously `baxter_hardware_bridge` declared four `test_depend`s and the repo contained no tests at all; the unused `ament_copyright` / `ament_pep257` / `ament_flake8` declarations are gone.
- `ruff --select F` in CI, gating unused imports (`F401`) and undefined names (`F821`). `compileall` and the import checks pass happily on both, which is how nine imports orphaned by the `ament_python` refactor survived every existing gate.

- **Supervised hardware motion, on a real Baxter.** On 2026-07-24 the I12 gate passed on BR-01 `011412P0024`: a tiny low-speed trajectory per arm, out and back, every goal returning `error_code: 0` with action feedback, worst tracking error 0.0078 rad. The I10 non-motion and I11 safety-interlock gates passed on 2026-07-22. MoveIt planned *and executed* on the robot through the same shims (31 waypoints, all 7 joints). A further supervised session on 2026-07-25 (I20) characterised the path-tolerance speed ceiling — see Support Labels below. Still one BR-01, not a general support claim.
- **I20 (2026-07-25) path-tolerance speed ceiling.** Lag ≈ 0.4 s × commanded velocity; default `path_tolerance_rad` 0.2 aborts near ~0.5 rad/s (`left_s1` 0.202 vs 0.200). The 2.0 rad/s per-cycle clamp is unreachable under that tolerance. Decision: do not tighten `path_tolerance_rad` — it *is* the speed limit.
- **I20 SRDF collision matrix kept.** MoveIt Setup Assistant / `collisions_updater` sampling (10k–2M trials) does not converge; regenerated matrices wrongly disable head/gripper/screen pairs. The checked-in 54-pair matrix stays.
- **I20 `sim_tiny_trajectory` joint-state merge.** Baxter publishes arm and gripper joints on separate `/robot/joint_states` publishers; the client now merges name→position across messages (same shape as the action shim). Also gained a `joint` parameter for per-joint left/right compares.
- `scripts/check_srdf.py`, which guards the hand-added collision pairs across a Setup Assistant re-run and carries a negative control (a pose that *must* collide), so a check that silently stops checking is detectable.
- Trajectory shim safety gate on the `/robot/state` publisher count: motion is refused unless exactly one node publishes the state being read, and `hardware_bringup.launch.py` aborts if `mock_baxter_robot` is running. A stale mock publishing a fake "safe" state alongside the real disabled robot went unnoticed for ~15 minutes during the hardware session, and a safety gate that samples "the latest" message cannot tell which robot it is reading. `dry_run_test` grew a case for it; the suite is 25.
- Real ROS 1 md5sum and message definition on the four types `py_bridge.py` publishes. `rosbag` stores whatever the publisher advertised, so the previous `md5sum "*"` recorded our `joint_command` with an empty schema and the payload could not be deserialised afterwards. The wildcard remains on the subscribe side, where it is what lets the bridge carry any type with no schema table.
- `duration` and `offset` parameters on `sim_tiny_trajectory`, so commanded speed is tunable via duration/offset. I20 later showed default `path_tolerance_rad` 0.2 aborts near ~0.5 rad/s, so the 2.0 rad/s per-cycle clamp is not the binding limit. The per-move log line reports the resulting rad/s.
- `ik_service_client`: ROS 2 port of the ROS 1 Baxter IK example, querying MoveIt `/compute_ik` instead of the robot-only `baxter_core_msgs/SolvePositionIK`.
- `docs/known_issues.md`: resolved defects with their root cause, and the benign log noise to ignore.
- Hardware-free `dry_run_test` mid-goal cancel and unsafe-abort coverage; CI now compiles and runs `baxter_hardware_bridge` dry-run.
- Trajectory shim path-tolerance monitoring (`path_tolerance_rad`, default 0.2) and a stopped-velocity check at goal end (`stopped_velocity_tolerance`, default 0.25, after a `goal_time_sec` settle window of 0.1), all three from Rethink's `PositionJointTrajectoryActionServer.cfg`. They abort with the standard `PATH_TOLERANCE_VIOLATED` / `GOAL_TOLERANCE_VIOLATED` codes and **hold**, unlike a safety abort which stops commanding. Path tolerance measures against the command actually published rather than the raw interpolated setpoint, and holds the *measured* pose so a blocked arm is not driven further into whatever is blocking it. It is skipped in `mock_mode`, where nothing is published and the arm cannot track by construction.
- `mock_mode` launch argument on `dry_run.launch.py`, so the closed-loop rehearsal against `mock_robot` is one launch instead of three hand-started nodes.
- `dry_run_test` cases for both tolerance branches and for the clamp-limited velocity rejection, plus `MockRobot.command_feedthrough` / `MockRobot.velocity` to drive them; the suite is now 25 cases.
- Session recorders `scripts/record_ros1.sh` and `scripts/record_ros2.sh`, writing to a gitignored `data/sessions/<date>/{ros1,ros2}/`. The ROS 1 side records the robot master's full topic set from inside the Noetic container (so topics the bridge does not carry are captured too) plus a topic/node/param inventory; the ROS 2 side records the bridged and shim view together with the git revision and the live node parameters, so a bag is always matched to the tolerances that produced it. Both refuse to start below `MIN_FREE_GB` rather than fill the disk mid-session. The ROS 2 recorder passes `--include-hidden-topics`: action feedback and status live under `.../_action/...` and a plain `-a` silently drops them. The ROS 1 recorder takes an optional `TOPICS_RE` regex so a run can capture just the topics a question needs instead of everything — including `/robot/ref_joint_states`, the robot's own commanded reference and better tracking-error ground truth than anything reconstructed from the command side.
- `docs/hardware_day_plan.md`: stage-by-stage plan for a full robot day, with abort criteria per stage and a documented pivot when the robot cannot be enabled.
- `docs/noetic_native_notes.md`: robot-side behavior notes for a future native ROS 1 Noetic stack, seeded with the enable-from-tucked deadlock, `JointCommand` timeout semantics, the ROS 1 `Header.seq` wire gotcha, and the robot's measured topic inventory (202 published topics across 23 nodes).
- A container-free-path analysis (originally `docs/container_free_path.md`, merged into `docs/noetic_native_notes.md` for v0.2.0): what still requires the ~5 GB `baxter-noetic` image and what does not. Because `py_bridge.py` negotiates TCPROS with a wildcard md5sum when it *subscribes*, receiving a new message type needs no md5 table and no message definition, only correct payload bytes — so enable/disable (`std_msgs/Bool` plus `std_msgs/Empty` collision suppression at 20 Hz) and `/robot/ref_joint_states` (already-supported `sensor_msgs/JointState`) are both small additions over the existing pure-Python primitives. Untucking is documented as the one real exception: tucked arms sit at `s1 = -2.175`, outside the URDF limit table, so the shim rejects the pose by design and a container-free untuck would command outside the safety envelope.
- `hardware_moveit.launch.py` and a `controllers` / `joint_states_topic` argument pair on `move_group.launch.py`, so MoveIt can plan against the hardware action shims (`moveit_controllers_hardware.yaml`) instead of Gazebo. Verified against `mock_robot`: move_group loads both shim action servers as its controllers. Execution is driven from the RViz MotionPlanning panel — `moveit_left_tiny` refuses to move unless move_group is on simulated time, deliberately, so a sim example can never command the robot. Run on hardware 2026-07-24: planner SUCCESS over 31 waypoints, executed through the shims with no tolerance abort, settling 0.0128 rad from target (against 0.0043–0.0078 rad for a single-joint scripted move). Getting there took three fixes — MoveIt's leading `t=0` start point, its alphabetical joint ordering, and an SRDF false-positive self-collision of 1.7 mm that made the planner refuse the robot's own untuck pose.

### Changed

- **`docs/` reorganised for publication: 19 files down to 15 active.** `compatibility_matrix.md` + `package_map.md` + `repos_and_pins.md` merged into `support_matrix.md`; the container-free-path analysis folded into `noetic_native_notes.md`, where the native ROS 1 work it feeds already lives; `i12_completion_plan.md` (a working plan for a gate that passed 2026-07-24) and the superseded `release_notes_v0.1.0-sim.md` moved to `docs/archive/`, which says plainly that it is frozen. `docs/index.md` dropped its duplicate of the README mode selector and became pure navigation, and cross-references are now real relative links instead of bare filenames — nothing in the repo was clickable before, and nothing could check the links. `hardware_day_plan.md`'s "fast motion, the open question" phase is relabelled as characterised, because I20 answered it.
- `scripts/baxter_env.sh` drops an active conda/mamba install from `PATH`. Its `python3` shadows the system one, and rclpy's C extension is built for the system interpreter, so `python3 scripts/py_bridge.py` failed with `No module named 'rclpy._rclpy_pybind11'` in any shell where the env was active. The same shadowing also poisons a *build*: setuptools bakes the active interpreter into every installed entry point's shebang, so a workspace built from a conda-active shell compiles cleanly and then fails at runtime on every `ros2 run` and on the shim launch. `docs/hardware_runbook.md` now states that the environment script must be sourced before `colcon build`, with the one-line check for a poisoned shebang.
- `scripts/test_bridge_loopback.sh` takes `IMAGE` from the environment and defaults to the maintained `baxter-noetic:n07` instead of the hardcoded `baxter-noetic:audit`, which nothing in the repo builds.
- `scripts/baxter_env.sh`, `scripts/record_ros1.sh` and `docker/bridge_entrypoint.sh` no longer default to this lab's robot serial or LAN IP. `BAXTER_HOST` / `ROS_MASTER_URI` are now required and fail with a message naming the variable; a stale hardcoded host silently points a hardware session at the wrong machine.
- `baxter_examples` is now an `ament_python` package. `install(PROGRAMS ...)` copies even under `--symlink-install`, so `ros2 run baxter_examples ...` could run code you had edited but not built — that is how two I19 rehearsals silently tested stale code. Its five entry points are unchanged, including the `moveit_tiny` alias.
- The four helpers that had two or three copies across the example clients (`wait_for_future`, `cancel_active_goal`, `require_sim_move_group`, `positions_for_joints`) now live once in `baxter_examples/trajectory_helpers.py`. `wait_for_fresh_joint_state` and the joint-state callback deliberately stay per-client: `sim_tiny_trajectory`'s merged, incomplete-tolerant version is the I20 F-C hardware fix and must not be unified with the sim-only one.
- Removed `scripts/run_bridge.sh` (no documented caller — the runbook uses `python3 scripts/py_bridge.py` directly), `executor_util.py` (a module wrapping one constructor call, now inlined at both call sites with its threading invariant kept as a comment), and an orphaned image asset referenced nowhere.
- Dropped `ROS_DOMAIN_ID`/`GZ_PARTITION` isolation from the documented workflow; run one simulation at a time.
- Stopped passing `joint_limits` to the RViz node and aligned `moveit.rviz` with the ROS 1 MoveIt layout.
- Added checked-in `sim_rviz` and `sim_moveit_rviz` profiles.
- Documented `baxter_hardware_bridge` as prep-only / unsupported until I10. The I10, I11 and I12 gates have since passed; the package and its documentation are no longer prep-only, and the labels below record what the gates actually cover.

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

### Support Labels

Supersedes the `v0.1.0-sim` table for the next release. Hardware labels name the
session that earned them, per this project's rule that a claim points at a gate.

| Profile | Label |
|---|---:|
| `sim` | passed |
| `sim_moveit` | passed, manual/local smoke |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | passed — 2026-07-22, BR-01 `011412P0024` |
| supervised hardware motion | passed — supervised, 2026-07-24 (I12) and 2026-07-25 (I20), BR-01 `011412P0024`, both arms |
| MoveIt on hardware | passed **with limits** — supervised, 2026-07-24/25 (I20); left arm aborted 8 of 11 goals from RViz at default speeds; use Velocity Scaling 0.1 and single-arm groups |
| grippers | not implemented; gripper joint *states* bridge since 2026-07-24 |
| Zenoh/compatibility fallback | deferred |

These cover supervised sessions on one BR-01. At ~0.12 rad/s (I12), in-flight
lag was ~0.035 rad. I20 (2026-07-25): lag ≈ 0.4 s × commanded velocity; default
`path_tolerance_rad` 0.2 aborts near ~0.5 rad/s. The 2.0 rad/s clamp is
unreachable under that tolerance. Sustained duty, grippers, and a second robot
remain unmeasured.

### Known Limitations

- **MoveIt aborts most left-arm goals on hardware at default planning speeds.**
  Driven from RViz on 2026-07-25, the left arm aborted 8 of 11 goals on
  `left_w0`/`left_e0` at exactly the 0.2 rad path tolerance while the right
  completed 9 of 11 on the same `both_arms` plans; `move_group` logged 8 ×
  `CONTROL_FAILED`, because one controller aborting ends the whole dual-arm
  execution. Workaround: `Velocity Scaling: 0.1` and single-arm groups. Whether
  the left arm was *commanded* faster or *tracked* worse is undecided — no bag
  was recording. Open in `docs/known_issues.md`; sim is unaffected.

### Earlier Sim Hardening

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
