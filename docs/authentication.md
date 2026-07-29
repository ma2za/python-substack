# Authentication

python-substack accepts email and password credentials, a cookies JSON file, or
a browser cookie header string.

## Environment

```env
EMAIL=
PASSWORD=
PUBLICATION_URL=
COOKIES_PATH=
COOKIES_STRING=
```

Use either `EMAIL` and `PASSWORD`, or one cookie method. When both cookie
methods and email credentials are present, cookie authentication takes
precedence.

## Cookie file

```python
import os

from substack import Api

api = Api(
    cookies_path=os.getenv("COOKIES_PATH"),
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

Export the active session for later use:

```python
api.export_cookies("cookies.json")
```

Set `COOKIES_PATH=cookies.json` or pass the file to the CLI:

```bash
substack --cookies cookies.json status
```

## Browser cookie string

1. Sign in to Substack in a browser.
2. Open developer tools and select the network tab.
3. Refresh Substack.
4. Select an authenticated request.
5. Copy the complete `cookie` request header value into `COOKIES_STRING`.

```python
api = Api(
    cookies_string=os.getenv("COOKIES_STRING"),
    publication_url=os.getenv("PUBLICATION_URL"),
)
```

Never commit `.env`, cookie files, passwords, or copied request headers.

## Password sign-in

Some accounts use magic-link sign-in by default. To configure a password, sign
out of Substack, choose "Sign in with password", and then choose "Set a new
password".

## Publication selection

Set `PUBLICATION_URL` for the default publication or override it for one
unified CLI invocation:

```bash
substack --publication-url https://example.substack.com status
```

List the publications available to the authenticated account:

```bash
substack publications list
```
