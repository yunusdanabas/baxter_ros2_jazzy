---
log_type: problem
title: "Sim GUI testing — observed problems"
date: 2026-07-19
status: open
session: local GUI sim smoke test (sessions 1–3)
related_docs: [docs/getting_started_sim.md, docs/simulation.md, docs/moveit_guide.md]
---

# Sim GUI Testing — Problem Log

User-reported issues from manual GUI simulation tests on 2026-07-19. **No fixes attempted in this log** — observations and evidence only.

## Environment

| Item | Value |
|---|---|
| Workspace | `/home/yunusdanabas/baxter_ros2_jazzy` |
| ROS distro | Jazzy (`/opt/ros/jazzy`) |
| Shell prompt | `(ros_env)` |
| Sim launch (sessions 1–2) | `ros2 launch baxter_gz_sim sim.launch.py headless:=false` |
| MoveIt sim launch (session 3) | `ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=false` |
| Trajectory test | `ros2 launch baxter_examples sim_tiny_trajectory.launch.py` |
| MoveIt test (session 3) | `ros2 run baxter_examples moveit_left_tiny` |
| RViz (session 3) | `rviz2` (standalone; no project RViz config) |
| Terminals | Terminal 1 = sim / MoveIt launch; Terminal 4 = client / RViz |

## Test sessions

| Session | Launch | Client / viz | ROS result | User-visible motion |
|---|---|---|---|---|
| 1 | `baxter_gz_sim` GUI | `sim_tiny_trajectory` | Partial (Ctrl+C) | None reported |
| 2 | `baxter_gz_sim` GUI | `sim_tiny_trajectory` | Clean pass | None reported |
| 3 | `baxter_moveit_config/sim_moveit` GUI | `moveit_left_tiny` + standalone `rviz2` | MoveIt plan+execute pass; RViz errors | Not re-tested in Gazebo this session; RViz model incomplete |

---

## P1 — No visible arm movement in Gazebo GUI (user report)

**Severity:** high (primary user concern)

**Symptom:** Baxter appears spawned in Gazebo, but the user did not observe any arm motion during the trajectory test. **Reproduced in both sessions** (session 2 was a clean run with no Ctrl+C).

**Contradicting log evidence (controllers report success):**

Session 1 — Terminal 1 / Terminal 4:

```text
[left_arm_controller]: Goal reached, success!
[right_arm_controller]: Goal reached, success!
/left_arm_controller/follow_joint_trajectory succeeded
(right arm client interrupted before printing succeeded)
```

Session 2 — Terminal 1 (`2026-07-19-23-25-58-*`):

```text
[left_arm_controller]: Received new action goal
[left_arm_controller]: Accepted new action goal
[left_arm_controller]: Goal reached, success!
[right_arm_controller]: Received new action goal
[right_arm_controller]: Accepted new action goal
[right_arm_controller]: Goal reached, success!
```

Session 2 — Terminal 4 (`2026-07-19-23-26-19-*`):

```text
ros2 control list_controllers   → all three controllers active
/left_arm_controller/follow_joint_trajectory: moving left_s1 0.151 -> 0.301 rad
/left_arm_controller/follow_joint_trajectory succeeded
/right_arm_controller/follow_joint_trajectory: moving right_s1 0.145 -> 0.295 rad
/right_arm_controller/follow_joint_trajectory succeeded
Tiny trajectories completed for both arms
[INFO] [sim_tiny_trajectory-1]: process has finished cleanly
```

**Notes:**

- Controllers were active before the test in both sessions.
- Session 2 rules out P4 (user interrupt) as the cause of P1 — full gate passed on ROS side, still no visible motion.
- `/joint_states` was not captured in either session; only controller/action logs are available here.
- Trajectory delta is small (~0.15 rad on `left_s1` / `right_s1` only); motion may be subtle if it is occurring — user reports seeing none at all.
- Discrepancy to investigate later: ROS-side trajectory success vs. no perceived motion in the Gazebo GUI.

**Status:** open (confirmed ×2)

---

## P2 — Shell sources missing workspace (`ros_ws`)

**Severity:** low (noise; may affect sourcing discipline)

**Symptom:** Every ROS command prints:

```text
not found: "/home/yunusdanabas/ros_ws/install/local_setup.bash"
```

**Notes:**

- Likely from shell startup (`.bashrc` or similar) referencing a workspace that does not exist.
- User still ran explicit `source install/setup.bash` for `baxter_ros2_jazzy`; sim did start despite the warning.

**Status:** open

---

## P3 — Gripper mimic constraint unsupported in Gazebo physics

**Severity:** low (documented sim limitation; not arm-controller gate)

**Symptom:** During sim startup:

```text
[Err] [Physics.cc:1808] Attempting to create a mimic constraint for joint [l_gripper_r_finger_joint]
but the chosen physics engine does not support mimic constraints, so no constraint will be created.
```

**Notes:**

- Matches known sim scope: arm joints only; grippers not controlled in default profile.
- Did not block controller activation in this run.

**Status:** open (informational)

---

## P4 — Trajectory test interrupted by user (Ctrl+C) before clean exit

**Severity:** medium (test session incomplete from client side)

**Symptom:** Terminal 4 shows Ctrl+C while the right-arm trajectory was still running:

```text
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
...
KeyboardInterrupt
...
RCLError: failed to shutdown: rcl_shutdown already called on the given context
[ERROR] [sim_tiny_trajectory-1]: process has died [pid 161369, exit code 1]
```

**Notes:**

- Left arm had already reported success before the interrupt.
- Right arm had started (`moving right_s1 0.145 -> 0.295 rad`) but the client did not print `succeeded` before SIGINT.
- Terminal 1 later shows right-arm `Goal reached, success!` — sim-side completion may have occurred after/for the in-flight goal.
- Exit code 1 here is consistent with manual interrupt, not necessarily a controller failure.

**Status:** open (session 1 only; not applicable to session 2)

---

## P7 — Spawn pose / tuck state may hide or prevent visible motion (user hypothesis)

**Severity:** medium (unverified hypothesis; not implemented)

**User observation:** After two failed visual checks, user suggests the sim should perhaps **start with the robot active and arms untucked** before running trajectories — similar to real Baxter bringup (enable + untuck), which the current default sim launch does not perform.

**Current default sim path (as documented):**

- `baxter_gz_sim/sim.launch.py` spawns Baxter from `/robot_description` at fixed height (`-z 2.0`) with no explicit enable, untuck, or named-pose initialization step.
- `sim_tiny_trajectory` commands a small delta on shoulder joint `s1` only; no pre-check of tuck/transport pose or collision self-block.

**Hypothesis (log only — no implementation):**

- Baxter may spawn in a tucked or otherwise visually static pose where the commanded joint motion is not obvious or not reflected in the GUI model.
- Adding an explicit sim bringup step (robot “active”, arms untucked / neutral pose) might make motion visible and easier to validate.

**Notes:**

- Not verified in this log; no joint-state before/after capture, no Gazebo joint inspector output, no comparison to default URDF initial positions.
- Real-hardware enable/untuck topics and services are out of scope for the default sim docs; any sim equivalent would be new design work — **deferred, not started**.

**Status:** open (hypothesis recorded)

---

## P5 — Gazebo process exit code -2 on sim shutdown

**Severity:** low (likely normal SIGINT teardown)

**Symptom:** After Ctrl+C in Terminal 1:

```text
[ERROR] [gazebo-1]: process has died [pid 159936, exit code -2, cmd '... gz sim -r empty.sdf --force-version 8'].
```

**Notes:**

- Occurred during intentional shutdown (`user interrupted with ctrl-c`).
- Not observed as a startup failure in this session.

**Status:** open (informational)

---

## P6 — Non-blocking startup warnings (recorded for completeness)

**Severity:** low

**Observed warnings during successful startup:**

| Message | Source |
|---|---|
| `Executor is not available during hardware component initialization for 'GazeboSimSystem'. Skipping node creation!` | `controller_manager` / `gz_ros_control` |
| `Desired controller update period (0.01 s) is slower than the gazebo simulation period (0.001 s).` | `gz_ros_control` |
| `Component 'GazeboSimSystem' does not have read or write statistics initialized, skipping registration.` | `controller_manager` |

**Notes:** Sim reached active controllers and executed action goals despite these warnings.

**Status:** open (informational)

---

## Session 3 — MoveIt sim + standalone RViz (2026-07-19 ~23:27)

### Launch and client evidence

Terminal 1 — `ros2 launch baxter_moveit_config sim_moveit.launch.py headless:=false`  
Log dir: `2026-07-19-23-27-44-*`

- Gazebo spawned Baxter; all three arm controllers activated.
- `move_group` started after 8 s timer; OMPL loaded successfully:

```text
Successfully loaded planner 'OMPL'
MoveGroup context using pipeline ompl
You can start planning now!
```

- MoveIt plan + execute from RViz/MoveIt request succeeded on ROS side:

```text
[left_arm_controller]: Goal reached, success!
Completed trajectory execution with status SUCCEEDED ...
Solution was found and executed.
```

Terminal 4 — `ros2 run baxter_examples moveit_left_tiny`

```text
MoveIt left_arm: moving left_s1 0.151 -> 0.201 rad
MoveIt left-arm plan+execute passed
```

Terminal 4 — `rviz2` (standalone, after MoveIt test)

- RViz started with OpenGL 4.6; no project `.rviz` config loaded.
- Screenshots saved under workspace assets (see P9, P10).

---

## P8 — Incomplete `/joint_states` (head + gripper joints missing)

**Severity:** medium

**Symptom:** `move_group` repeats warning every ~1 s for the entire session:

```text
The complete state of the robot is not yet known. Missing head_pan, l_gripper_l_finger_joint, r_gripper_l_finger_joint
```

**Notes:**

- Default sim `gz_ros2_control` exposes **14 arm joints only** (documented in `docs/moveit_guide.md` as known non-blocker for arm planning).
- Head and gripper joints exist in URDF/MoveIt model but are **not published** on `/joint_states` in the current sim profile.
- Likely contributes to RViz TF gaps (P9) and incomplete RobotModel display.
- Arm-only MoveIt planning still reports success despite incomplete full-robot state.

**Status:** open (expected sim limitation; impacts visualization)

---

## P9 — RViz RobotModel TF errors (head + gripper finger links)

**Severity:** medium (visualization)

**Symptom:** In standalone `rviz2`, **RobotModel → Status: Error**. Fixed frame: `base`. `/joint_states` topic received (~14.2 Hz).

**Links with transform errors** (`No transform from [link] to [base]`):

| Area | Links |
|---|---|
| Head | `display`, `dummyhead1`, `head`, `head_camera` |
| Left gripper fingers | `l_gripper_l_finger`, `l_gripper_l_finger_tip`, `l_gripper_r_finger`, `l_gripper_r_finger_tip` |
| Right gripper fingers | `r_gripper_l_finger`, `r_gripper_l_finger_tip`, `r_gripper_r_finger`, `r_gripper_r_finger_tip` |

**Links reporting Transform OK (sample):** `base`, arm mount/hand links, `left_upper_shoulder`, `left_wrist`, `pedestal`, `right_arm_*`, `right_gripper`, `right_gripper_base`, `right_hand`, collision head links.

**Screenshot artifacts:**

- `assets/image-ee35b206-ceb2-4917-8b9b-88cfc156115d.png`
- `assets/image-23f1169a-6e54-4ebb-8905-bb6357fe56c8.png`

**Notes:**

- Consistent with P8: missing joint states for `head_pan` and gripper finger joints breaks TF chain for dependent links.
- Not verified whether arm links alone would animate correctly in RViz if a trajectory were replayed.
- No fix attempted.

**Status:** open

---

## P10 — RViz MoveIt plugin shows “NO PLANNING LIBRARY LOADED”

**Severity:** medium (visualization / UX)

**Symptom:** In standalone `rviz2`, **MotionPlanning → Context** tab displays:

```text
NO PLANNING LIBRARY LOADED
```

Planning-library and planner dropdowns are empty; Planner Parameters panel blank.

**Contradicting evidence:** Terminal 1 `move_group` logs show OMPL loaded and planning succeeded:

```text
Successfully loaded planner 'OMPL'
Calling Planner 'OMPL'
Solution was found and executed.
```

**Notes:**

- `sim_moveit.launch.py` starts Gazebo + `move_group` only; it does **not** launch RViz and this repo has **no checked-in `.rviz` config** under `baxter_moveit_config`.
- User ran bare `rviz2`, so MoveIt RViz plugin was likely not configured with `move_group` namespace / planning pipeline parameters.
- Planning via `moveit_left_tiny` CLI worked; RViz plugin state may be a **configuration gap**, not a `move_group` failure.
- Screenshot: `assets/image-4369d442-d444-485a-a1ff-21a8abd56c66.png`

**Status:** open (log only; no RViz launch file added)

---

## P11 — MoveIt + RViz session: ROS success vs visual validation gap

**Severity:** medium (ties P1, P8–P10)

**Observation:** Session 3 adds a third case where ROS/MoveIt reports successful left-arm execution while visualization tooling shows problems:

| Layer | Result |
|---|---|
| `moveit_left_tiny` | `MoveIt left-arm plan+execute passed` |
| `move_group` | `Solution was found and executed` |
| Gazebo GUI | Not explicitly re-checked for visible motion this session |
| RViz RobotModel | Status Error; missing head/gripper TF |
| RViz MoveIt plugin | No planning library loaded |

**Notes:**

- Reinforces P1 pattern: controller/MoveIt success logs do not guarantee usable GUI feedback.
- Session 3 does not disprove P1; user focus shifted to MoveIt/RViz diagnostics.
- P7 hypothesis (active + untucked initial pose) still unverified.

**Status:** open

---

## P12 — MoveIt / move_group informational warnings (session 3)

**Severity:** low

**Observed (non-fatal in this run):**

| Message | Source |
|---|---|
| `No 3D sensor plugin(s) defined for octomap updates` | `occupancy_map_monitor` |
| Several links have visual but no collision geometry | `robot_model` |
| `It looks like the planning volume was not specified. Using default values.` | `validate_workspace_bounds` |
| `Execution of motions should always start at the robot's current state. Ignoring the state supplied as start state` | MoveGroup capability |

**Notes:** Documented as known non-blockers in `docs/moveit_guide.md` for arm-only sim scope.

**Status:** open (informational)

---

## Summary

| ID | Problem | Status |
|---|---|---|
| P1 | No visible arm movement in Gazebo GUI despite controller success logs | open (confirmed ×2; session 3 not re-checked in Gazebo) |
| P2 | Missing `ros_ws` auto-source warning on every command | open |
| P3 | Gripper mimic constraint error at startup | open (informational) |
| P4 | Trajectory client interrupted with Ctrl+C; messy shutdown / exit code 1 | open (session 1 only) |
| P5 | Gazebo exit code -2 on intentional sim stop | open (informational) |
| P6 | Startup warnings from gz_ros2_control / controller_manager | open (informational) |
| P7 | User hypothesis: need active + untucked initial pose before trajectories | open (hypothesis) |
| P8 | `/joint_states` missing `head_pan` and gripper finger joints | open |
| P9 | RViz RobotModel TF errors on head + gripper finger links | open |
| P10 | RViz MoveIt plugin: NO PLANNING LIBRARY LOADED (standalone `rviz2`) | resolved 2026-07-22, see final section |
| P11 | ROS/MoveIt success vs broken/incomplete RViz visualization | open |
| P12 | MoveIt informational warnings (octomap, collision, workspace) | open (informational) |

## Artifacts

**Session 1**

- Sim: `/home/yunusdanabas/.ros/log/2026-07-19-23-23-25-*`
- Trajectory: `/home/yunusdanabas/.ros/log/2026-07-19-23-24-27-*`

**Session 2**

- Sim: `/home/yunusdanabas/.ros/log/2026-07-19-23-25-58-*`
- Trajectory: `/home/yunusdanabas/.ros/log/2026-07-19-23-26-19-*`

**Session 3**

- MoveIt sim: `/home/yunusdanabas/.ros/log/2026-07-19-23-27-44-*`
- RViz screenshots: `assets/image-ee35b206-ceb2-4917-8b9b-88cfc156115d.png`, `assets/image-23f1169a-6e54-4ebb-8905-bb6357fe56c8.png`, `assets/image-4369d442-d444-485a-a1ff-21a8abd56c66.png`

---

## Review findings - 2026-07-20

This section records a read-only investigation of P1-P12 and related issues. It does not change the original observations above, and no fixes were implemented as part of this review.

### Review scope and evidence limits

Reviewed:

- `AGENTS.md`, `MASTER_PLAN.md`, `RESEARCH_FINDINGS.md`, and the relevant archived planning findings.
- `docs/getting_started_sim.md`, `docs/simulation.md`, `docs/moveit_guide.md`, compatibility/support/release documentation, and the README.
- All launch, URDF/Xacro, controller, SRDF, OMPL, and example files under `baxter_gz_sim`, `baxter_moveit_config`, and `baxter_examples`.
- I04-I09 implementation logs.
- ROS launch/node logs for all three 2026-07-19 sessions.
- Gazebo server logs under `~/.gz/sim/log/` for all three sessions.
- The still-running session-3 ROS/Gazebo graph and state, using read-only queries.
- Installed Jazzy `joint_trajectory_controller`, `gz_ros2_control`, `robot_state_publisher`, and `moveit_configs_utils` behavior and documentation.

Evidence limitations:

- Sessions 1 and 2 did not record `/joint_states`, controller state, Gazebo link pose, or video before/during/after the goals. Their physical final joint positions cannot be reconstructed conclusively.
- The three PNG files cited in P9/P10 do not exist under the workspace, home directory, or temporary directory. Screenshot-specific review is therefore unavailable. The RViz conclusions below use the exact RViz log and the problem log's recorded link list instead.
- Session 3 remained running during this review. Its live state is useful evidence, but it is not a substitute for a controlled replay of sessions 1-2.

### Decisive additional evidence

The still-running session-3 process retained the result of the MoveIt goal:

```text
moveit_left_tiny logged start/goal: left_s1 0.150786 -> 0.200786 rad
live /joint_states left_s1:       0.193850 rad
live controller reference:        0.193836 rad
live controller position error:  -0.000014 rad
live right_s1:                     0.145292 rad
```

The actual left-arm change was approximately `+0.0431 rad`. This is within the MoveIt goal constraint of `0.200786 +/- 0.01 rad` and proves that session 3 changed the Gazebo-backed joint state. It rules out a universal controller/plugin no-op, but it does not prove what the Gazebo GUI displayed in sessions 1-2.

The same live Gazebo model was stable over repeated queries:

```text
model pose XYZ: -0.00556 -0.00560 0.92413 m
model pose RPY:  0.00000  0.00000 0.01341 rad
```

The model is not fixed to `world`, but it had settled upright at the pedestal's expected floor height. This evidence is important when interpreting the DART mesh debug messages discussed under P6 and P13.

At review time, Gazebo reported a real-time factor near `0.219`. In session 2, each nominal two-sim-second direct trajectory took about 6.2 wall seconds, corresponding to a real-time factor near `0.32`. GUI users therefore observe simulation-time trajectories more slowly than their nominal durations.

### Overall diagnosis of the primary mystery

The evidence supports the following conclusion:

> P1 is a confirmed user-facing visual-validation failure, but the claim that the simulated arm joints did not physically move in sessions 1-2 is not established. The same control path moved joints numerically in I06 and session 3. The sessions 1-2 smoke command did not measure final state, while the GUI motion was small, sequential, viewed from a distant default camera, and not captured as video or before/after images.

Ranked explanations:

| Rank | Explanation | Confidence | Notes |
|---:|---|---:|---|
| 1 | Test-observability gap: no numeric post-check and weak visual stimulus | high | Directly demonstrated by the example and session artifacts. |
| 2 | Motion occurred but was not perceived from the default view | medium-high | The direct delta is only `0.15 rad` (`8.6 deg`) on one shoulder joint at a time; MoveIt used `0.05 rad` (`2.9 deg`). |
| 3 | Nondeterministic startup pose/base settling reduced visual clarity | medium | The model drops from `z=2.0`, is not fixed to world, and has no named-pose initialization. |
| 4 | Controller reported success despite physical position error | possible but unproven | Default per-joint goal position tolerance is disabled; sessions 1-2 lack final-state data. |
| 5 | GUI attached to a stale or different server | low | Session servers shut down before the next session, and Gazebo published state updates for the correct `empty` world. |
| 6 | Missing hardware-style enable/untuck operation | rejected as root cause | Active ros2_control controllers are the sim actuation boundary; no simulated Baxter motor-enable state exists. |

### P1 review - No visible arm motion in Gazebo

**Classification:** confirmed visual acceptance failure; physical no-motion remains unproven for sessions 1-2.

**Severity / priority:** high / immediate verification priority.

**Root-cause analysis:**

- `sim_tiny_trajectory.py` reads one initial `/joint_states` message, sends goals, and accepts the action result without rereading actual state (`src/baxter_examples/baxter_examples/sim_tiny_trajectory.py:121-136`).
- The controller YAML defines no goal-position tolerances. Jazzy defaults are `constraints.<joint>.goal: 0.0`, `constraints.goal_time: 0.0`, and `constraints.stopped_velocity_tolerance: 0.01`. A zero position tolerance is not enforced, and zero goal time can wait indefinitely. `Goal reached, success!` is therefore weaker evidence than an actual-position measurement.
- The I06 gate did measure `left_s1 0.150786 -> 0.300792` and `right_s1 0.145276 -> 0.295283` (`logs/I06_tiny_sim_trajectory.log.md:85-95`). That confirms this plugin/controller path can change Gazebo-backed state.
- Session 3 independently retained a physical left-arm change with negligible controller error, as recorded above.
- The direct example moves only `s1` by `0.15 rad`, sequentially, over two simulated seconds (`sim_tiny_trajectory.py:33-35`, `:126-135`). The default Gazebo camera is around 8 m from the robot (`~/.gz/sim/8/gui.config:18-29`), and the example does not return to the start pose or provide a visual marker.
- Session 2 had no startup race: the goals began roughly 16 seconds after both controllers were active. The model had ample time to settle before motion.

**What to verify next:**

- Record fresh `/joint_states` and both `/left_arm_controller/controller_state` and `/right_arm_controller/controller_state` before, during, and after each goal.
- Record the Gazebo model root and downstream shoulder-link pose over the same interval.
- Capture a screen recording with the camera focused on one arm before sending the goal.
- Require target, actual, and final absolute error in the client output.
- Run a safe, visibly larger, reversible absolute movement and return to the measured start pose instead of accumulating offsets.

**Recommended fix direction:**

- Make numeric post-state validation the primary pass criterion; visual observation should be a separate GUI criterion.
- Configure finite per-joint goal tolerances and a finite goal-time tolerance.
- Improve the manual GUI smoke with a closer camera, an obvious reversible movement, and explicit expected wall-time guidance.
- Do not add Baxter hardware enable semantics to solve this sim issue.

**Disposition:** keep open until a synchronized numeric and GUI replay passes.

### P2 review - Stale `ros_ws` source

**Classification:** confirmed environment/build-prefix defect, not merely harmless shell noise.

**Severity / priority:** low immediate runtime impact / medium reliability priority.

**Root-cause analysis:**

- The current generated `install/setup.bash` embeds `/home/yunusdanabas/ros_ws/install` as a chained underlay at lines 25-26. That directory no longer exists, producing the exact `local_setup.bash` warning whenever this workspace is sourced.
- The same stale prefix appears in `install/setup.sh`, `setup.zsh`, and `setup.ps1`.
- `~/.bashrc` also sources ROS Jazzy three times and references the missing `~/ros_ws/install/setup.bash` (`~/.bashrc:149-159`).
- Explicitly sourcing this workspace after the warning allowed the sessions to run, so P2 did not cause P1. It can still contaminate future builds, resolve packages from unintended underlays, and make generated installs non-reproducible.

**What to verify next:** start a clean shell with only `/opt/ros/jazzy`, rebuild the workspace, and confirm no generated setup file references `ros_ws`.

**Recommended fix direction:** remove the stale/duplicate shell startup sources and regenerate `build/`, `install/`, and `log/` from a clean environment. Do not hand-edit generated setup files.

**Disposition:** confirmed; fix outside this review.

### P3 review - Unsupported gripper mimic constraint

**Classification:** expected current-scope limitation; real gripper-physics fidelity defect.

**Severity / priority:** low for arm-only smoke / medium before gripper support.

**Root-cause analysis:**

- Both grippers define an actuated left finger and a right finger with URDF multiplier `-1.0` (`rethink_electric_gripper.xacro:63-83`).
- DART reports that it cannot create the physics mimic constraint. Neither gripper is present in the current ros2_control configuration, so this cannot explain shoulder-controller behavior.
- `robot_state_publisher` can still derive a mimic TF from the source finger state. Gazebo physics can disagree with that derived pose if the physical child finger is unconstrained, creating a Gazebo/RViz/MoveIt consistency risk.

**What to verify next:** compare the Gazebo positions of both physical fingers against the URDF-derived source/mimic TF relationship.

**Recommended fix direction:** leave gripper motion unsupported for the current arm profile. Before adding it, configure a supported mimic/control strategy and publish truthful source/child state rather than suppressing the warning.

**Disposition:** expected limitation for current scope; track for gripper work.

### P4 review - Interrupted trajectory and shutdown traceback

**Classification:** expected user interruption plus a client cleanup/cancellation defect.

**Severity / priority:** not causal for P1 / medium test-robustness priority.

**Root-cause analysis:**

- The server logged right-arm success at `1784492685.5035`; launch logged Ctrl+C at `1784492685.5223`, about 19 ms later. The physical action had effectively completed, but the client had not processed and printed the result.
- `sim_tiny_trajectory.py` has unbounded `spin_until_future_complete` calls for goal response and result (`:100-108`).
- It does not keep/cancel the active goal on interruption and calls `rclpy.shutdown()` unconditionally (`:117-139`). The rclpy signal handler may already have shut down the context, explaining `rcl_shutdown already called`.
- `wait_for_joint_states` uses ROS time for its timeout (`:55-63`), so the timeout can stop advancing if the simulator clock is paused or absent.

**What to verify next:** interrupt once during an active goal and confirm cancellation/hold, bounded process exit, and no traceback or orphaned action.

**Recommended fix direction:** use monotonic wall time for availability timeouts, bound all action waits, cancel the active goal on interruption, and use idempotent shutdown handling.

**Disposition:** session-1 test result is superseded by clean session 2; client robustness remains open.

### P5 review - Gazebo exit code `-2`

**Classification:** expected SIGINT process status during intentional shutdown.

**Severity / priority:** informational / no product fix required by current evidence.

**Root-cause analysis:** Python/ROS launch reports a child terminated by signal 2 as exit code `-2`. Session 1's other nodes exited cleanly. In session 2, repeated Ctrl+C signals also terminated `robot_state_publisher` with `-2`.

**What to verify next:** send one Ctrl+C, wait for teardown, and check that no Gazebo, bridge, controller, MoveIt, or RViz process remains.

**Recommended fix direction:** document single-interrupt teardown. Treat a reproducible hang, leftover process, or `move_group` segmentation fault as a separate defect rather than treating `-2` itself as one.

**Disposition:** expected behavior; close as informational after teardown is documented.

### P6 review - Startup warnings

**Classification:** the three listed messages are expected diagnostics; additional omitted messages need separate treatment.

**Severity / priority:** listed warnings low / related command-limit issue medium.

| Message | Review classification | Reason |
|---|---|---|
| Executor unavailable during hardware initialization | expected | Successful hardware initialization immediately follows. |
| 100 Hz controller period slower than 1 kHz physics period | expected | Controllers need not run at every physics step; this is not a GUI failure. |
| Read/write statistics not initialized | expected instrumentation gap | Hardware and controllers still initialize and execute. |
| `Enforcing command limits is disabled` | configuration risk | Direct controller clients do not receive controller-manager clamping. See P16. |
| DART mesh construction / geometry debug messages | inconclusive diagnostic | Upstream `gazebosim/gz-physics#985` documents successful later mesh attachment despite these messages. The live model settling exactly at pedestal floor height is evidence against declaring collision loss from text alone. |

**What to verify next:** inspect actual contacts/collision behavior and controller command-limit parameters rather than classifying by log wording alone.

**Recommended fix direction:** retain the 100 Hz/1 kHz rates unless measurements require tuning. Handle command limits under P16. Do not switch physics engines solely because of the misleading DART debug text.

**Disposition:** listed warnings are non-blocking; split actionable risks into their own findings.

### P7 review - Active/untucked startup hypothesis

**Classification:** hardware-style enable is not applicable; deterministic initial pose is a valid UX/configuration gap.

**Severity / priority:** medium / after truthful motion measurement and base mounting.

**Root-cause analysis:**

- The launch activates both arm controllers. There is no simulated Baxter `AssemblyState`, brake, e-stop, or motor-enable gate. Controller lifecycle `active` is the effective sim enable.
- The URDF and ros2_control state interfaces define no initial arm positions (`baxter_gz_control.urdf.xacro:18-44`).
- The SRDF neutral states exist but are not applied automatically (`baxter.srdf:24-40`).
- Observed starts near `s1=+0.15` are not the named neutral value `-0.55` and are not evidence of an intentional tucked pose. They are consistent with zero-ish startup plus dynamics/settling.
- A neutral pose would improve visual clarity, but applying a larger startup trajectory before resolving world mounting and collision-state fidelity could create a new failure mode.

**What to verify next:** capture all arm positions immediately at spawn, after controller activation, and after base settling; then test the existing named neutral state as an explicit user action.

**Recommended fix direction:** provide deterministic sim initial positions or an explicit, collision-checked neutral-pose action after the model is stable. Do not imitate real-hardware enable topics.

**Disposition:** reject enable as P1 root cause; retain deterministic neutral pose as follow-up.

### P8 review - Incomplete `/joint_states`

**Classification:** expected against the original arm-only gate, but a confirmed full-model state and visualization gap.

**Severity / priority:** medium / high for usable MoveIt/RViz GUI.

**Root-cause analysis:**

- The sim overlay registers exactly 14 arm joints with ros2_control (`baxter_gz_control.urdf.xacro:26-44`).
- `joint_state_broadcaster` publishes all available registered interfaces; it cannot publish head or gripper joints that the hardware interface does not expose.
- The three missing independent joints are `head_pan`, `l_gripper_l_finger_joint`, and `r_gripper_l_finger_joint`.
- The opposite gripper fingers are URDF mimic joints. When mimic semantics are valid, they do not require independent entries in `/joint_states`; the two source finger values are sufficient. The target complete independent-state count is 17, not 19.
- Arm-only planning succeeded because the arm chains are complete and stop at `left_gripper` / `right_gripper`. Full-robot collision state remains incomplete.

**What to verify next:** require all 17 independent joints in `/joint_states` continuously and confirm that MoveIt's missing-state warning disappears for at least 10 seconds.

**Recommended fix direction:** expose measured state-only interfaces for the head and two source fingers, without adding gripper command support. Reconcile physical mimic behavior before claiming truthful gripper collision state.

**Disposition:** confirmed scoped limitation; promote to high priority for RViz completeness.

### P9 review - RViz RobotModel TF errors

**Classification:** confirmed downstream symptom of P8, not a separate arm-TF failure.

**Severity / priority:** medium / resolve through P8.

**Root-cause analysis:**

- Head chain: `base -> torso -> head_pan -> head`. Without `head_pan`, `head`, `dummyhead1`, `head_camera`, `screen`, and `display` cannot connect to `base`.
- Gripper chain: each gripper body/tip is fixed to the arm, while each finger branch begins at the missing source or derived mimic joint. This explains why `left_gripper`, `right_gripper`, and arm links were valid while finger links and tips failed.
- The collision-head proxy links remained valid because they are fixed directly to `base`, bypassing `head_pan`.
- All 14 arm joints were present, so P9 does not explain missing arm motion or arm TF.

**What to verify next:** after P8 is addressed, check `base` transforms to `head`, `screen`, and all four finger links/tips, then require RobotModel status OK.

**Recommended fix direction:** fix the missing joint-state source. Do not publish static transforms for movable head/finger joints just to silence RViz.

**Disposition:** confirmed consequence of P8.

### P10 review - RViz says `NO PLANNING LIBRARY LOADED`

**Classification:** expected failure for bare `rviz2`; confirmed project RViz launch/configuration gap. `/move_group` and OMPL were healthy.

**Severity / priority:** medium / high GUI usability priority.

**Root-cause analysis:**

- The RViz log gives the immediate cause:

```text
Could not find parameter robot_description_semantic and did not receive
robot_description_semantic ... within 10 seconds
Unable to parse SRDF
Robot model not loaded
```

- ROS 2 parameters are node-local. `move_group.launch.py` gives the complete MoveIt config only to `/move_group` (`:19-39`); a separately launched RViz process does not inherit it.
- The custom launch uses the builder default `publish_robot_description_semantic: false`. A live query confirmed that `/move_group` had this parameter set to false and no `/robot_description_semantic` topic existed.
- The live `/rviz` node had `use_sim_time: false`, no semantic value, and an empty `default_planning_pipeline`.
- Standard MoveIt launch helpers explicitly enable semantic-description publication for `move_group` and pass planning pipeline, kinematics, and joint-limit parameters to RViz (`/opt/ros/jazzy/.../moveit_configs_utils/launches.py:47-73`, `:219-250`).
- `moveit_left_tiny` worked because it is an action client; it delegates group/pipeline/planner identifiers to the already configured `/move_group` and does not build its own RobotModel.

**What to verify next:** start RViz through a project launch, verify SRDF parsing, query planner interfaces, and require OMPL plus `RRTConnectkConfigDefault` in the MotionPlanning display.

**Recommended fix direction:** add a supported RViz launch and checked-in `.rviz` configuration, use sim time, provide RViz-local planning parameters, and publish or directly pass the semantic description. Do not document bare `rviz2` as the supported MoveIt path.

**Disposition:** confirmed UX/configuration gap; not a planner failure.

### P11 review - ROS success versus visual validation

**Classification:** inconclusive test design, not a third confirmed no-motion event.

**Severity / priority:** high validation impact / immediate correction to interpretation.

**Root-cause analysis:**

- `moveit_left_tiny` finished at timestamp `1784492894.453` (`python3_166266_1784492890697.log`).
- RViz started at `1784492904.957`, about 10.5 seconds later (`rviz2_166621_1784492904445.log`).
- The MotionPlanning display began initialization near `1784493000`, roughly 95 seconds after RViz startup and more than 105 seconds after motion completed.
- RViz could not have displayed the live trajectory. At most, it could show the final pose, whose requested change was only `0.05 rad`.
- The live session-3 state retained a valid left-arm change with negligible tracking error, proving numerical execution for that session.

**What to verify next:** start configured RViz before motion, require a healthy arm RobotModel, then capture the planned path, live robot state, Gazebo GUI, and final state in one synchronized run.

**Recommended fix direction:** define separate acceptance results for action/MoveIt success, measured physical state, Gazebo rendering, plain RViz RobotModel, and the MoveIt MotionPlanning plugin.

**Disposition:** replace "third case reinforcing P1" with "visual validation not performed; physical state changed."

### P12 review - MoveIt warnings

**Classification:** mixed; not all warnings have the same scope or severity.

**Severity / priority:** low-medium in the empty-world arm smoke / high before obstacle-aware or hardware claims.

| Message | Review classification | Impact |
|---|---|---|
| No 3D sensor plugin / octomap updates | expected scoped limitation | MoveIt does not automatically know Gazebo obstacles. Self-collision and explicit planning-scene objects still work. |
| Visual links without collision geometry | localized model gap | `display` and hand sensor visuals do not contribute their exact geometry to collision checking. Parent/proxy collisions cover some, but not necessarily all, volume. |
| Planning volume unspecified | low-impact request default | The tested request is joint constrained; default workspace use is not the execution failure. |
| Supplied start state ignored | expected for combined plan-and-execute | MoveGroup intentionally uses current monitored state before execution. The real concern is whether that monitored full state is complete and fresh. |

Additional conclusions:

- The octomap message is logged as an error, but it is an accepted empty-world scope decision. It becomes blocking for claims about unmodeled obstacles.
- The guide documents missing joint state and octomap scope, but not every P12 message. The statement that all P12 warnings are documented non-blockers is inaccurate.
- The current incomplete head/finger state means full-robot collision placement is not proven even though the seven controlled arm joints are current.

**What to verify next:** test state validity with head/fingers at bounds, verify collision coverage for visual-only links, and add a known obstacle to the explicit or sensed planning scene before obstacle-aware claims.

**Recommended fix direction:** keep empty-world scope explicit, complete independent joint state, validate collision geometry, and add sensing/planning-scene synchronization only when obstacle-aware simulation is required.

**Disposition:** split into expected scoped warnings and model/planning limitations; do not treat all as universally non-blocking.

---

## Related issues found during review

### P13 - Gazebo base mounting and MoveIt world-frame mismatch

**Classification:** confirmed simulation-modeling gap; possible P1 contributor, not proven root cause.

**Severity / priority:** medium-high / address before broader GUI or environment-planning claims.

Evidence:

- Gazebo spawns the URDF root at `z=2.0` (`sim.launch.py:54-58`).
- The pedestal is fixed to `torso`, but the imported `world -> base` joint is commented out (`pedestal.xacro:27-38`).
- The model is dynamic and falls until the pedestal reaches the floor. The live model settled at `z=0.92413` with a small yaw/XY shift.
- The SRDF `world_joint` is semantic only (`baxter.srdf:45`). It neither fixes Gazebo physics nor publishes a TF.
- No static transform publisher exists in the combined launch, although the archived design explicitly required a fixed `world -> base` transform (`plan/logs/S06_moveit_ros2_control.log.md:318-324`).

Risks:

- Startup pose depends on a drop and contact settling rather than a deterministic pedestal mount.
- MoveIt assumes fixed identity `world -> base`, while Gazebo's actual base is offset and can move slightly.
- Future Gazebo obstacles and MoveIt planning-scene objects will not share a consistent world frame.

**What to verify next:** record base pose from spawn through settling and compare a known Gazebo object pose against the same object in MoveIt's planning frame.

**Recommended fix direction:** use a sim-only physical world/base mount and a matching TF while preserving articulated arm joints. Replace arbitrary spawn height with the validated mount transform. Do not rely on the SRDF virtual joint to affect physics.

### P14 - Action success is not a sufficient motion gate

**Classification:** confirmed acceptance-test defect.

**Severity / priority:** high / immediate.

Evidence:

- No per-joint goal-position constraints are configured in `ros2_controllers.yaml`.
- Jazzy defaults leave goal-position/path tolerances disabled and goal time unbounded.
- Both examples trust the action/MoveGroup result and do not require a fresh final actual position.
- I06's one-off external numeric measurement was stronger than the reusable example itself.

**What to verify next:** deliberately block or perturb one joint and confirm the smoke fails on final position error rather than accepting a success status alone.

**Recommended fix direction:** add finite controller tolerances and make every motion smoke compare a fresh measured final state against its target.

### P15 - Direct trajectory example is cumulative, stale, and weakly bounded

**Classification:** confirmed test-repeatability and interruption-handling defect.

**Severity / priority:** medium / fix with P14.

Evidence:

- Every run adds `+0.15 rad` to the current `s1`; repeated runs in one session eventually approach/exceed the upper joint limit.
- One initial `JointState` snapshot supplies both arm starts. The right-arm start is already several wall seconds old after the left goal completes.
- Goal-response and result waits are unbounded.
- ROS-time availability timeout can stall when `/clock` is absent or paused.
- No cancel-on-interrupt or final-state check exists.

**What to verify next:** run the smoke repeatedly, pause the simulator, interrupt during motion, and delay/disable an action server; every case should terminate predictably without exceeding limits.

**Recommended fix direction:** use a fresh state per arm, choose bounded absolute/reversible targets, clamp/validate against URDF limits, use monotonic timeouts, cancel cleanly, and report final error.

### P16 - Controller-manager command limits are disabled

**Classification:** confirmed configuration risk.

**Severity / priority:** medium for direct sim clients / high before reusing the pattern elsewhere.

Evidence: every Gazebo server log states `Enforcing command limits is disabled. Command limits from URDF will be ignored.` The current ros2_control command-interface declarations also omit explicit min/max parameters.

**What to verify next:** inspect `/controller_manager` parameters and send a deliberately out-of-range test only in an isolated simulation; require rejection or clamping at the intended boundary.

**Recommended fix direction:** enable controller-manager command-limit enforcement and retain client-side target validation. MoveIt limits alone do not protect arbitrary direct FJT clients.

### P17 - `move_group` startup uses an arbitrary timer

**Classification:** latent launch race.

**Severity / priority:** medium.

Evidence:

- `sim_moveit.launch.py:29` starts `move_group` after a fixed 8-second wall timer.
- In session 3, `move_group` started at `1784492874.300`; the right controller activated around `1784492875.762`.
- The tested left goal was sent much later, so this race did not fail session 3. A slower host or immediate right-arm request can expose it.
- The archived design required active-controller verification before executable MoveIt use (`plan/logs/S06_moveit_ros2_control.log.md:243-257`).

**What to verify next:** repeat startup under low real-time factor and CPU load, then send left/right requests immediately after MoveIt reports ready.

**Recommended fix direction:** gate executable readiness on controller/action availability rather than elapsed time, or clearly separate early planning-only readiness from execution readiness.

### P18 - Evidence artifacts and process isolation are incomplete

**Classification:** confirmed reproducibility/operational gap.

**Severity / priority:** medium.

Evidence:

- The three cited screenshots are absent, leaving broken artifact references.
- Session 3 Gazebo, `ros_gz_bridge`, `robot_state_publisher`, `move_group`, and RViz processes were still running during the 2026-07-20 review.
- All sessions used default ROS/Gazebo discovery domains, which can collide with unrelated processes on the host.

**What to verify next:** begin from a process-empty graph, use isolated `ROS_DOMAIN_ID` and `GZ_PARTITION`, store timestamped numeric/video artifacts, and confirm teardown leaves no processes.

**Recommended fix direction:** add a reproducible manual test checklist and retain its artifacts in an agreed local or tracked location. Do not cite files that were not retained.

### P19 - Support labels exceed GUI evidence scope

**Classification:** documentation/support-claim qualification gap.

**Severity / priority:** medium release clarity.

Evidence:

- README, support, compatibility, and release notes label `sim` as passed based on spawn, controllers, arm states, and action success.
- Those original gates did pass at the ROS/action level, but no GUI-motion acceptance gate existed.
- `sim_moveit` evidence covers a left-arm tiny execution; right-arm MoveIt execution, configured RViz, complete full-model state, and obstacle synchronization remain unverified.
- Existing "known non-blocker" wording is accurate only for the arm-only, empty-world smoke profile.

**What to verify next:** map each support label to explicit action-level, numeric-motion, GUI, RViz, and environment-collision evidence.

**Recommended fix direction:** retain passed headless/action claims where earned, but explicitly mark GUI visual acceptance and full MoveIt visualization as open until their gates pass.

### P20 - Allowed-collision matrix provenance needs review

**Classification:** validation gap, not a demonstrated collision bug.

**Severity / priority:** medium before broader planning claims.

Evidence: I07 reports that the first plan failed on 19 contacts and those exact pairs were added to the SRDF until the test passed (`logs/I07_moveit2_sim_profile.log.md:51-61`). The current 52 disabled pairs look largely adjacent/model-related, but no sampled self-collision report or per-pair rationale is retained.

**What to verify next:** regenerate/sample the matrix with the final model, inspect all disabled non-adjacent pairs, and test arm-arm, arm-pedestal, head, and gripper collision cases.

**Recommended fix direction:** retain only justified adjacent/never-colliding pairs and document the matrix generation evidence. Do not blanket-disable contacts to make a smoke plan pass.

---

## Prioritized verification matrix

No item below was executed as a fix during this review. This is the recommended order for the next controlled test.

### Preflight

1. Stop the still-running session-3 process group from its original terminal and confirm no Gazebo, controller, MoveIt, bridge, RSP, or RViz process remains.
2. Remove stale shell underlay sourcing and rebuild from a shell containing only `/opt/ros/jazzy` plus the newly built workspace.
3. Assign a fresh `ROS_DOMAIN_ID` and `GZ_PARTITION` for the run.
4. Start one GUI Gazebo server and confirm exactly one `baxter` entity and one controller manager.
5. Record the base pose from spawn until stable; abort the motion test if the root continues moving or tips.

### Direct trajectory gate

| Layer | Required evidence | Pass criterion |
|---|---|---|
| Controller lifecycle | `ros2 control list_controllers` | broadcaster and both arm controllers active |
| Independent state | one fresh `/joint_states` stream | all 17 independent joints present; timestamps advance |
| Command | controller reference | intended bounded target is visible |
| Physical feedback | controller feedback and `/joint_states` | measured target joint changes and final absolute error is at most `0.02 rad` |
| Gazebo model | root and downstream link pose | root remains stable; target link pose changes consistently |
| Gazebo GUI | screen recording | focused arm visibly moves and returns to start |
| Cancellation | interrupt during a separate goal | goal cancels/holds and client exits without traceback |

### MoveIt/RViz gate

| Layer | Required evidence | Pass criterion |
|---|---|---|
| `move_group` | startup log and planner query | OMPL and RRTConnect available |
| Full robot state | current-state monitor | no missing `head_pan` or source-finger warning |
| RViz model | RobotModel status | all head, arm, hand, and finger links transform to fixed frame |
| MotionPlanning plugin | configured project launch | SRDF loads; planning library and planner dropdowns populated |
| Planning | left and right arm request | plan succeeds for each advertised arm |
| Execution | synchronized numeric/GUI capture | actual state, Gazebo, and RViz all show the same motion |
| Environment scope | known explicit obstacle | intersecting path is rejected before obstacle-aware support is claimed |

### Teardown gate

1. Send one Ctrl+C to the owning launch process.
2. Wait for orderly shutdown without repeated signals.
3. Confirm no related process remains.
4. Treat Gazebo `-2` as expected SIGINT status; record hangs, leftovers, or `move_group` crashes separately.

---

## Recommended fix order (direction only)

1. Make motion tests truthful: finite tolerances, bounded targets/timeouts, cancellation, and fresh final-state checks.
2. Complete full-model state and provide a supported MoveIt/RViz launch.
3. Make the pedestal/world mount and `world -> base` relationship deterministic and consistent across Gazebo, TF, and MoveIt.
4. Replace fixed-delay execution readiness with controller/action readiness and clean the stale build underlay.
5. Qualify support documentation to distinguish action-level, numeric, GUI, RViz, and obstacle-aware evidence.
6. Defer gripper control, octomap sensing, and broader collision fidelity until the corresponding profile is explicitly implemented and gated.

## Review disposition summary

| ID | Review disposition |
|---|---|
| P1 | open; visual failure confirmed, physical no-motion unproven |
| P2 | confirmed environment defect |
| P3 | expected current limitation; future gripper fidelity issue |
| P4 | session interruption explained; client cleanup remains open |
| P5 | expected SIGINT status |
| P6 | listed warnings expected; actionable items split to P15/P16 |
| P7 | hardware enable hypothesis rejected; deterministic neutral remains follow-up |
| P8 | confirmed scoped state gap |
| P9 | confirmed consequence of P8 |
| P10 | confirmed standalone-RViz configuration failure, not OMPL failure |
| P11 | reclassified as inconclusive visual test; session-3 physical state changed |
| P12 | split by warning and support scope |
| P13-P20 | newly logged related issues; no fixes attempted |

---

## Requested follow-up - RViz launch profiles (2026-07-20)

**Status:** planned as I15; implementation not started.

The user requested two supported RViz entry points:

1. A normal simulation RViz launch that starts Baxter simulation and a configured plain RobotModel/TF view without MoveIt.
2. A MoveIt simulation RViz launch that starts Baxter simulation, `move_group`, and a configured MotionPlanning display with OMPL available.

Planned requirements:

- Keep separate launch files and checked-in `.rviz` configurations for the plain and MoveIt views.
- Forward the existing `headless` option and set `use_sim_time:=true` for RViz.
- The plain profile must load `/robot_description`, display the Baxter model, and avoid the known head/finger TF errors from P8/P9.
- The MoveIt profile must load the URDF and SRDF, receive the required planning/kinematics/joint-limit parameters, connect to the root `move_group` namespace, and populate the OMPL/planner controls.
- A bare `rviz2` command is not the supported MoveIt path.
- Address the missing independent head/source-finger state needed for a complete RobotModel, without adding gripper command support.
- Preserve the existing headless simulation and CLI MoveIt smoke paths.
- Do not combine unrelated P1-P7 or P13-P20 fixes into this step.

Planned acceptance evidence:

| Profile | Pass criteria |
|---|---|
| Normal sim RViz | Baxter RobotModel loads; all expected links have TF to the fixed frame; arm motion follows `/joint_states`. |
| MoveIt sim RViz | RobotModel and SRDF load; MotionPlanning shows OMPL and configured planners; left-arm plan/execute remains available. |
| Regression | Existing `sim_tiny_trajectory` and `moveit_left_tiny` smoke commands still pass. |

Planning records:

- `MASTER_PLAN.md`: I15, RViz Simulation Launch Profiles.
- `PROMPTS.md`: self-contained I15 implementation prompt.
- Future implementation log: `logs/I15_rviz_launch_profiles.log.md`.

---

## I15 remediation disposition (2026-07-21)

Append-only update. Original observations (P1-P20) and the 2026-07-20 review are
unchanged above. This section supersedes the "implementation not started" footer:
**I15 is `completed`** (gate evidence in `logs/I15_rviz_launch_profiles.log.md`),
and the user's local GUI tests plus one follow-up fix are recorded here.

Sources for each disposition: the I15 gate log, the user's 2026-07-21 GUI runs
(Profile 1 `sim_rviz` ROS_DOMAIN_ID=42 → PASS; Profile 2 `sim_moveit_rviz`
ROS_DOMAIN_ID=43 → PASS after the RViz fix below), and the CLI MoveIt trifecta
(`moveit_left_tiny` / `moveit_tiny group:=right_arm` / `group:=both_arms`).

| ID | Disposition | Evidence |
|---|---|---|
| P1 | Fixed | Fixed `world→base` mount (`z=0.92418`), neutral-pose init, reversible/measured trajectory client. Motion visible in Gazebo **and** RViz (user Profile 1). |
| P2 | Fixed | Removed stale `~/ros_ws` auto-source + duplicate Jazzy sources; clean rebuild has no `ros_ws` reference. |
| P3 | Won't-fix (out of scope) | Gripper mimic/contact fidelity intentionally unsupported in the arm profile. |
| P4 | Fixed | Client now bounds all action waits, cancels the active goal on interrupt, uses idempotent shutdown. |
| P5 | Won't-fix (expected) | SIGINT `-2` is normal teardown status; single Ctrl+C leaves no residual process. Double Ctrl+C → Gazebo exit 1 remains cosmetic. |
| P6 | Won't-fix (expected) | Startup warnings classified non-blocking in the I15 warning table. |
| P7 | Fixed (reframed) | Deterministic neutral SRDF pose applied at startup. Hardware enable/untuck emulation rejected as root cause — not implemented. |
| P8 | Fixed | Added state-only head + source-finger interfaces → 17 independent joints (user-confirmed both profiles). |
| P9 | Fixed (via P8) | 58 link transforms now available; RobotModel resolves head/finger links. |
| P10 | Fixed | Supported project RViz launches + checked-in configs added; `move_group` publishes `robot_description_semantic`. Bare `rviz2` stays unsupported by design. |
| P11 | Fixed | Configured RViz + numeric acceptance are now separate, both gated. |
| P12 | Won't-fix (expected, scoped) | Octomap/workspace/start-state warnings expected for empty-world arm scope. |
| P13 | Fixed | Real sim-only fixed `world_joint` at `z=0.92418` + matching TF, replacing the dynamic drop. |
| P14 | Fixed | Finite controller goal/trajectory tolerances + measured final-state acceptance in both example clients. |
| P15 | Fixed | Fresh state per arm, reversible bounded targets, monotonic timeouts, cancel-on-interrupt. |
| P16 | Fixed | Controller-manager command-limit enforcement enabled; client-side validation retained. |
| P17 | Fixed | `wait_for_sim_ready` gates on both arm actions + 17 joints, replacing the 8 s timer (user saw "Simulation ready"). |
| P18 | Partially fixed | Isolated `ROS_DOMAIN_ID`/`GZ_PARTITION` + retained artifacts done. Durable archiving of `/tmp/opencode/i15_artifacts/` into `logs/` still **open**. |
| P19 | Fixed | Support/README/CHANGELOG/docs qualified; GUI + full MoveIt visualization gated. The Profile-2 RViz caveat is resolved by the fix below. |
| P20 | Fixed | ACM regenerated (sampled, 10000 trials); unjustified pairs removed, retained pairs documented. |

### Profile 2 MoveIt RViz blank screen — found post-gate, fixed 2026-07-21

The I15 gate log states MoveIt RViz reported `Global Status: Ok`. The user's
later GUI run contradicted that: RViz opened **blank** (no robot, no scene),
while CLI planning/execution passed. Root cause, verified against the current
working tree and upstream Jazzy:

1. `src/baxter_moveit_config/launch/sim_moveit.launch.py` passed the full
   `moveit_config.to_dict()` to the RViz node. Upstream
   `moveit_configs_utils/launches.py:59-63` (`generate_moveit_rviz_launch`)
   passes only `planning_pipelines`, `robot_description_kinematics`,
   `joint_limits`. The full dict makes RViz re-declare
   `robot_description_planning.joint_limits.<joint>.max_velocity` with a
   `{double}` vs `{string}` type clash, so `loadRobotModel` throws and the
   MotionPlanning display — the only display in `moveit.rviz` that renders the
   robot — never loads.
2. `src/baxter_moveit_config/config/moveit.rviz` had Grid + MotionPlanning only,
   with no standalone RobotModel/TF (unlike the working
   `baxter_gz_sim/config/sim.rviz`), so a MotionPlanning failure left nothing on
   screen.

Fix applied this session:

- `sim_moveit.launch.py`: RViz `parameters=` → upstream subset + `use_sim_time`.
- `moveit.rviz`: added `RobotModel` (`/robot_description`, Transient Local) + `TF`
  displays before MotionPlanning, mirroring the working `sim.rviz`.

Verification: both files are symlinked into `install/` (no rebuild needed);
`moveit.rviz` is valid YAML; `generate_launch_description()` builds and the three
`moveit_config` attributes resolve. Visual render (robot visible at startup, no
`loadRobotModel` type error, MotionPlanning groups populated) is the user's
manual GUI re-test — structurally verified here, GUI confirmation pending.

### Still open after I15

- P18 durable archiving of `/tmp/opencode/i15_artifacts/` into `logs/`.
- User GUI re-test of the Profile 2 RViz fix.
- 38 uncommitted files (I15 + this fix) — commit only on user request.
- Optional: Boost explicit link in `baxter_moveit_config/CMakeLists.txt` (builds
  today via transitive deps).

## Correction: Profile 2 RViz — first fix FAILED, real root cause (2026-07-22)

Supersedes the "found post-gate, fixed 2026-07-21" subsection above. That
diagnosis was wrong and the fix did not work. The user re-ran Profile 2 on
2026-07-22; RViz now renders the robot (the RobotModel/TF addition was correct
and is kept) but MotionPlanning shows a red **NO PLANNING LIBRARY LOADED** with
empty planner dropdowns, and the identical error is still present in
`~/.ros/log/rviz2_366035_1784710148227.log:18`:

```
Exception caught while processing action 'loadRobotModel': parameter
'robot_description_planning.joint_limits.left_s0.max_velocity' has invalid type:
Wrong parameter type, ... is of type {double}, setting it to {string} is not allowed.
```

What the 2026-07-21 entry got wrong: it blamed `moveit_config.to_dict()`. But the
upstream subset it was replaced with *also contains* `moveit_config.joint_limits`,
which is the actual trigger — so the swap changed nothing.

Evidence (this session):

- `move_group` is healthy on the same values: `You can start planning now!`,
  `Using planning pipeline 'ompl'`. Only the `rviz2` node throws.
- Throw site is `libmoveit_robot_model_loader.so` (only lib whose strings contain
  `_planning.joint_limits.`). Upstream `robot_model_loader.cpp` (2.12.4) declares
  `<prefix>.max_velocity` as `PARAMETER_DOUBLE` **only when `has_velocity_limits`
  resolved true** — i.e. only for the 14 joints in our `joint_limits.yaml`.
- Its `catch (const rclcpp::ParameterTypeException&)` does not catch the thrown
  `rclcpp::exceptions::InvalidParameterTypeException`, so this is fatal.
- Joints with no limits overrides (head, grippers) hit the same
  `declare_parameter(..., PARAMETER_DOUBLE)` earlier in the same loop and produce
  no error — the no-override path is safe.
- Profile 1 works because `sim_rviz.launch.py` passes only `use_sim_time`.

Two hypotheses tested and falsified — do not re-open them:

- `LC_NUMERIC=tr_TR.UTF-8` (it is set, and rviz2 is Qt) breaking `strtod`: glibc
  parses `"0.75"` fully under both `C` and `tr_TR`.
- launch_ros emitting the value as a string: driving rcl's own C parser
  (`rcl_parse_yaml_file` via ctypes) over the four real `/tmp/launch_params_*`
  files rviz2 received, in the same order, yields `max_velocity -> DOUBLE 0.75`.

The value is a well-formed double end to end; the residual mismatch is inside
rviz2's own rclcpp parameter bookkeeping and was not chased further, because the
fix removes the parameter from that node so the throwing line is never reached.
Runtime diagnostic if anyone wants to close it out:
`ros2 param describe /rviz2 robot_description_planning.joint_limits.left_s0.max_velocity`.

Fix applied 2026-07-22:

- `sim_moveit.launch.py`: dropped `moveit_config.joint_limits` from the RViz
  node's `parameters` (deliberately diverging from upstream
  `generate_moveit_rviz_launch`; `move_group` owns the limits and RViz only
  replays its already time-parameterized trajectories).
- `moveit.rviz`: rebuilt the MotionPlanning block from the upstream MoveIt
  template. Second latent bug fixed here — `Planning Group` was at the top level
  of the display, where the plugin never reads it; it belongs under
  `Planning Request:`. Now `Planning Group: both_arms`, `Query Goal State: true`,
  `Interactive Marker Size: 0.15`, giving a 6-DOF drag marker on each gripper
  (ROS 1 / Noetic style). Added the upstream `QMainWindow State` blob so the
  MotionPlanning - Trajectory Slider dock is laid out.

Verified here: both files valid and symlinked into `install/` (no rebuild);
`generate_launch_description()` builds (7 actions); rviz params no longer contain
`joint_limits`; `Planning Request.Planning Group = both_arms`. GUI confirmation
(planner list populated, markers draggable, Plan & Execute) is the user's re-test.

## Why the marker still was not seen — wrong entry point (2026-07-22, later)

Two follow-up runs, neither of which starts MoveIt RViz:

- 12:38 `sim_rviz.launch.py` — Profile 1. `sim.rviz` has Grid/RobotModel/TF only, no
  MotionPlanning display, so no marker is possible.
- 12:43 `sim_moveit.launch.py headless:=false` — starts Gazebo headed and
  `baxter_move_group`, but **no rviz2 at all**: `headless` controls Gazebo's GUI, while
  the separate `rviz` argument defaulted to `false`.

Fixed the footgun rather than the documentation: `rviz` now defaults to
`NotSubstitution(headless)`, so `headless:=false` implies RViz and `headless:=true`
(CI default) stays RViz-free. Verified both directions by evaluating the substitution,
and by a live headless run that started zero rviz2 processes.

`both_arms` confirmed safe after all: `RobotModel::setKinematicsAllocators` (moveit_core,
not robot_model_loader) has a second loop that builds the sub-group solver map for a group
with no solver of its own. left_arm and right_arm are disjoint subsets of both_arms, so
`getGroupKinematics().second` is populated and RobotInteraction renders one marker per
gripper.

`moveit.rviz` further aligned with the working ROS 1 config at
`~/baxter_noetic_ws/src/baxter_noetic/baxter_moveit_config/launch/moveit.rviz`:
`Interactive Marker Size` 0.15 → 0 (auto, as Noetic uses), the opaque `QMainWindow State`
blob replaced by Noetic's readable `collapsed:` dock keys (which is what actually makes the
Trajectory Slider visible), plus its `Planning Metrics` block and
`Scene Robot: Show Scene Robot: true`.

### `moveit_pose` relative motion was broken

`ros2 run baxter_examples moveit_pose --ros-args -p group:=left_arm -p delta_z:=0.05`
failed with `The parameter 'x' is not initialized: x`. `_parameter_is_unset` called
`node.get_parameter(name)`, which raises `ParameterUninitializedException` for a
declared-but-unset statically typed parameter (`rclpy/node.py:665-685`); its
`descriptor.type == PARAMETER_NOT_SET` guard never fired because
`declare_parameter(name, Type.DOUBLE)` sets the descriptor type to DOUBLE. Replaced with
`node.get_parameter_or(name).value is None`, which rclpy documents as returning the
alternative for uninitialized parameters.

### New example: `ik_service_client`

ROS 2 port of the Noetic `baxter_examples/scripts/ik_service_client.py`. Baxter's
`baxter_core_msgs/SolvePositionIK` is hardware-only, so it queries MoveIt `/compute_ik`
(`moveit_msgs/srv/GetPositionIK`), served by the `move_group/MoveGroupKinematicsService`
capability already in `baxter_move_group.cpp`. Keeps the ROS 1 seed poses (in `base`).

### End-to-end verification run (ROS_DOMAIN_ID=44, GZ_PARTITION=baxter_verify_44)

Live headless `sim_moveit.launch.py`, all against a real `move_group`:

- `headless:=true` started 0 rviz2 processes (CI regression intact).
- `ik_service_client -p limb:=left` → SUCCESS, 7 joints (left_s0 -0.3148 … left_w2 +0.7712).
- `ik_service_client -p limb:=right` → SUCCESS, 7 joints.
- `ik_service_client -p x:=9.0` → `INVALID POSE - No Valid Joint Solution Found`
  (MoveItErrorCodes -31), exit 1.
- `moveit_pose -p delta_z:=0.05` → z 0.063 → 0.113, position_error 0.0096 m (was a crash).
- `moveit_pose` with no target → usage message, exit 1.
- `moveit_pose -p x:=0.55 -p y:=0.25 -p z:=0.15` → position_error 0.0212 m (absolute path
  regression intact).
- Ctrl+C teardown clean, no leftover processes.

Still not verified by me: the RViz window itself (needs a display) — planner list
populated, markers draggable, Plan & Execute.

### Benign log noise, recorded so it stops being re-investigated

- `No root/virtual joint specified in SRDF. Assuming fixed joint` — correct here. Noetic's
  SRDF needs `<virtual_joint world→base>` because its URDF root is `base`; our
  `baxter_gz_control.urdf.xacro` already contains `world_joint`.
- `[Err] Physics.cc:1808 ... mimic constraint for l_gripper_r_finger_joint` — Gazebo
  physics has no mimic support; gripper fingers are out of scope.
- `No 3D sensor plugin(s) defined for octomap updates` — expected, no depth sensors.
- `tf2_echo` printing `Invalid frame ID "torso"` twice at startup — TF not published yet.
- `moveit_tiny` and `moveit_left_tiny` installing the same script — intentional, both are
  referenced in `docs/moveit_guide.md` and `docs/ci_release_checklist.md`.

## RViz MotionPlanning still fails — error moved, defect documented (2026-07-22, third run)

RViz now launches (`rviz2-10` in the launch output, so the entry-point fix works), and the
`joint_limits` failure is gone. The same exception class now names the **next** double
parameter instead:

```text
[rviz2.moveit.ros.motion_planning_frame]: MoveGroup namespace changed: / -> . Reloading params.
[rviz2.moveit.ros.rdf_loader]: Loaded robot model in 0.081 seconds
[rviz2.moveit.ros.background_processing]: Exception caught while processing action
'loadRobotModel': parameter
'robot_description_kinematics.left_arm.kinematics_solver_search_resolution' has invalid
type: ... is of type {double}, setting it to {string} is not allowed.
```

So removing `joint_limits` was correct and effective, but the defect is not specific to
joint limits — stripping parameters one at a time just moves the failure to the next
double-valued one. Per the user's instruction this round, the defect is **documented, not
fixed**, in the new `docs/known_issues.md`, together with the four ruled-out hypotheses
(Turkish `LC_NUMERIC`, launch_ros serialisation, `moveit_configs_utils` types, the `.rviz`
config) so none of them get re-investigated.

Open lead recorded for next time: the `MoveGroup namespace changed: / -> . Reloading
params.` line immediately precedes the throw. `MotionPlanningFrame` re-reads MoveIt
parameters at that point rather than using the launch-supplied ones, so the clash is in
that reload path, not in launch-time parameter loading.

Confirmed working in the same run, so the blast radius is display-only:

- `move_group`: `You can start planning now!`, OMPL + all six adapters, four
  plan-and-execute cycles all `SUCCEEDED`, clean Ctrl+C teardown.
- RViz Grid/RobotModel/TF render; only the MotionPlanning display is dead.
- `ik_service_client` left, right, custom pose all SUCCESS; `-p x:=9.0` correctly returned
  `INVALID POSE` (-31) and exit 1.
- `moveit_pose` `delta_z:=0.05`, `delta_x:=0.03` (twice), and absolute all reached target
  (position_error 0.0189-0.0278 m). The `delta_*` crash is fixed.
- IK joint values differ between runs for the same requested pose because `/compute_ik`
  seeds from the live robot state — expected, not a defect.

### Docs updated this round

`docs/known_issues.md` (new), `README.md`, `docs/index.md`, `docs/moveit_guide.md`,
`docs/ci_release_checklist.md`, `docs/compatibility_matrix.md`, `docs/maintainer_handoff.md`,
`docs/package_map.md`, `docs/simulation.md`, `docs/getting_started_sim.md`, `CHANGELOG.md`,
`.github/ISSUE_TEMPLATE/sim_bug.yml`. Status labels for `sim_moveit_rviz` moved from
"passed, manual/local GUI" to "known issue", the MotionPlanning pass criterion was removed
from the release checklist until the defect closes, and `ROS_DOMAIN_ID`/`GZ_PARTITION` were
dropped from the documented workflow at the user's request (one user, one machine, one sim
at a time). `.github/ISSUE_TEMPLATE/hardware_bridge_bug.yml` keeps its `ROS_DOMAIN_ID`
mention because that field is about ROS 1 to ROS 2 bridge networking, not local isolation.

## RESOLVED — MotionPlanning display, root cause was the locale (2026-07-22, fourth run)

P10 is closed. The display loads, the planner list populates, and both gripper markers drag
via IK.

### Root cause

`LC_NUMERIC=tr_TR.UTF-8` in the user's environment, combined with Qt's initialisation order
inside `rviz2`:

1. `rviz2/src/main.cpp` constructs `QApplication` **before** `vapp.init()` → `rclcpp::init`.
   `QApplication` calls `setlocale(LC_ALL, "")`, so the process leaves the `C` locale that
   every C program starts in.
2. `rclcpp::init` → `rcl_parse_arguments` → `rcl_parse_yaml_file` on each `--params-file`.
3. `rcl_yaml_param_parser/src/parse.c:198` accepts a scalar as a double only when `strtod`
   consumes it whole (line 202); otherwise it falls through to line 215, `DATA_TYPE_STRING`.
4. Under `tr_TR` the decimal separator is `,`, so `strtod("0.005")` stops at the `.` and the
   value lands in the override map as a **string**.
5. `loadRobotModel` → `KinematicsPluginLoader` → `kinematics::ParamListener` declares that
   key as a statically typed **double**; rclcpp rejects the string override with
   `InvalidParameterTypeException`; `RobotModelLoader` catches only `ParameterTypeException`,
   so it escapes and aborts the background job.

Measured on this machine, which is the fingerprint that identifies this cause and no other:

| value | `C` locale | after `setlocale(LC_ALL,"")` |
|---|---|---|
| `0.75` (`max_velocity`) | consumed | **string** |
| `0.005` (`kinematics_solver_search_resolution`) | consumed | **string** |
| `2.0` (`max_acceleration`) | consumed | still double |

That explains every earlier observation: stripping `joint_limits` only exposed the next
double; `max_acceleration: 2.0` never appeared because `strtod` does consume it even in
`tr_TR`; `move_group` was never affected because it has no Qt and stays in `C`; the URDF
loaded fine because it arrives on a topic, not through rcl's YAML parser.

### The previous "ruled out" verdict was wrong, and why

The third run recorded Turkish `LC_NUMERIC` + Qt as ruled out because `strtod("0.75")`
consumed the whole string under `tr_TR.UTF-8`. **That test was invalid.** A C program starts
in the `C` locale and only leaves it when something calls `setlocale` — which a standalone
test binary never does and Qt always does. The companion test that drove `rcl_parse_yaml_file`
over the temp params files had the same flaw and produced the same false negative.

Lesson for this log: when testing locale-sensitive C behaviour, the harness must call
`setlocale(LC_ALL, "")` or set the variable on the process under test. Otherwise it measures
the `C` locale and exonerates the real cause.

### The three leads carried into this run

- **`Move Group Namespace: ""` in `moveit.rviz`** — not the bug. `planning_scene_display.cpp:72`
  already defaults that property to `""` and `motion_planning_frame.cpp:604` compares it to the
  node namespace `/`, so `MoveGroup namespace changed: / -> .` prints on every MoveIt RViz
  start upstream. It still prints in the passing runs. The key was deleted anyway as
  redundant; it changed nothing. Now recorded as benign log noise.
- **The `initFromMoveGroupNS` reload path** — dead end. It creates topics/services, declares
  `default_planning_pipeline` as a string, and makes two `get_parameter_or` calls. It never
  touches kinematics parameters. It logged next to the throw only because `enable()` runs on
  the GUI thread while `loadRobotModel` runs as a background job.
- **Diff against ROS 1** — pointed the right way. The gap really was ROS 1's untyped global
  param server versus ROS 2's per-node typed declarations, just one layer below the launch
  plumbing.

### Fix

One kwarg on the `rviz2` node in `sim_moveit.launch.py`:

```python
additional_env={"LC_NUMERIC": "C"},
```

Applies to any comma-decimal locale (`tr`, `de`, `fr`, `es`, `it`, `nl`, …), not just Turkish.
An explicit `LC_ALL` would override it. `joint_limits` stays out of the RViz node's
parameters — not because it throws, but because RViz does not need limits; the stale comment
saying otherwise was replaced. `baxter_gz_sim/launch/sim_rviz.launch.py` needs nothing: it
passes only `use_sim_time`, a bool.

### Verification

`LC_NUMERIC=C ros2 launch ...` was run first with **no code changes** and passed, proving the
diagnosis before anything was edited. After the fix, under the real `tr_TR` shell, both
`sim_moveit.launch.py headless:=false` and `sim_moveit_rviz.launch.py`:

- 0 `Exception caught while processing action 'loadRobotModel'`; 0 `No robot state or robot
  model loaded`.
- `ros2 param get /rviz2 robot_description_kinematics.left_arm.kinematics_solver_search_resolution`
  → `Double value is: 0.005`. Before the fix the key was not declared at all.
- `/query_planner_interface` → `OMPL`, `RRTConnectkConfigDefault` for `both_arms`, `left_arm`,
  `right_arm`.
- `get_interactive_markers` → `EE:goal_left_gripper` and `EE:goal_right_gripper`; both visible
  in a window capture with `both_arms` selected and Plan / Plan & Execute enabled.
- Regression: bare `sim_moveit.launch.py` still starts headless with no `rviz2` process;
  clean single-Ctrl+C teardown, no leftovers.

### Follow-on: "RViz moves but Gazebo does not" — not a defect

Reported after the fix. Investigated via the launch logs: across all three sessions RViz had
sent **zero** requests — no `MoveGroupMoveAction: Received request`, no `/execute_trajectory`,
no controller traffic. Nothing was ever asked of `move_group`, so nothing could move.

Both execute paths were then proven independently:

- `/move_action` — `moveit_tiny -p group:=both_arms`, reversible, `max_error=0.0097 rad`.
- `/execute_trajectory` (the path RViz's `Execute` button uses, distinct from `Plan & Execute`)
  — raw action-client probe, `left_s1` moved 0.199 rad, error 0.0009 rad vs goal.

A live monitor was then armed on the launch log while the user clicked `Plan & Execute` in the
running session. Result: request received, trajectories sent to **both** controllers, both
`Goal reached, success!`, `Completed trajectory execution with status SUCCEEDED`,
`Plan and Execute request complete!`.

Conclusion: the earlier observation was the RViz-side preview. Dragging a marker moves the
orange goal-state ghost, and `Plan` replays the planned path on a loop (`Loop Animation: true`,
which matches the ROS 1 reference config). Both look like a moving robot while Gazebo sits
still. Only `Execute` and `Plan & Execute` command the controllers. A hypothesis that
`both_arms` lacked its own kinematics solver and so could not plan was raised and **falsified**
by that click — the subgroup solvers are sufficient. Documented in `moveit_guide.md` so it is
not re-reported.

### Docs updated this round

`docs/known_issues.md` (open defect → resolved entry with the corrected record, and the
`MoveGroup namespace changed` line moved into the benign-noise table), `docs/ci_release_checklist.md`
(MotionPlanning pass criterion restored), `README.md`, `docs/index.md`, `docs/moveit_guide.md`
(preview-vs-execute note added), `docs/compatibility_matrix.md`, `docs/maintainer_handoff.md`,
`docs/package_map.md`, `CHANGELOG.md`. `SUPPORT.md` already carried the correct label.
Status for `sim_moveit_rviz` moved from "known issue" back to "passed, manual/local GUI".
