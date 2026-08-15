# Release Notes: v0.2.0

Date: 2026-07-25 (draft for annotated tag after checklist green)

Sim-first public baseline for `baxter_ros2_jazzy`: Gazebo Harmonic, `ros2_control`,
MoveIt 2 in simulation, hardware-free CI. Supervised hardware is documented as an
appendix with dated gates — not general product support.

This supersedes the support labels in [archive/release_notes_v0.1.0-sim.md](archive/release_notes_v0.1.0-sim.md) (historical).
Full change list: `CHANGELOG.md` under `v0.2.0 - 2026-07-25`.

## Headline (simulation)

| Profile | Support label | Evidence |
|---|---:|---|
| `sim` | passed | Gazebo Harmonic, arm controllers, `sim_tiny_trajectory`. |
| `sim_rviz` | passed, manual/local GUI | Checked-in RobotModel/TF profile. |
| `sim_moveit` | passed, manual/local smoke | Readiness-gated OMPL; reversible left/right/both-arm checks. |
| `sim_moveit_rviz` | passed, manual/local GUI | MotionPlanning with OMPL/RRTConnect. |
| default CI/devcontainer | passed, hardware-free | Build, import/model, dry_run_test, static MoveIt checks. |

## Hardware appendix (supervised, one BR-01)

| Profile | Support label | Evidence |
|---|---:|---|
| `hardware_bridge` | passed, supervised | I10/I11, 2026-07-22, on one BR-01. |
| supervised hardware motion | passed, supervised | I12, 2026-07-24, both arms; I20 characterisation 2026-07-25. |
| MoveIt on hardware | passed **with limits**, supervised | 2026-07-24/25. From RViz the left arm aborted 8 of 11 goals on `left_w0`/`left_e0`; right completed 9 of 11. Use Velocity Scaling 0.1 and single-arm groups. |
| Zenoh/compatibility fallback | deferred | Not in default install/devcontainer/CI. |

### What I20 measured

- In-flight lag ≈ 0.4 s × commanded velocity.
- Default `path_tolerance_rad` 0.2 aborts near ~0.5 rad/s (`left_s1` 0.202 vs 0.200).
- The shim's 2.0 rad/s per-cycle clamp is unreachable under that tolerance.
- Setup Assistant collision sampling does not converge; the checked-in 54-pair SRDF matrix is kept.
- **MoveIt at default planning speeds is not usable on this robot.** From RViz the
  left arm aborted 8 of 11 goals on `left_w0`/`left_e0`, every one
  `PATH_TOLERANCE_VIOLATED` at exactly the 0.2 rad limit, while the right
  completed 9 of 11 on the same `both_arms` plans. One controller aborting ends
  the whole dual-arm execution (8 x `CONTROL_FAILED`). Use `Velocity Scaling: 0.1`
  and single-arm groups. Open defect, tracked in `docs/known_issues.md`.

### Still not claimed

Sustained duty, gripper commands, a second robot, motion above the ~0.5 rad/s abort
point, raising `path_tolerance_rad`, or any unsupervised operation. Every hardware
figure above comes from supervised sessions on a single robot with an e-stop in hand.

## Default Source Pin

```text
CentraleNantesRobotics/baxter_common_ros2@678bfabea8c895b4134951a6c076217a90b9e0e6
```

Default builds keep `--packages-skip baxter_bridge`. No bloom/rosdistro in this release.

## Getting Started

See `README.md` and `docs/getting_started_sim.md`. Hardware: `docs/hardware_runbook.md`
(set `BAXTER_HOST` explicitly; scripts have no lab serial/IP default).

## License

Local project code: BSD-3-Clause. Imported ECN sources keep upstream licenses.
Reference PDFs under `docs/reference/baxter_legacy/` are third-party and not covered
by the root BSD-3-Clause license.
