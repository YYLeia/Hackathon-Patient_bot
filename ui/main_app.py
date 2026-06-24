"""
ui/main_app.py
Root Tkinter application — phone-frame shell, frame switching, notification scheduler.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme
from ui.frames.dashboard_frame import PatientDashboardFrame
from ui.frames.chat_frame import CheckInChatFrame
from ui.frames.medications_frame import MedicationScheduleFrame
from ui.frames.appointments_frame import AppointmentsFrame
from ui.frames.risk_profile_frame import RiskProfileFrame
from ui.frames.notification_overlay import NotificationOverlay


class MainApp(tk.Tk):
    def __init__(
        self,
        patient_id: str,
        agent_controller,
        patient_repo,
        alert_repo,
        auto_notify_ms: int = 4000,   # show check-in notification after 4s
    ):
        super().__init__()
        self._agent = agent_controller
        self._patient_repo = patient_repo
        self._alert_repo = alert_repo
        self._patient = patient_repo.get(patient_id)
        self._current_frame = None
        self._session = None

        # Window setup — resizable, phone-style minimum size
        self.title("Dr. Mario — Post-Discharge Check-In")
        self.resizable(True, True)
        self.minsize(theme.APP_WIDTH, theme.APP_HEIGHT)
        self.configure(bg="#2D3748")  # dark outer background = phone body

        # Centre window on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - theme.APP_WIDTH) // 2
        y = max(0, (sh - theme.APP_HEIGHT) // 2 - 30)
        self.geometry(f"{theme.APP_WIDTH}x{theme.APP_HEIGHT}+{x}+{y}")

        # Phone bezel container — expands with window
        self._phone_frame = tk.Frame(self, bg="#2D3748")
        self._phone_frame.pack(fill="both", expand=True)

        # Phone screen area (the actual app content) — fills the window
        self._screen = tk.Frame(self._phone_frame, bg=theme.BG_MAIN)
        self._screen.pack(fill="both", expand=True, padx=0, pady=0)

        # Show dashboard first
        self._show_dashboard()

        # Schedule check-in notification
        self.after(auto_notify_ms, self._fire_checkin_notification)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate(self, destination: str):
        if destination == "dashboard":
            self._show_dashboard()
        elif destination == "chat":
            self._show_chat()
        elif destination == "medications":
            self._show_medications()
        elif destination == "appointments":
            self._show_appointments()
        elif destination == "risk":
            self._show_risk_profile()

    def _clear_screen(self):
        for w in self._screen.winfo_children():
            w.destroy()

    def _show_dashboard(self):
        self._clear_screen()
        frame = PatientDashboardFrame(
            self._screen,
            patient=self._patient,
            on_start_checkin=self._show_chat,
            on_nav=self._navigate,
        )
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

    def _show_chat(self):
        self._clear_screen()
        frame = CheckInChatFrame(
            self._screen,
            controller=self._agent,
            patient=self._patient,
            on_nav=self._navigate,
        )
        frame.pack(fill="both", expand=True)
        self._current_frame = frame
        # Start the session
        frame.start_session(self._patient.patient_id)

    def _show_medications(self):
        self._clear_screen()
        frame = MedicationScheduleFrame(
            self._screen,
            patient=self._patient,
            on_nav=self._navigate,
        )
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

    def _show_appointments(self):
        self._clear_screen()
        frame = AppointmentsFrame(
            self._screen,
            patient=self._patient,
            on_nav=self._navigate,
        )
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

    def _show_risk_profile(self):
        self._clear_screen()
        frame = RiskProfileFrame(
            self._screen,
            patient=self._patient,
            alert_repo=self._alert_repo,
            on_nav=self._navigate,
        )
        frame.pack(fill="both", expand=True)
        self._current_frame = frame

    # ── Notifications ──────────────────────────────────────────────────────────

    def _fire_checkin_notification(self):
        first_name = self._patient.name.split()[0]
        overlay = NotificationOverlay(
            self,
            title="Weekly Check-In 🩺",
            body=f"Hi {first_name}! Dr. Mario is ready for your weekly check-in.",
            on_action=self._show_chat,
            action_label="Start Check-In",
            auto_dismiss_ms=10000,
        )

    def trigger_medication_reminder(self, med):
        NotificationOverlay(
            self,
            title="Medication Reminder 💊",
            body=f"Time to take your {med.name} {med.dose}. {med.instructions}",
            on_action=self._show_medications,
            action_label="View Meds",
            auto_dismiss_ms=12000,
        )
