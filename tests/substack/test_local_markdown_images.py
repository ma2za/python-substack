"""Offline regression tests for Markdown local-image uploads."""

import os
from pathlib import Path
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
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
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
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
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


@pytest.mark.skipif(
    os.name == "nt",
    reason="Drive-qualified paths do not have a legacy root-relative fallback",
)
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


@pytest.fixture
def post_dir(tmp_path, monkeypatch):
    """A Markdown file's folder that is not the working directory."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    folder = tmp_path / "posts" / "first post"
    (folder / "figures").mkdir(parents=True)
    return folder


def render_from(markdown, api, markdown_dir):
    post = Post(title="Image test", subtitle="", user_id=1)
    post.from_markdown(markdown, api=api, markdown_dir=markdown_dir)
    return post.draft_body["content"]


@pytest.mark.parametrize("as_type", [str, lambda path: path])
def test_relative_file_found_beside_markdown(api, post_dir, as_type):
    image = post_dir / "figures" / "obraz żółty.png"
    image.touch()
    content = render_from("![alt](<figures/obraz żółty.png>)", api, as_type(post_dir))
    assert content[0]["content"][0]["attrs"]["src"] == UPLOADED
    api.get_image.assert_called_once_with(str(image))


@pytest.mark.parametrize(
    "markdown",
    [
        "> ![alt](figures/chart.png)",
        "- ![alt](figures/chart.png)",
        "1. Item\n\n   ![alt](figures/chart.png)",
        ":::callout\n![alt](figures/chart.png)\n:::",
        "Text.[^note]\n\n[^note]: ![alt](figures/chart.png)",
    ],
)
def test_nested_relative_file_found_beside_markdown(api, post_dir, markdown):
    image = post_dir / "figures" / "chart.png"
    image.touch()
    render_from(markdown, api, post_dir)
    api.get_image.assert_called_once_with(str(image))


def test_working_directory_takes_priority_over_markdown_folder(api, post_dir):
    (post_dir / "image.png").touch()
    Path("image.png").touch()
    render_from("![alt](image.png)", api, post_dir)
    api.get_image.assert_called_once_with("image.png")


def test_file_missing_from_both_folders_fails_before_upload(api, post_dir):
    with pytest.raises(FileNotFoundError) as error:
        render_from("![alt](figures/missing.png)", api, post_dir)
    # The message names the path as written, as it does without markdown_dir.
    written = Path("figures/missing.png")
    assert str(error.value) == f"Local image file not found: {written}"
    api.get_image.assert_not_called()


@pytest.mark.parametrize("src", ["/image.png", "~/image.png"])
def test_rooted_and_home_paths_ignore_markdown_folder(
    tmp_path, monkeypatch, api, post_dir, src
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    (post_dir / "image.png").touch()
    with pytest.raises(FileNotFoundError):
        render_from(f"![alt]({src})", api, post_dir)
    api.get_image.assert_not_called()


def test_directory_beside_markdown_is_not_an_image(api, post_dir):
    with pytest.raises(FileNotFoundError):
        render_from("![alt](figures)", api, post_dir)
    api.get_image.assert_not_called()


def test_remote_url_ignores_markdown_folder(api, post_dir):
    content = render_from("![alt](https://example.com/a.png)", api, post_dir)
    assert content[0]["content"][0]["attrs"]["src"] == "https://example.com/a.png"
    api.get_image.assert_not_called()


def test_create_draft_from_markdown_finds_file_beside_markdown(api, post_dir):
    image = post_dir / "figures" / "chart.png"
    image.touch()
    api.get_user_id = Mock(return_value=1)
    api.post_draft = Mock(return_value={"id": 123})
    api.create_draft_from_markdown(
        title="Title", markdown="![alt](figures/chart.png)", markdown_dir=post_dir
    )
    api.get_image.assert_called_once_with(str(image))


def test_update_draft_from_markdown_finds_file_beside_markdown(api, post_dir):
    image = post_dir / "figures" / "chart.png"
    image.touch()
    api.get_user_id = Mock(return_value=1)
    api.get_draft = Mock(
        return_value={"id": 42, "draft_body": '{"type":"doc","content":[]}'}
    )
    api.put_draft = Mock(return_value={"id": 42})
    api.update_draft_from_markdown(
        42,
        "![alt](figures/chart.png)",
        allow_conflict=True,
        allow_image_replacement=True,
        markdown_dir=post_dir,
    )
    api.get_image.assert_called_once_with(str(image))
