# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability involving credentials,
authentication, publishing, or private publication data.

Report it privately through GitHub's private vulnerability reporting for this
repository. If that option is unavailable, email
`mazzapaolo2019@gmail.com` with the subject `python-substack security report`.

Include:

- The affected python-substack version.
- The impact and conditions required to reproduce it.
- A minimal reproduction with all credentials removed.
- Any suggested mitigation.

Do not include passwords, session cookies, full request headers, publication
exports, or subscriber data.

The maintainer will acknowledge a complete report, assess affected versions,
and coordinate a compatible fix and disclosure. No response-time guarantee is
made for this volunteer-maintained project.

## Supported versions

Security fixes target the latest published version. Older releases may require
an upgrade. The project does not intentionally break public interfaces in the
1.x series.

## Scope

This package uses undocumented Substack interfaces and user-supplied
credentials. Upstream API changes and account-specific authentication failures
are compatibility defects, not security vulnerabilities, unless they expose
credentials or private data or allow an unintended write or publication.
