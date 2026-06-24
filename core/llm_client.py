"""
core/llm_client.py
LLM abstraction — OpenAI live client + fully scripted MockLLMClient for offline demos.
"""

from __future__ import annotations
import os
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


# ── Mock Scripted Client (for offline demos) ──────────────────────────────────

DEMO_SCRIPT = [
    # Opening greeting (start_session)
    (
        "Hello Margaret! 😊 I'm Dr. Mario, your post-discharge support assistant. "
        "I'm here to check in on how you've been feeling since you left hospital 3 days ago. "
        "How are you feeling overall today?"
    ),
    # Response 1
    (
        "I'm glad to hear that. It's completely normal to feel a bit tired after a hospital stay — "
        "your body has been through a lot. On a scale of 0 to 10, how would you rate any pain or "
        "discomfort you're experiencing right now?"
    ),
    # Response 2
    (
        "A pain level of 6 is something we want to keep an eye on. Have you been taking your "
        "Furosemide and Lisinopril as prescribed this morning?"
    ),
    # Response 3 — medication concern
    (
        "It's very important to take your Metformin with meals to manage your blood sugar. "
        "I'll flag this for your care team. Can you take it now with a small snack if you haven't eaten? "
        "Also — have you noticed any swelling in your legs or ankles today?"
    ),
    # Response 4
    (
        "Any new or increased swelling could be a sign your fluid balance needs attention. "
        "Please weigh yourself today — your discharge notes say to contact your doctor if "
        "your weight goes up more than 2kg in 2 days. Have you been able to do any gentle walking today?"
    ),
    # Response 5
    (
        "That's great to hear! Short walks help your circulation and recovery. "
        "I also want to remind you that you have a GP appointment with Dr. James Patel in 5 days. "
        "Is there anything else you'd like to share, or any questions you have for your care team?"
    ),
    # Closing
    (
        "Thank you so much for chatting with me today, Margaret. 💙 "
        "I've noted your responses and your care team will review them. "
        "Remember to take your medications, monitor your weight daily, and don't hesitate to "
        "call 000 if you feel chest pain, severe breathlessness, or anything urgent. "
        "I'll check in with you again next week. Take good care! ✅"
    ),
]


class MockLLMClient:
    """Steps through a scripted response list. Cycles when exhausted."""

    def __init__(self, script: list[str] | None = None):
        self._script = script or DEMO_SCRIPT
        self._index = 0

    def chat_completion(self, messages: list[dict], temperature: float = 0.7) -> str:  # noqa: ARG002
        response = self._script[self._index % len(self._script)]
        self._index += 1
        return response

    def reset(self) -> None:
        self._index = 0
