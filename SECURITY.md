# Security And Safety

This project treats unsafe robot motion, unsafe hardware enable flows, and misleading hardware support claims as safety issues.

## Reporting

For safety-sensitive or security-sensitive reports, use GitHub private vulnerability reporting if enabled for this repository, or contact the repository maintainers out of band. If no private channel is available, open a `Safety concern` issue with impact and mitigation only; do not include step-by-step unsafe hardware instructions.

## Scope

| Area | Status |
|---|---:|
| Sim-only bugs | Public issue is fine. |
| Docs ambiguity that could affect hardware safety | Use `Safety concern` if urgent. |
| Hardware bridge behavior | Gate passed 2026-07-22 on one robot; report as hardware bridge bug. |
| Supervised hardware motion | Gate passed 2026-07-24 on one robot, supervised and low speed. Anything that could cause unintended motion is a `Safety concern`, not a normal bug. |

Beginner and release docs must not teach raw safety-topic publishing or hardware enable commands.

## Maintainer Response

Maintainers should triage safety reports before feature work, remove unsafe public reproduction details if needed, and update `SUPPORT.md`, release notes, or docs when support labels change.
