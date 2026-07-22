# Baxter ROS 2 Jazzy Docs

This documentation covers the sim-first baseline that has passed gates in I01-I09 and the I14 release-hardening baseline. Hardware bridge and supervised hardware motion are not documented as supported modes yet.

## Mode Selector

| Mode | Support level | Doc |
|---|---:|---|
| Gazebo Harmonic sim | passed | `getting_started_sim.md`, `simulation.md` |
| Gazebo + RViz | passed, manual/local GUI | `simulation.md` |
| MoveIt 2 sim | passed, manual/local smoke | `moveit_guide.md` |
| Gazebo + MoveIt RViz | passed, manual/local GUI | `moveit_guide.md` |
| Default CI/devcontainer | passed, hardware-free | `ci_release_checklist.md` |
| Hardware bridge | blocked | Not in default docs |
| Hardware motion | blocked | Not supported |
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
| `package_map.md` | What is implemented, imported, skipped, and deferred. |
| `repos_and_pins.md` | Default `.repos`, ECN SHA pin, and update rule. |
| `licensing_and_sources.md` | Source/license status and local BSD-3-Clause project license. |
| `compatibility_matrix.md` | Tested Ubuntu/ROS/Gazebo/MoveIt/source-pin profile status. |
| `ci_release_checklist.md` | Default CI checks and manual smoke checklist. |
| `release_notes_v0.1.0-sim.md` | First sim-first release notes and support labels. |
| `maintainer_handoff.md` | Maintainer release checklist, pin policy, and blocked hardware handoff items. |
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
