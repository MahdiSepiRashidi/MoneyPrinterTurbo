"""Buffer GraphQL API client (middleware posting backend for the IG Reel Agent).

Docs: https://developers.buffer.com
Endpoint: POST https://api.buffer.com (GraphQL, no path).

Why a middleware: the operator has no Meta developer account, so posting a Reel
directly through the Meta Graph API would require building/approving a Meta app
and passing business verification. Buffer owns that Meta app; the operator just
connects their Instagram account to Buffer once, and we drive Buffer's GraphQL
API with a single Bearer API key. No Meta credentials, no operator dev account.

Verified 2026-10-01 (supervisor/buffer_poc.py live run against the operator's
account): the key authenticates, an Instagram channel is connected, and a test
Reel was created and published (post status "sent").

Media: Buffer has NO upload endpoint. A Reel's video must be a **public URL**
it can fetch, passed in ``assets`` (R-9). Cloudinary (free tier) is confirmed
to work; avoid bot-protected hosts and signed/expiring URLs.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import requests
from loguru import logger

BUFFER_API_BASE_URL = "https://api.buffer.com"

# GraphQL query/mutation fragments (shared selection sets).
_ORGANIZATIONS = "query { account { organizations { id } } }"


class BufferError(RuntimeError):
    """Raised when Buffer returns a non-2xx response or a GraphQL error."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Any = None):
        self.status_code = status_code
        self.payload = payload
        super().__init__(message)


def _gql_str(value: str) -> str:
    """Render a Python string as a GraphQL string literal (JSON escaping is a
    compatible superset for the text we send)."""
    return json.dumps(value, ensure_ascii=False)


class BufferClient:
    """Thin wrapper over the Buffer GraphQL API endpoints the agent uses."""

    def __init__(
        self,
        api_key: str,
        base_url: str = BUFFER_API_BASE_URL,
        organization_id: Optional[str] = None,
        proxies: Optional[dict] = None,
        timeout: int = 120,
    ) -> None:
        if not api_key:
            raise ValueError("Buffer API key is required (supervisor.buffer_api_key)")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.organization_id = organization_id
        self.proxies = proxies or None
        self.timeout = timeout

    # -- transport ----------------------------------------------------------

    def _post(self, query: str, variables: Optional[dict] = None) -> Any:
        logger.debug("Buffer GraphQL POST {}", self.base_url)
        response = requests.post(
            self.base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            json={"query": query, "variables": variables or {}},
            timeout=self.timeout,
            proxies=self.proxies,
        )
        if response.status_code in (401, 403):
            raise BufferError(
                f"Buffer auth failed (HTTP {response.status_code}): check supervisor.buffer_api_key",
                status_code=response.status_code,
            )
        if response.status_code >= 400:
            raise BufferError(f"Buffer HTTP {response.status_code}: {response.text}", status_code=response.status_code)
        try:
            body = response.json()
        except ValueError:
            raise BufferError(f"Buffer returned non-JSON response: {response.text[:200]}")
        if isinstance(body, dict) and body.get("errors"):
            raise BufferError(f"Buffer GraphQL error: {body['errors']}", payload=body)
        return body.get("data", body) if isinstance(body, dict) else body

    # -- discovery ----------------------------------------------------------

    def organizations(self) -> list:
        """GET account.organizations -> [{id}]."""
        data = self._post(_ORGANIZATIONS)
        return (data.get("account") or {}).get("organizations") or []

    def resolve_organization_id(self) -> Optional[str]:
        """Return the configured organization id, or the single discovered one."""
        if self.organization_id:
            return self.organization_id
        orgs = self.organizations()
        if len(orgs) == 1:
            self.organization_id = orgs[0].get("id")
            return self.organization_id
        if len(orgs) > 1:
            logger.warning("Multiple organizations found; set supervisor.buffer_organization_id: {}", [o.get("id") for o in orgs])
        return self.organization_id

    def channels(self, organization_id: Optional[str] = None) -> list:
        """List connected channels (each has id, name, service, ...)."""
        org_id = organization_id or self.resolve_organization_id()
        if not org_id:
            raise BufferError("No Buffer organization id available; set supervisor.buffer_organization_id")
        # Buffer's OrganizationId/ChannelId are custom scalars, so inline the ids
        # as string literals (a typed variable of type String! is rejected).
        query = (
            "query GetChannels { channels(input: { organizationId: "
            + _gql_str(org_id)
            + " }) { id name displayName service isQueuePaused } }"
        )
        data = self._post(query)
        return data.get("channels") or []

    def find_channel(
        self, service: str = "instagram", organization_id: Optional[str] = None, preferred_id: Optional[str] = None
    ) -> Optional[dict]:
        """Pick the first channel matching ``service`` (or ``preferred_id``)."""
        for channel in self.channels(organization_id):
            if preferred_id and str(channel.get("id")) == preferred_id:
                return channel
            if service.lower() in str(channel.get("service", "")).lower():
                return channel
        return None

    # -- posts --------------------------------------------------------------

    def create_post(
        self,
        channel_id: str,
        text: str,
        *,
        video_url: Optional[str] = None,
        thumbnail_offset: int = 2000,
        reel_type: str = "reel",
        save_to_draft: bool = True,
        publish_now: bool = False,
        needs_approval: bool = False,
        is_ai_generated: bool = False,
        first_comment: Optional[str] = None,
        due_at: Optional[str] = None,
    ) -> Any:
        """Create a Buffer post (a Reel when ``video_url`` + Instagram ``reel_type`` are given).

        - ``save_to_draft=True`` -> nothing publishes (POC default).
        - ``publish_now=True`` -> ``mode: shareNow`` (immediate; matches R-4 our-side schedule).
        - ``due_at`` (ISO 8601 UTC) -> ``mode: customScheduled`` for a specific time.

        Returns the parsed ``data.createPost`` payload: ``{post:{...}}`` on
        success or ``{message:"..."}`` on a domain error.
        """
        if publish_now:
            mode = "shareNow"
        elif due_at:
            mode = "customScheduled"
        else:
            mode = "addToQueue"

        assets = ""
        if video_url:
            assets = (
                "assets: [ { video: { url: "
                + _gql_str(video_url)
                + ", metadata: { thumbnailOffset: "
                + str(int(thumbnail_offset))
                + " } } } ]"
            )

        instagram_meta = ["type: " + reel_type, "shouldShareToFeed: false"]
        if is_ai_generated:
            instagram_meta.append("isAiGenerated: true")
        if first_comment:
            instagram_meta.append("firstComment: " + _gql_str(first_comment))
        metadata = "metadata: { instagram: { " + ", ".join(instagram_meta) + " } }"

        fields = [
            "text: " + _gql_str(text),
            "channelId: " + _gql_str(channel_id),
            "schedulingType: automatic",
            "mode: " + mode,
            "needsApproval: " + ("true" if needs_approval else "false"),
            "saveToDraft: " + ("true" if save_to_draft else "false"),
        ]
        if assets:
            fields.append(assets)
        if metadata:
            fields.append(metadata)
        if due_at:
            fields.append("dueAt: " + _gql_str(due_at))

        query = (
            "mutation CreatePost { createPost(input: { "
            + ", ".join(fields)
            + " }) { ... on PostActionSuccess { post { id text status dueAt } } "
            + "... on MutationError { message } } }"
        )
        logger.info("Buffer create_post (mode={} draft={} reel={} channel={})", mode, save_to_draft, bool(video_url), channel_id)
        data = self._post(query)
        return (data or {}).get("createPost") or data

    def get_posts(
        self,
        organization_id: Optional[str] = None,
        channel_ids: Optional[list] = None,
        statuses: Optional[list] = None,
        first: int = 20,
    ) -> list:
        """List recent posts (optionally filtered); returns the flattened nodes.

        ``statuses`` are bare PostStatus enum names (e.g. ["sent", "error"]).
        """
        org_id = organization_id or self.resolve_organization_id()
        if not org_id:
            raise BufferError("No Buffer organization id available; set supervisor.buffer_organization_id")
        filter_parts = []
        if channel_ids:
            filter_parts.append("channelIds: [" + ", ".join(_gql_str(c) for c in channel_ids) + "]")
        if statuses:
            filter_parts.append("status: [" + ", ".join(statuses) + "]")
        filter_str = ("filter: { " + ", ".join(filter_parts) + " } ") if filter_parts else ""
        query = (
            "query GetPosts { posts(first: "
            + str(int(first))
            + ", input: { organizationId: "
            + _gql_str(org_id)
            + ", "
            + filter_str
            + "}) { edges { node { id text status dueAt } } } }"
        )
        data = self._post(query)
        edges = ((data.get("posts") or {}).get("edges")) or []
        return [edge.get("node") for edge in edges]

    def find_post(self, post_id: str, organization_id: Optional[str] = None, channel_ids: Optional[list] = None) -> Optional[dict]:
        """Locate a post by id among the channel's recent posts (Buffer exposes no direct by-id query)."""
        for node in self.get_posts(organization_id, channel_ids, first=50):
            if str(node.get("id")) == str(post_id):
                return node
        return None

    def delete_post(self, post_id: str) -> Any:
        """Delete a post/draft by id (cleanup). Returns {id} on success or {message} on error.

        Only unsent posts (drafts/scheduled) can be deleted; an already-sent post
        cannot be removed from the platform through the API.
        """
        query = (
            "mutation DeletePost { deletePost(input: { id: "
            + _gql_str(post_id)
            + " }) { ... on DeletePostSuccess { id } ... on VoidMutationError { message } } }"
        )
        data = self._post(query)
        return (data or {}).get("deletePost") or data

    @staticmethod
    def dump(payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)


__all__ = ["BufferClient", "BufferError", "BUFFER_API_BASE_URL"]
