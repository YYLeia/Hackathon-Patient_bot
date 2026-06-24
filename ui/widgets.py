"""
ui/widgets.py
Reusable widget helpers: rounded frames, chat bubbles, cards, alert banners.
"""

from __future__ import annotations
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from ui import theme


# ── Rounded pill button (canvas-based, since tk.Button can't round corners) ────

def make_rounded_button(
    parent: tk.Widget,
    text: str,
    command,
    *,
    bg: str = theme.TEAL_PRIMARY,
    fg: str = theme.TEXT_LIGHT,
    hover_bg: str | None = None,
    font=theme.FONT_BODY_B,
    padx: int = 22,
    pady: int = 12,
    radius: int = 22,
    min_width: int | None = None,
) -> tk.Canvas:
    """A big, friendly, fully-rounded (pill) button drawn on a Canvas.

    tk.Button cannot render rounded corners, so we draw a rounded rectangle and
    centred text on a Canvas and bind the click ourselves.
    """
    hover_bg = hover_bg or theme.TEAL_DARK

    fam = font[0]
    size = font[1] if len(font) > 1 else 11
    weight = font[2] if len(font) > 2 else "normal"
    f = tkfont.Font(family=fam, size=size, weight=weight)

    lines = text.split("\n")
    text_w = max(f.measure(ln) for ln in lines)
    text_h = f.metrics("linespace") * len(lines)

    w = max(text_w + padx * 2, min_width or 0)
    h = text_h + pady * 2
    r = min(radius, h // 2)

    canvas = tk.Canvas(
        parent, width=w, height=h,
        bg=parent.cget("bg"), highlightthickness=0, cursor="hand2",
    )

    def _draw(fill):
        canvas.delete("all")
        _draw_rounded_rect(canvas, 1, 1, w - 1, h - 1, r, fill=fill, outline=fill)
        canvas.create_text(w / 2, h / 2, text=text, fill=fg, font=f, justify="center")

    _draw(bg)
    canvas.bind("<Enter>", lambda e: _draw(hover_bg))
    canvas.bind("<Leave>", lambda e: _draw(bg))
    canvas.bind("<Button-1>", lambda e: command())
    return canvas


# ── Rounded-corner canvas frame ───────────────────────────────────────────────

def make_rounded_frame(
    parent: tk.Widget,
    bg: str = theme.BG_CARD,
    radius: int = 16,
    width: int = 340,
    height: int = 80,
    **kwargs,
) -> tk.Canvas:
    canvas = tk.Canvas(
        parent, width=width, height=height,
        bg=parent.cget("bg"), highlightthickness=0, **kwargs
    )
    _draw_rounded_rect(canvas, 0, 0, width, height, radius, fill=bg, outline=theme.BORDER)
    return canvas


def _draw_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, fill="", outline="", width=1):
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", fill=fill, outline=outline, width=width)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90,  style="pieslice", fill=fill, outline=outline, width=width)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,  style="pieslice", fill=fill, outline=outline, width=width)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,  style="pieslice", fill=fill, outline=outline, width=width)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline="")
    canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline="")


# ── Chat bubble ───────────────────────────────────────────────────────────────

def add_chat_bubble(
    parent: tk.Frame,
    text: str,
    role: str,          # "agent" | "patient"
    show_avatar: bool = True,
) -> tk.Frame:
    """Append a chat bubble row to parent frame and return it."""
    is_agent = role == "agent"
    row = tk.Frame(parent, bg=theme.BG_MAIN)
    row.pack(fill="x", padx=theme.PADDING, pady=4, anchor="w" if is_agent else "e")

    bubble_bg  = theme.BUBBLE_AGENT   if is_agent else theme.BUBBLE_PATIENT
    text_color = theme.TEXT_DARK      if is_agent else theme.TEXT_LIGHT
    anchor     = "w"                  if is_agent else "e"
    side       = "left"               if is_agent else "right"
    justify    = "left"               if is_agent else "right"

    # Small avatar circle for agent
    if is_agent and show_avatar:
        av = tk.Label(
            row, text="🩺", font=("Segoe UI Emoji", 14),
            bg=theme.TEAL_LIGHT, width=2, height=1,
            relief="flat", bd=0,
        )
        av.pack(side="left", padx=(0, 6), pady=2, anchor="s")

    bubble = tk.Label(
        row,
        text=text,
        font=theme.FONT_CHAT,
        bg=bubble_bg,
        fg=text_color,
        wraplength=theme.BUBBLE_MAX_W,
        justify=justify,
        padx=14,
        pady=10,
        relief="flat",
        bd=0,
    )
    bubble.pack(side=side, anchor=anchor)

    # Add subtle shadow feel via a thin teal border for agent bubbles
    if is_agent:
        bubble.config(highlightbackground=theme.BORDER, highlightthickness=1)

    return row


# ── Quick-reply chip ──────────────────────────────────────────────────────────

def make_chip(
    parent: tk.Frame,
    text: str,
    command,
    color: str = theme.TEAL_LIGHT,
    text_color: str = theme.TEAL_DARK,
) -> tk.Button:
    btn = tk.Button(
        parent,
        text=text,
        font=theme.FONT_SMALL_B,
        bg=color,
        fg=text_color,
        activebackground=theme.TEAL_PRIMARY,
        activeforeground=theme.TEXT_LIGHT,
        bd=0,
        padx=12,
        pady=6,
        relief="flat",
        cursor="hand2",
        command=command,
    )
    return btn


# ── Alert banner ──────────────────────────────────────────────────────────────

SEVERITY_COLORS = {
    "CRITICAL": ("#E53E3E", "#FFF5F5"),
    "HIGH":     ("#DD6B20", "#FFFAF0"),
    "MEDIUM":   ("#D69E2E", "#FEFCBF"),
    "LOW":      ("#38A169", "#F0FFF4"),
}

SEVERITY_ICONS = {
    "CRITICAL": "🚨",
    "HIGH":     "⚠️",
    "MEDIUM":   "⚡",
    "LOW":      "ℹ️",
}


def make_alert_banner(parent: tk.Frame, alert) -> tk.Frame:
    """Create a coloured alert banner widget."""
    fg, bg = SEVERITY_COLORS.get(alert.severity, ("#333", "#fff"))
    icon = SEVERITY_ICONS.get(alert.severity, "⚠️")

    frame = tk.Frame(parent, bg=bg, bd=0)
    frame.pack(fill="x", padx=theme.PADDING, pady=4)

    header = tk.Frame(frame, bg=bg)
    header.pack(fill="x", padx=10, pady=(8, 2))

    tk.Label(
        header,
        text=f"{icon}  CLINICAL ALERT — {alert.severity}",
        font=theme.FONT_SMALL_B,
        bg=bg, fg=fg,
    ).pack(side="left")

    tk.Label(
        frame,
        text=alert.description,
        font=theme.FONT_SMALL,
        bg=bg, fg=theme.TEXT_DARK,
        wraplength=330,
        justify="left",
        padx=10,
    ).pack(anchor="w", pady=(0, 8))

    # Thin bottom border
    sep = tk.Frame(frame, bg=fg, height=2)
    sep.pack(fill="x", side="bottom")

    return frame


# ── Medication card ───────────────────────────────────────────────────────────

def make_med_card(parent: tk.Frame, med, on_take_callback) -> tk.Frame:
    frame = tk.Frame(parent, bg=theme.BG_CARD, bd=0,
                     highlightbackground=theme.BORDER, highlightthickness=1)
    frame.pack(fill="x", padx=theme.PADDING, pady=6)

    inner = tk.Frame(frame, bg=theme.BG_CARD)
    inner.pack(fill="x", padx=14, pady=10)

    # Name + dose
    name_row = tk.Frame(inner, bg=theme.BG_CARD)
    name_row.pack(fill="x")
    tk.Label(name_row, text=med.name, font=theme.FONT_BODY_B,
             bg=theme.BG_CARD, fg=theme.TEAL_DARK).pack(side="left")
    tk.Label(name_row, text=f"  {med.dose}", font=theme.FONT_BODY,
             bg=theme.BG_CARD, fg=theme.TEXT_MID).pack(side="left")

    # Frequency + times
    tk.Label(inner, text=f"🕐  {med.frequency}  ·  {', '.join(med.times)}",
             font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_MID).pack(anchor="w", pady=2)

    # Instructions
    tk.Label(inner, text=med.instructions, font=theme.FONT_SMALL,
             bg=theme.BG_CARD, fg=theme.TEXT_MID, wraplength=290, justify="left").pack(anchor="w")

    # Taken button (rounded, bright)
    if med.taken_today:
        btn = make_rounded_button(
            inner, "✓ Taken Today", lambda m=med: on_take_callback(m),
            bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK, hover_bg=theme.BORDER,
            font=theme.FONT_SMALL_B, padx=16, pady=7, radius=16,
        )
    else:
        btn = make_rounded_button(
            inner, "Mark as Taken", lambda m=med: on_take_callback(m),
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT, hover_bg=theme.TEAL_DARK,
            font=theme.FONT_SMALL_B, padx=16, pady=7, radius=16,
        )
    btn.pack(anchor="e", pady=(6, 0))

    return frame


# ── Appointment card ──────────────────────────────────────────────────────────

def make_appt_card(parent: tk.Frame, appt) -> tk.Frame:
    frame = tk.Frame(parent, bg=theme.BG_CARD, bd=0,
                     highlightbackground=theme.BORDER, highlightthickness=1)
    frame.pack(fill="x", padx=theme.PADDING, pady=6)

    inner = tk.Frame(frame, bg=theme.BG_CARD)
    inner.pack(fill="x", padx=14, pady=10)

    # Date badge
    date_str = appt.scheduled_dt.strftime("%d %b")
    time_str = appt.scheduled_dt.strftime("%I:%M %p")
    badge = tk.Frame(inner, bg=theme.TEAL_PRIMARY, width=50)
    badge.pack(side="left", padx=(0, 12), fill="y")
    tk.Label(badge, text=date_str, font=theme.FONT_SMALL_B,
             bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT).pack(pady=(8, 0), padx=6)
    tk.Label(badge, text=time_str, font=("Segoe UI", 8),
             bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT).pack(pady=(0, 8), padx=6)

    # Content
    content = tk.Frame(inner, bg=theme.BG_CARD)
    content.pack(side="left", fill="both", expand=True)
    tk.Label(content, text=appt.description, font=theme.FONT_BODY_B,
             bg=theme.BG_CARD, fg=theme.TEAL_DARK, anchor="w").pack(fill="x")
    tk.Label(content, text=f"👨‍⚕️ {appt.provider_name}", font=theme.FONT_SMALL,
             bg=theme.BG_CARD, fg=theme.TEXT_MID, anchor="w").pack(fill="x")
    tk.Label(content, text=f"📍 {appt.location}", font=theme.FONT_SMALL,
             bg=theme.BG_CARD, fg=theme.TEXT_MID, anchor="w", wraplength=220, justify="left").pack(fill="x")

    # What to expect
    expect_frame = tk.Frame(inner, bg=theme.BG_MAIN)
    expect_frame.pack(fill="x", side="bottom", pady=(8, 0))
    tk.Label(expect_frame, text="What to expect:", font=theme.FONT_SMALL_B,
             bg=theme.BG_MAIN, fg=theme.TEXT_MID).pack(anchor="w", padx=8, pady=(4, 0))
    tk.Label(expect_frame, text=appt.what_to_expect, font=theme.FONT_SMALL,
             bg=theme.BG_MAIN, fg=theme.TEXT_MID, wraplength=320,
             justify="left").pack(anchor="w", padx=8, pady=(0, 4))

    return frame


# ── Risk level badge ──────────────────────────────────────────────────────────

RISK_BADGE_COLORS = {
    "CRITICAL": ("#E53E3E", "#FFF5F5"),
    "HIGH":     ("#DD6B20", "#FFFAF0"),
    "MEDIUM":   ("#D69E2E", "#FEFCBF"),
    "LOW":      ("#38A169", "#F0FFF4"),
}


def make_risk_badge(parent: tk.Frame, risk_level: str, risk_score: int) -> tk.Frame:
    fg, bg = RISK_BADGE_COLORS.get(risk_level, ("#333", "#eee"))
    frame = tk.Frame(parent, bg=bg, bd=0,
                     highlightbackground=fg, highlightthickness=2)
    tk.Label(frame, text=f"Risk: {risk_level}  {risk_score}/100",
             font=theme.FONT_BADGE, bg=bg, fg=fg, padx=10, pady=4).pack()
    return frame
