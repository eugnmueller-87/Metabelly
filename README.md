# Metabelly Triage System

![Python](https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?logo=postgresql&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-notifications-4A154B?logo=slack&logoColor=white)
![License](https://img.shields.io/badge/license-private-lightgrey)

---

## The problem

[Metabelly](https://metabelly.com/en/) is a Croatian gut health company selling fiber supplements and microbiome analysis. As the brand grew, so did the volume of customer messages — across email, chat, and social. Many are simple product questions. But a significant share involve people describing real medical conditions: IBS, Crohn's disease, cancer treatment, medication interactions.

Handling these manually is slow, inconsistent, and risky. A FAQ question delayed by a day is annoying. A medical question handled carelessly is a liability.

The team needed a way to instantly understand what kind of message came in, what to do with it, and whether a human needs to act — without reading every message from scratch.

---

## What this system does

Every incoming customer message is automatically processed end-to-end:

1. **Email arrives** in the Metabelly inbox
2. **The system picks it up** via Gmail push notifications
3. **An AI agent classifies it** — category, priority, language, and whether it needs a human
4. **A reply is drafted** where appropriate (FAQ answers, medical deflections)
5. **The team is notified** in the right Slack channel with a structured summary
6. **Everything is logged** with an append-only audit trail

The human team sees only what requires their attention, in the right place, with context already prepared.

---

## The agents

The system is built around a small team of specialized agents, each with a defined role:

### Luka — The Classifier
Reads every incoming message and makes the first call: what kind of message is this, how urgent is it, what language is it in, does a human need to see it? Produces a structured triage result that drives everything downstream. Never touches raw PII in its output — summaries are always generic.

### Bruno — The Notifier
Takes Luka's output and routes it to the right place. Urgent medical concerns go to one channel. Business leads go to another. Auto-resolved FAQs get a quiet FYI. Sends daily briefings with resolved/escalated counts, response times, and top topics.

### Sven — The Queue Worker
Manages the processing pipeline. Picks up emails one at a time, runs them through Luka, hands results to Bruno. Handles retries on failure, resets stuck jobs, and ensures no message is processed twice.

### Maja — The Audit Logger
Silently records every security-relevant event: incoming webhooks, signature checks, rate limit hits, injection attempts, processing outcomes. Append-only — nothing is ever updated or deleted. The paper trail.

---

## Message categories and priorities

| Category | Description |
|---|---|
| `faq` | Product questions, ingredients, dosage, delivery, pricing |
| `medical` | Specific diagnoses, symptoms, medication interactions, health conditions |
| `business` | B2B, bulk orders, partnerships, clinics, media |
| `order` | Coupon issues, payment problems, delivery tracking |
| `spam` | Irrelevant or not a real inquiry |

| Priority | Meaning |
|---|---|
| P1 | Person in distress, medication interaction risk, serious health concern |
| P2 | Revenue opportunity, qualified lead, media inquiry |
| P3 | Order issue or technical problem needing resolution |
| P4 | Standard FAQ — auto-resolvable |
| P5 | Spam — silently dropped |

---

## Auto-reply behavior

- **FAQ** — A helpful reply is drafted in the customer's own language
- **Medical** — A warm, empathetic deflection is drafted: acknowledges the concern, explains Metabelly cannot provide medical advice, recommends consulting a doctor first, and offers a follow-up call after they have done so
- **Business / Order / Spam** — No auto-reply; routed to the team

---

## Architecture

```
metabelly/
├── agents/
│   └── classifier.py         # Luka — triage classification agent
├── api/
│   ├── app.py                # FastAPI application
│   ├── security.py           # Webhook signature verification, rate limiting
│   └── webhooks.py           # Gmail push notification endpoint
├── core/
│   ├── models.py             # Pydantic data models
│   ├── config.py             # Settings via environment variables
│   ├── queue.py              # Queue table definitions
│   ├── queue_service.py      # Sven — enqueue with deduplication
│   ├── worker.py             # Sven — processing loop with retry logic
│   ├── audit.py              # Maja — append-only audit log
│   ├── encryption.py         # AES encryption for stored email content
│   ├── database.py           # SQL query constants
│   └── db_pool.py            # Async connection pool
└── integrations/
    ├── gmail.py              # Gmail API — fetch and reply
    └── slack.py              # Bruno — Slack channel routing and briefings
```

---

## GDPR

Message summaries never contain personal health details, names, or email addresses — only generic topic descriptions. Email content is encrypted at rest. The audit log records events, not message content.
