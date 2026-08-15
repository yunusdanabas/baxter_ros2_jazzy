# Publish Checklist

Everything between "the code is ready" and "the repository is presentable". The
repository is **already public** — these steps fix what a first-time visitor sees
and close the reporting channel the release checklist calls a blocker.

Every step here is a **human action**. Nothing in this file should be run by an
agent: merging, tagging, pushing and changing repository settings are outward-facing
and not reversible by a `git checkout`.

Run them in order. Steps 1–2 are safe at any time; 3–6 depend on the merge.

## 0. State at the time of writing (2026-07-26)

```bash
gh repo view --json name,description,repositoryTopics,visibility,licenseInfo
```

| Field | Value |
|---|---|
| Visibility | public |
| Description | *(empty)* |
| Topics | *(none)* |
| License | BSD-3-Clause, detected |
| `origin/main` vs `i17-pre-hardware-hardening` | 32 commits behind |

## 1. Description

The description is the only text most people read. It has to carry the support
boundary, because "Baxter ROS 2" alone reads as a general-purpose driver.

```bash
gh repo edit --description \
  "ROS 2 Jazzy workspace for Rethink Baxter: Gazebo Harmonic sim, ros2_control, MoveIt 2, and a hardware bridge proven in supervised sessions on one robot."
```

## 2. Topics

```bash
gh repo edit \
  --add-topic ros2 --add-topic ros2-jazzy --add-topic baxter --add-topic moveit2 \
  --add-topic gazebo --add-topic ros2-control --add-topic robotics \
  --add-topic rethink-robotics
```

## 3. Private vulnerability reporting

`ci_release_checklist.md` lists this as **not yet enabled — blocks "ready"**, and
`SECURITY.md` §Reporting already tells people to prefer it. Until it is on, that
instruction points at a channel that does not exist.

**Settings → Security → Private vulnerability reporting → Enable.** Web UI only;
there is no `gh` subcommand for it.

## 4. Merge and tag

Only after `scripts/sim_smoke.sh` passes and CI is green on the branch.

```bash
git checkout main
git merge --no-ff i17-pre-hardware-hardening
git push origin main
git tag -a v0.2.0 -m "v0.2.0: supervised hardware motion, MoveIt limits, publish prep"
git push origin v0.2.0
```

`CHANGELOG.md` already carries `## v0.2.0 - 2026-07-25` and
`docs/release_notes_v0.2.0.md` is written; neither needs editing at tag time.

## 5. Branch protection on `main`

**Do this after step 4, not before.** The required status check can only be
selected from checks GitHub has already seen on that branch, and the CI badge in
`README.md` targets `main` — protecting an empty-history branch leaves you unable
to push the very merge that populates it.

Settings → Branches → Add rule for `main`:

- Require a pull request before merging — optional for a solo maintainer, and it
  will make step 4 fail if enabled first.
- Require status checks to pass → **`hardware-free`** (the job name in
  `.github/workflows/ci.yml`).
- Do not allow force pushes.

## 6. Release

Draft a release from the `v0.2.0` tag, body taken from
`docs/release_notes_v0.2.0.md`.

Keep the support wording as written. The rule from `ci_release_checklist.md`
applies here more than anywhere else, because a Release is the most quotable
surface in the repository: hardware claims name the session date and the gate that
earned them, one BR-01, supervised. Do not let a release note widen that to
general support, sustained duty, gripper commands, or a second robot.

## 7. Read back

```bash
gh repo view --json description,repositoryTopics
gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.contexts'
```

## Still open, deliberately

| Item | Why it is not on this list |
|---|---|
| The three reference PDFs (9.7 MB) in `docs/reference/baxter_legacy/` | A licensing decision, not a publishing step. Rethink's Intera manual and a third party's thesis are redistributed here under their own terms; `licensing_and_sources.md` already flags moving them to LFS or dropping the thesis. Decide before the repository gets attention, not after. |
| `path_tolerance_rad` 0.3–0.4, `left_w0` vs `right_w0` | Needs the robot. |
| Removing `speed_ratio` | Measured to have no effect (I20 F9), but wants one supervised session to confirm before removal. |
