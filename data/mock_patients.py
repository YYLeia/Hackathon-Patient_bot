"""
data/mock_patients.py
Demo patient data — no real PHI. Fully synthetic.
"""

from datetime import datetime, timedelta
from data.models import (
    PatientContext, RiskProfile, RiskFactor, Medication, Appointment
)

# ── Demo Patient: Margaret Thompson ───────────────────────────────────────────

DEMO_PATIENT = PatientContext(
    patient_id="PATIENT_001",
    name="Margaret Thompson",
    age=78,
    primary_diagnosis="Heart Failure (NYHA Class II)",
    discharge_date=datetime.now() - timedelta(days=3),
    risk_profile=RiskProfile(
        risk_score=72,
        risk_level="HIGH",
        factors=[
            RiskFactor("Age > 75",                        weight=0.30, category="demographic"),
            RiskFactor("Heart Failure diagnosis",          weight=0.40, category="clinical"),
            RiskFactor("Lives alone",                      weight=0.20, category="social"),
            RiskFactor("Prior readmission within 90 days", weight=0.10, category="clinical"),
        ],
        last_updated=datetime.now() - timedelta(days=3),
    ),
    medications=[
        Medication(
            medication_id="MED_001",
            name="Furosemide",
            dose="40mg",
            frequency="once daily",
            times=["08:00"],
            instructions="Take in the morning. Monitor for dizziness when standing.",
        ),
        Medication(
            medication_id="MED_002",
            name="Metformin",
            dose="500mg",
            frequency="twice daily",
            times=["08:00", "18:00"],
            instructions="Take with meals to reduce stomach upset.",
        ),
        Medication(
            medication_id="MED_003",
            name="Lisinopril",
            dose="5mg",
            frequency="once daily",
            times=["08:00"],
            instructions="Take at the same time each day. Avoid potassium supplements.",
        ),
    ],
    appointments=[
        Appointment(
            appointment_id="APPT_001",
            description="Cardiology Follow-Up",
            provider_name="Dr. Sarah Chen",
            scheduled_dt=datetime.now() + timedelta(days=11),
            location="St. George Hospital — Cardiology Dept, Level 3",
            what_to_expect=(
                "Weight check, ECG, and medication review. "
                "Bring your current medication list and any symptom diary. "
                "Allow 1–2 hours for the appointment."
            ),
        ),
        Appointment(
            appointment_id="APPT_002",
            description="GP Review",
            provider_name="Dr. James Patel",
            scheduled_dt=datetime.now() + timedelta(days=5),
            location="Eastside Family Practice — 12 Brown St",
            what_to_expect=(
                "Blood pressure check, review of discharge medications, "
                "and general wellbeing discussion. Fasting blood test may be requested."
            ),
        ),
    ],
    discharge_notes=(
        "Patient discharged after 4-day admission for decompensated heart failure. "
        "Fluid overload resolved with IV Furosemide. Blood pressure stable at 128/78 at discharge. "
        "Advise daily weight monitoring — return to ED if weight gain > 2kg in 2 days. "
        "Diet: low sodium (<2g/day). Activity: gentle walking as tolerated. "
        "Follow up with cardiology in 2 weeks and GP within 1 week."
    ),
)

# ── Additional Demo Patient: Robert Kim ───────────────────────────────────────

PATIENT_002 = PatientContext(
    patient_id="PATIENT_002",
    name="Robert Kim",
    age=82,
    primary_diagnosis="Hip Replacement (Right)",
    discharge_date=datetime.now() - timedelta(days=5),
    risk_profile=RiskProfile(
        risk_score=58,
        risk_level="HIGH",
        factors=[
            RiskFactor("Age > 80",             weight=0.35, category="demographic"),
            RiskFactor("Post-surgical",         weight=0.35, category="clinical"),
            RiskFactor("Mobility impairment",   weight=0.20, category="clinical"),
            RiskFactor("Family carer present",  weight=-0.10, category="social"),
        ],
        last_updated=datetime.now() - timedelta(days=5),
    ),
    medications=[
        Medication(
            medication_id="MED_010",
            name="Oxycodone",
            dose="5mg",
            frequency="every 6 hours as needed",
            times=["06:00", "12:00", "18:00", "00:00"],
            instructions="Take only if pain is 5 or above. Do not drive.",
        ),
        Medication(
            medication_id="MED_011",
            name="Enoxaparin",
            dose="40mg",
            frequency="once daily",
            times=["20:00"],
            instructions="Subcutaneous injection. Rotate injection sites.",
        ),
    ],
    appointments=[
        Appointment(
            appointment_id="APPT_010",
            description="Orthopaedic Post-Op Review",
            provider_name="Dr. Lena Torres",
            scheduled_dt=datetime.now() + timedelta(days=9),
            location="City Orthopaedic Clinic — 5 Park Ave",
            what_to_expect=(
                "Wound inspection, X-ray of hip, and physiotherapy assessment. "
                "Wear loose-fitting shorts. Bring walking aid."
            ),
        ),
    ],
    discharge_notes=(
        "Right total hip arthroplasty performed without complication. "
        "Patient ambulatory with frame at discharge. "
        "DVT prophylaxis with Enoxaparin for 35 days. "
        "Weight-bearing as tolerated. Physio twice weekly commencing Day 7. "
        "Report any increased redness, warmth, or discharge at wound site immediately."
    ),
)

ALL_PATIENTS: dict[str, PatientContext] = {
    DEMO_PATIENT.patient_id: DEMO_PATIENT,
    PATIENT_002.patient_id: PATIENT_002,
}
