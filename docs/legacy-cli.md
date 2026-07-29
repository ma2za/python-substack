# Legacy CLI commands

The original standalone console commands remain supported for compatibility.
New automation should prefer the unified `substack` command.

Check authentication:

```bash
substack-auth-check
substack-auth-check --cookies cookies.json
```

Create a Markdown draft:

```bash
substack-publish-markdown post.md --title "My Post"
```

Create and publish only when explicitly requested:

```bash
substack-publish-markdown post.md --title "My Post" --publish
```

Create or publish from YAML:

```bash
substack-publish-yaml draft.yaml
```

Markdown options:

```bash
substack-publish-markdown post.md \
  --title "My Post" \
  --subtitle "Optional subtitle" \
  --tag python \
  --tag substack \
  --slug my-post \
  --search-engine-title "SEO title" \
  --search-engine-description "SEO description"
```

Both publishing commands create drafts by default. `--publish` opts into
publishing. `--no-send` prevents email delivery when publishing.
