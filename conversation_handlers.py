import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class ConversationAction(str, Enum):
    SEND = "send"
    WAIT = "wait"
    END = "end"


@dataclass
class ConversationTurn:
    role: str
    message: str
    timestamp: str
    turn_number: int


@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    turns: List[ConversationTurn] = field(default_factory=list)
    last_vera_action: Optional[str] = None
    auto_reply_count: int = 0
    intent_detected: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationHandler:
    def __init__(self):
        self.states: Dict[str, ConversationState] = {}
        self.auto_reply_patterns = [
            "thank you for contacting",
            "automated response",
            "auto-reply",
            "out of office",
            "will get back to you",
            "appreciate your message",
            "thanks for reaching out",
            "we will respond",
            "automated message",
            "away from office"
        ]

    def get_or_create_state(
        self,
        conversation_id: str,
        merchant_id: str,
        customer_id: Optional[str] = None
    ) -> ConversationState:
        if conversation_id not in self.states:
            self.states[conversation_id] = ConversationState(
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                customer_id=customer_id
            )
        return self.states[conversation_id]

    def add_turn(
        self,
        conversation_id: str,
        role: str,
        message: str,
        turn_number: int
    ) -> ConversationState:
        state = self.get_or_create_state(conversation_id, "", None)
        turn = ConversationTurn(
            role=role,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            turn_number=turn_number
        )
        state.turns.append(turn)
        state.last_updated = datetime.utcnow().isoformat()
        return state

    def is_auto_reply(self, message: str, state: ConversationState) -> bool:
        message_lower = message.lower().strip()

        for pattern in self.auto_reply_patterns:
            if pattern in message_lower:
                return True

        merchant_turns = [t for t in state.turns if t.role == "merchant"]
        if len(merchant_turns) >= 2:
            if merchant_turns[-1].message.lower() == message_lower:
                return True

        return False

    def detect_intent(self, message: str) -> Optional[str]:
        message_lower = message.lower().strip()

        positive_keywords = [
            "yes", "yeah", "yep", "sure", "okay", "ok", "go ahead",
            "let's do it", "proceed", "start", "join", "sign up",
            "interested", "count me in", "sounds good", "perfect",
            "great", "absolutely", "definitely", "please do"
        ]

        negative_keywords = [
            "no", "nope", "nah", "stop", "not interested",
            "don't", "remove", "unsubscribe", "stop messaging",
            "leave me alone", "not now", "later", "busy"
        ]

        for keyword in positive_keywords:
            if keyword in message_lower:
                return "positive"

        for keyword in negative_keywords:
            if keyword in message_lower:
                return "negative"

        return None

    def should_continue_conversation(self, state: ConversationState) -> bool:
        merchant_turns = [t for t in state.turns if t.role == "merchant"]

        if len(merchant_turns) >= 3:
            return False

        if state.auto_reply_count >= 2:
            return False

        if state.intent_detected == "negative":
            return False

        return True

    def get_next_action(
        self,
        state: ConversationState,
        merchant_message: str
    ) -> Dict[str, Any]:

        is_auto = self.is_auto_reply(merchant_message, state)
        if is_auto:
            state.auto_reply_count += 1
            if state.auto_reply_count >= 2:
                return {
                    "action": ConversationAction.END,
                    "rationale": "Multiple auto-replies detected, ending conversation"
                }
            return {
                "action": ConversationAction.WAIT,
                "wait_seconds": 3600,
                "rationale": "Auto-reply detected, waiting before next attempt"
            }

        intent = self.detect_intent(merchant_message)
        state.intent_detected = intent

        if intent == "negative":
            return {
                "action": ConversationAction.END,
                "rationale": "Merchant expressed disinterest"
            }

        if intent == "positive":
            return {
                "action": ConversationAction.SEND,
                "body": "Excellent! I'm ready to help. What would you like to focus on first?",
                "cta": "open_ended",
                "rationale": "Merchant showed positive intent, moving to action mode"
            }

        merchant_turn_count = len([t for t in state.turns if t.role == "merchant"])
        if merchant_turn_count >= 3:
            return {
                "action": ConversationAction.END,
                "rationale": "Conversation reached maximum turns without clear intent"
            }

        return {
            "action": ConversationAction.SEND,
            "body": "Thanks for your message. Could you share more details about what you're looking for?",
            "cta": "open_ended",
            "rationale": "Continuing conversation with clarification request"
        }

    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        state = self.states.get(conversation_id)
        if not state:
            return None

        return {
            "conversation_id": conversation_id,
            "merchant_id": state.merchant_id,
            "customer_id": state.customer_id,
            "turn_count": len(state.turns),
            "auto_reply_count": state.auto_reply_count,
            "intent_detected": state.intent_detected,
            "created_at": state.created_at,
            "last_updated": state.last_updated,
            "turns": [
                {
                    "role": t.role,
                    "message": t.message,
                    "turn_number": t.turn_number,
                    "timestamp": t.timestamp
                }
                for t in state.turns
            ]
        }

    def cleanup_old_conversations(self, max_age_hours: int = 24):
        now = datetime.utcnow()
        to_delete = []

        for conv_id, state in self.states.items():
            last_updated = datetime.fromisoformat(state.last_updated)
            age_hours = (now - last_updated).total_seconds() / 3600

            if age_hours > max_age_hours:
                to_delete.append(conv_id)

        for conv_id in to_delete:
            del self.states[conv_id]

        return len(to_delete)


class ResponseBuilder:
    @staticmethod
    def build_send_response(
        body: str,
        cta: str,
        rationale: str
    ) -> Dict[str, Any]:
        return {
            "action": "send",
            "body": body,
            "cta": cta,
            "rationale": rationale
        }

    @staticmethod
    def build_wait_response(
        wait_seconds: int,
        rationale: str
    ) -> Dict[str, Any]:
        return {
            "action": "wait",
            "wait_seconds": wait_seconds,
            "rationale": rationale
        }

    @staticmethod
    def build_end_response(rationale: str) -> Dict[str, Any]:
        return {
            "action": "end",
            "rationale": rationale
        }


class IntentRouter:
    def __init__(self):
        self.action_keywords = {
            "profile_update": ["update", "profile", "google", "gbp", "business"],
            "campaign": ["campaign", "offer", "promotion", "discount", "deal"],
            "customer_engagement": ["customer", "message", "contact", "reach"],
            "analytics": ["stats", "performance", "views", "calls", "metrics"],
            "join": ["join", "subscribe", "sign up", "register", "enroll"]
        }

    def classify_intent(self, message: str) -> Optional[str]:
        message_lower = message.lower()

        for intent_type, keywords in self.action_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return intent_type

        return None

    def get_action_response(self, intent_type: str) -> str:
        responses = {
            "profile_update": "I can help you update your Google Business Profile. Let me guide you through it.",
            "campaign": "Great! Let's set up a campaign. What type of offer would work best for you?",
            "customer_engagement": "Perfect! I can help you engage your customers. What message would you like to send?",
            "analytics": "Let me pull up your performance metrics and show you the opportunities.",
            "join": "Excellent! Let me get you started with the onboarding process."
        }
        return responses.get(intent_type, "How can I help you today?")
