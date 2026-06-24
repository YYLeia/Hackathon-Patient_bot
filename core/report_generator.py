"""
core/report_generator.py
Converts a completed CheckInSession into a DischargeSummaryReport + exported files.
"""

from __future__ import annotations
import os
import uuid
import re
from datetime import datetime
from data.models import (
    CheckInSession, PatientContext, DischargeSummaryReport, ClinicalAlert
)

CARE_PLAN_QUESTIONS = [
    # (key, regex to detect in patient text, extraction hint)
    ("pain_level",      r"(\d+)\s*(out\s*of\s*10|/10)",             "numeric pain score"),
    ("mobility",        r"walk(ed|ing)|mov(ed|ing)|exercise|steps",  "mobility mention"),
    ("medication_taken", r"took|taken|taking|yes.{0,20}(med|pill)",  "medication adherence"),
    ("appetite",        r"eat(ing|en)|food|meal|appetite|hungry",    "appetite/nutrition"),
    ("mood",            r"feel(ing)?|mood|emotion|happy|sad|anxious|worry", "mood/emotion"),
    ("sleep",           r"sleep|slept|rest|tired|exhausted|insomnia",        "sleep quality"),
    ("swelling",        r"swell(ing|en)|puffy|ankle|legs?\s+look",           "fluid/swelling"),
]

ALERT_ACTION_MAP: dict[str, str] = {
    "EMERGENCY":        "URGENT: Contact patient immediately and escalate to emergency services.",
    "PAIN_ESCALATION":  "Review pain management — consider GP or specialist contact.",
    "MEDICATION_MISSED": "Follow up on medication adherence — pharmacist or nurse review.",
    "FALL_RISK":        "Assess fall risk — physio or OT referral recommended.",
    "MENTAL_HEALTH":    "Mental health follow-up — psychology or GP referral.",
    "GENERAL_CONCERN":  "Review with care team at next available opportunity.",
}


class ReportGenerator:
    def __init__(self, llm):
        self._llm = llm

    def generate_report(
        self, session: CheckInSession, patient: PatientContext
    ) -> DischargeSummaryReport:
        # 1. Extract structured care-plan answers from patient messages
        care_plan_answers: dict[str, str] = {}
        for msg in session.messages:
            if msg.role != "patient":
                continue
            text_lower = msg.text.lower()
            for key, pattern, _ in CARE_PLAN_QUESTIONS:
                if key not in care_plan_answers and re.search(pattern, text_lower):
                    care_plan_answers[key] = msg.text[:200]

        # 2. Compute wellbeing score (1–10)
        score = 7
        if "pain_level" in care_plan_answers:
            m = re.search(r"(\d+)", care_plan_answers["pain_level"])
            if m:
                pain = int(m.group(1))
                score -= pain // 3
        critical_alerts = [a for a in session.alerts if a.severity == "CRITICAL"]
        high_alerts = [a for a in session.alerts if a.severity == "HIGH"]
        score -= len(critical_alerts) * 2
        score -= len(high_alerts) * 1
        score = max(1, min(10, score))

        # 3. Generate LLM summary (short prompt, low temperature)
        summary_prompt = self._build_summary_prompt(session, patient)
        try:
            summary = self._llm.chat_completion(summary_prompt, temperature=0.3)
        except Exception:
            summary = "Summary unavailable — manual review of transcript required."

        # 4. Build recommended actions
        seen_types: set[str] = set()
        actions: list[str] = []
        for alert in session.alerts:
            if alert.severity in ("HIGH", "CRITICAL") and alert.alert_type not in seen_types:
                action = ALERT_ACTION_MAP.get(alert.alert_type, ALERT_ACTION_MAP["GENERAL_CONCERN"])
                actions.append(action)
                seen_types.add(alert.alert_type)

        return DischargeSummaryReport(
            report_id=str(uuid.uuid4()),
            session_id=session.session_id,
            patient_id=session.patient_id,
            generated_at=datetime.now(),
            care_plan_answers=care_plan_answers,
            alerts_summary=list(session.alerts),
            conversation_summary=summary,
            overall_wellbeing_score=score,
            recommended_actions=actions,
        )

    def export_transcript(self, session: CheckInSession, output_path: str) -> str:
        patient_name = "Patient"  # avoid loading repo here; caller can pass name
        lines = [
            "=" * 60,
            "POST-DISCHARGE CHECK-IN TRANSCRIPT",
            f"Session ID : {session.session_id}",
            f"Patient ID : {session.patient_id}",
            f"Started    : {session.started_at.strftime('%d %b %Y %H:%M:%S')}",
            f"Ended      : {session.ended_at.strftime('%d %b %Y %H:%M:%S') if session.ended_at else 'In Progress'}",
            f"Status     : {session.status}",
            "=" * 60,
            "",
        ]
        for msg in session.messages:
            if msg.role == "system":
                continue
            role_label = "Dr. Mario" if msg.role == "agent" else "Patient"
            lines.append(f"[{msg.timestamp.strftime('%H:%M:%S')}] {role_label}:")
            lines.append(f"  {msg.text}")
            lines.append("")

        lines += [
            "=" * 60,
            f"ALERTS RAISED: {len(session.alerts)}",
        ]
        for alert in session.alerts:
            lines.append(f"  [{alert.severity}] {alert.alert_type}: {alert.description}")
            lines.append(f"    Evidence: {alert.evidence}")

        content = "\n".join(lines)
        abs_path = os.path.abspath(output_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return abs_path

    def export_clinical_report(
        self, report: DischargeSummaryReport, output_path: str
    ) -> str:
        lines = [
            "=" * 60,
            "CLINICAL DISCHARGE SUMMARY REPORT",
            f"Report ID    : {report.report_id}",
            f"Session ID   : {report.session_id}",
            f"Patient ID   : {report.patient_id}",
            f"Generated    : {report.generated_at.strftime('%d %b %Y %H:%M:%S')}",
            f"Wellbeing    : {report.overall_wellbeing_score}/10",
            "=" * 60,
            "",
            "CARE PLAN ANSWERS:",
        ]
        if report.care_plan_answers:
            for key, val in report.care_plan_answers.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {val}")
        else:
            lines.append("  No structured answers extracted.")

        lines += [
            "",
            "CONVERSATION SUMMARY:",
            f"  {report.conversation_summary}",
            "",
            f"ALERTS ({len(report.alerts_summary)}):",
        ]
        for alert in report.alerts_summary:
            lines.append(f"  [{alert.severity}] {alert.alert_type}")
            lines.append(f"    {alert.description}")
            lines.append(f"    Evidence: \"{alert.evidence}\"")
            lines.append(f"    Time: {alert.triggered_at.strftime('%H:%M:%S')}")

        lines += [
            "",
            "RECOMMENDED ACTIONS:",
        ]
        if report.recommended_actions:
            for action in report.recommended_actions:
                lines.append(f"  • {action}")
        else:
            lines.append("  No high-priority actions required.")

        lines.append("\n" + "=" * 60)
        content = "\n".join(lines)
        abs_path = os.path.abspath(output_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return abs_path

    @staticmethod
    def _build_summary_prompt(session: CheckInSession, patient: PatientContext) -> list[dict]:
        patient_msgs = [m.text for m in session.messages if m.role == "patient"]
        conversation_text = "\n".join(f"Patient: {t}" for t in patient_msgs)
        alert_text = "\n".join(f"- [{a.severity}] {a.description}" for a in session.alerts)
        return [
            {
                "role": "system",
                "content": (
                    "You are a clinical documentation assistant. "
                    "Write a concise 2–3 sentence clinical summary of this patient check-in. "
                    "Focus on clinical findings, concerns, and any actions required. "
                    "Be objective and factual."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Patient: {patient.name}, {patient.age}yo, {patient.primary_diagnosis}\n"
                    f"Discharge: {patient.discharge_date.strftime('%d %b %Y')}\n\n"
                    f"Patient responses:\n{conversation_text}\n\n"
                    f"Alerts raised:\n{alert_text or 'None'}"
                ),
            },
        ]
