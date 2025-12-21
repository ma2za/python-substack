import argparse
import os

import yaml
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--post",
        default="draft.yaml",
        required=False,
        help="YAML file containing the post to publish.",
        type=str,
    )
    parser.add_argument(
        "--publish", help="Publish the draft.", action="store_true", default=True
    )
    parser.add_argument(
        "--cookies",
        help="Path to cookies JSON file for authentication (optional, can also be set via COOKIES_PATH or COOKIES_STRING env vars).",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    with open(args.post, "r") as fp:
        post_data = yaml.safe_load(fp)

    cookies_path = args.cookies or os.getenv("COOKIES_PATH")
    cookies_string = os.getenv("COOKIES_STRING")

    api = Api(
        email=os.getenv("EMAIL") if not cookies_path and not cookies_string else None,
        password=os.getenv("PASSWORD") if not cookies_path and not cookies_string else None,
        cookies_path=cookies_path,
        cookies_string=cookies_string,
        publication_url=os.getenv("PUBLICATION_URL"),
    )

    user_id = api.get_user_id()

    post = Post(
        post_data.get("title"),
        post_data.get("subtitle", ""),
        user_id,
        audience=post_data.get("audience", "everyone"),
        write_comment_permissions=post_data.get(
            "write_comment_permissions", "everyone"
        ),
    )

    body = post_data.get("body", {})

    for _, item in body.items():
        if item.get("type") == "captionedImage":
            image = api.get_image(item.get("src"))
            item.update({"src": image.get("url")})
        post.add(item)

    draft = api.post_draft(post.get_draft())

    # post.set_section(post_data.get("section"), api.get_sections())
    api.put_draft(draft.get("id"), draft_section_id=post.draft_section_id)

    if args.publish:
        api.prepublish_draft(draft.get("id"))

        api.publish_draft(draft.get("id"))
