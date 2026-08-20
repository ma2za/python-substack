from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from mcp.server.fastmcp import FastMCP

from substack.api import Api
from substack.post import Post

if load_dotenv is not None:
    load_dotenv()


def get_api() -> Api:
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    cookies_path = os.getenv("COOKIES_PATH")
    cookies_string = os.getenv("COOKIES_STRING")
    publication_url = os.getenv("PUBLICATION_URL")

    if cookies_path or cookies_string:
        return Api(
            cookies_path=cookies_path,
            cookies_string=cookies_string,
            publication_url=publication_url,
        )

    if email and password:
        return Api(
            email=email,
            password=password,
            publication_url=publication_url,
        )

    raise ValueError(
        "Missing Substack auth configuration: set EMAIL/PASSWORD or COOKIES_PATH/COOKIES_STRING"
    )


def _normalize_tags(tags: Optional[Any]) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [str(tag) for tag in tags]
    raise ValueError("tags must be a string or a list of strings")


mcp = FastMCP("substack")


@mcp.tool()
async def post_draft_from_markdown(
    title: str,
    markdown: str,
    subtitle: Optional[str] = "",
    audience: str = "everyone",
    write_comment_permissions: str = "everyone",
    search_engine_title: Optional[str] = None,
    search_engine_description: Optional[str] = None,
    slug: Optional[str] = None,
    draft_section_id: Optional[int] = None,
    tags: Optional[Any] = None,
    prepublish: bool = False,
    publish: bool = False,
    send: bool = True,
    share_automatically: bool = False,
) -> Dict[str, Any]:
    """Create or update a Substack draft from Markdown.

    This tool builds a Substack `Post` from markdown content and posts a draft.
    It supports optional tag assignment, prepublish (setup check), and publishing.

    Args:
        title: Draft title.
        markdown: Markdown body content.
        subtitle: Optional subtitle text.
        audience: One of `everyone`, `only_paid`, `founding`, `only_free`.
        write_comment_permissions: One of `none`, `only_paid`, `everyone`.
        search_engine_title: Optional title for search engine optimization.
        search_engine_description: Optional description for search engine optimization.
        slug: Optional URL slug for the post.
        draft_section_id: Optional section ID for the draft.
        tags: Tag or list of tags to attach to the post.
        prepublish: If true, calls `prepublish_draft` after creation.
        publish: If true, calls `publish_draft` after creation (and optionally prepublish).
        send: Passed to `publish_draft` for newsletter delivery.
        share_automatically: Passed to `publish_draft`.

    Returns:
        dict containing drafted post (`draft`), optional `tags`, `prepublish`, `publish` results.

    Examples:
        With the YAML structure from the README, a caller can map fields like:

        ```yaml
        title: "My Post Title"
        subtitle: "My Post Subtitle"
        audience: "everyone"
        write_comment_permissions: "everyone"
        markdown: |
          # Hello

          This is the body.

        tags:
          - python
          - substack
        prepublish: true
        publish: true
        send: false
        share_automatically: true
        ```

        Then invoke via MCP directly:

        ```python
        from substack_mcp.mcp_server import post_draft_from_markdown

        result = await post_draft_from_markdown(
            title='My Post Title',
            markdown='# Hello\n\nThis is the body.',
            subtitle='My Post Subtitle',
            audience='everyone',
            write_comment_permissions='everyone',
            tags=['python', 'substack'],
            prepublish=True,
            publish=False,  # set true when ready
        )
        print(result)
        ```

        A longer process with manual prepublish/publish calls:

        ```python
        from substack_mcp.mcp_server import (
            post_draft_from_markdown,
            prepublish_draft,
            publish_draft,
            add_tags,
        )

        d = await post_draft_from_markdown(
            title='Long flow',
            markdown='Content',
            tags=['a','b'],
            publish=False,
        )
        draft_id = d['draft']['id']

        await add_tags(draft_id, ['post-tag', 'news'])
        await prepublish_draft(draft_id)
        await publish_draft(draft_id, send=True, share_automatically=True)
        ```

        This docstring example is meant to mirror the YAML-driven workflow and show how to decompose the same operations into explicit tool calls.
    """
    client = get_api()

    return client.create_draft_from_markdown(
        title=title,
        markdown=markdown,
        subtitle=subtitle,
        audience=audience,
        write_comment_permissions=write_comment_permissions,
        search_engine_title=search_engine_title,
        search_engine_description=search_engine_description,
        slug=slug,
        draft_section_id=draft_section_id,
        tags=tags,
        prepublish=prepublish,
        publish=publish,
        send=send,
        share_automatically=share_automatically,
    )


@mcp.tool()
async def put_draft(
    draft_id: int,
    update_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Update an existing draft by draft ID.

    Args:
        draft_id: target draft identifier.
        update_payload: dict of fields supported by Substack `put_draft` (e.g. `slug`, `draft_section_id`).

    Returns:
        API response dict for the updated draft.
    """
    client = get_api()
    return client.put_draft(draft_id, **update_payload)


@mcp.tool()
async def add_tags(draft_id: int, tags: Any) -> Dict[str, Any]:
    """Add tags to a specific draft/post.

    Args:
        draft_id: target draft identifier.
        tags: string or list of tag names (e.g. `"tech"` or `["tech", "python"]`).

    Returns:
        Response from `add_tags_to_post` (tag IDs + names).
    """
    client = get_api()
    tags_list = _normalize_tags(tags)
    if not tags_list:
        raise ValueError("tags is required and cannot be empty")
    return client.add_tags_to_post(draft_id, tags_list)


@mcp.tool()
async def prepublish_draft(draft_id: int) -> Dict[str, Any]:
    """Invoke prepublish checks for a draft.

    Args:
        draft_id: target draft identifier.

    Returns:
        Prepublish response dict from Substack API.
    """
    client = get_api()
    return client.prepublish_draft(draft_id)


@mcp.tool()
async def publish_draft(
    draft_id: int,
    send: bool = True,
    share_automatically: bool = False,
) -> Dict[str, Any]:
    """Publish a draft to live post state. (Legacy compatibility interface).

    This tool remains for backward compatibility. It is recommended to use
    `publish_draft_checked` instead, which provides a safer publishing path
    with explicit confirmation and prepublish validation.

    Args:
        draft_id: target draft identifier.
        send: if False then do not send email to subscribers.
        share_automatically: whether to auto-share (e.g. social propagation).

    Returns:
        Response from Substack `publish_draft`.
    """
    client = get_api()
    return client.publish_draft(
        draft_id, send=send, share_automatically=share_automatically
    )


@mcp.tool()
async def publish_draft_checked(
    draft_id: int,
    confirm: bool = False,
    send: bool = False,
    share_automatically: bool = False,
) -> Dict[str, Any]:
    """A safer publishing path that requires confirmation and runs prepublish checks.

    Args:
        draft_id: target draft identifier.
        confirm: Must be True to proceed with publication.
        send: if False then do not send email to subscribers. Defaults to False.
        share_automatically: whether to auto-share.

    Returns:
        Response from Substack `publish_draft`.
    """
    if not confirm:
        raise ValueError("Publishing rejected: confirm parameter must be True.")

    client = get_api()
    client.prepublish_draft(draft_id)
    return client.publish_draft(
        draft_id, send=send, share_automatically=share_automatically
    )


@mcp.tool()
async def get_status() -> Dict[str, Any]:
    """Get the authentication status and basic user information.

    Returns:
        A dictionary containing user profile and primary publication details.
    """
    client = get_api()
    profile = client.get_user_profile()
    primary_pub = client.get_user_primary_publication()
    return {"profile": profile, "primary_publication": primary_pub}


@mcp.tool()
async def list_publications() -> List[Dict[str, Any]]:
    """List all publications available to the authenticated user.

    Returns:
        A list of publications.
    """
    client = get_api()
    return client.get_user_publications()


@mcp.tool()
async def list_drafts(
    filter: str = "draft", offset: int = 0, limit: int = 25
) -> List[Dict[str, Any]]:
    """List drafts for the current publication.

    Args:
        filter: Filter string, defaults to "draft".
        offset: Pagination offset.
        limit: Max number of drafts to return.

    Returns:
        A list of drafts.
    """
    client = get_api()
    return client.get_drafts(filter=filter, offset=offset, limit=limit)


@mcp.tool()
async def get_draft(draft_id: int) -> Dict[str, Any]:
    """Get a specific draft by its ID.

    Args:
        draft_id: The identifier of the draft.

    Returns:
        The draft details.
    """
    client = get_api()
    return client.get_draft(draft_id)


@mcp.tool()
async def schedule_draft(draft_id: int, at: str) -> Dict[str, Any]:
    """Schedule a draft for release.

    Args:
        draft_id: target draft identifier.
        at: ISO 8601 formatted datetime string (e.g., "2024-01-01T12:00:00Z").

    Returns:
        API response dict for the scheduled draft.
    """
    from datetime import datetime

    try:
        draft_datetime = datetime.fromisoformat(at.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Invalid ISO datetime string for 'at': {e}")

    client = get_api()
    return client.schedule_draft(draft_id, draft_datetime)


@mcp.tool()
async def unschedule_draft(draft_id: int) -> Dict[str, Any]:
    """Unschedule a previously scheduled draft.

    Args:
        draft_id: target draft identifier.

    Returns:
        API response dict for unscheduling.
    """
    client = get_api()
    return client.unschedule_draft(draft_id)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
