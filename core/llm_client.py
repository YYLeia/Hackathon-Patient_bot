"""
core/llm_client.py
LLM abstraction — OpenAI live client + context-aware MockLLMClient for offline demos.
"""

from __future__ import annotations
import os
import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def chat_completion(self, messages: list[dict], temperature: float = 0.7) -> str:
        ...


# ── OpenAI Live Client ─────────────────────────────────────────────────────────

class OpenAIClient:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", ""))
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.model = model

    def chat_completion(self, messages: list[dict], temperature: float = 0.7) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=512,
        )
        return response.choices[0].message.content or ""


# ── Context-Aware Mock Client (for offline demos) ─────────────────────────────

def _extract_patient_name(messages: list[dict]) -> str:
    """Pull the patient's first name out of the system prompt."""
    for msg in messages:
        if msg.get("role") == "system":
            m = re.search(r"Always refer to the patient by their first name: (\w+)", msg["content"])
            if m:
                return m.group(1)
            m = re.search(r"Name:\s+(\w+)", msg["content"])
            if m:
                return m.group(1)
    return "there"


def _last_patient_text(messages: list[dict]) -> str:
    """Return the most recent user/patient message text, or empty string."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg["content"].lower().strip()
    return ""


def _count_turns(messages: list[dict]) -> int:
    """Count how many user turns have occurred so far."""
    return sum(1 for m in messages if m.get("role") == "user")


def _build_context_aware_response(messages: list[dict]) -> str:
    """
    Generate a contextually relevant response by reading the conversation history.
    Matches key phrases in the patient's last message and responds appropriately,
    then advances to the next check-in topic.
    """
    name = _extract_patient_name(messages)
    patient_text = _last_patient_text(messages)
    turn = _count_turns(messages)

    # ── Emergency detection (highest priority) ─────────────────────────────
    if re.search(r"chest pain|can't breathe|cannot breathe|collapse|collapsed|fall\b|fallen|unconscious", patient_text):
        return (
            f"⚠️ {name}, what you're describing sounds serious. "
            "Please call 000 (emergency services) right now or ask someone nearby to help. "
            "If you have an emergency contact, please call them immediately too."
        )

    # ── Opening greeting (turn 0 = no patient messages yet) ───────────────
    if turn == 0:
        return (
            f"Hello {name}! 😊 I'm Dr. Mario, your post-discharge support assistant. "
            "I'm here to check in on how you've been feeling since you left hospital. "
            "How are you feeling overall today?"
        )

    # ── Pain acknowledgement ───────────────────────────────────────────────
    pain_match = re.search(r"\b([0-9]|10)\s*(out of|/|over)?\s*10\b", patient_text)
    if re.search(r"\bpain\b|hurt(ing)?|ache|sore|discomfort", patient_text):
        if pain_match:
            level = int(pain_match.group(1))
            if level >= 7:
                return (
                    f"A pain level of {level} is quite high, {name} — I'm sorry you're experiencing that. "
                    "I'll make sure to flag this for your care team right away. "
                    "Have you been able to take your pain relief medication as prescribed today?"
                )
            elif level >= 4:
                return (
                    f"Thank you for letting me know — a pain level of {level} is something we want to "
                    f"keep monitoring, {name}. I'll note that for your care team. "
                    "Have you been taking all your prescribed medications today?"
                )
            else:
                return (
                    f"I'm relieved to hear the pain is only at {level}, {name} — that's manageable. "
                    "Let's keep an eye on it. Have you been taking your medications as scheduled?"
                )
        return (
            f"I'm sorry to hear you're in pain, {name}. "
            "On a scale of 0 to 10, how would you rate the pain right now?"
        )

    # ── Feeling bad / unwell ───────────────────────────────────────────────
    if re.search(r"\b(not (well|good|great)|unwell|sick|terrible|awful|dizzy|nausea|vomit|weak|fatigue|tired|exhausted)\b", patient_text):
        return (
            f"I'm sorry to hear you're not feeling well, {name}. "
            "That sounds uncomfortable — can you tell me more about what you're experiencing? "
            "Is there any pain, dizziness, or anything that's gotten worse since yesterday?"
        )

    # ── Feeling okay / good ───────────────────────────────────────────────
    if re.search(r"\b(okay|ok|fine|good|well|better|great|alright|not bad)\b", patient_text):
        if turn == 1:
            return (
                f"That's good to hear, {name}! It's normal to feel a bit up and down after a hospital stay. "
                "On a scale of 0 to 10, how would you rate any pain or discomfort you're feeling right now?"
            )
        return (
            f"Glad to hear that, {name}. "
            "Have you been able to take all your prescribed medications today as scheduled?"
        )

    # ── Medication missed ──────────────────────────────────────────────────
    if re.search(r"miss(ed)?|forgot|forget|didn'?t take|skipped|haven'?t taken", patient_text):
        return (
            f"It's really important not to miss doses, {name} — especially your heart and blood pressure "
            "medications. If you can, please take the missed dose now unless it's almost time for the next one. "
            "Are you having trouble remembering when to take them? A pill organiser or alarm might help."
        )

    # ── Medications taken / adherent ──────────────────────────────────────
    if re.search(r"took|taken|yes.{0,15}(med|pill|tablet)|all\s+my\s+med", patient_text):
        return (
            f"Excellent work keeping up with your medications, {name}! 💊 "
            "That's one of the most important parts of your recovery. "
            "How has your appetite been — have you been eating and drinking regularly?"
        )

    # ── Appetite / eating ─────────────────────────────────────────────────
    if re.search(r"eat(ing|en)|food|meal|appetite|hungry|not eating|no appetite", patient_text):
        if re.search(r"not eating|no appetite|can'?t eat|haven'?t eaten", patient_text):
            return (
                f"Not having much of an appetite is common after a hospital stay, {name}, "
                "but it's important to eat small amounts regularly, especially when taking your medications. "
                "Try small snacks if full meals feel like too much. How has your sleep been lately?"
            )
        return (
            f"That's great — keeping up with regular meals supports your recovery, {name}. "
            "How has your sleep been since you came home from hospital?"
        )

    # ── Sleep ─────────────────────────────────────────────────────────────
    if re.search(r"sleep|slept|rest|tired|exhausted|can'?t sleep|insomnia|woke up", patient_text):
        if re.search(r"can'?t sleep|insomnia|bad sleep|poor sleep|not sleeping|woke up", patient_text):
            return (
                f"Poor sleep can really affect your recovery, {name}. "
                "Try to keep a consistent bedtime and avoid screens before bed. "
                "I'll mention this to your care team. Have you been able to do any gentle movement or "
                "short walks today?"
            )
        return (
            f"Rest is so important for recovery — I'm glad you're getting some, {name}. "
            "Have you been able to do any gentle walking or light activity today?"
        )

    # ── Mobility / walking ────────────────────────────────────────────────
    if re.search(r"walk(ed|ing)?|mov(ed|ing)|exercise|steps|activ", patient_text):
        if re.search(r"can'?t walk|not walking|haven'?t moved|no movement|too weak", patient_text):
            return (
                f"Not being able to move around much is understandable after your stay, {name}. "
                "Even very short, slow walks around the room help with circulation. "
                "If you're feeling too weak to walk safely, please let your care team know. "
                "How are you feeling emotionally — any worries or low mood?"
            )
        return (
            f"That's wonderful — staying active even in small ways speeds up recovery, {name}. "
            "I also want to check in on how you're feeling emotionally. "
            "Have you been feeling anxious, worried, or low in mood recently?"
        )

    # ── Mental health / mood ──────────────────────────────────────────────
    if re.search(r"depress(ed)?|anxious|anxiety|worry|worried|sad|lonely|overwhelm|scared|fear|low mood", patient_text):
        return (
            f"Thank you for sharing that with me, {name} — it takes courage to talk about how we're feeling. "
            "It's very normal to feel anxious or low after a hospital stay. "
            "I'll make sure your care team knows so they can offer the right support. "
            "Is there anything specific that's been on your mind?"
        )

    # ── Swelling / fluid ──────────────────────────────────────────────────
    if re.search(r"swell(ing|en)?|puffy|ankles?|legs?\s+(look|feel)|fluid", patient_text):
        return (
            f"Any swelling in the legs or ankles is worth keeping a close eye on, {name}. "
            "Please weigh yourself first thing tomorrow morning and note it down — "
            "contact your doctor if your weight goes up more than 2kg in two days. "
            "Have you been able to keep your fluid intake within the recommended limit?"
        )

    # ── Appointment / doctor ──────────────────────────────────────────────
    if re.search(r"appointment|doctor|gp|specialist|clinic|visit", patient_text):
        return (
            f"Good that you're thinking about your appointments, {name}! "
            "Please make sure you have transport arranged and bring your medication list. "
            "Is there anything specific you'd like to discuss with your doctor that I can help you note down?"
        )

    # ── Closing / nothing more ────────────────────────────────────────────
    if re.search(r"nothing|no (more|questions|concerns)|all good|that'?s? (it|all)|done|finished", patient_text):
        return (
            f"Thank you so much for chatting with me today, {name}. 💙 "
            "I've noted all your responses and your care team will review them. "
            "Remember to take your medications, monitor your weight daily, and call 000 immediately "
            "if you experience chest pain, severe breathlessness, or anything urgent. "
            "I'll check in with you again soon. Take good care! ✅"
        )

    # ── Fallback — advance the check-in to the next topic ─────────────────
    fallback_questions = [
        f"Thank you, {name}. On a scale of 0 to 10, how would you rate any pain or discomfort right now?",
        f"I appreciate you sharing that, {name}. Have you been taking all your medications as prescribed today?",
        f"Good to know, {name}. How has your appetite been — are you eating and drinking regularly?",
        f"Thanks {name}. How has your sleep been since coming home from hospital?",
        f"Noted, {name}. Have you been able to do any gentle walking or light movement today?",
        f"Thank you for letting me know, {name}. How are you feeling emotionally — any worries or low mood?",
        (
            f"Thank you for chatting with me today, {name}. 💙 "
            "I've noted your responses for your care team. "
            "Remember to take your medications and call 000 if anything urgent comes up. "
            "I'll check in with you again soon. Take good care! ✅"
        ),
    ]
    idx = min(turn - 1, len(fallback_questions) - 1)
    return fallback_questions[idx]


class MockLLMClient:
    """
    Context-aware mock LLM client for offline demos.
    Reads the full conversation history passed in 'messages' and generates
    a contextually relevant response — no hardcoded script cycling.
    """

    def chat_completion(self, messages: list[dict], temperature: float = 0.7) -> str:  # noqa: ARG002
        return _build_context_aware_response(messages)

    def reset(self) -> None:
        pass  # stateless — nothing to reset
