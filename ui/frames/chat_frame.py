"""
ui/frames/chat_frame.py
The primary check-in chat screen — scrollable bubbles, typing indicator, alert banners.
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from ui import theme
from ui.widgets import add_chat_bubble, make_chip, make_alert_banner


QUICK_REPLIES = [
    "I'm feeling okay",
    "I'm in pain",
    "I missed a medication",
    "I had a fall",
    "I'm feeling confused",
]


class CheckInChatFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, controller, patient, on_nav=None):
        super().__init__(parent, bg=theme.BG_MAIN)
        self._controller = controller
        self._patient = patient
        self._on_nav = on_nav
        self._session = None
        self._typing = False

        self._build_ui()

    # ── Build UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ─────────────────────────────────────────────────────────
        top_bar = tk.Frame(self, bg=theme.BG_NAV, height=56)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        # Back button — navigates to dashboard
        def _go_back(event=None):
            if self._on_nav:
                self._on_nav("dashboard")

        back_btn = tk.Label(
            top_bar, text="←", font=("Segoe UI", 16),
            bg=theme.BG_NAV, fg=theme.TEXT_DARK, cursor="hand2",
        )
        back_btn.pack(side="left", padx=16, pady=8)
        back_btn.bind("<Button-1>", _go_back)

        tk.Label(
            top_bar, text="Chat with Dr. Mario",
            font=theme.FONT_SUBTITLE, bg=theme.BG_NAV, fg=theme.TEXT_DARK,
        ).pack(side="left", padx=8)

        # Transcript button — always visible in top bar
        transcript_btn = tk.Button(
            top_bar,
            text="📄 Transcript",
            font=("Segoe UI", 10),
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_DARK, activeforeground=theme.TEXT_LIGHT,
            relief="flat", bd=0, padx=8, pady=4,
            cursor="hand2",
            command=self._show_transcript,
        )
        transcript_btn.pack(side="right", padx=12, pady=8)

        # separator
        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")

        # ── Alert container (appears above chat) ─────────────────────────────
        self._alert_container = tk.Frame(self, bg=theme.BG_MAIN)
        self._alert_container.pack(fill="x")

        # ── Scrollable chat area ──────────────────────────────────────────────
        chat_outer = tk.Frame(self, bg=theme.BG_MAIN)
        chat_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(chat_outer, bg=theme.BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_outer, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._chat_inner = tk.Frame(self._canvas, bg=theme.BG_MAIN)
        self._chat_window = self._canvas.create_window(
            (0, 0), window=self._chat_inner, anchor="nw"
        )

        self._chat_inner.bind("<Configure>", self._on_chat_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Typing indicator label ────────────────────────────────────────────
        self._typing_label = tk.Label(
            self._chat_inner, text="Dr. Mario is typing…",
            font=("Segoe UI", 11, "italic"),
            bg=theme.BG_MAIN, fg=theme.TEXT_HINT,
        )

        # ── Quick replies ─────────────────────────────────────────────────────
        self._quick_frame = tk.Frame(self, bg=theme.BG_MAIN)
        self._quick_frame.pack(fill="x", padx=theme.PADDING, pady=(4, 0))
        self._build_quick_replies()

        # ── Input bar ─────────────────────────────────────────────────────────
        input_bar = tk.Frame(self, bg=theme.BG_NAV, pady=8)
        input_bar.pack(fill="x", side="bottom")

        mic_btn = tk.Label(
            input_bar, text="🎤", font=("Segoe UI Emoji", 16),
            bg=theme.BG_NAV, fg=theme.TEXT_MID, cursor="hand2",
        )
        mic_btn.pack(side="left", padx=(12, 6))

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            input_bar, textvariable=self._input_var,
            font=theme.FONT_INPUT, bg="#F0F8F5",
            fg=theme.TEXT_DARK, insertbackground=theme.TEAL_PRIMARY,
            relief="flat", bd=0,
        )
        self._input_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self._input_entry.insert(0, "Message Dr. Mario…")
        self._input_entry.config(fg=theme.TEXT_HINT)
        self._input_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._input_entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._input_entry.bind("<Return>", lambda e: self._on_send())

        clip_btn = tk.Label(
            input_bar, text="📎", font=("Segoe UI Emoji", 16),
            bg=theme.BG_NAV, fg=theme.TEXT_MID, cursor="hand2",
        )
        clip_btn.pack(side="left", padx=6)

        send_btn = tk.Button(
            input_bar,
            text="➤",
            font=("Segoe UI", 14, "bold"),
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_DARK, activeforeground=theme.TEXT_LIGHT,
            relief="flat", bd=0, padx=12, pady=8,
            cursor="hand2",
            command=self._on_send,
        )
        send_btn.pack(side="right", padx=12)

    def _build_quick_replies(self):
        for w in self._quick_frame.winfo_children():
            w.destroy()

        row1 = tk.Frame(self._quick_frame, bg=theme.BG_MAIN)
        row1.pack(fill="x", pady=2)
        row2 = tk.Frame(self._quick_frame, bg=theme.BG_MAIN)
        row2.pack(fill="x", pady=2)

        for i, label in enumerate(QUICK_REPLIES):
            parent_row = row1 if i < 3 else row2
            chip = make_chip(parent_row, label, lambda l=label: self._send_quick(l))
            chip.pack(side="left", padx=3, pady=2)

    # ── Session management ────────────────────────────────────────────────────

    def start_session(self, patient_id: str):
        """Start a check-in session and display the opening message."""
        self._session = self._controller.start_session(patient_id)
        opening = self._session.messages[-1].text
        self.after(300, lambda: self._append_agent(opening))

    def _append_agent(self, text: str):
        add_chat_bubble(self._chat_inner, text, "agent")
        self._scroll_to_bottom()

    def _append_patient(self, text: str):
        add_chat_bubble(self._chat_inner, text, "patient", show_avatar=False)
        self._scroll_to_bottom()

    # ── Typing indicator ───────────────────────────────────────────────────────

    def _show_typing(self):
        self._typing_label.pack(anchor="w", padx=theme.PADDING + 30, pady=4)
        self._scroll_to_bottom()

    def _hide_typing(self):
        self._typing_label.pack_forget()

    # ── Send logic ─────────────────────────────────────────────────────────────

    def _on_send(self):
        text = self._input_var.get().strip()
        if not text or text == "Message Dr. Mario…":
            return
        if self._session is None:
            return

        self._input_var.set("")
        self._input_entry.config(fg=theme.TEXT_DARK)
        self._append_patient(text)
        self._hide_typing()
        self._show_typing()

        # Disable input while waiting
        self._input_entry.config(state="disabled")

        def _call():
            try:
                turn = self._controller.send_message(self._session.session_id, text)
                self.after(0, lambda: self._on_turn_complete(turn))
            except Exception as e:
                self.after(0, lambda: self._on_agent_error(str(e)))

        threading.Thread(target=_call, daemon=True).start()

    def _send_quick(self, text: str):
        self._input_var.set(text)
        self._input_entry.config(fg=theme.TEXT_DARK)
        self._on_send()

    def _on_turn_complete(self, turn):
        self._hide_typing()
        self._input_entry.config(state="normal")
        self._append_agent(turn.agent_message.text)

        # Show alerts
        for alert in turn.alerts:
            make_alert_banner(self._alert_container, alert)

        # Check if session is complete
        if turn.session_status == "COMPLETE":
            self._on_session_complete()

    def _on_agent_error(self, error_msg: str):
        self._hide_typing()
        self._input_entry.config(state="normal")
        self._append_agent(
            "I'm having a little trouble connecting right now. "
            "Please try again in a moment, or call your care team directly."
        )

    def _on_session_complete(self):
        # Show completion banner
        complete_frame = tk.Frame(self._chat_inner, bg=theme.TEAL_LIGHT, bd=0)
        complete_frame.pack(fill="x", padx=theme.PADDING, pady=8)
        tk.Label(
            complete_frame,
            text="✅  Check-in complete! Your responses have been sent to your care team.",
            font=theme.FONT_SMALL_B,
            bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
            wraplength=320, justify="center", pady=12,
        ).pack()

        # Export
        try:
            report = self._controller.finalize_session(self._session.session_id)
            from core.report_generator import ReportGenerator
            rg = ReportGenerator(self._controller._llm)
            ts_path = rg.export_transcript(
                self._controller._session_repo.get(self._session.session_id),
                f"transcript_{self._session.session_id[:8]}.txt"
            )
            rpt_path = rg.export_clinical_report(
                report, f"clinical_report_{self._session.session_id[:8]}.txt"
            )
            tk.Label(
                complete_frame,
                text=f"📄 Transcript: {ts_path}\n📋 Report: {rpt_path}",
                font=("Segoe UI", 9), bg=theme.TEAL_LIGHT, fg=theme.TEXT_MID,
                wraplength=320, justify="center", pady=4,
            ).pack()
        except Exception:
            pass

        self._input_entry.config(state="disabled")
        self._scroll_to_bottom()

    # ── Transcript viewer ──────────────────────────────────────────────────────

    def _show_transcript(self):
        """Open a separate scrollable window with the full conversation transcript."""
        win = tk.Toplevel(self)
        win.title("Full Conversation Transcript — Dr. Mario")
        win.configure(bg=theme.BG_MAIN)
        win.resizable(True, True)

        # Size and centre relative to parent
        tw, th = 620, 600
        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        rw = self.winfo_width()
        rh = self.winfo_height()
        wx = rx + (rw - tw) // 2
        wy = ry + (rh - th) // 2
        win.geometry(f"{tw}x{th}+{max(0, wx)}+{max(0, wy)}")
        win.minsize(400, 300)

        # Header
        header = tk.Frame(win, bg=theme.TEAL_PRIMARY, pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="📄  Full Conversation Transcript",
            font=theme.FONT_SUBTITLE,
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
        ).pack(side="left", padx=16)

        # Refresh button — re-reads session on demand
        def _refresh():
            _populate(txt)

        tk.Button(
            header, text="⟳ Refresh",
            font=("Segoe UI", 10),
            bg=theme.TEAL_DARK, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_PRIMARY,
            relief="flat", bd=0, padx=8, pady=4,
            cursor="hand2", command=_refresh,
        ).pack(side="right", padx=12)

        # Scrollable text area
        txt_frame = tk.Frame(win, bg=theme.BG_MAIN)
        txt_frame.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        txt = tk.Text(
            txt_frame,
            font=("Segoe UI", 11),
            bg="#FAFFFE",
            fg=theme.TEXT_DARK,
            wrap="word",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            state="disabled",
            cursor="arrow",
        )
        sb = tk.Scrollbar(txt_frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        # Text tags for colour-coded roles
        txt.tag_config("header",   font=("Segoe UI", 10, "bold"), foreground=theme.TEXT_HINT)
        txt.tag_config("mario",    font=("Segoe UI", 11, "bold"), foreground=theme.TEAL_DARK)
        txt.tag_config("patient",  font=("Segoe UI", 11, "bold"), foreground="#6B46C1")
        txt.tag_config("bubble_mario",   font=("Segoe UI", 11), foreground=theme.TEXT_DARK)
        txt.tag_config("bubble_patient", font=("Segoe UI", 11), foreground="#2D3748")
        txt.tag_config("divider",  foreground=theme.BORDER)
        txt.tag_config("empty",    font=("Segoe UI", 11, "italic"), foreground=theme.TEXT_HINT)

        def _populate(t: tk.Text):
            t.config(state="normal")
            t.delete("1.0", "end")

            if self._session is None or not self._session.messages:
                t.insert("end", "No conversation yet — start a check-in to see the transcript.\n", "empty")
                t.config(state="disabled")
                return

            # Session header
            started = self._session.started_at.strftime("%d %b %Y  %H:%M")
            status = self._session.status
            t.insert("end", f"Session started: {started}   |   Status: {status}\n", "header")
            t.insert("end", "─" * 70 + "\n\n", "divider")

            for msg in self._session.messages:
                if msg.role == "system":
                    continue
                ts = msg.timestamp.strftime("%H:%M:%S")
                if msg.role == "agent":
                    t.insert("end", f"[{ts}]  Dr. Mario\n", "mario")
                    t.insert("end", f"  {msg.text}\n\n", "bubble_mario")
                elif msg.role == "patient":
                    t.insert("end", f"[{ts}]  You\n", "patient")
                    t.insert("end", f"  {msg.text}\n\n", "bubble_patient")

            t.insert("end", "─" * 70 + "\n", "divider")
            if self._session.alerts:
                t.insert("end", f"⚠️  {len(self._session.alerts)} alert(s) raised during this session.\n", "header")

            t.config(state="disabled")
            t.yview_moveto(1.0)  # scroll to bottom

        _populate(txt)

        # Close button
        btn_bar = tk.Frame(win, bg=theme.BG_MAIN, pady=8)
        btn_bar.pack(fill="x", side="bottom")
        tk.Button(
            btn_bar, text="Close",
            font=("Segoe UI", 11),
            bg=theme.BORDER, fg=theme.TEXT_DARK,
            activebackground=theme.TEXT_HINT,
            relief="flat", bd=0, padx=16, pady=6,
            cursor="hand2", command=win.destroy,
        ).pack(pady=4)

    # ── Scroll helpers ─────────────────────────────────────────────────────────

    def _scroll_to_bottom(self):
        self.after(60, lambda: self._canvas.yview_moveto(1.0))

    def _on_chat_resize(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._chat_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Input placeholder behaviour ────────────────────────────────────────────

    def _on_entry_focus_in(self, event):
        if self._input_entry.get() == "Message Dr. Mario…":
            self._input_entry.delete(0, "end")
            self._input_entry.config(fg=theme.TEXT_DARK)

    def _on_entry_focus_out(self, event):
        if not self._input_entry.get():
            self._input_entry.insert(0, "Message Dr. Mario…")
            self._input_entry.config(fg=theme.TEXT_HINT)

        # ── Alert container (appears above chat) ─────────────────────────────
        self._alert_container = tk.Frame(self, bg=theme.BG_MAIN)
        self._alert_container.pack(fill="x")

        # ── Scrollable chat area ──────────────────────────────────────────────
        chat_outer = tk.Frame(self, bg=theme.BG_MAIN)
        chat_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(chat_outer, bg=theme.BG_MAIN, highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_outer, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._chat_inner = tk.Frame(self._canvas, bg=theme.BG_MAIN)
        self._chat_window = self._canvas.create_window(
            (0, 0), window=self._chat_inner, anchor="nw"
        )

        self._chat_inner.bind("<Configure>", self._on_chat_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Typing indicator label ────────────────────────────────────────────
        self._typing_label = tk.Label(
            self._chat_inner, text="Dr. Mario is typing…",
            font=("Segoe UI", 11, "italic"),
            bg=theme.BG_MAIN, fg=theme.TEXT_HINT,
        )

        # ── Quick replies ─────────────────────────────────────────────────────
        self._quick_frame = tk.Frame(self, bg=theme.BG_MAIN)
        self._quick_frame.pack(fill="x", padx=theme.PADDING, pady=(4, 0))
        self._build_quick_replies()

        # ── Input bar ─────────────────────────────────────────────────────────
        input_bar = tk.Frame(self, bg=theme.BG_NAV, pady=8)
        input_bar.pack(fill="x", side="bottom")

        mic_btn = tk.Label(
            input_bar, text="🎤", font=("Segoe UI Emoji", 16),
            bg=theme.BG_NAV, fg=theme.TEXT_MID, cursor="hand2",
        )
        mic_btn.pack(side="left", padx=(12, 6))

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            input_bar, textvariable=self._input_var,
            font=theme.FONT_INPUT, bg="#F0F8F5",
            fg=theme.TEXT_DARK, insertbackground=theme.TEAL_PRIMARY,
            relief="flat", bd=0,
        )
        self._input_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self._input_entry.insert(0, "Message Dr. Mario…")
        self._input_entry.config(fg=theme.TEXT_HINT)
        self._input_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._input_entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._input_entry.bind("<Return>", lambda e: self._on_send())

        clip_btn = tk.Label(
            input_bar, text="📎", font=("Segoe UI Emoji", 16),
            bg=theme.BG_NAV, fg=theme.TEXT_MID, cursor="hand2",
        )
        clip_btn.pack(side="left", padx=6)

        send_btn = tk.Button(
            input_bar,
            text="➤",
            font=("Segoe UI", 14, "bold"),
            bg=theme.TEAL_PRIMARY, fg=theme.TEXT_LIGHT,
            activebackground=theme.TEAL_DARK, activeforeground=theme.TEXT_LIGHT,
            relief="flat", bd=0, padx=12, pady=8,
            cursor="hand2",
            command=self._on_send,
        )
        send_btn.pack(side="right", padx=12)

    def _build_quick_replies(self):
        for w in self._quick_frame.winfo_children():
            w.destroy()

        row1 = tk.Frame(self._quick_frame, bg=theme.BG_MAIN)
        row1.pack(fill="x", pady=2)
        row2 = tk.Frame(self._quick_frame, bg=theme.BG_MAIN)
        row2.pack(fill="x", pady=2)

        for i, label in enumerate(QUICK_REPLIES):
            parent_row = row1 if i < 3 else row2
            chip = make_chip(parent_row, label, lambda l=label: self._send_quick(l))
            chip.pack(side="left", padx=3, pady=2)

    # ── Session management ────────────────────────────────────────────────────

    def start_session(self, patient_id: str):
        """Start a check-in session and display the opening message."""
        self._session = self._controller.start_session(patient_id)
        opening = self._session.messages[-1].text
        self.after(300, lambda: self._append_agent(opening))

    def _append_agent(self, text: str):
        add_chat_bubble(self._chat_inner, text, "agent")
        self._scroll_to_bottom()

    def _append_patient(self, text: str):
        add_chat_bubble(self._chat_inner, text, "patient", show_avatar=False)
        self._scroll_to_bottom()

    # ── Typing indicator ───────────────────────────────────────────────────────

    def _show_typing(self):
        self._typing_label.pack(anchor="w", padx=theme.PADDING + 30, pady=4)
        self._scroll_to_bottom()

    def _hide_typing(self):
        self._typing_label.pack_forget()

    # ── Send logic ─────────────────────────────────────────────────────────────

    def _on_send(self):
        text = self._input_var.get().strip()
        if not text or text == "Message Dr. Mario…":
            return
        if self._session is None:
            return

        self._input_var.set("")
        self._input_entry.config(fg=theme.TEXT_DARK)
        self._append_patient(text)
        self._hide_typing()
        self._show_typing()

        # Disable input while waiting
        self._input_entry.config(state="disabled")

        def _call():
            try:
                turn = self._controller.send_message(self._session.session_id, text)
                self.after(0, lambda: self._on_turn_complete(turn))
            except Exception as e:
                self.after(0, lambda: self._on_agent_error(str(e)))

        threading.Thread(target=_call, daemon=True).start()

    def _send_quick(self, text: str):
        self._input_var.set(text)
        self._input_entry.config(fg=theme.TEXT_DARK)
        self._on_send()

    def _on_turn_complete(self, turn):
        self._hide_typing()
        self._input_entry.config(state="normal")
        self._append_agent(turn.agent_message.text)

        # Show alerts
        for alert in turn.alerts:
            make_alert_banner(self._alert_container, alert)

        # Check if session is complete
        if turn.session_status == "COMPLETE":
            self._on_session_complete()

    def _on_agent_error(self, error_msg: str):
        self._hide_typing()
        self._input_entry.config(state="normal")
        self._append_agent(
            "I'm having a little trouble connecting right now. "
            "Please try again in a moment, or call your care team directly."
        )

    def _on_session_complete(self):
        # Show completion banner
        complete_frame = tk.Frame(self._chat_inner, bg=theme.TEAL_LIGHT, bd=0)
        complete_frame.pack(fill="x", padx=theme.PADDING, pady=8)
        tk.Label(
            complete_frame,
            text="✅  Check-in complete! Your responses have been sent to your care team.",
            font=theme.FONT_SMALL_B,
            bg=theme.TEAL_LIGHT, fg=theme.TEAL_DARK,
            wraplength=320, justify="center", pady=12,
        ).pack()

        # Export
        try:
            report = self._controller.finalize_session(self._session.session_id)
            from core.report_generator import ReportGenerator
            rg = ReportGenerator(self._controller._llm)
            ts_path = rg.export_transcript(
                self._controller._session_repo.get(self._session.session_id),
                f"transcript_{self._session.session_id[:8]}.txt"
            )
            rpt_path = rg.export_clinical_report(
                report, f"clinical_report_{self._session.session_id[:8]}.txt"
            )
            tk.Label(
                complete_frame,
                text=f"📄 Transcript: {ts_path}\n📋 Report: {rpt_path}",
                font=("Segoe UI", 9), bg=theme.TEAL_LIGHT, fg=theme.TEXT_MID,
                wraplength=320, justify="center", pady=4,
            ).pack()
        except Exception:
            pass

        self._input_entry.config(state="disabled")
        self._scroll_to_bottom()

    # ── Scroll helpers ─────────────────────────────────────────────────────────

    def _scroll_to_bottom(self):
        self.after(60, lambda: self._canvas.yview_moveto(1.0))

    def _on_chat_resize(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._chat_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Input placeholder behaviour ────────────────────────────────────────────

    def _on_entry_focus_in(self, event):
        if self._input_entry.get() == "Message Dr. Mario…":
            self._input_entry.delete(0, "end")
            self._input_entry.config(fg=theme.TEXT_DARK)

    def _on_entry_focus_out(self, event):
        if not self._input_entry.get():
            self._input_entry.insert(0, "Message Dr. Mario…")
            self._input_entry.config(fg=theme.TEXT_HINT)
