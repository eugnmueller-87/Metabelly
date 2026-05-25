# Metabelly Triage System

![n8n](https://img.shields.io/badge/n8n-workflow-EA4B71?logo=n8n&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-classifier-FF6B35?logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-notifications-4A154B?logo=slack&logoColor=white)
![License](https://img.shields.io/badge/license-private-lightgrey)

---

## The problem

[Metabelly](https://metabelly.com/en/) is a Croatian gut health company selling fiber supplements and microbiome analysis. As the brand grew, so did the volume of customer messages — across email, chat, and social. Many are simple product questions. But a significant share involve people describing real medical conditions: IBS, Crohn's disease, cancer treatment, medication interactions.

Handling these manually is slow, inconsistent, and risky. A FAQ question delayed by a day is annoying. A medical question handled carelessly is a liability.

The team needed a way to instantly understand what kind of message came in, what to do with it, and whether a human needs to act — without reading every message from scratch.

---

## What this system does

Every incoming customer email is automatically processed end-to-end:

1. **Email arrives** in the Metabelly support inbox
2. **The system picks it up** via Gmail
3. **Luka classifies it** — category, priority, language, and whether it needs a human
4. **A reply is drafted** where appropriate (FAQ answers, medical deflections with booking link)
5. **Bruno notifies the team** in the right Slack channel with a structured summary
6. **A daily briefing** is posted every weekday morning with the inbox status

The human team sees only what requires their attention, in the right place, with context already prepared.

---

## The agents

### Luka — The Classifier
Reads every incoming message and makes the first call: what kind of message is this, how urgent is it, what language is it in, does a human need to see it? Produces a structured triage result that drives everything downstream.

### Bruno — The Notifier
Takes Luka's output and routes it to the right Slack channel. Urgent medical concerns, business leads, order issues, and FAQs each go to their own channel. Sends a daily briefing every weekday morning.

### Maja — The Composer
Composes auto-replies in the customer's own language. FAQ questions get a helpful answer. Medical questions get a warm empathetic deflection plus a nutritionist booking link. P1 cases are always escalated to a human — no auto-reply.

---

## Message categories

| Category | Description |
|---|---|
| `FAQ` | Product questions, ingredients, dosage, delivery, pricing |
| `MEDICAL` | Diagnoses, symptoms, medication interactions, health conditions |
| `BUSINESS` | B2B, bulk orders, partnerships, clinics, media |
| `ORDER` | Coupon issues, payment problems, delivery tracking |

| Priority | Meaning |
|---|---|
| P1 | Person in distress or medication interaction risk — human only |
| P2 | Needs human attention — medical, order, business |
| P3 | Standard FAQ — auto-resolvable |

---

## Auto-reply behavior

- **FAQ (P3)** — A helpful reply in the customer's language, sent automatically
- **Medical** — A warm deflection: acknowledges the concern, explains medical advice requires a professional, offers nutritionist booking link
- **P1 (any category)** — No auto-reply, immediately escalated to the team

---

## Workflows (n8n)

```
n8n-workflows/
├── 01-email-triage.json      # Gmail trigger → Luka classifies → routes by category
├── 02-slack-notify.json      # Bruno — sends to right Slack channel, P1 hits #triage-urgent
├── 03-auto-reply.json        # Maja — composes and sends reply via Gmail
└── 04-daily-briefing.json    # 8am weekdays → inbox count → post to #daily-briefing
```

---

## Slack channels

| Channel | Purpose |
|---|---|
| `#triage-urgent` | P1 alerts — immediate human action required |
| `#triage-medical` | Medical questions awaiting nutritionist response |
| `#triage-orders` | Order and payment issues |
| `#triage-business` | B2B leads and partnership inquiries |
| `#triage-faq` | Auto-resolved FAQ confirmations |
| `#daily-briefing` | Morning inbox summary |

---

## GDPR

Message summaries never contain personal health details, names, or email addresses — only generic topic descriptions. The system processes email content in memory only and does not store raw message bodies.
