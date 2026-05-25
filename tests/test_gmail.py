"""Gmail integration tests — fully mocked, no API credentials needed."""
import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from metabelly.integrations.gmail import (
    GmailClient,
    ParsedEmail,
    _extract_email,
    _extract_body,
)


# ── Email parsing ─────────────────────────────────────────────────────────────

class TestExtractEmail:
    def test_angle_bracket_format(self) -> None:
        assert _extract_email("Marija Horvat <marija@example.com>") == "marija@example.com"

    def test_plain_email(self) -> None:
        assert _extract_email("marija@example.com") == "marija@example.com"

    def test_lowercases(self) -> None:
        assert _extract_email("MARIJA@EXAMPLE.COM") == "marija@example.com"

    def test_strips_whitespace(self) -> None:
        assert _extract_email("  marija@example.com  ") == "marija@example.com"


class TestExtractBody:
    def _encode(self, text: str) -> str:
        return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")

    def test_plain_text_payload(self) -> None:
        payload = {
            "mimeType": "text/plain",
            "body": {"data": self._encode("Koji je sastav fiber vlakana?")},
        }
        assert _extract_body(payload) == "Koji je sastav fiber vlakana?"

    def test_multipart_extracts_plain(self) -> None:
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": self._encode("Imam IBS problema")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": self._encode("<p>Imam IBS problema</p>")},
                },
            ],
        }
        assert _extract_body(payload) == "Imam IBS problema"

    def test_unknown_mimetype_returns_empty(self) -> None:
        payload = {"mimeType": "application/pdf", "body": {}}
        assert _extract_body(payload) == ""


# ── GmailClient ───────────────────────────────────────────────────────────────

def _make_gmail_message(sender: str, subject: str, body: str) -> dict:
    encoded_body = base64.urlsafe_b64encode(body.encode()).decode()
    return {
        "id": "msg123",
        "threadId": "thread456",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
            ],
            "body": {"data": encoded_body},
        },
    }


@patch("metabelly.integrations.gmail.settings")
@patch("metabelly.integrations.gmail.build")
@patch("metabelly.integrations.gmail.Credentials")
class TestGmailClient:
    def test_fetch_email_returns_parsed(
        self,
        mock_creds: MagicMock,
        mock_build: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        mock_settings.google_refresh_token = "token"
        mock_settings.google_client_id = "id"
        mock_settings.google_client_secret = "secret"

        fake_msg = _make_gmail_message(
            "Marija <marija@example.com>", "Pitanje o fiberu", "Koji je sastav?"
        )
        mock_service = MagicMock()
        mock_service.users().messages().get().execute.return_value = fake_msg
        mock_build.return_value = mock_service

        result = GmailClient().fetch_email("msg123")

        assert result is not None
        assert isinstance(result, ParsedEmail)
        assert result.sender_email == "marija@example.com"
        assert result.subject == "Pitanje o fiberu"
        assert "Koji je sastav?" in result.body

    def test_fetch_email_returns_none_on_error(
        self,
        mock_creds: MagicMock,
        mock_build: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        from googleapiclient.errors import HttpError
        from unittest.mock import Mock

        mock_settings.google_refresh_token = "token"
        mock_settings.google_client_id = "id"
        mock_settings.google_client_secret = "secret"

        mock_service = MagicMock()
        resp = Mock()
        resp.status = 404
        mock_service.users().messages().get().execute.side_effect = HttpError(resp, b"Not found")
        mock_build.return_value = mock_service

        result = GmailClient().fetch_email("bad_id")
        assert result is None

    def test_full_text_combines_subject_and_body(
        self,
        mock_creds: MagicMock,
        mock_build: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        mock_settings.google_refresh_token = "token"
        mock_settings.google_client_id = "id"
        mock_settings.google_client_secret = "secret"

        fake_msg = _make_gmail_message(
            "test@example.com", "IBS pitanje", "Imam jak IBS"
        )
        mock_service = MagicMock()
        mock_service.users().messages().get().execute.return_value = fake_msg
        mock_build.return_value = mock_service

        result = GmailClient().fetch_email("msg123")
        assert result is not None
        assert "IBS pitanje" in result.full_text
        assert "Imam jak IBS" in result.full_text
