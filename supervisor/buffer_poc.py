"""Proof of concept: post a Reel to Instagram via the Buffer GraphQL API.

Run from the repo root (reads the key from config.toml [supervisor] automatically):

    uv run python -X utf8 -m supervisor.buffer_poc --list
    uv run python -X utf8 -m supervisor.buffer_poc                 # safe draft Reel
    uv run python -X utf8 -m supervisor.buffer_poc --publish       # actually post now
    uv run python -X utf8 -m supervisor.buffer_poc --check <post_id>
    uv run python -X utf8 -m supervisor.buffer_poc --delete <post_id>

Verified 2026-10-01 against the operator's Buffer account: key authenticates, an
Instagram channel is connected, and a Reel was published (post status "sent").

Safety: the default action creates a DRAFT (nothing publishes). Pass --publish to
post immediately (shareNow). The default --media-url is a stable Cloudinary sample
video so the full path works out of the box; for a real reel pass the public URL
of your generated MP4 (Buffer has no upload endpoint - see plan R-9).
"""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

from loguru import logger

from supervisor.buffer import BufferClient, BufferError, BUFFER_API_BASE_URL

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEDIA_URL = "https://res.cloudinary.com/demo/video/upload/f_auto/fl_attachment/elephants.mp4"


def _load_config_toml() -> dict:
    path = REPO_ROOT / "config.toml"
    if not path.exists():
        return {}
    with open(path, "rb") as handle:
        try:
            return tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            logger.warning("config.toml could not be parsed: {}", exc)
            return {}


def _proxies_from_config(cfg: dict) -> dict | None:
    proxy = cfg.get("proxy") or {}
    proxies = {}
    if proxy.get("http"):
        proxies["http"] = proxy["http"]
    if proxy.get("https"):
        proxies["https"] = proxy["https"]
    return proxies or None


def _banner(text: str) -> None:
    print(f"\n=== {text} ===")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Buffer GraphQL IG Reel POC (non-destructive by default).")
    parser.add_argument("--api-key", dest="api_key", default=None, help="Buffer API key (Overrides config.toml).")
    parser.add_argument("--base-url", default=None, help="Override the Buffer GraphQL endpoint.")
    parser.add_argument("--org-id", default=None, help="Buffer organization id (from --list / config).")
    parser.add_argument("--channel-id", default=None, help="Exact channel id to target.")
    parser.add_argument("--channel-network", default=None, help="Network to auto-select (default instagram).")
    parser.add_argument("--content", default="Buffer API POC - test reel, safe to delete", help="Reel caption.")
    parser.add_argument("--hashtags", nargs="*", default=[], help="Hashtags (with or without leading #).")
    parser.add_argument("--media-url", default=DEFAULT_MEDIA_URL, help="Public MP4 URL to attach as the Reel video.")
    parser.add_argument("--publish", action="store_true", help="Publish now (shareNow) instead of a draft.")
    parser.add_argument("--check", metavar="POST_ID", default=None, help="Check a post's status and stop.")
    parser.add_argument("--delete", metavar="POST_ID", default=None, help="Delete a post/draft and stop.")
    parser.add_argument("--list", action="store_true", dest="list_only", help="List channels and stop.")
    args = parser.parse_args(argv)

    cfg = _load_config_toml()
    sup = cfg.get("supervisor") or {}
    api_key = args.api_key or os.environ.get("BUFFER_API_KEY") or str(sup.get("buffer_api_key", "") or "")
    base_url = args.base_url or str(sup.get("buffer_base_url", "")) or BUFFER_API_BASE_URL

    if not api_key:
        _banner("BLOCKED - no Buffer API key")
        print("Set it via one of: config.toml -> [supervisor] buffer_api_key, env BUFFER_API_KEY, or --api-key.")
        print("Create the key in Buffer: Settings -> API.")
        return 2

    client = BufferClient(
        api_key=api_key,
        base_url=base_url,
        organization_id=args.org_id or str(sup.get("buffer_organization_id", "") or ""),
        proxies=_proxies_from_config(cfg),
    )

    _banner("1. connectivity / org")
    try:
        orgs = client.organizations()
    except BufferError as exc:
        print(f"FAILED: {exc}")
        return 1
    print(f"organizations -> {client.dump(orgs)}")

    _banner("2. connected channels")
    channels = client.channels()
    for channel in channels:
        print(f"  - id={channel.get('id')}  service={channel.get('service')}  name={channel.get('name')}")
    if args.list_only:
        _banner("done (list-only)")
        return 0
    if not channels:
        print("No channels connected. Connect your Instagram in the Buffer app, then re-run.")
        return 3

    if args.check:
        _banner(f"3. check post {args.check}")
        cid = str(sup.get("buffer_channel_id", "") or "")
        node = client.find_post(args.check, channel_ids=[cid] if cid else None)
        print(f"post -> {client.dump(node) if node else 'not found among recent posts'}")
        return 0

    if args.delete:
        _banner(f"4. delete post {args.delete}")
        try:
            result = client.delete_post(args.delete)
            print(f"deletePost -> {client.dump(result)}")
            return 0
        except BufferError as exc:
            print(f"FAILED: {exc}")
            return 1

    _banner("3. target channel")
    network = args.channel_network or "instagram"
    channel = client.find_channel(service=network, preferred_id=args.channel_id or str(sup.get("buffer_channel_id", "") or ""))
    if channel is None:
        print(f"No '{network}' channel connected. Re-run with --channel-id or connect it in Buffer first.")
        return 4
    target_id = str(channel.get("id"))
    print(f"Selected: id={target_id} service={channel.get('service')} name={channel.get('name')}")

    _banner("4. create Reel " + ("NOW (publish)" if args.publish else "as draft"))
    caption = args.content.strip()
    if args.hashtags:
        joined = " ".join(h if h.startswith("#") else f"#{h}" for h in args.hashtags)
        caption = f"{caption}\n{joined}".strip() if caption else joined

    try:
        result = client.create_post(
            target_id,
            caption,
            video_url=args.media_url,
            reel_type=str(sup.get("buffer_reel_type", "reel") or "reel"),
            save_to_draft=not args.publish,
            publish_now=args.publish,
        )
    except BufferError as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"createPost -> {client.dump(result)}")
    post = result.get("post") if isinstance(result, dict) else None
    if post:
        print(f"post id={post.get('id')} status={post.get('status')} dueAt={post.get('dueAt')}")
        if args.publish:
            print("Published now. Verify in the Buffer app / your Instagram account.")
        else:
            print("Draft created (nothing published). To publish: re-run with --publish.")
            print(f"To check status later: ... -m supervisor.buffer_poc --check {post.get('id')}")
    elif isinstance(result, dict) and result.get("message"):
        print(f"Rejected: {result['message']}")
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
