# Intent: Farsi Instagram Reel Generation Agent
Author: مکتب جاذبه. Status: Done.

## Problem
We need an agent that automatically generates Instagram videos (Reels), built on the MoneyPrinterTurbo open-source project or a more relevant one, with the goal of growing followers so we can sell educational packages on how to attract girls. Content is in Farsi. Content must be completely free to produce. The agent must be able to extract content from our specified sources, like books.

## Proposed outcome
- Fork harry0703/MoneyPrinterTurbo (MIT, actively maintained) as the already-usable base we build on; no all-in-one tool.
- The human reviews the **script only** (text, via Telegram), not the video — for speed.
- After script approval the video is generated and posted automatically; no human video review.
- Posting is automated via the official Meta Graph API (ig_user_reels, professional account); on API failure → manual fallback: the exact video file + caption are delivered by Telegram for manual posting.
- Posting schedule: weekdays at 20:00 Tehran time, Friday at 14:00 Tehran time, scheduled via the Graph API; tuned with Instagram Insights after 2–4 weeks of data.
- LLM layer: pluggable, config-driven; free providers first, switchable once or twice a month; cheap models allowed as fallback when the free model doesn't work.
- Starting free LLM provider: agnes-3.0-flash; more free providers may be added later.
- TTS: pluggable provider interface; Farsi voice selection deferred to a future audition plan (test candidates before adopting).
- Visuals: stock footage (Pexels) + kinetic text, per the completely-free constraint; AI-generated video and digital avatars excluded (paid).
- Book sourcing: one-time LLM pass per book into "idea cards" (claim + quote + example) stored as JSON; the daily picker samples unused cards.
- Cadence: at 08:00 Tehran time the operator gets the card-picking message with 5 candidate idea cards; they may pick one, and if none is picked by 2 hours before the posting time the agent picks one at random from that day's 5 candidates (weekday fallback 18:00 Tehran time, Friday fallback 12:00 Tehran time).
- Operator interface: Telegram bot — daily shortlist of 5 idea card candidates (reply with a number to pick one from those 5, never the full library); script text sent for approval; on posting failure the video file + caption sent for manual posting.
- Reel spec: 60–90s, 9:16 1080p, burned Farsi subtitles, soft background music under narration, encoded at ~4 Mbps (CRF 22–23, 4.5 Mbps cap) so a 90s Reel stays ≤ ~48 MB — under the Telegram Bot API 50 MB upload limit.
- CTA: follow + link-in-bio; the agent generates the Farsi caption and hashtags with each draft.
- Orchestration: plain pipeline + a small Python supervisor (scheduler, card picker, retry logic); no agent framework.
- The software ships as a Docker image (pipeline + supervisor + Telegram bot).
- Development happens on Docker Desktop (Windows); production runs on a Linux host with Docker.
- Failure policy: retry with backoff → cheap-model fallback → Telegram notification only when a day is actually missed → a manual-resume mechanism so the process can be continued from its checkpoint after a manual fix.
- Music: fetched daily from the Pexels audio API.
- A meta-safe script skill (`skills/meta-safe-farsi-reel-script/SKILL.md`) governs all script generation: tone guardrails (no PUA/guarantees/sexual framing) and anti-spam variety rules; scripts failing the self-check are routed to human review.
- Team/brand name: مکتب جاذبه.
- Channel account: a new professional (Creator/Business) Instagram account is created for the channel; it is not an existing personal account.

## Affected users and systems
- The مکتب جاذبه operator (daily card pick and script approval, via Telegram).
- The Instagram audience of the channel; future buyers of the "how to attract girls" educational packages.
- Production: a 24/7 CPU-only Linux machine running the Docker image.
- Development: Docker Desktop on a Windows machine.
- The MoneyPrinterTurbo fork (its LLM/TTS/visuals/music providers + ffmpeg assembly).
- External free services: free-tier LLM providers, Pexels (footage + audio), Telegram Bot API, optionally Google Colab free tier hosting models as external providers, and the Meta Graph API (posting, professional Instagram account + Meta developer app).
- The local idea-card store (books → JSON cards).

## Constraints
- All content is in Farsi.
- The stack must be completely free (cheap-model fallback only where the free model didn't work).
- Exactly 1 Reel per day.
- Content must be extractable from specified sources such as books (mixed formats, mostly English books).
- The base must be already usable and easy to build on; we do not want a tool that handles everything.
- The core machine is CPU-only; free services (e.g. Google Colab) may host models and serve them to the CPU-only machine as external providers.
- Free LLM providers are not free forever: the setup must allow changing providers once or twice a month.
- Humans review the script only; the posting flow must be automated.
- Posting uses the official Meta Graph API only; unofficial Instagram libraries are rejected.
- Clip selection policy: Pexels footage must fit the scene semantically (not just keyword match), be deduplicated against clips used in the last 30 days, and avoid the overused top-download staples that saturate stock-based channels.
- Content demotion policy: scripts must follow the Meta-safe rules — wholesome social-skills tone (no PUA framing, no outcome guarantees, no sexual/suggestive framing, no manipulation), one soft follow+bio CTA per Reel, rotating hook types with 7-day no-repeat, 3–5 Farsi-first hashtags, and card-specific concrete elements; scripts failing the self-check go to human review.

## Open questions
- Which Farsi TTS voices/providers pass the audition, and which one is adopted.
- Farsi font choice for burned subtitles.
- State of the link-in-bio landing page and the educational packages.
- Channel handle: to be decided at account registration time.
- Google Colab free-tier runtime/persistence limits vs. daily scheduled use (needs verification).
- Residual demotion risk after the skill's tone/variety guardrails — monitor reach data over the first 2–4 weeks.
- Long-lived access-token refresh flow for the Graph API (who re-authenticates when tokens expire).
- IP egress policy for the machine calling Meta APIs (stable non-Iran relay?).
