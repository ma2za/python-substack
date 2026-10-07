import base64
import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from markdown_it import MarkdownIt


def compute_draft_revision(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Compute deterministic revision and fingerprint metadata from a Substack draft dict."""
    draft_id = draft.get("id")
    title = (
        draft.get("draft_title") if "draft_title" in draft else draft.get("title", "")
    )
    subtitle = (
        draft.get("draft_subtitle")
        if "draft_subtitle" in draft
        else draft.get("subtitle", "")
    )
    audience = draft.get("audience") or "everyone"
    write_comment_permissions = draft.get("write_comment_permissions") or "everyone"
    draft_section_id = (
        draft.get("draft_section_id")
        if "draft_section_id" in draft
        else draft.get("section_id")
    )
    slug = draft.get("slug") or ""
    updated_at = draft.get("draft_updated_at") or draft.get("updated_at")

    raw_body = draft.get("draft_body")
    if isinstance(raw_body, str):
        try:
            body_obj = json.loads(raw_body)
        except Exception:
            body_obj = raw_body
    else:
        body_obj = raw_body

    if isinstance(body_obj, (dict, list)):
        body_canonical = json.dumps(
            body_obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
    else:
        body_canonical = str(body_obj or "")

    body_hash = hashlib.sha256(body_canonical.encode("utf-8")).hexdigest()

    fingerprint_components = {
        "draft_id": draft_id,
        "body_hash": body_hash,
        "title": title or "",
        "subtitle": subtitle or "",
        "audience": audience,
        "write_comment_permissions": write_comment_permissions,
        "draft_section_id": draft_section_id,
        "slug": slug,
    }
    fingerprint_bytes = json.dumps(
        fingerprint_components,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    revision_hash = hashlib.sha256(fingerprint_bytes).hexdigest()

    return {
        "version": 1,
        "draft_id": draft_id,
        "revision": revision_hash,
        "body_hash": body_hash,
        "title": title or "",
        "subtitle": subtitle or "",
        "audience": audience,
        "write_comment_permissions": write_comment_permissions,
        "draft_section_id": draft_section_id,
        "slug": slug,
        "updated_at": str(updated_at) if updated_at else None,
    }


def format_revision_marker(revision_info: Dict[str, Any]) -> str:
    """Format revision metadata as a versioned HTML comment marker."""
    payload = json.dumps(
        revision_info, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    return f"<!-- python-substack-revision:v1 {encoded} -->"


def parse_revision_marker(markdown: str) -> Optional[Dict[str, Any]]:
    """
    Parse a python-substack-revision:v1 comment marker from markdown content.

    Only top-level HTML comment blocks are considered; comments inside code blocks
    are ignored.

    Returns the parsed revision dictionary, or None if no marker is found.
    Raises ValueError if an attempted marker is corrupt, malformed, unsupported, or duplicated.
    """
    md = MarkdownIt()
    tokens = md.parse(markdown)

    found_markers = []
    marker_pattern = re.compile(
        r"^<!--\s*python-substack-revision:v([0-9]+)\s+([A-Za-z0-9_-]+=*)\s*-->$"
    )

    for token in tokens:
        if token.type == "html_block":
            clean = token.content.strip()
            match = marker_pattern.match(clean)
            if match:
                found_markers.append(match.groups())
            elif "python-substack-revision:" in clean:
                raise ValueError(
                    "Malformed revision marker: corrupt comment format or invalid characters"
                )

    if not found_markers:
        return None

    if len(found_markers) > 1:
        raise ValueError("Malformed revision marker: multiple revision markers found")

    version_str, encoded = found_markers[0]
    if version_str != "1":
        raise ValueError(
            f"Malformed revision marker: unsupported version '{version_str}'"
        )

    pad = len(encoded) % 4
    if pad:
        encoded += "=" * (4 - pad)

    try:
        raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
    except Exception as exc:
        raise ValueError("Malformed revision marker: invalid base64 encoding") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Malformed revision marker: invalid JSON payload") from exc

    if not isinstance(data, dict):
        raise ValueError("Malformed revision marker: payload must be a JSON object")

    if not data.get("revision") or not isinstance(data.get("revision"), str):
        raise ValueError(
            "Malformed revision marker: missing or empty required 'revision' field"
        )

    return data


def compare_draft_revisions(
    expected: Dict[str, Any], current: Dict[str, Any]
) -> List[str]:
    """
    Compare expected revision metadata with current remote draft revision metadata.

    Returns a list of human-readable, actionable mismatch descriptions.
    If the list is empty, there is no conflict.
    """
    mismatches: List[str] = []

    if (
        expected.get("draft_id") is not None
        and current.get("draft_id") is not None
        and str(expected.get("draft_id")) != str(current.get("draft_id"))
    ):
        mismatches.append(
            f"Draft ID mismatch: expected {expected.get('draft_id')}, got {current.get('draft_id')}"
        )

    if (
        expected.get("body_hash")
        and current.get("body_hash")
        and expected.get("body_hash") != current.get("body_hash")
    ):
        mismatches.append("Remote draft body has changed since export")

    if (
        expected.get("title") is not None
        and current.get("title") is not None
        and expected.get("title") != current.get("title")
    ):
        mismatches.append(
            f"Remote title changed: expected '{expected.get('title')}', got '{current.get('title')}'"
        )

    if (
        expected.get("subtitle") is not None
        and current.get("subtitle") is not None
        and expected.get("subtitle") != current.get("subtitle")
    ):
        mismatches.append(
            f"Remote subtitle changed: expected '{expected.get('subtitle')}', got '{current.get('subtitle')}'"
        )

    if (
        expected.get("audience")
        and current.get("audience")
        and expected.get("audience") != current.get("audience")
    ):
        mismatches.append(
            f"Remote audience changed: expected '{expected.get('audience')}', got '{current.get('audience')}'"
        )

    if (
        expected.get("write_comment_permissions")
        and current.get("write_comment_permissions")
        and expected.get("write_comment_permissions")
        != current.get("write_comment_permissions")
    ):
        mismatches.append(
            f"Remote write_comment_permissions changed: expected '{expected.get('write_comment_permissions')}', got '{current.get('write_comment_permissions')}'"
        )

    if expected.get("draft_section_id") != current.get("draft_section_id"):
        mismatches.append(
            f"Remote section changed: expected {expected.get('draft_section_id')}, got {current.get('draft_section_id')}"
        )

    if (
        expected.get("slug") is not None
        and current.get("slug") is not None
        and expected.get("slug") != current.get("slug")
    ):
        mismatches.append(
            f"Remote slug changed: expected '{expected.get('slug')}', got '{current.get('slug')}'"
        )

    if (
        expected.get("updated_at")
        and current.get("updated_at")
        and expected.get("updated_at") != current.get("updated_at")
    ):
        mismatches.append(
            f"Remote update timestamp changed: expected '{expected.get('updated_at')}', got '{current.get('updated_at')}'"
        )

    if (
        expected.get("revision")
        and current.get("revision")
        and expected.get("revision") != current.get("revision")
        and not mismatches
    ):
        mismatches.append(
            f"Remote revision fingerprint mismatch: expected '{expected.get('revision')}', got '{current.get('revision')}'"
        )

    return mismatches
