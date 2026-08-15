---
step: I14
title: "Release Hardening"
agent_date: 2026-07-09
status: completed
previous_steps: [I00, I01, I02, I03, I04, I05, I06, I07, I08, I09]
---

# I14: Release Hardening

## Task

Prepared the public sim-first release hardening baseline after I09 documentation. This step stayed release-only: no hardware bridge tooling, action shims, gripper implementation, compatibility layer, Zenoh fallback, optional examples, ROS 1 dependencies, bridge build, hardware access, or `plan/` edits were added.

## Findings

Added release hygiene files:

- `LICENSE` with BSD-3-Clause terms for local project code.
- `CONTRIBUTING.md`, `SUPPORT.md`, `SECURITY.md`, and `CHANGELOG.md`.
- `.github/ISSUE_TEMPLATE/` forms for sim bug, hardware bridge bug, docs issue, safety concern, dependency pin update, and feature request.
- `.github/pull_request_template.md`.
- `docs/release_notes_v0.1.0-sim.md`.
- `docs/maintainer_handoff.md`.

Updated local package manifests to use `BSD-3-Clause`:

```text
src/baxter_bringup/package.xml
src/baxter_gz_sim/package.xml
src/baxter_examples/package.xml
src/baxter_moveit_config/package.xml
```

Imported ECN package manifests were not edited. The default imported source still carries its upstream root license at `src/baxter_common_ros2/LICENSE`; `baxter_maintenance_msgs` still has its upstream manifest TODO, which is not a local project package field and was not changed in I14.

Release support labels used in `SUPPORT.md` and `docs/release_notes_v0.1.0-sim.md`:

| Profile | Label |
|---|---:|
| `sim` | passed |
| `sim_moveit` | passed, manual/local smoke |
| default CI/devcontainer | passed, hardware-free |
| `hardware_bridge` | blocked |
| supervised hardware motion | blocked |
| Zenoh/compatibility fallback | deferred |

Static release-policy checks:

```text
$ python3 # release policy checks: required files, issue-template YAML, local package licenses, default .repos pin, support labels, no raw safety-topic publishing in release docs
release_static_checks=passed
required_issue_templates=docs_issue.yml,feature_request.yml,hardware_bridge_bug.yml,pin_update.yml,safety_concern.yml,sim_bug.yml
local_package_license=BSD-3-Clause
default_repos_pin=678bfabea8c895b4134951a6c076217a90b9e0e6
```

Default hardware-free build and pin gate:

```text
$ source /opt/ros/jazzy/setup.bash && test "$(git -C src/baxter_common_ros2 rev-parse HEAD)" = "678bfabea8c895b4134951a6c076217a90b9e0e6" && rosdep install --from-paths src --ignore-src -r -y && colcon build --base-paths src --symlink-install --packages-skip baxter_bridge && source install/setup.bash
#All required rosdeps installed successfully
Starting >>> rethink_ee_description
Starting >>> baxter_core_msgs
Starting >>> baxter_examples
Starting >>> baxter_maintenance_msgs
Finished <<< rethink_ee_description [0.33s]
Starting >>> baxter_description
Finished <<< baxter_description [0.44s]
Starting >>> baxter_gz_sim
Starting >>> baxter_bringup
Finished <<< baxter_examples [1.05s]
Finished <<< baxter_bringup [0.70s]
Finished <<< baxter_gz_sim [0.74s]
Starting >>> baxter_moveit_config
Finished <<< baxter_maintenance_msgs [1.70s]
Finished <<< baxter_moveit_config [0.56s]
Finished <<< baxter_core_msgs [2.95s]

Summary: 8 packages finished [3.10s]
```

CI release checklist static checks:

```text
$ source /opt/ros/jazzy/setup.bash && source install/setup.bash && python3 -m compileall -q src/baxter_bringup src/baxter_gz_sim src/baxter_moveit_config src/baxter_examples && python3 # import local launch/example modules
python_import_checks=passed

$ ros2 run xacro xacro src/baxter_gz_sim/urdf/baxter_gz_control.urdf.xacro >/tmp/baxter_gz_control_i14.urdf && check_urdf /tmp/baxter_gz_control_i14.urdf
robot name is: baxter
---------- Successfully Parsed XML ---------------

$ python3 # static SRDF/MoveIt config checks
moveit_static_check=passed groups=['both_arms', 'left_arm', 'left_hand', 'right_arm', 'right_hand']
```

Gate result: passed. `docs/ci_release_checklist.md` passes for the sim-first release scope, the default `.repos` path still imports only the pinned ECN source, default build still skips `baxter_bridge`, release docs do not imply vendor support or hardware support, and beginner/release docs do not teach raw safety-topic publishing.

## Decisions

- Chose BSD-3-Clause for local project code because it is small, permissive, common in ROS workspaces, and compatible with the BSD-style imported Baxter description license.
- Kept release notes as `docs/release_notes_v0.1.0-sim.md` and used capability naming rather than claiming a stable hardware-ready release.
- Kept hardware bridge and hardware motion issue templates even though the profiles are blocked, so reports are separated from supported sim issues without implying support.
- Did not add hardware setup docs, safety operation docs, bridge tooling, action shims, grippers, compatibility layers, Zenoh fallback, or optional examples because I10-I13 remain blocked/deferred.

## Open Questions

- Long-term maintainer group remains unnamed.
- Docs hosting target beyond GitHub Markdown remains undecided.
- Full Gazebo+MoveIt runtime remains manual/local smoke until teardown stability is proven in CI.
- Hardware bridge host, physical robot access, and university network policy still block I10.

## Artifacts

- `LICENSE`
- `CONTRIBUTING.md`
- `SUPPORT.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/ISSUE_TEMPLATE/sim_bug.yml`
- `.github/ISSUE_TEMPLATE/hardware_bridge_bug.yml`
- `.github/ISSUE_TEMPLATE/docs_issue.yml`
- `.github/ISSUE_TEMPLATE/safety_concern.yml`
- `.github/ISSUE_TEMPLATE/pin_update.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/pull_request_template.md`
- `docs/release_notes_v0.1.0-sim.md`
- `docs/maintainer_handoff.md`
- `README.md`
- `docs/index.md`
- `docs/licensing_and_sources.md`
- `docs/compatibility_matrix.md`
- `docs/ci_release_checklist.md`
- `docs/repos_and_pins.md`
- `src/baxter_bringup/package.xml`
- `src/baxter_gz_sim/package.xml`
- `src/baxter_examples/package.xml`
- `src/baxter_moveit_config/package.xml`
- `logs/I14_release_hardening.log.md`
- `MASTER_PLAN.md`
- `PROMPTS.md`
