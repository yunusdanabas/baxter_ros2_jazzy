---
step: S09
title: "Risk Register and Mitigation Strategies"
agent_date: 2026-06-18
status: completed
previous_steps: [S08]
---

# S09: Risk Register and Mitigation Strategies

## Task

Created a practical risk register and mitigation strategy for the future `baxter_ros2_jazzy` workspace. This is a planning-only step. No ROS 2 code, launch files, package manifests, or repository files were implemented.

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
- `MASTER_PLAN.md`

No changes were made to `baxter_noetic_ref/`.

## Findings

### Executive Summary

The highest project risks are not package layout risks. They are the hardware bridge boundary, hardware safety, licensing, and long-term maintenance. The safest first release should be honest about profiles:

| Profile | Recommended Release Label | Gate Summary |
|---|---|---|
| Core/model | Supported after local/CI checks | Build, model load, meshes, legacy joint names. |
| Sim | Supported after local/CI or documented manual smoke | Headless Gazebo Harmonic launch, Baxter spawn, active arm controllers, all arm joint states. |
| MoveIt sim | Supported after executable sim smoke | SRDF and KDL load, one-arm plan, tiny sim execution. |
| Sim compatibility | Optional supported only if implemented | `/robot/joint_states` and `/robot/state` publish; optional `JointCommand` shim rejects unsafe modes. |
| Hardware bridge | Supported as non-motion bridge only after target-robot smoke | State, joint states, IK/camera/gripper services, and both hardware action names visible without enable or motion. |
| Hardware motion | Supervised/experimental until proven on target robot | One tiny low-speed trajectory per advertised arm, valid feedback, cancel/hold behavior, no unsafe robot state. |
| Zenoh fallback | Experimental only | IT approval, restricted YAML, measured reason to prefer it over ECN bridge. |

Risk scale: likelihood and impact are `Low`, `Medium`, or `High`. Owner/profile names indicate who must own the mitigation in the future implementation, not a person assignment.

### Hardware Bridge Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| HB-01 | ECN `baxter_bridge` or its ROS 1 support dependencies cannot be installed reproducibly on the selected Noble/Jazzy bridge host. | Medium | High | Hardware bridge | Keep bridge-host setup separate from default student devcontainer; pin `CentraleNantesRobotics/baxter_common_ros2` to `678bfabea8c895b4134951a6c076217a90b9e0e6`; document ROS 1 dependency source; prepare a containerized bridge-host option if native install fails. | Clean bridge-host install rehearsal; `colcon build` for hardware profile; launch ECN bridge; verify bridge discovery topics/services. | No hardware profile release if ECN bridge and required ROS 1 deps cannot build/start from documented steps on one clean bridge host. |
| HB-02 | Target Baxter firmware or robot-side ROS 1 graph differs from ECN assumptions. | Medium | High | Hardware bridge | Treat robot firmware/distro as a validation item; run non-motion discovery before writing motion docs; keep Noetic reference names as expected contract but document target-specific deviations. | `ros2 topic list`, `/robot/state`, `/robot/joint_states`, camera services, IK services, gripper topics, and ECN bridge reports on the actual robot. | No hardware docs beyond "unverified" if `/robot/state` and `/robot/joint_states` do not match expected types/names. |
| HB-03 | Minimum allowlist misses required topics/services for camera, IK, gripper, endpoint state, or action shims. | Medium | Medium | Hardware bridge | Start from S04 minimum allowlist; add only measured missing items; keep maintenance/update/tare topics excluded by default. | `hardware_bridge_smoke` checks for `/robot/state`, `/robot/joint_states`, `ExternalTools/{left,right}/PositionKinematicsNode/IKService`, `/cameras/list`, `/cameras/open`, `/cameras/close`, gripper state/properties, and both action names. | No hardware bridge support if required non-motion smoke checks fail on the target robot. |
| HB-04 | ECN publisher arbitration does not behave as expected for multi-student labs. | Medium | High | Hardware safety / lab ops | Use one bridge host per Baxter; keep `allow_multiple:=False`; require `/bridge_auth` and `/bridge_force` procedure in instructor docs; use one active command owner per limb. | Two-client arbitration drill with read-only clients and one motion owner; verify bridge publisher display and forced owner behavior. | No multi-student hardware lab if arbitration cannot identify and restrict command publishers. |
| HB-05 | Broad bridge allowlist or fallback `bridge_topics.yaml` exposes unsafe maintenance, homing, stop, suppression, or high-bandwidth topics to beginners. | Medium | High | Hardware bridge / docs | Default to restricted allowlist; keep Rethought `baxter-zenoh` YAML behind `experimental_zenoh`; explicitly exclude maintenance/update/tare/calibration, raw suppression, and all camera streams by default. | Review committed bridge YAML; compare against S04 excluded list; run `ros2 topic list` on hardware profile. | No student hardware release if default profile exposes maintenance/admin topics or every camera stream without an instructor-only flag. |
| HB-06 | Bridge topic/service gaps are hidden because tests only check topic names, not message flow. | Medium | Medium | Hardware bridge | Smoke checks must read one message or complete one service call where safe, not only list names. | `ros2 topic echo --once /robot/state`, `/robot/joint_states`; service availability plus harmless `/cameras/list`; action server discovery without goal. | No-go if names appear but state/joint messages do not arrive within documented timeout on wired bridge host. |

### Hardware Safety Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| HS-01 | Launch files or examples auto-enable, reset, stop, or otherwise normalize raw safety topic publishing. | Medium | High | Hardware safety / docs | `hardware_bridge.launch.py` and `hardware_moveit.launch.py` must never enable automatically; provide `hardware_enable_status` tool that prints `ready`, `enabled`, `stopped`, `error`, `estop_button`, and `estop_source`; require explicit operator confirmation. | Static review of launch/examples/docs; manual launch test with robot disabled; confirm no publish to `/robot/set_super_enable` on startup. | No hardware release if any default launch auto-enables or auto-resets the robot. |
| HS-02 | Stale commands replay after bridge, node, or DDS restart. | Medium | High | Hardware safety / QoS | Commands use reliable volatile keep-last-1 QoS only; no transient-local command topics; action shims send speed ratio/timeout on startup and hold current position on cancel/failure. | Restart bridge/action shim while monitoring command topics; inspect QoS config; verify no latched motion command is replayed. | No hardware motion if stale command can move a limb after restart. |
| HS-03 | Action-shim cancellation or failure calls `/robot/set_super_stop` routinely, drops the arm, or keeps streaming stale trajectory points. | Medium | High | `baxter_hardware_bridge` | Cancel/failure must send a hold-position `JointCommand` and stop command streaming; reserve `/robot/set_super_stop` for explicit operator stop. | Supervised cancel test on sim shim first, then hardware tiny trajectory; inspect final command behavior. | No hardware motion support if cancel does not hold safely or if routine cancel triggers stop/reset behavior. |
| HS-04 | E-stop, stopped, error, or not-ready state is not enforced by action shims and tools. | Medium | High | Hardware safety | Every hardware motion path checks `/robot/state` before accepting goals and during execution; reject unsafe state with clear error. | Force disabled/stopped/error/e-stop-visible states where possible; send dry-run or tiny goal; verify rejection. | No hardware motion if action shims accept goals when `ready=false`, `enabled=false`, `stopped=true`, `error=true`, or e-stop is active. |
| HS-05 | Raw `JointCommand` exposure enables torque, raw-position, or velocity labs accidentally. | Medium | High | Hardware safety / examples | Keep ECN `SAFE_CMD=True`; beginner examples use actions or safe position commands only; direct `JointCommand` documented as advanced/instructor profile. | Topic allowlist/config review; run unsafe-mode publish in a controlled no-motion state and verify rejection or no forwarding if supported by bridge/shim. | No beginner hardware docs if torque/raw-position examples or unrestricted `JointCommand` publishing are shown. |
| HS-06 | Speed ratio or command timeout defaults are too permissive. | Medium | High | `baxter_hardware_bridge` | Action shims and hardware examples set low speed ratio and finite command timeout before motion; document conservative defaults. | Hardware tiny trajectory logs; topic echo for `/robot/limb/{side}/set_speed_ratio` and `/robot/limb/{side}/joint_command_timeout`. | No hardware motion if speed ratio/timeout are not explicitly set by the motion path. |
| HS-07 | Multi-student command ownership is unclear during labs. | Medium | High | Lab ops / docs | One bridge host, one `ROS_DOMAIN_ID` per robot bench, instructor-controlled reservations, no per-student motion bridges. | Lab dry run with two clients; verify only intended user can command each limb. | No multi-student motion lab if command ownership cannot be demonstrated before class. |

### Motion And Action Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| MA-01 | ROS 2 `FollowJointTrajectory` action shim timing, feedback, or result semantics are wrong. | Medium | High | `baxter_hardware_bridge` | Model shim behavior after Noetic `joint_trajectory_action_server.py`; validate trajectory timestamps, feedback from `/robot/joint_states`, and result codes; keep first trajectories tiny and position-only. | Unit/self-check in implementation, sim dry run, hardware action availability check, supervised tiny trajectory. | No hardware motion if feedback is missing, goal completion is false-positive, or timing causes jumps. |
| MA-02 | Joint-name validation accepts renamed, partial, duplicate, or cross-arm joints. | Medium | High | Hardware bridge / MoveIt | Require exact 7-joint set per limb: `left_s0`...`left_w2` or `right_s0`...`right_w2`; reject partial goals. | Dry-run action validation; MoveIt controller YAML review; malformed-goal tests. | No hardware or sim compatibility motion if invalid joint lists are accepted. |
| MA-03 | MoveIt hardware controller YAML does not work with `/robot/limb/{side}` action names. | Medium | Medium | `baxter_moveit_config` | Keep canonical hardware actions as `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory`; add `/left_arm_controller` aliases only if MoveIt 2 rejects legacy-style entries. | Launch `hardware_moveit.launch.py` non-motion; verify MoveIt detects both action servers without sending goals. | No hardware MoveIt docs if MoveIt cannot discover both action shims or requires undocumented aliases. |
| MA-04 | Hardware bridge latency is too high for closed-loop or frequent replanning assumptions. | Medium | Medium | Hardware bridge / docs | First release uses planned low-speed trajectories only; defer Servo/teleop/closed-loop control; prefer wired bridge host. | Measure action feedback latency and `/robot/joint_states` rate during non-motion and tiny trajectory tests. | No Servo, teleop, or closed-loop hardware claims unless measured latency supports them. |
| MA-05 | Hardware motion acceptance is ambiguous, causing S10/S11 to overclaim. | High | High | Release management / docs | Separate "hardware bridge non-motion supported" from "hardware motion supervised/validated"; require tiny trajectory gate for motion claims. | Release checklist review; README/profile wording review. | No public hardware motion support claim unless supervised tiny trajectory gate passes on target robot. |

### QoS And Network Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| QN-01 | DDS discovery is blocked by university multicast/firewall policy. | High | High | Lab ops / docs | Official hardware path should prefer SSH/devcontainer on bridge host or controlled lab VLAN; document DDS firewall/static peer/discovery-server options only after IT approval. | Student laptop to bridge-host discovery test; `ros2 topic list` and action discovery across intended network. | No remote-laptop hardware workflow if discovery fails on the target network. |
| QN-02 | Camera streams and high-rate `/robot/joint_states` overload Wi-Fi or bridge host. | Medium | Medium | Hardware bridge / camera docs | Bridge one camera on demand; set low resolution/FPS; prefer wired network; run vision on bridge host for heavy labs; keep all-camera streaming out of default profile. | `ros2 topic hz`, bandwidth monitoring, frame-drop check while `/robot/joint_states` remains stable. | No camera support claim if enabling one stream destabilizes joint states or action feedback. |
| QN-03 | `/tf_static` durability is wrong and late RViz/MoveIt subscribers miss static transforms. | Medium | Medium | Core/model / MoveIt | Use reliable transient-local keep-last for `/tf_static`; rely on `robot_state_publisher` from ROS 2 description. | Start RViz after robot_state_publisher; verify full TF tree without restarting publishers. | No MoveIt/model support if late subscribers miss static frames. |
| QN-04 | QoS mismatch causes silent data loss for state, commands, cameras, or services. | Medium | High | All profiles | Define profile QoS: reliable volatile for state/commands/services, best-effort shallow for cameras, transient-local only for `/tf_static`; document overrides. | `ros2 topic info --verbose`; smoke checks consume real messages; integration tests with chosen RMW. | No supported profile if required smoke messages/services are intermittently invisible due to QoS. |
| QN-05 | Docker host networking or permissions block sim or fallback Zenoh workflows. | Medium | Medium | Dev experience / experimental | Default sim must work headless without hardware/Zenoh; document Docker networking only where required; keep Zenoh optional. | Run default devcontainer sim smoke; separately test experimental Zenoh container with IT-approved host networking. | No default dependency on Docker host networking for ordinary CI or 15-minute sim path. |
| QN-06 | ROS domains collide across multiple robots or courses. | Medium | Medium | Lab ops / docs | Assign one `ROS_DOMAIN_ID` per robot bench; include `.env.example`; document domain isolation. | Two-bench discovery test; verify each laptop sees only intended bridge. | No multi-robot lab if cross-bench topics/actions are visible. |

### Simulation Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| SIM-01 | Gazebo Harmonic is unstable or flaky in CI. | Medium | Medium | Sim / CI | Keep model and MoveIt fake checks in mandatory CI; make headless Gazebo required only if runner proves stable; otherwise document as manual or allowed-flaky. | Repeated `smoke_sim.launch.py headless:=true` runs on chosen CI runner. | Do not block all releases on flaky Gazebo CI; do not advertise CI sim gate unless it passes reliably. |
| SIM-02 | Meshes or package URIs from ECN description fail to resolve. | Medium | High | Core/model / sim | Core/model gate includes mesh resolution; patch locally only in licensed files/overlays; keep `baxter_description.launch.py` smoke. | Launch robot_state_publisher/RViz; inspect logs for missing meshes; check installed package share paths. | No core/model support if meshes or `robot_description` fail to load. |
| SIM-03 | ECN description uses different joint/link names than legacy Baxter names. | Medium | High | Core/model / MoveIt / sim | Verify `left_s0`...`left_w2` and `right_s0`...`right_w2`; patch or fork licensed description if needed; reject accidental renamed names from unlicensed references. | Xacro/model inspection; `/joint_states`; MoveIt SRDF/controller YAML joint-name comparison. | No sim/MoveIt/hardware release if legacy arm joint names are absent or inconsistent. |
| SIM-04 | `gz_ros2_control` controller startup ordering is unreliable. | Medium | High | `baxter_gz_sim` | Launch must wait for `/controller_manager`, spawn `joint_state_broadcaster` first, then arm controllers, then MoveIt. | `ros2 control list_controllers`; headless launch logs; tiny trajectory after startup. | No sim support if `left_arm_controller` and `right_arm_controller` are not active deterministically. |
| SIM-05 | Controller tuning or physics causes oscillation, jumps, or unrealistic behavior. | Medium | Medium | Sim | Start with position interfaces and tiny trajectory smoke; avoid effort/velocity controllers in first release; document sim as planning/teaching fidelity, not dynamics validation. | Tiny trajectory execution; return-to-neutral test; visual/RViz inspection. | No sim motion support if tiny trajectories produce unstable or unsafe-looking motion. |
| SIM-06 | Gripper/head optionality confuses users. | Medium | Low | Sim / docs | Mark grippers/head optional; first acceptance focuses on arms; enable gripper/head examples only after model/hardware confirmation. | Launch variants with grippers enabled/disabled; docs review. | No gripper/head support claim unless corresponding controllers/topics pass smoke checks. |
| SIM-07 | Gazebo camera sensors are fragile or resource-heavy. | Medium | Low | Sim / camera docs | Keep camera optional; one head camera only for first examples; do not block core sim on camera. | Optional camera launch publishes one frame and camera info. | No camera demo claim if one-frame smoke fails; core sim may still release. |
| SIM-08 | Sim and hardware APIs diverge enough to confuse students. | High | Medium | Docs / examples | Document two personalities: standard sim `ros2_control` actions and hardware Baxter `/robot/*`; provide optional `baxter_sim_compat` only when needed. | Docs/tutorial review; examples use profile-specific action names. | No single "runs unchanged everywhere" claim unless `sim_compat` explicitly supports that workflow. |

### MoveIt Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| MV-01 | Regenerated SRDF collision matrix disables real collisions or overblocks valid motion. | Medium | High | `baxter_moveit_config` | Generate from final ROS 2 URDF; compare conceptually to Noetic; do not blanket-disable left/right arm collisions or pedestal collisions; sample self-collision in RViz. | MoveIt Setup Assistant output review; RViz planning scene; sampled planning for neutral/tiny deltas. | No MoveIt support if SRDF permits obvious self-collision or blocks neutral one-arm planning. |
| MV-02 | KDL IK fails for Baxter's 7-DOF arms or is too slow. | Medium | Medium | MoveIt | Start with KDL and conservative timeout; add TRAC-IK only if smoke tests fail; keep IKFast out of first release. | Plan pose/joint targets for `left_arm` and `right_arm`; log IK failures. | No one-arm MoveIt support if KDL cannot plan tiny/neutral goals reliably. |
| MV-03 | Joint limits are stale, mismatched, or too aggressive. | Medium | High | MoveIt / safety | Derive from final URDF and Noetic reference; use conservative velocity/acceleration; hardware action shims also enforce low speed ratio. | Compare URDF, `joint_limits.yaml`, controller YAML; tiny plan execution. | No hardware MoveIt motion if limits allow abrupt or out-of-range goals. |
| MV-04 | `both_arms` group overpromises synchronized dual-arm execution. | High | Medium | MoveIt / docs | Include `both_arms` for planning-scene completeness but mark experimental; no acceptance test requires synchronized dual-arm execution. | Docs review; MoveIt launch/controller config lacks unsupported `both_arms_controller` unless implemented. | No dual-arm execution claim without a real combined or coordinated controller test. |
| MV-05 | RViz/fake-controller success is mistaken for executable sim success. | Medium | Medium | Docs / CI | Separate `moveit_rviz.launch.py` model-only from `sim_moveit.launch.py` executable profile; release gates distinguish plan-only and execute tests. | Run both fake/model and sim execute smoke; README labels. | No sim MoveIt support unless tiny execution through `/left_arm_controller/follow_joint_trajectory` or `/right_arm_controller/follow_joint_trajectory` succeeds. |
| MV-06 | Deferred gripper/grasping expectations become hidden scope creep. | Medium | Medium | MoveIt / docs | Include gripper geometry if modeled; defer grasp pipeline, contact tuning, suction/pneumatic realism, and object pick-place. | Docs/examples review; no first-release tutorial claims full grasping. | No pick-place/grasping claim unless separate gripper/contact/perception gates are created. |

### Dependency And Package Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| DP-01 | All community repos have low adoption, including the default ECN source. | High | Medium | Maintainers | Pin SHAs, keep local graph small, add smoke tests, do not rely on upstream support for release quality. | Periodic metadata review; CI/smoke tests catch regressions. | No release should depend on untested floating upstream branches. |
| DP-02 | Pinned SHA drifts behind upstream fixes or breaks with Jazzy updates. | Medium | Medium | Maintainers | Manual dependency review cadence; update pins only after build/model/sim/MoveIt smoke passes. | Scheduled pin review; compare upstream commits; run full non-hardware smoke. | No pin update without passing gates and changelog note. |
| DP-03 | `baxter_common_ros2` package/API gaps require local patches. | Medium | High | Core/model / hardware | Prefer small local overlays or a project fork only for verified gaps; upstream contribution if practical; keep patch list documented. | Build and API smoke; compare S03 required interfaces against imported packages. | No core/hardware release if required message/service types or descriptions are missing. |
| DP-04 | Python 3.12 exposes old SDK assumptions in rewritten examples/shims. | Medium | Medium | `baxter_hardware_bridge` / `baxter_examples` | Rewrite minimal ROS 2 code instead of porting broad Noetic scripts; use `ruff`/unit smoke for local Python. | `colcon test`; import/run examples under Jazzy Python 3.12. | No example release if curated examples fail import/run on Python 3.12. |
| DP-05 | ROS/Gazebo/MoveIt Jazzy package churn changes APIs or apt availability. | Medium | Medium | CI / maintainers | Use Jazzy LTS apt packages; pin external source repos; keep CI on Noble/Jazzy; document tested versions. | CI build; rosdep install dry run; compatibility matrix update. | No release tag if documented dependency install fails from a clean Noble/Jazzy environment. |
| DP-06 | `rosdep` or apt keys/packages are unavailable in labs. | Medium | Medium | Dev experience | Provide apt/rosdep dependency group docs; keep default dependencies standard Jazzy/Harmonic packages; avoid exotic defaults. | Fresh devcontainer build; fresh native install rehearsal. | No 15-minute sim path if standard dependencies cannot install from documented sources. |
| DP-07 | Local package split grows too large and hard to maintain. | Medium | Medium | Package owners | Keep first-release local packages to `baxter_bringup`, `baxter_gz_sim`, `baxter_moveit_config`, `baxter_hardware_bridge`, `baxter_examples`; keep `baxter_sim_compat` optional; no default `baxter_smoke_tests`. | Package graph review before implementation milestones. | No new package unless it owns a distinct runtime boundary or the existing package becomes clearly bulky. |

### Licensing Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| LIC-01 | `angysof16/BaxterMotionPlanning` has no detected license but is tempting to copy for sim/MoveIt. | High | High | Licensing / sim / MoveIt | Use as reference only; regenerate `baxter_moveit_config`; create local sim files from licensed descriptions and standard docs. | `.repos` review; diff/source review; license scan. | No copied config/code or default `.repos` entry unless an explicit compatible license is added. |
| LIC-02 | `CentraleNantesRobotics/baxter_legacy` missing top-level license blocks redistribution/import. | Medium | High | Hardware bridge / licensing | Treat as bridge-host packaging reference only until license inheritance is verified; keep out of default student `.repos`. | License review; maintainer confirmation; source headers. | No default import/vendor of `baxter_legacy` without verified compatible license. |
| LIC-03 | `dabaspark/baxter_sdk_nvidia_any_os` is unlicensed and legacy-only. | Medium | Medium | Docs / fallback | Reference only as emergency legacy idea; do not import, vendor, or recommend as project dependency. | `.repos` and docs review. | No default or optional project `.repos` entry without license. |
| LIC-04 | Stale unlicensed MoveIt repos are accidentally reused. | Medium | Medium | MoveIt / licensing | Skip `bornaparo/baxter_moveit_config`, `maxilar20/baxter_moveit_ros2`, and similar repos for direct reuse. | Source attribution and `.repos` review. | No copied MoveIt files from unlicensed/stale repos. |
| LIC-05 | Documentation accidentally recommends vendoring/copying unlicensed community code. | Medium | High | Docs / release | S10 must label unlicensed repos as reference-only and provide licensed alternatives/regeneration guidance. | Documentation review before release. | No release docs that tell users to import or copy unlicensed repos by default. |

### Documentation And Distribution Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| DOC-01 | Users confuse sim support with safe real-hardware support. | High | High | Docs | README mode selector must separate `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, and `experimental_zenoh`; hardware docs start with safety and supervised-use language. | Docs review with a new user; check all tutorials state profile. | No public README release if hardware profile can be mistaken for plug-and-play safe motion. |
| DOC-02 | Bridge-host setup is unclear, leading to unsafe per-student bridges or broken networking. | High | High | Docs / lab ops | Provide `docs/hardware_bridge_setup.md` with robot LAN, `ROS_MASTER_URI`, bridge host IP, `ROS_DOMAIN_ID`, ECN arbitration, and smoke tests. | Lab admin dry run from docs on clean host. | No hardware docs release if bridge host cannot be set up from written instructions. |
| DOC-03 | `.repos` pins become stale or ambiguous. | Medium | Medium | Release management | Document exact pins, tested date, update policy, and profile-specific `.repos` files; never use branch names for default external repos. | `vcs import` dry run; release checklist. | No release tag with floating default external dependencies. |
| DOC-04 | Missing compatibility matrix causes unsupported OS/ROS/Gazebo assumptions. | Medium | Medium | Docs | Include matrix for Ubuntu 24.04 Noble, ROS 2 Jazzy, Gazebo Harmonic, MoveIt 2, ECN pinned SHA, hardware bridge host status, and experimental Zenoh status. | Docs review against CI/test environment. | No distribution docs without a tested compatibility matrix. |
| DOC-05 | External labs assume official vendor support. | Medium | Medium | Docs | State clearly: community/university planning stack, no official Baxter ROS 2 vendor support, no native robot firmware migration. | README wording review. | No release if README badges/title imply official Rethink support. |
| DOC-06 | Docs normalize unsafe commands. | Medium | High | Docs / safety | Do not show raw `ros2 topic pub /robot/set_super_enable`; use safe tool examples; put raw commands in instructor/admin appendix only if necessary. | Grep docs for safety topics and raw command patterns. | No hardware tutorial release with raw enable/reset/stop commands in beginner flow. |

### Maintenance Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| MT-01 | Bus factor is too low for ROS 1/ROS 2/bridge/Gazebo knowledge. | High | High | Maintainers / university | Add maintainer guide, bridge-host runbook, release checklist, and ownership of hardware ops; keep package graph small. | Handoff rehearsal: another student/lab admin runs sim and hardware non-motion smoke from docs. | No handoff-ready claim until someone other than primary author can run documented smoke checks. |
| MT-02 | Baxter hardware aging causes intermittent failures. | High | High | Lab ops | Separate software smoke failures from hardware condition; keep hardware checklist; document gripper/camera/end-effector inventory and known issues. | Session logs; repeat non-motion checks; physical inspection. | No hardware motion if state/errors/grippers/cameras are unstable before motion. |
| MT-03 | No official Baxter ROS 2 support exists. | High | Medium | Project governance | Be explicit that this is community-maintained; pin dependencies; prefer standard ROS 2 components; avoid promises of vendor parity. | Docs/release review. | No official-support language. |
| MT-04 | CI maintenance becomes too heavy. | Medium | Medium | CI / maintainers | Default CI covers build, lint, model, MoveIt config, and maybe headless sim; hardware/ROS 1/Zenoh stays manual. | CI runtime and flake tracking. | No default CI requirement for hardware, ROS 1 master, `baxter_legacy`, Zenoh, or broad camera streams. |
| MT-05 | Bridge-host operational knowledge is lost. | High | High | Lab ops / docs | Keep bridge-host setup and recovery docs; include how to stop bridge, check `/robot/state`, clear ownership, and close cameras. | Semester handoff drill. | No hardware lab if bridge host cannot be recovered by documented procedure. |
| MT-06 | University handoff after graduation fails. | High | High | Project governance | Create final S11 blueprint, S10 docs strategy, compatibility matrix, release checklist, and known-open-questions list. | Handoff review with faculty/lab admin. | No "production lab stack" claim without named maintainer or maintainer group. |

### Fallback And Zenoh Risks

| ID | Risk | Likelihood | Impact | Owner/Profile | Mitigation | Detection Method | Go/No-Go Threshold |
|---|---|---:|---:|---|---|---|---|
| FB-01 | `RethoughtRobotics/baxter-zenoh` has very low adoption and young custom bridge assumptions. | Medium | Medium | Experimental | Keep `experimental_zenoh` out of default `.repos`; use only after ECN bridge limitation is measured; pin full SHAs if used. | Maintainer-only prototype; compare against ECN bridge smoke. | No default or supported hardware path based on Zenoh without target-hardware validation. |
| FB-02 | University IT rejects Zenoh, Docker host networking, or port `7447`. | Medium | Medium | Lab ops / experimental | Ask IT before planning labs around Zenoh; keep ECN bridge as default; document ports and network model. | IT review and network test. | No Zenoh workflow if IT does not approve required networking. |
| FB-03 | Zenoh broad topic YAML forwards unsafe or excessive topics. | High | High | Experimental / safety | Restrict `bridge_topics.yaml` to S04 minimum allowlist before any student use; exclude maintenance/admin/high-risk topics. | YAML review; `ros2 topic list`; unsafe topic checklist. | No student Zenoh use with unfiltered upstream broad YAML. |
| FB-04 | Switch criteria from ECN to Zenoh are unclear. | Medium | Medium | Release management | Switch only if ECN cannot install/run on selected bridge host, or measured joint-state/camera transport fails and Zenoh passes safety/IT gates. | Written decision record comparing ECN and Zenoh smoke results. | No switch to Zenoh based only on novelty or convenience. |
| FB-05 | `BaxterSDK` fallback duplicates local package roles and confuses users. | Medium | Low | Docs / experimental | Treat `BaxterSDK` as reference/prototype only; do not mix its examples into default docs unless adopted deliberately later. | `.repos` and docs review. | No default examples that require `BaxterSDK` unless S11 changes architecture. |

### Acceptance Criteria And Release Gates

| Gate | Acceptance Criteria | Required For | Go/No-Go Threshold |
|---|---|---|---|
| Core/model | `colcon build --symlink-install` succeeds for default core; `baxter_description.launch.py` loads `robot_description`; meshes resolve; `/tf_static` works for late subscribers; legacy arm joint names `left_s0`...`left_w2` and `right_s0`...`right_w2` are present. | Any release | No-go if model fails to load, meshes are missing, or legacy joint names are absent/inconsistent. |
| Sim | `sim.launch.py headless:=true` starts Gazebo Harmonic; Baxter spawns; `joint_state_broadcaster`, `left_arm_controller`, and `right_arm_controller` are active; `/joint_states` publishes all 14 arm joints; one tiny sim FJT goal succeeds. | Supported sim profile | No-go for sim support if either arm controller is inactive or `/joint_states` lacks arm joints. |
| MoveIt | `robot_description_semantic` loads with `left_arm`, `right_arm`, `both_arms`, neutral states, and fixed `world_joint`; KDL plugin loads; one-arm plan succeeds; tiny sim execution succeeds through `/left_arm_controller/follow_joint_trajectory` and `/right_arm_controller/follow_joint_trajectory` for advertised arms. | Supported MoveIt sim profile | No-go for MoveIt support if SRDF/KDL fails or executable sim trajectory cannot run. |
| Sim compatibility | If `baxter_sim_compat` is shipped, `/robot/joint_states` and `/robot/state` publish; optional `JointCommand` shim accepts only safe complete position commands and rejects velocity, torque, raw-position, partial joints, and cross-arm joints. | Optional compatibility profile | No-go for compatibility support if unsafe `JointCommand` modes are accepted. |
| Hardware bridge non-motion | On target robot, without enabling or moving: `/robot/state`, `/robot/joint_states`, IK services, camera list/open/close, gripper state/properties where installed, and both hardware action names `/robot/limb/left/follow_joint_trajectory` and `/robot/limb/right/follow_joint_trajectory` are visible; at least one state/joint message is received. | Hardware bridge support | No-go if `/robot/state`, `/robot/joint_states`, or both action names are unavailable. |
| Hardware safety | No launch auto-enables; safe enable/status tool prints state fields and requires explicit confirmation; action shims reject unsafe `/robot/state`; command QoS is not transient-local; speed ratio/timeout are set before motion. | Any hardware docs/support | No-go if default launch can enable/move/reset without explicit operator action. |
| Hardware motion | First release may ship hardware bridge support without claiming motion. Hardware motion may be advertised only after a supervised tiny low-speed single-arm trajectory passes for each advertised arm, feedback is correct, cancel holds position, and disable/return-to-neutral procedure is documented. | Hardware motion support claim | No-go for hardware motion support if only action availability was tested or cancel/unsafe-state behavior is unverified. |
| CI | Default CI builds default core/local packages and runs lint/model/MoveIt config checks; headless sim is included only if stable; CI does not require hardware, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams. | Default repository CI | No-go if ordinary CI needs real hardware, ROS 1, Zenoh, or lab network access. |
| Licensing | Default `.repos` contains only licensed dependencies, initially ECN `baxter_common_ros2`; no copied config/code from unlicensed repos; unlicensed sources are labeled reference-only. | Any public release | No-go if unlicensed sources enter default imports or copied files without verified license. |

### Risk-Driven Documentation Requirements For S10

S10 should carry these requirements into the documentation and distribution plan:

| Documentation Item | Risk It Mitigates |
|---|---|
| Mode selector in README: `sim`, `sim_moveit`, `hardware`, `hardware_moveit`, `experimental_zenoh` | Prevents sim/hardware support confusion. |
| Compatibility matrix with OS, ROS, Gazebo, MoveIt, ECN SHA, and hardware verification status | Prevents unsupported platform assumptions and stale pins. |
| Hardware bridge-host setup guide | Prevents broken networking, unsafe per-student bridges, and lost ops knowledge. |
| Hardware safety guide and enable/status workflow | Prevents raw enable/reset/stop misuse. |
| Smoke-test checklist per profile | Converts risk thresholds into release gates. |
| Licensing and third-party sources page | Prevents accidental unlicensed copying/vendor recommendations. |
| Release notes template with tested profiles | Prevents overclaiming hardware motion, grippers, cameras, or Zenoh. |
| Maintainer handoff/runbook | Reduces bus factor and graduation risk. |

### Immediate Actions And Deferred Validation Log

These are the unresolved items from S09 split into what can be done in the planning phase now and what must wait for implementation, hardware access, IT review, or course-owner decisions.

Already done in this planning step:

| Item | Action Taken Now | Where Logged |
|---|---|---|
| Preserve hardware bridge vs hardware motion distinction | Added separate release gates for hardware bridge non-motion and supervised hardware motion. | `logs/S09_risk_register.log.md` acceptance gates and decisions. |
| Prevent S10/S11 from forgetting validation items | Added S10 documentation requirements for mode labels, compatibility matrix, release notes, smoke-test checklist, licensing page, and maintainer runbook. | `logs/S09_risk_register.log.md` risk-driven documentation requirements; S10 prompt in `PROMPTS.md`. |
| Keep unlicensed repos out of the default graph | Recorded strict licensing no-go gate and reference-only status for unlicensed repos. | `logs/S09_risk_register.log.md` licensing risks and decisions. |
| Keep unsafe hardware actions out of beginner docs | Recorded no-go threshold for auto-enable/raw enable docs and action-shim unsafe-state rejection. | `logs/S09_risk_register.log.md` hardware safety risks and S10 requirements. |
| Keep Zenoh experimental | Recorded switch criteria and no-go thresholds for unrestricted broad YAML or missing IT approval. | `logs/S09_risk_register.log.md` fallback and Zenoh risks. |

Deferred validation backlog:

| Backlog Item | Owner/Profile | Why Deferred | Required Future Check | Release Gate Affected |
|---|---|---|---|---|
| Target Baxter ROS 1 distro, firmware, and graph | Hardware bridge | Needs access to the physical robot and bridge host. | Run `hardware_bridge_smoke`: verify `/robot/state`, `/robot/joint_states`, IK services, camera services, gripper state/properties, and both action names without enabling. | Hardware bridge non-motion. |
| ECN `baxter_bridge` installability | Hardware bridge | Needs chosen bridge-host OS image and ROS 1 support path. | Clean bridge-host install and launch rehearsal using pinned `baxter_common_ros2` SHA. | Hardware bridge non-motion. |
| University DDS/multicast/firewall policy | Lab ops / docs | Needs IT or lab-network decision. | Test student laptop discovery to bridge host, or choose bridge-host SSH/devcontainer-only workflow. | Hardware docs and remote student workflow. |
| Zenoh and Docker host-networking acceptance | Experimental fallback | Only worth pursuing if ECN fails or high-rate transport is bad. | IT approval, restricted YAML, measured comparison against ECN bridge. | `experimental_zenoh` support. |
| Physical gripper and camera inventory | Hardware / examples | Needs target robot inspection. | Record installed end effectors/cameras and run optional camera/gripper smoke checks. | Gripper/camera examples and hardware compatibility matrix. |
| ECN `baxter_description` legacy joint/link names | Core/model / sim / MoveIt | Needs implementation checkout of pinned dependency. | Verify `left_s0`...`left_w2` and `right_s0`...`right_w2` in Xacro, `/joint_states`, controllers, and MoveIt config. | Core/model, sim, MoveIt, hardware action shims. |
| `baxter_legacy` and `BaxterMotionPlanning` licensing | Licensing | Needs license review or maintainer confirmation. | Confirm compatible license or keep reference-only. | Default `.repos`, hardware packaging, sim/MoveIt reuse. |
| Headless Gazebo Harmonic CI stability | CI / sim | Needs actual CI runner. | Repeat `smoke_sim.launch.py headless:=true`; decide required vs manual/allowed-flaky. | Sim CI gate. |
| MoveIt hardware controller name compatibility | MoveIt / hardware | Needs generated MoveIt config and action shim implementation. | Test `moveit_controllers_hardware.yaml` against `/robot/limb/{side}/follow_joint_trajectory`; add aliases only if needed. | Hardware MoveIt. |
| Course need for direct `JointCommand` in simulation | Course owner / sim compatibility | Needs instructor decision. | Ask whether assignments require Baxter-native command topics; if yes, implement safe position-only `baxter_sim_compat` shim. | Sim compatibility. |
| Maintainer ownership after graduation | Project governance | Needs university staffing decision. | Name maintainer group and run a handoff drill from docs. | Production/lab support claim. |

Planning instruction: S10 should document the deferred backlog as compatibility-matrix fields, release-note checkboxes, and known-open validation items. S11 should carry the same backlog into the final blueprint's implementation-phase validation plan.

## Decisions

1. **Hardware bridge support and hardware motion support are separate release claims.** A first release can support hardware bridge non-motion checks after the hardware bridge gate passes. It must not claim hardware motion until the supervised tiny trajectory gate passes on the target robot.
2. **ECN `baxter_bridge` remains the default hardware path.** Use a restricted allowlist and ECN arbitration. Keep Rethought `baxter-zenoh` and `BaxterSDK` experimental unless ECN fails a documented install/runtime/throughput criterion.
3. **Default CI must stay hardware-free.** It should not require a Baxter, ROS 1 master, `baxter_legacy`, Zenoh, Docker host networking, or broad camera streams.
4. **Default licensing gate is strict.** Only licensed sources may enter default `.repos` or copied project files. `angysof16/BaxterMotionPlanning`, `baxter_legacy`, `dabaspark/baxter_sdk_nvidia_any_os`, and stale unlicensed MoveIt repos remain reference-only until license verification changes that status.
5. **Safety checks are release blockers, not documentation nice-to-haves.** No launch auto-enables the robot, action shims reject unsafe `/robot/state`, command QoS avoids stale replay, and hardware examples require explicit operator intent.
6. **MoveIt first-release support is one-arm execution.** `both_arms` can exist in SRDF but synchronized dual-arm execution, Servo, full grasping, and native hardware `ros2_control` are not first-release claims.
7. **Sim compatibility is optional and bounded.** If implemented, `/robot/joint_states` and `/robot/state` are useful. Direct sim `JointCommand` support must be position-only and reject unsafe modes.
8. **Documentation must make support level visible.** S10 should define profile badges or labels such as supported, optional, supervised hardware, and experimental fallback.

## Open Questions

- What exact ROS 1 distro, firmware, and topic/service surface does the target Baxter expose on the robot-side graph?
- Can ECN `baxter_bridge` and its ROS 1 support dependencies be installed reproducibly on the chosen bridge host, or is a bridge container required?
- Will the university network permit DDS discovery from student laptops, or should hardware docs require SSH/devcontainer use on the bridge host?
- Will university IT approve Zenoh and Docker host networking if the fallback path is needed?
- Which physical grippers and cameras are installed, and should gripper/camera support be release-blocking or optional?
- Is headless Gazebo Harmonic stable enough in the chosen CI runner to become a required CI gate?
- Can `CentraleNantesRobotics/baxter_legacy` and `angysof16/BaxterMotionPlanning` licensing be clarified, or must they remain reference-only indefinitely?
- Will MoveIt 2 accept hardware controller entries based on `/robot/limb/left` and `/robot/limb/right`, or will aliases be needed?
- Does the target course require direct `JointCommand` in simulation, or is standard `FollowJointTrajectory` simulation enough?
- Who owns bridge-host operations and dependency pin updates after graduation?

## Artifacts

- Updated this S09 risk register log: `logs/S09_risk_register.log.md`
- Added immediate-action and deferred-validation backlog to this S09 log.
- Updated S09 status in `MASTER_PLAN.md`
- Appended S10 handoff prompt to `PROMPTS.md`
- Prior planning logs used as source decisions:
  - `logs/S01_validate_assumptions.log.md`
  - `logs/S02_audit_community_packages.log.md`
  - `logs/S03_local_repo_analysis.log.md`
  - `logs/S04_bridge_architecture.log.md`
  - `logs/S05_simulation_architecture.log.md`
  - `logs/S06_moveit_ros2_control.log.md`
  - `logs/S07_dev_experience_tooling.log.md`
  - `logs/S08_package_mapping.log.md`
