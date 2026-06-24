"""
ui/doctor_mario.py
Animated Doctor Mario character drawn with pure Tkinter canvas shapes.

Public API (backwards-compatible):
    create_doctor_mario_canvas(parent, width, height, bg, scale) -> tk.Canvas
        Returns the canvas widget (already packed is NOT done — caller packs it).
        The animation starts automatically.

Internal:
    DoctorMarioWidget  — class that owns canvas + animation loop
"""

from __future__ import annotations
import math
import tkinter as tk
from ui import theme


# ── Animation parameters ──────────────────────────────────────────────────────
_FPS          = 30          # redraws per second
_FRAME_MS     = 1000 // _FPS
_BOB_PERIOD   = 90          # frames for one full body bob cycle
_WAVE_PERIOD  = 60          # frames for one full wave cycle
_BOB_AMP      = 4.0         # pixels up/down for body bob
_WAVE_AMP     = 22.0        # degrees of arm rotation for wave


class DoctorMarioWidget:
    """
    Self-contained animated Dr. Mario.
    Create it, then pack/grid ``widget.canvas`` wherever you want it.
    """

    def __init__(
        self,
        parent: tk.Widget,
        width: int = 240,
        height: int = 220,
        bg: str = theme.BG_MAIN,
        scale: float = 0.9,
    ):
        self.canvas = tk.Canvas(
            parent, width=width, height=height,
            bg=bg, highlightthickness=0,
        )
        self._width  = width
        self._height = height
        self._bg     = bg
        self._scale  = scale
        self._cx     = width // 2
        self._cy     = height // 2 + 15   # slightly lower so cap isn't clipped
        self._frame  = 0
        self._running = False

        # Kick off the first draw immediately
        self.canvas.after(10, self._tick)

        # Stop animating if the widget is destroyed
        self.canvas.bind("<Destroy>", lambda e: self._stop())

    # ── Animation loop ────────────────────────────────────────────────────────

    def _stop(self):
        self._running = False

    def _tick(self):
        self._running = True
        self._redraw()
        self._frame += 1
        if self._running:
            self.canvas.after(_FRAME_MS, self._tick)

    # ── Redraw ────────────────────────────────────────────────────────────────

    def _redraw(self):
        self.canvas.delete("all")

        t = self._frame
        s = self._scale
        cx = self._cx
        bg = self._bg

        # ── Body bob: sinusoidal vertical offset ──────────────────────────────
        bob = math.sin(2 * math.pi * t / _BOB_PERIOD) * _BOB_AMP
        # cy for the body group (torso, legs, shoes, arms)
        bcy = self._cy + bob

        # ── Wave: right arm angle oscillates ─────────────────────────────────
        wave_angle = math.sin(2 * math.pi * t / _WAVE_PERIOD) * _WAVE_AMP
        # Raise the arm UP and OUT to the right of the head (+angle = outward),
        # so the waving hand clears the face instead of crossing over it.
        arm_angle = math.radians(50 + wave_angle)

        # ── Head: fixed y (does NOT bob) so it looks like it bobs relative ───
        # Actually bob head slightly less than body for a gentle "nod" feel
        hcy = self._cy + bob * 0.4

        # helper lambdas bound to body centre
        def oval(x1, y1, x2, y2, cy_=None, **kw):
            cy_ = cy_ if cy_ is not None else bcy
            self.canvas.create_oval(
                cx + x1*s, cy_ + y1*s,
                cx + x2*s, cy_ + y2*s,
                **kw,
            )

        def rect(x1, y1, x2, y2, cy_=None, **kw):
            cy_ = cy_ if cy_ is not None else bcy
            self.canvas.create_rectangle(
                cx + x1*s, cy_ + y1*s,
                cx + x2*s, cy_ + y2*s,
                **kw,
            )

        def poly(*pts, cy_=None, **kw):
            cy_ = cy_ if cy_ is not None else bcy
            scaled = []
            for i in range(0, len(pts), 2):
                scaled += [cx + pts[i]*s, cy_ + pts[i+1]*s]
            self.canvas.create_polygon(*scaled, **kw)

        # ══════════════════════════════════════════════════════════════════════
        # BODY GROUP  (bobs up and down)
        # ══════════════════════════════════════════════════════════════════════

        # ── Legs ──────────────────────────────────────────────────────────────
        rect(-28, 18, -10, 48, fill="#2D3748", outline="#1A202C", width=1)
        rect(10,  18,  28, 48, fill="#2D3748", outline="#1A202C", width=1)

        # Shoes
        poly(-34, 46, -6, 46, -4, 58, -36, 58,
             fill="#E53E3E", outline="#C53030", width=2)
        poly(6, 46,  34, 46,  36, 58,   4, 58,
             fill="#E53E3E", outline="#C53030", width=2)

        # ── Lab coat torso ────────────────────────────────────────────────────
        poly(
            -36, -22,  36, -22,  44, 18,  -44, 18,
            fill="#FFFFFF", outline="#CCCCCC", width=2,
        )

        # Coat lapels
        poly(-10, -22, 10, -22, 13, 8, -13, 8,
             fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1)

        # Medical cross pocket (white background + red cross)
        rect(-5, -10, 5, 2, fill="#FFFFFF", outline="#DDDDDD", width=1)
        rect(-8, -5, -5, 0,  fill="#E53E3E", outline="")
        rect( 5, -5,  8, 0,  fill="#E53E3E", outline="")
        rect(-2, -10, 2, -7, fill="#E53E3E", outline="")
        rect(-2,  -1, 2,  2, fill="#E53E3E", outline="")

        # Coat collar V-shape
        poly(-11, -22, 0, -12, 11, -22,
             fill="#FFFFFF", outline="#CCCCCC", width=1)

        # ── Left arm (static, hanging naturally) ──────────────────────────────
        poly(-36, -20, -52, -8, -56, 16, -42, 20, -38, 6,
             fill="#FFFFFF", outline="#CCCCCC", width=2)
        # Left hand
        oval(-58, 12, -42, 26, fill="#F4C2A1", outline="#D4956B", width=2)

        # ── Right arm (animated wave) ─────────────────────────────────────────
        # Arm is a polygon: shoulder pivot at approx (36, -20)
        # We rotate the arm tip around the shoulder using wave_angle
        shoulder_x = 36
        shoulder_y = -20
        arm_len    = 38 * s   # px

        # Tip position (end of forearm)
        tip_x = shoulder_x * s + arm_len * math.sin(arm_angle)
        tip_y = shoulder_y * s - arm_len * math.cos(arm_angle)  # negative = up

        # Build arm polygon relative to body centre (bcy)
        sx  = cx + shoulder_x * s
        sy  = bcy + shoulder_y * s
        tx  = cx + tip_x
        ty  = bcy + tip_y
        dx  = ty - sy   # perpendicular vector components (rotated 90°)
        dy  = -(tx - sx)
        norm = math.hypot(dx, dy) or 1
        dx /= norm
        dy /= norm
        hw = 8 * s   # half-width of arm

        arm_pts = [
            sx + dx*hw, sy + dy*hw,
            sx - dx*hw, sy - dy*hw,
            tx - dx*(hw*0.6), ty - dy*(hw*0.6),
            tx + dx*(hw*0.6), ty + dy*(hw*0.6),
        ]
        self.canvas.create_polygon(*arm_pts,
                                   fill="#FFFFFF", outline="#CCCCCC", width=2)

        # ── Right hand: open palm waving (palm + four fingers + thumb) ────────
        skin, skin_edge = "#F4C2A1", "#D4956B"
        hr = 9 * s
        # Palm
        self.canvas.create_oval(
            tx - hr, ty - hr * 0.7, tx + hr, ty + hr,
            fill=skin, outline=skin_edge, width=2,
        )
        # Four fingers fanned upward (open, waving hand)
        fw, fh = 3.0 * s, 9.0 * s
        for fx in (-6.6, -2.2, 2.2, 6.6):
            x = tx + fx * s
            self.canvas.create_oval(
                x - fw, ty - hr * 0.4 - fh,
                x + fw, ty - hr * 0.4 + 2 * s,
                fill=skin, outline=skin_edge, width=1,
            )
        # Thumb to the lower-left of the palm (toward the arm)
        self.canvas.create_oval(
            tx - hr - 3 * s, ty - 1 * s,
            tx - hr + 4 * s, ty + hr * 0.9,
            fill=skin, outline=skin_edge, width=1,
        )

        # Stethoscope arc (stays near torso, doesn't move with arm for simplicity)
        self.canvas.create_arc(
            cx + 32*s, bcy - 18*s, cx + 58*s, bcy + 10*s,
            start=20, extent=200,
            style="arc", outline=theme.TEAL_DARK, width=int(3*s),
        )
        oval(50, -4, 58, 4, fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=2)

        # ══════════════════════════════════════════════════════════════════════
        # NECK — connects body top to head bottom (fixes the floating head)
        # ══════════════════════════════════════════════════════════════════════
        # Body collar top is at bcy + (-22)*s, head face bottom is at hcy + (-18)*s
        # Draw a filled neck rectangle bridging them
        neck_top_y    = hcy  + (-18) * s   # bottom of face oval
        neck_bottom_y = bcy  + (-22) * s   # top of torso
        if neck_bottom_y < neck_top_y:     # guard against scale oddities
            neck_bottom_y = neck_top_y + 2
        self.canvas.create_rectangle(
            cx - 7*s, neck_top_y,
            cx + 7*s, neck_bottom_y,
            fill="#F4C2A1", outline="#D4956B", width=0,
        )
        # Small overlap over the collar to hide any seam
        self.canvas.create_rectangle(
            cx - 11*s, neck_bottom_y - 4*s,
            cx + 11*s, neck_bottom_y + 4*s,
            fill="#FFFFFF", outline="",
        )

        # ══════════════════════════════════════════════════════════════════════
        # HEAD GROUP  (bobs at half amplitude for a gentle nodding effect)
        # ══════════════════════════════════════════════════════════════════════

        # Hair / back of head
        oval(-28, -78, 28, -28, cy_=hcy, fill="#5D3A1A", outline="#3D2010", width=2)

        # Face
        oval(-26, -72, 26, -18, cy_=hcy, fill="#F4C2A1", outline="#D4956B", width=2)

        # Doctor cap
        rect(-28, -82, 28, -64, cy_=hcy, fill="#FFFFFF", outline="#CCCCCC", width=2)
        rect(-28, -70, 28, -64, cy_=hcy,
             fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1)
        rect(-4,  -82,  4, -64, cy_=hcy, fill="#E53E3E", outline="")
        rect(-13, -76, 13, -70, cy_=hcy, fill="#E53E3E", outline="")

        # Glasses
        oval(-20, -58,  -6, -46, cy_=hcy,
             fill="#FFFFFF", outline=theme.TEAL_DARK, width=2)
        oval(  6, -58,  20, -46, cy_=hcy,
             fill="#FFFFFF", outline=theme.TEAL_DARK, width=2)
        self.canvas.create_line(
            cx - 6*s, hcy - 52*s,
            cx + 6*s, hcy - 52*s,
            fill=theme.TEAL_DARK, width=int(2*s),
        )
        # Pupils
        oval(-15, -55, -11, -51, cy_=hcy, fill="#2D3748", outline="")
        oval( 11, -55,  15, -51, cy_=hcy, fill="#2D3748", outline="")
        # Eye shine
        oval(-14, -55, -12, -53, cy_=hcy, fill="#FFFFFF", outline="")
        oval( 12, -55,  14, -53, cy_=hcy, fill="#FFFFFF", outline="")

        # Nose
        oval(-3, -44, 3, -38, cy_=hcy, fill="#E8A98A", outline="")

        # Smile
        self.canvas.create_arc(
            cx - 12*s, hcy - 38*s,
            cx + 12*s, hcy - 24*s,
            start=200, extent=140,
            style="arc", outline="#C53030", width=int(2*s),
        )

        # Moustache
        poly(-16, -36, -2, -32, 0, -34, 2, -32, 16, -36,
             cy_=hcy, fill="#5D3A1A", outline="")

        # ══════════════════════════════════════════════════════════════════════
        # SPEECH BUBBLE  (fixed position, doesn't bob)
        # ══════════════════════════════════════════════════════════════════════
        # Cycle through a few messages
        messages = ["Hi! 😊", "How are\nyou? 💙", "Feel\nbetter! ✨"]
        msg_idx  = (t // (_BOB_PERIOD * 3)) % len(messages)
        msg_text = messages[msg_idx]

        bx = cx + 48*s
        by = self._cy - 82*s
        bw = 54*s
        bh = 34*s
        self.canvas.create_oval(
            bx, by, bx + bw, by + bh,
            fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=2,
        )
        self.canvas.create_text(
            bx + bw / 2, by + bh / 2,
            text=msg_text,
            font=("Segoe UI", max(7, int(7*s)), "bold"),
            fill="#FFFFFF",
            justify="center",
        )
        # Bubble tail
        self.canvas.create_polygon(
            bx + 6,  by + bh - 2,
            bx + 18, by + bh + 12,
            bx + 22, by + bh - 2,
            fill=theme.TEAL_PRIMARY, outline=theme.TEAL_DARK, width=1,
        )


# ── Backwards-compatible factory function ─────────────────────────────────────

def create_doctor_mario_canvas(
    parent: tk.Widget,
    width: int  = 240,
    height: int = 220,
    bg: str     = theme.BG_MAIN,
    scale: float = 0.9,
) -> tk.Canvas:
    """
    Create an animated Doctor Mario canvas and return it.
    Caller is responsible for packing/gridding the returned canvas.
    """
    widget = DoctorMarioWidget(parent, width=width, height=height,
                               bg=bg, scale=scale)
    return widget.canvas


# ── Legacy single-draw function (kept for compatibility) ──────────────────────

def draw_doctor_mario(canvas: tk.Canvas, cx: int, cy: int, scale: float = 1.0):
    """Static single-frame draw. Prefer DoctorMarioWidget for animation."""
    widget = DoctorMarioWidget.__new__(DoctorMarioWidget)
    widget.canvas = canvas
    widget._width  = int(canvas.cget("width"))
    widget._height = int(canvas.cget("height"))
    widget._bg     = str(canvas.cget("bg"))
    widget._scale  = scale
    widget._cx     = cx
    widget._cy     = cy
    widget._frame  = 0
    widget._running = False
    widget._redraw()
