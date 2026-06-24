"""
ui/frames/medications_frame.py
Medication schedule screen — cards with mark-as-taken functionality.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme
from ui.widgets import make_med_card


class MedicationScheduleFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, patient, on_nav):
        super().__init__(parent, bg=theme.BG_MAIN)
        self._patient = patient
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

        tk.Label(header, text="💊  Medications",
                 font=theme.FONT_SUBTITLE, bg=theme.BG_NAV, fg=theme.TEXT_DARK
                 ).pack(side="left", padx=8)

        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")

        # Scrollable content
        outer = tk.Frame(self, bg=theme.BG_MAIN)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=theme.BG_MAIN, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=theme.BG_MAIN)
        win_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        # Info banner
        info = tk.Frame(self._inner, bg=theme.TEAL_LIGHT)
        info.pack(fill="x", padx=theme.PADDING, pady=(12, 4))
        tk.Label(
            info,
            text="💡  Mark each medication as taken to help your care team track your adherence.",
            font=theme.FONT_SMALL, bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
            wraplength=330, justify="left", padx=10, pady=8,
        ).pack(anchor="w")

        # Title
        tk.Label(
            self._inner, text="Today's Medications",
            font=theme.FONT_SUBTITLE, bg=theme.BG_MAIN, fg=theme.TEXT_DARK,
        ).pack(anchor="w", padx=theme.PADDING, pady=(12, 4))

        for med in self._patient.medications:
            make_med_card(self._inner, med, self._on_mark_taken)

        tk.Frame(self._inner, bg=theme.BG_MAIN, height=60).pack()

        # Nav bar
        self._build_nav()

    def _on_mark_taken(self, med):
        med.taken_today = not med.taken_today
        # Rebuild the whole frame (clear ALL children) so the header and nav bar
        # aren't duplicated on top of the existing ones.
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

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
            is_active = key == "medications"
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
