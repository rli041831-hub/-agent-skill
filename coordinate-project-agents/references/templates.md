# External Agent Collaboration Templates

Fill bracketed fields from the actual project. Each task message must stand alone when pasted into another tool.

## Project charter

```markdown
# [Project] collaborative development

Goal: [Product outcome]
Repository or shared workspace: [URL/path]
Stable base: [Branch and commit, or other version identifier]
Current blockers: [Issue/PR, owner, required fix]
Product decision owner: [Person]
Integration owner: [Person/agent]
Independent reviewer: [Person/agent]

| Work area | Agent/tool | Owned files/interfaces | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| [Area] | [Name/tool] | [Scope] | [Input] | [Test and real flow] |

Shared contracts: [Version, owner, consumers, change notice]
Shared files: [Edit owner and integration order]
Isolated runtime: [Test data, ports, databases, secrets handling]
Required checks: [Exact commands]
End-to-end flow: [User action through relevant modules]
Return channel: [PR, branch, files, or message relayed by user]
```

## Message to send to one external agent

```markdown
You are responsible for [area] in [project]. This message contains the complete task context; do not rely on earlier chats.

Repository/workspace: [URL/path and access method]
Read first: [Project instructions and relevant docs]
Base revision: [Exact branch and commit]
Your branch/output: [Unique branch and PR target, or file delivery]

Goal: [Observable result]
Edit scope: [Owned files/modules]
Shared files: [Owner and coordination method]
Dependencies: [Upstream branch/contract/status]
Data contract: [Version, fields, errors, missing data, time/ID semantics]
Constraints: [Project-specific data/security/product boundaries]

Acceptance:
1. [Focused tests with commands]
2. [Real flow with expected result]
3. [Failure/restart/permission case where relevant]

Return: [Link or path, commit, changed files, test results, real-flow evidence, known gaps, contract changes]
If blocked: state the exact missing input and continue independent work within scope.
Do not merge into the integration or release branch yourself unless explicitly assigned.
```

## Returned handoff

```markdown
Task and owner: [Identifier]
Deliverable and exact revision: [PR/branch/commit or files]
Base revision: [Reference]
Changed files and contract: [List/version]
Checks run: [Commands, counts, environment]
Real-flow observation: [Action and actual result]
Unverified items or failures: [List]
Data/security: [Where runtime data and secrets stayed]
Integration dependencies: [What must land first; shared-file conflicts]
Reviewer result: [Approved, changes requested, or blocked, with evidence]
```

## Independent review brief

```markdown
Review [PR or artifact URL] at exact revision [SHA/version] against [base revision].
For a re-review, the last reviewed revision is [SHA/version]; its findings and open acceptance items are [links/summary].
Read [project instructions] and [contract]. On a first review inspect the complete change; on a re-review inspect the new delta and affected paths, including generated or configuration files where relevant.

Check: [observable user flow], [data/permission boundaries], [failure and recovery cases], [compatibility], [secrets and runtime data].
Run focused checks for the new delta: [exact commands]. Record current CI for the full suite; repeat broader local checks if the baseline, changed interfaces, or risk requires it. Compare any failures with equivalent checks on the base before labeling them pre-existing.
Verify open real-environment gates: [API/browser/service scenario and expected result]. Do not substitute a fixture or unit test for this item.

Return findings first with severity, file and line, risk, and reproduction. Then separate prior evidence carried forward, checks performed now, external claims, and remaining unverified items; include exact revisions, commands, counts, and environment differences.
Do not merge or publish without explicit authorization. If review permissions are unavailable, return the report for relay; do not claim a GitHub review was submitted.
```

