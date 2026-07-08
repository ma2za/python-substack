from pathlib import Path


def test_publish_flags_use_store_true():
    root = Path(__file__).parents[2]
    for path in [
        root / "examples" / "publish_post.py",
        root / "examples" / "publish_markdown.py",
    ]:
        source = path.read_text(encoding="utf-8")
        assert '"--publish", help="Publish the draft.", action="store_true"' in source
        assert (
            '"--publish", help="Publish the draft.", action="store_false"' not in source
        )
