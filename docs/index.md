# Baxter ROS 2 Jazzy Docs

The sim-first baseline and the hardware path. The hardware bridge, the action
shims and supervised motion have passed their gates on a real BR-01 — under
supervision, in dated sessions (2026-07-22, 2026-07-24, and I20 on 2026-07-25).
Read [hardware_runbook.md](hardware_runbook.md) before going near a robot.

Support levels for every profile live in one place:
**[support_matrix.md](support_matrix.md)**.

## Start here

1. Build the sim workspace — [getting_started_sim.md](getting_started_sim.md).
2. Launch Gazebo and run `sim_tiny_trajectory` — [simulation.md](simulation.md).
3. Use MoveIt only after the sim controllers work — [moveit_guide.md](moveit_guide.md).
4. Verify the whole thing without a robot — [sim_test_commands.md](sim_test_commands.md).

Hit a problem in MoveIt RViz? Check [known_issues.md](known_issues.md) first — a
comma-decimal `LC_NUMERIC` is the known trigger for four symptoms at once.

## Simulation

| Doc | Purpose |
|---|---|
| [getting_started_sim.md](getting_started_sim.md) | The default 15-minute path: devcontainer or native Ubuntu 24.04, then a smoke test. |
| [simulation.md](simulation.md) | Gazebo launch modes, controllers, joint states, and the expected diagnostics. |
| [moveit_guide.md](moveit_guide.md) | MoveIt 2 in sim, the IK/pose clients, and what MoveIt does on hardware. |
| [sim_test_commands.md](sim_test_commands.md) | Copy-paste sheet for every check that needs no robot. |
| [known_issues.md](known_issues.md) | Open defects, resolved defects with their root cause, and the benign log noise to ignore. |

## Hardware

Required reading before a session, in this order.

| Doc | Purpose |
|---|---|
| [hardware_runbook.md](hardware_runbook.md) | Lab procedures for the bridge and supervised motion. Safety rules live here. |
| [hardware_test_commands.md](hardware_test_commands.md) | Copy-paste command sheet for a full session, with the interlock and malformed-goal checks. |
| [hardware_day_plan.md](hardware_day_plan.md) | Phase-by-phase schedule: order, abort criteria, decision points. |
| [noetic_native_notes.md](noetic_native_notes.md) | Robot-side behaviour for a future native ROS 1 stack, plus the plan for dropping the Noetic container. |

## Project reference

| Doc | Purpose |
|---|---|
| [support_matrix.md](support_matrix.md) | Canonical support levels, tested profile, local and imported packages, the ECN pin and its update rule, and what is deferred. |
| [licensing_and_sources.md](licensing_and_sources.md) | Source/license status and the local BSD-3-Clause project license. |
| [ci_release_checklist.md](ci_release_checklist.md) | Default CI checks, gate status, and release no-go conditions. |
| [maintainer_handoff.md](maintainer_handoff.md) | Maintainer release checklist, pin policy, and hardware handoff items. |
| [publish_checklist.md](publish_checklist.md) | Human-only steps: repository description and topics, vulnerability reporting, merge, tag, branch protection, release. |
| [release_notes_v0.2.0.md](release_notes_v0.2.0.md) | Current publish notes and support labels. |
| [manual/](manual/) | LaTeX sources for a ~30-page printable workspace manual assembled from these docs. `cd docs/manual && make`. |
| [archive/](archive/) | Frozen material: superseded release notes and the completed I12 working plan. |
| [reference/baxter_legacy/](reference/baxter_legacy/) | Legacy Rethink Baxter PDFs (Intera user guide, research demos, thesis). |

## Default rules

Build from the repository root, and run one simulation at a time:

```bash
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source /opt/ros/jazzy/setup.bash && source install/setup.bash
```

Default docs, devcontainer, and CI are hardware-free.
