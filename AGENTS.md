# AGENTS.md — baxter_ros2_jazzy

Agent guide for this repo. The workflow is **Baton** (see `WORKFLOW.md` for the
generic template); this file is the project-specific instance.

## Project purpose and scope

ROS 2 Jazzy workspace for the Baxter Research Robot: Gazebo Harmonic simulation
first, then MoveIt 2 in sim, then gated real-hardware bridge work. Baxter itself
stays a ROS 1 robot; no native firmware migration.

- Active plan: `MASTER_PLAN.md` (steps I00–I14). This is the source of truth.
- Planning archive: `plan/` (steps S01–S11, completed, git-ignored). **Read-only.**
- Implementation blueprint: `plan/logs/S11_final_synthesis.log.md`.
- Implementation cheat sheet (apt packages, YAML formats, gotchas): `RESEARCH_FINDINGS.md`.

## How to run one step

1. Find the first non-`completed`, non-`blocked` step in `MASTER_PLAN.md`.
2. Open a **fresh Claude Code session** and paste that step's latest prompt from
   `PROMPTS.md` (the last entry for that step supersedes earlier ones).
3. One step at a time, in step-number order. No parallel steps.
4. The step is complete only when its **gate** passes with evidence in the log.

## What each agent reads, writes, and updates

Reads:
- `AGENTS.md` (this file), its step in `MASTER_PLAN.md`
- prior `logs/*.log.md` (at minimum the previous step)
- `RESEARCH_FINDINGS.md` and, when needed, `plan/logs/S11_final_synthesis.log.md`

Writes:
- `logs/IXX_<name>.log.md` — YAML frontmatter (`step`, `title`, `agent_date`,
  `status`, `previous_steps`) + sections Task / Findings / Decisions /
  Open Questions / Artifacts. Templates in `WORKFLOW.md`.
- Code/config **only within the current step's scope** (e.g. I04 creates
  `baxter_gz_sim`, nothing else).

Updates:
- Its own status line in `MASTER_PLAN.md` (`completed` only if the gate passed).
- `PROMPTS.md`: appends a self-contained prompt for the next step. Append-only —
  never edit prior entries; to correct one, append a superseding version.

## Rules

- `plan/` is a read-only archive. Never modify anything under it.
- Never mark a step `completed` without gate evidence recorded in its log.
- Hardware steps (I10–I12) stay `blocked` until their named blockers clear.
  Never enable or move the real robot outside the supervised gates.
- No implementation beyond the current step's deliverable; no scaffolding
  "for later steps".
- The `## Rules` list in `MASTER_PLAN.md` is binding: pinned ECN SHA only,
  `--packages-skip baxter_bridge` in sim builds, hardware-free default CI,
  no unlicensed repos in default `.repos`, no raw safety-topic publishing in
  beginner docs.
- If a prior step's finding turns out wrong, record the correction in the
  current log — never rewrite completed logs or past prompts.

## How to resume from the current step

Check `MASTER_PLAN.md` for the first non-completed step — currently **I01** —
and use its latest prompt in `PROMPTS.md` (for I01 that is the **v2** prompt at
the end of the file). If no prompt exists yet for the current step, first write
one from the step's `MASTER_PLAN.md` entry using the prompt template in
`WORKFLOW.md`, append it to `PROMPTS.md`, then run it in a fresh session.
