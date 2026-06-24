"""
core/agent_controller.py
Orchestrates check-in sessions: start, send messages, finalise.
"""

from __future__ import annotations
import uuid
from datetime import datetime

from data.models import (
    CheckInSession, ConversationMessage, AgentTurn, DischargeSummaryReport
)
from data.repositories import PatientRepository, SessionRepository, AlertRepository
from core.llm_client import LLMClient
from core.risk_evaluator import RiskEvaluator
from core.prompt_builder import PromptBuilder
from core.report_generator import ReportGenerator


# Phrases that indicate the agent has closed the session
_COMPLETION_SIGNALS = (
    "take good care",
    "check in with you again",
    "take care of yourself",
    "goodbye",
    "end of our check-in",
    "session is now complete",
)


class ActiveSessionError(Exception):
    pass


class AgentController:
    def __init__(
        self,
        llm: LLMClient,
        patient_repo: PatientRepository,
        session_repo: SessionRepository,
        alert_repo: AlertRepository,
    ):
        self._llm = llm
        self._patient_repo = patient_repo
        self._session_repo = session_repo
        self._alert_repo = alert_repo
        self._prompt_builders: dict[str, PromptBuilder] = {}
        self._risk_evaluators: dict[str, RiskEvaluator] = {}
        self._report_gen = ReportGenerator(self._llm)

    # ── Session Lifecycle ──────────────────────────────────────────────────────

    def start_session(self, patient_id: str) -> CheckInSession:
        # Enforce no duplicate active sessions
        existing = self._session_repo.get_active_for_patient(patient_id)
        if existing:
            return existing  # resume existing session

        patient = self._patient_repo.get(patient_id)
        session_id = str(uuid.uuid4())

        pb = PromptBuilder(patient)
        re_ = RiskEvaluator(patient)
        self._prompt_builders[session_id] = pb
        self._risk_evaluators[session_id] = re_

        # Get opening message from LLM
        opening_text = self._llm.chat_completion(
            pb.build([]), temperature=0.7
        )

        opening_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            role="agent",
            text=opening_text,
            timestamp=datetime.now(),
        )

        session = CheckInSession(
            session_id=session_id,
            patient_id=patient_id,
            started_at=datetime.now(),
            ended_at=None,
            status="ACTIVE",
            messages=[opening_msg],
        )
        self._session_repo.save(session)
        return session

    def send_message(self, session_id: str, patient_text: str) -> AgentTurn:
        session = self._session_repo.get(session_id)
        patient = self._patient_repo.get(session.patient_id)

        # Lazy-init builders if app was restarted mid-session
        if session_id not in self._prompt_builders:
            self._prompt_builders[session_id] = PromptBuilder(patient)
            self._risk_evaluators[session_id] = RiskEvaluator(patient)

        pb = self._prompt_builders[session_id]
        re_ = self._risk_evaluators[session_id]

        # Record patient message
        patient_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            role="patient",
            text=patient_text,
            timestamp=datetime.now(),
        )
        session.messages.append(patient_msg)

        # Build messages list and call LLM
        messages = pb.build(session.messages)
        agent_text = self._llm.chat_completion(messages, temperature=0.7)

        agent_msg = ConversationMessage(
            message_id=str(uuid.uuid4()),
            role="agent",
            text=agent_text,
            timestamp=datetime.now(),
        )
        session.messages.append(agent_msg)

        # Risk evaluation
        indicators = re_.evaluate(patient_text, agent_text, session.messages)
        alerts = []
        if indicators:
            alert = re_.to_clinical_alert(indicators, session_id)
            if alert:
                self._alert_repo.save(alert)
                session.alerts.append(alert)
                alerts.append(alert)

        # Check for session completion signal
        if any(sig in agent_text.lower() for sig in _COMPLETION_SIGNALS):
            session.status = "COMPLETE"
            session.ended_at = datetime.now()

        self._session_repo.save(session)

        return AgentTurn(
            session_id=session_id,
            patient_message=patient_msg,
            agent_message=agent_msg,
            alerts=alerts,
            session_status=session.status,
        )

    def finalize_session(self, session_id: str) -> DischargeSummaryReport:
        session = self._session_repo.get(session_id)
        patient = self._patient_repo.get(session.patient_id)

        if session.status != "COMPLETE":
            session.status = "COMPLETE"
            session.ended_at = datetime.now()
            self._session_repo.save(session)

        return self._report_gen.generate_report(session, patient)
