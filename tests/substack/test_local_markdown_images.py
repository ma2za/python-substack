"""Offline regression tests for Markdown local-image uploads."""

from unittest.mock import Mock

import pytest

from substack.api import Api
from substack.post import Post

UPLOADED = "https://substack-post-media.s3.amazonaws.com/test-image.gif"


@pytest.fixture
def api():
    client = Api.__new__(Api)
    client.get_image = Mock(return_value={"url": UPLOADED})
    return client


def render(src, api=None):
    post = Post(title="Image test", subtitle="", user_id=1)
    post.from_markdown(f'![alt](<{src}> "caption")', api=api)
    return post.draft_body["content"][0]["content"][0]["attrs"]["src"]


@pytest.mark.parametrize("extension", ["png", "jpg", "gif", "webp"])
def test_absolute_file_uploaded_unchanged(tmp_path, api, extension):
    path = tmp_path / f"image.{extension}"
    path.write_bytes(b"image bytes")
    assert render(str(path), api) == UPLOADED
    api.get_image.assert_called_once_with(str(path))


def test_home_path_expanded(tmp_path, monkeypatch, api):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / "image.png"
    path.touch()
    assert render("~/image.png", api) == UPLOADED
    api.get_image.assert_called_once_with(str(path))


def test_spaces_unicode_and_percent_in_filename(tmp_path, api):
    path = tmp_path / "obraz żółty 100%.png"
    path.touch()
    assert render(str(path), api) == UPLOADED
    api.get_image.assert_called_once_with(str(path))


@pytest.mark.parametrize("src", ["missing.png", "/missing/image.gif", "~/missing.webp"])
def test_missing_file_fails_before_upload(tmp_path, monkeypatch, api, src):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="Local image file not found:") as error:
        render(src, api)
    assert src.rsplit("/", 1)[-1] in str(error.value)
    api.get_image.assert_not_called()


def test_directory_is_not_an_image(tmp_path, api):
    with pytest.raises(FileNotFoundError):
        render(str(tmp_path), api)
    api.get_image.assert_not_called()


@pytest.mark.parametrize("src", ["image.png", "/image.png"])
def test_relative_and_legacy_root_relative_file(tmp_path, monkeypatch, api, src):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "image.png").touch()
    assert render(src, api) == UPLOADED
    api.get_image.assert_called_once_with("image.png")


def test_absolute_file_takes_priority_over_relative(tmp_path, monkeypatch, api):
    absolute = tmp_path / "image.png"
    absolute.touch()
    cwd = tmp_path / "cwd"
    shadow = cwd / str(absolute)[1:]
    shadow.parent.mkdir(parents=True)
    shadow.touch()
    monkeypatch.chdir(cwd)
    assert render(str(absolute), api) == UPLOADED
    api.get_image.assert_called_once_with(str(absolute))


def test_upload_error_names_file(tmp_path, api):
    path = tmp_path / "failed.gif"
    path.touch()
    api.get_image.side_effect = RuntimeError("upload refused")
    with pytest.raises(ValueError, match="Failed to upload local image:") as error:
        render(str(path), api)
    assert str(path) in str(error.value)
    assert error.value.__cause__ is api.get_image.side_effect


@pytest.mark.parametrize(
    "result", [{}, {"url": None}, {"url": ""}, {"url": "local.png"}, None]
)
def test_invalid_upload_result_fails(tmp_path, api, result):
    path = tmp_path / "failed.png"
    path.touch()
    api.get_image.return_value = result
    with pytest.raises(ValueError, match="failed.png"):
        render(str(path), api)


@pytest.mark.parametrize(
    "src",
    ["http://example.com/a.jpg", "https://example.com/a.png", "//example.com/a.gif"],
)
def test_remote_url_unchanged(api, src):
    assert render(src, api) == src
    api.get_image.assert_not_called()


@pytest.mark.parametrize(
    "src", ["/missing/image.png", "~/missing.gif", "relative.webp"]
)
def test_without_api_retains_source(src):
    assert render(src) == src
