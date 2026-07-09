# Baton — a step-by-step multi-agent workflow

Reusable template. Copy this file into any project that should be executed as a
sequence of gated steps, each run by one agent in a **fresh session**. The name:
each agent finishes its leg, then passes the baton — a self-contained prompt for
the next step.

## The loop

Each agent, in order:

1. Read `AGENTS.md`, its step in `MASTER_PLAN.md`, and all prior logs in `logs/`
   (at minimum the immediately previous step).
2. Execute the step's task, staying inside its scope.
3. Verify the step's **gate** and capture evidence (command output, checks).
4. Write `logs/<STEP>_<name>.log.md` (format below).
5. Update the step's status line in `MASTER_PLAN.md`.
6. Append a **self-contained prompt for the next step** to `PROMPTS.md`.

Because every step runs in a fresh session with no memory of prior sessions, the
prompt is the only context handed over. It must contain every path, gate, rule,
and prior decision the next agent needs — never "as discussed above".

## Required files

| File | Purpose | Discipline |
|---|---|---|
| `MASTER_PLAN.md` | All steps with status tracking | Only the current agent flips its own status |
| `PROMPTS.md` | Accumulated per-step prompts | **Append-only** — never edit prior entries; to fix a prompt, append a superseding one |
| `logs/` | One log per step, evidence of work and gate | Never rewrite completed logs; correct earlier findings in the *current* log |
| `AGENTS.md` | Project-specific rules, scope, resume instructions | Updated only by explicit decision, not by step agents |

## Step definition schema (in MASTER_PLAN.md)

```markdown
### <ID>: <Title>

- **Status:** `pending`
- **Type:** <Research | Design | Setup | Implementation | Tooling | Documentation | Hardware | Release | Optional>
- **Description:** <what to do and what to avoid>
- **Gate:** <objective pass/fail check; a step without a verifiable gate is not done, it is unstarted>
- **Log:** `logs/<ID>_<name>.log.md`
```

Status codes: `pending` → `in_progress` → `completed`; `blocked` (waiting on an
external input, name it in **Blocked By**); `deferred` (intentionally postponed).
`completed` requires gate evidence in the log — status is a claim, the log is the proof.

## Prompt template (append to PROMPTS.md)

````markdown
## <ID> Prompt

You are agent <ID> for the <project> project.

### Task
<what to do, including relevant decisions/findings from earlier steps, restated in full>

### Read First
- `AGENTS.md`
- `MASTER_PLAN.md` — your step <ID>
- `logs/<previous step log>.log.md`
- <other reference files>

### Gate
<copy the gate from MASTER_PLAN.md verbatim>

### Finish — Baton handoff (required)
1. Verify the gate; record the evidence in your log.
2. Write `logs/<ID>_<name>.log.md` in the log format from `WORKFLOW.md`.
3. Update the <ID> status line in `MASTER_PLAN.md` (`completed` only if the gate passed).
4. Append a self-contained prompt for <next ID> to `PROMPTS.md` (append-only).

### Rules
<copy the binding rules from AGENTS.md that apply to this step>
````

## Log template (logs/<ID>_<name>.log.md)

````markdown
---
step: <ID>
title: "<Title>"
agent_date: <YYYY-MM-DD>
status: <completed | blocked>
previous_steps: [<IDs read>]
---

# <ID>: <Title>

## Task
<what was attempted>

## Findings
<what happened, including gate evidence: commands run and their output>

## Decisions
<choices made and why>

## Open Questions
<anything unresolved, for later steps or the human owner>

## Artifacts
<files created/modified>
````

## When a gate fails

- Status stays `pending`/`in_progress` (or becomes `blocked` with a named blocker).
- The log still gets written, with the failure evidence — a failed attempt with a
  good log is progress; a silent retry is not.
- The appended prompt may target the **same step** (a retry prompt carrying what
  was learned) instead of the next one.
- If the failure invalidates an earlier step's finding, say so in the current
  log; do not rewrite the earlier log.
