import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import OpenAI
from models import (
    CategoryContext, MerchantContext, TriggerContext, CustomerContext,
    ComposedMessage, VoiceProfile, OfferTemplate, PeerStats, DigestItem,
    SeasonalBeat, Identity, Subscription, PerformanceSnapshot, MerchantOffer,
    ConversationHistory, CustomerAggregate, DerivedSignal, CustomerIdentity,
    Relationship
)


class ContextStore:
    def __init__(self):
        self.categories: Dict[str, tuple[CategoryContext, int]] = {}
        self.merchants: Dict[str, tuple[MerchantContext, int]] = {}
        self.customers: Dict[str, tuple[CustomerContext, int]] = {}
        self.triggers: Dict[str, tuple[TriggerContext, int]] = {}

    def store_context(self, scope: str, context_id: str, version: int, payload: Dict[str, Any]):
        if scope == "category":
            existing_version = self.categories.get(context_id, (None, 0))[1]
            if version > existing_version:
                self.categories[context_id] = (self._build_category(payload), version)
        elif scope == "merchant":
            existing_version = self.merchants.get(context_id, (None, 0))[1]
            if version > existing_version:
                self.merchants[context_id] = (self._build_merchant(payload), version)
        elif scope == "customer":
            existing_version = self.customers.get(context_id, (None, 0))[1]
            if version > existing_version:
                self.customers[context_id] = (self._build_customer(payload), version)
        elif scope == "trigger":
            existing_version = self.triggers.get(context_id, (None, 0))[1]
            if version > existing_version:
                self.triggers[context_id] = (self._build_trigger(payload), version)

    def get_category(self, category_id: str) -> Optional[CategoryContext]:
        result = self.categories.get(category_id)
        return result[0] if result else None

    def get_merchant(self, merchant_id: str) -> Optional[MerchantContext]:
        result = self.merchants.get(merchant_id)
        return result[0] if result else None

    def get_customer(self, customer_id: str) -> Optional[CustomerContext]:
        result = self.customers.get(customer_id)
        return result[0] if result else None

    def get_trigger(self, trigger_id: str) -> Optional[TriggerContext]:
        result = self.triggers.get(trigger_id)
        return result[0] if result else None

    def get_stats(self) -> Dict[str, int]:
        return {
            "category": len(self.categories),
            "merchant": len(self.merchants),
            "customer": len(self.customers),
            "trigger": len(self.triggers)
        }

    def _build_category(self, data: Dict[str, Any]) -> CategoryContext:
        voice = VoiceProfile(
            tone=data["voice"]["tone"],
            allowed_vocab=data["voice"]["allowed_vocab"],
            taboos=data["voice"]["taboos"],
            formality=data["voice"]["formality"],
            language_preference=data["voice"]["language_preference"]
        )

        offers = [
            OfferTemplate(
                service=o["service"],
                price_range=o["price_range"],
                typical_duration=o.get("typical_duration")
            )
            for o in data["offer_catalog"]
        ]

        peer_stats = PeerStats(
            avg_rating=data["peer_stats"]["avg_rating"],
            avg_reviews=data["peer_stats"]["avg_reviews"],
            avg_ctr=data["peer_stats"]["avg_ctr"],
            locality=data["peer_stats"]["locality"]
        )

        digest = [
            DigestItem(
                title=d["title"],
                source=d["source"],
                summary=d["summary"],
                relevance=d["relevance"],
                published_date=d["published_date"]
            )
            for d in data["digest"]
        ]

        seasonal = [
            SeasonalBeat(
                months=s["months"],
                pattern=s["pattern"],
                opportunity=s["opportunity"]
            )
            for s in data["seasonal_beats"]
        ]

        return CategoryContext(
            slug=data["slug"],
            offer_catalog=offers,
            voice=voice,
            peer_stats=peer_stats,
            digest=digest,
            seasonal_beats=seasonal
        )

    def _build_merchant(self, data: Dict[str, Any]) -> MerchantContext:
        identity = Identity(
            name=data["identity"]["name"],
            owner_name=data["identity"].get("owner_name"),
            place_id=data["identity"]["place_id"],
            locality=data["identity"]["locality"],
            city=data["identity"]["city"],
            verified=data["identity"]["verified"],
            languages=data["identity"]["languages"]
        )

        subscription = Subscription(
            status=data["subscription"]["status"],
            days_remaining=data["subscription"]["days_remaining"],
            plan=data["subscription"]["plan"]
        )

        performance = PerformanceSnapshot(
            views_30d=data["performance"]["views_30d"],
            calls_30d=data["performance"]["calls_30d"],
            directions_30d=data["performance"]["directions_30d"],
            ctr_30d=data["performance"]["ctr_30d"],
            views_7d_delta=data["performance"]["views_7d_delta"],
            calls_7d_delta=data["performance"]["calls_7d_delta"]
        )

        offers = [
            MerchantOffer(
                service=o["service"],
                price=o["price"],
                status=o["status"],
                created_date=o["created_date"],
                expiry_date=o.get("expiry_date")
            )
            for o in data["offers"]
        ]

        history = ConversationHistory(
            turns=data["conversation_history"]["turns"],
            last_merchant_reply=data["conversation_history"].get("last_merchant_reply"),
            last_vera_message=data["conversation_history"].get("last_vera_message"),
            engagement_score=data["conversation_history"]["engagement_score"]
        )

        customer_agg = CustomerAggregate(
            total_customers=data["customer_aggregate"]["total_customers"],
            active_customers=data["customer_aggregate"]["active_customers"],
            lapsed_customers=data["customer_aggregate"]["lapsed_customers"],
            retention_rate=data["customer_aggregate"]["retention_rate"],
            segments=data["customer_aggregate"]["segments"]
        )

        signals = [
            DerivedSignal(
                signal_type=s["signal_type"],
                value=s["value"],
                detected_at=s["detected_at"]
            )
            for s in data["signals"]
        ]

        return MerchantContext(
            merchant_id=data["merchant_id"],
            identity=identity,
            subscription=subscription,
            performance=performance,
            offers=offers,
            conversation_history=history,
            customer_aggregate=customer_agg,
            signals=signals
        )

    def _build_customer(self, data: Dict[str, Any]) -> CustomerContext:
        identity = CustomerIdentity(
            name=data["identity"]["name"],
            phone=data["identity"]["phone"],
            language_pref=data["identity"]["language_pref"]
        )

        relationship = Relationship(
            first_visit=data["relationship"]["first_visit"],
            last_visit=data["relationship"]["last_visit"],
            visits_total=data["relationship"]["visits_total"],
            services_received=data["relationship"]["services_received"]
        )

        return CustomerContext(
            customer_id=data["customer_id"],
            merchant_id=data["merchant_id"],
            identity=identity,
            relationship=relationship,
            state=data["state"],
            preferences=data["preferences"],
            consent=data["consent"]
        )

    def _build_trigger(self, data: Dict[str, Any]) -> TriggerContext:
        return TriggerContext(
            id=data["id"],
            scope=data["scope"],
            kind=data["kind"],
            source=data["source"],
            payload=data["payload"],
            urgency=data["urgency"],
            suppression_key=data["suppression_key"],
            expires_at=data["expires_at"]
        )


class Composer:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(
            api_key=api_key or os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.store = ContextStore()
        self.sent_messages: Dict[str, set] = {}

    def compose(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        trigger: TriggerContext,
        customer: Optional[CustomerContext] = None
    ) -> ComposedMessage:

        system_prompt = self._build_system_prompt(category, customer is not None)
        user_prompt = self._build_user_prompt(category, merchant, trigger, customer)

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=2000
        )

        content = response.choices[0].message.content
        parsed = self._parse_response(content)

        return ComposedMessage(
            body=parsed["body"],
            cta=parsed["cta"],
            send_as=parsed["send_as"],
            suppression_key=trigger.suppression_key,
            rationale=parsed["rationale"],
            merchant_id=merchant.merchant_id,
            customer_id=customer.customer_id if customer else None,
            trigger_id=trigger.id
        )

    def _build_system_prompt(self, category: CategoryContext, is_customer_facing: bool) -> str:
        voice = category.voice

        base = f"""You are Vera, an AI assistant for merchants on WhatsApp.

Your voice: {voice.tone}
Formality level: {voice.formality}
Language preference: {voice.language_preference}

Allowed technical vocabulary: {', '.join(voice.allowed_vocab)}
NEVER use these words: {', '.join(voice.taboos)}

Rules:
1. Be specific - anchor on verifiable facts (numbers, dates, sources)
2. Single CTA only - either YES/STOP, open_ended, or none
3. No fabrication - only use data from contexts
4. Match merchant's language preference
5. Peer tone, not promotional
6. Keep it concise for WhatsApp
7. Use compulsion levers: curiosity, social proof, loss aversion, reciprocity, effort externalization

Response format (JSON):
{{
    "body": "The WhatsApp message",
    "cta": "YES/STOP" or "open_ended" or "none",
    "send_as": "vera" or "merchant_on_behalf",
    "rationale": "Why this message, what it achieves"
}}"""

        if is_customer_facing:
            base += "\n\nYou are composing a message FROM the merchant TO their customer."
            base += "\nDo not mention Vera or magicpin."
            base += "\nUse merchant's name and personal touch."

        return base

    def _build_user_prompt(
        self,
        category: CategoryContext,
        merchant: MerchantContext,
        trigger: TriggerContext,
        customer: Optional[CustomerContext]
    ) -> str:

        prompt = f"""Compose a WhatsApp message for {merchant.identity.name} in {merchant.identity.city}.

MERCHANT CONTEXT:
- Owner: {merchant.identity.owner_name or merchant.identity.name}
- Location: {merchant.identity.locality}, {merchant.identity.city}
- Subscription: {merchant.subscription.plan} ({merchant.subscription.status})
- Performance (30d): {merchant.performance.views_30d} views, {merchant.performance.calls_30d} calls, CTR {merchant.performance.ctr_30d:.1%}
- Peer benchmark CTR: {category.peer_stats.avg_ctr:.1%}
- Active offers: {', '.join([o.service for o in merchant.offers if o.status == 'active']) or 'None'}
- Signals: {', '.join([s.signal_type for s in merchant.signals]) or 'None'}
- Last Vera message: {merchant.conversation_history.last_vera_message or 'None'}
- Engagement score: {merchant.conversation_history.engagement_score:.1f}/1.0

TRIGGER:
- Type: {trigger.kind}
- Source: {trigger.source}
- Urgency: {trigger.urgency}/5
- Details: {json.dumps(trigger.payload, indent=2)}

CATEGORY INSIGHTS:
- Peer avg rating: {category.peer_stats.avg_rating}★
- Peer avg reviews: {category.peer_stats.avg_reviews}
- Recent digest: {category.digest[0].title if category.digest else 'None'} ({category.digest[0].source if category.digest else 'N/A'})
"""

        if customer:
            prompt += f"""
CUSTOMER CONTEXT:
- Name: {customer.identity.name}
- Language: {customer.identity.language_pref}
- Relationship: {customer.relationship.visits_total} visits, last visit {customer.relationship.last_visit}
- State: {customer.state}
- Services: {', '.join(customer.relationship.services_received)}
- Preferences: {json.dumps(customer.preferences)}
"""

        prompt += "\nCompose the message now. Return valid JSON only."
        return prompt

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            json_str = content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            parsed = json.loads(json_str.strip())
            return {
                "body": parsed.get("body", ""),
                "cta": parsed.get("cta", "none"),
                "send_as": parsed.get("send_as", "vera"),
                "rationale": parsed.get("rationale", "")
            }
        except json.JSONDecodeError:
            return {
                "body": content[:500],
                "cta": "none",
                "send_as": "vera",
                "rationale": "Parse error"
            }

    def detect_auto_reply(self, message: str, history: List[Dict[str, Any]]) -> bool:
        if not history:
            return False

        recent_messages = [turn.get("message", "") for turn in history[-3:] if turn.get("role") == "merchant"]

        if len(recent_messages) >= 2 and message == recent_messages[-1]:
            return True

        auto_reply_patterns = [
            "thank you for contacting",
            "automated response",
            "auto-reply",
            "out of office",
            "will get back to you",
            "appreciate your message"
        ]

        message_lower = message.lower()
        return any(pattern in message_lower for pattern in auto_reply_patterns)

    def detect_intent(self, message: str) -> Optional[str]:
        message_lower = message.lower()

        positive_intents = ["yes", "go ahead", "let's do it", "proceed", "start", "join", "sign up", "interested"]
        negative_intents = ["no", "stop", "not interested", "don't", "remove", "unsubscribe"]

        for intent in positive_intents:
            if intent in message_lower:
                return "positive"

        for intent in negative_intents:
            if intent in message_lower:
                return "negative"

        return None
