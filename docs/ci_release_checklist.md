# CI And Release Checklist

This checklist reflects the current sim-first baseline. It is not a hardware release checklist.

## Default CI Checks

Default CI is hardware-free and should keep doing these checks:

```bash
source /opt/ros/jazzy/setup.bash
test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Run release evidence from `bash --noprofile --norc` or an equivalent clean shell. Before rebuilding after a workspace/underlay change, remove generated `build/`, `install/`, and `log/`. Generated setup files must not reference a deleted workspace.

Then run:

| Check | Current status |
|---|---:|
| Placeholder maintainer contact rejected (`package.xml` / SECURITY / CoC) | passed, 2026-07-25 |
| Python compile/import for local launch/example/hardware-bridge files | passed, 2026-07-25 |
| `ruff --select F` — unused imports and undefined names | passed, 2026-07-26 |
| `colcon test` on `baxter_examples` (`trajectory_helpers` logic) | passed, 16 tests, 2026-07-26 |
| Cleanup-handler AST guard (3 `except BaseException` handlers inspected) | passed, 2026-07-25 |
| Hardware-free `baxter_hardware_bridge` dry_run_test | passed, 25/25, 2026-07-25 |
| Xacro expansion of `baxter_gz_control.urdf.xacro` | passed, 2026-07-25 |
| `check_urdf` on generated model | passed, 2026-07-25 |
| Static fixed-world, 17-state/14-command, and neutral-state checks | passed, 2026-07-25 |
| Finite controller limit/tolerance checks | passed, 2026-07-25 |
| Static SRDF ACM and MoveIt/OMPL/RViz config checks | passed, 2026-07-25, `acm_pairs=54` |

The CI path must not install ROS 1 dependencies, robot-network dependencies, or Zenoh. Local `baxter_hardware_bridge` dry-run is hardware-free and is part of CI.

## Manual Sim Smoke

The commands live in **[sim_test_commands.md](sim_test_commands.md)** §3-§5 and
are not duplicated here. Run one simulation at a time.

What must be true before this is release evidence:

```text
all three controllers active
17 independent joints with advancing stamps
fixed world -> base at z=0.92418
RobotModel and TF status OK
outbound and return max_error <= 0.02 rad for each arm, direct and via MoveIt
cancellation accepted, position held, bounded exit, no traceback
moveit_pose reaches both absolute and delta targets
ik_service_client solves left/right and exits non-zero on an unreachable pose
MotionPlanning panel loads with a populated OMPL planner dropdown
motion visible in Gazebo, robot visible in RViz
one Ctrl+C leaves no Gazebo, bridge, controller, robot-state-publisher,
  MoveIt, or RViz process behind
```

A hang, a leftover process, or a `move_group` crash fails the gate; Gazebo `-2`
after SIGINT does not. The MotionPlanning panel failing to load is almost always
a comma-decimal `LC_NUMERIC` — see [known_issues.md](known_issues.md).

Retain the launch logs, numeric outputs, environment values, and
before/target/return screenshots or video before citing any of it as evidence.

## Hardware Gates

| Gate | Status |
|---|---:|
| I10 hardware bridge non-motion | passed, 2026-07-22 |
| I11 hardware action shims and safety tools | passed, 2026-07-22 |
| I12 supervised hardware motion | passed, 2026-07-24 |
| I20 path-tolerance speed / SRDF re-run | passed, 2026-07-25 |

I10–I12 and I20 passed on a single BR-01 under supervision. Release notes may
state the I20 result that default `path_tolerance_rad` 0.2 binds near ~0.5 rad/s
and must not imply 2.0 rad/s clamp use, sustained duty, gripper commands, or any
second robot. A claim without a session date and a log behind it does not go in
release notes.

## Release Hardening Checks

Before tagging a sim-first release, verify these files exist and use the same profile labels as this checklist:

| File | Required status |
|---|---:|
| `LICENSE` | BSD-3-Clause for local project code |
| `CONTRIBUTING.md` | Present |
| `SUPPORT.md` | Present |
| `SECURITY.md` | Present, real contact — CI rejects `@example.com` |
| `CODE_OF_CONDUCT.md` | Present, enforcement contact matches SECURITY |
| `CHANGELOG.md` | Present |
| `.github/ISSUE_TEMPLATE/` | Sim bug, hardware bridge bug, docs, safety concern, pin update, feature request |
| `.github/pull_request_template.md` | Present |
| `docs/sim_test_commands.md` | Present (no-robot verification sheet) |
| `docs/archive/release_notes_v0.1.0-sim.md` | Present (historical) |
| `docs/release_notes_v0.2.0.md` | Present (current publish notes) |
| `docs/maintainer_handoff.md` | Present |
| `docs/publish_checklist.md` | Present (human-only publish steps) |
| GitHub private vulnerability reporting | **Not yet enabled — human action, blocks “ready”**; see [publish_checklist.md](publish_checklist.md) §3 |

## Release No-Go Conditions

Do not release the sim-first profile if any of these are true:

| Condition | Current status |
|---|---:|
| Default `.repos` imports anything besides the pinned ECN source | no-go if true |
| Default build omits `--packages-skip baxter_bridge` | no-go if true |
| Docs claim **unearned or over-broad** hardware support (beyond dated I10–I20 supervised evidence) | no-go if true |
| Beginner docs teach raw safety-topic publishing | no-go if true |
| Root project or local package licenses still contain `TODO` | no-go if true |
| Any local `package.xml` / SECURITY / CoC still uses `@example.com` | no-go if true |
| Script/docker defaults hardcode a lab serial or LAN IP | no-go if true |
