"""
ui/frames/calendar_frame.py
Medication streak calendar — a month grid of adherence that highlights
consecutive (streak) days, plus current/longest streak summary (Req 12).

Adherence history isn't stored on the model, so it is generated
deterministically per patient from the discharge date to today.
"""

from __future__ import annotations
import calendar as _cal
import tkinter as tk
from datetime import date, timedelta

from ui import theme
from ui.widgets import make_rounded_button


# ── Adherence history (deterministic mock) ────────────────────────────────────

def build_adherence(patient) -> dict[date, bool]:
    """Map each day from discharge to today -> True if all meds were taken.

    The most recent week is always taken (a satisfying current streak); earlier
    days are deterministically mostly-taken with the occasional miss so the
    consecutive-day highlighting has some contrast to show.
    """
    start = patient.discharge_date.date()
    today = date.today()
    seed = sum(ord(c) for c in patient.patient_id) + 1

    hist: dict[date, bool] = {}
    d = start
    while d <= today:
        days_ago = (today - d).days
        if days_ago < 7:
            taken = True
        else:
            taken = ((seed * 31 + d.toordinal() * 17) % 4) != 0  # ~1 in 4 missed
        hist[d] = taken
        d += timedelta(days=1)
    return hist


def current_streak(hist: dict[date, bool]) -> int:
    s, d = 0, date.today()
    while hist.get(d):
        s += 1
        d -= timedelta(days=1)
    return s


def longest_streak(hist: dict[date, bool]) -> int:
    best = cur = 0
    for d in sorted(hist):
        cur = cur + 1 if hist[d] else 0
        best = max(best, cur)
    return best


def _is_streak_day(hist: dict[date, bool], d: date) -> bool:
    """A taken day that is adjacent to another taken day (run length >= 2)."""
    return bool(hist.get(d)) and (
        bool(hist.get(d - timedelta(days=1))) or bool(hist.get(d + timedelta(days=1)))
    )


# ── Frame ─────────────────────────────────────────────────────────────────────

class CalendarFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, patient, on_nav):
        super().__init__(parent, bg=theme.BG_MAIN)
        self._patient = patient
        self._on_nav = on_nav
        self._hist = build_adherence(patient)
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
        tk.Label(header, text="🗓️  Medication Streak",
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
        inner = tk.Frame(canvas, bg=theme.BG_MAIN)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        self._build_streak_card(inner)
        self._build_month_grid(inner)
        self._build_legend(inner)
        tk.Frame(inner, bg=theme.BG_MAIN, height=70).pack()

        self._build_nav()

    def _build_streak_card(self, parent):
        cur = current_streak(self._hist)
        best = longest_streak(self._hist)

        card = tk.Frame(parent, bg=theme.ACCENT)
        card.pack(fill="x", padx=theme.PADDING, pady=(14, 8))
        inner = tk.Frame(card, bg=theme.ACCENT)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="🔥", font=("Segoe UI Emoji", 34),
                 bg=theme.ACCENT, fg=theme.TEXT_LIGHT).pack(side="left", padx=(0, 12))

        col = tk.Frame(inner, bg=theme.ACCENT)
        col.pack(side="left", anchor="w")
        tk.Label(col, text=f"{cur} day{'s' if cur != 1 else ''}",
                 font=theme.FONT_HUGE, bg=theme.ACCENT, fg=theme.TEXT_LIGHT
                 ).pack(anchor="w")
        tk.Label(col, text="Current medication streak",
                 font=theme.FONT_SMALL_B, bg=theme.ACCENT, fg=theme.TEXT_LIGHT
                 ).pack(anchor="w")

        tk.Label(card, text=f"🏆  Personal best: {best} days",
                 font=theme.FONT_SMALL_B, bg=theme.ACCENT, fg=theme.TEXT_LIGHT,
                 padx=16).pack(anchor="w", pady=(0, 12))

        msg = ("Amazing! Keep that streak alive! 🎉" if cur >= 7
               else "Great start — take today's meds to grow your streak! 💪" if cur >= 1
               else "Take all your meds today to start a new streak! 🌱")
        tk.Label(parent, text=msg, font=theme.FONT_BODY_B,
                 bg=theme.BG_MAIN, fg=theme.TEAL_DARK,
                 wraplength=330, justify="left").pack(anchor="w", padx=theme.PADDING)

    def _build_month_grid(self, parent):
        today = date.today()
        year, month = today.year, today.month

        tk.Label(parent, text=f"{_cal.month_name[month]} {year}",
                 font=theme.FONT_SUBTITLE, bg=theme.BG_MAIN, fg=theme.TEXT_DARK
                 ).pack(anchor="w", padx=theme.PADDING, pady=(14, 4))

        grid = tk.Frame(parent, bg=theme.BG_MAIN)
        grid.pack(padx=theme.PADDING, anchor="w")

        weekday_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for c, wd in enumerate(weekday_names):
            tk.Label(grid, text=wd, font=theme.FONT_SMALL_B,
                     bg=theme.BG_MAIN, fg=theme.TEXT_MID, width=4
                     ).grid(row=0, column=c, padx=2, pady=2)

        cal = _cal.Calendar(firstweekday=0)  # Monday first
        for r, week in enumerate(cal.monthdayscalendar(year, month), start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Frame(grid, bg=theme.BG_MAIN, width=40, height=40
                             ).grid(row=r, column=c, padx=2, pady=2)
                    continue
                self._build_day_cell(grid, r, c, date(year, month, day), today)

    def _build_day_cell(self, grid, r, c, d: date, today: date):
        # Decide colours from adherence status.
        if d > today:                              # future
            bg, fg = theme.BG_MAIN, theme.TEXT_HINT
        elif d not in self._hist:                  # before discharge (no data)
            bg, fg = "#EEF4F2", theme.TEXT_HINT
        elif not self._hist[d]:                    # missed
            bg, fg = "#FFE0DC", "#C0392B"
        elif _is_streak_day(self._hist, d):        # consecutive streak day → highlight
            bg, fg = theme.TEAL_PRIMARY, theme.TEXT_LIGHT
        else:                                      # isolated taken day
            bg, fg = theme.TEAL_LIGHT, theme.TEAL_DARK

        is_today = (d == today)
        cell = tk.Frame(
            grid, bg=bg, width=40, height=40,
            highlightthickness=3 if is_today else 0,
            highlightbackground=theme.ACCENT, highlightcolor=theme.ACCENT,
        )
        cell.grid(row=r, column=c, padx=2, pady=2)
        cell.grid_propagate(False)
        tk.Label(cell, text=str(d.day),
                 font=theme.FONT_SMALL_B if fg == theme.TEXT_LIGHT else theme.FONT_SMALL,
                 bg=bg, fg=fg).place(relx=0.5, rely=0.5, anchor="center")

    def _build_legend(self, parent):
        legend = tk.Frame(parent, bg=theme.BG_MAIN)
        legend.pack(anchor="w", padx=theme.PADDING, pady=(12, 4))
        items = [
            (theme.TEAL_PRIMARY, "Streak day"),
            (theme.TEAL_LIGHT, "Taken"),
            ("#FFE0DC", "Missed"),
            (theme.ACCENT, "Today"),
        ]
        for color, label in items:
            row = tk.Frame(legend, bg=theme.BG_MAIN)
            row.pack(side="left", padx=(0, 14))
            tk.Frame(row, bg=color, width=14, height=14).pack(side="left", padx=(0, 5))
            tk.Label(row, text=label, font=theme.FONT_SMALL,
                     bg=theme.BG_MAIN, fg=theme.TEXT_MID).pack(side="left")

    # ── Bottom navigation ────────────────────────────────────────────────────

    def _build_nav(self):
        nav = tk.Frame(self, bg=theme.BG_NAV, height=theme.NAV_HEIGHT,
                       highlightbackground=theme.BORDER, highlightthickness=1)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        nav_items = [
            ("🏠", "Home", "dashboard"),
            ("💬", "Check-In", "chat"),
            ("💊", "Meds", "medications"),
            ("🗓️", "Streak", "calendar"),
            ("📅", "Appts", "appointments"),
            ("👤", "Profile", "risk"),
        ]
        for icon, label, key in nav_items:
            is_active = key == "calendar"
            col = theme.TEAL_PRIMARY if is_active else theme.TEXT_HINT
            btn_frame = tk.Frame(nav, bg=theme.BG_NAV, cursor="hand2")
            btn_frame.pack(side="left", expand=True, fill="y")
            icon_lbl = tk.Label(btn_frame, text=icon, font=("Segoe UI Emoji", 17),
                                bg=theme.BG_NAV, fg=col)
            icon_lbl.pack(pady=(6, 0))
            text_lbl = tk.Label(btn_frame, text=label, font=theme.FONT_NAV,
                                bg=theme.BG_NAV, fg=col)
            text_lbl.pack()
            for w in (btn_frame, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._on_nav(k))
