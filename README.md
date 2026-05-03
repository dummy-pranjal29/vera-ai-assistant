# Vera AI Assistant

An intelligent WhatsApp messaging system for small business owners.

---

## Overview

Vera helps merchants grow their business by sending personalized, context-aware messages about:
- Industry research and trends
- Performance insights and benchmarks
- Customer engagement opportunities
- Timely business actions

Every message combines four types of context to ensure relevance and personalization.

---

## The 4-Context Framework

Vera's intelligence comes from combining four layers of context:

### 1. Category Context
Industry-specific knowledge for 5 business types:
- **Dentists** - Clinical vocabulary, peer journals (JIDA), recall protocols
- **Salons** - Beauty trends, seasonal demand, service terminology
- **Restaurants** - Food industry insights, footfall patterns, menu strategies
- **Gyms** - Fitness trends, membership patterns, seasonal cycles
- **Pharmacies** - Medical terminology, regulatory knowledge, chronic care programs

Each category has its own voice, vocabulary, peer benchmarks, and research insights.

### 2. Merchant Context
Individual business data:
- Owner name and business name
- Location and category
- Performance metrics (views, CTR, calls)
- Subscription status
- Active offers

### 3. Trigger Context
Events that prompt a message (the "why now?"):
- `research_digest` - New industry study published
- `competitor_opened` - Competitor joined platform nearby
- `perf_dip` - Performance metrics dropped
- `perf_spike` - Performance metrics improved
- `customer_lapsed_soft` - Customer hasn't visited recently
- `recall_due` - Customer due for appointment/refill
- `renewal_due` - Subscription expiring soon
- `festival_upcoming` - Festival season approaching
- `milestone_reached` - Hit view/call milestone
- `review_theme_emerged` - Pattern in customer reviews

### 4. Customer Context (Optional)
Used for customer-specific messages:
- Customer name and visit history
- Last visit date and frequency
- Relationship strength with merchant

---

## Example Message

**Scenario:**
- **Merchant:** Sandeep runs "Tandoor Treats" restaurant in Hyderabad
- **Trigger:** A competitor just opened nearby
- **Performance:** 4.7% CTR (higher than 2.5% peer average)
- **Category:** Restaurants

**Vera composes:**

> Hey Sandeep, a competitor in Hyderabad just opened. Your 4.7% CTR is higher than the peer benchmark of 2.5%. What do you think is driving this engagement?

**Why it works:**
- **Specific:** Real numbers (4.7%, 2.5%)
- **Timely:** Explains why now (competitor opened)
- **Category-appropriate:** Casual restaurant owner tone
- **Personalized:** Uses actual performance data
- **Engaging:** Sparks curiosity and invites conversation

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                      (bot.py)                            │
├─────────────────────────────────────────────────────────┤
│  POST /v1/context   - Store/update context              │
│  POST /v1/tick      - Decide what messages to send      │
│  POST /v1/reply     - Handle merchant responses         │
│  GET  /v1/healthz   - Health check                      │
│  GET  /v1/metadata  - Bot information                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Message Composer (composer.py)              │
│                                                          │
│  • Loads 4 contexts (category, merchant, trigger,       │
│    customer)                                             │
│  • Uses Groq LLM (llama-3.3-70b-versatile)              │
│  • Temperature = 0 (deterministic output)               │
│  • Generates personalized, specific messages            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           Conversation Handler                           │
│        (conversation_handlers.py)                        │
│                                                          │
│  • Multi-turn conversation management                   │
│  • Auto-reply detection                                 │
│  • Intent classification (positive/negative/neutral)    │
│  • Context-aware response routing                       │
└─────────────────────────────────────────────────────────┘
```

---

## Dataset Structure

```
expanded/
├── categories/          (5 files)
│   ├── dentists.json
│   ├── salons.json
│   ├── restaurants.json
│   ├── gyms.json
│   └── pharmacies.json
│
├── merchants/           (51 files)
│   ├── m_001_drmeera_dentist_delhi.json
│   ├── m_022_sandeep_restaurant_hyderabad.json
│   └── ...
│
├── customers/           (200 files)
│   ├── c_001_priya_for_m_001_drmeera_dentist_delhi.json
│   └── ...
│
├── triggers/            (78 files)
│   ├── trg_001_research_digest_m_001_drmeera_dent.json
│   ├── trg_045_competitor_opened_m_022_sandeep_restau.json
│   └── ...
│
└── test_pairs.json      (30 test cases)
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Groq API key

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure API Key
Create a `.env` file in the root directory:
```
GROQ_API_KEY=gsk_your_api_key_here
```

### Start the Server
```bash
python bot.py
```

Server runs on `http://localhost:8080`

### Generate Test Submission
```bash
python generate_submission.py
```

This creates `submission.jsonl` with 30 test messages.

---

## API Endpoints

### POST /v1/context
Store or update context for categories, merchants, customers, or triggers.

**Request:**
```json
{
  "scope": "merchant",
  "context_id": "m_022_sandeep_restaurant_hyderabad",
  "version": 1,
  "payload": {
    "identity": {
      "name": "Sandeep",
      "business_name": "Tandoor Treats"
    },
    "category_slug": "restaurants",
    "performance": {
      "views_30d": 2847,
      "calls_30d": 134,
      "ctr": 0.047
    }
  }
}
```

### POST /v1/tick
Decide what messages to send based on available triggers.

**Request:**
```json
{
  "available_triggers": [
    "trg_045_competitor_opened_m_022_sandeep_restau"
  ]
}
```

**Response:**
```json
{
  "actions": [
    {
      "trigger_id": "trg_045_competitor_opened_m_022_sandeep_restau",
      "merchant_id": "m_022_sandeep_restaurant_hyderabad",
      "customer_id": null,
      "body": "Hey Sandeep, a competitor in Hyderabad just opened...",
      "cta": "open_ended",
      "send_as": "vera",
      "suppression_key": "competitor_opened:m_022_sandeep_restaurant_hyderabad:gen_45"
    }
  ]
}
```

### POST /v1/reply
Handle merchant's response to a message.

**Request:**
```json
{
  "merchant_id": "m_022_sandeep_restaurant_hyderabad",
  "inbound_text": "Yes, I'd like to know more about creating offers"
}
```

---

## Submission Format

The `submission.jsonl` file contains 30 test messages, one per line:

```json
{"test_id": "T01", "body": "...", "cta": "open_ended", "send_as": "vera", "suppression_key": "...", "rationale": "..."}
{"test_id": "T02", "body": "...", "cta": "open_ended", "send_as": "vera", "suppression_key": "...", "rationale": "..."}
...
```

**Fields:**
- `test_id` - Unique test identifier (T01-T30)
- `body` - The message text
- `cta` - Call-to-action type (always "open_ended")
- `send_as` - Sender identity ("vera" or "merchant_on_behalf")
- `suppression_key` - Deduplication key
- `rationale` - Why this message was composed this way

---

## Key Features

### 1. Specificity
Every message includes concrete numbers, dates, or sources:
- "4.7% CTR vs 2.5% peer average"
- "5274 views in the last 30 days"
- "JIDA Oct 2026, p.14"

### 2. Category Fit
Messages use appropriate vocabulary and tone for each business type:
- Dentists: Clinical, professional, journal citations
- Restaurants: Casual, operator-focused, footfall metrics
- Salons: Warm, trend-aware, service terminology
- Gyms: Motivational, fitness-focused, membership language
- Pharmacies: Trustworthy, precise, medical terminology

### 3. Trigger Relevance
Every message explains why it's being sent now:
- "A competitor just opened"
- "Your performance has improved"
- "Festival season is coming"
- "Your subscription is expiring"

### 4. Auto-Reply Detection
Identifies automated responses to avoid wasting conversation turns:
- Pattern matching for common auto-reply phrases
- Repetition detection
- Ends conversation after 2 auto-replies

### 5. Intent Classification
Routes merchant responses appropriately:
- **Positive intent** → Take action, provide next steps
- **Negative intent** → Acknowledge, offer alternatives
- **Neutral intent** → Clarify, ask follow-up questions

---

## Design Decisions

### Why Groq LLM?
- Fast inference (llama-3.3-70b-versatile)
- Cost-effective for high-volume messaging
- Strong instruction-following for structured output

### Why Temperature = 0?
- Deterministic output for consistent quality
- Reproducible results for testing
- Reduces hallucination risk

### Why 4-Context Framework?
- **Category** ensures industry-appropriate language
- **Merchant** enables personalization
- **Trigger** provides timely relevance
- **Customer** adds relationship depth

### Why In-Memory Storage?
- Fast context retrieval
- Version management for updates
- Suitable for challenge scope (production would use database)

---

## Testing

Run the test script to verify message composition:

```bash
python test_bot.py
```

This loads sample contexts and generates a test message.

---

## Project Structure

```
vera-ai-assistant/
├── bot.py                      # FastAPI server
├── composer.py                 # Message composition engine
├── conversation_handlers.py    # Multi-turn conversation logic
├── models.py                   # Data structures (Pydantic models)
├── generate_submission.py      # Creates submission.jsonl
├── test_bot.py                 # Test script
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not in git)
├── .env.example                # Example environment file
├── .gitignore                  # Git ignore rules
├── submission.jsonl            # 30 test messages (submission file)
└── expanded/                   # Dataset
    ├── categories/             # 5 category files
    ├── merchants/              # 51 merchant files
    ├── customers/              # 200 customer files
    ├── triggers/               # 78 trigger files
    └── test_pairs.json         # 30 test case mappings
```

---

## Coverage

**30 test messages covering:**
- 5 business categories (dentists, salons, restaurants, gyms, pharmacies)
- 10 trigger types (research_digest, competitor_opened, perf_dip, perf_spike, customer_lapsed_soft, recall_due, renewal_due, festival_upcoming, milestone_reached, review_theme_emerged)
- 2 sender types (vera, merchant_on_behalf)
- 22 merchant-facing messages
- 8 customer-facing messages

---

## Evaluation Criteria

Messages are scored on:

1. **Specificity** - Concrete numbers, dates, sources
2. **Category Fit** - Appropriate vocabulary and tone
3. **Merchant Fit** - Personalized to specific merchant
4. **Trigger Relevance** - Clear "why now"
5. **Engagement** - Likely to get a response

---

## Technologies Used

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Groq API** - LLM inference (llama-3.3-70b-versatile)
- **Python 3.8+** - Programming language

