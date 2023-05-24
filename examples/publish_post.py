import argparse
import os

import yaml
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--post", default="draft.yaml", required=False,
                        help="YAML file containing the post to publish.", type=str)
    parser.add_argument("--publish", help="Publish the draft.", action="store_true", default=False)
    args = parser.parse_args()

    with open(args.post, "r") as fp:
        post_data = yaml.safe_load(fp)

    api = Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=os.getenv("PUBLICATION_URL"),
    )

    post = Post(post_data.get("title"),
                post_data.get("subtitle", ""),
                os.getenv("USER_ID"),
                audience=post_data.get("audience", "everyone"),
                write_comment_permissions=post_data.get("write_comment_permissions", "everyone"))

    body = post_data.get("body", {})

    for _, item in body.items():
        if item.get("type") == "captionedImage":
            image = api.get_image(item.get("src"))
            item.update({"src": image.get("url")})
        post.add(item)

    draft = api.post_draft(post.get_draft())

    if args.publish:
        api.prepublish_draft(draft.get("id"))

        api.publish_draft(draft.get("id"))
