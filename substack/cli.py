import argparse
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from substack import Api
from substack.post import Post


def _api_from_env(cookies_path=None):
    load_dotenv()

    cookies_path = cookies_path or os.getenv("COOKIES_PATH")
    cookies_string = os.getenv("COOKIES_STRING")

    if cookies_path or cookies_string:
        return Api(
            cookies_path=cookies_path,
            cookies_string=cookies_string,
            publication_url=os.getenv("PUBLICATION_URL"),
        )

    return Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=os.getenv("PUBLICATION_URL"),
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
