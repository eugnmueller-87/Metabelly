"""
Calendly integration — qualifies leads before showing booking links.

Qualification gate:
  - Business/clinic inquiry  → 30-min founder call
  - Medical follow-up        → 20-min nutritionist call
  - General support          → 15-min support call
  - Unqualified              → no link, async response only

Uses Calendly v2 API (OAuth2 personal token).
"""
import logging
from dataclasses import dataclass
from enum import Enum

import httpx

from metabelly.core.config import settings
from metabelly.core.models import Category, TriageResult

logger = logging.getLogger(__name__)

_CALENDLY_API = "https://api.calendly.com"


class MeetingType(str, Enum):
    FOUNDER_30    = "founder-30min"
    NUTRITIONIST_20 = "nutritionist-20min"
    SUPPORT_15    = "support-15min"


@dataclass
class BookingLink:
    meeting_type: MeetingType
    url: str
    message: str   # message to include in the auto-reply


class CalendlyClient:
    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.calendly_api_key}",
            "Content-Type": "application/json",
        }

    def get_booking_link(self, result: TriageResult) -> BookingLink | None:
        meeting_type = _qualify(result)
        if not meeting_type:
            return None

        url = self._fetch_event_link(meeting_type)
        if not url:
            return None

        return BookingLink(
            meeting_type=meeting_type,
            url=url,
            message=_booking_message(meeting_type, result),
        )

    def _fetch_event_link(self, meeting_type: MeetingType) -> str | None:
        try:
            with httpx.Client() as client:
                resp = client.get(
                    f"{_CALENDLY_API}/event_types",
                    headers=self._headers,
                    params={"active": "true"},
                    timeout=10,
                )
                resp.raise_for_status()
                for event in resp.json().get("collection", []):
                    if meeting_type.value in event.get("slug", ""):
                        return event["scheduling_url"]
        except httpx.HTTPError as e:
            logger.error("Calendly API error: %s", e)
        return None


def _qualify(result: TriageResult) -> MeetingType | None:
    if result.category == Category.SPAM:
        return None
    if result.category == Category.BUSINESS:
        return MeetingType.FOUNDER_30
    if result.category == Category.MEDICAL:
        return MeetingType.NUTRITIONIST_20
    if result.category == Category.ORDER:
        return MeetingType.SUPPORT_15
    return None  # FAQ — no call needed, auto-reply is enough


def _booking_message(meeting_type: MeetingType, result: TriageResult) -> str:
    is_hr = result.language.value == "hr"

    if meeting_type == MeetingType.NUTRITIONIST_20:
        if is_hr:
            return (
                "Nakon što posjetite svog liječnika, slobodno zakažite razgovor "
                "s našim nutricionistom:"
            )
        return "After consulting your doctor, feel free to book a call with our nutritionist:"

    if meeting_type == MeetingType.FOUNDER_30:
        if is_hr:
            return "Zakažite razgovor s našim timom:"
        return "Book a call with our team:"

    if is_hr:
        return "Zakažite poziv s našom podrškom:"
    return "Book a call with our support team:"
