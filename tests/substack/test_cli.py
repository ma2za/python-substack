from substack import cli


class FakeApi:
    def __init__(self):
        self.kwargs = None

    def create_draft_from_markdown(self, **kwargs):
        self.kwargs = kwargs
        return {"draft": {"id": 42}}

    def get_user_profile(self):
        return {"email": "writer@example.com"}

    def get_user_primary_publication(self):
        return {
            "name": "Writer Notes",
            "publication_url": "https://writer.substack.com",
        }

    def get_user_publications(self):
        return [
            {"name": "Writer Notes"},
            {"name": "Second Pub"},
        ]


def test_publish_markdown_creates_draft_by_default(tmp_path, monkeypatch, capsys):
    markdown = tmp_path / "post.md"
    markdown.write_text("# Title from file\n\nBody", encoding="utf-8")
    api = FakeApi()
    monkeypatch.setattr(cli, "_api_from_env", lambda cookies_path=None: api)

    result = cli.publish_markdown([str(markdown)])

    assert result == 0
    assert api.kwargs["title"] == "Title from file"
    assert api.kwargs["publish"] is False
    assert api.kwargs["prepublish"] is False
    assert '"draft_id": 42' in capsys.readouterr().out


def test_publish_markdown_publish_flag_prepublishes_and_publishes(
    tmp_path, monkeypatch
):
    markdown = tmp_path / "post.md"
    markdown.write_text("Body", encoding="utf-8")
    api = FakeApi()
    monkeypatch.setattr(cli, "_api_from_env", lambda cookies_path=None: api)

    result = cli.publish_markdown(
        [
            str(markdown),
            "--title",
            "Explicit title",
            "--tag",
            "python",
            "--publish",
            "--no-send",
        ]
    )

    assert result == 0
    assert api.kwargs["title"] == "Explicit title"
    assert api.kwargs["tags"] == ["python"]
    assert api.kwargs["publish"] is True
    assert api.kwargs["prepublish"] is True
    assert api.kwargs["send"] is False


def test_auth_check_prints_profile_and_publication(monkeypatch, capsys):
    api = FakeApi()
    monkeypatch.setattr(cli, "_api_from_env", lambda cookies_path=None: api)
    monkeypatch.setattr(cli, "_auth_method", lambda cookies_path=None: "cookies_path")

    result = cli.auth_check(["--cookies", "cookies.json"])

    assert result == 0
    output = capsys.readouterr().out
    assert "Authenticated as: writer@example.com" in output
    assert "Auth method: cookies_path" in output
    assert "Primary publication: Writer Notes" in output
    assert "Publication URL: https://writer.substack.com" in output
    assert "Available publications: 2" in output


def test_auth_method_prefers_explicit_cookies_path(monkeypatch):
    monkeypatch.delenv("COOKIES_PATH", raising=False)
    monkeypatch.delenv("COOKIES_STRING", raising=False)
    monkeypatch.setenv("EMAIL", "writer@example.com")
    monkeypatch.setenv("PASSWORD", "secret")

    assert cli._auth_method("cookies.json") == "cookies_path"


def test_auth_method_reads_env(monkeypatch):
    monkeypatch.delenv("EMAIL", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("COOKIES_PATH", raising=False)
    monkeypatch.setenv("COOKIES_STRING", "substack.sid=value")

    assert cli._auth_method() == "cookies_string"
