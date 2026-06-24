"""
ui/frames/risk_profile_frame.py
Patient risk profile and clinical summary screen.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme
from ui.widgets import make_risk_badge, RISK_BADGE_COLORS


class RiskProfileFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, patient, alert_repo, on_nav):
        super().__init__(parent, bg=theme.BG_MAIN)
        self._patient = patient
        self._alert_repo = alert_repo
        self._on_nav = on_nav
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=theme.BG_NAV, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        back = tk.Label(header, text="←", font=("Segoe UI", 16),
                        bg=theme.BG_NAV, fg=theme.TEXT_DARK, cursor="hand2")
        back.pack(side="left", padx=16)
        back.bind("<Button-1>", lambda e: self._on_nav("dashboard"))

        tk.Label(header, text="👤  Risk Profile",
                 font=theme.FONT_SUBTITLE, bg=theme.BG_NAV, fg=theme.TEXT_DARK
                 ).pack(side="left", padx=8)

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")

        # Scrollable
        outer = tk.Frame(self, bg=theme.BG_MAIN)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=theme.BG_MAIN, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=theme.BG_MAIN)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        rp = self._patient.risk_profile

        # ── Patient identity card ──────────────────────────────────────────
        id_card = tk.Frame(inner, bg=theme.BG_CARD,
                           highlightbackground=theme.BORDER, highlightthickness=1)
        id_card.pack(fill="x", padx=theme.PADDING, pady=(12, 6))

        id_inner = tk.Frame(id_card, bg=theme.BG_CARD)
        id_inner.pack(fill="x", padx=14, pady=12)

        # Avatar circle
        av_frame = tk.Frame(id_inner, bg=theme.TEAL_LIGHT, width=60, height=60)
        av_frame.pack(side="left", padx=(0, 12))
        av_frame.pack_propagate(False)
        tk.Label(av_frame, text="👴" if self._patient.age >= 65 else "👤",
                 font=("Segoe UI Emoji", 28), bg=theme.TEAL_LIGHT).pack(
            expand=True)

        details = tk.Frame(id_inner, bg=theme.BG_CARD)
        details.pack(side="left", fill="both", expand=True)
        tk.Label(details, text=self._patient.name,
                 font=theme.FONT_BODY_B, bg=theme.BG_CARD, fg=theme.TEXT_DARK,
                 anchor="w").pack(fill="x")
        tk.Label(details,
                 text=f"Age {self._patient.age}  ·  {self._patient.primary_diagnosis}",
                 font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_MID,
                 anchor="w").pack(fill="x")
        tk.Label(details,
                 text=f"Language: {self._patient.language.upper()}",
                 font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_MID,
                 anchor="w").pack(fill="x")

        # ── Risk score gauge ──────────────────────────────────────────────
        score_frame = tk.Frame(inner, bg=theme.BG_CARD,
                               highlightbackground=theme.BORDER, highlightthickness=1)
        score_frame.pack(fill="x", padx=theme.PADDING, pady=6)
        score_inner = tk.Frame(score_frame, bg=theme.BG_CARD)
        score_inner.pack(fill="x", padx=14, pady=12)

        tk.Label(score_inner, text="Overall Risk Score",
                 font=theme.FONT_BODY_B, bg=theme.BG_CARD, fg=theme.TEXT_DARK).pack(anchor="w")

        gauge_frame = tk.Frame(score_inner, bg=theme.BG_CARD)
        gauge_frame.pack(fill="x", pady=6)

        # Score bar
        bar_bg = tk.Frame(gauge_frame, bg=theme.BORDER, height=16)
        bar_bg.pack(fill="x", pady=4)
        bar_bg.pack_propagate(False)
        bar_fill_w = max(10, int(3.4 * rp.risk_score))  # scale to ~340px
        fg, bg = RISK_BADGE_COLORS.get(rp.risk_level, ("#333", "#eee"))
        bar_fill = tk.Frame(bar_bg, bg=fg, width=bar_fill_w, height=16)
        bar_fill.place(x=0, y=0)

        tk.Label(gauge_frame,
                 text=f"{rp.risk_score} / 100  —  {rp.risk_level}",
                 font=theme.FONT_BODY_B, bg=theme.BG_CARD, fg=fg).pack(anchor="w")
        tk.Label(gauge_frame,
                 text=f"Last updated: {rp.last_updated.strftime('%d %b %Y')}",
                 font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_HINT).pack(anchor="w")

        # ── Risk factors ──────────────────────────────────────────────────
        tk.Label(inner, text="Contributing Risk Factors",
                 font=theme.FONT_SUBTITLE, bg=theme.BG_MAIN, fg=theme.TEXT_DARK
                 ).pack(anchor="w", padx=theme.PADDING, pady=(12, 4))

        CATEGORY_ICONS = {"demographic": "👤", "clinical": "🏥", "social": "🏠"}
        for factor in sorted(rp.factors, key=lambda f: -f.weight):
            row = tk.Frame(inner, bg=theme.BG_CARD,
                           highlightbackground=theme.BORDER, highlightthickness=1)
            row.pack(fill="x", padx=theme.PADDING, pady=3)
            icon = CATEGORY_ICONS.get(factor.category, "•")
            tk.Label(row, text=icon, font=("Segoe UI Emoji", 14),
                     bg=theme.BG_CARD).pack(side="left", padx=(10, 6), pady=8)
            tk.Label(row, text=factor.name, font=theme.FONT_SMALL_B,
                     bg=theme.BG_CARD, fg=theme.TEXT_DARK).pack(side="left")
            weight_pct = f"{factor.weight:.0%}"
            wt_color = fg if factor.weight >= 0.3 else theme.TEXT_MID
            tk.Label(row, text=f"  {weight_pct} weight",
                     font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=wt_color).pack(side="left")
            tk.Label(row, text=factor.category.title(),
                     font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_HINT
                     ).pack(side="right", padx=10)

        # ── Active alerts ─────────────────────────────────────────────────
        alerts = self._alert_repo.get_for_patient(self._patient.patient_id)
        if alerts:
            tk.Label(inner, text="Clinical Alerts",
                     font=theme.FONT_SUBTITLE, bg=theme.BG_MAIN, fg=theme.TEXT_DARK
                     ).pack(anchor="w", padx=theme.PADDING, pady=(12, 4))

            from ui.widgets import make_alert_banner
            for alert in sorted(alerts, key=lambda a: a.triggered_at, reverse=True):
                make_alert_banner(inner, alert)

        tk.Frame(inner, bg=theme.BG_MAIN, height=60).pack()
        self._build_nav()

    def _build_nav(self):
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
            is_active = key == "risk"
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
