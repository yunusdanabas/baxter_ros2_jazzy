# Baxter ROS 2 Jazzy — Master Plan

## Overview

Planning workspace for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. Goal: make Baxter usable for our university (real hardware), other schools (real hardware), and users without hardware (strong simulation). All work is research and design only, no code implementation.

**Scope boundary:** Planning and design only. No code, no repository creation, no file changes outside this workspace. The deliverable is a comprehensive migration blueprint (S11) that can guide actual implementation later.

**Starting point:** Existing research report at `EXISTING_RESEARCH.md` (copy of original at `~/Yunus Portfolio/ROS1/catkin_ws/src/baxter_noetic/.cursor/plans/baxter_ros2_jazzy_research_3dea542e.plan.md`) is considered substantially complete. S01-S03 re-validate and deepen those findings rather than starting from scratch.

---

## Steps

### S01: Validate Research Assumptions

- **Status:** `completed`
- **Type:** Research (coarse)
- **Description:** Re-check key claims from the existing research report: Jazzy LTS timeline, ros1_bridge constraints on Ubuntu 24.04 Noble, Gazebo Classic EOL vs Harmonic status, MoveIt 2 Jazzy maturity, community repo activity and recency. Flag anything that changed since the research was done or that is weaker than assumed. Do not redo the full research, only validate and update.
- **Log:** `logs/S01_validate_assumptions.log.md`

### S02: Audit Community Packages

- **Status:** `completed`
- **Type:** Research (coarse)
- **Description:** Deep evaluation of all candidate community repos: CentraleNantesRobotics/baxter_common_ros2, baxter_legacy, RethoughtRobotics/BaxterSDK, baxter-zenoh, angysof16/BaxterMotionPlanning, bornaparo/baxter_moveit_config. Score each on: completeness (which packages are covered), maintenance (last commit, issue response), licensing (BSD/compatible?), Jazzy compatibility (actual tested version), code quality (structure, tests, docs), and adoption (stars, forks, known users). Decide per repo: adopt, fork and customize, reference only, or skip.
- **Log:** `logs/S02_audit_community_packages.log.md`

### S03: Local Repo Detailed Analysis

- **Status:** `completed`
- **Type:** Research (coarse)
- **Description:** Map every Noetic package's ROS 1 API surface: topics subscribed/published, services called/provided, actions used/provided, parameters, launch files, and dependencies. Use the read-only reference copy at `baxter_noetic_ref/` in this workspace. For each of the 17 packages, identify what must be preserved vs what can be simplified or dropped. Quantify approximate porting effort (low/medium/high) per package. Record the full list of custom messages, services, and any hidden dependencies.
- **Log:** `logs/S03_local_repo_analysis.log.md`

### S04: Bridge Architecture for Real Robot

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Define how a ROS 2 Jazzy workstation communicates with Baxter's ROS 1 robot-side software. Decide among: ECN baxter_bridge, RethoughtRobotics baxter-zenoh, custom bridge, or containerized ros1_bridge. Specify what runs where (robot, bridge machine, student laptop), what topics/services/actions cross the boundary, how students connect in practice, and networking topology. Address: action bridging limitations, QoS, latency concerns, enable/disable/estop safety flows.
- **Log:** `logs/S04_bridge_architecture.log.md`

### S05: Simulation Stack Architecture

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Define the Gazebo Harmonic + ros2_control simulation stack for Baxter. Decide whether to adopt/extend BaxterMotionPlanning or build new simulation packages from scratch. Specify: which ros2_control controllers, which Gazebo plugins, URDF/SDF approach for Harmonic, how the sim control API differs from hardware. Document the deliberate sim-vs-hardware API divergence and how students will understand it.
- **Log:** `logs/S05_simulation_architecture.log.md`

### S06: MoveIt 2 and ros2_control Integration

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Define the MoveIt 2 configuration architecture: how much of the existing SRDF/kinematics can be reused, controller integration for both sim and bridged hardware, dual-arm planning approach, gripper/hand integration. Choose between adopting BaxterMotionPlanning's MoveIt config or generating a new one. Specify the ros2_control controller layout for both sim and bridged hardware paths.
- **Log:** `logs/S06_moveit_ros2_control.log.md`

### S07: Developer Experience and Tooling

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Define the developer onboarding flow: devcontainer spec, .repos file strategy (which community packages to vendor and at what versions), colcon workspace layout, launch file structure and naming conventions, environment setup scripts, which 3-5 examples to prioritize, and the target "15-minute onboarding" experience for a new student. Also decide: repo name, README structure, hardware vs sim launch profiles.
- **Log:** `logs/S07_dev_experience_tooling.log.md`

### S08: Package Mapping and Dependency Graph

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Finalize the package-by-package mapping from Noetic to Jazzy: which Noetic packages become which ROS 2 packages, which are adopted from community repos (with specific repos identified in S02), which are new, and which are dropped. Produce a dependency graph. Decide colcon workspace layout and package naming. This step depends on S02, S03, S04, S05, S06, and S07 findings.
- **Log:** `logs/S08_package_mapping.log.md`

### S09: Risk Register and Mitigation Strategies

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Catalog all identified risks with likelihood (low/medium/high), impact (low/medium/high), and mitigation strategy. Cover: bridge latency for closed-loop control, QoS mismatches, maintenance burden and bus factor, licensing conflicts with community code, hardware failure or aging, sim/hardware behavioral divergence, community repo abandonment, Ubuntu/ROS version upgrade treadmill, Python 3.12 compatibility gaps, and university IT/networking constraints for Docker. Define acceptance criteria or go/no-go thresholds for each risk.
- **Log:** `logs/S09_risk_register.log.md`

### S10: Documentation and Distribution Strategy

- **Status:** `completed`
- **Type:** Design (fine)
- **Description:** Define: repo naming and discoverability, README structure and badges, hardware mode vs simulation mode documentation layout, contributing guide content, issue template design, compatibility matrix format, relationship documentation to the Noetic repo and community forks, and release/versioning approach. Decide whether to pursue rosdistro inclusion for message packages. Define the documentation audience (new student vs external lab vs potential contributor).
- **Log:** `logs/S10_docs_distribution.log.md`

### S11: Final Synthesis

- **Status:** `completed`
- **Type:** Synthesis
- **Description:** Produce a single comprehensive migration blueprint document consolidating all prior steps into an actionable reference. Include: final architecture diagram (text/mermaid), complete package list with sources, dependency graph, phased timeline with dependencies between phases, full risk register with mitigations, open questions requiring user decision, and go/no-go criteria. This document is the primary deliverable of the entire planning process and the handoff to actual implementation.
- **Log:** `logs/S11_final_synthesis.log.md`

---

## Dependencies Between Steps

```
S01 ──┐
S02 ──┤── S04 ──┐
S03 ──┘          ├── S07 ──┐
      S05 ───────┤         ├── S08 ── S09 ── S10 ── S11
      S06 ───────┘         ┘
```

- S01, S02, S03 can review existing research but should validate/deepen it
- S04 depends on S01, S02, S03 (needs validated assumptions, community options, local API surface)
- S05 and S06 are parallel-ish to S04 but should read S01-S03 logs first
- S07 depends on S04, S05, S06 (needs architecture decisions)
- S08 depends on S04, S05, S06, S07 (needs all design decisions)
- S09 depends on S08 (needs full package mapping to assess risks)
- S10 depends on S08 (needs package list to document)
- S11 depends on everything (synthesis)

Note: despite the dependency graph, steps execute strictly sequentially in step number order. Each agent reads prior logs and can incorporate findings from earlier steps even if those steps are not direct dependencies in the graph.
