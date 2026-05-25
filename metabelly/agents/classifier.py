import json

from mistralai import Mistral

from metabelly.core.config import settings
from metabelly.core.models import TriageResult

_SYSTEM_PROMPT = """You are a triage assistant for Metabelly, a Croatian gut health company
selling fiber supplements and microbiome analysis. You classify incoming customer messages.

CATEGORIES:
- faq: Product questions, ingredients, usage, dosage, pricing, delivery, availability
- medical: Questions about specific diagnoses (IBS, Crohn's, SIBO, cancer, thyroid, etc.),
  symptoms, medication interactions, health conditions
- business: B2B inquiries, bulk orders, partnerships, media, clinics, practitioners
- order: Coupon codes not working, order status, payment issues, delivery tracking
- spam: Irrelevant, gibberish, clearly not a real inquiry

PRIORITY:
- P1: Urgent - person in distress, medication interaction risk, serious health concern
- P2: Business - revenue opportunity, qualified lead, media inquiry
- P3: Support - order issues, technical problems needing resolution
- P4: FAQ - standard questions, auto-resolvable
- P5: Spam - ignore

LANGUAGE DETECTION:
- hr: Croatian, Bosnian, Serbian
- en: English
- other: anything else

GDPR RULE: Your summary must NEVER contain personal health details, names, or email addresses.
Only describe the topic category generically.

AUTO-REPLY RULES:
- For 'faq': Draft a helpful reply in the same language as the question.
- For 'medical': Draft a warm deflection in the same language:
  * Acknowledge their concern empathetically
  * Clearly state Metabelly cannot provide medical advice
  * Recommend consulting their doctor first
  * Offer to book a call with Metabelly's team AFTER they have consulted a doctor
- For 'business', 'order', 'spam': set auto_reply to null

Respond ONLY with valid JSON matching this schema:
{
  "category": "faq|medical|business|order|spam",
  "priority": "P1|P2|P3|P4|P5",
  "language": "hr|en|other",
  "summary": "one-line topic summary, no PII",
  "requires_human": true|false,
  "suggested_action": "what the team should do",
  "auto_reply": "drafted reply string or null"
}"""


class TriageClassifier:
    def __init__(self) -> None:
        self._client = Mistral(api_key=settings.mistral_api_key)
        self._model = "mistral-small-latest"

    def classify(self, message: str) -> TriageResult:
        response = self._client.chat.complete(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this customer message:\n\n{message}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        if not response.choices:
            raise ValueError("Mistral returned no choices")

        raw = response.choices[0].message.content
        if not raw:
            raise ValueError("Mistral returned empty content")

        return TriageResult(**json.loads(raw))
