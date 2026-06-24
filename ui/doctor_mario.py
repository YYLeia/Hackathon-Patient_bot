"""
ui/doctor_mario.py
Draws a Doctor Mario style character on a tk.Canvas using pure Tkinter shapes.
No external image assets required.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme


def draw_doctor_mario(canvas: tk.Canvas, cx: int, cy: int, scale: float = 1.0):
    """
    Draw a Doctor Mario character centred at (cx, cy).
    scale=1.0 → approx 120×150px. All coordinates are relative offsets from (cx, cy).
    """
    s = scale

    def p(dx, dy):
        return cx + dx * s, cy + dy * s

    def oval(x1, y1, x2, y2, **kw):
        canvas.create_oval(cx + x1*s, cy + y1*s, cx + x2*s, cy + y2*s, **kw)

    def rect(x1, y1, x2, y2, **kw):
        canvas.create_rectangle(cx + x1*s, cy + y1*s, cx + x2*s, cy + y2*s, **kw)

    def poly(*pts, **kw):
        scaled = []
        for i in range(0, len(pts), 2):
            scaled += [cx + pts[i]*s, cy + pts[i+1]*s]
        canvas.create_polygon(*scaled, **kw)

    # ── Lab coat body ──────────────────────────────────────────────────────────
    # Main torso (white coat)
    poly(
        -38, 20,  38, 20,  48, 80,  -48, 80,
        fill="#FFFFFF", outline="#CCCCCC", width=2,
    )
    # Coat lapels (teal inner shirt visible)
    poly(-10, 20, 10, 20, 14, 50, -14, 50,
         fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1)

    # Red cross on coat pocket
    rect(-6, 32, 6, 44, fill=theme.TEAL_PRIMARY, outline="")
    rect(-14, 35, -6, 41, fill="#E53E3E", outline="")
    rect(-6, 29, 0, 35, fill="#E53E3E", outline="")
    rect(0, 29, 6, 35, fill="#E53E3E", outline="")
    rect(6, 35, 14, 41, fill="#E53E3E", outline="")
    rect(-6, 41, 0, 47, fill="#E53E3E", outline="")
    rect(0, 41, 6, 47, fill="#E53E3E", outline="")
    # Simplified: just a white + cross
    rect(-5, 33, 5, 43, fill="#FFFFFF", outline="")
    rect(-9, 36, -5, 40, fill="#E53E3E", outline="")
    rect(5, 36, 9, 40, fill="#E53E3E", outline="")
    rect(-2, 33, 2, 36, fill="#E53E3E", outline="")
    rect(-2, 40, 2, 43, fill="#E53E3E", outline="")

    # Coat collar
    poly(-12, 20, 0, 28, 12, 20,
         fill="#FFFFFF", outline="#CCCCCC", width=1)

    # ── Arms ───────────────────────────────────────────────────────────────────
    # Left arm
    poly(-38, 22, -55, 35, -60, 65, -45, 70, -40, 50,
         fill="#FFFFFF", outline="#CCCCCC", width=2)
    # Right arm — raised, holding stethoscope
    poly(38, 22, 58, 18, 68, 48, 52, 55, 40, 42,
         fill="#FFFFFF", outline="#CCCCCC", width=2)

    # ── Hands ──────────────────────────────────────────────────────────────────
    oval(-62, 62, -44, 78, fill="#F4C2A1", outline="#D4956B", width=2)  # left
    oval(50, 46, 72, 62, fill="#F4C2A1", outline="#D4956B", width=2)    # right

    # ── Stethoscope (right hand) ───────────────────────────────────────────────
    canvas.create_arc(
        cx + 52*s, cy + 30*s, cx + 80*s, cy + 60*s,
        start=20, extent=200,
        style="arc", outline=theme.TEAL_DARK, width=int(3*s)
    )
    oval(74, 46, 84, 56, fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=2)

    # ── Legs ───────────────────────────────────────────────────────────────────
    rect(-30, 78, -10, 110, fill="#2D3748", outline="#1A202C", width=1)
    rect(10, 78, 30, 110, fill="#2D3748", outline="#1A202C", width=1)

    # Shoes
    poly(-36, 108, -6, 108, -4, 122, -38, 122,
         fill="#E53E3E", outline="#C53030", width=2)
    poly(6, 108, 36, 108, 38, 122, 4, 122,
         fill="#E53E3E", outline="#C53030", width=2)

    # ── Head ───────────────────────────────────────────────────────────────────
    # Hair (brown/dark)
    oval(-32, -78, 32, -30, fill="#5D3A1A", outline="#3D2010", width=2)

    # Face
    oval(-28, -70, 28, -18, fill="#F4C2A1", outline="#D4956B", width=2)

    # ── Doctor cap (white with teal cross) ─────────────────────────────────────
    rect(-30, -80, 30, -62, fill="#FFFFFF", outline="#CCCCCC", width=2)
    # Cap band
    rect(-30, -68, 30, -62, fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1)
    # Cross on cap
    rect(-4, -80, 4, -62, fill="#E53E3E", outline="")
    rect(-14, -74, 14, -68, fill="#E53E3E", outline="")

    # ── Eyes ───────────────────────────────────────────────────────────────────
    # Glasses frames
    oval(-22, -56, -6, -44, fill="#FFFFFF", outline=theme.TEAL_DARK, width=2)
    oval(6, -56, 22, -44, fill="#FFFFFF", outline=theme.TEAL_DARK, width=2)
    # Bridge
    canvas.create_line(cx - 6*s, cy - 50*s, cx + 6*s, cy - 50*s,
                       fill=theme.TEAL_DARK, width=int(2*s))
    # Pupils
    oval(-17, -53, -11, -47, fill="#2D3748", outline="")
    oval(11, -53, 17, -47, fill="#2D3748", outline="")
    # Eye shine
    oval(-15, -52, -13, -50, fill="#FFFFFF", outline="")
    oval(13, -52, 15, -50, fill="#FFFFFF", outline="")

    # ── Nose ───────────────────────────────────────────────────────────────────
    oval(-4, -42, 4, -36, fill="#E8A98A", outline="")

    # ── Smile ──────────────────────────────────────────────────────────────────
    canvas.create_arc(
        cx - 14*s, cy - 36*s, cx + 14*s, cy - 20*s,
        start=200, extent=140,
        style="arc", outline="#C53030", width=int(2*s)
    )

    # ── Moustache ──────────────────────────────────────────────────────────────
    poly(-18, -34, -2, -30, 0, -32, 2, -30, 18, -34,
         fill="#5D3A1A", outline="")

    # ── Speech bubble (small, top right) ──────────────────────────────────────
    bubble_x = cx + 50*s
    bubble_y = cy - 80*s
    bw, bh = 50*s, 30*s
    oval_kw = dict(fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=2)
    canvas.create_oval(bubble_x, bubble_y, bubble_x + bw, bubble_y + bh, **oval_kw)
    canvas.create_text(
        bubble_x + bw//2, bubble_y + bh//2,
        text="Hi! 😊", font=("Segoe UI", int(8*s), "bold"),
        fill="#FFFFFF",
    )
    # Bubble tail
    poly_pts_x = [bubble_x + 5*s/s, bubble_x - 5*s/s, bubble_x + 12]
    canvas.create_polygon(
        bubble_x + 6, bubble_y + bh - 4,
        bubble_x + 16, bubble_y + bh + 10,
        bubble_x + 20, bubble_y + bh - 4,
        fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1,
    )

    # ── Heart bubble (left) ────────────────────────────────────────────────────
    hx = cx - 90*s
    hy = cy - 50*s
    hw = 40*s
    canvas.create_oval(hx, hy, hx + hw, hy + hw,
                       fill=theme.TEAL_LIGHT, outline=theme.BORDER, width=2)
    canvas.create_text(hx + hw//2, hy + hw//2, text="❤️",
                       font=("Segoe UI Emoji", int(14*s)))


def create_doctor_mario_canvas(
    parent: tk.Widget,
    width: int = 220,
    height: int = 200,
    bg: str = theme.BG_MAIN,
    scale: float = 0.85,
) -> tk.Canvas:
    canvas = tk.Canvas(parent, width=width, height=height,
                       bg=bg, highlightthickness=0)
    draw_doctor_mario(canvas, cx=width // 2, cy=height // 2 + 10, scale=scale)
    return canvas
