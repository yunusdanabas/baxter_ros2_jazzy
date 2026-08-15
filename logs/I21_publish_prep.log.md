---
step: I21
title: "Publish Prep: Merge Dual Plans And Execute"
agent_date: 2026-07-25
status: completed
previous_steps: [I00-I09, I10-prep, I10-prep2, I10, I11, I14, I15, I17, I12, I18, I19, I20]
---

# I21: Publish Prep

## Task

Merge two independent I21 research plans (Agent A / Claude, Agent B / Cursor) and
execute publish prep for the already-public `origin/main`, which sits 32 commits
behind `i17-pre-hardware-hardening`. No merge, no push, no tag — those are human.

## Merged Plan

### Starting condition (discovered, not planned for)

**Agent B did not stop at research — it executed its plan into the working tree.**
At I21 start the tree carried 35 modified files, 5 untracked files and 2 deletions,
none committed. Agent B's own plan file marks its Tasks 1–4 `completed` and Task 5
`in_progress`. The prompt's conflict table was written as if both agents had only
planned, so several "A wins" rows describe work B had *already done its way*.

Confirmed with the human (2026-07-25) before touching anything:

| Decision | Ruling |
|---|---|
| Base state | **Keep B's tree**, surgically revert only where it contradicts the table |
| `dry_run_test.py` refactor (already applied, 213 lines) | **Revert to HEAD** — safety gate stays byte-identical to the version that passed on hardware |
| `scripts/run_bridge.sh` (B hardened it) | **Delete** per table |

### Conflict table applied

| Topic | Ruling | State at I21 start | Action |
|---|---|---|---|
| CI asserts shoulder↔elbow pairs must NOT be disabled | A (P0-1) | **untouched — still `not in`, still red** | invert |
| MoveIt-on-hardware claim + F-F | A | partly done; `moveit_guide.md` + `known_issues.md` **untouched** | finish |
| Fast-motion / 5.7× / 2.0 clamp | both, A wording | done by B; 3 × `uncharacterised` remain | reword to `unmeasured` |
| Maintainer email + version 0.2.0 | A | B wrote `REPLACE_ME@example.com`, versions still `0.0.0` | real email + bump |
| `baxter_examples` → `ament_python` | A | not done; B kept `ament_cmake` | convert |
| Shared example helpers | A `_common.py` (4 helpers) | B created `trajectory_helpers.py` (constants + 2 helpers), already imported | **fold A's 4 helpers into B's module** — see deviation below |
| `executor_util.py` | A — inline and delete | not done | inline |
| Shrink `dry_run_test.py` | A — do not | **B did it** | revert |
| Delete `i12_completion_plan.md` / fold `container_free_path.md` | A — keep files | **B deleted both** | restore both |
| Delete `scripts/run_bridge.sh` + sticker | A | B hardened `run_bridge.sh`; sticker untouched | delete both |
| `.env.example` domain lines | A — delete lines | B only added comments around them | delete lines |
| Keep `sim_moveit_rviz` | B | kept | none |
| PDFs under `docs/reference/` | flag human | untouched | flag |
| CODEOWNERS | A `* @yunusdanabas` | B wrote `*` + 3 path lines | keep — superset, harmless |
| v0.1.0-sim banner | A — pointer only | B added pointer, body intact | none |

### Deliberate deviations from the table (with reasons)

1. **`_common.py` → fold into the existing `trajectory_helpers.py`.** The table
   names A's file, but B already shipped a shared module that
   `sim_tiny_trajectory.py` and `moveit_left_tiny.py` import (−82 / −48 lines).
   Two shared modules in a four-file package is the over-engineering ponytail
   exists to stop. A's *substance* — the four deduplicated helpers, the F-C merge
   staying in `sim_tiny_trajectory` only, thin `_cancel_active_goal` methods so
   CI's AST check still matches — is what lands.
2. **`docs/publish_readiness.md` deleted, not edited.** B wrote its readiness
   report into the *published* docs tree. `logs/` is gitignored and is where this
   project's agent reports live; this file is that report, so it moves here.

### Corrections to earlier plans, recorded here (completed logs are never rewritten)

1. Agent A's plan asserts `src/baxter_examples/resource/baxter_examples` "does
   exist". It does not — `resource/` is an empty untracked directory. The
   `ament_python` conversion has to create the marker file.
2. Agent A's plan puts `hardware_moveit.launch.py` in `baxter_hardware_bridge`.
   It is `src/baxter_moveit_config/launch/hardware_moveit.launch.py`.
3. `logs/I19_backlog_plan.md:43` closes item 4 as "measured 0.0352 rad in-flight;
   leave at 0.2 (F22)". I20 F-A reframes it: 0.2 *is* a ~0.5 rad/s speed ceiling
   and *raising* it is the open experiment. Right conclusion, withdrawn reason.
4. I20's Artifacts table claims `docs/moveit_guide.md` was updated. It was — for
   F-B (the trials table). **F-F never reached it.** Closed in this step.
5. `MASTER_PLAN.md:213` (I18 findings) still carries the 5.7×-margin claim that
   F-A withdrew. Left as historical narrative per the AGENTS.md rule; the
   correction lives here.

## Findings

### F21-A. CI had been red-in-waiting since `e543449`, and nobody had run it

Reproduced before fixing, by executing CI's own parse against the working tree:

```text
acm_pairs = 54
('left_upper_elbow', 'left_upper_shoulder') disabled: True
('right_upper_elbow', 'right_upper_shoulder') disabled: True
CI currently asserts these are NOT disabled -> both asserts FAIL today
```

A guard written in I15 (`c600d41`) asserted the two `upper_shoulder`↔`upper_elbow`
pairs were **not** disabled. I18 F18.3 then disabled them on hardware to clear
`-10 START_STATE_IN_COLLISION` at the pose `tuck_arms.py -u` leaves the robot in,
and `scripts/check_srdf.py` grew a `REQUIRED_PAIRS` set demanding the opposite of
what CI demanded. Two guards, contradicting each other, for 32 unpushed commits.

Fixed by inverting the assertions with the reason inline. Also added
`assert len(collision_pairs) == 54` — three documents promise that number and CI
only *printed* it.

### F21-B. The biggest overclaim was an omission, not a sentence

Six status surfaces read "MoveIt on hardware | passed, supervised", and four of
them pointed the reader at `docs/moveit_guide.md` for detail. That file contained
**nothing** about I20 F-F: no abort rate, no `Velocity Scaling: 0.1`, no
single-arm-group advice. `docs/known_issues.md` still opened with "No defect is
currently open." while an unexplained, reproducible left-arm abort pattern was
open. The gate `grep -rln "8 of 11\|left_w0"` over the four required surfaces
returned **zero files** at I21 start.

The stale *sentences* Agent B had already fixed. The missing *page* is what a
grep-based claim audit cannot find, and it was the real defect.

### F21-C. `ament_python` alone did not fix the stale-code trap

Converting `baxter_examples` and rebuilding produced **zero** working entry
points — the scripts landed in `install/baxter_examples/bin/` instead of
`lib/baxter_examples/`, so `ros2 run` could not see them. The sibling
`ament_python` package works only because it carries a `setup.cfg`:

```text
[develop]
script_dir=$base/lib/baxter_examples
[install]
install_scripts=$base/lib/baxter_examples
```

Neither plan mentioned this file. Agent A's plan additionally asserted
`resource/baxter_examples` already existed; `resource/` was an empty untracked
directory and the marker had to be created. Both would have failed the 5c gate.

After adding `setup.cfg`, the claim was verified **empirically** rather than by
inspection — a build that compiles is not evidence the trap is gone:

```text
=== empirical test: edit src, run WITHOUT rebuilding ===
module file: .../build/baxter_examples/baxter_examples/sim_tiny_trajectory.py
probe visible without rebuild: True
```

`docs/hardware_runbook.md` documented the old copy-not-symlink behaviour as a
standing gotcha; that paragraph was false the moment 5c landed and was rewritten.

### F21-D. The refactor changed a log string a doc asserted on

Sharing `cancel_active_goal` normalised three message wordings into one, so the
arm now logs `Controller goal canceled; holding position` instead of
`Active trajectory canceled; controller is holding position`.
`docs/hardware_test_commands.md:437` told the operator to expect the old string
verbatim. Caught by running the cancel test, not by reading the diff. Updated.

### F21-E. CI's cleanup-handler guard survived the refactor, and can still fail

The AST check matches an *attribute* call named `_cancel_active_goal` as a direct
child of an `except BaseException` handler. Moving the body to a module function
would have left it passing vacuously, so each class keeps a thin delegating
method. Verified both directions:

```text
cleanup_handler_checks=passed  (BaseException handlers inspected: 3)
NEGATIVE CONTROL -> CORRECTLY FAILED: src/.../sim_tiny_trajectory.py:232
```

The negative control matters: a guard that cannot fail is not a guard.

### F21-F. The refactor orphaned nine imports, which no gate would have caught

`compileall` and the import checks both pass with unused imports present, so the
refactor's fallout was invisible to every gate in the prompt. A `pyflakes` pass
over the touched files found nine:

```text
moveit_left_tiny.py:  math, sys, pathlib.Path, ParameterType, AsyncParameterClient
moveit_pose.py:       ParameterType, AsyncParameterClient
sim_tiny_trajectory.py: math, sys, pathlib.Path
```

`sys` and `Path` were the `sys.path.insert` hack the `ament_python` conversion
removed; `ParameterType`/`AsyncParameterClient` were `_require_sim_move_group`'s
body; `math` was `positions_for_joints`, which had already moved. Verified against
`HEAD` to separate this session's fallout from pre-existing lint — only two
findings predate it (`mock_robot.py:15 List`, `moveit_pose.py:5 Optional`). Fixed
the nine plus `Optional` (that file was already open); left `mock_robot.py` alone
as an untouched file.

Because pyflakes reports undefined names as well as unused ones, a clean run also
proves no *needed* import was removed by mistake — but the whole sim smoke was
re-run afterwards anyway, since method bodies are not executed at import time.

## Gate evidence

All run from a clean `rm -rf build install log` rebuild, `scripts/baxter_env.sh`
sourced first (conda-shebang trap), `BAXTER_HOST=unused`.

```text
$ colcon build --base-paths src --symlink-install --packages-skip baxter_bridge
Summary: 9 packages finished [1min 8s]
  1 package had stderr output: baxter_moveit_config      <- upstream tl_expected
                                                            deprecation only

$ ros2 run baxter_hardware_bridge dry_run_test
OVERALL: PASS
(25 PASS lines + 1 OVERALL = 26; Tests 1-25 all present)

$ bash scripts/test_bridge_loopback.sh
PASS: ROS1->bridge received 3.14
PASS: bridge->ROS1 publish loop done
=== OVERALL: PASS (both directions negotiated real TCPROS with genuine rospy) ===

$ # CI "Model and MoveIt config checks", heredoc extracted from ci.yml verbatim
robot name is: baxter
---------- Successfully Parsed XML ---------------
moveit_static_check=passed groups=['both_arms', 'left_arm', 'left_hand',
  'right_arm', 'right_hand'] independent_joints=17 acm_pairs=54

$ # CI import checks, expanded list, package imports for ament_python
python_import_checks=passed

$ # CI cleanup-handler AST guard
cleanup_handler_checks=passed  (BaseException handlers inspected: 3)

$ python3 -m compileall -q src/...
compileall=passed

$ python3 -c "import yaml;yaml.safe_load(open('.github/workflows/ci.yml'))"
ci yaml ok
issue template ok: ['blank_issues_enabled', 'contact_links']
```

### Manual sim smoke (required — Task 5 touched the evidence-producing client)

```text
$ ros2 control list_controllers
left_arm_controller     joint_trajectory_controller/JointTrajectoryController  active
right_arm_controller    joint_trajectory_controller/JointTrajectoryController  active
joint_state_broadcaster joint_state_broadcaster/JointStateBroadcaster          active

$ ros2 launch baxter_examples sim_tiny_trajectory.launch.py
left  outbound verified: max_error=0.0105 rad (settled in 0.01 s)
left  return   verified: max_error=0.0102 rad (settled in 0.00 s)
right outbound verified: max_error=0.0069 rad (settled in 0.01 s)
right return   verified: max_error=0.0061 rad (settled in 0.01 s)
Reversible trajectories verified for both arms
process has finished cleanly
                                          (all four <= 0.02 rad threshold)

$ ros2 run baxter_examples sim_tiny_trajectory -p cancel_after_sec:=1.0
Controller goal canceled; holding position
Cancellation hold verified: max_drift=0.0012 rad (settled in 1.01 s)
EXIT CODE: 0
```

### Manual MoveIt sim smoke

```text
move_group: "You can start planning now!"   pipeline ompl
/move_action present; 3 controllers active

moveit_left_tiny  left_arm  outbound points=23 max_error=0.0092 / return 0.0078
moveit_tiny       right_arm outbound points=21 max_error=0.0097 / return 0.0090
moveit_tiny       both_arms outbound points=22 max_error=0.0094 / return 0.0115
moveit_pose       left_arm  pose goal reached: points=95, position_error=0.0255 m
ik_service_client left      solved (left_w0 +1.9231, left_w1 -0.4186, left_w2 -2.2221)
ik_service_client x:=9.0    exit code 1   (unreachable must exit non-zero)

moveit_tiny -p cancel_after_sec:=1.0
  MoveGroup goal canceled; holding position
  Cancellation hold verified: max_drift=0.0015 rad

teardown: one SIGINT to the owning launch
  gazebo-1, parameter_bridge-2, robot_state_publisher-3 all
  "process has finished cleanly"
  leftover processes: NONE      ros2 node list: EMPTY
```

Note on teardown: two orphans (`rviz2`, `ros_gz_bridge`) did survive at first,
but they came from an **earlier** `sim_rviz.launch.py` that I had killed with
`pkill -9` mid-session, not from the MoveIt launch's SIGINT path. The MoveIt
launch's own teardown was clean on its first and only attempt. Recording this
because "leftover process" is a gate failure and the distinction matters.

### Publish-hygiene greps

```text
$ grep -rn "example\.com" src/*/package.xml                            -> no output
$ grep -rn "011412P0024\|192\.168\.1\.224" scripts/ docker/ .env.example -> no output
$ grep -rn "5\.7×\|5\.7x\|uncharacterised\|gentle motion only" \
    README.md SUPPORT.md CONTRIBUTING.md CHANGELOG.md docs/ --include='*.md' \
    | grep -v docs/i12_completion_plan.md                              -> no output
$ grep -rln "8 of 11\|left_w0" docs/moveit_guide.md docs/known_issues.md \
    SUPPORT.md README.md
    SUPPORT.md  README.md  docs/moveit_guide.md  docs/known_issues.md  (all four)
$ git check-ignore -q docker/local_image_inventory.md && echo ignored   -> ignored
$ grep -c badge.svg README.md                                          -> 1
$ grep -h "<version>" src/*/package.xml | sort -u            -> <version>0.2.0</version>

$ # sourcing without BAXTER_HOST must fail loudly and NOT kill the shell
$ bash -c 'source scripts/baxter_env.sh; echo "shell survived, rc=$?"'
ERROR: set BAXTER_HOST before sourcing (e.g. export BAXTER_HOST=<robot-serial>.local)
shell survived, rc=1

$ # link integrity: every docs/*.md referenced from markdown exists
(no MISSING lines)

$ python3 -m pyflakes src/baxter_examples/baxter_examples/*.py
(clean)
$ # markdown table integrity across every edited .md, escaped pipes ignored
all markdown tables well-formed
```

### Polish pass (re-run after the import cleanup and doc fixes)

Clean `rm -rf build install log` rebuild, then every gate again:

```text
Summary: 9 packages finished [1min 7s]
OVERALL: PASS          (25 PASS lines)
all 5 entry points present; shebang #!/usr/bin/python3
moveit_static_check=passed ... independent_joints=17 acm_pairs=54
compileall=passed
python_import_checks=passed (baxter_examples package imports)
test_bridge_loopback: OVERALL: PASS
cleanup_handler_checks=passed (handlers inspected: 3)

re-smoke of every refactored client after removing imports:
  sim_tiny_trajectory  0.0105 / 0.0102 / 0.0095 / 0.0067 rad, both arms reversible
  cancel-and-hold      max_drift=0.0012 rad
  moveit_left_tiny     0.0058 / 0.0111 rad
  moveit_tiny right    0.0081 / 0.0096 rad
  moveit_pose          pose goal reached, position_error=0.0291 m
  moveit_tiny cancel   max_drift=0.0000 rad
  ik_service_client    exit=1 on unreachable
  teardown             NONE — clean on first attempt, no orphans

12/12 consolidated final gate sweep: all PASS
final publishable diff: 41 files, +435/-444
```

## Decisions

1. **Kept Agent B's working tree, reverted six items.** Reverting everything
   would have discarded ~20 files of correct I20 doc sync, the Contributor
   Covenant, CODEOWNERS and the v0.2.0 notes, all of which I would have rewritten
   near-identically. The cost is that B's wording had to be re-read line by line
   against A's claim matrix rather than trusted.
2. **`dry_run_test.py` reverted to HEAD byte-for-byte.** B's refactor looked
   sound and kept all 25 cases, but the release evidence is "this gate passed on
   the robot", and that sentence is only true of the file that ran. Verified
   identical to HEAD with `git diff --quiet`.
3. **`trajectory_helpers.py` rather than a second `_common.py`.** The conflict
   table names A's filename; A's *substance* is what landed. Two shared modules
   in a four-file package would be the exact over-engineering this project's
   ponytail rule exists to prevent.
4. **`wait_for_fresh_joint_state` and `_joint_state_cb` deliberately NOT
   shared.** They look like duplication and are not: the `sim_tiny_trajectory`
   versions carry the I20 F-C two-publisher merge and tolerate an incomplete
   merged view. Unifying them on the sim-only version would silently undo a
   hardware fix. The reason is now in the module docstring so the next reader
   does not "tidy" it.
5. **Serial dropped from `docs/release_notes_v0.2.0.md`, kept in runbook and
   evidence docs.** Release notes are the most-copied file in any repo, and
   `011412P0024` has zero hits on `origin/main` today — publishing it there is a
   new disclosure, not a continuation. "one BR-01" carries the same meaning.
6. **`docs/publish_readiness.md` deleted.** B had written its agent report into
   the *published* docs tree; `docs/index.md` even listed it. This log is that
   report, and `logs/` is gitignored.
7. **CI's contact gate widened to `SECURITY.md` and `CODE_OF_CONDUCT.md`.** The
   checklist no-go row already promised all three surfaces; the gate only checked
   `package.xml`. B's gate also deadlocked against B's own
   `REPLACE_ME@example.com`, so CI would have failed on its first run either way.
8. **Added an I21 step to `MASTER_PLAN.md` and marked it `completed`.** Its gate
   text states only what actually passed and explicitly excludes the merge, tag
   and GitHub settings, which are not mine to run.

## Open Questions

1. **Does raising `path_tolerance_rad` to 0.3–0.4 buy usable speed?** Unchanged
   from I20 — still the top hardware question, still needs a supervised session.
2. **`left_w0` vs `right_w0`:** commanded faster, or tracked worse? The decisive
   experiment is specified in `docs/known_issues.md` and needs the ROS 1 recorder
   running, which is what I20 lacked.
3. **`speed_ratio` is inert** (I18 F9, reconfirmed I20). Removal needs a robot
   session to prove nothing depends on it. Untouched.
4. **`docs/reference/baxter_legacy/*.pdf`** — 9.4 MB, ~85 % of the tracked tree,
   redistributing a Rethink manual and a named third party's thesis. Already
   public since `ee03d60`, so this is a retraction decision with a
   history-rewrite cost, not a prevention. Flagged, not acted on.
5. **`AGENTS.md:12` still says "steps I00–I19".** Gitignored, so not a publish
   issue; left alone rather than edited, since it is local agent scaffolding.

## Human-only leftovers

None of these were attempted, per the prompt's hard stop.

1. **Enable GitHub private vulnerability reporting** (Settings → Security).
   `SECURITY.md` now names it as the preferred channel; that pointer is a lie
   until it is switched on. Tracked as an explicit no-go row in the checklist.
2. **Merge `i17-pre-hardware-hardening` → `main` (32 commits) and tag `v0.2.0`.**
   The first push runs CI on the already-public repo, so the F21-A fix must be in
   the merge — that is the whole reason it was P0.
3. **The PDF retention decision** (Open Question 4).
4. **Confirm the serial call** — Decision 5 keeps `011412P0024` out of the
   release notes and in the runbook/evidence docs. Reversible either way.

## Artifacts

**Reverted to HEAD:** `dry_run_test.py`; `docs/i12_completion_plan.md` and
`docs/container_free_path.md` restored, with their `docs/index.md` rows.

**Deleted:** `scripts/run_bridge.sh`, `docs/baxter_sticker.jpeg`,
`src/baxter_examples/CMakeLists.txt`,
`src/baxter_hardware_bridge/baxter_hardware_bridge/executor_util.py`,
`docs/publish_readiness.md` (untracked).

**Added:** `src/baxter_examples/setup.py`, `src/baxter_examples/setup.cfg`,
`src/baxter_examples/resource/baxter_examples`, `docs/release_notes_v0.2.0.md`,
`CODE_OF_CONDUCT.md`, `.github/CODEOWNERS` (last three from Agent B, corrected).

**Modified:** `.github/workflows/ci.yml` (SRDF asserts inverted + 54-pair
assertion + widened contact gate + expanded/restructured import list),
`.github/ISSUE_TEMPLATE/config.yml`, `.env.example`, 5 × `package.xml`
(email + version 0.2.0), `src/baxter_hardware_bridge/setup.py`,
`follow_joint_trajectory_shim.py`, `dry_run_test.py` (executor inline only),
`trajectory_helpers.py` + the three example clients, `MASTER_PLAN.md` (I21 step),
`CHANGELOG.md` (v0.2.0 promotion, structure, I20 + I21 entries, F-F limitation),
`README.md`, `SUPPORT.md`, `CONTRIBUTING.md`, `SECURITY.md`, and
`docs/{moveit_guide,known_issues,index,maintainer_handoff,compatibility_matrix,
package_map,noetic_native_notes,ci_release_checklist,hardware_day_plan,
hardware_runbook,hardware_test_commands,licensing_and_sources,
release_notes_v0.1.0-sim,release_notes_v0.2.0}.md`.

`MASTER_PLAN.md`, `AGENTS.md`, `WORKFLOW.md`, `PROMPTS.md` and `logs/` are all
gitignored, so the I21 step entry and this log are local agent scaffolding, not
part of the published diff. The publishable change is **41 files, +435/−431**.

**Not committed.** Working tree only, as instructed.

---

# I21b: Docs reorganization, test surface, full no-robot verification

Second pass, 2026-07-26. User asked for a publish-grade test and polish pass, a
set of no-robot test commands, and a docs reorganization (merge / archive /
remove). Plan approved before execution; commit decision: **leave uncommitted**.

## Findings

### F21-G. `colcon test` was a no-op while four test deps claimed otherwise

`src/baxter_hardware_bridge/package.xml` declared `ament_copyright`,
`ament_pep257`, `ament_flake8` and `python3-pytest`. `find src -path '*/test*'`
returned nothing: **zero tests in the repository**. A maintainer running
`colcon test` got a green summary that verified nothing, and the declared
linters had never run — the code has no copyright headers and does not follow
pep257, so enabling them would have failed immediately.

Fixed by giving the branchiest pure logic one real test rather than restoring
three boilerplate `ament_lint` files: `test_trajectory_helpers.py`, 16 tests over
`choose_reversible_target` and the two joint-state readers. The phantom lint
deps are removed; `python3-pytest` stays and `baxter_examples` gained one.

### F21-H. The first version of that test could not fail

Mutation check before trusting it. Removing the negative-direction fallback
failed 2 tests as intended — but **setting `JOINT_LIMIT_MARGIN_RAD = 0.0`
changed nothing**: 15/15 still passed. Every start position I had picked
(`0.0`, `0.9`, `±2.0`, both limits) resolves the same way with or without the
margin; the margin only decides the outcome when `start + delta` lands in the
narrow band between `upper - margin` and `upper`.

Added `start = 0.68` (0.68 + 0.35 = 1.03 rad, a legal `s1` position 0.017 rad
inside the 0.05 rad margin). Both mutations now fail. The generalisable point:
a test whose inputs never reach the branch under test passes for the wrong
reason, and only a mutation run exposes that — coverage would have reported the
line as covered.

### F21-I. `baxter_env.sh` cannot be used for the sim build path

The first draft of `sim_test_commands.md` told the reader to
`source scripts/baxter_env.sh` before `colcon build`, carried over from the
hardware runbook where that instruction is correct. It fails immediately:

```
ERROR: set BAXTER_HOST before sourcing (e.g. export BAXTER_HOST=<robot-serial>.local)
```

It is a hardware-session script — it also exports `ROS_MASTER_URI` and prints
bridge terminal instructions. But the reason it is cited (stripping conda from
`PATH`, or the console scripts get a conda shebang and die on
`rclpy._rclpy_pybind11`) applies to the sim path too. `conda deactivate` is
sufficient and was verified to restore `/usr/bin/python3`. The sheet now says
that, and says explicitly not to use the hardware script.

Caught by *running* the sheet's own first command, not by writing it.

### F21-J. The lint gate needs a tool the ROS environment does not provide

`ruff` is not a ROS package and `rosdep` will not install it. On this machine it
lives inside the conda install — which the build path requires deactivating, so
`ruff` vanished from `PATH` exactly when the sheet told the reader to run it. CI
is unaffected (`pipx install ruff`). The sheet now states where `ruff` comes
from and that it is a standalone binary needing neither ROS nor the system
python3.

## Docs reorganization

19 active docs → **15**, plus `docs/archive/` (2 + a README). Four removed by
merging, two moved to the archive, two added.

| Action | Files |
|---|---|
| Merged into `support_matrix.md` | `compatibility_matrix.md`, `package_map.md`, `repos_and_pins.md` |
| Folded into `noetic_native_notes.md` | `container_free_path.md` |
| Moved to `docs/archive/` | `i12_completion_plan.md`, `release_notes_v0.1.0-sim.md` |
| New | `sim_test_commands.md`, `support_matrix.md`, `archive/README.md` |
| Rewritten in place | `index.md` (navigation only), `hardware_day_plan.md` P4a/P6 |

Rationale for the merge: the support table existed in **three** places
(`README.md`, `docs/index.md`, `compatibility_matrix.md`) and the ECN pin in
three of the merged files. Over-broad hardware claims are an explicit release
no-go, so three copies of the claim table is the highest-value duplication to
remove. `README.md` keeps the landing-page table; `index.md` now points at
`support_matrix.md` instead of restating it.

The I21 merge table had ruled "keep `i12_completion_plan.md` /
`container_free_path.md`". The user's later instruction to remove and merge
supersedes it; both files were **preserved** (archived / folded) rather than
deleted, so the reproducibility record that ruling protected still exists.

Every cross-reference in the repo was a bare backtick filename — not one
markdown hyperlink, so nothing was clickable on GitHub and no link checker could
verify the moves. Converted in `index.md`, `README.md` and each edited doc.

## Gate evidence — 2026-07-26

Clean rebuild: `rm -rf build install log`, conda deactivated
(`which python3` = `/usr/bin/python3`), `source /opt/ros/jazzy/setup.bash`,
`colcon build --base-paths src --symlink-install --packages-skip baxter_bridge`
→ 9 packages, 1 min 11 s, only a `tl_expected` deprecation on stderr.

```text
maintainer_contact_check=passed
compileall=passed
ruff_f_checks=passed                    (All checks passed!)
colcon test baxter_examples             Summary: 16 tests, 0 errors, 0 failures, 0 skipped
python_import_checks=passed
cleanup_handler_checks=passed (handlers inspected: 3)
dry_run_test                            OVERALL: PASS, 25 "PASS: Test" lines
check_urdf                              Successfully Parsed XML, root link world -> base
acm_pairs=54                            both hand-added pairs present
entry points                            install/baxter_examples/lib/baxter_examples/ (5), no bin/
docs links                              0 broken relative .md links
table integrity                         table_check=passed
```

Gazebo smoke (`sim.launch.py headless:=true`): 3 controllers active, 17 joints.

```text
sim_tiny_trajectory.launch.py   left 0.0069 / 0.0103, right 0.0105 / 0.0067 rad
joint:=e1                       left 0.0085 / 0.0102, right 0.0104 rad
joint:=elbow                    RuntimeError: Unknown joint 'elbow'; exit 1
cancel_after_sec:=1.0           "Controller goal canceled; holding position", max_drift=0.0012 rad
```

MoveIt smoke (`sim_moveit.launch.py headless:=true`), pipeline `ompl`, planner
`OMPL` loaded, `/move_action` present:

```text
moveit_left_tiny                0.0096 / 0.0098 rad (23 points)
group:=right_arm                0.0097 / 0.0117 rad
group:=both_arms                0.0088 / 0.0108 rad
moveit_pose delta_z:=0.05       position_error=0.0225 m (103 points)
moveit_pose plan_only:=true     "pose plan succeeded: points=90" — no execution
ik_service_client left          solved, exit 0
ik_service_client x:=9.0        MoveItErrorCodes -31, exit 1
moveit_tiny cancel              "MoveGroup goal canceled; holding position", max_drift=0.0000 rad
```

Teardown: one SIGINT to each owning launch, both exited 0, **no orphans on the
first attempt either time**.

The cancel log strings were re-verified against what `sim_test_commands.md`
tells an operator to expect, because a refactor in the first pass silently
changed one of them and only running it caught that.

## Deliberate non-changes

- The three reference PDFs (9.7 MB) stay. Out of scope, and the retention
  decision is a licensing question for a human — redistributing Rethink's Intera
  manual and a third party's thesis from a BSD-3 repo is not a taste call.
- Active docs stay flat. At 15 files, `hardware/` and `release/` subdirectories
  would cost more reference churn than the grouping is worth; trivially
  reversible later.
- The pinned SHA still appears in 16 files. The merge removed 2 of them
  (3 → 1 across the merged docs); the rest are issue templates asking for it, CI
  enforcing it, the `.repos` files defining it, and release notes recording it —
  records, not drift-prone duplication. The plan's claim that this would drop to
  4 files was wrong; it only ever counted the docs being merged.

## Publishable diff

**58 files, +1617/−852** including new files, of which the tracked-file delta is
47 files / +687/−852. `logs/`, `MASTER_PLAN.md`, `AGENTS.md`, `WORKFLOW.md`,
`PROMPTS.md` remain gitignored.

**Not committed, not pushed, not merged, not tagged.**

---

# I22: Sim smoke script, LaTeX manual, publish surface

2026-07-26. Three follow-ups the user selected from the I21b "what's worth doing
next" list. Plan approved before execution.

## Findings

### F22-A. `kill -INT` on a backgrounded launch is a silent no-op

`sim_smoke.sh` teardown failed with *"still alive 30 s after one SIGINT"* while
the identical `kill -INT <launch pid>` had worked when run by hand. Cause: bash
sets SIGINT and SIGQUIT to `SIG_IGN` in **asynchronous commands when job control
is off**, which it is in a non-interactive script. The signal was delivered and
discarded. `set -m` restores job control and the default disposition.

Then a second, opposite mistake: signalling the *process group*
(`kill -INT -$PID`) kills `ros2 launch` outright in ~2 s and leaves its children
orphaned, because the launch never runs its own shutdown sequence. The correct
form is `set -m` plus SIGINT to the launch PID alone.

This also explains a downstream red herring: MoveIt `left_arm` and `both_arms`
failed in the same run. They were contending with the controllers orphaned by
the broken teardown, and passed once teardown was fixed.

### F22-B. `pgrep -f` treats any shell that *mentions* a process name as that process

The orphan check matched the invoking wrapper shell, so the script refused to
start with no simulation running. Matching command lines is unavoidable —
Gazebo runs as `ruby` (`gz sim -r -s empty.sdf`) and `comm` truncates at 15
characters (`parameter_bridg`, `robot_state_pub`) — so the fix is to exclude
processes whose `comm` is a shell. No real simulation process is a shell.

An ancestry walk was tried first and was insufficient: the false positive was a
*sibling* fork of the wrapper, not an ancestor.

### F22-C. The smoke script's first draft could pass on a client that printed nothing

Threshold checks over `max_error` are vacuous when there are no `max_error`
lines to check. `assert_motion` therefore takes a minimum count (4 for the
two-arm client, 2 for a single MoveIt group) and fails below it. Same defect
class as I21b's margin test that passed with the margin removed.

### F22-D. `sim_test_commands.md` told readers to source a hardware script

Already recorded as F21-I; repeated here because `sim_smoke.sh` now enforces it:
the script refuses to run unless `python3` is `/usr/bin/python3`, which is the
condition the prose describes. A `PATH` carrying conda's `ruff` also carries
conda's `python3`, so the two requirements conflict on this machine — resolved
by symlinking `ruff` alone into a directory on `PATH`.

## Mutation evidence — the script can fail

| Mutation | Result |
|---|---|
| `MAX_ERROR_RAD=0.001` (below the observed ~0.01) | 2 FAIL, exit 1 — the parsed values, not the exit codes |
| Real stray `robot_state_publisher` running | REFUSING, exit 1 |
| Log with 0 or 2 `max_error` lines where 4 required | rejected; 2-of-2 case still accepted |
| (unplanned) broken teardown | 6 FAIL including both orphan checks |

## Gate evidence — 2026-07-26

```text
scripts/sim_smoke.sh all        24 passed, 0 failed, exit 0
  gates                         7/7 (hygiene, compileall, ruff, colcon test,
                                dry_run 25 cases, check_urdf, acm_pairs=54)
  gazebo                        ready 2 s; both arms, joint:=e1, unknown joint
                                refused, cancel max_drift 0.0012 rad; teardown clean
  moveit                        ready 5 s; left/right/both <= 0.02 rad;
                                moveit_pose 103 pts; plan_only planned without
                                executing; ik exit 0 / exit 1; cancel drift
                                0.0000; teardown clean

docs/manual  make from distclean rc=0, 31 pages, 0 undefined refs, 0 "??",
             0 placeholder boxes, worst overfull 11.2 pt
```

Claims audit: 24 numeric/date claims cross-checked against `docs/`, `README.md`
and `CHANGELOG.md` — **0 unbacked**. Appendix B verified programmatically against
`follow_joint_trajectory_shim.py`: 7 joint limit rows and 9 parameter defaults,
**0 mismatches**.

## Figures — and what was declined

The user asked for images taken from the three legacy PDFs "but don't give
credit". Declined, and said so plainly: `docs/reference/baxter_legacy/README.md`
already records that those files "retain their original authorship and terms" and
are "not relicensed under the repository BSD-3-Clause", the repository is public,
and uncredited artwork from Rethink's Intera manual and a third party's thesis
would contradict the repository's own licensing page.

The PDFs are used as **information** sources for Chapter 2 — joint layout,
workspace limits, enable/tuck semantics, legacy SDK topics. Facts are not
copyrightable and restating them is ordinary technical writing.

All six figures are original: three TikZ diagrams, one pgfplots chart of the
measured I20 lag points, a graphviz TF tree generated from the URDF, and two
RViz screenshots captured during this session. The lag chart is the one figure
no source PDF could have provided — it is this robot's measured behaviour and
the basis of the workspace's central safety claim.

## Item 3 — prepared, not executed

`docs/publish_checklist.md` drafts the description, topics, vulnerability
reporting, merge/tag, branch protection and release steps. Nothing was run:
`gh repo view` confirmed the repository is already **public** with an empty
description and no topics, and repository settings remain human-only.

One ordering trap recorded: branch protection must be added *after* the merge and
the first green CI run on `main`, or the required status check cannot be selected
and the merge itself is blocked.

## Publishable diff

**84 files, +3967/−852**, 37 of them new. `docs/manual/` sources are tracked; the
PDF and latexmk artifacts are gitignored, verified per file.

**Not committed, not pushed, not merged, not tagged.**
