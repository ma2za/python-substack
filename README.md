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

## Add a YouTube video

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

draft = api.post_draft(post.get_draft())

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
```

