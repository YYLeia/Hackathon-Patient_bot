"""
data/models.py
All dataclass models for the Post-Discharge Support Agent.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


# ── Risk Models ────────────────────────────────────────────────────────────────

@dataclass
class RiskFactor:
    name: str
    weight: float          # 0.0–1.0
    category: str          # "demographic" | "clinical" | "social"


@dataclass
class RiskProfile:
    risk_score: int                  # 0–100
    risk_level: str                  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    factors: list[RiskFactor]
    last_updated: datetime


# ── Clinical Models ────────────────────────────────────────────────────────────

@dataclass
class Medication:
    medication_id: str
    name: str
    dose: str
    frequency: str
    times: list[str]                 # e.g. ["08:00", "20:00"]
    instructions: str
    refill_date: datetime | None = None
    taken_today: bool = False


@dataclass
class Appointment:
    appointment_id: str
    description: str
    provider_name: str
    scheduled_dt: datetime
    location: str
    what_to_expect: str
    reminder_sent: bool = False


@dataclass
class PatientContext:
    patient_id: str
    name: str
    age: int
    primary_diagnosis: str
    discharge_date: datetime
    risk_profile: RiskProfile
    medications: list[Medication]
    appointments: list[Appointment]
    discharge_notes: str
    language: str = "en"
    device_token: str | None = None


# ── Conversation Models ────────────────────────────────────────────────────────

@dataclass
class RiskIndicator:
    indicator_type: str
    matched_text: str
    confidence: float                # 0.0–1.0
    severity_contribution: str       # "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"


@dataclass
class ConversationMessage:
    message_id: str
    role: str                        # "system"|"agent"|"patient"
    text: str
    timestamp: datetime
    risk_indicators: list[RiskIndicator] = field(default_factory=list)


@dataclass
class ClinicalAlert:
    alert_id: str
    session_id: str
    patient_id: str
    alert_type: str                  # "MEDICATION_MISSED"|"PAIN_ESCALATION"|
                                     # "FALL_RISK"|"MENTAL_HEALTH"|"EMERGENCY"|"GENERAL_CONCERN"
    severity: str                    # "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
    description: str
    evidence: str
    triggered_at: datetime
    acknowledged: bool = False
    acknowledged_by: str | None = None


@dataclass
class CheckInSession:
    session_id: str
    patient_id: str
    started_at: datetime
    ended_at: datetime | None
    status: str                      # "ACTIVE"|"COMPLETE"|"ABANDONED"
    messages: list[ConversationMessage] = field(default_factory=list)
    alerts: list[ClinicalAlert] = field(default_factory=list)
    care_plan_answers: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentTurn:
    session_id: str
    patient_message: ConversationMessage
    agent_message: ConversationMessage
    alerts: list[ClinicalAlert]
    session_status: str


@dataclass
class DischargeSummaryReport:
    report_id: str
    session_id: str
    patient_id: str
    generated_at: datetime
    care_plan_answers: dict[str, str]
    alerts_summary: list[ClinicalAlert]
    conversation_summary: str
    overall_wellbeing_score: int     # 1–10
    recommended_actions: list[str]
    transcript_path: str = ""
