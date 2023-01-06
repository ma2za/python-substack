import argparse
import os

import yaml
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-p", "--post", default="draft.yaml", required=True,
	                    help="YAML file containing the post to publish.", type=str)
	parser.add_argument("--publish", help="Publish the draft.", action="store_true")
	args = parser.parse_args()

	with open(args.post, "r") as fp:
		post_data = yaml.safe_load(fp)

	title = post_data.get("title", "")
	subtitle = post_data.get("subtitle", "")
	body = post_data.get("body", {})

	api = Api(
		email=os.getenv("EMAIL"),
		password=os.getenv("PASSWORD"),
		publication_url=os.getenv("PUBLICATION_URL"),
	)

	post = Post(title, subtitle, os.getenv("USER_ID"))
	for _, item in body.items():
		post.add(item)

	draft = api.post_draft(post.get_draft())

	if args.publish:
		api.prepublish_draft(draft.get("id"))

		api.publish_draft(draft.get("id"))
