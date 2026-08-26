# Maintainer Handoff

This handoff is for the sim-first release baseline. It is not a hardware runbook.

## Release Baseline

| Item | Current state |
|---|---:|
| `sim` | passed |
| `sim_rviz` | passed, manual/local GUI |
| `sim_moveit` | passed, manual/local smoke |
| `sim_moveit_rviz` | passed, manual/local GUI |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | experimental and unsupported |
| supervised hardware motion | unsupported |
| Zenoh/compatibility fallback | deferred |

## Default Release Check

From the repository root:

```bash
source /opt/ros/jazzy/setup.bash
test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6"
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
source install/setup.bash
```

Then follow `docs/ci_release_checklist.md` for static checks and manual smoke checks.

## Pin Update Handoff

Pin updates are release work, not incidental cleanup.

Required evidence:

1. Full current SHA and proposed SHA.
2. License status of the source.
3. Default build result with `--packages-skip baxter_bridge`.
4. Sim smoke result if model, sim, controller, or MoveIt behavior can change.
5. Updated `docs/repos_and_pins.md`, `CHANGELOG.md`, and release notes.

## Hardware Blockers

Hardware support remains unavailable until maintainers complete and review:

- Physical Baxter access.
- Bridge host choice.
- University network policy.
- I10 non-motion bridge gate.
- I11 safety/action-shim gate.
- I12 supervised tiny motion gate.

Do not merge hardware bridge tooling, action shims, gripper implementation, Zenoh fallback, or hardware examples into the default sim path without new gates and logs.

## Ownership Backlog

- Name the long-term maintainer group.
- Decide docs hosting beyond GitHub Markdown if needed.
- Revisit full Gazebo+MoveIt CI only if a reliable GUI-capable runner is available; local teardown remains a required gate.
- Run a future handoff drill where someone other than the primary author follows the sim docs from a clean checkout.

## Files Maintainers Should Review Before Tagging

- `README.md`
- `SUPPORT.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `docs/simulation_baseline.md`
- `docs/ci_release_checklist.md`
- `docs/repos_and_pins.md`
- `docs/licensing_and_sources.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/pull_request_template.md`
