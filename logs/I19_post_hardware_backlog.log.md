---
step: I19
title: "Post-Hardware Backlog — Desk Work"
agent_date: 2026-07-25
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15, I17, I12, I18]
---

# I19: Post-Hardware Backlog — Desk Work

## Task

Work the improvement backlog the I18 hardware session produced
(`logs/I19_backlog_plan.md`, evidence in `logs/I18_hardware_day.log.md`), in the
order that plan recommends: items 1, 10, 3, 5, 6, 7. All desk work — the robot
stayed idle, disabled and tucked throughout. Item 9 (full MoveIt Setup Assistant
re-run) is GUI work and was deliberately left for its own sitting.

One commit per item, `bash scripts/test_bridge_loopback.sh` after any
`py_bridge.py` change, kill by explicit PID.

Baseline confirmed before starting: `dry_run_test` `OVERALL: PASS`, 24/24.

## Findings

### F-A. Item 1 — a second `/robot/state` publisher now refuses motion (I18 F1)

`SafetyStateChecker` keeps the topic it was constructed with and counts
publishers on it; `is_safe_for_motion()` returns False unless the count is
exactly 1, checked before anything else. `describe()` appends
`CONTESTED: N publishers on /robot/state, expected 1`, so the shim's existing
rejection line names the fault instead of printing a state that looks safe.

The gate also runs mid-goal (`follow_joint_trajectory_shim.py:497`) and in the
hold loop (`:280`), so a second publisher appearing during a move aborts and
holds. That is intended: the in-flight case is the dangerous one.

`hardware_bringup.launch.py` gained an `OpaqueFunction` that runs `ros2 node
list` and raises if `mock_baxter_robot` is present, aborting before either shim
starts. Verified both ways:

```text
# with the mock running
[ERROR] [launch]: Caught exception in launch (see debug for traceback):
mock_baxter_robot is running; it publishes a fake safe /robot/state. Stop it
(kill by PID) and confirm `ros2 node list` is clean before bringing up the
hardware shims.
launch exit: 1

# on a clean graph
/left_arm_shim
/right_arm_shim
```

**Test 25** covers the shim half: a second `AssemblyState` publisher flips
`safe_for_motion` to False and the goal is rejected, then the graph recovers.

Worth recording for anyone writing a similar test: publishing the rogue state
from `test_node` and calling `destroy_publisher()` does **not** clear the
endpoint from the graph cache — the count stayed at 2 for the full 5 s window,
and the recovery assertion failed. Publishing from a throwaway node and calling
`destroy_node()` clears it immediately. The isolated two-node repro dropped the
count instantly either way, so this only shows up in the full suite.

### F-B. Item 10 — recordings of what we publish now decode (I18 F23)

`ROS1Publisher` answered every TCPROS handshake with `md5sum "*"` and no message
definition, so rosbag stored our `joint_command` with an empty schema. New
module-level `ROS1_MSG_META` carries the real md5sum and `.msg` text for the four
published types, taken from `rosmsg md5` / `rosmsg show -r` inside
`baxter-noetic:n07`:

| type | md5sum |
|---|---|
| `baxter_core_msgs/JointCommand` | `19bfec8434dd568ab3c633d187c36f2e` |
| `std_msgs/Float64` | `fdb28210bfa9d7c91146260178d9a584` |
| `std_msgs/Bool` | `8b94c1b53db61fb6aed406028ad6332a` |
| `std_msgs/Empty` | `d41d8cd98f00b204e9800998ecf8427e` |

Anything unlisted still falls back to the wildcard, and `ROS1Subscriber` is
untouched — the wildcard is correct on the subscribe side and is what lets the
bridge take any type with no schema.

Proven with a rosbag round-trip in the Noetic image, publishing from
`ROS1Publisher` with the real serializer:

```text
types:   baxter_core_msgs/JointCommand [19bfec8434dd568ab3c633d187c36f2e]
type   : baxter_core_msgs/JointCommand
md5sum : 19bfec8434dd568ab3c633d187c36f2e
mode   : 1
names  : ['left_s0', 'left_s1', 'left_e0', 'left_e1', 'left_w0', 'left_w1', 'left_w2']
command: [0.11, -0.55, 0.13, 0.75, 0.15, 1.26, 0.17]
decoded 20 messages
```

`scripts/test_bridge_loopback.sh` is the standing regression: `rostopic echo` is
a genuine rospy subscriber and validates the publisher's md5sum, so a wrong
constant fails at the desk rather than on the robot.

### F-C. Item 3 — the robot's `header.stamp` survives the bridge (I18 F14)

`_flush_ros2_queue` overwrote every JointState stamp with bridge dequeue time.
`deser_joint_state` already parsed the ROS 1 stamp correctly; it was simply
discarded. Now published as received, with two exceptions:

- a stamp of exactly 0 (a ROS 1 peer that never stamped) still falls back to
  receive time, rather than publishing 1970;
- a stamp more than `CLOCK_SKEW_WARN_SEC` (0.5 s) from this host's clock raises
  one throttled warning.

The warning exists because the robot and the workstation keep time
independently, and when they disagree MoveIt discards the state as out of date
without saying why — expensive to diagnose with the robot in front of you.

Verified against a real roscore: a ROS 1 JointState stamped `12345.678900000`
arrives on ROS 2 as `sec: 12345 nanosec: 678900000`, and the warning fires once
with the right sign and magnitude.

Nothing downstream regressed: the shim measures staleness from its own receive
time (`_joint_state_ns`, `follow_joint_trajectory_shim.py:205`), not from this
stamp, so `joint_states_stale_sec` behaves exactly as before.

### F-D. Item 5 — the cancel-hold check settles before it judges (I18 F2)

`_check_hold` compared two joint states taken immediately after the cancel, so on
a real arm it measured the deceleration transient (~0.02 rad, right at
`FINAL_TOLERANCE_RAD`) rather than a hold failure. It now retries the same
one-second window until the arm is quiet, bounded by `SETTLE_TIMEOUT_SEC` — the
shape `send_trajectory` already used for goal completion. An arm that genuinely
sags never goes quiet, so a real failure still fails.

### F-E. Item 6 — `duration` and `offset` are parameters (I18 F9)

Distance and duration were hardcoded at 0.35 rad over 3.0 s = 0.12 rad/s, so no
run came near the shim's 2.0 rad/s clamp and every tolerance number in the repo
describes gentle motion only. Both are now ros-params defaulting to the old
constants, and the per-move log line reports the resulting rad/s — the number to
watch when walking a run toward the clamp.

No client-side speed validation was added: the shim already rejects an over-fast
segment at accept time with a precise reason (`needs X rad/s, limit is Y
(max_step_rad_per_cycle)`), which is more useful than a guess in the client.

### F-F. Item 7 — clean shutdown is quiet (I18 F17)

`rclpy.try_shutdown()` replaces `rclpy.shutdown()`, and the except clause also
catches `ExternalShutdownException`: with rclpy's SIGINT handler having already
shut the context down, `spin()` leaves that way rather than by
`KeyboardInterrupt`, which was the second half of the traceback. SIGINT by
explicit PID now gives exit 0 and a log that ends on its own last line.

**A dead end worth recording.** The first attempt used
`rclpy.init(signal_handler_options=SignalHandlerOptions.NO)`, matching the four
interactive clients in this repo. That made the bridge unkillable by SIGINT when
started as a background job: the shell sets SIGINT to ignore for those, Python
honours an inherited `SIG_IGN`, and only rclpy's own handler overrides it. A
long-running bridge gets backgrounded, so it keeps rclpy's handler. The reason is
in a comment at the call site.

### F-G. `baxter_env.sh` killed every `set -e` caller whenever the robot was offline

**Unplanned, and it blocked the verification the plan depended on.**
`scripts/test_bridge_loopback.sh` — the check to run after any `py_bridge.py`
change — died immediately with exit 2 and no message.

With the robot off the network, `getent hosts "$BAXTER_HOST"` and
`ip route get "$BAXTER_IP"` both fail. Their command substitutions were
unguarded, so sourcing the script under `set -e` (which the loopback script sets,
with `pipefail`) killed the caller on the spot, with stdout redirected and stderr
suppressed. Confirmed pre-existing by stashing the day's changes and reproducing.

Both lookups now fall back to the empty string, which is what the defaults
already expect: `BAXTER_IP` falls back to the hostname, `ROS_IP` to unset.

This had presumably been true since the script was written; it only surfaces on a
desk day, and desk days had not been running the loopback test.

### F-H. `ros2 run` lies about what code is running, in two different ways

Both cost real time today and both are the same class as I18's F1 and F12 —
something you believe you are running, and are not.

**1. `baxter_examples` runs a build-time copy.** It is `ament_cmake` and installs
its scripts with `install(PROGRAMS ...)`, which copies even under
`--symlink-install`. Two rehearsals for items 5 and 6 therefore tested the *old*
script: the `duration:=1.0` override silently did nothing and the run still
reported success. Caught only because a newly added log line never appeared.
After `colcon build --packages-select baxter_examples` the same commands showed
`in 1.00 s (0.50 rad/s)` and completed each move in ~1.1 s against ~3.1 s.
`baxter_hardware_bridge` is `ament_python` and *is* symlinked, so it picks edits
up live — that inconsistency is what makes the trap effective.

**2. `ros2 run` spawns the node as a child process.** Killing the PID that `$!`
returns leaves the node running, orphaned and still publishing:

```text
$ kill 72583        # the `ros2 run` wrapper
$ ros2 node list
/mock_baxter_robot  # still there, 60 s later
$ ps -eo pid,ppid,cmd | grep mock_robot
72587  4591  /usr/bin/python3 .../lib/baxter_hardware_bridge/mock_robot
```

The graph was telling the truth; the kill was wrong. `--no-daemon` made no
difference, because the node really was alive. Kill the child PID.

## Gate evidence

```text
$ source scripts/baxter_env.sh && ros2 run baxter_hardware_bridge dry_run_test
... 25 PASS lines ...
OVERALL: PASS
exit 0

$ bash scripts/test_bridge_loopback.sh
=== OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy) ===

$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 9 packages finished [3.95s]
```

Mock rehearsal, `dry_run.launch.py mock_mode:=false`, after the rebuild:

```text
defaults        left_s1 -0.550 -> -0.200 rad in 3.00 s (0.12 rad/s)   both arms, exit 0
duration:=1.0
offset:=0.5     left_s1 -0.550 -> -0.050 rad in 1.00 s (0.50 rad/s)   both arms, exit 0
cancel_after_sec:=1.0   Cancellation hold verified: max_drift=0.0000 rad (settled in 1.02 s)
```

## Decisions

| Decision | Why |
|---|---|
| Refuse motion whenever the `/robot/state` publisher count is not exactly 1, including mid-goal | Whose message we sampled is unknowable while the topic is contested. Aborting in flight is the case I18 F1 shows is dangerous |
| The launch guard checks node names via `ros2 node list`, not rclpy | One ~2 s discovery pass at bringup, no rclpy state in the launch process. The shim's own publisher-count gate is the real backstop; this just fails loudly instead of arming against a mock |
| Real md5sum on the publish side only; wildcard kept on subscribe | The wildcard is what lets the bridge carry any type with no schema table. Only recordings of what *we* publish were undecodable |
| `std_msgs/Bool` and `std_msgs/Empty` included though nothing publishes them yet | They are the rest of the Baxter command surface named in the backlog item, and cost one line each |
| Preserve the robot's stamp outright rather than adding a second field | I18 F14 suggested keeping receive time "somewhere". Nothing consumes it — the shim uses its own receive time — so a second field would have been unused weight |
| Warn on clock skew rather than correcting it | Correcting silently would hide a real configuration fault. The failure it prevents (MoveIt discarding states) is silent and expensive to diagnose on robot time |
| No client-side speed validation on `duration`/`offset` | The shim already rejects over-fast segments at accept time and names which bound applied |
| Keep rclpy's SIGINT handler in `py_bridge` | `SignalHandlerOptions.NO` makes a backgrounded bridge unkillable; see F-F |
| **I17 R7 closed — the success path keeps its current behaviour** | I17 left "the shim stops commanding after SUCCESS" to the user for want of data. I18 F11 supplies it: arms uncommanded for ~20 s drifted **0.001 rad**, so gravity compensation already holds this pose. The legacy's indefinite hold would trade hand-guiding and cuff/zero-G behaviour for no measured gain |

## Corrections to earlier logs

Recorded here rather than by editing those logs, per `AGENTS.md`.

- **I18 F14** asks that the bridge "preserve the original stamp somewhere rather
  than destroy it". As built there is no second stamp: the robot's is published
  and receive time is used only when the incoming stamp is zero.
- **I18 "Not done"** lists P7 MoveIt-on-hardware as untested, which its own F18
  in the same file contradicts — F18 records planner SUCCESS, 31 waypoints, and
  the shim executing the goal on the robot. F18 is the correct entry.
- **I18 "Not done"** also lists the cancel sweep as blocked on F2. F2 is fixed
  (item 5), so the sweep at `cancel_after_sec` 0.5 / 2.0 is now runnable.
- **I18 F3** and its "Recommended tolerance values" section carry the withdrawn
  26× margin and the 0.05 proposal. F22 in the same log supersedes both;
  documentation outside `logs/` has been updated to F22's numbers.

## Open Questions

- **Every item here is desk-verified only.** Three have hardware behaviour that
  only the robot can confirm: the publisher-count gate against the real bridge,
  the clock-skew warning against the robot's actual clock, and a real capture
  decoding through the fixed md5sum path.
- **`path_tolerance_rad` stays at 0.2.** F22 measured a worst in-flight lag of
  0.0352 rad (5.7× margin) on gentle motion only. Item 6 now makes fast motion
  possible; 0.15 is the most aggressive defensible value and only with that data.
- **Item 9**, the full MoveIt Setup Assistant re-run, is untouched. 52
  `disable_collisions` pairs is sparse, and the pair that blocked planning from
  the robot's own untuck pose was found by hand.
- `analyze_tracking_lag.py` can now read `|command − measured|`, but not from the
  I12 bag — that recording has the empty schema baked in. It needs a fresh
  capture.

## Artifacts

| Path | Change |
|---|---|
| `src/baxter_hardware_bridge/baxter_hardware_bridge/safety.py` | `publisher_count()`; `is_safe_for_motion()` requires exactly one publisher; `describe()` names a contested topic |
| `src/baxter_hardware_bridge/launch/hardware_bringup.launch.py` | `refuse_if_mock_running` `OpaqueFunction` aborting the launch |
| `src/baxter_hardware_bridge/baxter_hardware_bridge/dry_run_test.py` | Test 25; docstring list completed for Tests 21-25 |
| `scripts/py_bridge.py` | `ROS1_MSG_META` and real metadata in the publish handshake; `_keep_robot_stamp()`; `CLOCK_SKEW_WARN_SEC`; `try_shutdown()` + `ExternalShutdownException` |
| `src/baxter_examples/baxter_examples/sim_tiny_trajectory.py` | `_check_hold` settle loop; `HOLD_WINDOW_SEC`; `duration` / `offset` parameters; rad/s in the per-move log line |
| `scripts/baxter_env.sh` | Guarded the two robot-address lookups so `set -e` callers survive an offline robot |
| `scripts/analyze_tracking_lag.py` | Docstring updated: F23 fixed, and why the rewrite waits for a fresh capture |
| `logs/I19_backlog_plan.md` | Status table updated; robot-session queue recorded |

Commits: `e7f86e7` (item 1), `b4a3e5a` (F-G), `d801a7a` (item 10), `3c802b8`
(item 3), `41cd5f7` (item 5), `d445baa` (item 6), `7748197` (item 7).
