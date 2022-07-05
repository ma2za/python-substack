import os

from dotenv import load_dotenv

from substack import Api

load_dotenv()

content = ""
title = ""
subtitle = ""

api = Api(
    email=os.getenv("EMAIL"),
    password=os.getenv("PASSWORD"),
    publication_url=os.getenv("PUBLICATION_URL"),
)

body = f'{{"type":"doc","content": {content}}}'

draft = api.post_draft(
    [{"id": os.getenv("USER_ID"), "is_guest": False}],
    title=title,
    subtitle=subtitle,
    body=body,
)

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
