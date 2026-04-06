"""Dataclasses for Substack API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class Byline:
    id: int
    name: str
    handle: str | None = None
    photo_url: str | None = None
    bio: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> Byline:
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            handle=data.get("handle"),
            photo_url=data.get("photo_url"),
            bio=data.get("bio"),
        )


@dataclass
class ScheduledRelease:
    trigger_at: datetime
    post_audience: str
    email_audience: str

    @classmethod
    def from_api(cls, data: dict) -> ScheduledRelease:
        return cls(
            trigger_at=_parse_dt(data["trigger_at"]),
            post_audience=data.get("post_audience", ""),
            email_audience=data.get("email_audience", ""),
        )


@dataclass
class PostMetadata:
    """Metadata for a Substack post (draft or published)."""

    id: int
    title: str | None
    subtitle: str | None
    slug: str | None
    type: str
    uuid: str
    audience: str
    write_comment_permissions: str
    is_published: bool
    publication_id: int

    post_date: datetime | None = None
    draft_created_at: datetime | None = None
    draft_updated_at: datetime | None = None
    email_sent_at: datetime | None = None
    updated_at: datetime | None = None

    section_id: int | None = None
    subscriber_set_id: int | None = None

    cover_image: str | None = None
    search_engine_title: str | None = None
    search_engine_description: str | None = None

    should_send_email: bool = True
    should_send_free_preview: bool = False
    hide_from_feed: bool = False
    teaser_post_eligible: bool = True
    meter_type: str = "none"

    free_unlock_required: bool = False
    exempt_from_archive_paywall: bool = False

    bylines: list[Byline] = field(default_factory=list)
    scheduled_releases: list[ScheduledRelease] = field(default_factory=list)

    # Raw response for any fields not mapped above
    _raw: dict = field(default_factory=dict, repr=False)

    @property
    def needs_comment_fix(self) -> bool:
        """True if post is free but comments are still restricted."""
        return (
            self.audience == "everyone" and self.write_comment_permissions != "everyone"
        )

    @classmethod
    def from_api(cls, data: dict) -> PostMetadata:
        bylines = [
            Byline.from_api(b)
            for b in data.get("publishedBylines") or data.get("draftBylines") or []
        ]
        schedules = [
            ScheduledRelease.from_api(s) for s in data.get("postSchedules") or []
        ]

        return cls(
            id=data["id"],
            title=data.get("title") or data.get("draft_title"),
            subtitle=data.get("subtitle") or data.get("draft_subtitle"),
            slug=data.get("slug"),
            type=data.get("type", "newsletter"),
            uuid=data.get("uuid", ""),
            audience=data.get("audience", "everyone"),
            write_comment_permissions=data.get("write_comment_permissions", "everyone"),
            is_published=data.get("is_published", False),
            publication_id=data.get("publication_id", 0),
            post_date=_parse_dt(data.get("post_date")),
            draft_created_at=_parse_dt(data.get("draft_created_at")),
            draft_updated_at=_parse_dt(data.get("draft_updated_at")),
            email_sent_at=_parse_dt(data.get("email_sent_at")),
            updated_at=_parse_dt(data.get("updated_at")),
            section_id=data.get("section_id"),
            subscriber_set_id=data.get("subscriber_set_id"),
            cover_image=data.get("cover_image"),
            search_engine_title=data.get("search_engine_title"),
            search_engine_description=data.get("search_engine_description"),
            should_send_email=data.get("should_send_email", True),
            should_send_free_preview=data.get("should_send_free_preview", False),
            hide_from_feed=data.get("hide_from_feed", False),
            teaser_post_eligible=data.get("teaser_post_eligible", True),
            meter_type=data.get("meter_type", "none"),
            free_unlock_required=data.get("free_unlock_required", False),
            exempt_from_archive_paywall=data.get("exempt_from_archive_paywall", False),
            bylines=bylines,
            scheduled_releases=schedules,
            _raw=data,
        )

    def print_summary(self) -> None:
        """Print a human-readable summary of the post metadata."""
        print(f"{'=' * 50}")
        print(f"Post: {self.title}")
        print(f"{'=' * 50}")
        print(f"  id:                {self.id}")
        print(f"  slug:              {self.slug}")
        print(f"  type:              {self.type}")
        print(f"  uuid:              {self.uuid}")
        print(f"  audience:          {self.audience}")
        print(f"  comments:          {self.write_comment_permissions}")
        print(f"  published:         {self.is_published}")
        print(f"  post_date:         {self.post_date}")
        print(f"  send_email:        {self.should_send_email}")
        print(f"  meter_type:        {self.meter_type}")
        print(f"  free_unlock:       {self.free_unlock_required}")
        if self.bylines:
            names = ", ".join(b.name for b in self.bylines)
            print(f"  bylines:           {names}")
        if self.scheduled_releases:
            for sr in self.scheduled_releases:
                print(
                    f"  scheduled_release: {sr.trigger_at} -> {sr.post_audience} (email: {sr.email_audience})"
                )
        if self.needs_comment_fix:
            print("  *** NEEDS COMMENT FIX ***")
        print(f"{'=' * 50}")
