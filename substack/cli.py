import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import yaml
from dotenv import load_dotenv

from substack import Api, __version__
from substack.exceptions import SubstackAPIException, SubstackRequestException
from substack.post import Post


class CLIUsageError(Exception):
    pass


def _api_from_env(cookies_path=None, publication_url=None):
    load_dotenv()

    cookies_path = cookies_path or os.getenv("COOKIES_PATH")
    cookies_string = os.getenv("COOKIES_STRING")
    publication_url = publication_url or os.getenv("PUBLICATION_URL")

    if cookies_path or cookies_string:
        return Api(
            cookies_path=cookies_path,
            cookies_string=cookies_string,
            publication_url=publication_url,
        )

    return Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=publication_url,
    )


def _auth_method(cookies_path=None):
    load_dotenv()

    if cookies_path:
        return "cookies_path"
    if os.getenv("COOKIES_PATH"):
        return "cookies_path"
    if os.getenv("COOKIES_STRING"):
        return "cookies_string"
    if os.getenv("EMAIL") and os.getenv("PASSWORD"):
        return "email_password"
    return "unknown"


def _title_from_markdown(markdown, fallback):
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _print_result(result):
    draft = result["draft"]
    print(json.dumps({"draft_id": draft.get("id"), "draft": draft}, indent=2))


def _print_json(value, stream=None):
    print(json.dumps(value, indent=2, default=str), file=stream)


def _display(value):
    if value is None or value == "":
        return "-"
    return str(value)


def _print_rows(headers, rows):
    rows = [[_display(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    print(
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    )
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _identity(profile):
    return (
        profile.get("email")
        or profile.get("name")
        or profile.get("handle")
        or str(profile.get("id", "unknown"))
    )


def _selected_publication(api, publications):
    for publication in publications:
        publication_url = publication.get("publication_url")
        if (
            publication_url
            and urljoin(publication_url, "api/v1") == api.publication_url
        ):
            return publication
    return {"publication_url": api.publication_url.removesuffix("/api/v1")}


def _parse_schedule(value):
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        scheduled_at = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CLIUsageError("--at must be a valid ISO 8601 timestamp") from exc
    if scheduled_at.utcoffset() is None:
        raise CLIUsageError("--at must include a timezone offset or Z")
    return scheduled_at


def _confirm(action, target, yes, json_output):
    if yes:
        return
    if json_output or not sys.stdin.isatty():
        raise CLIUsageError(f"{action} requires --yes in non-interactive or JSON mode")
    try:
        confirmed = input(f"{action} draft {target}? [y/N] ").strip().lower()
    except EOFError as exc:
        raise CLIUsageError(f"{action} requires confirmation or --yes") from exc
    if confirmed not in {"y", "yes"}:
        raise CLIUsageError("Cancelled")


def _redact(message):
    redacted = str(message)
    for name in ("EMAIL", "PASSWORD", "COOKIES_STRING"):
        secret = os.getenv(name)
        if secret:
            redacted = redacted.replace(secret, "[redacted]")
    return redacted


def _error_payload(exc):
    if isinstance(exc, SubstackAPIException):
        return {
            "error": {
                "type": "api_error",
                "message": _redact(exc.message),
                "status_code": exc.status_code,
            }
        }
    if isinstance(exc, SubstackRequestException):
        return {
            "error": {
                "type": "request_error",
                "message": _redact(exc.message),
            }
        }
    if isinstance(exc, OSError):
        return {"error": {"type": "io_error", "message": _redact(exc)}}
    return {"error": {"type": "configuration_error", "message": _redact(exc)}}


def _print_error(exc, json_output):
    payload = _error_payload(exc)
    if json_output:
        _print_json(payload, stream=sys.stderr)
    else:
        print(f"Error: {payload['error']['message']}", file=sys.stderr)


def _print_usage_error(exc, json_output):
    if json_output:
        _print_json(
            {"error": {"type": "usage_error", "message": str(exc)}},
            stream=sys.stderr,
        )
    else:
        print(f"Error: {exc}", file=sys.stderr)


def _status(api, args):
    profile = api.get_user_profile()
    publications = api.get_user_publications()
    selected = _selected_publication(api, publications)
    subscriber_count = api.get_publication_subscriber_count()
    result = {
        "status": {
            "identity": _identity(profile),
            "auth_method": _auth_method(args.cookies),
            "subscriber_count": subscriber_count,
        },
        "profile": profile,
        "publication": selected,
        "publications": publications,
    }
    if args.json_output:
        _print_json(result)
    else:
        print(f"Authenticated as: {result['status']['identity']}")
        print(f"Auth method: {result['status']['auth_method']}")
        print(f"Publication: {_display(selected.get('name'))}")
        print(f"Publication URL: {_display(selected.get('publication_url'))}")
        print(f"Subscribers: {subscriber_count}")
        print(f"Available publications: {len(publications)}")


def _publications_list(api, args):
    publications = api.get_user_publications()
    if args.json_output:
        _print_json({"publications": publications, "count": len(publications)})
    else:
        _print_rows(
            ["ID", "NAME", "SUBDOMAIN", "URL"],
            [
                [
                    publication.get("id"),
                    publication.get("name"),
                    publication.get("subdomain"),
                    publication.get("publication_url"),
                ]
                for publication in publications
            ],
        )


def _drafts_list(api, args):
    if args.offset < 0:
        raise CLIUsageError("--offset must be zero or greater")
    if args.limit < 1:
        raise CLIUsageError("--limit must be greater than zero")
    drafts = api.get_drafts(filter=args.filter, offset=args.offset, limit=args.limit)
    if args.json_output:
        _print_json(
            {
                "drafts": drafts,
                "count": len(drafts),
                "filter": args.filter,
                "offset": args.offset,
                "limit": args.limit,
            }
        )
    else:
        _print_rows(
            ["ID", "TITLE", "STATUS", "SCHEDULED"],
            [
                [
                    draft.get("id"),
                    draft.get("draft_title") or draft.get("title"),
                    draft.get("type") or draft.get("status") or "draft",
                    draft.get("post_date"),
                ]
                for draft in drafts
            ],
        )


def _drafts_get(api, args):
    draft = api.get_draft(args.draft_id)
    if args.json_output:
        _print_json({"draft": draft})
    else:
        fields = [
            ("ID", draft.get("id")),
            ("Title", draft.get("draft_title") or draft.get("title")),
            ("Subtitle", draft.get("draft_subtitle") or draft.get("subtitle")),
            ("Status", draft.get("type") or draft.get("status") or "draft"),
            ("Slug", draft.get("slug")),
            ("Scheduled", draft.get("post_date")),
            ("Audience", draft.get("audience")),
        ]
        for label, value in fields:
            print(f"{label}: {_display(value)}")


def _drafts_schedule(api, args):
    scheduled_at = _parse_schedule(args.at)
    result = api.schedule_draft(args.draft_id, scheduled_at)
    payload = {
        "action": "schedule",
        "draft_id": args.draft_id,
        "scheduled_at": scheduled_at.isoformat(),
        "result": result,
    }
    if args.json_output:
        _print_json(payload)
    else:
        print(f"Scheduled draft {args.draft_id} for {scheduled_at.isoformat()}")


def _drafts_unschedule(api, args):
    result = api.unschedule_draft(args.draft_id)
    payload = {"action": "unschedule", "draft_id": args.draft_id, "result": result}
    if args.json_output:
        _print_json(payload)
    else:
        print(f"Unscheduled draft {args.draft_id}")


def _drafts_publish(api, args):
    _confirm("Publish", args.draft_id, args.yes, args.json_output)
    prepublish = api.prepublish_draft(args.draft_id)
    result = api.publish_draft(
        args.draft_id,
        send=args.send,
        share_automatically=args.share_automatically,
    )
    payload = {
        "action": "publish",
        "draft_id": args.draft_id,
        "prepublish": prepublish,
        "result": result,
    }
    if args.json_output:
        _print_json(payload)
    else:
        delivery = "without email" if not args.send else "with email"
        print(f"Published draft {args.draft_id} {delivery}")


def _drafts_delete(api, args):
    _confirm("Delete", args.draft_id, args.yes, args.json_output)
    result = api.delete_draft(args.draft_id)
    payload = {"action": "delete", "draft_id": args.draft_id, "result": result}
    if args.json_output:
        _print_json(payload)
    else:
        print(f"Deleted draft {args.draft_id}")


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="substack", description="Manage Substack publications and drafts."
    )
    parser.add_argument("--cookies", help="Path to a cookies JSON file.")
    parser.add_argument(
        "--publication-url", help="Override PUBLICATION_URL for this command."
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--version", action="version", version=__version__)

    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser(
        "status", help="Show authentication and publication status."
    )
    status.set_defaults(handler=_status)

    publications = commands.add_parser("publications", help="Manage publications.")
    publication_commands = publications.add_subparsers(
        dest="publication_command", required=True
    )
    publications_list = publication_commands.add_parser(
        "list", help="List available publications."
    )
    publications_list.set_defaults(handler=_publications_list)

    drafts = commands.add_parser("drafts", help="Manage drafts.")
    draft_commands = drafts.add_subparsers(dest="draft_command", required=True)

    drafts_list = draft_commands.add_parser("list", help="List drafts.")
    drafts_list.add_argument("--filter", default="draft")
    drafts_list.add_argument("--offset", type=int, default=0)
    drafts_list.add_argument("--limit", type=int, default=25)
    drafts_list.set_defaults(handler=_drafts_list)

    drafts_get = draft_commands.add_parser("get", help="Inspect a draft.")
    drafts_get.add_argument("draft_id", type=int)
    drafts_get.set_defaults(handler=_drafts_get)

    drafts_schedule = draft_commands.add_parser("schedule", help="Schedule a draft.")
    drafts_schedule.add_argument("draft_id", type=int)
    drafts_schedule.add_argument("--at", required=True)
    drafts_schedule.set_defaults(handler=_drafts_schedule)

    drafts_unschedule = draft_commands.add_parser(
        "unschedule", help="Remove a draft schedule."
    )
    drafts_unschedule.add_argument("draft_id", type=int)
    drafts_unschedule.set_defaults(handler=_drafts_unschedule)

    drafts_publish = draft_commands.add_parser("publish", help="Publish a draft.")
    drafts_publish.add_argument("draft_id", type=int)
    drafts_publish.add_argument(
        "--no-send", action="store_false", dest="send", default=True
    )
    drafts_publish.add_argument("--share-automatically", action="store_true")
    drafts_publish.add_argument("--yes", action="store_true")
    drafts_publish.set_defaults(handler=_drafts_publish)

    drafts_delete = draft_commands.add_parser("delete", help="Delete a draft.")
    drafts_delete.add_argument("draft_id", type=int)
    drafts_delete.add_argument("--yes", action="store_true")
    drafts_delete.set_defaults(handler=_drafts_delete)
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        api = _api_from_env(
            cookies_path=args.cookies,
            publication_url=args.publication_url,
        )
        args.handler(api, args)
    except CLIUsageError as exc:
        _print_usage_error(exc, args.json_output)
        return 2
    except (SubstackAPIException, SubstackRequestException, OSError, ValueError) as exc:
        _print_error(exc, args.json_output)
        return 1
    return 0


def publish_markdown(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", nargs="?", default="README.md")
    parser.add_argument("-m", "--markdown-file", dest="markdown_file")
    parser.add_argument("--title")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--audience", default="everyone")
    parser.add_argument("--write-comment-permissions", default="everyone")
    parser.add_argument("--search-engine-title")
    parser.add_argument("--search-engine-description")
    parser.add_argument("--slug")
    parser.add_argument("--draft-section-id", type=int)
    parser.add_argument("--tag", action="append", dest="tags")
    parser.add_argument("--cookies")
    parser.add_argument("--prepublish", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--no-send", action="store_false", dest="send", default=True)
    parser.add_argument("--share-automatically", action="store_true")
    args = parser.parse_args(argv)

    markdown_path = Path(args.markdown_file or args.markdown)
    markdown = markdown_path.read_text(encoding="utf-8")

    api = _api_from_env(args.cookies)
    result = api.create_draft_from_markdown(
        title=args.title or _title_from_markdown(markdown, markdown_path.stem),
        markdown=markdown,
        subtitle=args.subtitle,
        audience=args.audience,
        write_comment_permissions=args.write_comment_permissions,
        search_engine_title=args.search_engine_title,
        search_engine_description=args.search_engine_description,
        slug=args.slug,
        draft_section_id=args.draft_section_id,
        tags=args.tags,
        prepublish=args.prepublish or args.publish,
        publish=args.publish,
        send=args.send,
        share_automatically=args.share_automatically,
    )
    _print_result(result)
    return 0


def publish_yaml(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("post", nargs="?", default="draft.yaml")
    parser.add_argument("-p", "--post-file", dest="post_file")
    parser.add_argument("--cookies")
    parser.add_argument("--prepublish", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--no-send", action="store_false", dest="send", default=True)
    parser.add_argument("--share-automatically", action="store_true")
    args = parser.parse_args(argv)

    post_path = Path(args.post_file or args.post)
    post_data = yaml.safe_load(post_path.read_text(encoding="utf-8"))
    api = _api_from_env(args.cookies)

    markdown = post_data.get("markdown")
    markdown_file = post_data.get("markdown_file")
    if markdown_file:
        markdown_path = Path(markdown_file)
        if not markdown_path.is_absolute():
            markdown_path = post_path.parent / markdown_path
        markdown = markdown_path.read_text(encoding="utf-8")

    if markdown is not None:
        result = api.create_draft_from_markdown(
            title=post_data.get("title"),
            markdown=markdown,
            subtitle=post_data.get("subtitle", ""),
            audience=post_data.get("audience", "everyone"),
            write_comment_permissions=post_data.get(
                "write_comment_permissions", "everyone"
            ),
            search_engine_title=post_data.get("search_engine_title"),
            search_engine_description=post_data.get("search_engine_description"),
            slug=post_data.get("slug"),
            draft_section_id=post_data.get("draft_section_id"),
            tags=post_data.get("tags"),
            prepublish=args.prepublish or args.publish,
            publish=args.publish,
            send=args.send,
            share_automatically=args.share_automatically,
        )
        _print_result(result)
        return 0

    post = Post(
        post_data.get("title"),
        post_data.get("subtitle", ""),
        api.get_user_id(),
        audience=post_data.get("audience", "everyone"),
        write_comment_permissions=post_data.get(
            "write_comment_permissions", "everyone"
        ),
    )

    section = post_data.get("section")
    if section:
        post.set_section(section, api.get_sections())

    for item in post_data.get("body", {}).values():
        if item.get("type") == "captionedImage":
            src = item.get("src", "")
            if not src.startswith("http"):
                image = api.get_image(src)
                item.update({"src": image.get("url")})
        post.add(item)

    draft = api.post_draft(post.get_draft())
    draft_id = draft.get("id")

    update_payload = {
        "draft_section_id": post.draft_section_id,
        "search_engine_title": post_data.get("search_engine_title"),
        "search_engine_description": post_data.get("search_engine_description"),
        "slug": post_data.get("slug"),
    }
    update_payload = {
        key: value for key, value in update_payload.items() if value is not None
    }
    if update_payload:
        draft = api.put_draft(draft_id, **update_payload)

    tags = Api._normalize_tags(post_data.get("tags"))
    if tags:
        api.add_tags_to_post(draft_id, tags)

    if args.prepublish or args.publish:
        api.prepublish_draft(draft_id)
    if args.publish:
        api.publish_draft(
            draft_id,
            send=args.send,
            share_automatically=args.share_automatically,
        )

    print(json.dumps({"draft_id": draft_id, "draft": draft}, indent=2))
    return 0


def auth_check(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookies")
    args = parser.parse_args(argv)

    api = _api_from_env(args.cookies)
    profile = api.get_user_profile()
    primary_publication = api.get_user_primary_publication()
    publications = api.get_user_publications()

    identity = (
        profile.get("email")
        or profile.get("name")
        or profile.get("handle")
        or str(profile.get("id", "unknown"))
    )

    print(f"Authenticated as: {identity}")
    print(f"Auth method: {_auth_method(args.cookies)}")
    print(f"Primary publication: {primary_publication.get('name', 'unknown')}")
    print(f"Publication URL: {primary_publication.get('publication_url', 'unknown')}")
    print(f"Available publications: {len(publications)}")
    return 0
