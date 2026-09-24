---
name: coordinate-project-agents
description: Coordinate coding agents from different tools or platforms on a software project. Use when assigning work to external agents through the user, defining module ownership and handoffs, or reviewing their combined changes.
---

# Coordinate External Project Agents

The user works with agents in other tools or chats. Act as the coordinator: inspect the project, split work, write self-contained task messages the user can send, review returned branches or artifacts, and check integration. Do not assume those agents share this conversation, filesystem, credentials, or tool access.

## Prepare a project

1. Read the project's own instructions, code structure, branch state, open work, and tests. Record a stable baseline and blockers; do not treat an unreviewed or failing PR as the starting point for dependent work.
2. Assign ownership by meaningful module or interface boundary. Choose one integration owner for shared files. Use as many parallel agents as the work supports, without fixing roles or count in advance.
3. Agree on shared contracts before dependent coding. State field meanings, error cases, missing data, timestamps, IDs, and compatibility as needed. Version a changed contract and notify every consumer.
4. Produce one self-contained brief per external agent. Include repository location, exact base revision, owned files, goal, dependencies, interface contract, tests, real-flow acceptance, and delivery format. The prompt must make sense when pasted into a fresh chat with no prior context.
5. Ask the user to relay briefs and results when no direct communication channel is available. Do not claim to have dispatched a task or seen unpushed work. If branches, PRs, or files become accessible, inspect those artifacts directly.
6. Track status as assigned, working, review, blocked, or integrated. Record the owner, exact revision or artifact, dependency, and next action. A common board may be a document, issue tracker, or conversation summary.
7. Review each returned change against its brief and contract at the exact delivered revision. Re-run risk-relevant checks where possible; record commands, environment, results, and what was not tested. Compare failures with the same checks on the agreed base before calling them pre-existing.
8. Integrate in dependency order on the agreed branch, resolve shared-file conflicts with the owner, and run actual cross-module user flows. Separate code review, integration, and release acceptance: passing unit tests alone does not establish any of the latter two.
9. Report verified behavior and remaining gaps to the user. Follow the project's own rules and the user's authorization for merging, deployment, and messages to people or external services.

## Isolation and evidence

- Prefer a separate branch and checkout for each agent when using Git. In other environments, require an equivalent isolated deliverable and a clear base revision.
- Keep credentials and private data in authorized local storage. Use synthetic or authorized fixtures and separate runtime state for concurrent tests.
- Require a handoff with changed files, interface changes, commands and results, real-flow evidence, known gaps, and a link or path to the deliverable.
- Distinguish direct evidence from an external agent's claim. Re-run important checks where the work is accessible.
- Do not publish private repository content, credentials, paid data, or agent transcripts in a shared brief or public artifact. When outside access is limited, ask for redacted evidence instead of broadening access silently.
- If a reviewer cannot test an external API, browser flow, or deployment, mark that acceptance item unverified. A favorable review of accessible code does not close the missing gate.

## Output

Use the [project charter, paste-ready task brief, review brief, and handoff templates](references/templates.md) when they help. Give the user messages or a document they can share with external agents. Adapt the templates to the project; do not write them into a repository unless the user requests that.

