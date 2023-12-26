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

    EMAIL=
    PASSWORD=

## If you don't have a password

Recently Substack has been setting up new accounts without a password. If you sign-out and sign back in it just uses
your email address with a "magic" link.

Set a password:

- Sign-out of Substack
- At the sign-in page click, "Sign in with password" under the `Email` text box
- Then choose, "Set a new password"

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
)

user_id = api.get_user_id()

# Switch Publications - The library defaults to your users primary publication. You can retrieve all your publications and change which one you want to use.

# primary publication
user_publication = api.get_user_primary_publication()
# all publications
user_publications = api.get_user_publications()

# This step is only necessary if you are not using your primary publication
# api.change_publication(user_publication)

post = Post(
    title="How to publish a Substack post using the Python API",
    subtitle="This post was published using the Python API",
    user_id=user_id
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

# embed publication
embedded = api.publication_embed("https://jackio.substack.com/")
post.add({"type": "embeddedPublication", "url": embedded})

draft = api.post_draft(post.get_draft())

# set section (THIS CAN BE DONE ONLY AFTER HAVING FIRST POSTED THE DRAFT)
post.set_section("rick rolling", api.get_sections())
api.put_draft(draft.get("id"), draft_section_id=post.draft_section_id)

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
```

# Contributing

Install pre-commit:

```shell
pip install pre-commit
```

Set up pre-commit

```shell
pre-commit install
```
