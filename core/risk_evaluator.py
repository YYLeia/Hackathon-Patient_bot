"""
core/risk_evaluator.py
Evaluates each conversation turn for clinical risk signals.
"""

from __future__ import annotations
import re
import uuid
from datetime import datetime
from data.models import PatientContext, RiskIndicator, ClinicalAlert

# ── Rule Definitions ───────────────────────────────────────────────────────────

EMERGENCY_RULES: list[tuple[str, str, float]] = [
    # (regex_pattern, indicator_type, confidence)
    (r"chest\s*pain|chest\s*tight|can.?t\s*breath|difficulty\s*breath|shortness\s*of\s*breath",
     "EMERGENCY_RESPIRATORY", 0.95),
    (r"i\s*want\s*to\s*die|suicid|kill\s*myself|end\s*my\s*life",
     "MENTAL_HEALTH_CRISIS", 0.98),
    (r"i\s*(had\s*a\s*)?fall|i\s*fell|fallen\s*down|collapsed",
     "EMERGENCY_FALL", 0.90),
    (r"unconscious|unresponsive|not\s*waking|won.?t\s*wake",
     "EMERGENCY_UNRESPONSIVE", 0.97),
    (r"stroke|face\s*drooping|arm\s*weak|speech\s*(slurred|problem)",
     "EMERGENCY_STROKE", 0.95),
]

STANDARD_RULES: list[tuple[str, str, str, float]] = [
    # (regex_pattern, indicator_type, severity, confidence)
    (r"pain.{0,20}([7-9]|10)\s*(out\s*of\s*10|/10)?|([7-9]|10)\s*(out\s*of\s*10|/10)?.{0,10}pain",
     "PAIN_ESCALATION", "HIGH", 0.85),
    (r"pain.{0,20}([4-6])\s*(out\s*of\s*10|/10)?|([4-6])\s*(out\s*of\s*10|/10)?.{0,10}pain",
     "PAIN_MODERATE", "MEDIUM", 0.75),
    (r"didn.?t\s*take|haven.?t\s*taken|forgot.{0,10}(med|pill|tablet|dose)|missed.{0,10}(dose|med|pill)",
     "MEDICATION_MISSED", "MEDIUM", 0.85),
    (r"swelling|swollen|puffy\s*(ankle|leg|feet)|weight\s*(gain|up|increase)",
     "FLUID_RETENTION", "MEDIUM", 0.80),
    (r"confus|disoriented|don.?t\s*know\s*where|can.?t\s*remember",
     "CONFUSION", "MEDIUM", 0.80),
    (r"dizz|lightheaded|feel\s*faint|nearly\s*faint",
     "DIZZINESS", "MEDIUM", 0.75),
    (r"sad|depress|hopeless|no\s*point|crying\s*a\s*lot|very\s*upset",
     "MOOD_CONCERN", "MEDIUM", 0.70),
    (r"haven.?t\s*eaten|not\s*eating|no\s*appetite|can.?t\s*eat",
     "NUTRITION_CONCERN", "LOW", 0.65),
    (r"haven.?t\s*slept|can.?t\s*sleep|very\s*tired|exhausted",
     "SLEEP_CONCERN", "LOW", 0.60),
]

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
ALERT_TYPE_MAP: dict[str, str] = {
    "EMERGENCY_RESPIRATORY": "EMERGENCY",
    "EMERGENCY_FALL": "EMERGENCY",
    "EMERGENCY_UNRESPONSIVE": "EMERGENCY",
    "EMERGENCY_STROKE": "EMERGENCY",
    "MENTAL_HEALTH_CRISIS": "MENTAL_HEALTH",
    "PAIN_ESCALATION": "PAIN_ESCALATION",
    "PAIN_MODERATE": "PAIN_ESCALATION",
    "MEDICATION_MISSED": "MEDICATION_MISSED",
    "FLUID_RETENTION": "GENERAL_CONCERN",
    "CONFUSION": "GENERAL_CONCERN",
    "DIZZINESS": "FALL_RISK",
    "MOOD_CONCERN": "MENTAL_HEALTH",
    "NUTRITION_CONCERN": "GENERAL_CONCERN",
    "SLEEP_CONCERN": "GENERAL_CONCERN",
}


class RiskEvaluator:
    def __init__(self, patient_context: PatientContext):
        self.patient = patient_context

    def evaluate(
        self,
        patient_text: str,
        agent_response: str,
        history: list,  # list[ConversationMessage] — not typed to avoid circular import
    ) -> list[RiskIndicator]:
        indicators: list[RiskIndicator] = []
        combined = (patient_text + " " + agent_response).lower()

        # Pass 1: Emergency rules (short-circuit on first match)
        for pattern, ind_type, confidence in EMERGENCY_RULES:
            m = re.search(pattern, combined)
            if m:
                indicators.append(RiskIndicator(
                    indicator_type=ind_type,
                    matched_text=m.group(0),
                    confidence=confidence,
                    severity_contribution="CRITICAL",
                ))
                return indicators  # emergency: return immediately

        # Pass 2: Standard risk rules
        for pattern, ind_type, severity, confidence in STANDARD_RULES:
            m = re.search(pattern, combined)
            if m:
                indicators.append(RiskIndicator(
                    indicator_type=ind_type,
                    matched_text=m.group(0),
                    confidence=confidence,
                    severity_contribution=severity,
                ))

        # Pass 3: Amplify confidence for high-baseline-risk patients
        if self.patient.risk_profile.risk_level in ("HIGH", "CRITICAL"):
            for ind in indicators:
                ind.confidence = min(1.0, ind.confidence * 1.25)

        return indicators

    def score_severity(self, indicators: list[RiskIndicator]) -> str:
        if not indicators:
            return "LOW"
        return max(indicators, key=lambda i: SEVERITY_ORDER[i.severity_contribution]).severity_contribution

    def to_clinical_alert(
        self,
        indicators: list[RiskIndicator],
        session_id: str,
    ) -> ClinicalAlert | None:
        if not indicators:
            return None
        severity = self.score_severity(indicators)
        if SEVERITY_ORDER[severity] < SEVERITY_ORDER["MEDIUM"]:
            return None
        top = max(indicators, key=lambda i: SEVERITY_ORDER[i.severity_contribution])
        evidence = "; ".join(i.matched_text for i in indicators)
        return ClinicalAlert(
            alert_id=str(uuid.uuid4()),
            session_id=session_id,
            patient_id=self.patient.patient_id,
            alert_type=ALERT_TYPE_MAP.get(top.indicator_type, "GENERAL_CONCERN"),
            severity=severity,
            description=self._describe(top.indicator_type, severity),
            evidence=evidence,
            triggered_at=datetime.now(),
        )

    @staticmethod
    def _describe(indicator_type: str, severity: str) -> str:
        descriptions: dict[str, str] = {
            "EMERGENCY_RESPIRATORY": "Patient reports breathing difficulty — potential emergency.",
            "EMERGENCY_FALL": "Patient reports a fall — assess for injury.",
            "EMERGENCY_UNRESPONSIVE": "Reports of unresponsiveness — emergency response required.",
            "EMERGENCY_STROKE": "Possible stroke symptoms reported.",
            "MENTAL_HEALTH_CRISIS": "Patient expressing suicidal ideation or self-harm intent.",
            "PAIN_ESCALATION": "Patient reporting high pain levels (7–10/10).",
            "PAIN_MODERATE": "Patient reporting moderate pain (4–6/10).",
            "MEDICATION_MISSED": "Patient has missed or forgotten a scheduled medication dose.",
            "FLUID_RETENTION": "Reports of swelling or weight gain — possible fluid retention.",
            "CONFUSION": "Patient appears confused or disoriented.",
            "DIZZINESS": "Patient reports dizziness — fall risk elevated.",
            "MOOD_CONCERN": "Patient expressing low mood or depression.",
            "NUTRITION_CONCERN": "Patient reports not eating — nutrition concern.",
            "SLEEP_CONCERN": "Patient reports sleep disturbance.",
        }
        base = descriptions.get(indicator_type, "Clinical concern detected in check-in.")
        return f"[{severity}] {base}"
