"""Calendly integration tests — fully mocked."""
from unittest.mock import MagicMock, patch

from metabelly.core.models import Category, Language, Priority, TriageResult
from metabelly.integrations.calendly import (
    CalendlyClient,
    MeetingType,
    _qualify,
    _booking_message,
)


def _result(category: Category, language: Language = Language.HR) -> TriageResult:
    return TriageResult(
        category=category,
        priority=Priority.P2_BUSINESS,
        language=language,
        summary="Test",
        requires_human=True,
        suggested_action="Test action",
        auto_reply="Test reply",
    )


# ── Qualification logic ───────────────────────────────────────────────────────

class TestQualify:
    def test_business_gets_founder_call(self) -> None:
        assert _qualify(_result(Category.BUSINESS)) == MeetingType.FOUNDER_30

    def test_medical_gets_nutritionist(self) -> None:
        assert _qualify(_result(Category.MEDICAL)) == MeetingType.NUTRITIONIST_20

    def test_order_gets_support(self) -> None:
        assert _qualify(_result(Category.ORDER)) == MeetingType.SUPPORT_15

    def test_faq_gets_no_call(self) -> None:
        assert _qualify(_result(Category.FAQ)) is None

    def test_spam_gets_no_call(self) -> None:
        assert _qualify(_result(Category.SPAM)) is None


# ── Booking message language ──────────────────────────────────────────────────

class TestBookingMessage:
    def test_medical_hr(self) -> None:
        msg = _booking_message(MeetingType.NUTRITIONIST_20, _result(Category.MEDICAL, Language.HR))
        assert "liječnika" in msg

    def test_medical_en(self) -> None:
        msg = _booking_message(MeetingType.NUTRITIONIST_20, _result(Category.MEDICAL, Language.EN))
        assert "doctor" in msg

    def test_business_hr(self) -> None:
        msg = _booking_message(MeetingType.FOUNDER_30, _result(Category.BUSINESS, Language.HR))
        assert "timom" in msg

    def test_business_en(self) -> None:
        msg = _booking_message(MeetingType.FOUNDER_30, _result(Category.BUSINESS, Language.EN))
        assert "team" in msg


# ── CalendlyClient ────────────────────────────────────────────────────────────

@patch("metabelly.integrations.calendly.settings")
@patch("metabelly.integrations.calendly.httpx.Client")
class TestCalendlyClient:
    def test_returns_booking_link_for_business(
        self, mock_httpx: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.calendly_api_key = "test-key"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "collection": [{"slug": "founder-30min", "scheduling_url": "https://calendly.com/test"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.return_value.__enter__.return_value.get.return_value = mock_resp

        result = _result(Category.BUSINESS, Language.EN)
        link = CalendlyClient().get_booking_link(result)

        assert link is not None
        assert link.url == "https://calendly.com/test"
        assert link.meeting_type == MeetingType.FOUNDER_30

    def test_returns_none_for_faq(
        self, mock_httpx: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.calendly_api_key = "test-key"
        result = _result(Category.FAQ)
        link = CalendlyClient().get_booking_link(result)
        assert link is None
        mock_httpx.assert_not_called()

    def test_api_error_returns_none(
        self, mock_httpx: MagicMock, mock_settings: MagicMock
    ) -> None:
        import httpx
        mock_settings.calendly_api_key = "test-key"
        mock_httpx.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("timeout")

        result = _result(Category.BUSINESS)
        link = CalendlyClient().get_booking_link(result)
        assert link is None
