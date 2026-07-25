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
| `hardware_bridge` | passed, supervised (2026-07-22) |
| supervised hardware motion | passed, supervised (2026-07-24) |
| MoveIt on hardware | passed, supervised (2026-07-24) |
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

## Hardware Scope

The I10 non-motion, I11 action-shim and I12 supervised-motion gates have all
passed on BR-01 `011412P0024` (2026-07-22 and 2026-07-24). Reproducing any of it
still needs physical Baxter access, a bridge host, and whatever the local network
policy allows.

What a maintainer should hold the line on:

- Hardware claims name the session that earned them. One supervised session on
  one robot at low speed is what exists; do not let a PR widen that.
- Anything touching the shim, the safety gate or `scripts/py_bridge.py` needs
  `dry_run_test` (25 cases) green, and `scripts/test_bridge_loopback.sh` for
  bridge changes, before merge.
- Gripper commands, Zenoh fallback and hardware examples stay out of the default
  sim path without new gates and logs.

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
- `docs/release_notes_v0.1.0-sim.md`
- `docs/ci_release_checklist.md`
- `docs/repos_and_pins.md`
- `docs/licensing_and_sources.md`
- `.github/ISSUE_TEMPLATE/`
- `.github/pull_request_template.md`
