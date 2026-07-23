# Pull Request

## Profile Changed

- [ ] `sim`
- [ ] `sim_rviz`
- [ ] `sim_moveit`
- [ ] `sim_moveit_rviz`
- [ ] default CI/devcontainer
- [ ] docs only
- [ ] pin/source metadata
- [ ] hardware bridge or safety scope, blocked unless a gate says otherwise

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

- [ ] This PR does not claim hardware support without I10-I12 evidence
- [ ] This PR does not claim hardware support or expand prep-only bridge tooling into a support claim; grippers, Zenoh fallback, and hardware examples stay out of the default sim path unless new gates and logs exist
- [ ] Beginner and release docs do not teach raw safety-topic publishing or hardware enable commands

## Notes

Link issues, logs, or release notes here.
