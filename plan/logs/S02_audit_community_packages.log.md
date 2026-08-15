---
step: S02
title: "Audit Community Packages"
agent_date: 2026-06-17
status: completed
previous_steps: [S01]
---

# S02: Audit Community Packages

## Task

Audited candidate community Baxter ROS 2, bridge, simulation, MoveIt, and fallback ROS 1 container repositories for the Baxter ROS 2 Jazzy migration blueprint. This was a research/design step only. The output is intended to guide S04 bridge architecture, S05 simulation architecture, S06 MoveIt/ros2_control design, S07 workspace sourcing, and S08 package mapping.

Inputs read first:

- `EXISTING_RESEARCH.md`
- `logs/S01_validate_assumptions.log.md`
- `MASTER_PLAN.md`
- Read-only Noetic reference context: `baxter_noetic_ref/`

Audit sources were GitHub repository metadata, latest commit metadata, README/raw documentation, issue pages/search where available, and package tree summaries. No repositories were cloned and `baxter_noetic_ref/` was not modified.

## Findings

### Executive Summary

The practical community baseline is split across three areas:

| Area | Best Source | Planning Decision | Why |
|---|---|---:|---|
| Baxter ROS 2 messages, URDF, end-effector description, ECN bridge | `CentraleNantesRobotics/baxter_common_ros2` | Adopt | Most mature Baxter ROS 2 common stack; BSD-3-Clause; active through 2026-05-27; 21 stars/11 forks. |
| ROS 1 robot-side Python 3 packages and Debian workflow | `CentraleNantesRobotics/baxter_legacy` | Fork and customize | Provides Focal/Jammy/Noble Debian strategy and ROS 1 Python 3 robot-side packages, but repo license is not detected. |
| Hardware bridge alternative | `RethoughtRobotics/baxter-zenoh` | Fork and customize | New but relevant Docker/Zenoh bridge for Jazzy/Noble; low adoption means S04 must verify before relying on it. |
| Jazzy/Harmonic simulation + MoveIt2 | `angysof16/BaxterMotionPlanning` | Reference only | Best modern sim reference, but missing license blocks direct reuse until clarified. |
| Legacy/partial MoveIt wrappers | `bornaparo`, `JuanCSUCoder`, `maxilar20` repos | Skip or reference only | Stale, partial, unlicensed, or superseded by stronger repos. |
| ROS 1 Classic Gazebo fallback | `dabaspark/baxter_sdk_nvidia_any_os` | Reference only | Useful rescue path for legacy SDK/sim on modern Ubuntu, not a ROS 2 Jazzy architecture base. |

### Metadata Snapshot

Checked on 2026-06-17.

| Repo | Default Branch | Latest Commit | Stars | Forks | Issues | License | Primary Use |
|---|---|---|---:|---:|---|---|---|
| `CentraleNantesRobotics/baxter_common_ros2` | `master` | `678bfab`, 2026-05-27, `rosconsole dep for baxter_bridge` | 21 | 11 | 0 open, 3 closed | BSD-3-Clause | ROS 2 common packages and ECN bridge |
| `CentraleNantesRobotics/baxter_legacy` | `main` | `ba38dea`, 2025-04-10, `also copy setup files for obese` | 2 | 2 | 0 open, 0 closed | Not detected | ROS 1 Python 3 robot-side packages and debs |
| `CentraleNantesRobotics/baxter_gz` | `main` | `f96ff52`, 2026-01-20, `default to robot namespace` | 0 | 1 | 0 open, 0 closed | MIT | Gazebo Sim bridge using Baxter `JointCommand` topics |
| `Baxterminator/ECN_Baxter` | `master` | `9e5d44d`, 2023-09-20, merge PR #14 `Pre releases` | 2 | 0 | 0 open, 1 closed | MIT | ECN teaching wrappers, gripper/game nodes |
| `RethoughtRobotics/BaxterSDK` | `main` | `bcd50c1`, 2026-05-26, `update recording playback` | 1 | 0 | 0 open, 0 closed | MIT | New ROS 2 Baxter SDK and MoveIt2 integration |
| `RethoughtRobotics/baxter-zenoh` | `main` | `3b22a05`, 2026-06-03, `update dockerfile` | 0 | 0 | 0 open, 0 closed | MIT | Docker/Zenoh bridge from Baxter ROS 1 to ROS 2 |
| `RethoughtRobotics/ros1_bridge` | `kilted` | `8ad7b11`, 2026-06-03, custom-service mapping fix | 0 | 0 | 0 open, 0 closed | Apache-2.0 | Bridge fork used by `baxter-zenoh` |
| `angysof16/BaxterMotionPlanning` | `main` | `2a0ed74`, 2026-06-07, `/move_server correctly receiving goal, IK not processed correctly` | 6 | 0 | 0 open, 0 closed | Not detected | Jazzy + Harmonic + ros2_control + MoveIt2 sim |
| `bornaparo/baxter_moveit_config` | `master` | `58b3262`, 2025-02-05, `minor launch change` | 0 | 0 | 0 open, 0 closed | Not detected | Small MoveIt2/Ignition config |
| `JuanCSUCoder/baxter_interface_2` | `main` | `9d6f3bb`, 2023-06-01, `Feat: Update GIF` | 0 | 0 | 0 open, 0 closed | MIT | Partial Humble C++ wrapper |
| `maxilar20/baxter_moveit_ros2` | `main` | `1782869`, 2023-07-28, `Added table to xacro` | 0 | 0 | 0 open, 0 closed | Not detected | Galactic/bridge-era MoveIt2 attempt |
| `dabaspark/baxter_sdk_nvidia_any_os` | `main` | `90df761`, 2025-01-11, `Update README.md` | 7 | 2 | 0 open, 1 closed | Not detected | Dockerized ROS 1 Kinetic SDK + Classic Gazebo fallback |

### Detailed Repository Scores

Scores are 0-5. Decision labels: Adopt, Fork and customize, Reference only, Skip.

#### CentraleNantesRobotics/baxter_common_ros2

URL: https://github.com/CentraleNantesRobotics/baxter_common_ros2

Decision: **Adopt** with pinned SHA, likely `678bfabea8c895b4134951a6c076217a90b9e0e6` unless later integration testing picks a newer revision.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 4 | Covers `baxter_core_msgs`, `baxter_maintenance_msgs`, `baxter_description`, `rethink_ee_description`, and `baxter_bridge`; no full SDK/examples/sim/MoveIt2. |
| Maintenance | 4 | Active through 2026-05-27 with maintainer commits; 81 commits; 0 open issues and 3 closed issues. |
| Licensing | 5 | BSD-3-Clause detected, compatible with Baxter SDK-style reuse. |
| Jazzy compatibility | 4 | README says ROS 2 port and classical Baxter use heavily tested; S01 confirms recent use, but repo does not present a formal Jazzy release. |
| Code quality | 4 | Clear ROS 2 package split, bridge package, message/service mappings, README explains bridge behavior and multi-user publish arbitration. |
| Adoption | 4 | Highest adoption in this audit: 21 stars, 11 forks, referenced by ECN/bornaparo workflows and existing research. |

Influence on blueprint: Make this the default source for ROS 2 common packages and first bridge design candidate. S04 should inspect `baxter_bridge` topic allowlist/dynamic forwarding and multi-student arbitration. S08 should map Noetic `baxter_common/*` packages here rather than porting them from scratch.

#### CentraleNantesRobotics/baxter_legacy

URL: https://github.com/CentraleNantesRobotics/baxter_legacy

Decision: **Fork and customize** if a robot-side ROS 1 Debian/workstation path is selected.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 4 | Includes `baxter_common`, `baxter_interface`, `baxter_tools`, `control_msgs`, and `obese`; README provides Focal/Jammy/Noble Debian package links. |
| Maintenance | 3 | Recent enough for migration planning: 2025-04-10 push, but only 2 commits and no visible issue history. |
| Licensing | 2 | GitHub detects no repo license; likely inherited Baxter BSD content must be verified before redistribution. |
| Jazzy compatibility | 3 | Not a ROS 2 repo; Noble support matters indirectly through ROS 1 recompiled from source in `/opt/ros/obese`. |
| Code quality | 3 | Pragmatic packaging workflow and Python 3 port, but Debian generation is described as “a bit tricky” and requires compiled workspaces. |
| Adoption | 2 | 2 stars, 2 forks; important through ECN linkage, not broad public adoption. |

Influence on blueprint: Treat as robot-side packaging reference, not as student-facing ROS 2 code. S04 should decide whether to reuse ECN debs, fork Debian scripts, or prefer a container. S09 should flag the missing top-level license before any vendoring.

#### CentraleNantesRobotics/baxter_gz

URL: https://github.com/CentraleNantesRobotics/baxter_gz

Decision: **Reference only**.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 2 | Narrow package: custom bridge for joint command and range sensors plus `ros_gz_bridge` for standard topics; no full MoveIt2 stack. |
| Maintenance | 3 | Updated 2026-01-20, but small repo with low activity footprint. |
| Licensing | 5 | MIT detected. |
| Jazzy compatibility | 3 | Modern Gazebo/Ignition/Gazebo Sim direction, but README does not explicitly claim Jazzy/Harmonic. |
| Code quality | 3 | Clear narrow purpose and keeps real Baxter topic semantics; custom bridge increases maintenance burden. |
| Adoption | 1 | 0 stars, 1 fork, 0 issues; no evidence of broad use. |

Influence on blueprint: Use as S05 reference if preserving `/robot/limb/*/joint_command` in simulation becomes a requirement. Do not make it the default sim base unless S05 decides hardware-identical APIs matter more than standard `ros2_control`.

#### Baxterminator/ECN_Baxter

URL: https://github.com/Baxterminator/ECN_Baxter

Decision: **Reference only**.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 2 | Provides ECN gripper simplification and game/course nodes; not a core Baxter SDK, bridge, or sim replacement. |
| Maintenance | 2 | Last commit 2023-09-20; issue #1 closed; no recent Jazzy activity. |
| Licensing | 5 | MIT detected. |
| Jazzy compatibility | 1 | Topics include `ros2-humble`; no Jazzy/Noble/Harmonic claim. |
| Code quality | 3 | README is clear for gripper action abstraction and GameMaster, but package is course-specific. |
| Adoption | 2 | 2 stars, 0 forks; known ECN lab context but low public use. |

Influence on blueprint: Useful for S07 examples and optional high-level gripper API ideas. Do not vendor as core stack.

#### RethoughtRobotics/BaxterSDK

URL: https://github.com/RethoughtRobotics/BaxterSDK

Decision: **Reference only** for now; reconsider after hardware verification.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 4 | Advertises ROS 2 SDK, `baxter_interface`, `baxter_tools`, `baxter_examples`, MoveIt2 launch, docs, and joint trajectory action server. |
| Maintenance | 3 | Created 2026-05-18, 116 commits, last commit 2026-05-26, but no issue/PR history and only one public star. |
| Licensing | 5 | MIT detected. |
| Jazzy compatibility | 4 | README badges claim Jazzy/Kilted/Lyrical compatibility and MoveIt2; requires `baxter-zenoh`. |
| Code quality | 4 | Has docs, GitHub workflows, `.pre-commit-config.yaml`, `.ruff.toml`, `pyproject.toml`, and ReadTheDocs config. |
| Adoption | 1 | 1 star, 0 forks, 0 open/closed issues; too new to trust as base dependency. |

Influence on blueprint: S04/S06/S08 should mine API choices, examples, and MoveIt2 hardware launch patterns. Do not adopt directly until bridge behavior, action handling, and target robot compatibility are proven.

#### RethoughtRobotics/baxter-zenoh

URL: https://github.com/RethoughtRobotics/baxter-zenoh

Decision: **Fork and customize** as an S04 candidate, not default without a hardware smoke test.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 4 | Docker bridge, ROS 1/ROS 2 message workspaces, `bridge_topics.yaml`, NetworkManager profile, setup scripts, architecture doc, prebuilt image guidance. |
| Maintenance | 4 | Created 2026-05-12, 88 commits, last commit 2026-06-03; active but young. |
| Licensing | 5 | MIT detected. |
| Jazzy compatibility | 4 | README claims Ubuntu 24.04 plus Jazzy/Kilted/Lyrical; architecture uses ROS-O Noetic on Noble and `rmw_zenoh_cpp`. |
| Code quality | 3 | Good architecture doc and pinned container concept; uses 10 GB image, shell aliases, `sudo pkill -9 -f ros`, and Zenoh-specific assumptions that need hardening. |
| Adoption | 1 | 0 stars, 0 forks, 0 issues; no external validation found. |

Influence on blueprint: Strong bridge option for S04 because it directly targets Noble/Jazzy and high-rate topics. S04 must compare this against ECN `baxter_bridge`, especially for actions, services, cameras, IT/network policy, and whether Zenoh is acceptable in the university environment.

#### RethoughtRobotics/ros1_bridge

URL: https://github.com/RethoughtRobotics/ros1_bridge

Decision: **Reference only** as an implementation dependency of `baxter-zenoh`.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 2 | Fork of generic `ros1_bridge`, not Baxter-specific by itself; relevant custom service mapping patch only. |
| Maintenance | 3 | Last commit 2026-06-03; default branch `kilted`; no public issue history. |
| Licensing | 5 | Apache-2.0 detected, matching upstream ROS 2 style. |
| Jazzy compatibility | 2 | Default branch is `kilted`; `baxter-zenoh` claims Jazzy compatibility, but this repo itself is not a standalone Jazzy package story. |
| Code quality | 3 | Based on upstream bridge plus patch from unmerged upstream PR #347; custom fork risk remains. |
| Adoption | 1 | 0 stars, 0 forks; no independent consumers except `baxter-zenoh` found. |

Influence on blueprint: Do not depend on this directly in S08. If S04 chooses `baxter-zenoh`, pin it transitively via the bridge container and document the forked-bridge risk.

#### angysof16/BaxterMotionPlanning

URL: https://github.com/angysof16/BaxterMotionPlanning

Decision: **Reference only** until a license is added; likely S05/S06 starting point for architecture.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 4 | Contains `gazebo_baxter`, `baxter_description`, `baxter_moveit_config`, `baxter_arm_action`, sensors, ros2_control controllers, and MoveIt2 demos. |
| Maintenance | 4 | Created 2026-03-28, 26 commits, last commit 2026-06-07; active current Jazzy/Harmonic work. |
| Licensing | 0 | No license detected; cannot be vendored or copied safely. |
| Jazzy compatibility | 5 | README explicitly targets ROS 2 Jazzy, Gazebo Harmonic, `ros-jazzy-gz-ros2-control`, and MoveIt2. |
| Code quality | 3 | Clear README, package layout, launch instructions, troubleshooting, and controller checks; latest commit says IK not processed correctly for `/move_server`. |
| Adoption | 2 | 6 stars, 0 forks, 0 issues; strongest sim candidate but still low adoption. |

Influence on blueprint: S05 should use this as the primary sim architecture reference, not direct source. S06 should compare its MoveIt2 SRDF/controllers with regenerated MoveIt2 config. S09 must list missing license and current IK uncertainty.

#### bornaparo/baxter_moveit_config

URL: https://github.com/bornaparo/baxter_moveit_config

Decision: **Skip** as direct dependency; keep one note as historical reference.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 2 | Small MoveIt2/Gazebo Ignition config only; depends on `bornaparo/baxter_common_ros2` fork. |
| Maintenance | 2 | Only 2 commits; last commit 2025-02-05. |
| Licensing | 0 | No license detected. |
| Jazzy compatibility | 2 | README says ROS 2 and Gazebo Ignition, not Jazzy/Harmonic; dependency fork was modified for Ignition. |
| Code quality | 2 | Simple launch/config package, credits ROS 1 config; no tests/CI/docs beyond usage commands. |
| Adoption | 0 | 0 stars, 0 forks, 0 open/closed issues. |

Influence on blueprint: Superseded by BaxterMotionPlanning for S05/S06. Do not vendor unlicensed content.

Related discovered repo: `bornaparo/baxter_common_ros2` is a fork of ECN common, 0 stars/0 forks, latest visible commit `7cf730b` on 2025-02-05. It exists mainly to support `bornaparo/baxter_moveit_config`; prefer upstream ECN plus explicit local patches over this fork.

#### JuanCSUCoder/baxter_interface_2

URL: https://github.com/JuanCSUCoder/baxter_interface_2

Decision: **Skip**.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 1 | Partial C++ SDK wrapper example around MoveIt; no bridge/common/sim/package coverage. |
| Maintenance | 1 | Last commit 2023-06-01; no recent activity. |
| Licensing | 5 | MIT detected. |
| Jazzy compatibility | 1 | README targets ROS 2 Humble only. |
| Code quality | 2 | Basic C++ example and GIFs; too thin for architecture reuse. |
| Adoption | 0 | 0 stars, 0 forks, 0 issues. |

Influence on blueprint: Ignore for S08. If a future C++ facade is needed, build a fresh minimal wrapper from the final API mapping.

#### maxilar20/baxter_moveit_ros2

URL: https://github.com/maxilar20/baxter_moveit_ros2

Decision: **Skip**.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 2 | Contains bridge-era instructions for a controller and MoveIt launch; not a full stack. |
| Maintenance | 1 | Last commit 2023-07-28; stale. |
| Licensing | 0 | No license detected. |
| Jazzy compatibility | 0 | README uses ROS 2 Galactic and a Noetic/Galactic bridge container. |
| Code quality | 1 | Sparse terminal-command README; no clear package maturity. |
| Adoption | 0 | 0 stars, 0 forks, 0 open/closed issues. |

Influence on blueprint: Historical only. Do not use for S04/S06 except as evidence that old Galactic bridge workflows are superseded.

#### dabaspark/baxter_sdk_nvidia_any_os

URL: https://github.com/dabaspark/baxter_sdk_nvidia_any_os

Decision: **Reference only**.

| Criterion | Score | Rationale |
|---|---:|---|
| Completeness | 3 | Dockerized ROS Kinetic + Baxter SDK + Classic Gazebo/RViz with NVIDIA/X11 support; good fallback, no ROS 2. |
| Maintenance | 2 | Created 2025-01-09, last commit 2025-01-11; updated repo metadata in 2026 but no recent commits. |
| Licensing | 0 | No license detected. |
| Jazzy compatibility | 1 | Runs on Ubuntu 24.04 hosts but internally uses Ubuntu 16.04, ROS Kinetic, Gazebo 7. |
| Code quality | 2 | Practical Docker instructions and prebuilt image, but legacy stack and no CI/license. |
| Adoption | 2 | 7 stars, 2 forks, 1 closed issue/demo; highest fallback interest after ECN and BaxterMotionPlanning. |

Influence on blueprint: Useful in S09 risk mitigation and S10 docs as an emergency legacy simulation/hardware fallback. It should not shape the Jazzy-native package graph.

### Additional Active/Relevant Repos Found

No stronger active Baxter ROS 2/Jazzy/Harmonic repository was found beyond the requested audit list. GitHub search was partially rate-limited during broad searches, but repository-specific checks and known S01 candidates covered the active ecosystem. The only additional relevant repo identified was `bornaparo/baxter_common_ros2`, a low-adoption fork used by `bornaparo/baxter_moveit_config`; it should not displace upstream ECN common packages.

### Cross-Cutting Observations

- **Licensing is the biggest blocker for sim reuse.** `BaxterMotionPlanning`, `bornaparo/baxter_moveit_config`, `baxter_legacy`, `maxilar20/baxter_moveit_ros2`, and `dabaspark/baxter_sdk_nvidia_any_os` have no GitHub-detected license. Treat them as reference-only unless license is confirmed or added.
- **Adoption is low across the board.** Even the strongest repo, `baxter_common_ros2`, has only 21 stars and 11 forks. Plan for project ownership, pinned SHAs, and verification tests rather than relying on upstream support.
- **There are two bridge philosophies.** ECN `baxter_bridge` is Baxter-specific and lab-tested; Rethought `baxter-zenoh` uses Docker, ROS-O Noetic on Noble, `ros1_bridge` parameter mode, and Zenoh for high-rate topics. S04 should evaluate both with the target robot.
- **There are two simulation philosophies.** `BaxterMotionPlanning` follows standard ROS 2 manipulator practice with `joint_trajectory_controller` and MoveIt2; `baxter_gz` tries to preserve Baxter `JointCommand` semantics. Default should be standard ros2_control unless S05 decides homework/API parity requires `JointCommand`.
- **MoveIt2 work should be regenerated or carefully diffed.** Existing community MoveIt2 configs are useful references, but no repo has enough license/adoption/test evidence to make its config canonical without validation.

## Decisions

1. **Adopt `CentraleNantesRobotics/baxter_common_ros2`** as the likely base dependency for ROS 2 Baxter messages, descriptions, end-effector descriptions, and ECN bridge evaluation. Pin to a known SHA in S07/S08.
2. **Fork/customize `CentraleNantesRobotics/baxter_legacy` only if ECN robot-side debs/scripts are selected** for the hardware path. Before reuse, verify license inheritance from original Baxter SDK packages.
3. **Evaluate both ECN `baxter_bridge` and Rethought `baxter-zenoh` in S04.** Do not assume upstream `ros1_bridge` on Jazzy/Noble works; both candidates are workarounds with different operational risks.
4. **Use `angysof16/BaxterMotionPlanning` as S05/S06 reference only** until license is clarified. Its Jazzy/Harmonic/MoveIt2 structure is valuable; copying files is not safe without permission/license.
5. **Skip stale/partial wrappers for direct reuse**: `JuanCSUCoder/baxter_interface_2`, `maxilar20/baxter_moveit_ros2`, and `bornaparo/baxter_moveit_config` should not enter the core package graph.
6. **Keep `dabaspark/baxter_sdk_nvidia_any_os` as a documented fallback/reference** for legacy ROS 1 Classic Gazebo workflows on modern Ubuntu, not as part of the ROS 2 Jazzy architecture.
7. **Downstream agents should prefer thin integration over wholesale vendoring.** The shortest safe route is pinned dependencies plus local glue/docs; direct source copying from low-adoption or unlicensed repos should be avoided.

## Open Questions

- Can `CentraleNantesRobotics/baxter_legacy` be redistributed under the original Baxter BSD-style license, or does the missing top-level license block vendoring?
- Will the target university allow Zenoh and Docker host/network setup required by `RethoughtRobotics/baxter-zenoh`?
- Does `baxter-zenoh` bridge enough action/service semantics for `FollowJointTrajectory`, IK, enable/reset, grippers, cameras, and head display on the target robot?
- Can `angysof16/BaxterMotionPlanning` receive an explicit open-source license, or must S05/S06 regenerate equivalent sim/MoveIt files from first principles?
- Is standard `ros2_control`/MoveIt2 simulation acceptable for courses, or do assignments require Baxter-native `JointCommand` semantics in sim?
- Which bridge candidate has better latency and stability for high-rate joint states and camera streams on the target network?
- Should S07 include both ECN bridge and Rethought Zenoh bridge in `.repos`, or one primary path plus a documented experimental alternative?

## Artifacts

- Updated this S02 audit log: `logs/S02_audit_community_packages.log.md`
- Updated S02 status in `MASTER_PLAN.md`
- Appended S03 handoff prompt to `PROMPTS.md`
- Read-only reference inspected for context: `baxter_noetic_ref/`
- Primary audited repository URLs:
  - https://github.com/CentraleNantesRobotics/baxter_common_ros2
  - https://github.com/CentraleNantesRobotics/baxter_legacy
  - https://github.com/CentraleNantesRobotics/baxter_gz
  - https://github.com/Baxterminator/ECN_Baxter
  - https://github.com/RethoughtRobotics/BaxterSDK
  - https://github.com/RethoughtRobotics/baxter-zenoh
  - https://github.com/RethoughtRobotics/ros1_bridge
  - https://github.com/angysof16/BaxterMotionPlanning
  - https://github.com/bornaparo/baxter_moveit_config
  - https://github.com/bornaparo/baxter_common_ros2
  - https://github.com/JuanCSUCoder/baxter_interface_2
  - https://github.com/maxilar20/baxter_moveit_ros2
  - https://github.com/dabaspark/baxter_sdk_nvidia_any_os
