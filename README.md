# Coordinate Project Agents

A Codex skill for coordinating software work across agents in different tools or chats. It helps a coordinator define ownership, write self-contained briefs, track exact revisions, review returned work, and verify integration without assuming the agents share a filesystem or conversation.

The skill is project-agnostic. It does not dispatch agents, merge pull requests, or grant access by itself.

## Install

Copy the [`coordinate-project-agents`](coordinate-project-agents) directory into your Codex skills directory:

- Windows: `%USERPROFILE%\.codex\skills\coordinate-project-agents`
- macOS/Linux: `~/.codex/skills/coordinate-project-agents`

Restart or refresh Codex if the new skill is not discovered immediately.

## Use

Ask Codex to split a project task among external agents, draft a handoff for another tool, or review work returned from a collaborator. The skill provides optional [charter, task, review, and handoff templates](coordinate-project-agents/references/templates.md); adapt them to the actual project rather than treating them as mandatory forms.

For each deliverable, keep the base and head revisions explicit. Separate an external agent's claims from checks you ran yourself, and distinguish code review from integration and release acceptance. Share redacted evidence when a collaborator cannot access a private repository or service.

## Boundaries

Do not put API keys, private code, paid data, runtime caches, or conversation transcripts into public briefs or repositories. Confirm authorization before merging, deploying, or sending content to an external service.

