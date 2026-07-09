# Pull Request

## Profile Changed

- [ ] `sim`
- [ ] `sim_moveit`
- [ ] default CI/devcontainer
- [ ] docs only
- [ ] pin/source metadata
- [ ] hardware bridge or safety scope, blocked unless a gate says otherwise

## Checks

- [ ] `colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`
- [ ] Pinned ECN SHA verified
- [ ] Sim smoke run, if affected
- [ ] MoveIt sim smoke run, if affected
- [ ] `docs/ci_release_checklist.md` reviewed, if release/support labels changed

## Pins And Licensing

- [ ] No default `.repos` import added beyond the pinned ECN source
- [ ] Any pin change uses a full SHA and has license evidence
- [ ] No copied/imported third-party code or config without a compatible license

## Safety Boundary

- [ ] This PR does not claim hardware support without I10-I12 evidence
- [ ] This PR does not add hardware bridge tooling, action shims, grippers, compatibility layers, Zenoh fallback, or hardware examples to the default sim path
- [ ] Beginner and release docs do not teach raw safety-topic publishing or hardware enable commands

## Notes

Link issues, logs, or release notes here.
