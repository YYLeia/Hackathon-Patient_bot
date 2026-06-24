"""
ui/frames/dashboard_frame.py
Landing screen — Doctor Mario welcome, patient name, quick-reply chips, navigation.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme
from ui.widgets import make_risk_badge, make_appt_card
from ui.doctor_mario import create_doctor_mario_canvas


class PatientDashboardFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, patient, on_start_checkin, on_nav):
        super().__init__(parent, bg=theme.BG_MAIN)
        self._patient = patient
        self._on_start_checkin = on_start_checkin
        self._on_nav = on_nav
        self._build_ui()

    def _build_ui(self):
        # ── Status bar ──────────────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=theme.BG_MAIN, height=theme.STATUS_HEIGHT)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar, text="9:41", font=theme.FONT_SMALL_B,
            bg=theme.BG_MAIN, fg=theme.TEXT_DARK,
        ).pack(side="left", padx=16, pady=10)
        tk.Label(
            status_bar, text="▲ ▼ 🔋", font=theme.FONT_SMALL,
            bg=theme.BG_MAIN, fg=theme.TEXT_MID,
        ).pack(side="right", padx=16)

        # ── Scrollable content ───────────────────────────────────────────────
        outer = tk.Frame(self, bg=theme.BG_MAIN)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=theme.BG_MAIN, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=theme.BG_MAIN)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ── Doctor Mario avatar + greeting ────────────────────────────────────
        mario_canvas = create_doctor_mario_canvas(inner, width=240, height=210, scale=0.9)
        mario_canvas.pack(pady=(16, 0))

        first_name = self._patient.name.split()[0]
        tk.Label(
            inner,
            text=f"Hey, {first_name}! 👋",
            font=theme.FONT_HUGE,
            bg=theme.BG_MAIN, fg=theme.TEXT_DARK,
        ).pack(pady=(8, 2))

        tk.Label(
            inner,
            text="How can I help you with\nyour health today?",
            font=theme.FONT_SUBTITLE,
            bg=theme.BG_MAIN, fg=theme.TEXT_MID,
            justify="center",
        ).pack(pady=(0, 8))

        # ── Risk badge ────────────────────────────────────────────────────────
        risk_frame = tk.Frame(inner, bg=theme.BG_MAIN)
        risk_frame.pack(pady=4)
        badge = make_risk_badge(
            risk_frame,
            self._patient.risk_profile.risk_level,
            self._patient.risk_profile.risk_score,
        )
        badge.pack()

        # ── Quick symptom chips ───────────────────────────────────────────────
        tk.Frame(inner, bg=theme.BORDER, height=1).pack(fill="x",
                                                          padx=theme.PADDING, pady=12)

        chips_label = tk.Label(
            inner, text="Quick check-in topics:",
            font=theme.FONT_SMALL_B, bg=theme.BG_MAIN, fg=theme.TEXT_MID,
        )
        chips_label.pack(anchor="w", padx=theme.PADDING)

        chip_data = [
            ("Pain", "🔴"), ("Medications", "💊"), ("Breathlessness", "💨"),
            ("Mobility", "🚶"), ("Swelling", "💧"), ("Mood", "💬"),
        ]
        row1 = tk.Frame(inner, bg=theme.BG_MAIN)
        row1.pack(pady=4, padx=theme.PADDING, anchor="w")
        row2 = tk.Frame(inner, bg=theme.BG_MAIN)
        row2.pack(pady=4, padx=theme.PADDING, anchor="w")

        for i, (label, icon) in enumerate(chip_data):
            row = row1 if i < 3 else row2
            btn = tk.Button(
                row, text=f"{icon}  {label}",
                font=theme.FONT_SMALL_B,
                bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
                activebackground=theme.TEAL_PRIMARY, activeforeground=theme.TEXT_LIGHT,
                bd=0, padx=10, pady=6, relief="flat", cursor="hand2",
                command=self._on_start_checkin,
            )
            btn.pack(side="left", padx=4)

        # ── START CHECK-IN button ─────────────────────────────────────────────
        tk.Frame(inner, bg=theme.BORDER, height=1).pack(fill="x",
                                                          padx=theme.PADDING, pady=12)

        start_btn = tk.Button(
            inner,
            text="▶  Start Weekly Check-In",
            font=theme.FONT_BODY_B,
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_DARK, activeforeground=theme.TEXT_LIGHT,
            bd=0, padx=20, pady=14, relief="flat", cursor="hand2",
            command=self._on_start_checkin,
        )
        start_btn.pack(pady=4, padx=theme.PADDING, fill="x")

        # ── Upcoming appointments preview ─────────────────────────────────────
        if self._patient.appointments:
            tk.Label(
                inner, text="Upcoming Appointments",
                font=theme.FONT_SUBTITLE, bg=theme.BG_MAIN, fg=theme.TEXT_DARK,
            ).pack(anchor="w", padx=theme.PADDING, pady=(16, 4))

            for appt in self._patient.appointments[:2]:
                make_appt_card(inner, appt)

        # ── Discharge info snippet ────────────────────────────────────────────
        from datetime import datetime
        days_since = (datetime.now() - self._patient.discharge_date).days
        info_frame = tk.Frame(inner, bg=theme.TEAL_LIGHT, bd=0)
        info_frame.pack(fill="x", padx=theme.PADDING, pady=12)
        tk.Label(
            info_frame,
            text=f"🏥  Discharged {days_since} day{'s' if days_since != 1 else ''} ago · "
                 f"{self._patient.primary_diagnosis}",
            font=theme.FONT_SMALL_B, bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
            wraplength=330, justify="left", padx=12, pady=10,
        ).pack(anchor="w")

        # bottom padding
        tk.Frame(inner, bg=theme.BG_MAIN, height=80).pack()

        # ── Bottom navigation bar ─────────────────────────────────────────────
        self._build_nav_bar()

    def _build_nav_bar(self):
        nav = tk.Frame(self, bg=theme.BG_NAV, height=theme.NAV_HEIGHT,
                       highlightbackground=theme.BORDER, highlightthickness=1)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        nav_items = [
            ("🏠", "Home", "dashboard"),
            ("💬", "Check-In", "chat"),
            ("💊", "Meds", "medications"),
            ("📅", "Appointments", "appointments"),
            ("👤", "Profile", "risk"),
        ]
        for icon, label, key in nav_items:
            is_active = key == "dashboard"
            col = theme.TEAL_PRIMARY if is_active else theme.TEXT_HINT
            btn_frame = tk.Frame(nav, bg=theme.BG_NAV, cursor="hand2")
            btn_frame.pack(side="left", expand=True, fill="y")
            icon_lbl = tk.Label(btn_frame, text=icon, font=("Segoe UI Emoji", 18),
                                bg=theme.BG_NAV, fg=col)
            icon_lbl.pack(pady=(6, 0))
            text_lbl = tk.Label(btn_frame, text=label, font=theme.FONT_NAV,
                                bg=theme.BG_NAV, fg=col)
            text_lbl.pack()
            # Bind the click to the frame AND its child labels — in Tk a click
            # on a child Label does not propagate up to the parent Frame.
            for w in (btn_frame, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._on_nav(k))
