"""
Dispatcher — receives a classified TriageResult and orchestrates the response:
  1. Send auto-reply (FAQ / medical deflection) via Gmail
  2. Append Calendly booking link if qualified
  3. Post to Slack channel
  4. Log ticket to DB
"""
import logging

from metabelly.core.audit import AuditEvent, Severity, log
from metabelly.core.models import Category, Priority, TriageResult

logger = logging.getLogger(__name__)

INSERT_TICKET = """
INSERT INTO tickets
    (queue_item_id, category, priority, language, summary,
     requires_human, suggested_action, auto_reply_sent)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
"""


class Dispatcher:
    def __init__(self) -> None:
        from metabelly.integrations.gmail import GmailClient
        from metabelly.integrations.slack import SlackNotifier, TicketNotification
        from metabelly.integrations.calendly import CalendlyClient

        self._gmail = GmailClient()
        self._slack = SlackNotifier()
        self._calendly = CalendlyClient()
        self._TicketNotification = TicketNotification

    async def handle(
        self,
        gmail_id: str,
        sender_email: str,
        subject: str,
        thread_id: str,
        result: TriageResult,
        queue_item_id: str,
    ) -> None:
        auto_reply_sent = False

        # 1 — build reply body
        reply_body = _compose_reply(result, self._calendly)

        # 2 — send auto-reply for FAQ and medical (not for business/order/spam)
        if reply_body and result.category in (Category.FAQ, Category.MEDICAL):
            sent = self._gmail.send_reply(
                to=sender_email,
                subject=subject,
                body=reply_body,
                thread_id=thread_id,
            )
            auto_reply_sent = sent
            if sent:
                log(AuditEvent.EMAIL_CLASSIFIED, detail=f"auto-reply sent to {sender_email[:4]}***")

        # 3 — notify Slack
        self._slack.post_ticket(
            self._TicketNotification(
                gmail_id=gmail_id,
                sender_email=sender_email,
                result=result,
            )
        )

        # 4 — alert immediately for P1
        if result.priority == Priority.P1_URGENT:
            self._slack.post_alert(
                f"P1 urgent email received — {result.summary}. Immediate review needed."
            )

        # 5 — log ticket to DB
        from metabelly.core.db_pool import pool
        async with pool.acquire() as conn:
            await conn.execute(
                INSERT_TICKET,
                queue_item_id,
                result.category.value,
                result.priority.value,
                result.language.value,
                result.summary,
                result.requires_human,
                result.suggested_action,
                auto_reply_sent,
            )

        logger.info(
            "Dispatched %s %s — auto_reply=%s human=%s",
            result.priority.value,
            result.category.value,
            auto_reply_sent,
            result.requires_human,
        )


def _compose_reply(result: TriageResult, calendly: object) -> str | None:
    if not result.auto_reply:
        return None

    from metabelly.integrations.calendly import CalendlyClient
    booking = CalendlyClient.get_booking_link(calendly, result)  # type: ignore[arg-type]

    if booking:
        return f"{result.auto_reply}\n\n{booking.message}\n{booking.url}"

    return result.auto_reply
