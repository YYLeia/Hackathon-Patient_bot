"""
ui/theme.py
Colour palette, fonts, and shared style constants — teal/mint medical theme.
"""

# ── Colour Palette ─────────────────────────────────────────────────────────────
BG_MAIN       = "#E8F5F2"   # soft mint background
BG_CARD       = "#FFFFFF"   # white cards
BG_NAV        = "#FFFFFF"   # nav bar
TEAL_PRIMARY  = "#2BA88A"   # primary teal (buttons, accents)
TEAL_DARK     = "#1D7A64"   # darker teal (hover, headers)
TEAL_LIGHT    = "#C8EDE5"   # light teal (quick-reply chips)
BUBBLE_AGENT  = "#FFFFFF"   # agent chat bubble bg (white)
BUBBLE_PATIENT= "#2BA88A"   # patient chat bubble bg (teal)
TEXT_DARK     = "#1A2E2A"   # main dark text
TEXT_MID      = "#4A6860"   # secondary text
TEXT_LIGHT    = "#FFFFFF"   # text on teal
TEXT_HINT     = "#9AB8B0"   # placeholder / hint text
BORDER        = "#D0EBE4"   # card borders
ALERT_CRITICAL= "#E53E3E"
ALERT_HIGH    = "#DD6B20"
ALERT_MEDIUM  = "#D69E2E"
ALERT_LOW     = "#38A169"
RISK_HIGH_BG  = "#FFF5F5"
RISK_HIGH_FG  = "#E53E3E"
RISK_MED_BG   = "#FFFAF0"
RISK_MED_FG   = "#DD6B20"
RISK_LOW_BG   = "#F0FFF4"
RISK_LOW_FG   = "#38A169"

# ── Fonts ──────────────────────────────────────────────────────────────────────
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 14, "bold")
FONT_BODY     = ("Segoe UI", 12)
FONT_BODY_B   = ("Segoe UI", 12, "bold")
FONT_SMALL    = ("Segoe UI", 10)
FONT_SMALL_B  = ("Segoe UI", 10, "bold")
FONT_CHAT     = ("Segoe UI", 13)
FONT_CHAT_B   = ("Segoe UI", 13, "bold")
FONT_HUGE     = ("Segoe UI", 22, "bold")
FONT_INPUT    = ("Segoe UI", 13)
FONT_NAV      = ("Segoe UI", 9)
FONT_BADGE    = ("Segoe UI", 10, "bold")

# ── Layout ─────────────────────────────────────────────────────────────────────
APP_WIDTH     = 390          # iPhone-ish width
APP_HEIGHT    = 780
PHONE_RADIUS  = 36
NAV_HEIGHT    = 60
STATUS_HEIGHT = 44
BUBBLE_MAX_W  = 260
PADDING       = 16
