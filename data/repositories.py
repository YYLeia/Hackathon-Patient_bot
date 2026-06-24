"""
data/repositories.py
In-memory repositories for demo. No external DB required.
"""

from __future__ import annotations
from data.models import PatientContext, CheckInSession, ClinicalAlert
from data.mock_patients import ALL_PATIENTS


class PatientNotFoundError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


class PatientRepository:
    def __init__(self, patients: dict[str, PatientContext] | None = None):
        self._store: dict[str, PatientContext] = patients or dict(ALL_PATIENTS)

    def get(self, patient_id: str) -> PatientContext:
        patient = self._store.get(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient '{patient_id}' not found.")
        return patient

    def all(self) -> list[PatientContext]:
        return list(self._store.values())


class SessionRepository:
    def __init__(self):
        self._store: dict[str, CheckInSession] = {}

    def save(self, session: CheckInSession) -> None:
        self._store[session.session_id] = session

    def get(self, session_id: str) -> CheckInSession:
        session = self._store.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session '{session_id}' not found.")
        return session

    def get_active_for_patient(self, patient_id: str) -> CheckInSession | None:
        for s in self._store.values():
            if s.patient_id == patient_id and s.status == "ACTIVE":
                return s
        return None

    def all(self) -> list[CheckInSession]:
        return list(self._store.values())


class AlertRepository:
    def __init__(self):
        self._store: dict[str, ClinicalAlert] = {}

    def save(self, alert: ClinicalAlert) -> None:
        self._store[alert.alert_id] = alert

    def get_for_patient(self, patient_id: str) -> list[ClinicalAlert]:
        return [a for a in self._store.values() if a.patient_id == patient_id]

    def get_unacknowledged(self) -> list[ClinicalAlert]:
        return [a for a in self._store.values() if not a.acknowledged]

    def acknowledge(self, alert_id: str, by: str = "system") -> None:
        if alert_id in self._store:
            self._store[alert_id].acknowledged = True
            self._store[alert_id].acknowledged_by = by

    def all(self) -> list[ClinicalAlert]:
        return list(self._store.values())
