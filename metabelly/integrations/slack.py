"""
Slack integration — posts triage results to the right channel,
sends daily briefings, and handles internal bot queries.

Channels:
  #urgent    → P1
  #business  → P2
  #orders    → P3 order
  #medical   → medical (any priority)
  #faq       → P4 auto-handled (FYI only)
  #daily-briefing → scheduled summary
  #internal-bot   → team queries answered by agent
"""

import logging
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from metabelly.core.config import settings
from metabelly.core.models import Category, Priority, TriageResult

logger = logging.getLogger(__name__)

# Channel routing table — change names here to match your Slack workspace
_CHANNEL_MAP: dict[str, str] = {
    "urgent": "triage-urgent",
    "business": "triage-business",
    "medical": "triage-medical",
    "orders": "triage-orders",
    "faq": "triage-faq",
    "briefing": "daily-briefing",
    "internal": "internal-bot",
}

_PRIORITY_EMOJI: dict[Priority, str] = {
    Priority.P1_URGENT: ":red_circle:",
    Priority.P2_BUSINESS: ":large_yellow_circle:",
    Priority.P3_SUPPORT: ":large_blue_circle:",
    Priority.P4_FAQ: ":white_circle:",
    Priority.P5_SPAM: ":black_circle:",
}


@dataclass
class TicketNotification:
    gmail_id: str
    sender_email: str
    result: TriageResult


class SlackNotifier:
    def __init__(self) -> None:
        self._client = WebClient(token=settings.slack_bot_token)

    def post_ticket(self, notification: TicketNotification) -> bool:
        channel = _route_channel(notification.result)
        if not channel:
            return True  # spam — silently drop

        blocks = _build_ticket_blocks(notification)

        return self._post(channel, blocks)

    def post_daily_briefing(self, stats: "BriefingStats") -> bool:
        blocks = _build_briefing_blocks(stats)
        return self._post(_CHANNEL_MAP["briefing"], blocks)

    def post_heartbeat(self, processed_last_30min: int) -> bool:
        return self._post(
            _CHANNEL_MAP["briefing"],
            text=f":green_heart: System alive. Processed {processed_last_30min} emails in last 30 min.",
        )

    def post_alert(self, message: str) -> bool:
        return self._post(_CHANNEL_MAP["urgent"], text=f":warning: *ALERT:* {message}")

    def _post(
        self,
        channel: str,
        blocks: list | None = None,
        text: str = "",
    ) -> bool:
        try:
            self._client.chat_postMessage(
                channel=channel,
                blocks=blocks or [],
                text=text,
            )
            return True
        except SlackApiError as e:
            logger.error("Slack post failed to #%s: %s", channel, e.response["error"])
            return False


@dataclass
class BriefingStats:
    date_range: str
    total_received: int
    auto_resolved: int
    escalated: int
    medical_deflections: int
    calls_booked: int
    avg_response_seconds: int
    uptime_pct: float
    top_topics: list[tuple[str, int]]  # [(topic, count), ...]


def _route_channel(result: TriageResult) -> str | None:
    if result.priority == Priority.P5_SPAM:
        return None
    if result.category == Category.MEDICAL:
        return _CHANNEL_MAP["medical"]
    if result.priority == Priority.P1_URGENT:
        return _CHANNEL_MAP["urgent"]
    if result.category == Category.BUSINESS:
        return _CHANNEL_MAP["business"]
    if result.category == Category.ORDER:
        return _CHANNEL_MAP["orders"]
    return _CHANNEL_MAP["faq"]


def _build_ticket_blocks(n: TicketNotification) -> list:
    emoji = _PRIORITY_EMOJI.get(n.result.priority, ":white_circle:")
    auto = (
        ":white_check_mark: Auto-reply sent"
        if n.result.auto_reply
        else ":bust_in_silhouette: Needs human"
    )

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{emoji} *{n.result.priority.value} — {n.result.category.value.upper()}*\n"
                    f"*Summary:* {n.result.summary}\n"
                    f"*Language:* `{n.result.language.value}` | {auto}"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Action:* {n.result.suggested_action}",
            },
        },
        {"type": "divider"},
    ]


def _build_briefing_blocks(s: BriefingStats) -> list:
    auto_pct = round(s.auto_resolved / max(s.total_received, 1) * 100)
    topics = "\n".join(f"  {i + 1}. {t} ({c})" for i, (t, c) in enumerate(s.top_topics[:5]))

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Weekly Report {s.date_range}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Emails received:* {s.total_received}\n"
                    f"*Auto-resolved:* {s.auto_resolved} ({auto_pct}%)\n"
                    f"*Escalated to human:* {s.escalated}\n"
                    f"*Medical deflections:* {s.medical_deflections}\n"
                    f"*Calls booked:* {s.calls_booked}\n\n"
                    f"*Avg response time:* {s.avg_response_seconds}s\n"
                    f"*Uptime:* {s.uptime_pct:.1f}%\n\n"
                    f"*Top topics:*\n{topics}"
                ),
            },
        },
    ]
