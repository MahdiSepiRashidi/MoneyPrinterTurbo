## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Trello task board

Task tracking for the IG Reel Agent project lives on Trello: "IG Reel Agent — Backlog"
(board ARI `ari:cloud:trello::board/workspace/61518eec263c130f81128e52/6abe2db909db2e4a0eeb2fed`,
https://trello.com/b/C3cabZHA/ig-reel-agent-backlog). Lists: Resolve First, Epic A: Foundation,
Epic B: Content, Epic C: Media, Epic D: Post & Ship, F-1: Final Validation.

Rules:
- Before starting any task work (R-x, FR-x, P-x, F-x), check the Trello card first: find it via `trelloSearch` (search_cards) or list the relevant list with `trelloReadCard` list_by_list, then `trelloReadCard` action=get on the card. Its description (steps + "Done when" checklist) is the source of truth — it can be more detailed or more recent than the in-repo `plan/*.md`.
- Do task work per the card description; treat the card's "Done when" checklist as acceptance criteria.
- In-repo `plan/2026-09-29-ig-reel-agent/plan.md` remains the architectural reference; when a card and plan conflict, follow the card and note the discrepancy.
