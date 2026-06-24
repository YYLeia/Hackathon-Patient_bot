"""
core/prompt_builder.py
Builds the LLM system prompt + message list from patient context and conversation history.
"""

from __future__ import annotations
from data.models import PatientContext, ConversationMessage

MAX_TOKENS = 8000  # conservative budget


def _estimate_tokens(messages: list[dict]) -> int:
    """Rough token estimate: ~4 chars per token."""
    total = sum(len(m.get("content", "")) for m in messages)
    return total // 4


def build_system_prompt(patient: PatientContext) -> str:
    meds_str = "\n".join(
        f"  - {m.name} {m.dose} {m.frequency} at {', '.join(m.times)} — {m.instructions}"
        for m in patient.medications
    ) or "  None listed."

    appts_str = "\n".join(
        f"  - {a.description} with {a.provider_name} on "
        f"{a.scheduled_dt.strftime('%A %d %B %Y at %I:%M %p')} at {a.location}"
        for a in patient.appointments
    ) or "  None scheduled."

    risk_factors_str = "\n".join(
        f"  - {f.name} (weight {f.weight:.0%})"
        for f in patient.risk_profile.factors
    )

    return f"""You are Dr. Mario, a warm, friendly, and professional AI post-discharge support assistant.
You are conducting a structured weekly wellbeing check-in with a patient who has recently been discharged from hospital.

PATIENT PROFILE:
  Name: {patient.name}
  Age: {patient.age}
  Primary Diagnosis: {patient.primary_diagnosis}
  Discharge Date: {patient.discharge_date.strftime('%d %B %Y')}
  Risk Level: {patient.risk_profile.risk_level} (score {patient.risk_profile.risk_score}/100)

RISK FACTORS:
{risk_factors_str}

CURRENT MEDICATIONS:
{meds_str}

UPCOMING APPOINTMENTS:
{appts_str}

DISCHARGE NOTES:
{patient.discharge_notes}

YOUR ROLE:
- Ask one clear, simple question at a time. Never ask multiple questions in one message.
- Cover these areas in order: general wellbeing, pain level (0–10), medication adherence, mobility, appetite, sleep, emotional state.
- If the patient mentions emergency symptoms (chest pain, can't breathe, collapse, fall), immediately advise them to call 000 and contact their emergency contact.
- Use simple, warm, non-clinical language appropriate for an elderly patient.
- Keep responses concise (2–4 sentences maximum).
- When you have covered all check-in areas, provide a warm closing summary and end the session.
- Do NOT provide medical advice beyond what is in the discharge notes.
- Always refer to the patient by their first name: {patient.name.split()[0]}.

Begin the check-in warmly and ask about their general wellbeing first."""


class PromptBuilder:
    def __init__(self, patient: PatientContext):
        self.patient = patient
        self._system_prompt = build_system_prompt(patient)

    def build(self, conversation_history: list[ConversationMessage]) -> list[dict]:
        messages: list[dict] = [
            {"role": "system", "content": self._system_prompt}
        ]

        for msg in conversation_history:
            if msg.role == "agent":
                messages.append({"role": "assistant", "content": msg.text})
            elif msg.role == "patient":
                messages.append({"role": "user", "content": msg.text})

        # Trim oldest non-system messages if over token budget
        while _estimate_tokens(messages) > MAX_TOKENS and len(messages) > 2:
            messages.pop(1)  # remove oldest non-system message

        return messages
