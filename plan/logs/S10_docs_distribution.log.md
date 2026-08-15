---
step: S10
title: "Documentation and Distribution Strategy"
agent_date: 2026-06-23
status: completed
previous_steps: [S01, S02, S03, S04, S05, S06, S07, S08, S09]
---

# S10: Documentation and Distribution Strategy

## Task

Designed the documentation and distribution strategy for the future `baxter_ros2_jazzy` workspace. This was a planning-only step. No ROS 2 package code, launch files, `.repos` files, documentation files, or release assets were implemented.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `logs/S02_audit_community_packages.log.md`
- `logs/S03_local_repo_analysis.log.md`
- `logs/S04_bridge_architecture.log.md`
- `logs/S05_simulation_architecture.log.md`
- `logs/S06_moveit_ros2_control.log.md`
- `logs/S07_dev_experience_tooling.log.md`
- `logs/S08_package_mapping.log.md`
- `logs/S09_risk_register.log.md`
- `MASTER_PLAN.md`

No changes were made to `baxter_noetic_ref/`.

## Findings

### Executive Summary

The future repository should present itself as a **community/university Baxter ROS 2 Jazzy workspace**, not an official vendor SDK and not a native ROS 2 robot firmware migration. The first screen of `README.md` should force users to pick a support profile before running commands:

| Profile | README Label | Release Claim |
|---|---|---|
| `sim` | Supported after smoke | Gazebo Harmonic + `ros2_control` arm trajectory execution. |
| `sim_moveit` | Supported after smoke | MoveIt 2 one-arm planning/execution in sim. |
| `hardware` | Hardware bridge, non-motion | Real Baxter bridge-host setup and non-motion checks only unless motion gate passes. |
| `hardware_moveit` | Supervised hardware motion | Advertise only after tiny low-speed trajectory gate passes for each advertised arm. |
| `experimental_zenoh` | Experimental fallback | Maintainer-only fallback after IT, safety YAML, and target-robot validation. |

Default distribution should be **source-based through pinned `.repos` files**, not bloom/apt packages. `CentraleNantesRobotics/baxter_common_ros2` should be the only default external source dependency, pinned initially to `678bfabea8c895b4134951a6c076217a90b9e0e6`. Rosdistro inclusion is a later possibility for message/description packages only, after licensing, CI, maintainer ownership, and upstream coordination are stable.

### README Structure

Recommended first screen:

1. Title: `baxter_ros2_jazzy`
2. One-line scope statement: "ROS 2 Jazzy workspace for Baxter simulation, MoveIt 2, and bridged real-hardware operation; community-maintained; no native robot firmware migration."
3. Badges:
   - `ROS 2 Jazzy`
   - `Ubuntu 24.04 Noble`
   - `Gazebo Harmonic`
   - `MoveIt 2`
   - `source .repos install`
   - CI build/model status once implemented
   - Optional docs badge once docs are hosted
4. Hardware warning box:
   - Real Baxter support is bridge-host based.
   - No launch auto-enables the robot.
   - Hardware motion is supervised and gated.
5. Mode selector table:

| I want to... | Profile | Start Here | Main Command Shape | Support Level |
|---|---|---|---|---|
| Try Baxter without hardware | `sim` | `docs/getting_started_sim.md` | `ros2 launch baxter_gz_sim sim.launch.py headless:=true` | Supported after sim smoke. |
| Use MoveIt 2 in Gazebo | `sim_moveit` | `docs/moveit_guide.md` | `ros2 launch baxter_bringup sim_moveit.launch.py` | Supported after MoveIt sim smoke. |
| Check a real robot bridge | `hardware` | `docs/hardware_bridge_setup.md` | `ros2 launch baxter_hardware_bridge smoke_hardware.launch.py` | Non-motion only until gate passes. |
| Execute MoveIt on real hardware | `hardware_moveit` | `docs/hardware_safety.md` | `ros2 launch baxter_hardware_bridge hardware_moveit.launch.py allow_motion:=false` | Supervised only after tiny trajectory gate. |
| Try the Zenoh fallback | `experimental_zenoh` | `docs/experimental_zenoh.md` | Maintainer-specific | Experimental. |

The README should not put raw `ros2 topic pub /robot/set_super_enable`, `/robot/set_super_reset`, or `/robot/set_super_stop` commands in the beginner path. Link users to `hardware_enable_status` behavior instead.

### Documentation Tree

Recommended future `docs/` tree:

| Path | Audience | Purpose |
|---|---|---|
| `docs/index.md` | All users | Short docs landing page mirroring the README mode selector. |
| `docs/getting_started_sim.md` | New students, sim-only users | 15-minute devcontainer + sim path. |
| `docs/simulation.md` | Sim users, contributors | Gazebo Harmonic, `ros_gz`, `gz_ros2_control`, controllers, camera/gripper optionality. |
| `docs/moveit_guide.md` | Students, sim-only users | Regenerated `baxter_moveit_config`, one-arm scope, action names, smoke checks. |
| `docs/hardware_bridge_setup.md` | Instructors, lab admins | Bridge host, robot LAN, ROS 1 env, `ROS_MASTER_URI`, `ROS_IP`, `ROS_DOMAIN_ID`, ECN arbitration, allowlist, smoke checks. |
| `docs/hardware_safety.md` | Instructors, students, external labs | Physical checklist, e-stop expectations, enable/status wrapper behavior, action-shim rejection, speed ratio/timeouts, ownership. |
| `docs/examples.md` | Students | Curated examples: `sim_tiny_trajectory`, `sim_moveit_neutral`, `hardware_bridge_smoke`, `hardware_enable_status`, optional `gripper_open_close`. |
| `docs/troubleshooting.md` | All users | DDS discovery, missing meshes, controller inactive, Gazebo startup, MoveIt controller names, bridge/camera/gripper failures. |
| `docs/package_map.md` | Contributors, maintainers | S08 package map, local packages, adopted packages, bridge-host-only packages, intentionally not recreated packages. |
| `docs/compatibility_matrix.md` | External labs, maintainers | Tested OS/ROS/Gazebo/MoveIt/RMW/hardware support table and deferred validation backlog. |
| `docs/repos_and_pins.md` | Maintainers, contributors | `.repos` files, pin update policy, license gates, full SHA requirements. |
| `docs/licensing_and_sources.md` | Maintainers, external labs | Adopted/reference/skipped third-party sources and license status. |
| `docs/ci_release_checklist.md` | Maintainers | Build, lint, model, sim, MoveIt, hardware non-motion, hardware motion, licensing, release notes. |
| `docs/maintainer_handoff.md` | Future maintainers, lab admins | Bridge-host runbook, release cadence, pin review, hardware inventory, known risks, ownership. |
| `docs/experimental_zenoh.md` | Maintainers only | Rethought `baxter-zenoh` fallback, IT/network constraints, restricted YAML requirement. |

Keep docs boring and profile-oriented. Do not create separate pages for deferred Classic Gazebo, old MoveIt 1, Qt IO sim, maintenance/tare/update workflows, or broad Noetic example parity except as "intentionally not recreated" notes.

### 15-Minute Student Onboarding

Target path for a new student using the default devcontainer and `sim` profile:

| Minute | Step | Expected Outcome |
|---:|---|---|
| 0-2 | Clone `baxter_ros2_jazzy` and open default devcontainer. | Noble/Jazzy/Harmonic dependencies available. |
| 2-4 | Import default core sources: `vcs import src < repos/baxter_core.repos`. | ECN common packages pinned by full SHA. |
| 4-8 | Run `rosdep install` and `colcon build --symlink-install`. | Core/model/sim packages build. |
| 8-10 | Source `install/setup.bash`. | ROS 2 workspace active. |
| 10-13 | Launch headless sim: `ros2 launch baxter_gz_sim sim.launch.py headless:=true`. | Baxter spawns; arm controllers active. |
| 13-15 | Run `sim_tiny_trajectory --arm left` or documented equivalent. | Tiny one-arm `FollowJointTrajectory` succeeds. |

The onboarding doc should include a fallback if Gazebo GUI is unavailable: keep `headless:=true`, run controller and trajectory smoke, then view model in RViz through `moveit_rviz.launch.py` or `baxter_description.launch.py`.

### Hardware Bridge-Host Guide

`docs/hardware_bridge_setup.md` should be written for instructors and lab admins, not new students.

Required sections:

| Section | Required Content |
|---|---|
| Hardware topology | Baxter ROS 1 robot wired to one lab bridge host; students use SSH/devcontainer on bridge host or controlled ROS 2 lab domain. |
| Robot LAN | Fixed robot-facing bridge-host IP, robot IP/hostname, no reliance on campus DNS or `.local`. |
| ROS 1 env | `ROS_MASTER_URI=http://<baxter-host>:11311`, `ROS_IP=<bridge-host-robot-lan-ip>`, exact target robot graph validation. |
| ROS 2 env | One `ROS_DOMAIN_ID` per Baxter bench; tested RMW documented; no arbitrary campus Wi-Fi promise. |
| ECN bridge | `baxter_bridge` from `CentraleNantesRobotics/baxter_common_ros2`, pinned SHA, restricted allowlist, `SAFE_CMD=True` expectation, `allow_multiple:=False`. |
| Arbitration | `/bridge_auth`, `/bridge_force`, bridge publisher display, one active command owner per limb. |
| Smoke checks | Network, bridge process, `/robot/state`, `/robot/joint_states`, IK services, camera services, gripper state/properties, action shim availability, no enable/no motion. |
| No auto-enable | `hardware_bridge.launch.py` and `hardware_moveit.launch.py` do not enable, reset, or move the robot automatically. |
| Recovery | How to stop bridge processes, close cameras, clear command ownership, inspect `/robot/state`, and hand off to another instructor. |

Bridge docs should keep `baxter_legacy` as reference-only until license verification and packaging decisions are complete.

### Hardware Safety Guide

`docs/hardware_safety.md` should be a release blocker for any hardware docs.

Required content:

| Topic | Documentation Requirement |
|---|---|
| Physical checklist | Clear workspace, robot stable, correct bench/domain, e-stop reachable, cables clear, grippers/cameras installed as documented. |
| E-stop expectations | Physical e-stop is primary emergency stop; software stop is secondary/admin-only. |
| Enable/status tool | Document `hardware_enable_status` behavior: prints `ready`, `enabled`, `stopped`, `error`, `estop_button`, `estop_source`; requires explicit operator confirmation for enable/disable/reset. |
| No raw beginner commands | Do not teach raw topic publishing to safety topics in beginner docs. |
| Action-shim gating | Hardware action shims reject goals unless `/robot/state` is ready, enabled, not stopped, not in error, and not e-stopped. |
| Cancel behavior | Cancel/failure holds current position; routine cancel does not call `/robot/set_super_stop`. |
| Speed/timeout defaults | Action shims set conservative `/robot/limb/{side}/set_speed_ratio` and finite `/robot/limb/{side}/joint_command_timeout` before motion. |
| Unsafe commands | Torque, raw-position, unrestricted velocity, collision suppression, maintenance/tare/update are instructor-only or deferred. |
| Multi-student ownership | One bridge host per Baxter; `allow_multiple:=False`; instructor owns `/bridge_force`; no per-student motion bridge containers. |
| Motion gate | Hardware motion claim requires supervised tiny low-speed trajectory per advertised arm, feedback, cancel/hold, safe state gating. |

### Compatibility Matrix

Use a dedicated `docs/compatibility_matrix.md` with support labels and a tested-profile table.

Support labels:

| Label | Meaning |
|---|---|
| Supported | Release gate passed and documented. |
| Optional | Available only if installed/enabled and smoke-tested. |
| Bridge non-motion | Real robot bridge checks pass without enable or motion. |
| Supervised motion | Real hardware motion tested only under physical supervision. |
| Experimental | Maintainer-only; not part of default support. |
| Reference-only | Not imported; used only as research material. |

Compatibility matrix format:

| Component | Tested Version / Pin | Profile | Status | Gate / Notes |
|---|---|---|---|---|
| Ubuntu | 24.04 Noble | all | Required | Jazzy Tier 1 target. |
| ROS 2 | Jazzy | all | Required | No native ROS 1 on Noble. |
| Gazebo | Harmonic | `sim`, `sim_moveit` | Supported after smoke | Headless launch and controller gate. |
| MoveIt 2 | Jazzy apt/source as documented | `sim_moveit`, `hardware_moveit` | Supported/supervised by profile | KDL + OMPL one-arm scope. |
| `baxter_common_ros2` | `678bfabea8c895b4134951a6c076217a90b9e0e6` | core/hardware | Adopted | BSD-3-Clause; pin update requires smoke gates. |
| RMW | `rmw_fastrtps_cpp` default; Cyclone DDS if tested | all | Tested field required | Record actual CI/lab RMW. |
| Bridge host | Noble/Jazzy + ECN bridge + ROS 1 support path | `hardware` | Deferred until target host smoke | Must not be implied solved. |
| Real Baxter robot | Target robot graph | `hardware` | Deferred | Validate `/robot/state`, `/robot/joint_states`, IK, cameras, grippers, actions. |
| Cameras | Head camera first | sim/hardware optional | Optional | One stream on demand; not all streams by default. |
| Grippers | Electric gripper if installed/modeled | sim/hardware optional | Optional | Inventory required. |
| Zenoh | `baxter-zenoh` pinned full SHA if used | `experimental_zenoh` | Experimental | IT approval and restricted YAML required. |

Deferred validation backlog should be visible in the same page or linked from it:

| Backlog Item | Current Status | Blocks | Future Check |
|---|---|---|---|
| Target Baxter ROS 1 graph | Deferred | Hardware support | Run `hardware_bridge_smoke` on robot. |
| ECN bridge installability | Deferred | Hardware bridge docs | Clean bridge-host install rehearsal. |
| DDS/IT policy | Deferred | Remote student hardware workflow | Test discovery or require SSH/devcontainer. |
| Zenoh acceptance | Deferred | `experimental_zenoh` | IT approval, port/network test, restricted YAML. |
| Gripper/camera inventory | Deferred | Optional examples/support labels | Physical inspection and smoke checks. |
| ECN description joint names | Deferred | Core/model, sim, MoveIt, hardware shims | Verify legacy `left_s0`...`right_w2` names. |
| Unlicensed repo status | Deferred | Reuse/import decisions | License review or keep reference-only. |
| Headless Gazebo CI stability | Deferred | Required sim CI gate | Repeated CI smoke. |
| MoveIt hardware action-name compatibility | Deferred | `hardware_moveit` | Test `/robot/limb/{side}` action names, add aliases only if needed. |
| Course need for sim `JointCommand` | Deferred | `baxter_sim_compat` scope | Instructor decision. |
| Maintainer ownership | Deferred | Production/lab support claim | Named maintainer group and handoff drill. |

### `.repos` Documentation

`docs/repos_and_pins.md` should document these files:

| File | Default? | Intended Contents | License Gate |
|---|---:|---|---|
| `repos/baxter_core.repos` | Yes | `CentraleNantesRobotics/baxter_common_ros2` pinned to `678bfabea8c895b4134951a6c076217a90b9e0e6`. | BSD-3-Clause detected; verify package manifests during implementation. |
| `repos/baxter_sim.repos` | Optional/no-op initially | No unlicensed sim repo by default; local sim packages live in this repo. | Do not import `BaxterMotionPlanning` unless license changes. |
| `repos/baxter_hardware.repos` | Bridge-host only | ECN common if standalone bridge-host setup needs it; optional `baxter_legacy` only after license verification. | No `baxter_legacy` default import until verified. |
| `repos/baxter_experimental.repos` | Explicit opt-in | `RethoughtRobotics/baxter-zenoh`, `RethoughtRobotics/BaxterSDK`, optional `CentraleNantesRobotics/baxter_gz`, all pinned by full SHA. | Experimental; restricted topic YAML before student use. |

Pin update policy:

- Default external dependencies use full SHAs, never floating branches.
- Pin updates require release-note entry and passing relevant gates: build, model, sim, MoveIt, hardware non-motion if hardware affected, licensing review.
- Unlicensed sources remain reference-only and must not appear in default `.repos`.
- Experimental pins must be marked as unsupported by default.

### Relationship To Noetic And Community Sources

Documentation should use four labels consistently:

| Label | Source Examples | Meaning |
|---|---|---|
| Adopted | `CentraleNantesRobotics/baxter_common_ros2` | Imported by default or profile, pinned, smoke-tested. |
| Referenced | Noetic repo, `angysof16/BaxterMotionPlanning`, `CentraleNantesRobotics/baxter_gz`, `dabaspark/baxter_sdk_nvidia_any_os` | Used for design comparison only; not copied/vendor imported unless license/status changes. |
| Experimental | `RethoughtRobotics/baxter-zenoh`, `RethoughtRobotics/BaxterSDK` | Explicit opt-in fallback; not default support. |
| Not recreated | Classic Gazebo packages, Qt IO sim, maintenance workflows, broad Noetic examples, MoveIt 1 launch/plugins, native real-Baxter `ros2_control` | Intentionally out of first-release scope. |

The Noetic reference should be described as the ROS 1 API and behavior reference. The Jazzy repo should not claim drop-in parity with the Noetic SDK, Gazebo Classic, or MoveIt 1 stack.

### Release And Distribution Strategy

Recommended release strategy:

| Item | Strategy |
|---|---|
| Version tags | Use `v0.1.0-sim`, `v0.2.0-hardware-bridge`, or normal semver with profile status in release notes. Avoid `1.0` until handoff and hardware gates are stable. |
| Release notes | Include tested profile table, pins, CI result, manual hardware gates, known risks, deferred validation backlog, and support labels. |
| Distribution | Source checkout + `vcs import` from `.repos` for first release. |
| Docker/devcontainer | Default devcontainer for sim/MoveIt/docs/build; bridge-host setup documented separately. |
| CI | Build/lint/model/MoveIt fake checks by default; headless sim only if stable; no hardware/ROS 1/Zenoh/default camera CI requirement. |
| Support policy | Best-effort community/university support; supported profiles only after gates; hardware motion supervised only. |
| Security policy | Report safety/security issues privately if possible; do not publish exploit-like unsafe hardware instructions in issues. |
| Rosdistro | Not first release. Consider later only for message/description packages after sustained maintainer ownership and CI. |

Rosdistro decision:

- **Now:** Do not pursue rosdistro inclusion. Use source `.repos` and pinned SHAs.
- **Later:** Consider bloom/rosdistro for `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, and `rethink_ee_description` only if licensing is clean, package manifests are standard, CI is stable, and a maintainer commits to releases.
- **Not realistic initially:** Do not promise apt packages for bridge-host workflows, hardware action shims, Gazebo sim, MoveIt config, or experimental Zenoh until the workspace has stable users and release ownership.

### Issue Templates

Recommended `.github/ISSUE_TEMPLATE/` set:

| Template | Required Fields |
|---|---|
| `sim_bug.yml` | Profile (`sim`/`sim_moveit`), OS, ROS 2 distro, Gazebo version, RMW, launch command, controller list, `/joint_states` status, logs. |
| `hardware_bridge_bug.yml` | Bridge host OS, ECN pin, robot graph status, `ROS_MASTER_URI`, `ROS_IP`, `ROS_DOMAIN_ID`, RMW, smoke check results, whether robot was enabled. |
| `docs_issue.yml` | Page path, unclear step, expected audience, proposed correction. |
| `safety_concern.yml` | Affected profile, safety risk, whether real hardware was involved, immediate mitigation; route to maintainers urgently. |
| `dependency_pin_update.yml` | Repo, current SHA, proposed SHA, reason, license status, smoke gates run, release-note impact. |
| `feature_request.yml` | Profile, user story, course/lab need, hardware/sim impact, safety/licensing risks, why existing profiles do not cover it. |

Pull request template should ask:

- Which profile changed?
- Which smoke checks passed?
- Did dependencies or `.repos` pins change?
- Does this touch hardware safety, bridge allowlists, or raw command topics?
- Does this copy or import third-party code/config, and what is the license?

### Contribution, Support, And Security Docs

Recommended top-level files:

| File | Content |
|---|---|
| `CONTRIBUTING.md` | Profile labels, package layout, coding style, tests/smoke checks, dependency pin rules, license rules, hardware safety review requirement. |
| `SUPPORT.md` | Supported profiles by release, unsupported/deferred scope, how external labs report hardware compatibility, no official vendor support. |
| `SECURITY.md` | Safety/security contact, private reporting for unsafe hardware behavior, no public raw dangerous command recipes. |
| `CHANGELOG.md` | Profile-gated changes, pins, compatibility matrix updates, known risks. |
| `LICENSE` | Project license once chosen; third-party license page must remain separate. |

### What S11 Should Carry Forward

S11 should include documentation and distribution requirements as part of final go/no-go criteria, not as an appendix only.

Required S11 go/no-go criteria:

| Area | S11 Requirement |
|---|---|
| README | Mode selector and support labels exist before public release. |
| Student onboarding | 15-minute `sim` path is documented and matches smoke gates. |
| Hardware docs | Bridge-host setup and safety docs exist before any hardware support claim. |
| Release notes | Tested-profile table and deferred backlog included for every tag. |
| Licensing | Default `.repos` excludes unlicensed sources. |
| Distribution | First release uses source `.repos`; no apt/rosdistro promise. |
| Handoff | Maintainer handoff/runbook and ownership backlog carried into final blueprint. |

## Decisions

1. **README must start with a mode selector.** Profiles are `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, and `experimental_zenoh`; each has a visible support label and gate.
2. **Documentation tree should be profile-oriented.** Prioritize `getting_started_sim`, `simulation`, `moveit_guide`, `hardware_bridge_setup`, `hardware_safety`, `compatibility_matrix`, `repos_and_pins`, `licensing_and_sources`, `ci_release_checklist`, and `maintainer_handoff`.
3. **The 15-minute onboarding path is sim-first only.** It uses the default devcontainer, `repos/baxter_core.repos`, `colcon build`, `sim.launch.py headless:=true`, and `sim_tiny_trajectory`.
4. **Hardware docs are bridge-host/admin docs.** They must cover robot LAN, `ROS_MASTER_URI`, `ROS_IP`, `ROS_DOMAIN_ID`, ECN arbitration, restricted allowlist, smoke checks, and no auto-enable.
5. **Safety docs are mandatory before hardware support.** Beginner docs must not normalize raw enable/reset/stop topic publishing.
6. **Compatibility matrix must include unresolved validation items.** Deferred S09 backlog items remain visible until tested; do not present them as solved.
7. **Default distribution is source `.repos`.** First release should not promise bloom, apt packages, or rosdistro availability.
8. **Rosdistro inclusion is later, message/description-only at most.** Consider it only after stable CI, licensing, maintainer ownership, and upstream release readiness.
9. **Default `.repos` files must exclude unlicensed sources.** `BaxterMotionPlanning`, `baxter_legacy`, `dabaspark/baxter_sdk_nvidia_any_os`, and stale unlicensed MoveIt repos remain reference-only unless license status changes.
10. **Issue templates must separate sim, hardware bridge, docs, safety, dependency pins, and features.** Safety concerns and dependency pin updates require extra fields.
11. **Release notes must use tested-profile tables.** Hardware bridge non-motion and hardware motion are separate claims.
12. **S11 should treat documentation as a release gate.** README, compatibility matrix, hardware safety docs, `.repos` docs, release checklist, and maintainer handoff are required blueprint outputs.

## Open Questions

- Which exact docs hosting target should the implementation use: GitHub Markdown only, GitHub Pages, Read the Docs, or a ROS docs site later?
- What project license will the future local `baxter_ros2_jazzy` repository use?
- Who will be named in `SUPPORT.md`, `SECURITY.md`, and `docs/maintainer_handoff.md` as the maintainer group after graduation?
- Will the target lab allow student laptops on the ROS 2 hardware domain, or should all hardware docs require SSH/devcontainer use on the bridge host?
- Which RMW should the compatibility matrix list as tested first: default Fast DDS only, Cyclone DDS too, or a lab-specific choice?
- Will the course require `baxter_sim_compat` and direct sim `JointCommand`, or can documentation keep it optional/deferred?
- Are gripper and camera examples release-blocking for the target course, or should they be optional support rows in the compatibility matrix?
- Should the first public tag be named by capability (`v0.1.0-sim`) or normal semver (`v0.1.0`) with profile labels in release notes?

## Artifacts

- Updated this S10 documentation/distribution strategy log: `logs/S10_docs_distribution.log.md`
- Updated S10 status in `MASTER_PLAN.md`
- Appended S11 handoff prompt to `PROMPTS.md`
- Prior planning logs used as source decisions:
  - `logs/S01_validate_assumptions.log.md`
  - `logs/S02_audit_community_packages.log.md`
  - `logs/S03_local_repo_analysis.log.md`
  - `logs/S04_bridge_architecture.log.md`
  - `logs/S05_simulation_architecture.log.md`
  - `logs/S06_moveit_ros2_control.log.md`
  - `logs/S07_dev_experience_tooling.log.md`
  - `logs/S08_package_mapping.log.md`
  - `logs/S09_risk_register.log.md`
