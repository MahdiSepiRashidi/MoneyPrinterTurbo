# Spec: Farsi Instagram Reel Generation Agent (MoneyPrinterTurbo)
**Source intent:** intent.md (2026-09-29, مکتب جاذبه)
**Status:** approved
**Spec version:** 1

## 1. Problem Summary

مکتب جاذبه needs a self-hosted agent that produces one Farsi Instagram Reel per day on the MoneyPrinterTurbo (MPT) pipeline, sourcing content from books via LLM-extracted "idea cards," and posts it automatically through the official Meta Graph API. The operator stays hands-on only for the daily card pick and the script text (via a Telegram bot); everything after script approval is automated. "Better" means: a repeatable, near-zero-cost daily reel that grows a dedicated professional account while keeping a human on the text (speed) and only escalating to a human when posting fails.

## 2. Requirements

### 2.1 Functional

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| FR-1 | Ingest a book (plain text) into idea cards via a one-time LLM pass | Given sample book text, `python -m supervisor ingest-books <file>` emits cards `{id, book, claim, quote, example}` to the JSON store; ≥1 card per meaningful passage; re-running is idempotent (no duplicate ids) |
| FR-2 | At 08:00 Tehran, send the operator 5 unused idea cards over Telegram | Operator receives exactly 5 cards (id + claim) at 08:00; operator may reply with a number 1–5 to lock the pick; pick is recorded on the card (`status: picked`) |
| FR-3 | Fallback pick when the operator does not choose | If no reply by 18:00 Tehran (weekday) / 12:00 (Friday), the supervisor selects one of that day's 5 at random and proceeds; choice logged as `picked_by: fallback` |
| FR-4 | Generate the Farsi reel script from the picked card using `skills/meta-safe-farsi-reel-script` | Output JSON has `status` in {ok, needs_review}, 150–220 Farsi words, `hook_type` matches the rotated value, `self_check.flags` empty when `passed:true`, and the Farsi text passes the TTS-readiness check (correct diacritics/ZWNJ/punctuation — FR-17); scripts failing self-check are routed to human review, not auto-posted |
| FR-5 | Script approval gate (text only, via Telegram) | The video is built only after the operator replies `approve`; `rewrite` regenerates the script; no video is generated before approval |
| FR-6 | Farsi TTS narration via a pluggable provider | Narration MP3 duration is within 60–90s for a 150–220-word script; TTS consumes the TTS-ready normalized script (FR-17); provider is switchable in config without code change |
| FR-7 | Daily background music from the Pexels audio API | Final video has a music bed mixed under narration at low volume; the track id is logged and not reused on the next day |
| FR-8 | Pexels footage that is semantically fit, 30-day deduplicated, and avoids top-download staples | Selected clips are LLM-ranked against script scene terms; no `pexels_asset_id` appears in the last 30 days of `ClipUsageLog`; high-download staples are filtered/suppressed |
| FR-9 | Assemble the reel | Final MP4 is 1080x1920 (9:16), 60–90s, burned Farsi subtitles, ~4 Mbps (CRF 22–23, cap 4.5 Mbps), file size ≤ 48 MB |
| FR-10 | Farsi caption + 3–5 hashtags + one soft CTA | Caption is Farsi, 1–2 lines, exactly one follow+bio CTA, 3–5 hashtags (Farsi-first), not a verbatim repeat of the narration |
| FR-11 | Post via the official Meta Graph API on schedule | Reel is scheduled/published at 20:00 Tehran (weekdays) / 14:00 (Friday) via `ig_user_reels` for a professional account; only official Meta endpoints are used (no unofficial IG libraries) |
| FR-12 | Manual fallback on post failure | If the Graph API call fails after retries, the exact video file (<48 MB) + caption are sent to the operator via Telegram for manual posting; run marked `post_status: manual` |
| FR-13 | Failure policy | Per-stage retry with backoff → cheap-model fallback → Telegram notification only when the day is actually missed → a manual-resume command continues from the last checkpoint |
| FR-14 | Pluggable, config-driven LLM layer | Provider/model is switched by editing config only (1–2×/month); starting provider is `agnes-3.0-flash`; a cheap fallback model is used when the free model fails |
| FR-15 | Telegram bot is the sole operator surface | The full operator workflow (card pick, script approval, manual post) is completable entirely through the Telegram bot |
| FR-16 | Ship as a Docker image (pipeline + supervisor + Telegram bot) | A single image runs the MPT pipeline, the supervisor, and the Telegram bot; works on CPU-only Linux in production and Docker Desktop on Windows for dev |
| FR-17 | TTS-ready Farsi text normalization | Generated script + caption are normalized for TTS: correct Farsi diacritics (harakat/shadda/sukun on ambiguous words), correct ZWNJ/half-space, and punctuation tuned for prosody; a validator check passes (required ZWNJ words joined, ambiguous tokens diacritized, punctuation density in range) before TTS |

### 2.2 Non-Functional

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Cost | Completely free stack; cheap-model fallback only where the free model does not work |
| NFR-2 | Cadence | Exactly 1 Reel per day |
| NFR-3 | Media budget | 9:16 1080p, 60–90s, ~4 Mbps, ≤ 48 MB per Reel (fits the 50 MB Telegram Bot API upload limit) |
| NFR-4 | Runtime | CPU-only 24/7 Linux host; free services (e.g. Google Colab) may host models as external providers |
| NFR-5 | Security | Official Meta Graph API only; credentials live in `config.toml` (never committed); TLS verified; Telegram/Meta tokens stored server-side |
| NFR-6 | Compliance | All content obeys `meta-safe-farsi-reel-script` tone guardrails (no PUA, no guarantees, no sexual framing, no engagement bait) and anti-spam variety (rotating hooks, 7-day no-repeat, 3–5 Farsi-first hashtags) |
| NFR-7 | Localization | All generated content is Farsi and TTS-ready: correct diacritics (harakat on ambiguous words), correct ZWNJ/half-space, and appropriate punctuation so the TTS engine pronounces and pauses accurately |
| NFR-8 | Resilience | Supervisor is restartable and resumes from checkpoint; failures are observable via Telegram |

## 3. Data Model

New entities (JSON files under `storage/`); all reference the MPT pipeline only through its existing `VideoParams` + task state.

```
Entity: IdeaCard            (new, storage/idea_cards.json)
Fields:
  - id: str (uuid, PK)
  - book: str
  - claim: str
  - quote: str
  - example: str
  - status: enum{unused, picked, used, needs_review}
  - picked_date: date|null
  - run_id: str|null        (DailyRun that consumed it)
Relationships: belongs_to DailyRun (when picked/used); has_one

Entity: DailyRun            (new, storage/daily_runs.json — supervisor checkpoint)
Fields:
  - run_id: str (PK)
  - date_tehran: date (unique per day)
  - candidate_card_ids: [str]      (5)
  - picked_card_id: str|null
  - picked_by: enum{operator, fallback}|null
  - hook_type: enum{question, myth, story, stat}
  - script_status: enum{pending, approved, rejected, needs_review}
  - narration_file: path|null
  - video_file: path|null
  - caption: str|null
  - hashtags: [str]
  - post_status: enum{not_scheduled, scheduled, posted, failed, manual}
  - scheduled_time_tehran: timestamp
  - checkpoint: enum{cards_picked, script_approved, video_built, posting, posted}
  - retry_count: int
  - last_error: str|null
Relationships: has_one IdeaCard (picked); has_one PostJob (Meta call state)

Entity: ClipUsageLog        (new, extends MPT material cache, 30-day retention)
Fields:
  - pexels_asset_id: str
  - used_date: date
  - run_id: str
Constraints: dedup source for FR-8; prune rows older than 30 days

Entity: HookRotationLog     (new, last-7 window)
Fields:
  - date_tehran: date
  - hook_type: enum
  - opening_line: str
Constraints: supplies `recent_hooks` to FR-4; 7-day no-repeat

Entity: MusicUsageLog       (new, extends BGM service)
Fields:
  - pexels_audio_track_id: str
  - used_date: date
```

## 4. API Contracts

The operator interface is Telegram, not HTTP. MPT's existing FastAPI surface (`/api/v1/video`, `/api/v1/llm`) is **not** the operator channel; the supervisor invokes the pipeline in-process. Outbound contracts below.

```
A) Meta Graph API (outbound, official only)
   Auth:  Bearer long-lived IG user token (FB app → Page → professional IG account)
   A1. POST /v19.0/{ig-user-id}/media
        { "media_type": "REELS", "video_url": "<cdn url of final mp4>", "caption": "<fr-10>" }
        201 -> { "id": "<container>" }
   A2. POST /v19.0/{container}/published_media
        { "creation_id": "<container>", "publish_time": "<scheduled unix ts, if tier supports>" }
        200 -> { "id": "<published media>" }
   A3. GET  /v19.0/{media-id}?fields=status_code  ->  "posted"|"PUBLISHED"|"SCHEDULED"
   Errors: 190 short-lived token (refresh needed); #2000 invalid params;
           1/200 permission; 4 rate-limited. See open question OQ-7 (token refresh).

B) Telegram Bot API (outbound + inbound)
   Auth:  Bot token (server-side)
   B1. POST /bot<T>/sendMessage   { chat_id, text }            -> shortlist / script / alerts
   B2. POST /bot<T>/sendVideo     { chat_id, video(<48MB), caption } -> FR-12 manual fallback
   B3. GET  /bot<T>/getUpdates    (long-poll or webhook)        -> operator replies ("3", "approve")
   Errors: 429 retry_after; 400 bad request; network -> FR-13 retry/backoff

C) Pexels Audio (outbound, same key as Pexels video)
   C1. GET https://api.pexels.com/audio/search?query=<mood>&per_page=10   (Authorization: key)
        200 -> { "tracks": [ {id, ...} ] }; 401 bad key; 429 rate-limited
```

## 5. UX / UI Design

The operator "UI" is the Telegram bot. There is no consumer-facing UI in scope. Journey:

- **08:00 Tehran** — entry point: bot sends 5 numbered unused idea cards (id + claim). Operator replies with a number (1–5). Empty state: if <5 unused cards, bot sends a warning + however many exist and a request to ingest more books.
- **After pick (~18:00 weekday / ~12:00 Friday, or on fallback)** — bot sends the Farsi script text. Operator replies `approve` / `rewrite` / `reject`. `needs_review` scripts (self-check fail) are flagged for explicit human review before build.
- **On approval** — loading state: bot confirms "building." Reel is scheduled/published at 20:00 (weekday) / 14:00 (Friday). Confirmation: "posted to @handle" with the media id.
- **On post failure** — error state: bot sends the video file + caption for manual posting (FR-12).
- **Edge states** — loading (script/build in flight), error (retry → cheap fallback → notify), empty (no unused cards), needs_review (guardrail self-check failure).

All bot copy is Farsi. No WebUI work is required (see Out of Scope).

## 6. AI / Agent Feature Design

The intent mandates **plain pipeline + a small Python supervisor; no agent framework.** Each AI step below is a single-shot LLM call with bounded retries inside the deterministic pipeline, not a multi-step tool-calling loop.

```
Feature: A) Idea-card extraction (book -> cards)   [FR-1]
Capability: one-time LLM pass converts book passages into {claim, quote, example} cards
Agent loop:
  - Tools: LLM chat-completions (provider from FR-14, default agnes-3.0-flash)
  - Context: book text chunk; instruction to emit strictly one JSON array of cards
  - Termination: single pass over chunks; stop when all chunks processed; no agent loop
Prompt strategy:
  - System: "Extract atomic idea cards. Each = one claim + supporting quote + concrete
    example. Output a JSON array only. Do not invent content."
  - User: book chunk
  - Few-shot: yes — 2 example cards from a sample domain
Fallback:
  - Model unavailable: retry w/ backoff -> cheap fallback model -> notify; abort card run
  - Malformed output: JSON-validate; reject chunk and log; never persist unvalidated cards
  - Escalation: card content that violates guardrails -> status needs_review (human)

Feature: B) Daily candidate picker (5 unused cards)   [FR-2/FR-3]
Capability: sample/rank 5 unused cards for the day
Agent loop:
  - Tools: LLM optional ranking over unused cards; default = uniform random (no agent)
  - Context: unused cards + last-7 topics (variety signal)
  - Termination: single call (or deterministic random); stop at 5
Prompt strategy:
  - System: "Return 5 unused cards most relevant + diverse for today. JSON ids only."
  - User: unused card ids + recent topics
  - Few-shot: no
Fallback:
  - LLM ranking fails -> uniform random from unused; never block the day
  - <5 unused -> send available + ingest warning

Feature: C) Farsi reel script generation   [FR-4, FR-17; governed by skills/meta-safe-farsi-reel-script]
Capability: produce the narration + caption + hashtags JSON for the picked card, TTS-ready
Agent loop:
  - Tools: LLM (default agnes-3.0-flash); the skill's guardrails + a TTS-readiness check run as self-checks
  - Context: picked idea card; rotated hook_type; recent_hooks (last 7 opening lines)
  - Termination: single call; if self_check.passed==false or flags non-empty (incl. diacritics/
    punctuation failures) -> needs_review (human), do NOT auto-post; at most 1 rewrite on `rewrite`
Prompt strategy:
  - System: the full SKILL.md body (tone guardrails, structure, anti-spam, Farsi rules) PLUS:
    emit TTS-ready Farsi — correct diacritics (harakat on ambiguous words), correct ZWNJ/half-space,
    and punctuation tuned for prosody (FR-17)
  - User: card + hook_type + recent_hooks
  - Few-shot: yes — one TTS-ready sample script showing correct diacritics + punctuation
Post-step: TTS-readiness validator normalizes/diacritizes the text before TTS; mechanism (LLM-only
  vs a dedicated Farsi diacritization post-step) is open — see concern #9 / OQ-9
Fallback:
  - Model unavailable: retry -> cheap fallback model -> mark script failed, notify
  - Malformed/needs_review or TTS-readiness check fails: route to operator for human review; never auto-post
  - Escalation: any guardrail or TTS-readiness flag -> human

Feature: D) Semantic clip selection (Pexels footage)   [FR-8]
Capability: rank Pexels candidates so footage fits the scene, dedups 30 days, avoids staples
Agent loop:
  - Tools: Pexels video search + LLM ranking of returned clips vs. script scene terms
  - Context: script-derived terms; candidate clip metadata (title/desc/duration)
  - Termination: rank top candidates, stop at required clip count; drop ids in ClipUsageLog
  - Few-shot: no
Fallback:
  - LLM ranking fails -> keyword match (existing MPT behavior); still enforce 30-day dedup
  - No clean clips -> retry search w/ alternate terms -> notify if day at risk
```

TTS narration (FR-6) is a pluggable provider call, not an agent loop: provider interface mirrors MPT's `voice.py` dispatch; Farsi voice selection is deferred to an audition (open question OQ-1). Pexels BGM (FR-7) is a deterministic fetch + ffmpeg mix, no AI.

## 7. Flagged Concerns

| # | Title | Severity | Conflicting Policies | Owner | Status |
|---|-------|----------|---------------------|-------|--------|
| 1 | Reels scheduling via `publish_time` may be unavailable for the app's access tier; if not, fall back to triggering the build just before 20:00/14:00 and posting immediately | blocker | NFR-5 (official API only) vs uncertain Meta API capability | Tech Lead + Meta app reviewer | open |
| 2 | `ig_user_reels` for a professional account may require Meta app review / business verification; can block the free self-serve launch | blocker | NFR-1 (free) vs Meta review/compliance | Compliance + Meta reviewer | open |
| 3 | Free LLM (agnes-3.0-flash) Farsi + ZWNJ correctness unverified; guardrail compliance may need a stronger/cheap model | warning | NFR-1 (free) vs content quality/compliance | Tech Lead | open |
| 4 | Free Farsi TTS quality unverified (audition deferred); a quality voice may require a paid provider | warning | NFR-1 (free) vs audio quality | Product | open |
| 5 | Stable non-Iran relay for Meta egress may be a paid service, conflicting with "completely free" | warning | NFR-1 (free) vs NFR-5 egress policy | Ops | open |
| 6 | Google Colab free-tier runtime/persistence limits vs daily scheduled external-model use — needs verification | info | NFR-4 (free hosting) vs reliability | Tech Lead | open |
| 7 | Residual Meta demotion risk after the meta-safe guardrails; monitor Insights 2–4 weeks | info | NFR-6 (anti-spam) vs automation | Product/Brand | open |
| 8 | Pexels Audio API availability + CC0 license + daily variety not yet confirmed | info | NFR-1 (free music) | Tech Lead | open |
| 9 | Diacritization mechanism (FR-17): rely on the LLM to emit correct Farsi harakat/ZWNJ, or add a dedicated Farsi diacritization post-step before TTS; free-LLM diacritic accuracy is unverified and directly affects TTS quality | warning | NFR-1 (free) + NFR-7 (TTS-ready quality) | Tech Lead | open |

**Severity:** blocker = cannot build until resolved; warning = build may proceed with documented risk; info = awareness only.

## 8. Governance & Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Product Owner | مکتب جاذبه | approved | |
| Tech Lead | | approved | |

## 9. Open Questions (Carried Forward)

From intent.md, accepted to carry into Build (surface in plan mode):
- OQ-1 Which Farsi TTS voice/provider passes the audition and is adopted.
- OQ-2 Farsi font choice for burned subtitles.
- OQ-3 State of the link-in-bio landing page and the educational packages.
- OQ-4 Channel handle (decided at account registration).
- OQ-5 Google Colab free-tier runtime/persistence limits vs daily scheduled use.
- OQ-6 Residual demotion risk after the skill's guardrails (monitor 2–4 weeks).
- OQ-7 Long-lived access-token refresh flow for the Graph API (who re-authenticates).
- OQ-8 IP egress policy for the machine calling Meta APIs (stable non-Iran relay?).
- New (spec): whether the 5 daily candidates are LLM-ranked (Feature B) or uniform random — default is random, LLM ranking optional.
- OQ-9 Whether to add a dedicated Farsi diacritization post-step (rule- or model-based) before TTS, or rely on LLM-emitted diacritics (ties to concern #9 and FR-17).

## 10. Out of Scope

Explicitly NOT in this spec (prevent build-time scope creep):
- Any WebUI changes; the operator surface is Telegram only.
- More than 1 Reel/day; non-Farsi content; landscape/other aspect ratios.
- AI-generated video or digital avatars (paid — excluded by the free constraint).
- Unofficial Instagram libraries; paid models except the documented cheap fallback.
- Implementing the TTS audition (deferred); selling/checkout of educational packages; the landing page.
- Multi-channel/multi-account posting.
