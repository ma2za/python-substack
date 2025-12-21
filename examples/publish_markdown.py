"""
Example: Publishing a post from Markdown content

This example demonstrates how to use the new Markdown support
to create Substack posts from Markdown files.

This example reads from README.md to test the Markdown parsing.
"""

import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--markdown",
        default="README.md",
        required=False,
        help="Markdown file to publish (default: README.md).",
        type=str,
    )
    parser.add_argument(
        "--publish", help="Publish the draft.", action="store_true", default=False
    )
    parser.add_argument(
        "--cookies",
        help="Path to cookies JSON file for authentication (optional, can also be set via COOKIES_PATH or COOKIES_STRING env vars).",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    cookies_path = args.cookies or os.getenv("COOKIES_PATH")
    cookies_string = os.getenv("COOKIES_STRING")

    # Initialize API
    api = Api(
        email=os.getenv("EMAIL") if not cookies_path and not cookies_string else None,
        password=os.getenv("PASSWORD") if not cookies_path and not cookies_string else None,
        cookies_path=cookies_path,
        cookies_string=cookies_string,
        publication_url=os.getenv("PUBLICATION_URL"),
    )

    user_id = api.get_user_id()

    # Determine the markdown file path
    markdown_path = Path(args.markdown)
    if not markdown_path.is_absolute():
        # If relative path, try relative to current directory first, then parent directory
        if markdown_path.exists():
            pass  # Use as-is
        else:
            # Try relative to parent directory (for README.md in project root)
            markdown_path = Path(__file__).parent.parent / args.markdown
    
    if not markdown_path.exists():
        print(f"Error: Markdown file not found at {markdown_path}")
        exit(1)
    
    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()
    
    # Extract title from first heading (if it starts with #)
    title = "Python Substack"
    subtitle = "Markdown Test Post"
    
    lines = markdown_content.split("\n")
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
        elif line.startswith("#"):
            # Skip badge lines and other non-title content
            continue
    
    # Create a post
    post = Post(
        title=title,
        subtitle=subtitle,
        user_id=user_id,
    )

    # Parse and add Markdown content
    print(f"Parsing Markdown from {markdown_path}...")
    post.from_markdown(markdown_content, api=api)

    # Create draft
    print("Creating draft...")
    draft = api.post_draft(post.get_draft())

    if args.publish:
        print("Preparing to publish...")
        api.prepublish_draft(draft.get("id"))
        print("Publishing...")
        api.publish_draft(draft.get("id"))
        print("Post published successfully!")
    else:
        print(f"Draft created with ID: {draft.get('id')}")
        print(f"Title: {title}")
        print(f"Subtitle: {subtitle}")
        print("Use --publish flag to publish the draft.")

