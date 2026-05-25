"""Unit tests for TriageClassifier — mocked so no Mistral API key needed in CI."""

import json
from unittest.mock import MagicMock, patch

import pytest

from metabelly.agents.classifier import TriageClassifier
from metabelly.core.models import Category, Language, Priority, TriageResult


def _make_mock_response(data: dict) -> MagicMock:
    content = MagicMock()
    content.message.content = json.dumps(data)
    response = MagicMock()
    response.choices = [content]
    return response


MEDICAL_PAYLOAD = {
    "category": "medical",
    "priority": "P1",
    "language": "hr",
    "summary": "Customer asks about product safety with serious diagnosis",
    "requires_human": True,
    "suggested_action": "Review and send medical deflection",
    "auto_reply": "Hvala na poruci. Nažalost, ne možemo davati medicinske savjete...",
}

FAQ_PAYLOAD = {
    "category": "faq",
    "priority": "P4",
    "language": "hr",
    "summary": "Customer asks about product ingredients",
    "requires_human": False,
    "suggested_action": "Auto-reply sent",
    "auto_reply": "Naš Fiber sadrži...",
}

ORDER_PAYLOAD = {
    "category": "order",
    "priority": "P3",
    "language": "hr",
    "summary": "Coupon code not working",
    "requires_human": True,
    "suggested_action": "Support team to resolve coupon issue",
    "auto_reply": None,
}


@patch("metabelly.agents.classifier.settings")
@patch("metabelly.agents.classifier.Mistral")
class TestTriageClassifier:
    def test_medical_classification(
        self, mock_mistral: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.mistral_api_key = "test-key"
        mock_mistral.return_value.chat.complete.return_value = _make_mock_response(MEDICAL_PAYLOAD)

        result = TriageClassifier().classify("Imam karcinom dojke, mogu li koristiti fiber?")

        assert result.category == Category.MEDICAL
        assert result.priority == Priority.P1_URGENT
        assert result.language == Language.HR
        assert result.requires_human is True
        assert result.auto_reply is not None

    def test_faq_classification(self, mock_mistral: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.mistral_api_key = "test-key"
        mock_mistral.return_value.chat.complete.return_value = _make_mock_response(FAQ_PAYLOAD)

        result = TriageClassifier().classify("Koji je sastav metabelly fiber?")

        assert result.category == Category.FAQ
        assert result.priority == Priority.P4_FAQ
        assert result.requires_human is False
        assert result.auto_reply is not None

    def test_order_no_auto_reply(self, mock_mistral: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.mistral_api_key = "test-key"
        mock_mistral.return_value.chat.complete.return_value = _make_mock_response(ORDER_PAYLOAD)

        result = TriageClassifier().classify("Kupon welcome10 ne radi")

        assert result.category == Category.ORDER
        assert result.auto_reply is None
        assert result.requires_human is True

    def test_empty_response_raises(self, mock_mistral: MagicMock, mock_settings: MagicMock) -> None:
        mock_settings.mistral_api_key = "test-key"
        empty = MagicMock()
        empty.choices = []
        mock_mistral.return_value.chat.complete.return_value = empty

        with pytest.raises(ValueError, match="no choices"):
            TriageClassifier().classify("test")

    def test_result_is_triage_result(
        self, mock_mistral: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.mistral_api_key = "test-key"
        mock_mistral.return_value.chat.complete.return_value = _make_mock_response(FAQ_PAYLOAD)

        result = TriageClassifier().classify("test message")

        assert isinstance(result, TriageResult)
