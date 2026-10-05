# MoneyPrinterTurbo + IG Reel Agent — Operator Runbook

One runbook for the whole project. MoneyPrinterTurbo (MPT) is the underlying
video engine; the **supervisor** is the operator-facing "IG Reel Agent" that
turns a book into daily Farsi reels and auto-posts one. This runbook covers
setup, every entry point, configuration, data layout, deployment, and
recovery — and marks clearly what is **live** vs. **in build** today.

> Status legend: **[LIVE]** = works now · **[POC]** = built + verified, not
> yet in the daily loop · **[BUILD]** = planned/stub, not runnable end-to-end.
> Architecture detail lives in `plan/2026-09-29-ig-reel-agent/plan.md`.

---

## 0. System map

```
                 +-------------------------------------------+
                 |  Base MPT (video engine)                  |
                 |  - WebUI (Streamlit, :8501)   [LIVE]      |
                 |  - API   (FastAPI/uvicorn, :8080) [LIVE]  |
                 |  - CLI   (cli.py, no browser)   [LIVE]    |
                 +-------------------+-----------------------+
                                       | drives stage fns
                 +---------------------v-----------------------+
                 |  Supervisor (IG Reel Agent)                |
                 |  - FR-1 ingest book->cards      [LIVE]     |
                 |  - supervisor/llm.py (Agnes+Gemini)[LIVE]  |
                 |  - Buffer post client + POC     [POC]      |
                 |  - media chain (R-10)           [POC]      |
                 |  - daily loop + Telegram bot    [BUILD]    |
                 +--------------------------------------------+
```

---

## 1. Environment setup

Requirements: Python **3.11+**, `uv`, and **FFmpeg** on PATH.

```
# 1. clone + enter
git clone <repo> MoneyPrinterTurbo
cd MoneyPrinterTurbo

# 2. environment (uv is the primary tool; uv.lock pins everything)
uv python install 3.11
uv sync --frozen

# 3. config
cp config.example.toml config.toml    # Windows: copy config.example.toml config.toml
#   then edit config.toml (keys in §6). Secrets live here ONLY (NFR-5) — never commit.
```

Legacy `pip` fallback: `python3.11 -m venv .venv && pip install -r requirements.txt`.

Verify: `uv run python -X utf8 -c "import app, supervisor; print('ok')"`.

> `-X utf8` is used throughout on Windows to avoid the legacy console codepage
> killing UTF-8/Farsi output (see `cli.py` `_force_utf8_console`).

---

## 2. Base MPT — generate a video three ways

All three share the same pipeline (`app/services/task.py`): script → terms →
audio → subtitle → materials → video. Pick whichever surface you need.

### 2.1 WebUI [LIVE]

```
# Windows
.\webui.bat
# macOS / Linux
sh webui.sh
```

Browser auto-opens at http://127.0.0.1:8501. For LAN access:
`set MPT_WEBUI_HOST=0.0.0.0` (Win) / `MPT_WEBUI_HOST=0.0.0.0 sh webui.sh`.

### 2.2 API service [LIVE]

```
uv run python main.py
# -> http://127.0.0.1:8080/docs  and  /redoc
```

### 2.3 Pure CLI [LIVE]

```
uv run python cli.py --video-subject "How AI is changing everyday life"
uv run python cli.py --help                       # full flag reference
uv run python cli.py --batch-file ./tasks.json --stop-at video   # many tasks
```

Settings resolve as: explicit CLI flag > saved `[ui]` value > built-in default.
A generation settings change made in the WebUI does **not** carry to the CLI.

Output lands in `storage/tasks/<task_id>/` (final MP4s under that dir).

---

## 3. Supervisor — the Reel Agent

Supervisor commands run as `uv run python -X utf8 -m supervisor <cmd>`.

### 3.1 Ingest a book into idea cards (FR-1) [LIVE]

Turns a book (PDF or plain text) into **teachable** idea cards in
`storage/idea_cards.json`. One-time, idempotent, quota-resumable.

Each card is a **generalizable, actionable lesson** (`claim` + `quote` +
`example` + a one-line `lesson` + a `type` of `principle|tip|insight`).
**Quality gate:** the LLM is told to return `[]` for scene/plot/anecdote
content, and any card whose `lesson` is empty/vague is **dropped** (never
persisted) — so non-educational chunks don't become cards. Cards stay in the
book's language; FR-4 translates them to Farsi.

```
uv run python -X utf8 -m supervisor ingest-books \
  "contents/The-Game-Neil-Strauss-bMRpEc6o_SciOne.ir.pdf" --book "The Game" --max-chunks 50
```

- Chunking starts at character 0, so **no page is ever dropped**; a chunk with
  nothing teachable just returns an empty array `[]` → zero cards (by design).
- **Auto-resume:** progress is checkpointed per book in
  `storage/ingest_progress.json`. Re-run the *same* command and it continues
  from the last answered chunk — no `--from-chunk` needed. A hard LLM `Error:`
  does not advance the checkpoint, so it is retried next run.
- `--max-chunks N` caps LLM calls per run for quota control. `--from-chunk N`
  forces an explicit start. Fully-ingested books are a no-op.
- **Refused chunks (`--skip-chunk N`):** if a chunk's content trips the LLM
  safety filter, both Agnes and Gemini return *empty text* (`Error: [gemini]
  returned empty text content`). That is a **permanent** refusal, not quota —
  auto-resume will keep re-trying it forever. Skip it:
  ```
  uv run python -X utf8 -m supervisor ingest-books "contents/…pdf" --book "The Game" --skip-chunk 49 --max-chunks 50
  ```
  The index is the 0-based one shown in the progress log. Skips are recorded in
  the progress row (`skipped_chunks`), the checkpoint advances past them, and
  the rest of the book continues. Re-ingest a skipped chunk later with
  `--from-chunk N --max-chunks 1`.
- **The Game ≈ 329 chunks ≈ 329 LLM calls.** Batch in ~50s: ~7 batches.
  The book contains explicit sexual content; expect several refused chunks to
  skip (e.g. chunk 49) as you go.
- LLM: Agnes primary (free, 512K context) → one Gemini fallback attempt.
- Verify counts / quality:
  ```
  uv run python -X utf8 -c "import json,os; p='storage/idea_cards.json'; c=json.load(open(p)) if os.path.exists(p) else []; m=[x for x in c if x.get('book')=='The Game']; r=[x for x in m if x.get('status')=='needs_review']; nol=[x for x in m if not x.get('lesson','').strip()]; print('cards:',len(m),'| needs_review:',len(r),'| blank-lesson(stale):',len(nol))"
  ```
  `blank-lesson` counts pre-`lesson` cards (stale, from an older contract) —
  zero them out with the re-ingest step below.
- **Re-ingest after a contract/prompt change:** card IDs are
  `sha1(book|claim|quote)`, so a stricter prompt changes the claims → new IDs
  that *coexist* with the old cards. To get a clean result, clear the book
  first, then re-run from chunk 0:
  ```
  uv run python -X utf8 -c "import json,os; p='storage/idea_cards.json'; c=json.load(open(p)) if os.path.exists(p) else []; open(p,'w').write(json.dumps([x for x in c if x.get('book')!='The Game'],ensure_ascii=False,indent=2)); print('cleared The Game cards')"
  uv run python -X utf8 -c "import json,os; p='storage/ingest_progress.json'; r=json.load(open(p)) if os.path.exists(p) else []; open(p,'w').write(json.dumps([x for x in r if x.get('book')!='The Game'],ensure_ascii=False,indent=2)); print('cleared The Game progress')"
  ```
  Then run the batched `--max-chunks 50` command again (auto-resume now starts
  at chunk 0). This is what to do when the FR-1 extraction contract (e.g. the
  `lesson`/`type` quality gate above) is tightened.
- The run summary prints `Vague cards dropped` (cards whose `lesson` was empty/
  short and were not persisted). A high number means many chunks had nothing
  teachable — expected for a narrative book.
- `needs_review` cards (a blank `claim`/`quote`/`example`) stay in the pool
  flagged for manual review before FR-2 picks from them.

### 3.2 Daily pipeline (FR-2 → FR-12) [BUILD / POC parts]

The intended daily job: pick 5 unused cards → generate a Farsi TTS-ready
script → **operator approves via Telegram** → build the reel (TTS/subtitles/
footage/BGM/encode) → post via Buffer → mark card used.

Current state:

| Piece | Module | Status |
|---|---|---|
| Card pick + run creation | `supervisor/daily.py` `create_daily_run()` | implemented, persists via `DailyRunStore` |
| 08:00 pick job (Telegram delivery) | `supervisor/daily.py` `run_pick_job` + `supervisor/telegram_client.py` | [LIVE] |
| Pipeline runner w/ retry+backoff+checkpoint | `supervisor/flow.py` `run_pipeline`, `resume_run` | implemented |
| Media chain (audio→sub→materials→video) | `app/services/task.py` stage fns | verified via `supervisor/r10_check.py` |
| Post via Buffer | `supervisor/buffer.py` | [POC] |
| Scheduler (08:00 pick, deadlines, build+post) | `supervisor/scheduler.py` | implemented, wired into `serve` |
| Telegram operator surface (approve/rewrite/reject) | `supervisor/telegram_bot.py` | **not built** (outbound `send_message`/`send_video` live via `telegram_client.py`) |

There is **no automatic 1-5 reply receiver** yet (that is FR-15's long-poll
loop); the manual `pick-send` / `lock-pick` bridge below closes the loop
for now. Until the full bot lands, media + posting can be exercised via the
POC and `r10_check.py` below.

### 3.3 Resume a stuck daily run (FR-13) [LIVE]

```
uv run python -X utf8 -m supervisor resume <run_id>
```

Loads the `DailyRun`, continues from its `checkpoint`, re-running the current
stage. Prints checkpoint / post_status / last_error. Run ids come from
`storage/daily_runs.json`.

### 3.4 Serve (scheduler + bot) [BUILD]

```
uv run python -X utf8 -m supervisor serve
```

Runs the in-process scheduler (08:00 Tehran pick job) and the Telegram bot.
The pick job (FR-2) is now live: it fires at 08:00 Tehran (07:00 Friday),
picks 5 unused cards, marks them `picked`, persists the `DailyRun`, and sends
the numbered Farsi shortlist to the operator via `telegram_client`. The full
command bot (FR-15) is still in build. Requires `telegram_bot_token` +
`telegram_chat_id` in `[supervisor]` to do anything useful.

### 3.5 Manual daily cycle: pick → send → lock (FR-2 bridge) [LIVE]

The full Telegram command bot (auto 1-5 receiver, approve/rewrite/reject) is
FR-15's build. Until it lands, this two-step bridge drives the pick +
operator choice from the CLI, with the delivery and locking done for real:

```
# 1. create today's run, send the numbered 5-card shortlist to Telegram
uv run python -X utf8 -m supervisor pick-send

# 2. read the cards in your chat, then lock the pick (1-5 = the number shown)
uv run python -X utf8 -m supervisor lock-pick <run_id> <1-5>
```

- `pick-send` runs `run_pick_job()`: picks 5 unused cards, marks them
  `picked`, persists the `DailyRun` (`checkpoint = cards_picked`), and sends
  the Farsi numbered list via `telegram_client` (honors `[proxy]`). It prints
  the `run_id`. With <5 unused cards it sends however many exist plus an
  "ingest more books" warning.
- `lock-pick <run_id> <n>` runs `lock_pick()`: sets
  `picked_card_id` = the nth candidate, `picked_by = "operator"`, persists.
  The checkpoint stays `cards_picked`; FR-5's `approve` is what advances it.
- Run ids come from `storage/daily_runs.json`. Invalid number / unknown run
  → the command errors and nothing is changed.

You can also inspect state directly:

```
# today's run
uv run python -X utf8 -c "import json,os; p='storage/daily_runs.json'; print(json.load(open(p)) if os.path.exists(p) else [])"
# how many unused cards are left
uv run python -X utf8 -c "import json,os; c=json.load(open('storage/idea_cards.json')); print('unused:', sum(1 for x in c if x.get('status')=='unused'))"
```

### 3.6 Buffer post POC [POC]

Non-destructive by default. List channels / create a draft / publish / check /
delete a Reel through the operator's Buffer account:

```
uv run python -X utf8 -m supervisor.buffer_poc --list
uv run python -X utf8 -m supervisor.buffer_poc --publish --content "test reel"
uv run python -X utf8 -m supervisor.buffer_poc --check <post_id>
uv run python -X utf8 -m supervisor.buffer_poc --delete <post_id>
```

Requires `[supervisor] buffer_api_key` (and optionally org/channel ids) in
`config.toml`; honors `[proxy]`.

### 3.7 Media-chain proof (R-10) [POC]

```
uv run python -X utf8 -m supervisor.r10_check
```

Runs the in-process media chain under a synthetic task id and produces a
9:16 MP4 in `storage/tasks/sup-<date>-<id>/` without touching the task
manager. Good smoke test of the reel build path.

---

## 4. Operator surface (Telegram) [PARTIAL — outbound live, reply loop BUILD]

The plan's target: a Telegram bot is the **sole** operator UI, with Farsi
replies. Two halves:

**Outbound delivery — [LIVE] via `supervisor/telegram_client.py`:**
`send_message` / `send_video` to the operator's `telegram_chat_id` (429 →
`retry_after` sleep, `[proxy]` honored). The 08:00 numbered card shortlist
(FR-2) and the manual-fallback video (FR-12) both go through it.

**Inbound reply loop — [BUILD] (`supervisor/telegram_bot.py`, FR-15).**
Full command set (to be implemented, driven by `serve`):

| Command | Effect |
|---|---|
| `1`–`5` | lock one of the day's 5 candidate cards as picked |
| `approve` | pass the script gate → build + post |
| `rewrite` | one re-generation of the script |
| `reject` | fail the day; card + candidates return to `unused` |
| `review <text>` | edit the script text before approval |
| `ack-post` | record a manual post result |
| `resume <run_id>` | continue a stuck run |
| `refresh-key <key>` | rotate the Buffer key via `save_config()` |

Until the inbound loop is built, the operator's `1`–`5` choice is made by
hand: run `pick-send` (it messages you the numbered cards), read them, then
`lock-pick <run_id> <n>` (§3.5). Everything else is done by hand today
(inspect `storage/*.json`, run `resume`, use the Buffer POC).

---

## 5. Daily timing

The 08:00 pick is live (via `serve` or manually with `pick-send`, §3.5).
The rest of the day's gates land with the scheduler loop build. All times
are Tehran (`Asia/Tehran`), computed in-process — no cron/APScheduler:

- **08:00** pick 5 cards → Telegram. **[LIVE via `serve` / `pick-send`]**
- **Pick deadline:** 18:00 weekday / 12:00 Friday (never fires twice).
- **Build** reel at 19:55 / 13:55; **post immediately** at 20:00 / 14:00
  (our-side scheduling, R-4).
- A failure past the post time raises the day-missed alert (FR-13).

---

## 6. Configuration reference

`config.toml` (copy from `config.example.toml`). Key sections:

### `[app]` — LLM + media
- `llm_provider = "agnes"` (primary, free) · `llm_fallback_provider = "gemini"`.
- `agnes_api_key` / `agnes_base_url` / `agnes_model_name = "agnes-3.0-flash"`.
- `gemini_api_key` / `gemini_model_name = "gemini-flash-latest"` /
  `gemini_tts_model_name = "gemini-3.8-flash-tts"`.
- `listen_host` / `listen_port` (API, default 8080). `[ui]` holds WebUI-persisted
  generation settings (voice, subtitle position, etc.).
- Quota note: Gemini TTS free tier is ~10 req/day and Pro-class LLM 429s.
  When TTS quota is exhausted the run fails through the FR-13 retry
  (30/120/600 s backoff) and escalates to the day-missed alert; there is
  **no** Edge-TTS fallback — the key-free `fa-IR-DilaraNeural` floor was
  rejected for quality (reversed 2026-10-04). `resume <run_id>` after the
  daily quota resets; production uses paid Gemini TTS rates.

### `[supervisor]` — the Reel Agent
Defaults come from `supervisor/config.py`. Set these in `config.toml`:
- `tts_voice = "gemini:Charon"` · `candidates_count = 5`
  (`candidates_llm_ranking = false` → uniform-random pick).
- `pick_deadline_weekday / pick_deadline_friday / post_time_weekday /
  post_time_friday` (see §5).
- **Buffer:** `buffer_api_key` (required), `buffer_base_url`,
  `buffer_organization_id` (empty = auto-resolve), `buffer_channel_id`
  (empty = first instagram channel), `buffer_reel_type = "reel"`,
  `buffer_media_host = "cloudinary"`.
- `clip_max_downloads = 10000` · `bgm_moods` · `bgm_volume = 0.2`.
- `retry_backoff_seconds = "30,120,600"` · `poll_interval_seconds = 30`.
- **Telegram (needed for the bot):** `telegram_bot_token`, `telegram_chat_id`.

### `[proxy]` — egress relay (R-7)
For networks that can't reach the internet directly, SOCKS5 relay:
`[proxy]` with a `socks5h://user:pass@host:port` URL (PySocks installed).
Buffer/Telegram/Meta egress all honor it.

### API key for MPT (LLM/TTS/footage)
Base MPT reads its provider keys from `[app]`/`[api_key]` per its own config.

---

## 7. Data & storage layout

Everything the supervisor persists is plain JSON under `storage/` (atomic
writes, file-locked):

| File | Contents |
|---|---|
| `storage/idea_cards.json` | FR-1 cards `{id,book,claim,quote,example,status,…}` |
| `storage/ingest_progress.json` | per-book ingest checkpoint (auto-resume) |
| `storage/daily_runs.json` | one `DailyRun` per Tehran date (state machine) |
| `storage/clip_usage.json` | Pexels asset ids (30-day dedup) |
| `storage/hook_rotation.json` | last-7 hook types |
| `storage/music_usage.json` | BGM track ids (no same-track next day) |
| `storage/tasks/<task_id>/` | generated reels + intermediates |
| `contents/` | source books (PDF/text) for FR-1 |

`status` lifecycle: `unused → picked → used`; `needs_review` / `rejected`
return to `unused`.

---

## 8. Deployment (Docker) [LIVE for MPT; supervisor service pending]

`docker-compose.yml` runs **webui** (:8501) + **api** (:8080) on the local
host. Variants: `docker-compose.release.yml` (prebuilt GCR image),
`docker-compose.gpu.yml` (GPU).

```
cp config.example.toml config.toml     # mount target; must exist before start
docker compose -f docker-compose.release.yml up   # or: docker compose up
```

- WebUI: http://127.0.0.1:8501 · API docs: http://127.0.0.1:8080/docs.
- `./` is bind-mounted into `/MoneyPrinterTurbo`, so `config.toml`,
  `storage/`, and `contents/` persist on the host.
- **Supervisor service (FR-16, [BUILD]):** plan adds a `supervisor` service
  (`python -m supervisor serve`, `TZ=Asia/Tehran`) to the same image/compose
  once the bot + scheduler are done.

---

## 9. Tests

```
uv run python -X utf8 -m pytest -q test          # whole suite
uv run python -X utf8 -m pytest -q test/supervisor   # just the Reel Agent
```

Branch-coverage floor is 70% (`pyproject.toml`). Run the targeted file you
touched first, then the suite.

---

## 10. Troubleshooting & recovery

| Symptom | Fix |
|---|---|
| Ingest stalls / LLM `Error:` mid-run | It's quota. Shrink `--max-chunks`, wait for the Agnes/Gemini window, re-run the same command — it auto-resumes. |
| Ingest chunk `Error: [gemini] returned empty text content` | Content the LLM refuses (explicit text), **not** quota — auto-resume re-tries it forever. Skip it: `ingest-books … --skip-chunk <index> --max-chunks 50`. It's recorded in the progress store and the run moves on. |
| Buffer `401`/`403` | Key rotated/invalid → get a fresh key in Buffer (Settings → API), update `[supervisor] buffer_api_key` (or `refresh-key` once the bot exists). |
| Buffer "Video could not be read from its URL" | The reel MP4 URL isn't publicly fetchable — the media host must be a stable public URL (`buffer_media_host`), not a signed/expiring one (R-9). |
| Reel day missed | Run `uv run python -X utf8 -m supervisor resume <run_id>`; check `daily_runs.json` `last_error`. |
| Farsi subtitles tofu-box | Encode with the Vazirmatn font (`resource/fonts/`) — set `params.font_name="Vazirmatn-Regular.ttf"` (R-3). |
| Outbound egress blocked | Configure `[proxy]` SOCKS5 relay (R-7); verify with `buffer_poc --list`. |
| Gemini TTS `429` (quota exhausted) | No fallback — the Edge-TTS `fa-IR-DilaraNeural` floor was rejected for quality (reversed 2026-10-04). FR-13 retries (30/120/600 s) then day-missed alert; `resume <run_id>` after the daily quota resets, or move to paid Gemini TTS. |

---

## 11. TL;DR operator loop (today)

1. `uv sync --frozen` once; keep `config.toml` current.
2. Ingest your book(s) via `ingest-books` (batch + auto-resume). [LIVE]
3. Build/post reels manually for now: `r10_check` for the media path,
   `buffer_poc` for publishing. [POC]
4. `resume <run_id>` to recover a stuck day. [LIVE]
5. Full daily automation + Telegram operator surface = in build (§3.2, §4).
