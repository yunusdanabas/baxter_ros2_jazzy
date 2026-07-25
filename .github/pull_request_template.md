# Pull Request

## Profile Changed

- [ ] `sim`
- [ ] `sim_rviz`
- [ ] `sim_moveit`
- [ ] `sim_moveit_rviz`
- [ ] default CI/devcontainer
- [ ] docs only
- [ ] pin/source metadata
- [ ] hardware bridge or safety scope — can move a real robot

## Checks

- [ ] `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`
- [ ] Pinned ECN SHA verified
- [ ] Sim smoke run, if affected
- [ ] MoveIt sim smoke run, if affected
- [ ] Numeric final state and clean teardown verified, if runtime is affected
- [ ] `docs/ci_release_checklist.md` reviewed, if release/support labels changed

## Pins And Licensing

- [ ] No default `.repos` import added beyond the pinned ECN source
- [ ] Any pin change uses a full SHA and has license evidence
- [ ] No copied/imported third-party code or config without a compatible license

## Safety Boundary

- [ ] This PR does not widen a hardware claim past the session that earned it (one BR-01, low speed, supervised)
- [ ] If it touches the shim, the safety gate or `py_bridge.py`: `ros2 run baxter_hardware_bridge dry_run_test` passes 25/25, and `bash scripts/test_bridge_loopback.sh` passes for bridge changes
- [ ] Grippers, Zenoh fallback, and hardware examples stay out of the default sim path unless new gates and logs exist
- [ ] Beginner and release docs do not teach raw safety-topic publishing or hardware enable commands

## Notes

Link issues, logs, or release notes here.
