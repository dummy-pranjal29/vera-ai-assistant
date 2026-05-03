import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from models import (
    ContextUpdate, TickRequest, TickResponse, ReplyRequest, ReplyResponse,
    HealthResponse, MetadataResponse, ComposedMessage, CategoryContext,
    MerchantContext, TriggerContext, CustomerContext
)
from composer import Composer, ContextStore

load_dotenv()

app = FastAPI(title="Vera AI Assistant", version="1.0.0")

composer = Composer()
start_time = time.time()
conversation_states: Dict[str, Dict[str, Any]] = {}
sent_suppressions: Dict[str, set] = {}


@app.post("/v1/context")
async def store_context(update: ContextUpdate):
    try:
        composer.store.store_context(
            scope=update.scope,
            context_id=update.context_id,
            version=update.version,
            payload=update.payload
        )
        return {
            "status": "stored",
            "context_id": update.context_id,
            "scope": update.scope,
            "version": update.version
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/tick")
async def tick(request: TickRequest):
    try:
        actions = []

        for trigger_id in request.available_triggers:
            trigger = composer.store.get_trigger(trigger_id)
            if not trigger:
                continue

            if trigger.suppression_key in sent_suppressions:
                if trigger_id in sent_suppressions[trigger.suppression_key]:
                    continue

            merchant_id = trigger.payload.get("merchant_id")
            if not merchant_id:
                continue

            merchant = composer.store.get_merchant(merchant_id)
            if not merchant:
                continue

            category_slug = merchant_id.split("_")[1] if "_" in merchant_id else None
            if not category_slug:
                for cat_id in ["dentists", "salons", "restaurants", "gyms", "pharmacies"]:
                    if cat_id in merchant_id.lower():
                        category_slug = cat_id
                        break

            category = composer.store.get_category(category_slug) if category_slug else None
            if not category:
                continue

            customer_id = trigger.payload.get("customer_id")
            customer = None
            if customer_id:
                customer = composer.store.get_customer(customer_id)

            try:
                message = composer.compose(category, merchant, trigger, customer)

                if trigger.suppression_key not in sent_suppressions:
                    sent_suppressions[trigger.suppression_key] = set()
                sent_suppressions[trigger.suppression_key].add(trigger_id)

                actions.append(message)
            except Exception as e:
                continue

        return TickResponse(actions=actions)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/reply")
async def reply(request: ReplyRequest):
    try:
        if request.conversation_id not in conversation_states:
            conversation_states[request.conversation_id] = {
                "merchant_id": request.merchant_id,
                "turns": [],
                "last_action": None
            }

        state = conversation_states[request.conversation_id]
        state["turns"].append({
            "role": request.from_role,
            "message": request.message,
            "turn_number": request.turn_number
        })

        merchant = composer.store.get_merchant(request.merchant_id)
        if not merchant:
            return ReplyResponse(
                action="end",
                rationale="Merchant context not found"
            )

        is_auto_reply = composer.detect_auto_reply(request.message, state["turns"])
        if is_auto_reply:
            if state["turns"].count(lambda t: t.get("role") == "merchant") >= 2:
                return ReplyResponse(
                    action="end",
                    rationale="Auto-reply detected, ending conversation"
                )
            return ReplyResponse(
                action="wait",
                wait_seconds=3600,
                rationale="Auto-reply detected, waiting before retry"
            )

        intent = composer.detect_intent(request.message)
        if intent == "negative":
            return ReplyResponse(
                action="end",
                rationale="Merchant expressed disinterest"
            )

        if intent == "positive":
            return ReplyResponse(
                action="send",
                body="Great! Let me help you with that. What would you like to focus on first?",
                cta="open_ended",
                rationale="Merchant showed positive intent, moving to action mode"
            )

        if request.turn_number >= 4:
            return ReplyResponse(
                action="end",
                rationale="Conversation reached max turns"
            )

        return ReplyResponse(
            action="send",
            body="Thanks for your message. Can you tell me more about what you're looking for?",
            cta="open_ended",
            rationale="Continuing conversation with clarification"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/healthz")
async def health():
    uptime = int(time.time() - start_time)
    stats = composer.store.get_stats()

    return HealthResponse(
        status="ok",
        uptime_seconds=uptime,
        contexts_loaded=stats
    )


@app.get("/v1/metadata")
async def metadata():
    return MetadataResponse(
        team_name="Vera AI Team",
        model="claude-opus-4-7",
        approach="Multi-context composition with LLM-based message generation",
        version="1.0.0"
    )


@app.get("/")
async def root():
    return {
        "service": "Vera AI Assistant",
        "version": "1.0.0",
        "endpoints": {
            "POST /v1/context": "Store context updates",
            "POST /v1/tick": "Compose messages for available triggers",
            "POST /v1/reply": "Handle merchant replies",
            "GET /v1/healthz": "Health check",
            "GET /v1/metadata": "Bot metadata"
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
