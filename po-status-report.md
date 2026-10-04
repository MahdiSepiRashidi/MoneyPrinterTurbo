# IG Reel Agent — Status Report for Product Owner

**Date:** 2026-10-04
**Board:** [IG Reel Agent — Backlog](https://trello.com/b/C3cabZHA/ig-reel-agent-backlog)

---

## Executive Summary

The **IG Reel Agent** project automates the creation and publishing of daily Instagram Reels for a book author. The pipeline ingests book chapters, generates Farsi scripts, produces a short video with narration and background music, and posts it to Instagram at a set time.

**Overall progress: ~50%.** All foundational decisions and the content pipeline (from book to approved script) are complete. The media production layer (turning the script into a finished video) and the final posting/publishing layer are in progress.

---

## What's Done

### Decisions & Architecture (settled)
- **Posting platform:** Buffer middleware (not direct Instagram/Meta API). Verified live.
- **Voice (TTS):** Gemini 3.8 Flash TTS with the "Charon" prebuilt voice (best Farsi delivery & question tone). Edge-TTS kept only as a key-free fallback.
- **Font:** Vazirmatn (Farsi font) added to the project for subtitles.
- **Scheduling:** We control publish timing on our side (no reliance on Instagram's native scheduler).
- **Compute:** Running on free-tier Gemini models; no paid cloud GPU needed.
- **Out of scope for v1:** Rule-based Farsi text cleanup (postponed — current TTS output is acceptable; will revisit only if quality issues arise).

### Content Pipeline (Epic A — Complete)
All of the following are built, tested, and working:

| Capability | Status |
|---|---|
| Book chapters converted to "idea cards" (short content topics) | ✅ Done |
| Daily pick of 5 unused cards, sent to the operator at 08:00 Tehran via Telegram | ✅ Done |
| Deadline fallback: if no card is picked by 18:00 (or 12:00 on Friday), auto-pick from remaining | ✅ Done |
| Farsi script generation (60–90 seconds of spoken content) | ✅ Done |
| Script approval gate: operator reviews/approves/edits the script via Telegram before video production | ✅ Done |
| Farsi caption + hashtags + soft call-to-action for the post | ✅ Done |
| Text normalization for TTS (clean input to the voice engine) | ✅ Done |
| Retry / backoff / resume: if a run fails mid-way, it can pick up where it left off | ✅ Done |
| Pluggable LLM: model and provider are configurable, no code changes to swap | ✅ Done |
| Data model & persistence (JSON stores for cards, run state, usage logs) | ✅ Done |

---

## What Remains

### Epic C — Media Production (5 tasks, not started)
This is the layer that turns the approved Farsi script into a finished video reel.

| Task | What it means in plain language |
|---|---|
| **Farsi narration (TTS)** | Generate the spoken Farsi voiceover (60–90 s) with automatic duration adjustment. |
| **Daily background music** | Automatically pick fresh, royalty-free music from Pexels each day (no repeated tracks). Fallback to a local library if the service is down. |
| **Background video clips** | Select stock video clips from Pexels that match the content topic. 30-day no-repeat rule to avoid stale visuals. |
| **Assemble the final video** | Combine clips + narration + music + burned-in Farsi subtitles into a single vertical 9:16 video (1080×1920, 60–90 s, under 48 MB — Instagram's limit). |
| **Video encoding proof-of-concept** | Verify the video is encoded within the size/quality caps before integrating into the pipeline. |

### Epic D — Publishing & Deployment (6 tasks, mostly not started)

| Task | What it means in plain language | Progress |
|---|---|---|
| **Post to Instagram via Buffer** | Upload the finished reel and schedule/publish it at 20:00 (or 14:00 Friday) Tehran time. | 🟡 Buffer client built and verified live (a test reel was successfully posted). Remaining: hosting the video file publicly, wiring into the daily flow, and tests. |
| **Public video hosting for Buffer** | Buffer needs a stable, public URL for the video file. Default: Cloudinary (free tier). Alternative: Cloudflare R2. | ⬜ Not started. Blocked on credentials. |
| **Manual fallback on posting failure** | If the automated post fails after retries, the video + caption is sent to the operator's Telegram for manual posting. | ⬜ Not started. |
| **Telegram operator bot** | The Telegram bot becomes the single place to manage the whole workflow: pick cards, approve scripts, acknowledge manual posts, rotate credentials. | ⬜ Not started (design done). |
| **Pexels Audio proof-of-concept** | Confirm the music API endpoint works with our key before building the BGM feature. | ⬜ Not started. Gates the BGM task. |
| **Ship as Docker container** | Package the entire system (video pipeline + scheduler + bot) into one container for easy deployment. | ⬜ Not started. |

### Final Validation (1 task)
| Task | What it means |
|---|---|
| **End-to-end daily flow test** | A full automated test that runs the pipeline from "ingest a book chapter" all the way to "reel posted on Instagram", verifying every stage. Must pass before the system is considered ready. |

### Postponed
| Task | Reason |
|---|---|
| **Rule-based Farsi text cleanup (R-2)** | Skipped for v1. The TTS engine produces acceptable Farsi output without it. Will revisit only if narration quality issues are observed in practice. |

---

## Dependencies & Order of Work

The remaining work follows a clear sequence:

```
1. Pexels Audio POC          (unlocks BGM)
2. Background Music          (music layer)
3. Video Clip Selection      (visual layer)
4. Video Encoding POC        (quality gate)
5. Final Video Assembly      (reel is produced)
6. Public Media Hosting       (so Buffer can fetch the file)
7. Post via Buffer           (reel goes live)
8. Manual Fallback           (safety net)
9. Telegram Bot              (operator control)
10. Docker Packaging          (deployment)
11. End-to-End Test          (final validation)
```

Steps 1–5 are **independent of each other** at the data level but 5 depends on 2 and 3 being done. Steps 6–7 are dependent (you need the public URL before you can post). Steps 8–10 can run in parallel once 7 is done.

---

## Key Risks

1. **Public media hosting (R-9 revised):** Buffer has no upload endpoint. We need a stable, public URL for each reel. Cloudinary free tier is the default but needs credentials in place. If Cloudinary's free tier limits (e.g. bandwidth, storage) become a bottleneck, we'd need to switch to Cloudflare R2.
2. **Pexels Audio API:** We haven't yet verified the endpoint works with our key. If there are licensing or format surprises, the BGM plan needs adjustment.
3. **Docker in production:** The system is designed to run in a single CPU-only container. Any surprise in ffmpeg/moviepy build on Linux vs. Windows Docker Desktop would delay deployment.

---

## Summary for PO

| Area | Status |
|---|---|
| Strategy & architecture decisions | ✅ All settled |
| Content pipeline (book → script → approval) | ✅ Complete & tested |
| Media production (script → finished video) | ⬜ Not started (5 tasks) |
| Publishing (video → Instagram) | 🟡 30% done (client built & verified live; hosting + wiring remaining) |
| Operator tooling (Telegram bot, manual fallback) | ⬜ Not started (design done) |
| Deployment (Docker) | ⬜ Not started |
| Final end-to-end test | ⬜ Not started |
| Postponed items | 1 item deferred to v2 |

**Bottom line:** The "thinking" side of the system (what to say, who approves, when to post) is done. The "making" side (producing the video file and getting it onto Instagram) is next. Estimated effort to completion: the 5 media tasks are the bulk of remaining work, followed by a smaller set of publishing/deployment tasks.
