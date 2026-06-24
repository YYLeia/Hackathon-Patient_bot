"""
ui/frames/notification_overlay.py
In-app notification overlay — simulates a push notification banner.
"""

from __future__ import annotations
import tkinter as tk
from ui import theme


class NotificationOverlay(tk.Toplevel):
    """
    A floating notification banner that appears at the top of the app window.
    Auto-dismisses after `auto_dismiss_ms` milliseconds.
    """

    def __init__(
        self,
        parent: tk.Tk,
        title: str,
        body: str,
        on_action=None,
        action_label: str = "Open",
        auto_dismiss_ms: int = 8000,
    ):
        super().__init__(parent)
        self._on_action = on_action
        self.overrideredirect(True)  # no window chrome

        # Position at top-centre of parent
        parent.update_idletasks()
        pw = parent.winfo_width()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        ow = min(pw - 20, 370)
        self.geometry(f"{ow}x90+{px + (pw - ow)//2}+{py + 10}")

        self.attributes("-topmost", True)
        self.configure(bg=theme.TEAL_DARK)

        frame = tk.Frame(self, bg=theme.TEAL_DARK, padx=14, pady=10)
        frame.pack(fill="both", expand=True)

        # Icon + title row
        top_row = tk.Frame(frame, bg=theme.TEAL_DARK)
        top_row.pack(fill="x")
        tk.Label(top_row, text="🔔  " + title,
                 font=theme.FONT_SMALL_B, bg=theme.TEAL_DARK,
                 fg=theme.TEXT_LIGHT).pack(side="left")

        dismiss_btn = tk.Label(top_row, text="✕", font=theme.FONT_SMALL_B,
                               bg=theme.TEAL_DARK, fg=theme.TEXT_LIGHT, cursor="hand2")
        dismiss_btn.pack(side="right")
        dismiss_btn.bind("<Button-1>", lambda e: self.dismiss())

        # Body
        tk.Label(frame, text=body, font=theme.FONT_SMALL,
                 bg=theme.TEAL_DARK, fg=theme.TEXT_LIGHT,
                 wraplength=280, justify="left").pack(anchor="w", pady=(2, 0))

        # Action button
        if on_action:
            act_btn = tk.Button(
                frame, text=action_label, font=theme.FONT_SMALL_B,
                bg=theme.TEXT_LIGHT, fg=theme.TEAL_DARK,
                bd=0, padx=10, pady=3, relief="flat", cursor="hand2",
                command=self._action,
            )
            act_btn.pack(anchor="e", pady=(4, 0))

        if auto_dismiss_ms > 0:
            self.after(auto_dismiss_ms, self.dismiss)

    def _action(self):
        self.dismiss()
        if self._on_action:
            self._on_action()

    def dismiss(self):
        try:
            self.destroy()
        except Exception:
            pass
