"""
ui/i18n.py
Lightweight in-app translations for the patient home screen.

Holds a small string table for the languages offered by the home-screen
language selector. A module-level "current language" is read by the UI and
updated by the selector; screens re-render to pick up the new strings.
"""

from __future__ import annotations

# (code, full label shown in the dropdown, short label shown on the button)
LANGUAGES = [
    ("en", "English",            "EN"),
    ("zh", "中文 (Mandarin)",     "中文"),
    ("hi", "हिन्दी (Hindi)",      "हिन्दी"),
    ("es", "Español (Spanish)",  "ES"),
    ("ar", "العربية (Arabic)",    "عربي"),
]

# Right-to-left languages (for text justification hints)
_RTL = {"ar"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "greeting":      "Hey, {name}! 👋",
        "subtitle":      "How can I help you with\nyour health today?",
        "quick_topics":  "Quick check-in topics:",
        "pain":          "Pain",
        "medications":   "Medications",
        "breathlessness":"Breathlessness",
        "mobility":      "Mobility",
        "swelling":      "Swelling",
        "mood":          "Mood",
        "start_checkin": "Start Weekly Check-In",
        "upcoming_appts":"Upcoming Appointments",
        "discharged":    "🏥  Discharged {days} days ago",
        "nav_home":      "Home",
        "nav_checkin":   "Check-In",
        "nav_meds":      "Meds",
        "nav_streak":    "Streak",
        "nav_appts":     "Appts",
        "nav_profile":   "Profile",
    },
    "zh": {
        "greeting":      "你好，{name}！👋",
        "subtitle":      "今天我能为您的\n健康做些什么？",
        "quick_topics":  "快速签到主题：",
        "pain":          "疼痛",
        "medications":   "药物",
        "breathlessness":"呼吸困难",
        "mobility":      "行动能力",
        "swelling":      "肿胀",
        "mood":          "情绪",
        "start_checkin": "开始每周签到",
        "upcoming_appts":"即将到来的预约",
        "discharged":    "🏥  {days} 天前出院",
        "nav_home":      "主页",
        "nav_checkin":   "签到",
        "nav_meds":      "药物",
        "nav_streak":    "打卡",
        "nav_appts":     "预约",
        "nav_profile":   "资料",
    },
    "hi": {
        "greeting":      "नमस्ते, {name}! 👋",
        "subtitle":      "आज मैं आपके स्वास्थ्य में\nकैसे मदद कर सकता हूँ?",
        "quick_topics":  "त्वरित चेक-इन विषय:",
        "pain":          "दर्द",
        "medications":   "दवाइयाँ",
        "breathlessness":"साँस फूलना",
        "mobility":      "चलना-फिरना",
        "swelling":      "सूजन",
        "mood":          "मनोदशा",
        "start_checkin": "साप्ताहिक चेक-इन शुरू करें",
        "upcoming_appts":"आगामी अपॉइंटमेंट",
        "discharged":    "🏥  {days} दिन पहले छुट्टी मिली",
        "nav_home":      "होम",
        "nav_checkin":   "चेक-इन",
        "nav_meds":      "दवा",
        "nav_streak":    "स्ट्रीक",
        "nav_appts":     "अपॉइंटमेंट",
        "nav_profile":   "प्रोफ़ाइल",
    },
    "es": {
        "greeting":      "¡Hola, {name}! 👋",
        "subtitle":      "¿Cómo puedo ayudarte hoy\ncon tu salud?",
        "quick_topics":  "Temas rápidos de control:",
        "pain":          "Dolor",
        "medications":   "Medicamentos",
        "breathlessness":"Falta de aire",
        "mobility":      "Movilidad",
        "swelling":      "Hinchazón",
        "mood":          "Ánimo",
        "start_checkin": "Iniciar control semanal",
        "upcoming_appts":"Próximas citas",
        "discharged":    "🏥  Dado de alta hace {days} días",
        "nav_home":      "Inicio",
        "nav_checkin":   "Control",
        "nav_meds":      "Medicinas",
        "nav_streak":    "Racha",
        "nav_appts":     "Citas",
        "nav_profile":   "Perfil",
    },
    "ar": {
        "greeting":      "مرحباً، {name}! 👋",
        "subtitle":      "كيف يمكنني مساعدتك\nفي صحتك اليوم؟",
        "quick_topics":  "مواضيع سريعة للمتابعة:",
        "pain":          "ألم",
        "medications":   "الأدوية",
        "breathlessness":"ضيق التنفس",
        "mobility":      "الحركة",
        "swelling":      "تورم",
        "mood":          "المزاج",
        "start_checkin": "ابدأ المتابعة الأسبوعية",
        "upcoming_appts":"المواعيد القادمة",
        "discharged":    "🏥  خرجت من المستشفى قبل {days} يوماً",
        "nav_home":      "الرئيسية",
        "nav_checkin":   "متابعة",
        "nav_meds":      "الأدوية",
        "nav_streak":    "تتابع",
        "nav_appts":     "المواعيد",
        "nav_profile":   "الملف",
    },
}

_current = "en"


def set_language(code: str) -> None:
    global _current
    if code in TRANSLATIONS:
        _current = code


def get_language() -> str:
    return _current


def is_rtl(code: str | None = None) -> bool:
    return (code or _current) in _RTL


def short_label(code: str | None = None) -> str:
    code = code or _current
    for c, _full, short in LANGUAGES:
        if c == code:
            return short
    return code.upper()


def t(key: str, **fmt) -> str:
    """Translate a key into the current language (falls back to English)."""
    table = TRANSLATIONS.get(_current, {})
    text = table.get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**fmt) if fmt else text
