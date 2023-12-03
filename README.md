# Python Substack

This is an unofficial library providing a Python interface for [Substack](https://substack.com/).
I am in no way affiliated with Substack.

[![Python](https://img.shields.io/pypi/pyversions/fastapi.svg?color=%2334D058)](https://www.python.org/downloads/)
[![Downloads](https://static.pepy.tech/badge/python-substack/month)](https://pepy.tech/project/python-substack)
![Release Build](https://github.com/ma2za/python-substack/actions/workflows/ci_publish.yml/badge.svg)
---

# Installation

You can install python-substack using:

    $ pip install python-substack

---

# Setup

Set the following environment variables by creating a **.env** file:

    PUBLICATION_URL=https://ma2za.substack.com
    EMAIL=
    PASSWORD=
    USER_ID=

To discover the USER_ID go to your public profile page,
in the URL bar of the browser you find the substack address
followed by your USER_ID and your username:
https://substack.com/profile/[USER_ID]-[username]

The .env file will be ignored by git but always be careful.

---

# Usage

Check out the examples folder for some examples 😃 🚀

```python
import os

from substack import Api
from substack.post import Post

api = Api(
    email=os.getenv("EMAIL"),
    password=os.getenv("PASSWORD"),
    publication_url=os.getenv("PUBLICATION_URL"),
)

post = Post(
    title="How to publish a Substack post using the Python API",
    subtitle="This post was published using the Python API",
    user_id=os.getenv("USER_ID")
)

post.add({'type': 'paragraph', 'content': 'This is how you add a new paragraph to your post!'})

# bolden text
post.add({'type': "paragraph",
          'content': [{'content': "This is how you "}, {'content': "bolden ", 'marks': [{'type': "strong"}]},
                      {'content': "a word."}]})

# add hyperlink to text
post.add({'type': 'paragraph', 'content': [
    {'content': "View Link", 'marks': [{'type': "link", 'href': 'https://whoraised.substack.com/'}]}]})

# set paywall boundary
post.add({'type': 'paywall'})

# add image
post.add({'type': 'captionedImage', 'src': "https://media.tenor.com/7B4jMa-a7bsAAAAC/i-am-batman.gif"})

# add local image
image = api.get_image('image.png')
post.add({"type": "captionedImage", "src": image.get("url")})

draft = api.post_draft(post.get_draft())

# set section (THIS CAN BE DONE ONLY AFTER HAVING FIRST POSTED THE DRAFT)
post.set_section("rick rolling", api.get_sections())
api.put_draft(draft.get("id"), draft_section_id=post.draft_section_id)

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
```

