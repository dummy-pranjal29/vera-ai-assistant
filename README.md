# Vera

An AI assistant that talks to merchants on WhatsApp.

Built for the magicpin AI Challenge 2026.

## What it does

Vera helps merchants grow their business by sending personalized messages about:
- Industry research and trends
- Performance insights
- Customer engagement opportunities
- Profile improvements

Every message combines four types of context: what we know about the industry, what we know about the merchant, what just happened, and (sometimes) what we know about their customers.

## Running it

Install dependencies:
```bash
py -m pip install -r requirements.txt
```

Add your API key to `.env`:
```
GROQ_API_KEY=gsk_...
```

Start the server:
```bash
py bot.py
```

Generate a test message:
```bash
py generate_submission.py
```

## How it works

The bot exposes five HTTP endpoints. A judge sends context updates, asks what messages to send, and simulates merchant replies.

**POST /v1/context** — Store or update context (category, merchant, customer, trigger)

**POST /v1/tick** — Given available triggers, decide what to send

**POST /v1/reply** — Handle a merchant's response

**GET /v1/healthz** — Health check

**GET /v1/metadata** — Bot info

## What makes a good message

The judge scores on five things:

**Specificity** — Does it cite real numbers, dates, or sources?

**Category fit** — Does it sound right for this type of business?

**Merchant fit** — Is it personalized to this specific merchant?

**Trigger relevance** — Does it explain why now?

**Engagement** — Would a real merchant want to reply?

## Example

Dr. Meera runs a dental clinic in Delhi. Her click-through rate is 2.1%, below the peer median of 3.0%. A research digest just dropped with a study on fluoride recall intervals.

Vera composes:

> Dr. Meera, JIDA's Oct issue landed. One item relevant to your high-risk adult patients — 2,100-patient trial showed 3-month fluoride recall cuts caries recurrence 38% better than 6-month. Worth a look (2-min abstract). Want me to pull it + draft a patient-ed WhatsApp you can share? — JIDA Oct 2026 p.14

Why it works:
- Specific: "2,100-patient", "38% better", "JIDA Oct 2026 p.14"
- Category fit: Clinical vocabulary, peer tone, source citation
- Merchant fit: "your high-risk adult patients" comes from her customer data
- Trigger relevance: Explicitly references the digest
- Engagement: Curiosity + reciprocity + low-friction ask

## Files

**bot.py** — FastAPI server

**composer.py** — Message composition engine

**conversation_handlers.py** — Multi-turn conversation logic

**models.py** — Data structures

**generate_submission.py** — Test script

**dataset/** — Sample contexts

## Design choices

We use Groq API (llama-3.3-70b-versatile) for composition. Temperature is set to 0 for deterministic output.

Auto-reply detection looks for repeated messages and common patterns like "thank you for contacting" or "automated response".

Intent detection classifies merchant responses as positive, negative, or neutral and routes accordingly.

Conversation state tracks history per merchant. We end conversations after three merchant turns or two auto-replies.

Context storage is in-memory with version management. Higher versions replace older ones.

## What's missing

This submission has 22 test cases covering all business categories (dentists, salons, restaurants, gyms, pharmacies).

The dataset has 5 categories, 51 merchants, 200 customers, and 78 triggers.

Multi-turn conversation handling is implemented with auto-reply detection and intent classification.

The prompt could be tuned further with more examples per trigger type.

## Notes

The challenge brief says production Vera struggles with auto-reply detection, intent handoff, and generic copy. We tried to address all three.

For auto-replies: pattern matching plus repetition detection.

For intent handoff: when a merchant says "yes" or "let's do it", we switch to action mode immediately instead of asking more questions.

For generic copy: we anchor every message on a verifiable fact from the context and use service+price format instead of percentage discounts.
