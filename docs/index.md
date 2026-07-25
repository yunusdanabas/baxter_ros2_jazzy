# Baxter ROS 2 Jazzy Docs

This documentation covers the sim-first baseline and the hardware path. The hardware bridge, the action shims and supervised motion have all passed their gates on a real BR-01 — under supervision, at low speed, in single sessions (2026-07-22 and 2026-07-24). Read `hardware_runbook.md` before going near a robot.

## Mode Selector

| Mode | Support level | Doc |
|---|---:|---|
| Gazebo Harmonic sim | passed | `getting_started_sim.md`, `simulation.md` |
| Gazebo + RViz | passed, manual/local GUI | `simulation.md` |
| MoveIt 2 sim | passed, manual/local smoke | `moveit_guide.md` |
| Gazebo + MoveIt RViz | passed, manual/local GUI | `moveit_guide.md` |
| Default CI/devcontainer | passed, hardware-free | `ci_release_checklist.md` |
| Hardware bridge | passed, supervised | `hardware_runbook.md` — 2026-07-22, one BR-01 |
| Supervised hardware motion | passed, supervised | `hardware_runbook.md` — 2026-07-24, both arms, low speed |
| MoveIt on hardware | passed, supervised | `moveit_guide.md` — 2026-07-24, single session |
| Zenoh/compatibility fallback | deferred | Not in default docs |

## Recommended Path

1. Build the sim workspace with `getting_started_sim.md`.
2. Launch Gazebo and run `sim_tiny_trajectory` with `simulation.md`.
3. Use MoveIt only after the sim controllers are working; see `moveit_guide.md`.
4. Check `known_issues.md` before reporting a MoveIt RViz problem — a comma-decimal `LC_NUMERIC` is the known trigger.

## Reference Docs

| Doc | Purpose |
|---|---|
| `known_issues.md` | Resolved defects with their root cause, and the benign log noise to ignore. |
| `hardware_runbook.md` | Lab procedures for the hardware bridge and supervised motion. Required reading before a robot session. |
| `hardware_test_commands.md` | Copy-paste command sheet for a full hardware session, with the interlock and malformed-goal checks. |
| `hardware_day_plan.md` | Stage-by-stage schedule for a full day with the robot: order, time budget, abort criteria, and the fallback when the robot will not enable. |
| `noetic_native_notes.md` | Robot-side behavior notes for a future native ROS 1 Noetic stack; filled in during robot days. |
| `container_free_path.md` | What still needs the Noetic Docker image, what is trivially replaceable over `py_bridge`, and why untucking is the one real exception. |
| `i12_completion_plan.md` | Historical: the plan that finished I12. Kept as the record of what was decided and why; the gate passed 2026-07-24. |
| `package_map.md` | What is implemented, imported, skipped, and deferred. |
| `repos_and_pins.md` | Default `.repos`, ECN SHA pin, and update rule. |
| `licensing_and_sources.md` | Source/license status and local BSD-3-Clause project license. |
| `compatibility_matrix.md` | Tested Ubuntu/ROS/Gazebo/MoveIt/source-pin profile status. |
| `ci_release_checklist.md` | Default CI checks and manual smoke checklist. |
| `release_notes_v0.1.0-sim.md` | First sim-first release notes and support labels. |
| `maintainer_handoff.md` | Maintainer release checklist, pin policy, and hardware handoff items. |
| `reference/baxter_legacy/` | Legacy Rethink Baxter PDFs (Intera user guide, research demos, thesis). |

## Default Rules

Use this build command from the repository root:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
```

Before checks, source ROS 2 Jazzy and the workspace install:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
```

Default docs, devcontainer, and CI are hardware-free.
