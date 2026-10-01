# Backlog

Create a Trello backlog from a project's spec + plan documents.

## When to use
- User says "create a backlog", "make Trello cards from the plan", "turn the spec into a Trello board"
- A spec.md + plan.md (or equivalent) exist in the repo and the user wants a tracking board

## Inputs
- **Spec**: `intent/<date>-<project>/spec.md` (or similar) — functional requirements, data model, API contracts
- **Plan**: `plan/<date>-<project>/plan.md` (or similar) — resolution items, epics, features, order of work, risks, proofs
- **Intent** (optional): `intent/<date>-<project>/intent.md` — original problem statement

## Workflow

### 1. Ask the user
Before creating anything, ask:
- **Board structure**: "By Epic" (lists per epic + a Resolve First list + POCs in their epics) vs "By Workflow" (To Do / In Progress / Done with labels)
- **Card granularity**: "FR + R + Proof" (one card per FR, per R, per P/F — recommended) vs "Sub-tasks" (one card per checklist item in the plan)
- **Board name**: default = `<Project> — Backlog`
- **Target workspace**: list the user's workspaces, ask which to use (or create in default)

### 2. Create the board
- `trelloWriteBoard` action=create, name, workspaceId
- Capture the returned board ARI

### 3. Create lists
From the plan's structure:
- **"Resolve First"** — for all R-items (decision items, zero code)
- **One list per epic** — e.g. "Epic A: Foundation", "Epic B: Content", etc.
- **POCs go INTO their epic's list** — P-2 (encode POC) belongs in the epic it gates (e.g. Epic C for FR-9); P-1 (Meta POC) belongs in the epic it gates (e.g. Epic D for FR-11). Only truly final validation (F-1) gets its own last list.
- Create lists one at a time (no `pos` param on create). Then reorder: move "Resolve First" to `top`, move each epic in sequence, move the final list to `bottom`.

### 4. Create cards
One card per FR, R, P, or F item. **Every card description follows this template:**

```
**Goal:** <one-line summary of what this achieves + which spec FR/R/OQ it maps to>

**Steps:**
1. <concrete, numbered, actionable step with file paths and line refs from the plan>
2. <next step>
...

**Done when:**
- [ ] <observable acceptance criterion 1>
- [ ] <observable acceptance criterion 2>
- [ ] <all tests pass / command succeeds / etc.>
```

Rules:
- **Goal** is one line, references the FR/R/OQ number.
- **Steps** are numbered, concrete (file paths, function names, config keys, API endpoints from the plan). No vague "implement X" — say exactly which file, which function, which line.
- **Done when** is a checkbox list of observable, verifiable criteria. At least 3 items. Include "all tests pass" as the last item for code tasks.
- Card name format: `<ID>: <short title>` e.g. `FR-14: Pluggable config-driven LLM layer`, `R-3: Font — Add Vazirmatn TTFs to resource/fonts/`, `P-1: Meta / external POC`. Keep names under 80 chars.

### 5. Ordering within lists
Cards within each list should follow the plan's "Order of work" section. Within a single epic, order by the step number they appear in.

### 6. Verify
- `trelloReadBoard` action=get on the board — confirm all lists and card counts.
- Report the board URL to the user.
- Note any column ordering issues the user should fix by dragging in the Trello UI.

## Card count heuristic
| Plan element | Cards |
|---|---|
| Each R-item (R-1 … R-N) | 1 card in "Resolve First" |
| Each FR (FR-1 … FR-N) | 1 card in its epic |
| Each proof (P-1, P-2, …) | 1 card in the epic it gates |
| Final flow test (F-1) | 1 card in its own last list |

Typical range: 25–45 cards for a medium project.

## Pitfalls
- `trelloWriteList` create does NOT accept `pos` as a number — only omit it or use "top"/"bottom" on move.
- `trelloWriteCard` create requires `listId` + `name`; `desc` is optional but always include it.
- POC cards must NOT go in a generic "Proof" list at the end — they gate specific epics and belong there.
- Card names with special chars (→, —, ×) are fine in Trello.
- The Trello API's list position system is float-based; `top`/`bottom` work but arbitrary numbers may fail validation.
- Create cards one at a time with named parameters (not JSON blobs). The `action` param must be passed as a separate field, not embedded in a JSON string.
- Batch 2-3 card creates/updates in parallel for speed, but don't exceed that (Trello rate limits).
