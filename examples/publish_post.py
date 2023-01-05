import os

from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

content = """
1)

Set the EMAIL, PASSWORD and PUBLICATION_URL environment variables.

2)

Discover your USER ID by inspecting the request body of any publish request.

"""

api = Api(
	email=os.getenv("EMAIL"),
	password=os.getenv("PASSWORD"),
	publication_url=os.getenv("PUBLICATION_URL"),
)

body = f'{{"type":"doc","content": {content}}}'

post = Post("How to publish a Substack post using the Python API",
            "This post was published using the Python API",
            os.getenv("USER_ID"))
post.paragraph().text("Set the EMAIL, PASSWORD and PUBLICATION_URL environment variables.")

draft = api.post_draft(post.get_draft())

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
print()
