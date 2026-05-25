"""Slack integration tests — fully mocked."""
from unittest.mock import MagicMock, patch

from metabelly.core.models import Category, Language, Priority, TriageResult
from metabelly.integrations.slack import (
    BriefingStats,
    SlackNotifier,
    TicketNotification,
    _route_channel,
    _CHANNEL_MAP,
)


def _result(category: Category, priority: Priority, language: Language = Language.HR) -> TriageResult:
    return TriageResult(
        category=category,
        priority=priority,
        language=language,
        summary="Test summary",
        requires_human=priority in (Priority.P1_URGENT, Priority.P2_BUSINESS),
        suggested_action="Test action",
        auto_reply=None,
    )


# ── Channel routing ───────────────────────────────────────────────────────────

class TestRouteChannel:
    def test_spam_returns_none(self) -> None:
        assert _route_channel(_result(Category.SPAM, Priority.P5_SPAM)) is None

    def test_medical_goes_to_medical(self) -> None:
        assert _route_channel(_result(Category.MEDICAL, Priority.P1_URGENT)) == _CHANNEL_MAP["medical"]

    def test_p1_non_medical_goes_to_urgent(self) -> None:
        assert _route_channel(_result(Category.ORDER, Priority.P1_URGENT)) == _CHANNEL_MAP["urgent"]

    def test_business_goes_to_business(self) -> None:
        assert _route_channel(_result(Category.BUSINESS, Priority.P2_BUSINESS)) == _CHANNEL_MAP["business"]

    def test_order_goes_to_orders(self) -> None:
        assert _route_channel(_result(Category.ORDER, Priority.P3_SUPPORT)) == _CHANNEL_MAP["orders"]

    def test_faq_goes_to_faq(self) -> None:
        assert _route_channel(_result(Category.FAQ, Priority.P4_FAQ)) == _CHANNEL_MAP["faq"]


# ── SlackNotifier ─────────────────────────────────────────────────────────────

@patch("metabelly.integrations.slack.settings")
@patch("metabelly.integrations.slack.WebClient")
class TestSlackNotifier:
    def test_post_ticket_calls_slack(self, mock_client: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.slack_bot_token = "xoxb-test"
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        notifier = SlackNotifier()
        result = _result(Category.FAQ, Priority.P4_FAQ)
        notification = TicketNotification(gmail_id="abc", sender_email="test@x.com", result=result)

        notifier.post_ticket(notification)
        mock_instance.chat_postMessage.assert_called_once()

    def test_spam_not_posted(self, mock_client: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.slack_bot_token = "xoxb-test"
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        notifier = SlackNotifier()
        result = _result(Category.SPAM, Priority.P5_SPAM)
        notification = TicketNotification(gmail_id="abc", sender_email="test@x.com", result=result)

        notifier.post_ticket(notification)
        mock_instance.chat_postMessage.assert_not_called()

    def test_post_heartbeat(self, mock_client: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.slack_bot_token = "xoxb-test"
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        SlackNotifier().post_heartbeat(42)
        mock_instance.chat_postMessage.assert_called_once()

    def test_slack_error_returns_false(self, mock_client: MagicMock, mock_settings: MagicMock) -> None:
        from slack_sdk.errors import SlackApiError
        mock_settings.slack_bot_token = "xoxb-test"
        mock_instance = MagicMock()
        mock_instance.chat_postMessage.side_effect = SlackApiError("error", {"error": "not_in_channel"})
        mock_client.return_value = mock_instance

        result = SlackNotifier().post_heartbeat(1)
        assert result is False
