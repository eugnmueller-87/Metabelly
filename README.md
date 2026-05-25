# Metabelly Triage System

![Python](https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-mistral--small-ff7000?logo=mistral&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/license-private-lightgrey)

An AI-powered customer support triage backend for **Metabelly** — a Croatian gut health company selling fiber supplements and microbiome analysis.

The system automatically classifies incoming customer messages, prioritizes them, detects language, and drafts replies — so the human support team only handles what actually needs them.

---

## What it does

**Incoming message → AI classification → structured result**

Every message gets:

| Field | Description |
|---|---|
| `category` | faq / medical / business / order / spam |
| `priority` | P1 (urgent) → P5 (spam) |
| `language` | Croatian/Bosnian/Serbian, English, or other |
| `summary` | One-line topic description (no personal data) |
| `requires_human` | Boolean flag for routing |
| `suggested_action` | What the team should do next |
| `auto_reply` | Drafted reply for FAQ and medical deflections, null otherwise |

### Priority levels

- **P1** — Person in distress, medication interaction risk, serious health concern
- **P2** — Business opportunity, qualified lead, media inquiry
- **P3** — Order issues, payment problems, technical support
- **P4** — Standard FAQ, auto-resolvable questions
- **P5** — Spam

### Auto-reply behavior

- **FAQ** — Drafts a helpful reply in the customer's language
- **Medical** — Drafts a warm, empathetic deflection recommending the customer consult their doctor first
- **Business / Order / Spam** — No auto-reply, routed to the team

---

## Architecture

```
metabelly/
├── agents/
│   └── classifier.py     # Mistral AI triage classifier
├── api/
│   ├── app.py            # FastAPI application
│   ├── security.py       # Request authentication middleware
│   └── webhooks.py       # Webhook endpoints
├── core/
│   ├── models.py         # Pydantic data models
│   ├── config.py         # Settings via environment variables
│   ├── database.py       # Database layer
│   ├── db_pool.py        # Async connection pool
│   ├── queue.py          # Message queue
│   ├── queue_service.py  # Queue service logic
│   ├── worker.py         # Background worker
│   ├── audit.py          # Audit logging
│   └── encryption.py     # Data encryption utilities
└── integrations/
    └── gmail.py          # Gmail integration
```

**Stack:** Python · FastAPI · Mistral AI · PostgreSQL (asyncpg) · Slack SDK · Gmail API

---

## Setup

**Requirements:** Python 3.11+, PostgreSQL

```bash
git clone https://github.com/eugnmueller-87/Metabelly.git
cd Metabelly
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Create a `.env` file:

```env
MISTRAL_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/metabelly
```

Run the API:

```bash
uvicorn metabelly.api.app:app --reload
```

Health check: `GET /health`

---

## Testing the classifier

```bash
python test_classifier.py
```

Runs 12 real-world test cases (Croatian and English) across all categories and prints structured triage output for each.

---

## GDPR

Message summaries never contain personal health details, names, or email addresses — only generic topic descriptions.
