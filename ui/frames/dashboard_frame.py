"""
ui/frames/dashboard_frame.py
Landing screen — Doctor Mario welcome, patient name, quick-reply chips, navigation.
"""

from __future__ import annotations
import math
import os
import tkinter as tk
import tkinter.font as tkfont
from ui import theme
from ui import i18n
from ui.widgets import make_risk_badge, make_appt_card, make_rounded_button
from ui.doctor_mario import create_doctor_mario_canvas

# Optional custom mascot image — drop a PNG here to replace the drawn Dr. Mario.
_MASCOT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "dr_mario.png")


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

        # Language / translate selector (top-right)
        self._build_language_selector(status_bar)

        tk.Label(
            status_bar, text="▲ ▼ 🔋", font=theme.FONT_SMALL,
            bg=theme.BG_MAIN, fg=theme.TEXT_MID,
        ).pack(side="right", padx=(16, 8))

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
        # Prefer a custom mascot image if present; otherwise use the drawn one.
        # Any previous bounce loop must be cancelled before a rebuild.
        if getattr(self, "_mascot_after", None):
            try:
                self.after_cancel(self._mascot_after)
            except Exception:
                pass
            self._mascot_after = None

        self._mascot_img = self._load_mascot_image(max_w=230, max_h=240)
        if self._mascot_img is not None:
            # Float/bounce the image inside a fixed-height holder so the layout
            # below it stays put while the mascot gently hovers.
            self._bounce_amp = 9
            top_pad = 6
            holder = tk.Frame(
                inner, bg=theme.BG_MAIN,
                width=self._mascot_img.width(),
                height=self._mascot_img.height() + self._bounce_amp * 2 + top_pad * 2,
            )
            holder.pack(pady=(12, 0))
            holder.pack_propagate(False)
            self._mascot_label = tk.Label(holder, image=self._mascot_img, bg=theme.BG_MAIN)
            self._mascot_base_y = top_pad + self._bounce_amp
            self._mascot_label.place(relx=0.5, y=self._mascot_base_y, anchor="n")
            self._bounce_phase = 0.0
            self._animate_mascot()
        else:
            mario_canvas = create_doctor_mario_canvas(inner, width=240, height=210, scale=0.9)
            mario_canvas.pack(pady=(16, 0))

        first_name = self._patient.name.split()[0]
        tk.Label(
            inner,
            text=i18n.t("greeting", name=first_name),
            font=theme.FONT_HUGE,
            bg=theme.BG_MAIN, fg=theme.TEXT_DARK,
        ).pack(pady=(8, 2))

        tk.Label(
            inner,
            text=i18n.t("subtitle"),
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
            inner, text=i18n.t("quick_topics"),
            font=theme.FONT_SMALL_B, bg=theme.BG_MAIN, fg=theme.TEXT_MID,
        )
        chips_label.pack(anchor="w", padx=theme.PADDING)

        chip_data = [
            ("pain", "🔴"), ("medications", "💊"), ("breathlessness", "💨"),
            ("mobility", "🚶"), ("swelling", "💧"), ("mood", "💬"),
        ]

        # Uniform chip width keeps the wrapped grid tidy at any window size.
        _f = theme.FONT_SMALL_B
        cf = tkfont.Font(family=_f[0], size=_f[1],
                         weight=(_f[2] if len(_f) > 2 else "normal"))
        chip_pad = 14
        self._chip_w = max(
            cf.measure(f"{icon}  {i18n.t(key)}") for key, icon in chip_data
        ) + chip_pad * 2

        chips_container = tk.Frame(inner, bg=theme.BG_MAIN)
        chips_container.pack(fill="x", padx=theme.PADDING, pady=4)
        self._chips_container = chips_container

        self._chip_buttons = []
        for key, icon in chip_data:
            btn = make_rounded_button(
                chips_container, f"{icon}  {i18n.t(key)}", self._on_start_checkin,
                bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
                hover_bg=theme.TEAL_DARK,
                font=theme.FONT_SMALL_B, padx=chip_pad, pady=8, radius=18,
                min_width=self._chip_w,
            )
            self._chip_buttons.append(btn)

        # Reflow chips into as many columns as the current width allows, and
        # re-run whenever the window (and so this container) is resized.
        chips_container.bind("<Configure>", self._reflow_chips)
        self.after(0, self._reflow_chips)

        # ── START CHECK-IN button ─────────────────────────────────────────────
        tk.Frame(inner, bg=theme.BORDER, height=1).pack(fill="x",
                                                          padx=theme.PADDING, pady=12)

        start_btn = make_rounded_button(
            inner,
            f"▶  {i18n.t('start_checkin')}",
            self._on_start_checkin,
            bg=theme.ACCENT, fg=theme.TEXT_LIGHT, hover_bg=theme.ACCENT_DARK,
            font=theme.FONT_BODY_B, padx=24, pady=15, radius=26,
            min_width=300,
        )
        start_btn.pack(pady=6, padx=theme.PADDING)

        # ── Upcoming appointments preview ─────────────────────────────────────
        if self._patient.appointments:
            tk.Label(
                inner, text=i18n.t("upcoming_appts"),
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
            text=f"{i18n.t('discharged', days=days_since)} · {self._patient.primary_diagnosis}",
            font=theme.FONT_SMALL_B, bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
            wraplength=330, justify="left", padx=12, pady=10,
        ).pack(anchor="w")

        # bottom padding
        tk.Frame(inner, bg=theme.BG_MAIN, height=80).pack()

        # ── Bottom navigation bar ─────────────────────────────────────────────
        self._build_nav_bar()

    def _reflow_chips(self, event=None):
        """Lay the check-in chips into as many equal columns as fit the width."""
        cont = getattr(self, "_chips_container", None)
        btns = getattr(self, "_chip_buttons", None)
        if not cont or not btns:
            return
        avail = event.width if event is not None else cont.winfo_width()
        if avail <= 1:
            return
        unit = self._chip_w + 10          # chip width + 5px padding on each side
        cols = max(1, int(avail // unit))
        for i, b in enumerate(btns):
            b.grid_configure(row=i // cols, column=i % cols,
                             padx=5, pady=3, sticky="w")

    def _build_language_selector(self, parent: tk.Widget):
        """A 🌐 translate dropdown in the top bar offering the five languages."""
        mb = tk.Menubutton(
            parent,
            text=f"🌐  {i18n.short_label()}  ▾",
            font=theme.FONT_SMALL_B,
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_DARK, activeforeground=theme.TEXT_LIGHT,
            bd=0, padx=10, pady=4, relief="flat", cursor="hand2",
        )
        menu = tk.Menu(mb, tearoff=0, font=theme.FONT_BODY)
        current = i18n.get_language()
        for code, label, _short in i18n.LANGUAGES:
            menu.add_command(
                label=("✓ " if code == current else "    ") + label,
                command=lambda c=code: self._set_language(c),
            )
        mb.config(menu=menu)
        mb.pack(side="right", padx=(0, 16), pady=8)

    def _set_language(self, code: str):
        i18n.set_language(code)
        # Keep the patient record in sync so other screens reflect the choice.
        try:
            self._patient.language = code
        except Exception:
            pass
        # Re-render the whole dashboard in the new language.
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    def _animate_mascot(self):
        """Gently float the mascot image up and down (a soft hover/bounce)."""
        lbl = getattr(self, "_mascot_label", None)
        if lbl is None or not lbl.winfo_exists():
            return
        self._bounce_phase += 0.13
        y = self._mascot_base_y + self._bounce_amp * math.sin(self._bounce_phase)
        lbl.place_configure(y=int(round(y)))
        self._mascot_after = self.after(33, self._animate_mascot)  # ~30 fps

    def _load_mascot_image(self, max_w: int, max_h: int):
        """Load assets/dr_mario.png scaled to fit; return None if unavailable."""
        if not os.path.exists(_MASCOT_PATH):
            return None
        # Prefer Pillow for clean scaling; fall back to Tk's integer subsample.
        try:
            from PIL import Image, ImageTk
            img = Image.open(_MASCOT_PATH).convert("RGBA")
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            try:
                photo = tk.PhotoImage(file=_MASCOT_PATH)
                # Ceiling division so the result always fits within max_w x max_h.
                factor = max(1,
                             -(-photo.width() // max_w),
                             -(-photo.height() // max_h))
                if factor > 1:
                    photo = photo.subsample(factor, factor)
                return photo
            except Exception:
                return None

    def _build_nav_bar(self):
        nav = tk.Frame(self, bg=theme.BG_NAV, height=theme.NAV_HEIGHT,
                       highlightbackground=theme.BORDER, highlightthickness=1)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)

        nav_items = [
            ("🏠", "nav_home", "dashboard"),
            ("💬", "nav_checkin", "chat"),
            ("💊", "nav_meds", "medications"),
            ("🗓️", "nav_streak", "calendar"),
            ("📅", "nav_appts", "appointments"),
            ("👤", "nav_profile", "risk"),
        ]
        for icon, label_key, key in nav_items:
            is_active = key == "dashboard"
            col = theme.TEAL_PRIMARY if is_active else theme.TEXT_HINT
            btn_frame = tk.Frame(nav, bg=theme.BG_NAV, cursor="hand2")
            btn_frame.pack(side="left", expand=True, fill="y")
            icon_lbl = tk.Label(btn_frame, text=icon, font=("Segoe UI Emoji", 18),
                                bg=theme.BG_NAV, fg=col)
            icon_lbl.pack(pady=(6, 0))
            text_lbl = tk.Label(btn_frame, text=i18n.t(label_key), font=theme.FONT_NAV,
                                bg=theme.BG_NAV, fg=col)
            text_lbl.pack()
            # Bind the click to the frame AND its child labels — in Tk a click
            # on a child Label does not propagate up to the parent Frame.
            for w in (btn_frame, icon_lbl, text_lbl):
                w.bind("<Button-1>", lambda e, k=key: self._on_nav(k))
