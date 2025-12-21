# Python Substack

This is an unofficial library providing a Python interface for [Substack](https://substack.com/).
I am in no way affiliated with Substack.

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
    PUBLICATION_URL=  # Optional: your publication URL
    COOKIES_PATH=     # Optional: path to cookies JSON file
    COOKIES_STRING=   # Optional: cookie string for authentication

## If you don't have a password

Recently Substack has been setting up new accounts without a password. If you sign out and sign back in, it just uses
your email address with a "magic" link.

Set a password:

- Sign out of Substack
- At the sign-in page, click "Sign in with password" under the `Email` text box
- Then choose, "Set a new password"

The .env file will be ignored by git but always be careful.

---

# Usage

Check out the examples folder for some examples 😃 🚀

## Basic Authentication

```python
import os
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

# Authenticate with email and password
api = Api(
    email=os.getenv("EMAIL"),
    password=os.getenv("PASSWORD"),
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

## Cookie-based Authentication

You can also authenticate using cookies instead of email/password:

```python
import os
from dotenv import load_dotenv

from substack import Api

load_dotenv()

# Authenticate with cookies (alternative to email/password)
api = Api(
    cookies_path=os.getenv("COOKIES_PATH"),  # Path to cookies JSON file
    # OR
    cookies_string=os.getenv("COOKIES_STRING"),  # Cookie string
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

## Creating and Publishing Posts

```python
user_id = api.get_user_id()

# Switch Publications - The library defaults to your user's primary publication. You can retrieve all your publications and change which one you want to use.

# primary publication
user_publication = api.get_user_primary_publication()
# all publications
user_publications = api.get_user_publications()

# This step is only necessary if you are not using your primary publication
# api.change_publication(user_publication)

# Create a post with basic settings
post = Post(
    title="How to publish a Substack post using the Python API",
    subtitle="This post was published using the Python API",
    user_id=user_id
)

# Create a post with audience and comment permissions
post = Post(
    title="My Post Title",
    subtitle="My Post Subtitle",
    user_id=user_id,
    audience="everyone",  # Options: "everyone", "only_paid", "founding", "only_free"
    write_comment_permissions="everyone"  # Options: "none", "only_paid", "everyone"
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

# create post from Markdown
markdown_content = """
# My Heading

This is a paragraph with **bold** and *italic* text.

![Image Alt](https://example.com/image.jpg)
"""
post.from_markdown(markdown_content, api=api)

draft = api.post_draft(post.get_draft())

# set section (can only be done after first posting the draft)
# post.set_section("rick rolling", api.get_sections())
# api.put_draft(draft.get("id"), draft_section_id=post.draft_section_id)

api.prepublish_draft(draft.get("id"))

api.publish_draft(draft.get("id"))
```

## Loading Posts from YAML Files

You can define your posts in YAML files for easier management:

```python
import yaml
import os
from dotenv import load_dotenv

from substack import Api
from substack.post import Post

load_dotenv()

# Load post data from YAML file
with open("draft.yaml", "r") as fp:
    post_data = yaml.safe_load(fp)

# Authenticate (using cookies or email/password)
cookies_path = os.getenv("COOKIES_PATH")
cookies_string = os.getenv("COOKIES_STRING")

api = Api(
    email=os.getenv("EMAIL") if not cookies_path and not cookies_string else None,
    password=os.getenv("PASSWORD") if not cookies_path and not cookies_string else None,
    cookies_path=cookies_path,
    cookies_string=cookies_string,
    publication_url=os.getenv("PUBLICATION_URL"),
)

user_id = api.get_user_id()

# Create post from YAML data
post = Post(
    post_data.get("title"),
    post_data.get("subtitle", ""),
    user_id,
    audience=post_data.get("audience", "everyone"),
    write_comment_permissions=post_data.get("write_comment_permissions", "everyone"),
)

# Add body content from YAML
body = post_data.get("body", {})
for _, item in body.items():
    # Handle local images - upload them first
    if item.get("type") == "captionedImage" and not item.get("src").startswith("http"):
        image = api.get_image(item.get("src"))
        item.update({"src": image.get("url")})
    post.add(item)

draft = api.post_draft(post.get_draft())
api.put_draft(draft.get("id"), draft_section_id=post.draft_section_id)

# Publish the draft
api.prepublish_draft(draft.get("id"))
api.publish_draft(draft.get("id"))
```

Example YAML structure:

```yaml
title: "My Post Title"
subtitle: "My Post Subtitle"
audience: "everyone"  # everyone, only_paid, founding, only_free
write_comment_permissions: "everyone"  # none, only_paid, everyone
section: "my-section"
body:
  0:
    type: "heading"
    level: 1
    content: "Introduction"
  1:
    type: "paragraph"
    content: "This is a paragraph."
  2:
    type: "captionedImage"
    src: "local_image.jpg"  # Local images will be uploaded automatically
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

## Cookie Help

To get a cookie string, after login, go to dev tools (F12), network tab, refresh and find one of the requests like subscription/unred/subscriptions, right click and copy as fetch (Node.js), paste somewhere and get the entire cookie string assigned to the cookie header and put it in the env variables as COOKIES_STRING, et voila!
