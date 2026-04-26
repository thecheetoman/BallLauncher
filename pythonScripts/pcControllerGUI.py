#!/usr/bin/env python3
"""
Xbox 360 Controller to RC Car Bridge — GUI Edition
Reads Xbox controller and sends commands to ROCK 4C+ over Wi-Fi
"""

import sys
import time
import threading
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: requests library is not installed.")
    print("Install it with: pip install requests")
    sys.exit(1)

try:
    import inputs
    INPUTS_AVAILABLE = True
except ImportError:
    INPUTS_AVAILABLE = False

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
ROCK_IP   = "192.168.4.1"
ROCK_PORT = 8000
ROCK_URL  = f"http://{ROCK_IP}:{ROCK_PORT}"
RZ_THRESHOLD = 50

# ─────────────────────────────────────────────
# Palette / design tokens
# ─────────────────────────────────────────────
BG       = "#0d0d0d"
PANEL    = "#141414"
BORDER   = "#2a2a2a"
ACCENT   = "#e8ff00"       # electric yellow
ACCENT2  = "#ff4444"       # danger red
DIM      = "#3a3a3a"
TEXT     = "#e0e0e0"
TEXT_DIM = "#5a5a5a"
GREEN    = "#39ff14"       # neon green
ORANGE   = "#ff8c00"

LOG_MAX  = 200             # max log lines kept


class RCControllerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RC CAR CONTROL")
        self.configure(bg=BG)
        self.resizable(False, False)

        # ── state ──
        self.rz_value        = tk.IntVar(value=0)
        self.rz_is_pressed   = False
        self.b_button_pressed = False
        self.motor_enabled   = False
        self.motor_high      = False
        self.server_ok       = False
        self.controller_ok   = False
        self._controller_thread = None
        self._stop_event     = threading.Event()
        self._poll_after_id  = None

        self._load_fonts()
        self._build_ui()
        self.after(300, self._initial_checks)

    # ─────────────────────────────────────────
    # Fonts
    # ─────────────────────────────────────────
    def _load_fonts(self):
        self.f_title   = tkfont.Font(family="Courier New", size=22, weight="bold")
        self.f_label   = tkfont.Font(family="Courier New", size=9,  weight="bold")
        self.f_value   = tkfont.Font(family="Courier New", size=28, weight="bold")
        self.f_status  = tkfont.Font(family="Courier New", size=10, weight="bold")
        self.f_log     = tkfont.Font(family="Courier New", size=8)
        self.f_btn     = tkfont.Font(family="Courier New", size=10, weight="bold")
        self.f_badge   = tkfont.Font(family="Courier New", size=8,  weight="bold")

    # ─────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────
    def _build_ui(self):
        # ── outer frame with thick border ──
        outer = tk.Frame(self, bg=ACCENT, padx=2, pady=2)
        outer.pack(padx=10, pady=10)

        root_frame = tk.Frame(outer, bg=BG, padx=14, pady=12)
        root_frame.pack()

        # ── title bar ──
        title_row = tk.Frame(root_frame, bg=BG)
        title_row.pack(fill="x", pady=(0, 10))

        tk.Label(title_row, text="◈ RC CAR", font=self.f_title,
                 fg=ACCENT, bg=BG).pack(side="left")

        tk.Label(title_row, text="CONTROL BRIDGE",
                 font=tkfont.Font(family="Courier New", size=22),
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=(8, 0))

        self._ver_badge = tk.Label(title_row, text="v2.0", font=self.f_badge,
                                   fg=BG, bg=ACCENT, padx=6, pady=2)
        self._ver_badge.pack(side="right", anchor="n", pady=4)

        # ── separator ──
        tk.Frame(root_frame, bg=ACCENT, height=1).pack(fill="x", pady=(0, 10))

        # ── top row: status cards ──
        top = tk.Frame(root_frame, bg=BG)
        top.pack(fill="x", pady=(0, 10))

        self._card_server     = self._status_card(top, "SERVER", ROCK_URL, side="left")
        tk.Frame(top, bg=BG, width=8).pack(side="left")
        self._card_controller = self._status_card(top, "CONTROLLER", "Xbox 360", side="left")

        # ── middle row: telemetry + trigger ──
        mid = tk.Frame(root_frame, bg=BG)
        mid.pack(fill="x", pady=(0, 10))

        self._build_trigger_panel(mid)
        tk.Frame(mid, bg=BG, width=8).pack(side="left")
        self._build_motor_panel(mid)
        tk.Frame(mid, bg=BG, width=8).pack(side="left")
        self._build_buttons_panel(mid)

        # ── log ──
        log_frame = tk.Frame(root_frame, bg=PANEL, bd=0,
                             highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="x", pady=(0, 4))

        hdr = tk.Frame(log_frame, bg=PANEL)
        hdr.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(hdr, text="COMMAND LOG", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(side="left")
        self._clear_btn = tk.Label(hdr, text="[CLEAR]", font=self.f_badge,
                                   fg=DIM, bg=PANEL, cursor="hand2")
        self._clear_btn.pack(side="right")
        self._clear_btn.bind("<Button-1>", lambda e: self._clear_log())

        self._log_text = tk.Text(
            log_frame, height=8, bg=PANEL, fg=TEXT_DIM,
            font=self.f_log, bd=0, relief="flat",
            state="disabled", cursor="arrow",
            selectbackground=DIM, insertbackground=ACCENT
        )
        self._log_text.pack(fill="x", padx=8, pady=(0, 6))

        sb = tk.Scrollbar(log_frame, command=self._log_text.yview,
                          bg=PANEL, troughcolor=PANEL, relief="flat", width=6)
        self._log_text["yscrollcommand"] = sb.set

        # ── footer ──
        foot = tk.Frame(root_frame, bg=BG)
        foot.pack(fill="x", pady=(4, 0))
        tk.Label(foot, text="CTRL+C / window close to stop",
                 font=self.f_badge, fg=TEXT_DIM, bg=BG).pack(side="left")
        self._conn_btn = self._pill_button(foot, "RECONNECT", self._reconnect,
                                           side="right", color=ACCENT, fg=BG)

        # ── tag colours for log ──
        self._log_text.tag_config("ok",  foreground=GREEN)
        self._log_text.tag_config("err", foreground=ACCENT2)
        self._log_text.tag_config("cmd", foreground=ACCENT)
        self._log_text.tag_config("inf", foreground=TEXT_DIM)
        self._log_text.tag_config("ts",  foreground=DIM)

        # ── window close ──
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── widget factories ──────────────────────
    def _status_card(self, parent, label, sub, side="left"):
        frame = tk.Frame(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER)
        frame.pack(side=side, fill="y")

        tk.Label(frame, text=label, font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(anchor="w", padx=10, pady=(8, 0))

        dot_row = tk.Frame(frame, bg=PANEL)
        dot_row.pack(anchor="w", padx=10, pady=(2, 0))

        dot = tk.Label(dot_row, text="●", font=self.f_status,
                       fg=ACCENT2, bg=PANEL)
        dot.pack(side="left")

        status_lbl = tk.Label(dot_row, text="OFFLINE",
                              font=self.f_status, fg=ACCENT2, bg=PANEL)
        status_lbl.pack(side="left", padx=(4, 0))

        tk.Label(frame, text=sub, font=self.f_badge,
                 fg=DIM, bg=PANEL).pack(anchor="w", padx=10, pady=(2, 8))

        return {"dot": dot, "label": status_lbl, "frame": frame}

    def _build_trigger_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER)
        frame.pack(side="left", fill="both")

        tk.Label(frame, text="RIGHT TRIGGER", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(padx=12, pady=(8, 2))

        self._rz_canvas = tk.Canvas(frame, width=60, height=120,
                                    bg=PANEL, bd=0, highlightthickness=0)
        self._rz_canvas.pack(padx=12)

        self._rz_val_lbl = tk.Label(frame, text="0", font=self.f_value,
                                    fg=TEXT_DIM, bg=PANEL, width=4)
        self._rz_val_lbl.pack(pady=(4, 8))

        self._draw_trigger_bar(0)

    def _draw_trigger_bar(self, value):
        """Redraw the trigger bar (0-255)."""
        c = self._rz_canvas
        c.delete("all")
        W, H = 60, 120
        # track
        c.create_rectangle(18, 4, 42, H - 4,
                            fill=DIM, outline="", width=0)
        # fill
        if value > 0:
            pct   = value / 255
            fill_h = int((H - 8) * pct)
            color = ACCENT if value < RZ_THRESHOLD else GREEN
            c.create_rectangle(18, H - 4 - fill_h, 42, H - 4,
                                fill=color, outline="", width=0)
        # threshold line
        th_y = H - 4 - int((H - 8) * RZ_THRESHOLD / 255)
        c.create_line(12, th_y, 48, th_y, fill=ACCENT2, width=1, dash=(3, 3))

    def _build_motor_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER)
        frame.pack(side="left", fill="both", expand=True)

        tk.Label(frame, text="MOTOR STATE", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(padx=14, pady=(8, 4))

        # Enable indicator
        en_row = tk.Frame(frame, bg=PANEL)
        en_row.pack(fill="x", padx=14)
        tk.Label(en_row, text="ENABLE", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL, width=7, anchor="w").pack(side="left")
        self._en_dot = tk.Label(en_row, text="■ DISABLED",
                                font=self.f_status, fg=ACCENT2, bg=PANEL)
        self._en_dot.pack(side="left", padx=(6, 0))

        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", padx=14, pady=6)

        # Speed indicator
        spd_row = tk.Frame(frame, bg=PANEL)
        spd_row.pack(fill="x", padx=14)
        tk.Label(spd_row, text="SPEED", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL, width=7, anchor="w").pack(side="left")
        self._spd_lbl = tk.Label(spd_row, text="■ LOW",
                                 font=self.f_status, fg=ORANGE, bg=PANEL)
        self._spd_lbl.pack(side="left", padx=(6, 0))

        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", padx=14, pady=6)

        # Last command
        tk.Label(frame, text="LAST CMD", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(anchor="w", padx=14)
        self._last_cmd_lbl = tk.Label(frame, text="—", font=self.f_status,
                                      fg=TEXT, bg=PANEL)
        self._last_cmd_lbl.pack(anchor="w", padx=14, pady=(2, 10))

    def _build_buttons_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER)
        frame.pack(side="left", fill="both")

        tk.Label(frame, text="MANUAL", font=self.f_badge,
                 fg=TEXT_DIM, bg=PANEL).pack(padx=14, pady=(8, 6))

        btns = [
            ("C_ON:MHigh",  GREEN,   "THROTTLE\nHIGH"),
            ("C_ON:MLow",   ORANGE,  "THROTTLE\nLOW"),
            ("MEnable",     ACCENT,  "MOTOR\nENABLE"),
            ("MDisable",    ACCENT2, "MOTOR\nDISABLE"),
        ]
        for cmd, color, label in btns:
            b = tk.Button(
                frame, text=label,
                font=self.f_badge,
                fg=BG, bg=color,
                activeforeground=BG, activebackground=color,
                relief="flat", bd=0, cursor="hand2",
                padx=10, pady=4, width=10,
                command=lambda c=cmd: self._manual_send(c)
            )
            b.pack(padx=14, pady=3)

        tk.Frame(frame, bg=BG, height=6).pack()

    def _pill_button(self, parent, text, cmd, side="left",
                     color=ACCENT, fg=BG):
        b = tk.Button(parent, text=text, font=self.f_badge,
                      fg=fg, bg=color, activeforeground=fg,
                      activebackground=color, relief="flat", bd=0,
                      cursor="hand2", padx=10, pady=4, command=cmd)
        b.pack(side=side, padx=(6, 0))
        return b

    # ─────────────────────────────────────────
    # Status updates
    # ─────────────────────────────────────────
    def _set_server_status(self, ok: bool):
        self.server_ok = ok
        color = GREEN if ok else ACCENT2
        text  = "ONLINE" if ok else "OFFLINE"
        self._card_server["dot"].config(fg=color)
        self._card_server["label"].config(fg=color, text=text)

    def _set_controller_status(self, ok: bool):
        self.controller_ok = ok
        color = GREEN if ok else ACCENT2
        text  = "CONNECTED" if ok else "NOT FOUND"
        self._card_controller["dot"].config(fg=color)
        self._card_controller["label"].config(fg=color, text=text)

    def _update_motor_ui(self, enabled=None, high=None):
        if enabled is not None:
            self.motor_enabled = enabled
            self._en_dot.config(
                text="■ ENABLED"  if enabled else "■ DISABLED",
                fg=GREEN          if enabled else ACCENT2
            )
        if high is not None:
            self.motor_high = high
            self._spd_lbl.config(
                text="■ HIGH" if high else "■ LOW",
                fg=GREEN      if high else ORANGE
            )

    def _update_trigger_ui(self, value: int):
        self._draw_trigger_bar(value)
        self._rz_val_lbl.config(
            text=str(value),
            fg=GREEN if value >= RZ_THRESHOLD else TEXT_DIM
        )

    # ─────────────────────────────────────────
    # Log
    # ─────────────────────────────────────────
    def _log(self, msg: str, tag="inf"):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_text.config(state="normal")

        # Trim old lines
        line_count = int(self._log_text.index("end-1c").split(".")[0])
        if line_count > LOG_MAX:
            self._log_text.delete("1.0", f"{line_count - LOG_MAX}.0")

        self._log_text.insert("end", f"[{ts}] ", "ts")
        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _clear_log(self):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

    # ─────────────────────────────────────────
    # Network
    # ─────────────────────────────────────────
    def send_command(self, command: str) -> bool:
        try:
            response = requests.post(
                ROCK_URL,
                json={"command": command},
                timeout=0.5
            )
            ok = response.status_code == 200
            tag = "ok" if ok else "err"
            sym = "✓" if ok else "✗"
            self.after(0, self._log, f"{sym} {command}", tag)
            self.after(0, self._last_cmd_lbl.config, {"text": command,
                        "fg": GREEN if ok else ACCENT2})
            return ok
        except requests.exceptions.Timeout:
            self.after(0, self._log, f"✗ Timeout → {command}", "err")
        except requests.exceptions.ConnectionError:
            self.after(0, self._log, f"✗ No connection → {command}", "err")
            self.after(0, self._set_server_status, False)
        except Exception as e:
            self.after(0, self._log, f"✗ {e}", "err")
        return False

    def check_connection(self) -> bool:
        try:
            r = requests.get(ROCK_URL, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    # ─────────────────────────────────────────
    # Startup / reconnect
    # ─────────────────────────────────────────
    def _initial_checks(self):
        self._log("Starting up…", "inf")
        threading.Thread(target=self._check_all, daemon=True).start()

    def _check_all(self):
        # Controller
        if not INPUTS_AVAILABLE:
            self.after(0, self._log,
                       "✗ inputs library not installed (pip install inputs)", "err")
            self.after(0, self._set_controller_status, False)
        else:
            try:
                pads = inputs.devices.gamepads
                found = bool(pads)
            except Exception:
                found = False
            self.after(0, self._set_controller_status, found)
            if found:
                self.after(0, self._log,
                           f"✓ Controller found ({len(pads)})", "ok")
            else:
                self.after(0, self._log, "✗ No controller detected", "err")

        # Server
        ok = self.check_connection()
        self.after(0, self._set_server_status, ok)
        if ok:
            self.after(0, self._log, f"✓ Server reachable at {ROCK_URL}", "ok")
        else:
            self.after(0, self._log, f"✗ Cannot reach {ROCK_URL}", "err")

        # Start controller loop if both ok
        if self.controller_ok and self.server_ok:
            threading.Thread(target=self._send_initial, daemon=True).start()
            self._start_controller_thread()

    def _send_initial(self):
        self.send_command("C_ON:MLow")

    def _reconnect(self):
        self._log("Reconnecting…", "inf")
        self._stop_controller_thread()
        threading.Thread(target=self._check_all, daemon=True).start()

    # ─────────────────────────────────────────
    # Controller thread
    # ─────────────────────────────────────────
    def _start_controller_thread(self):
        self._stop_event.clear()
        self._controller_thread = threading.Thread(
            target=self._controller_loop, daemon=True)
        self._controller_thread.start()
        self.after(0, self._log, "Controller loop started", "inf")

    def _stop_controller_thread(self):
        self._stop_event.set()

    def _controller_loop(self):
        while not self._stop_event.is_set():
            try:
                events = inputs.get_gamepad()
                for event in events:
                    if self._stop_event.is_set():
                        return

                    if event.code == "ABS_RZ":
                        val = event.state
                        self.after(0, self._update_trigger_ui, val)

                        if val >= RZ_THRESHOLD and not self.rz_is_pressed:
                            self.rz_is_pressed = True
                            self.after(0, self._update_motor_ui, None, True)
                            threading.Thread(
                                target=self.send_command,
                                args=("C_ON:MHigh",), daemon=True).start()

                        elif val < RZ_THRESHOLD and self.rz_is_pressed:
                            self.rz_is_pressed = False
                            self.after(0, self._update_motor_ui, None, False)
                            threading.Thread(
                                target=self.send_command,
                                args=("C_ON:MLow",), daemon=True).start()

                    elif event.code == "BTN_EAST" and event.ev_type == "Key":
                        if event.state == 1 and not self.b_button_pressed:
                            self.b_button_pressed = True
                            self.after(0, self._update_motor_ui, True, None)
                            threading.Thread(
                                target=self.send_command,
                                args=("MEnable",), daemon=True).start()
                        elif event.state == 0 and self.b_button_pressed:
                            self.b_button_pressed = False
                            self.after(0, self._update_motor_ui, False, None)
                            threading.Thread(
                                target=self.send_command,
                                args=("MDisable",), daemon=True).start()

            except Exception:
                if not self._stop_event.is_set():
                    self.after(0, self._log, "✗ Controller disconnected", "err")
                    self.after(0, self._set_controller_status, False)
                    self.after(0, self._update_trigger_ui, 0)
                    break
                return

            time.sleep(0.001)

    # ─────────────────────────────────────────
    # Manual buttons
    # ─────────────────────────────────────────
    def _manual_send(self, cmd: str):
        if cmd == "MEnable":
            self._update_motor_ui(enabled=True)
        elif cmd == "MDisable":
            self._update_motor_ui(enabled=False)
        elif cmd == "C_ON:MHigh":
            self._update_motor_ui(high=True)
        elif cmd == "C_ON:MLow":
            self._update_motor_ui(high=False)
        threading.Thread(target=self.send_command, args=(cmd,), daemon=True).start()

    # ─────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────
    def _on_close(self):
        self._stop_controller_thread()
        if self.rz_is_pressed:
            try:
                requests.post(ROCK_URL, json={"command": "C_OFF:MLow"}, timeout=1)
            except Exception:
                pass
        self.destroy()


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = RCControllerApp()
    app.mainloop()