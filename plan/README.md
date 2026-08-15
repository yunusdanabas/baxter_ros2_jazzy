# Baxter ROS 2 Jazzy Planning Workspace

Planning workspace for migrating the Baxter Research Robot SDK from ROS 1 Noetic to ROS 2 Jazzy. This is a research and design space only, no code implementation.

## Location

```
~/baxter_ros2_jazzy/plan/               # This workspace (planning only, archived)
~/.../catkin_ws/src/baxter_noetic/      # Original Noetic repo (unchanged)
```

`baxter_noetic_ref/` is 64 MB and untracked. On a fresh machine, restore it with:

```bash
git clone https://github.com/yunusdanabas/baxter_noetic.git plan/baxter_noetic_ref
```

Several gate logs (I10, I17) cite file paths under it as evidence, so those
citations only resolve once it is restored.

## Files

| File | Purpose |
|------|---------|
| `MASTER_PLAN.md` | All steps with status tracking |
| `PROMPTS.md` | Accumulated agent prompts (append-only) |
| `EXISTING_RESEARCH.md` | Copy of the original research plan — starting reference for S01-S03 |
| `CONDUCTOR_RESEARCH.md` | The migration feasibility report this whole project started from |
| `baxter_noetic_ref/` | Read-only copy of the Noetic repo for agent reference (no .git) |
| `logs/SXX_*.log.md` | Agent findings per step (YAML+Markdown) |
| `.gitignore` | Prevents tracking in version control |

## Agent Workflow

Each agent follows this sequence:

1. Read its step from `MASTER_PLAN.md`
2. Read all prior logs in `logs/` (especially the immediately previous step)
3. Execute the step's task (research, analysis, or design)
4. Write findings to `logs/SXX_<name>.log.md` using YAML+Markdown format
5. Append the prompt for the next agent to `PROMPTS.md`
6. Update its step status in `MASTER_PLAN.md` from `pending` to `completed`

## Rules

- No agent modifies the original Noetic repo at `~/Yunus Portfolio/ROS1/catkin_ws/src/baxter_noetic/`
- The `baxter_noetic_ref/` copy in this workspace is read-only reference; agents may read but must not edit it
- No agent writes code or creates implementation files
- No parallel execution, one step at a time
- Each agent reads all prior logs before starting its step
- PROMPTS.md is append-only, never edit prior entries
- If a step reveals that a prior step's findings are wrong, note it in the current log, do not edit prior logs

## Step Status Codes

- `pending` — not started yet
- `in_progress` — currently being worked on
- `completed` — finished and logged
- `blocked` — waiting on external input or decision