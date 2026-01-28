# -*- coding: utf-8 -*-
import threading
import time
import math
import os
import tkinter as tk
from tkinter import ttk, messagebox

import sys
import platform
import logging
from datetime import datetime

import keyboard
import pandas as pd
import matplotlib.pyplot as plt

from controllers.gamepad_vigem import VirtualGamepad
from i18n import init_i18n, get_i18n, T


# ===== App Meta =====
APP_VERSION = "v1.8.6"
APP_NAME = "游戏摇杆曲线探测器"
APP_AUTHOR = "刘云耀"
APP_TITLE = f"{APP_NAME} {APP_VERSION}  |  哔哩哔哩：{APP_AUTHOR}"


# ===== Matplotlib 中文 =====
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def clamp(v, lo=-1.0, hi=1.0):
    try:
        v = float(v)
    except (ValueError, TypeError):
        # 无效的数值，返回默认值 0.0
        return 0.0
    return max(lo, min(hi, v))


def tk_event_to_hotkey(event: tk.Event):
    # Tk 捕获按键，返回“键名模式”的 key name（给 keyboard.add_hotkey 用）
    ks = event.keysym
    if ks.startswith("F") and ks[1:].isdigit():
        return ks.lower()  # keyboard 更偏好小写 "f6"

    mapping = {
        "Escape": "esc",
        "Return": "enter",
        "Tab": "tab",
        "space": "space",
        "BackSpace": "backspace",
        "Delete": "delete",
        "Insert": "insert",
        "Home": "home",
        "End": "end",
        "Prior": "page up",
        "Next": "page down",
        "Up": "up",
        "Down": "down",
        "Left": "left",
        "Right": "right",
        "Shift_L": "shift",
        "Shift_R": "shift",
        "Control_L": "ctrl",
        "Control_R": "ctrl",
        "Alt_L": "alt",
        "Alt_R": "alt",
    }
    if ks in mapping:
        return mapping[ks]

    ch = (event.char or "").strip()
    if ch:
        # 单字符也允许
        return ch.lower()

    return ks.lower()


def pav_isotonic_increasing(y):
    # 单调回归
    n = len(y)
    blocks = [(y[i], 1, i, i) for i in range(n)]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] <= blocks[i + 1][0]:
            i += 1
            continue
        a1, w1, s1, e1 = blocks[i]
        a2, w2, s2, e2 = blocks[i + 1]
        nw = w1 + w2
        na = (a1 * w1 + a2 * w2) / nw
        blocks[i] = (na, nw, s1, e2)
        del blocks[i + 1]
        if i > 0:
            i -= 1
    yhat = [0.0] * n
    for a, w, s, e in blocks:
        for j in range(s, e + 1):
            yhat[j] = a
    return yhat


class _StreamToLogger:
    # print -> logger

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self._buf = ""

    def write(self, message):
        if not message:
            return
        self._buf += message
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip()
            if line:
                try:
                    self.logger.log(self.level, f"[STD] {line}")
                except (IOError, ValueError):
                    # 日志写入失败，静默处理避免递归
                    pass

    def flush(self):
        if self._buf.strip():
            try:
                self.logger.log(self.level, f"[STD] {self._buf.strip()}")
            except (IOError, ValueError):
                # 日志写入失败，静默处理
                pass
        self._buf = ""


class VirtualStick(tk.Canvas):
    # 虚拟摇杆

    def __init__(self, master, size=360, deadzone=0.0, **kwargs):
        super().__init__(master, width=size, height=size, bg="#1e1e1e", highlightthickness=0, **kwargs)
        self.size = size
        self.r = size // 2
        self.deadzone = float(deadzone)
        self.cx = self.r
        self.cy = self.r

        self.create_oval(10, 10, size - 10, size - 10, outline="#888", width=2)
        self.create_line(self.cx, 12, self.cx, size - 12, fill="#444")
        self.create_line(12, self.cy, size - 12, self.cy, fill="#444")

        self.knob_r = 12
        self.knob = self.create_oval(
            self.cx - self.knob_r,
            self.cy - self.knob_r,
            self.cx + self.knob_r,
            self.cy + self.knob_r,
            fill="#dddddd",
            outline="",
        )

        self.x = 0.0
        self.y = 0.0
        self._dragging = False

        self.bind("<Button-1>", self._on_down)
        self.bind("<B1-Motion>", self._on_move)
        self.bind("<ButtonRelease-1>", self._on_up)

    def _on_down(self, e):
        self._dragging = True
        self._update(e.x, e.y)

    def _on_move(self, e):
        if self._dragging:
            self._update(e.x, e.y)

    def _on_up(self, e):
        self._dragging = False
        self.set_value(0.0, 0.0)

    def _update(self, mx, my):
        dx = mx - self.cx
        dy = my - self.cy
        maxr = self.r - 18
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > maxr and dist > 0:
            s = maxr / dist
            dx *= s
            dy *= s
        x = dx / maxr
        y = -dy / maxr

        if abs(x) < self.deadzone:
            x = 0.0
        if abs(y) < self.deadzone:
            y = 0.0
        self.set_value(x, y)

    def set_value(self, x, y):
        self.x = clamp(x)
        self.y = clamp(y)
        maxr = self.r - 18
        px = self.cx + self.x * maxr
        py = self.cy - self.y * maxr
        self.coords(self.knob, px - self.knob_r, py - self.knob_r, px + self.knob_r, py + self.knob_r)

    def get_value(self):
        return self.x, self.y


class ScrollableFrame(ttk.Frame):
    # 右侧滚动

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfigure(self.inner_id, width=e.width)

    def _on_mousewheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")


class App(tk.Tk):
    # ✅ 已落实的3项改动：

    def __init__(self):
        super().__init__()

        # ===== 国际化 =====
        # i18n 已由 launcher.py 初始化，这里直接获取实例
        self.i18n = get_i18n()
        # Get initial language name from i18n
        available_langs = self.i18n.get_available_languages()
        initial_lang_name = available_langs.get("zh_CN", "中文（简体）")
        self.current_language_name = tk.StringVar(value=initial_lang_name)

        # ===== 日志 =====
        self.logger = None
        self.log_path = None
        self._log_active = False
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        self._init_runtime_logger()

        # ===== 软件改名（含版本号）=====
        self.title(APP_TITLE)

        self.geometry("1200x780")
        self.minsize(980, 660)
        self.resizable(True, True)

        # ===== 手柄模拟 =====
        self.emu_enabled = False
        self.gamepad_type = tk.StringVar(value="ds4")
        self.gamepad = None

        self.running = True

        # ===== 参数 =====
        self.sample_count = tk.StringVar(value="8")
        self.repeats_per_mag = tk.IntVar(value=5)

        self.min_mag = tk.DoubleVar(value=0.10)
        self.max_mag = tk.DoubleVar(value=1.00)

        self.direction = tk.StringVar(value="right")

        # 死区探测步长 / 回退步长
        self.deadzone_step = tk.DoubleVar(value=0.02)
        self.deadzone_back_step = tk.DoubleVar(value=0.005)

        # 显示坐标
        self.x_axis_max = tk.DoubleVar(value=100.0)
        self.y_axis_max = tk.DoubleVar(value=100.0)

        # keepalive（高频按按钮，防游戏切回键鼠）
        self.keepalive_enabled = tk.BooleanVar(value=True)
        self.keepalive_interval_ms = tk.IntVar(value=120)
        self.keepalive_btn_name = tk.StringVar(value=self.i18n.get("ui.button_square"))
        self._keepalive_last = 0.0

        # ===== 长按 =====
        self.hold_enabled = tk.BooleanVar(value=False)
        self.hold_key_name = tk.StringVar(value=self.i18n.get("ui.trigger_l2"))
        self._hold_applied = False

        # ===== 热键 =====
        self.hotkey_backend = tk.StringVar(value="keyboard_name")
        self._scan_hook_installed = False

        # 兼容性提示（显示在 UI 内，不弹窗）
        self.hotkey_compat_hint = tk.StringVar(value="")

        # ===== 热键 =====
        self.start_key = "f6"
        self.record_key = "f9"
        self.deadzone_key = "f10"
        self.deadzone_back_key = "f11"
        self.end_deadzone_key = "f12"
        self.retry_last_key = "f7"

        # scan_code 版（None 表示未设置）
        self.start_scan = None
        self.record_scan = None
        self.deadzone_scan = None
        self.deadzone_back_scan = None
        self.end_deadzone_scan = None
        self.retry_last_scan = None

        # keyboard.add_hotkey 返回的 handle
        self.hotkey_start = None
        self.hotkey_record = None
        self.hotkey_deadzone = None
        self.hotkey_deadzone_back = None
        self.hotkey_end_deadzone = None
        self.hotkey_retry_last = None

        # 热键捕获模式
        self.capture_mode = None
        self.capture_target_backend = None  # "keyboard_name" or "keyboard_scan"
        self._scan_capture_thread = None

        # ===== 状态机 =====
        self.mode = "idle"  # idle / deadzone / curve
        self.is_armed = False
        self.in_trial = False

        self.deadzone_current_m = 0.0
        self.deadzone_mag = 0.0

        self.measure_mag_list = []
        self.mag_index = 0
        self.rep_index = 0
        self.t0 = None
        self.results = []

        self.allow_adjust_after_deadzone = True

        # ===== 热键 =====
        self._start_guard_lock = threading.Lock()
        self._test_running = False  # 硬锁：测试进行中禁止 start_test 重入
        self._hotkey_cooldown_ms = 250
        self._hotkey_last_ts = {}  # name -> perf_counter()

        # ===== UI =====
        self.status = tk.StringVar(value=self.i18n.get("messages.initial_hint"))
        self.left_stick = None
        self.right_stick = None
        self.lbl_status = None
        self.lbl_tip = None
        self.cmb_pad = None
        self.lbl_emu = None
        self.lbl_keys = None

        # “热键模式”控件放到热键设置旁边
        self.cmb_hotkey_backend = None
        self.lbl_hotkey_hint = None

        self._build_ui()

        self.out_thread = threading.Thread(target=self._output_loop, daemon=True)
        self.out_thread.start()

        # Tk 捕获（键名模式用）”；scan 模式用 keyboard.read_event 捕获）
        self.bind_all("<Key>", self._on_any_key)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(250, self._refresh_wraplengths)

        # 初次评估 + 注册热键
        self._auto_select_backend(reason="init")
        self._register_hotkeys()
        self._log("App init done.")

    # ===== 日志 =====
    def _get_app_base_dir_early(self) -> str:
        """在日志初始化前调用，获取基础目录"""
        try:
            if getattr(sys, "frozen", False):
                return os.path.dirname(sys.executable)
            else:
                return os.getcwd()
        except Exception:
            return os.getcwd()

    def _get_app_base_dir(self) -> str:
        try:
            if getattr(sys, "frozen", False):
                base = os.path.dirname(sys.executable)
            else:
                base = os.getcwd()
        except Exception:
            base = os.getcwd()

        logs_dir = os.path.join(base, "logs")
        try:
            os.makedirs(logs_dir, exist_ok=True)
            return logs_dir
        except Exception:
            home = os.path.expanduser("~")
            logs_dir = os.path.join(home, "stick_calibrator_logs")
            os.makedirs(logs_dir, exist_ok=True)
            return logs_dir

    def _init_runtime_logger(self):
        try:
            logs_dir = self._get_app_base_dir()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_path = os.path.join(logs_dir, f"run_log_{ts}.txt")

            logger = logging.getLogger("stick_calibrator")
            logger.setLevel(logging.DEBUG)
            logger.handlers.clear()
            logger.propagate = False

            fmt = logging.Formatter(
                fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            fh = logging.FileHandler(self.log_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(fmt)
            logger.addHandler(fh)

            self.logger = logger
            self._log_active = True

            sys.stdout = _StreamToLogger(self.logger, logging.INFO)
            sys.stderr = _StreamToLogger(self.logger, logging.ERROR)

            self._log_header()
            self._log_write_permissions_check()

        except Exception as e:
            try:
                messagebox.showwarning(self.i18n.get("hints.log_init_failed_title"), str(e))
            except (RuntimeError, tk.TclError):
                # Tkinter 弹窗失败，无法通知用户
                pass

    def _log_header(self):
        if not self.logger:
            return
        self.logger.info("========== 程序启动 ==========")
        self.logger.info(f"app_version={APP_VERSION}")
        self.logger.info(f"frozen={getattr(sys, 'frozen', False)}")
        self.logger.info(f"sys.executable={getattr(sys, 'executable', '')}")
        self.logger.info(f"cwd={os.getcwd()}")
        self.logger.info(f"platform={platform.platform()}")
        self.logger.info(f"python={sys.version.replace(os.linesep, ' ')}")
        self.logger.info(f"log_path={self.log_path}")

        # 用户提示（仅一次））
        self.logger.info(f"[HINT] {self.i18n.get('hints.log_header_msg1')}")
        self.logger.info(f"[HINT] {self.i18n.get('hints.log_header_msg2')}")

    def _log_write_permissions_check(self):
        if not self.logger or not self.log_path:
            return
        try:
            test_dir = os.path.dirname(self.log_path)
            test_file = os.path.join(test_dir, "write_test.tmp")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(test_file)
            self.logger.info(f"[WRITE_TEST] OK dir={test_dir}")
        except Exception:
            self.logger.exception("[WRITE_TEST] FAILED (目录不可写/被拦截)")
            self._log_user_hint(
                title=self.i18n.get("hints.log_write_failed_title"),
                cause=self.i18n.get("hints.log_write_failed_cause"),
                action=self.i18n.get("hints.log_write_failed_action"),
                who="USER_ENV",
            )

    def _stop_logger(self, reason: str = ""):
        if not self.logger or not self._log_active:
            return
        try:
            self.logger.info(f"========== 日志结束 {reason} ==========")
            handlers = list(self.logger.handlers)
            for h in handlers:
                try:
                    h.flush()
                    h.close()
                except Exception:
                    pass
                try:
                    self.logger.removeHandler(h)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self._log_active = False
            try:
                sys.stdout = self._orig_stdout
                sys.stderr = self._orig_stderr
            except Exception:
                pass

    def _log(self, msg: str, level: str = "info"):
        if not self.logger:
            return
        try:
            if level == "debug":
                self.logger.debug(msg)
            elif level == "warning":
                self.logger.warning(msg)
            elif level == "error":
                self.logger.error(msg)
            else:
                self.logger.info(msg)
        except Exception:
            pass

    def _log_user_hint(self, title: str, cause: str, action: str, who: str = "UNKNOWN"):
        # who:
        self._log(f"[HINT] {title}")
        self._log(f"[CAUSE] ({who}) {cause}")
        self._log(f"[ACTION] {action}")

    # ===== 日志 =====
    def _now(self) -> float:
        return time.perf_counter()

    def _hotkey_debounced(self, name: str) -> bool:
        # True=允许触发；False=本次忽略（防抖）
        now = self._now()
        last = self._hotkey_last_ts.get(name, 0.0)
        if (now - last) * 1000.0 < float(self._hotkey_cooldown_ms):
            self._log(f"HOTKEY ignored (cooldown): name={name}", level="debug")
            return False
        self._hotkey_last_ts[name] = now
        return True

    def _hotkey_log(self, name: str):
        self._log(
            f"HOTKEY fired: name={name} backend={self.hotkey_backend.get()} "
            f"mode={self.mode} is_armed={self.is_armed} in_trial={self.in_trial} "
            f"mag_index={self.mag_index} rep_index={self.rep_index}"
        )

    def _ensure_scan_code(self, name: str, current_sc: int | None) -> int | None:
        # 解决：数字/符号键在 keyboard_name 捕获后被自动切到 keyboard_scan，但没有 scan_code -> 热键无法触发
        if current_sc is not None:
            return current_sc
        try:
            codes = keyboard.key_to_scan_codes(name)
            if codes:
                return int(codes[0])
        except Exception:
            pass
        self._log(f"scan code resolve failed for '{name}'", level="warning")
        return None

    def _on_hotkey_start(self):
        self._hotkey_log("start")
        if not self._hotkey_debounced("start"):
            return

        # 若尚未开启手柄模拟，自动开启（但不提前改测试状态）
        if not self.emu_enabled or self.gamepad is None:
            self.enable_emulation()

        # 交给 start_test 正常进入流程（内部会设置 is_armed/mode）
        self.start_test()

    def _on_hotkey_record(self):
        self._hotkey_log("record")
        if not self._hotkey_debounced("record"):
            return
        self.on_record_key()

    def _on_hotkey_deadzone(self):
        self._hotkey_log("deadzone+")
        if not self._hotkey_debounced("deadzone+"):
            return
        self.on_deadzone_key()

    def _on_hotkey_deadzone_back(self):
        self._hotkey_log("deadzone-")
        if not self._hotkey_debounced("deadzone-"):
            return
        self.on_deadzone_back_key()

    def _on_hotkey_end_deadzone(self):
        self._hotkey_log("end_deadzone")
        if not self._hotkey_debounced("end_deadzone"):
            return
        self.on_end_deadzone_key()

    def _on_hotkey_retry_last(self):
        self._hotkey_log("retry_last")
        if not self._hotkey_debounced("retry_last"):
            return
        self.on_retry_last_key()

    # ===== 热键 =====
    def _sanitize_hotkey_name(self, hk: str, fallback: str) -> str:
        # keyboard.add_hotkey 只吃键名，不吃 'scan code 5' 这种字符串；遇到就回退。
        hk = (hk or "").strip()
        if not hk:
            return fallback
        if hk.lower().startswith("scan code"):
            self._log(f"hotkey '{hk}' is scan-code style -> fallback '{fallback}'", level="warning")
            return fallback
        return hk.lower()

    def _is_symbol_or_digit_single_key(self, hk_name: str) -> bool:
        # 判断：是否为单字符数字/符号键（触发强制 scan 模式）
        hk_name = (hk_name or "").strip()
        if len(hk_name) != 1:
            return False
        ch = hk_name
        if ch.isdigit():
            return True
        if ch in r"""`~!@#$%^&*()-_=+[]{}\|;:'",.<>/?""":
            return True
        return False

    def _all_hotkey_names(self):
        return [self.start_key, self.record_key, self.deadzone_key, self.deadzone_back_key, self.end_deadzone_key, self.retry_last_key]

    def _auto_select_backend(self, reason: str = ""):
        # - 只要任何热键绑定到数字/符号单字符 => keyboard_scan
        names = [((x or "").strip().lower()) for x in self._all_hotkey_names()]
        has_symbol_digit = any(self._is_symbol_or_digit_single_key(x) for x in names)

        old = self.hotkey_backend.get()

        if has_symbol_digit:
            if old != "keyboard_scan":
                self.hotkey_backend.set("keyboard_scan")
                self._install_scan_hook()
                self._log(f"auto-switch backend -> keyboard_scan (symbol/digit detected) reason={reason}", level="warning")
            self._update_hotkey_hint(has_symbol_digit=True)
            return

        if old != "keyboard_name":
            self.hotkey_backend.set("keyboard_name")
            self._log(f"auto-switch backend -> keyboard_name (no symbol/digit) reason={reason}", level="info")

        self._update_hotkey_hint(has_symbol_digit=False)

    def _update_hotkey_hint(self, has_symbol_digit: bool | None = None):
        if has_symbol_digit is None:
            names = [((x or "").strip().lower()) for x in self._all_hotkey_names()]
            has_symbol_digit = any(self._is_symbol_or_digit_single_key(x) for x in names)

        if has_symbol_digit:
            self.hotkey_compat_hint.set(self.i18n.get("ui.hotkey_hint_symbol"))
        else:
            self.hotkey_compat_hint.set(self.i18n.get("ui.hotkey_hint_normal"))

        if self.lbl_hotkey_hint is not None:
            try:
                self.lbl_hotkey_hint.configure(textvariable=self.hotkey_compat_hint)
            except (RuntimeError, tk.TclError):
                # Tkinter 控件配置失败，继续执行
                pass

    # ===== 热键 =====
    def _install_scan_hook(self):
        if self._scan_hook_installed:
            return

        def _hook_cb(e):
            try:
                if e.event_type != "up":  # 抬起触发，避免长按连发
                    return
                sc = getattr(e, "scan_code", None)
                if sc is None:
                    return

                if self.start_scan is not None and sc == self.start_scan:
                    self.after(0, self._on_hotkey_start)
                    return
                if self.record_scan is not None and sc == self.record_scan:
                    self.after(0, self._on_hotkey_record)
                    return
                if self.deadzone_scan is not None and sc == self.deadzone_scan:
                    self.after(0, self._on_hotkey_deadzone)
                    return
                if self.deadzone_back_scan is not None and sc == self.deadzone_back_scan:
                    self.after(0, self._on_hotkey_deadzone_back)
                    return
                if self.end_deadzone_scan is not None and sc == self.end_deadzone_scan:
                    self.after(0, self._on_hotkey_end_deadzone)
                    return
                if self.retry_last_scan is not None and sc == self.retry_last_scan:
                    self.after(0, self._on_hotkey_retry_last)
                    return
            except Exception:
                pass

        keyboard.hook(_hook_cb)
        self._scan_hook_installed = True
        self._log("keyboard_scan: hook installed")

    def _unregister_name_hotkeys(self):
        for h in [
            self.hotkey_start,
            self.hotkey_record,
            self.hotkey_deadzone,
            self.hotkey_deadzone_back,
            self.hotkey_end_deadzone,
            self.hotkey_retry_last,
        ]:
            if h is not None:
                try:
                    keyboard.remove_hotkey(h)
                except Exception:
                    pass
        self.hotkey_start = None
        self.hotkey_record = None
        self.hotkey_deadzone = None
        self.hotkey_deadzone_back = None
        self.hotkey_end_deadzone = None
        self.hotkey_retry_last = None

    def _register_hotkeys(self):
        # 测试中禁止改热键
        if self.is_armed or self._test_running or self.mode != "idle":
            self._log("register_hotkeys blocked: test is running", level="warning")
            self._log_user_hint(
                title="测试过程中无法重绑热键",
                cause="你正在测试/计时，重绑热键可能导致热键突然失效（用户操作问题）",
                action="先点击【停止/重置】，再修改热键。",
                who="USER_OP",
            )
            return

        self._auto_select_backend(reason="register_hotkeys")

        backend = (self.hotkey_backend.get() or "keyboard_name").strip()
        self._log(f"register_hotkeys: backend={backend}")

        self._unregister_name_hotkeys()

        if backend == "keyboard_scan":
            # 若此前在 keyboard_name 模式绑定了数字/符号，切换到 scan 时补全 scan_code
            self.start_scan = self._ensure_scan_code(self.start_key, self.start_scan)
            self.record_scan = self._ensure_scan_code(self.record_key, self.record_scan)
            self.deadzone_scan = self._ensure_scan_code(self.deadzone_key, self.deadzone_scan)
            self.deadzone_back_scan = self._ensure_scan_code(self.deadzone_back_key, self.deadzone_back_scan)
            self.end_deadzone_scan = self._ensure_scan_code(self.end_deadzone_key, self.end_deadzone_scan)
            self.retry_last_scan = self._ensure_scan_code(self.retry_last_key, self.retry_last_scan)
            self._install_scan_hook()
            return

        # ===== 键名模式 =====
        start = self._sanitize_hotkey_name(self.start_key, "f6")
        record = self._sanitize_hotkey_name(self.record_key, "f9")
        dzp = self._sanitize_hotkey_name(self.deadzone_key, "f10")
        dzm = self._sanitize_hotkey_name(self.deadzone_back_key, "f11")
        dzend = self._sanitize_hotkey_name(self.end_deadzone_key, "f12")
        retry = self._sanitize_hotkey_name(self.retry_last_key, "f7")

        self.start_key = start
        self.record_key = record
        self.deadzone_key = dzp
        self.deadzone_back_key = dzm
        self.end_deadzone_key = dzend
        self.retry_last_key = retry
        if self.lbl_keys is not None:
            self.lbl_keys.configure(text=self._keys_text())

        def _wrap(fn):
            # keyboard 期望 callback 返回 None/bool，这里显式返回 None
            def _inner():
                self.after(0, fn)
                return None

            return _inner

        try:
            self.hotkey_start = keyboard.add_hotkey(
                start, _wrap(self._on_hotkey_start), trigger_on_release=True
            )
            self.hotkey_record = keyboard.add_hotkey(
                record, _wrap(self._on_hotkey_record), trigger_on_release=True
            )
            self.hotkey_deadzone = keyboard.add_hotkey(
                dzp, _wrap(self._on_hotkey_deadzone), trigger_on_release=True
            )
            self.hotkey_deadzone_back = keyboard.add_hotkey(
                dzm, _wrap(self._on_hotkey_deadzone_back), trigger_on_release=True
            )
            self.hotkey_end_deadzone = keyboard.add_hotkey(
                dzend, _wrap(self._on_hotkey_end_deadzone), trigger_on_release=True
            )
            self.hotkey_retry_last = keyboard.add_hotkey(
                retry, _wrap(self._on_hotkey_retry_last), trigger_on_release=True
            )
        except Exception as e:
            # 异常要兜底
            self._log(f"register_hotkeys FAILED: {repr(e)}", level="error")
            self._log_user_hint(
                title=self.i18n.get("hints.hotkey_capture_fail_title"),
                cause=self.i18n.get("hints.hotkey_capture_fail_cause"),
                action=self.i18n.get("hints.hotkey_capture_fail_action"),
                who="USER_ENV",
            )

            # 自动切 scan
            self.hotkey_backend.set("keyboard_scan")
            self._install_scan_hook()

            self.hotkey_compat_hint.set(self.i18n.get("ui.hotkey_hint_failed"))
            if self.lbl_hotkey_hint is not None:
                try:
                    self.lbl_hotkey_hint.configure(textvariable=self.hotkey_compat_hint)
                except Exception:
                    pass

            self.status.set(self.i18n.get("messages.hotkey_registration_failed"))

    def _on_hotkey_backend_changed(self, _event=None):
        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set(self.i18n.get("messages.hotkey_mode_forbidden"))
            return

        self._auto_select_backend(reason="user_changed_backend")
        self._register_hotkeys()
        self.status.set(self.i18n.get("messages.hotkey_mode_changed").format(mode=self.hotkey_backend.get()))

    # ===== UI =====
    def _build_ui(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text=self.i18n.get("ui.left_stick"), font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=0, pady=(0, 6))
        ttk.Label(left, text=self.i18n.get("ui.right_stick"), font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=1, pady=(0, 6))

        self.left_stick = VirtualStick(left, size=360)
        self.right_stick = VirtualStick(left, size=360)
        self.left_stick.grid(row=1, column=0, padx=8, pady=8, sticky="n")
        self.right_stick.grid(row=1, column=1, padx=8, pady=8, sticky="n")

        info = ttk.LabelFrame(left, text=self.i18n.get("ui.info_title"))
        info.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=(10, 0))
        info.columnconfigure(0, weight=1)
        info.rowconfigure(1, weight=1)

        self.lbl_status = ttk.Label(info, textvariable=self.status, justify="left")
        self.lbl_status.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.lbl_tip = ttk.Label(
            info,
            justify="left",
            foreground="#333",
            text=self.i18n.get("ui.info_description"),
        )
        self.lbl_tip.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        right_scroll = ScrollableFrame(root)
        right_scroll.grid(row=0, column=1, sticky="nsew")
        right = right_scroll.inner
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text=self.i18n.get("ui.settings_panel"), font=("Microsoft YaHei", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10), padx=6)

        # ===== 语言选择 =====
        lang_frm = ttk.LabelFrame(right, text=self.i18n.get("ui.language_select"))
        lang_frm.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=6)
        lang_frm.columnconfigure(0, weight=1)
        
        ttk.Label(lang_frm, text=self.i18n.get("ui.language_label")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        available_langs = self.i18n.get_available_languages()
        lang_codes = sorted(available_langs.keys())
        lang_names = [available_langs[code] for code in lang_codes]
        
        # 保存语言代码映射
        self._lang_name_to_code = {available_langs[code]: code for code in lang_codes}
        self._lang_code_to_name = {code: available_langs[code] for code in lang_codes}
        
        self.cmb_language = ttk.Combobox(
            lang_frm, 
            values=lang_names, 
            state="readonly", 
            width=25,
            textvariable=self.current_language_name
        )
        self.cmb_language.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        
        # 获取当前语言代码并设置下拉框初始选择
        current_lang_code = self.i18n.current_lang
        current_lang_name = self._lang_code_to_name.get(current_lang_code, available_langs.get("zh_CN", "中文（简体）"))
        self.current_language_name.set(current_lang_name)
        if current_lang_code in lang_codes:
            self.cmb_language.current(lang_codes.index(current_lang_code))
        else:
            self.cmb_language.current(0)
        
        self.cmb_language.bind("<<ComboboxSelected>>", lambda e: self._on_language_changed(lang_codes))

        padfrm = ttk.LabelFrame(right, text=self.i18n.get("ui.gamepad"))
        padfrm.grid(row=2, column=0, sticky="ew", pady=(0, 10), padx=6)
        padfrm.columnconfigure(0, weight=1)

        ttk.Label(padfrm, text=self.i18n.get("ui.gamepad_type")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        self.cmb_pad = ttk.Combobox(padfrm, values=["ds4", "xbox360"], state="readonly", width=18, textvariable=self.gamepad_type)
        self.cmb_pad.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))

        btnrow = ttk.Frame(padfrm)
        btnrow.grid(row=2, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(btnrow, text=self.i18n.get("ui.enable_emulation"), command=self.enable_emulation).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btnrow, text=self.i18n.get("ui.neutral"), command=self.neutral_only).grid(row=0, column=1)

        self.lbl_emu = ttk.Label(padfrm, text=self.i18n.get("ui.status") + self.i18n.get("ui.status_disabled"), foreground="#aa0000")
        self.lbl_emu.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        frm = ttk.LabelFrame(right, text=self.i18n.get("ui.test_params"))
        frm.grid(row=3, column=0, sticky="ew", pady=(0, 10), padx=6)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text=self.i18n.get("ui.sample_count")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(frm, width=10, textvariable=self.sample_count).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(frm, text=self.i18n.get("ui.repeats_per_mag")).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))
        ttk.Spinbox(frm, from_=1, to=50, width=10, textvariable=self.repeats_per_mag).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(frm, text=self.i18n.get("ui.magnitude_range")).grid(row=4, column=0, sticky="w", padx=8, pady=(0, 2))
        rng = ttk.Frame(frm)
        rng.grid(row=5, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rng, text=self.i18n.get("ui.min")).grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rng, width=8, textvariable=self.min_mag).grid(row=0, column=1)
        ttk.Label(rng, text=self.i18n.get("ui.max")).grid(row=0, column=2, padx=(12, 6))
        ttk.Entry(rng, width=8, textvariable=self.max_mag).grid(row=0, column=3)

        ttk.Label(frm, text=self.i18n.get("ui.test_direction")).grid(row=6, column=0, sticky="w", padx=8, pady=(0, 2))
        dirfrm = ttk.Frame(frm)
        dirfrm.grid(row=7, column=0, sticky="w", padx=8, pady=(0, 8))
        direction_labels = {
            "right": self.i18n.get("ui.direction_right"),
            "left": self.i18n.get("ui.direction_left"),
            "up": self.i18n.get("ui.direction_up"),
            "down": self.i18n.get("ui.direction_down")
        }
        for i, (val, label) in enumerate([("right", direction_labels["right"]), 
                                           ("left", direction_labels["left"]), 
                                           ("up", direction_labels["up"]), 
                                           ("down", direction_labels["down"])]):
            ttk.Radiobutton(dirfrm, text=label, value=val, variable=self.direction).grid(row=0, column=i, padx=6)

        dzfrm = ttk.LabelFrame(right, text=self.i18n.get("ui.deadzone_params"))
        dzfrm.grid(row=4, column=0, sticky="ew", pady=(0, 10), padx=6)
        dzfrm.columnconfigure(0, weight=1)
        ttk.Label(dzfrm, text=self.i18n.get("ui.deadzone_step")).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(dzfrm, width=10, textvariable=self.deadzone_step).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))
        ttk.Label(dzfrm, text=self.i18n.get("ui.deadzone_back_step")).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))
        ttk.Entry(dzfrm, width=10, textvariable=self.deadzone_back_step).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        axfrm = ttk.LabelFrame(right, text=self.i18n.get("ui.axis_config"))
        axfrm.grid(row=5, column=0, sticky="ew", pady=(0, 10), padx=6)
        axfrm.columnconfigure(0, weight=1)
        rowa = ttk.Frame(axfrm)
        rowa.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 8))
        ttk.Label(rowa, text=self.i18n.get("ui.x_axis_max")).grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rowa, width=10, textvariable=self.x_axis_max).grid(row=0, column=1)
        ttk.Label(rowa, text=self.i18n.get("ui.y_axis_max")).grid(row=0, column=2, padx=(12, 6))
        ttk.Entry(rowa, width=10, textvariable=self.y_axis_max).grid(row=0, column=3)

        kfrm = ttk.LabelFrame(right, text=self.i18n.get("ui.keepalive"))
        kfrm.grid(row=6, column=0, sticky="ew", pady=(0, 10), padx=6)
        kfrm.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            kfrm,
            text=self.i18n.get("ui.keepalive_enable"),
            variable=self.keepalive_enabled,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        rowk = ttk.Frame(kfrm)
        rowk.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rowk, text=self.i18n.get("ui.keepalive_interval")).grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rowk, width=8, textvariable=self.keepalive_interval_ms).grid(row=0, column=1)

        ttk.Label(rowk, text=self.i18n.get("ui.keepalive_button")).grid(row=0, column=2, padx=(12, 6))
        keepalive_buttons = [
            self.i18n.get("ui.button_square"),
            self.i18n.get("ui.button_cross"),
            self.i18n.get("ui.button_circle"),
            self.i18n.get("ui.button_triangle"),
            self.i18n.get("ui.button_l1"),
            self.i18n.get("ui.button_r1"),
            self.i18n.get("ui.button_share"),
            self.i18n.get("ui.button_options"),
        ]
        ttk.Combobox(
            rowk,
            values=keepalive_buttons,
            textvariable=self.keepalive_btn_name,
            width=14,
            state="readonly",
        ).grid(row=0, column=3)

        hfrm = ttk.LabelFrame(right, text=self.i18n.get("ui.hold"))
        hfrm.grid(row=7, column=0, sticky="ew", pady=(0, 10), padx=6)
        hfrm.columnconfigure(0, weight=1)

        ttk.Checkbutton(hfrm, text=self.i18n.get("ui.hold_enable"), variable=self.hold_enabled).grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4)
        )

        rowh = ttk.Frame(hfrm)
        rowh.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rowh, text=self.i18n.get("ui.hold_key")).grid(row=0, column=0, padx=(0, 6))
        hold_buttons = [
            self.i18n.get("ui.trigger_l2"),
            self.i18n.get("ui.trigger_r2"),
            self.i18n.get("ui.button_l1"),
            self.i18n.get("ui.button_r1"),
            self.i18n.get("ui.button_square"),
            self.i18n.get("ui.button_cross"),
            self.i18n.get("ui.button_circle"),
            self.i18n.get("ui.button_triangle"),
        ]
        ttk.Combobox(
            rowh,
            values=hold_buttons,
            textvariable=self.hold_key_name,
            width=16,
            state="readonly",
        ).grid(row=0, column=1)

        # ===== 热键 =====
        hot = ttk.LabelFrame(right, text=self.i18n.get("ui.hotkey"))
        hot.grid(row=8, column=0, sticky="ew", pady=(0, 10), padx=6)
        hot.columnconfigure(0, weight=1)

        hk_backend_frm = ttk.Frame(hot)
        hk_backend_frm.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        hk_backend_frm.columnconfigure(2, weight=1)

        ttk.Label(hk_backend_frm, text=self.i18n.get("ui.hotkey_mode")).grid(row=0, column=0, sticky="w")
        self.cmb_hotkey_backend = ttk.Combobox(
            hk_backend_frm,
            values=["keyboard_name", "keyboard_scan"],
            textvariable=self.hotkey_backend,
            width=16,
            state="normal",
        )
        self.cmb_hotkey_backend.grid(row=0, column=1, sticky="w", padx=(8, 12))
        self.cmb_hotkey_backend.bind("<<ComboboxSelected>>", self._on_hotkey_backend_changed)

        self._update_hotkey_hint()
        self.lbl_hotkey_hint = ttk.Label(
            hot,
            textvariable=self.hotkey_compat_hint,
            foreground="#555",
            justify="left",
        )
        self.lbl_hotkey_hint.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))

        self.lbl_keys = ttk.Label(hot, text=self._keys_text(), justify="left")
        self.lbl_keys.grid(row=2, column=0, sticky="w", padx=8, pady=(0, 6))

        btns = ttk.Frame(hot)
        btns.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)

        row1 = ttk.Frame(btns)
        row1.grid(row=0, column=0, sticky="ew", columnspan=3)
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)
        row1.columnconfigure(2, weight=1)
        ttk.Button(row1, text=self.i18n.get("ui.set_start_key"), command=self.capture_start_key).grid(row=0, column=0, padx=(0, 4), pady=(0, 6), sticky="ew")
        ttk.Button(row1, text=self.i18n.get("ui.set_record_key"), command=self.capture_record_key).grid(row=0, column=1, padx=(2, 2), pady=(0, 6), sticky="ew")
        ttk.Button(row1, text=self.i18n.get("ui.set_deadzone_key"), command=self.capture_deadzone_key).grid(row=0, column=2, padx=(4, 0), pady=(0, 6), sticky="ew")

        row2 = ttk.Frame(btns)
        row2.grid(row=1, column=0, sticky="ew", columnspan=3)
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)
        row2.columnconfigure(2, weight=1)
        ttk.Button(row2, text=self.i18n.get("ui.set_deadzone_back_key"), command=self.capture_deadzone_back_key).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ttk.Button(row2, text=self.i18n.get("ui.set_end_deadzone_key"), command=self.capture_end_deadzone_key).grid(row=0, column=1, padx=(2, 2), sticky="ew")
        ttk.Button(row2, text=self.i18n.get("ui.set_retry_key"), command=self.capture_retry_last_key).grid(row=0, column=2, padx=(4, 0), sticky="ew")

        ctr = ttk.LabelFrame(right, text=self.i18n.get("ui.control"))
        ctr.grid(row=9, column=0, sticky="ew", pady=(0, 10), padx=6)
        ctr.columnconfigure(0, weight=1)
        ctr.columnconfigure(1, weight=1)
        cbtn = ttk.Frame(ctr)
        cbtn.grid(row=0, column=0, sticky="ew", padx=8, pady=8, columnspan=2)
        cbtn.columnconfigure(0, weight=1)
        cbtn.columnconfigure(1, weight=1)
        ttk.Button(cbtn, text=self.i18n.get("ui.start_test"), command=self.start_test).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ttk.Button(cbtn, text=self.i18n.get("ui.stop_reset"), command=self.reset_test).grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # ===== 导出与图表 =====
        charts = ttk.LabelFrame(right, text=self.i18n.get("ui.export_and_charts"))
        charts.grid(row=10, column=0, sticky="ew", pady=(0, 10), padx=6)
        charts.columnconfigure(0, weight=1)
        charts.columnconfigure(1, weight=1)
        ttk.Button(charts, text=self.i18n.get("ui.generate_charts"), command=self.generate_charts_from_current).grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=8)
        ttk.Button(charts, text=self.i18n.get("ui.generate_from_csv"), command=self.generate_charts_from_csv).grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=8)

        ttk.Label(
            right,
            text=self.i18n.get("ui.author_footer").format(author=APP_AUTHOR, version=APP_VERSION),
            foreground="#888",
            font=("Microsoft YaHei", 9),
        ).grid(row=11, column=0, sticky="w", padx=10, pady=(0, 16))

    def _refresh_wraplengths(self):
        try:
            w = max(420, self.winfo_width() // 2 - 40)
            if self.lbl_status is not None:
                self.lbl_status.configure(wraplength=w)
            if self.lbl_tip is not None:
                self.lbl_tip.configure(wraplength=w)
            if self.lbl_hotkey_hint:
                self.lbl_hotkey_hint.configure(wraplength=max(320, self.winfo_width() // 2 - 80))
        except (RuntimeError, tk.TclError):
            # UI 尚未初始化，跳过此轮更新
            pass
        self.after(350, self._refresh_wraplengths)

    # ===== 手柄模拟 =====
    def enable_emulation(self):
        self._log(f"enable_emulation: request kind={self.gamepad_type.get()}")
        if self.emu_enabled and self.gamepad is not None:
            self.status.set(self.i18n.get("messages.emulation_already_on"))
            self._log("enable_emulation: already enabled (no restart).")
            return
        try:
            self.gamepad = VirtualGamepad(kind=self.gamepad_type.get())
        except Exception as e:
            self._log(f"enable_emulation: FAIL err={repr(e)}", level="error")
            self._log_user_hint(
                title=self.i18n.get("hints.enable_gamepad_fail_title"),
                cause=self.i18n.get("hints.enable_gamepad_fail_cause"),
                action=self.i18n.get("hints.enable_gamepad_fail_action"),
                who="USER_ENV",
            )
            messagebox.showerror(self.i18n.get("hints.enable_gamepad_fail_dialog"), str(e))
            return
        self.emu_enabled = True
        if self.lbl_emu is not None:
            self.lbl_emu.configure(text=f"状态：已开启（{self.gamepad_type.get()}）", foreground="#008800")
        self.status.set(self.i18n.get("messages.emulation_enabled"))
        if self.cmb_pad is not None:
            self.cmb_pad.configure(state="disabled")
        self._log("enable_emulation: SUCCESS")

    def neutral_only(self):
        self._log("neutral_only")
        if not self.emu_enabled or self.gamepad is None:
            self.status.set(self.i18n.get("messages.emulation_not_enabled"))
            self._log("neutral_only: ignored (emu not enabled).", level="warning")
            return
        try:
            self.gamepad.neutral()
        except Exception as e:
            self._log(f"neutral_only: gamepad.neutral exception: {type(e).__name__}", level="warning")
        if self.left_stick is not None:
            self.left_stick.set_value(0.0, 0.0)
        if self.right_stick is not None:
            self.right_stick.set_value(0.0, 0.0)
        self._hold_applied = False
        self.status.set(self.i18n.get("messages.neutral_done"))

    def _on_language_changed(self, lang_codes):
        """语言选择变化回调"""
        selected_name = self.cmb_language.get()
        lang_code = self._lang_name_to_code.get(selected_name, "zh_CN")
        
        # 设置新语言
        self.i18n.set_language(lang_code)
        self.current_language_name.set(selected_name)
        
        self._log(f"Language changed to: {lang_code}")
        
        # 重新构建 UI 以应用新语言
        try:
            for widget in self.winfo_children():
                widget.destroy()
            
            # 重新构建 UI
            self._build_ui()
            
            # 重新绑定快捷键
            self.bind_all("<Key>", self._on_any_key)
            self.after(250, self._refresh_wraplengths)
            
            # 更新状态栏为新语言的初始提示
            self.status.set(self.i18n.get("messages.initial_hint"))
            
            self._log(f"UI rebuilt for language: {lang_code}")
        except Exception as e:
            self._log(f"UI rebuild error: {e}", level="error")
            # 降级：只更新 i18n，不重建 UI
            self.status.set(self.i18n.get("hints.language_switched_status").format(lang_code=lang_code))

    # ===== 热键 =====
    def _keys_text(self):
        return self.i18n.get("ui.hotkey_keys_label").format(
            start_key=self.start_key,
            record_key=self.record_key,
            retry_key=self.retry_last_key,
            deadzone_key=self.deadzone_key,
            deadzone_back_key=self.deadzone_back_key,
            end_deadzone_key=self.end_deadzone_key,
            mode=self.hotkey_backend.get()
        )

    def capture_start_key(self):
        self.capture_mode = "start"
        self._begin_capture()

    def capture_record_key(self):
        self.capture_mode = "record"
        self._begin_capture()

    def capture_deadzone_key(self):
        self.capture_mode = "deadzone"
        self._begin_capture()

    def capture_deadzone_back_key(self):
        self.capture_mode = "deadzone_back"
        self._begin_capture()

    def capture_end_deadzone_key(self):
        self.capture_mode = "end_deadzone"
        self._begin_capture()

    def capture_retry_last_key(self):
        self.capture_mode = "retry_last"
        self._begin_capture()

    def _begin_capture(self):
        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set(self.i18n.get("messages.hotkey_capture_forbidden"))
            self._log("hotkey capture blocked: test is running", level="warning")
            self._log_user_hint(
                title="尝试在测试中改热键",
                cause="测试中改热键会导致热键触发异常/丢失（用户操作问题）",
                action="先停止/重置，再设置热键。",
                who="USER_OP",
            )
            self.capture_mode = None
            return

        self.status.set(self.i18n.get("messages.hotkey_capture_waiting"))

        backend = (self.hotkey_backend.get() or "keyboard_name").strip()
        self.capture_target_backend = backend

        if backend == "keyboard_scan":
            self.status.set(self.i18n.get("messages.hotkey_capture_scan"))
            self._start_scan_capture_thread()
        else:
            self.status.set(self.i18n.get("messages.hotkey_capture_name"))

    def _start_scan_capture_thread(self):
        if self._scan_capture_thread and self._scan_capture_thread.is_alive():
            return

        def _worker():
            try:
                e = keyboard.read_event()
                if e.event_type != "up":
                    e2 = keyboard.read_event()
                    if e2:
                        e = e2
                sc = getattr(e, "scan_code", None)
                nm = getattr(e, "name", None)
                if sc is None:
                    return

                def _apply():
                    if self.capture_mode is None:
                        return
                    show_name = (nm or f"scan:{sc}").lower()
                    self._apply_captured_hotkey(show_name, sc)

                self.after(0, _apply)
            except Exception as ex:
                self._log(f"scan capture exception: {repr(ex)}", level="warning")
                self._log_user_hint(
                    title=self.i18n.get("hints.hotkey_capture_fail_title"),
                    cause=self.i18n.get("hints.hotkey_capture_fail_cause"),
                    action=self.i18n.get("hints.hotkey_capture_fail_action"),
                    who="USER_ENV",
                )

        self._scan_capture_thread = threading.Thread(target=_worker, daemon=True)
        self._scan_capture_thread.start()

    def _apply_captured_hotkey(self, hk_name: str, scan_code: int | None):
        mode = self.capture_mode
        self.capture_mode = None

        hk_name = (hk_name or "").strip().lower()
        sc = int(scan_code) if scan_code is not None else None

        if mode == "start":
            self.start_key = hk_name
            self.start_scan = sc
        elif mode == "record":
            self.record_key = hk_name
            self.record_scan = sc
        elif mode == "deadzone":
            self.deadzone_key = hk_name
            self.deadzone_scan = sc
        elif mode == "deadzone_back":
            self.deadzone_back_key = hk_name
            self.deadzone_back_scan = sc
        elif mode == "end_deadzone":
            self.end_deadzone_key = hk_name
            self.end_deadzone_scan = sc
        elif mode == "retry_last":
            self.retry_last_key = hk_name
            self.retry_last_scan = sc

        self._auto_select_backend(reason=f"capture_{mode}")

        if self.lbl_keys is not None:
            self.lbl_keys.configure(text=self._keys_text())
        self._register_hotkeys()

        self.status.set(self.i18n.get("messages.hotkey_updated"))
        self._log(f"hotkeys updated: {self._keys_text()}")

        if self._is_symbol_or_digit_single_key(hk_name):
            self._log_user_hint(
                title="Symbol or digit key detected",
                cause="Symbol/digit keys often have compatibility issues in keyboard_name mode (not a code bug, but a common environment limitation)",
                action="Auto-switched to keyboard_scan; if you want to return to keyboard_name mode, change these keys to F-keys/letters.",
                who="USER_ENV",
            )

    def _on_any_key(self, event):
        if self.capture_mode is None:
            return
        if self.capture_target_backend != "keyboard_name":
            return

        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set(self.i18n.get("messages.hotkey_capture_forbidden"))
            self._log("hotkey capture blocked: test is running", level="warning")
            self.capture_mode = None
            return

        hk = tk_event_to_hotkey(event)
        if not hk:
            return

        self._apply_captured_hotkey(hk, None)

    # ===== 参数 =====
    def _parse_sample_count(self) -> int:
        s = (self.sample_count.get() or "").strip()
        try:
            n = int(s)
        except (ValueError, TypeError):
            raise ValueError(self.i18n.get("errors.sample_count_invalid_type"))
        if n < 2 or n > 100:
            raise ValueError(self.i18n.get("errors.sample_count_out_of_range"))
        return n

    def _validate_ranges(self):
        try:
            mn = float(self.min_mag.get())
            mx = float(self.max_mag.get())
        except (ValueError, TypeError) as e:
            self._log(f"Invalid magnitude range values: {e}", level="error")
            raise ValueError(self.i18n.get("errors.magnitude_range_invalid"))
        if not (0.0 <= mn < mx <= 1.0):
            raise ValueError(self.i18n.get("errors.magnitude_range_invalid"))
        return mn, mx

    def build_measure_magnitudes(self, measure_points: int, deadzone: float):
        mn, mx = self._validate_ranges()
        deadzone = float(deadzone)

        if measure_points <= 0:
            return []

        start = mn
        if deadzone > 0:
            start = max(mn, deadzone)

        if measure_points == 1:
            return [round(mx, 4)]

        step = (mx - start) / (measure_points - 1)
        mags = [round(start + i * step, 4) for i in range(measure_points)]
        mags[-1] = round(mx, 4)
        return mags

    # ===== 测试 =====
    def start_test(self):
        if self._test_running or self.is_armed or self.mode != "idle":
            self._log(f"start_test ignored: already running mode={self.mode} is_armed={self.is_armed}", level="warning")
            return

        with self._start_guard_lock:
            if self._test_running or self.is_armed or self.mode != "idle":
                self._log(f"start_test ignored (lock): already running mode={self.mode} is_armed={self.is_armed}", level="warning")
                return
            self._test_running = True

        self._log("start_test: begin")
        self._log(
            f"params: sample_count(measure)={self.sample_count.get()} repeats={self.repeats_per_mag.get()} "
            f"min={self.min_mag.get()} max={self.max_mag.get()} dir={self.direction.get()}"
        )

        try:
            if not (self.emu_enabled and self.gamepad):
                messagebox.showwarning(self.i18n.get("hints.no_emulation_start_dialog_title"), self.i18n.get("hints.no_emulation_start_dialog_msg"))
                self._log("start_test: blocked (emu not enabled).", level="warning")
                self._log_user_hint(
                    title=self.i18n.get("hints.no_emulation_start_title"),
                    cause=self.i18n.get("hints.no_emulation_start_cause"),
                    action=self.i18n.get("hints.no_emulation_start_action"),
                    who="USER_OP",
                )
                return

            try:
                _ = self._parse_sample_count()
                _ = self._validate_ranges()
            except Exception as e:
                self._log(f"start_test: param error {repr(e)}", level="error")
                self._log_user_hint(
                    title=self.i18n.get("hints.param_error_title"),
                    cause=self.i18n.get("hints.param_error_cause"),
                    action=self.i18n.get("hints.param_error_action"),
                    who="USER_OP",
                )
                messagebox.showerror(self.i18n.get("hints.param_error_dialog"), str(e))
                return

            self.is_armed = True
            self.in_trial = False
            self.t0 = None
            self.mag_index = 0
            self.rep_index = 0
            self.results = []

            self.mode = "deadzone"
            self.deadzone_current_m = 0.0
            self.deadzone_mag = 0.0
            self.allow_adjust_after_deadzone = True
            self._hold_applied = False

            step = float(self.deadzone_step.get())
            if step <= 0:
                step = 0.02
            self.deadzone_current_m = max(0.0, min(1.0, step))
            self._apply_test_stick(self.deadzone_current_m)

            self._log(f"start_test: enter deadzone, m={self.deadzone_current_m:.4f}")

            msg = self.i18n.get("messages.test_started").format(
                magnitude=self.deadzone_current_m
            )
            self.status.set(msg)
        finally:
            if not self.is_armed:
                self._test_running = False

    def reset_test(self):
        self._log("reset_test")
        self._test_running = False

        self.is_armed = False
        self.in_trial = False
        self.t0 = None
        self.mode = "idle"
        self.mag_index = 0
        self.rep_index = 0
        self.results = []

        self.deadzone_current_m = 0.0
        self.deadzone_mag = 0.0
        self.allow_adjust_after_deadzone = True

        if self.right_stick is not None:
            self.right_stick.set_value(0.0, 0.0)

        try:
            if self.gamepad:
                self.gamepad.release_hold()
        except Exception:
            self._log("reset_test: release_hold exception", level="warning")
        self._hold_applied = False

        self.status.set(self.i18n.get("messages.test_stopped"))
        # v1.6: 日志仅 on_close 停止）

    # ===== 死区 =====
    def on_deadzone_key(self):
        if not self.is_armed:
            return
        if self.mode not in ("deadzone", "curve"):
            return
        if self.mode == "curve" and not self._can_adjust_deadzone_in_curve():
            return

        step = float(self.deadzone_step.get())
        if step <= 0:
            step = 0.02

        self.deadzone_current_m = min(1.0, float(self.deadzone_current_m) + step)
        self._apply_test_stick(self.deadzone_current_m)
        self._log(f"deadzone +step => m={self.deadzone_current_m:.4f} mode={self.mode}")

        if self.mode == "deadzone":
            msg = self.i18n.get("messages.deadzone_increased").format(
                magnitude=self.deadzone_current_m
            )
            self.status.set(msg)
        else:
            msg = self.i18n.get("messages.deadzone_adjust").format(
                magnitude=self.deadzone_current_m
            )
            self.status.set(msg)

    def on_deadzone_back_key(self):
        if not self.is_armed:
            return
        if self.mode not in ("deadzone", "curve"):
            return
        if self.mode == "curve" and not self._can_adjust_deadzone_in_curve():
            return

        back = float(self.deadzone_back_step.get())
        if back <= 0:
            back = 0.005

        self.deadzone_current_m = max(0.0, float(self.deadzone_current_m) - back)

        if self.deadzone_current_m <= 0.0:
            self.deadzone_current_m = 0.0
            if self.right_stick is not None:
                self.right_stick.set_value(0.0, 0.0)
        else:
            self._apply_test_stick(self.deadzone_current_m)

        self._log(f"deadzone -back => m={self.deadzone_current_m:.4f} mode={self.mode}")

        if self.mode == "deadzone":
            msg = self.i18n.get("messages.deadzone_decreased").format(
                magnitude=self.deadzone_current_m
            )
            self.status.set(msg)
        else:
            msg = self.i18n.get("messages.deadzone_adjust_back").format(
                magnitude=self.deadzone_current_m
            )
            self.status.set(msg)

    def on_end_deadzone_key(self):
        if not self.is_armed:
            return
        if self.mode != "deadzone":
            return

        self.deadzone_mag = float(self.deadzone_current_m)

        measure_points = self._parse_sample_count()
        self.measure_mag_list = self.build_measure_magnitudes(measure_points, self.deadzone_mag)

        self._log(f"end_deadzone: dz={self.deadzone_mag:.4f} measure_points={measure_points}")
        self._log(f"measure_mag_list={self.measure_mag_list}")

        self.mode = "curve"
        self.mag_index = 0
        self.rep_index = 0
        self.in_trial = False
        self.t0 = None

        if self.right_stick is not None:
            self.right_stick.set_value(0.0, 0.0)

        if self.deadzone_mag <= 0.0:
            first_point_text = self.i18n.get("messages.first_point_text_no_deadzone")
        else:
            first_point_text = self.i18n.get("messages.first_point_text_with_deadzone").format(
                magnitude=self.deadzone_mag
            )

        nm = self.measure_mag_list[0] if self.measure_mag_list else float(self.max_mag.get())
        msg = self.i18n.get("messages.deadzone_ended").format(
            first_point_text=first_point_text,
            point_count=len(self.measure_mag_list),
            next_mag=nm
        )
        self.status.set(msg)

    def _can_adjust_deadzone_in_curve(self) -> bool:
        if not self.allow_adjust_after_deadzone:
            return False
        if self.mag_index != 0 or self.rep_index != 0:
            return False
        return True

    # ===== 采样 =====
    def on_record_key(self):
        if not self.is_armed:
            return
        if self.mode != "curve":
            return

        if not self.in_trial:
            self.in_trial = True
            self.t0 = time.perf_counter()
            m = self.measure_mag_list[self.mag_index] if self.measure_mag_list else float(self.max_mag.get())
            self._apply_test_stick(m)

            self._log(f"record START mag_index={self.mag_index} rep={self.rep_index} m={m:.4f}")

            msg = self.i18n.get("messages.record_start").format(
                magnitude=m,
                repeat=self.rep_index + 1,
                total=int(self.repeats_per_mag.get()),
                current=self.mag_index + 1,
                total_points=len(self.measure_mag_list)
            )
            self.status.set(msg)
            return

        t1 = time.perf_counter()
        dt = t1 - (self.t0 or t1)

        m = self.measure_mag_list[self.mag_index] if self.measure_mag_list else float(self.max_mag.get())
        self.results.append({"magnitude": float(m), "repeat_index": int(self.rep_index), "seconds": float(dt), "flag": ""})

        self._log(f"record END mag_index={self.mag_index} rep={self.rep_index} m={m:.4f} dt={dt:.6f}")

        self.rep_index += 1
        self.in_trial = False
        self.t0 = None
        if self.right_stick is not None:
            self.right_stick.set_value(0.0, 0.0)

        if self.mag_index == 0 and self.rep_index >= 1:
            self.allow_adjust_after_deadzone = False

        if self.rep_index >= int(self.repeats_per_mag.get()):
            self.rep_index = 0
            self.mag_index += 1

        self._log(f"progress: next mag_index={self.mag_index} rep_index={self.rep_index} total_points={len(self.measure_mag_list)}")

        if self.measure_mag_list and self.mag_index >= len(self.measure_mag_list):
            self._log("all points done -> finish_and_save")
            self.is_armed = False
            self._finish_and_save()
            return

        nm = self.measure_mag_list[self.mag_index] if self.measure_mag_list else float(self.max_mag.get())
        msg = self.i18n.get("messages.record_saved").format(
            magnitude=m,
            time=dt,
            next_mag=nm,
            current=self.mag_index + 1,
            total_points=len(self.measure_mag_list)
        )
        self.status.set(msg)

    def on_retry_last_key(self):
        # 重新测试上一个点（从头开始，重复设定的次数）
        if not self.is_armed:
            return
        if self.mode != "curve":
            return
        
        # 检查能否重测（至少在第1个点之后）
        if self.mag_index == 0 and self.rep_index == 0:
            self.status.set(self.i18n.get("messages.retry_no_test"))
            self._log("retry_last_key ignored: no test started yet", level="warning")
            return
        
        # 正在计时就先中止
        if self.in_trial:
            self.in_trial = False
            self.t0 = None
            if self.right_stick is not None:
                self.right_stick.set_value(0.0, 0.0)
            self._log("retry_last_key: interrupted ongoing trial")
        
        # 目标重测点：若当前刚进入下一点（rep_index==0），则退回到上一点
        target_index = self.mag_index
        if self.rep_index == 0 and self.mag_index > 0:
            target_index = self.mag_index - 1
        
        # 获取该点幅值
        mag_to_retry = self.measure_mag_list[target_index] if self.measure_mag_list else float(self.max_mag.get())

        # 删除当前点的已有记录（仅当前 magnitude），保留其他点
        self.results = [r for r in self.results if r.get("magnitude") != mag_to_retry]

        # 回到该点的开头
        self.in_trial = False
        self.t0 = None
        self.rep_index = 0
        self.mag_index = target_index
        if self.right_stick is not None:
            self.right_stick.set_value(0.0, 0.0)

        self._log(f"retry_last_key: reset to mag_index={self.mag_index} rep_index=0 m={mag_to_retry:.4f}")

        # 状态提示
        try:
            rc = int(self.repeats_per_mag.get())
        except Exception:
            rc = 1
        self.status.set(
            self.i18n.get("messages.retry_reset_message").format(
                magnitude=mag_to_retry,
                repeat_count=rc,
            )
        )

        # 确保当前点后续还能继续记录（mag_index 不动，只重置 rep_index）
        self.allow_adjust_after_deadzone = False

    def _apply_test_stick(self, m):
        m = float(m)
        d = self.direction.get()
        if self.right_stick is None:
            return
        if d == "right":
            self.right_stick.set_value(m, 0.0)
        elif d == "left":
            self.right_stick.set_value(-m, 0.0)
        elif d == "up":
            self.right_stick.set_value(0.0, m)
        elif d == "down":
            self.right_stick.set_value(0.0, -m)

    # ===== keepalive =====
    def _keepalive_btn_code(self):
        name = (self.keepalive_btn_name.get() or "").strip()
        
        # Build mapping from translated button names
        mapping = {
            self.i18n.get("ui.button_square"): ("square", "x"),
            self.i18n.get("ui.button_cross"): ("cross", "a"),
            self.i18n.get("ui.button_circle"): ("circle", "b"),
            self.i18n.get("ui.button_triangle"): ("triangle", "y"),
            self.i18n.get("ui.button_l1"): ("l1", "lb"),
            self.i18n.get("ui.button_r1"): ("r1", "rb"),
            self.i18n.get("ui.button_share"): ("share", "back"),
            self.i18n.get("ui.button_options"): ("options", "start"),
        }
        ds4_code, x360_code = mapping.get(name, ("square", "x"))
        return ds4_code if self.gamepad_type.get() == "ds4" else x360_code

    def _maybe_keepalive(self):
        if not (self.keepalive_enabled.get() and self.emu_enabled and self.gamepad):
            return
        now = time.perf_counter()
        interval = int(self.keepalive_interval_ms.get() or 120)
        interval = max(40, min(500, interval))
        if (now - self._keepalive_last) * 1000.0 < interval:
            return
        self._keepalive_last = now
        try:
            self.gamepad.tap_keepalive_button(self._keepalive_btn_code(), ms=30)
            self._log(f"keepalive tap ok btn={self._keepalive_btn_code()}", level="debug")
        except Exception:
            self._log("keepalive tap exception", level="warning")
            self._log_user_hint(
                title=self.i18n.get("hints.keepalive_tap_fail_title"),
                cause=self.i18n.get("hints.keepalive_tap_fail_cause"),
                action=self.i18n.get("hints.keepalive_tap_fail_action"),
                who="USER_ENV",
            )

    # ===== 长按 =====
    def _hold_target(self):
        name = (self.hold_key_name.get() or "").strip()

        # Check for trigger keys using translated names
        if name.startswith(self.i18n.get("ui.trigger_l2")[:4]):  # "左扳" or "Left Trig"
            return ("trigger", "l2")
        if name.startswith(self.i18n.get("ui.trigger_r2")[:4]):  # "右扳" or "Right Trig"
            return ("trigger", "r2")

        # Build mapping from translated button names
        mapping = {
            self.i18n.get("ui.button_l1"): ("l1", "lb"),
            self.i18n.get("ui.button_r1"): ("r1", "rb"),
            self.i18n.get("ui.button_square"): ("square", "x"),
            self.i18n.get("ui.button_cross"): ("cross", "a"),
            self.i18n.get("ui.button_circle"): ("circle", "b"),
            self.i18n.get("ui.button_triangle"): ("triangle", "y"),
        }
        ds4_code, x360_code = mapping.get(name, ("l1", "lb"))
        code = ds4_code if self.gamepad_type.get() == "ds4" else x360_code
        return ("button", code)

    def _apply_hold_state(self):
        if not (self.emu_enabled and self.gamepad):
            return

        should_hold = bool(self.hold_enabled.get()) and bool(self.is_armed)
        if not should_hold:
            if self._hold_applied:
                try:
                    self.gamepad.release_hold()
                except Exception:
                    self._log("release_hold exception", level="warning")
                self._hold_applied = False
            return

        typ, key = self._hold_target()
        try:
            if typ == "trigger":
                if key == "l2":
                    self.gamepad.hold_triggers(l2=1.0, r2=0.0)
                else:
                    self.gamepad.hold_triggers(l2=0.0, r2=1.0)
                self.gamepad.hold_button("", False)
            else:
                self.gamepad.hold_triggers(0.0, 0.0)
                self.gamepad.hold_button(key, True)
            self._hold_applied = True
        except Exception:
            self._log("apply_hold_state exception", level="warning")
            self._log_user_hint(
                title=self.i18n.get("hints.hold_key_apply_fail_title"),
                cause=self.i18n.get("hints.hold_key_apply_fail_cause"),
                action=self.i18n.get("hints.hold_key_apply_fail_action"),
                who="USER_ENV",
            )

    # ===== 输出 =====
    def _finish_and_save(self):
        self._log("_finish_and_save: ENTER")
        try:
            self._log(f"_finish_and_save: cwd={os.getcwd()}")
            if self.log_path:
                self._log(f"_finish_and_save: log_path={self.log_path}")

            df = pd.DataFrame(self.results)
            df.to_csv("results.csv", index=False, encoding="utf-8-sig")
            self._log("save: results.csv OK")

            if df.empty:
                self._log("_finish_and_save: df empty", level="error")
                self._log_user_hint(
                    title=self.i18n.get("hints.no_valid_records_title"),
                    cause=self.i18n.get("hints.no_valid_records_cause"),
                    action=self.i18n.get("hints.no_valid_records_action"),
                    who="USER_OP",
                )
                messagebox.showerror(self.i18n.get("hints.no_valid_records_dialog"), f"{self.i18n.get('messages.no_valid_records_msg')}\n\n{self.i18n.get('messages.log_path_prefix')}{self.log_path}")
                return

            df_ok = df[df["seconds"].notna()].copy()
            if df_ok.empty:
                self._log("_finish_and_save: df_ok empty", level="error")
                self._log_user_hint(
                    title=self.i18n.get("hints.timing_result_empty_title"),
                    cause=self.i18n.get("hints.timing_result_empty_cause"),
                    action=self.i18n.get("hints.timing_result_empty_action"),
                    who="USER_OP",
                )
                messagebox.showerror(self.i18n.get("hints.timing_result_empty_title"), f"{self.i18n.get('hints.timing_result_empty_dialog')}\n\n{self.i18n.get('messages.log_path_prefix')}{self.log_path}")
                return

            g = df_ok.groupby("magnitude")["seconds"]
            stats = g.agg(["count", "mean", "std"]).reset_index()
            stats["omega"] = 2 * math.pi / stats["mean"]
            stats.to_csv("curve_summary.csv", index=False, encoding="utf-8-sig")
            self._log("save: curve_summary.csv OK")

            dz = float(self.deadzone_mag or 0.0)
            mx = float(self.max_mag.get())

            Xmax = float(self.x_axis_max.get())
            Ymax = float(self.y_axis_max.get())
            if Xmax <= 0:
                Xmax = 100.0
            if Ymax <= 0:
                Ymax = 100.0
            if mx <= 0:
                mx = 1.0

            xs_meas = stats["magnitude"].tolist()
            ys_meas = stats["omega"].tolist()

            if len(xs_meas) == 0:
                self._log("_finish_and_save: xs_meas empty", level="error")
                self._log_user_hint(
                    title=self.i18n.get("hints.stats_result_empty_title"),
                    cause=self.i18n.get("hints.stats_result_empty_cause"),
                    action=self.i18n.get("hints.stats_result_empty_action"),
                    who="USER_OP",
                )
                messagebox.showerror(self.i18n.get("hints.stats_result_empty_title"), f"{self.i18n.get('hints.stats_result_empty_dialog')}\n\n{self.i18n.get('messages.log_path_prefix')}{self.log_path}")
                return

            # 不再自动生成图片，改为仅保存 CSV，并在 UI 提示用户点击“生成曲线图”按钮

            try:
                if self.gamepad:
                    self.gamepad.release_hold()
            except Exception:
                self._log("_finish_and_save: release_hold exception", level="warning")
            self._hold_applied = False
            
            # 测试完成，摇杆归零静止
            if self.right_stick is not None:
                self.right_stick.set_value(0.0, 0.0)
                self._log("_finish_and_save: right_stick zeroed")
            
            self.status.set(self.i18n.get("messages.ready_to_generate_charts"))
            messagebox.showinfo(self.i18n.get("ui.generate_charts_prompt_title"), self.i18n.get("ui.generate_charts_prompt_body"))
            self._log("_finish_and_save: SUCCESS (CSV saved, charts pending by user)")

        except Exception:
            if self.logger:
                self.logger.exception("_finish_and_save: EXCEPTION")
            self._log_user_hint(
                title=self.i18n.get("hints.output_phase_error_title"),
                cause=self.i18n.get("hints.output_phase_error_cause"),
                action=self.i18n.get("hints.output_phase_error_action"),
                who="BUG",
            )
            try:
                messagebox.showerror(self.i18n.get("hints.export_fail_title"), f"{self.i18n.get('hints.output_phase_error_dialog')}\n\n{self.i18n.get('messages.log_path_prefix')}{self.log_path}")
            except Exception:
                pass
        finally:
            self._test_running = False
            self.is_armed = False
            self.in_trial = False

    # ===== 图表生成入口 =====
    def _generate_charts_from_stats(self, stats: pd.DataFrame):
        # 复用现有参数
        dz = float(self.deadzone_mag or 0.0)
        mx = float(self.max_mag.get())
        Xmax = float(self.x_axis_max.get() or 100.0)
        Ymax = float(self.y_axis_max.get() or 100.0)
        if Xmax <= 0:
            Xmax = 100.0
        if Ymax <= 0:
            Ymax = 100.0
        if mx <= 0:
            mx = 1.0

        xs_meas = stats["magnitude"].tolist()
        ys_meas = (stats["omega"].tolist() if "omega" in stats.columns else (2 * math.pi / stats["mean"]).tolist())

        if len(xs_meas) == 0:
            messagebox.showerror(self.i18n.get("hints.stats_result_empty_title"), self.i18n.get("hints.stats_result_empty_dialog"))
            return

        ys_mono = pav_isotonic_increasing(ys_meas)
        x0 = 0.0 if dz <= 0.0 else dz
        y0 = 0.0
        y_end = float(ys_mono[-1])
        if y_end <= 1e-12:
            y_end = max(ys_mono) if max(ys_mono) > 1e-12 else 1.0
        x_scale = Xmax / mx
        y_scale = Ymax / y_end
        plot_x = [x0]
        plot_y = [y0]
        for x, y in zip(xs_meas, ys_mono):
            if dz > 0 and x <= dz:
                plot_x.append(float(x))
                plot_y.append(0.0)
            else:
                plot_x.append(float(x))
                plot_y.append(float(y))
        plot_x_disp = [v * x_scale for v in plot_x]
        plot_y_disp = [v * y_scale for v in plot_y]

        # 正向图
        self._plot_curve(
            plot_x_disp,
            plot_y_disp,
            title=self.i18n.get("charts.curve_title"),
            xlabel=self.i18n.get("charts.curve_xlabel"),
            ylabel=self.i18n.get("charts.curve_ylabel"),
            filename="曲线图.png",
            with_coords=False,
            xlim_max=Xmax,
            ylim_max=Ymax,
        )
        self._log("save: 曲线图.png OK")
        self._plot_curve(
            plot_x_disp,
            plot_y_disp,
            title=self.i18n.get("charts.curve_title"),
            xlabel=self.i18n.get("charts.curve_xlabel"),
            ylabel=self.i18n.get("charts.curve_ylabel"),
            filename="带坐标曲线图.png",
            with_coords=True,
            xlim_max=Xmax,
            ylim_max=Ymax,
        )
        self._log("save: 带坐标曲线图.png OK")

        # 反曲线 + 补偿表
        inv_x = []
        inv_y = []
        table = []
        for i, (x_d, y_d) in enumerate(zip(plot_x_disp, plot_y_disp), start=1):
            px = 0.0 if Ymax <= 1e-12 else float(y_d) / float(Ymax)
            py = 0.0 if Xmax <= 1e-12 else float(x_d) / float(Xmax)
            x_inv = max(0.0, min(Xmax, px * Xmax))
            y_inv = max(0.0, min(Ymax, py * Ymax))
            inv_x.append(x_inv)
            inv_y.append(y_inv)
            table.append({
                "point_index(1-based)": i,
                "forward_x": float(x_d),
                "forward_y": float(y_d),
                "inv_x": float(x_inv),
                "inv_y": float(y_inv),
                "note": "inv_x=(forward_y/Ymax)*Xmax ; inv_y=(forward_x/Xmax)*Ymax",
            })
        pd.DataFrame(table).to_csv("compensation_table.csv", index=False, encoding="utf-8-sig")
        self._log("save: compensation_table.csv OK (one-to-one percent swap)")
        self._plot_curve(
            inv_x,
            inv_y,
            title=self.i18n.get("charts.inverse_title"),
            xlabel=self.i18n.get("charts.inverse_xlabel"),
            ylabel=self.i18n.get("charts.inverse_ylabel"),
            filename="反曲线图.png",
            with_coords=False,
            xlim_max=Xmax,
            ylim_max=Ymax,
        )
        self._log("save: 反曲线图.png OK (one-to-one percent swap)")
        self._plot_curve(
            inv_x,
            inv_y,
            title=self.i18n.get("charts.inverse_title"),
            xlabel=self.i18n.get("charts.inverse_xlabel"),
            ylabel=self.i18n.get("charts.inverse_ylabel"),
            filename="带坐标反曲线图.png",
            with_coords=True,
            xlim_max=Xmax,
            ylim_max=Ymax,
        )
        self._log("save: 带坐标反曲线图.png OK (one-to-one percent swap)")

    def generate_charts_from_current(self):
        # 从内存 results 生成
        df = pd.DataFrame(self.results)
        if df.empty:
            messagebox.showerror(self.i18n.get("hints.no_valid_records_title"), self.i18n.get("hints.no_valid_records_dialog"))
            return
        df_ok = df[df["seconds"].notna()].copy()
        if df_ok.empty:
            messagebox.showerror(self.i18n.get("hints.timing_result_empty_title"), self.i18n.get("hints.timing_result_empty_dialog"))
            return
        g = df_ok.groupby("magnitude")["seconds"]
        stats = g.agg(["count", "mean", "std"]).reset_index()
        stats["omega"] = 2 * math.pi / stats["mean"]
        self._generate_charts_from_stats(stats)

    def generate_charts_from_csv(self):
        # 打开 CSV 生成图表（支持 results.csv 或 curve_summary.csv 结构）
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                title=self.i18n.get("ui.select_csv_title"),
                filetypes=[("CSV", "*.csv"), (self.i18n.get("ui.all_files"), "*.*")],
            )
        except Exception:
            path = None
        if not path:
            return
        try:
            df = pd.read_csv(path)
        except Exception as e:
            messagebox.showerror(self.i18n.get("hints.export_fail_title"), f"CSV load failed: {e}")
            return
        # Normalize to stats format
        if {"magnitude", "omega"}.issubset(df.columns):
            stats = df.copy()
        elif {"magnitude", "seconds"}.issubset(df.columns):
            g = df.groupby("magnitude")["seconds"]
            stats = g.agg(["count", "mean", "std"]).reset_index()
            stats["omega"] = 2 * math.pi / stats["mean"]
        else:
            messagebox.showerror(self.i18n.get("hints.export_fail_title"), self.i18n.get("errors.csv_format_not_supported"))
            return
        self._generate_charts_from_stats(stats)

    def _plot_curve(
        self,
        x_list,
        y_list,
        title,
        xlabel,
        ylabel,
        filename,
        with_coords=False,
        xlim_max=None,
        ylim_max=None,
    ):
        # 100 种颜色
        colors = [
            # Tableau
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
            # Light
            "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
            "#c49c94", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5",
            # Dark
            "#1a4d7a", "#b35806", "#1d5a1d", "#8b1a1a", "#5a3d7a",
            "#4a2f28", "#9b3d6b", "#5a5a5a", "#7a7a1a", "#0d6f80",
            # Blue
            "#003f87", "#1a5490", "#356aa0", "#5180b0", "#6d9bc0",
            "#88b5d0", "#a3cfe0", "#bde9f0", "#d9f5ff", "#e8f9ff",
            # Red/Orange
            "#8b0000", "#a72828", "#c35050", "#d97878", "#e59a9a",
            "#f0b8b8", "#fad4d4", "#fce8e8", "#fff0f0", "#ffe8e8",
            # Green
            "#0d5c0d", "#1a7a1a", "#2a9a2a", "#3ab83a", "#4ad04a",
            "#5ae85a", "#7af87a", "#9aff9a", "#baffba", "#daffda",
            # Purple
            "#4a0080", "#6b1ba3", "#8b3dc6", "#a85dd9", "#c57dec",
            "#d99dff", "#e8bfff", "#f0d4ff", "#f8e8ff", "#fdf0ff",
            # Brown/Tan
            "#66330d", "#804d26", "#9a6633", "#b3804d", "#cc9966",
            "#d9ad7f", "#e6c299", "#f0d9b3", "#f5e8d0", "#faf5eb",
            # Cyan/Teal
            "#003333", "#004d4d", "#006666", "#1a8080", "#339999",
            "#4db3b3", "#66cccc", "#80e6e6", "#99ffff", "#ccffff",
            # Yellow
            "#999900", "#b3b300", "#cccc00", "#e6e600", "#ffff00",
            "#ffff33", "#ffff66", "#ffff99", "#ffffcc", "#fffff0",
        ]

        # 计算所需高度（坐标显示在图表下方）
        total_points = len(x_list)
        
        if with_coords:
            max_rows = 20
            num_cols = (total_points + max_rows - 1) // max_rows if total_points > 0 else 1
            # 估算坐标区域需要的高度（每行约0.3cm）
            coords_height = 0.15 + 0.3 * max_rows / 2.54  # 转换为英寸
        else:
            coords_height = 0
        
        # 图表高度 = 基础高度 + 坐标区域高度
        fig_height = 5.6 + coords_height
        
        fig = plt.figure(figsize=(8.6, fig_height))
        
        # 创建图表子区域
        if with_coords:
            # 图表占据上面部分，坐标区在下面
            ax = fig.add_axes((0.1, (coords_height + 0.3) / fig_height, 0.8, 5.6 / fig_height))
        else:
            ax = fig.add_subplot(111)
        
        ax.plot(x_list, y_list, "-", linewidth=2)

        for i, (x, y) in enumerate(zip(x_list, y_list), start=1):
            c = colors[(i - 1) % len(colors)]
            ax.scatter([x], [y], s=55, color=c, zorder=3)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)

        if xlim_max is not None:
            ax.set_xlim(0, float(xlim_max))
        if ylim_max is not None:
            ax.set_ylim(0, float(ylim_max))

        if with_coords:
            # 坐标显示在图表下方专门区域
            max_rows = 20
            col_width = 0.19
            
            # 下方区域从 0 到 coords_height/fig_height
            bottom_area_height = coords_height / fig_height
            y_base = bottom_area_height * 0.9  # 区域内的起始y
            row_dy = bottom_area_height * 0.8 / max_rows  # 每行的间距
            
            for idx, (x, y) in enumerate(zip(x_list, y_list), start=1):
                c = colors[(idx - 1) % len(colors)]
                s = f"{idx}: ({x:.1f}, {y:.1f})"
                
                row = (idx - 1) % max_rows
                col = (idx - 1) // max_rows
                
                x_pos = 0.1 + col * col_width
                y_pos = y_base - row * row_dy
                
                fig.text(x_pos, y_pos, s, color=c, fontsize=8.5, ha="left", va="center", family='monospace')

        # 添加水印（右下角）
        watermark = f"{APP_NAME} by {APP_AUTHOR}"
        fig.text(0.99, 0.01, watermark, fontsize=9, ha="right", va="bottom", 
                color="#888888", alpha=0.7, style='italic')

        plt.savefig(filename, dpi=220, bbox_inches='tight')
        plt.close()

    # ===== 输出 =====
    def _output_loop(self):
        hz = 100.0
        interval = 1.0 / hz
        while self.running:
            try:
                if self.emu_enabled and self.gamepad is not None:
                    if self.mode == "deadzone" or self.in_trial:
                        self._maybe_keepalive()

                    self._apply_hold_state()

                    lx, ly = (0.0, 0.0)
                    rx, ry = (0.0, 0.0)
                    if self.left_stick is not None:
                        lx, ly = self.left_stick.get_value()
                    if self.right_stick is not None:
                        rx, ry = self.right_stick.get_value()
                    self.gamepad.set_sticks(lx, ly, rx, ry)
            except Exception:
                pass
            time.sleep(interval)

    def on_close(self):
        self._log("on_close")

        if self.is_armed or self._test_running or self.mode != "idle":
            try:
                ok = messagebox.askyesno(self.i18n.get("hints.exit_confirm_title"), self.i18n.get("hints.exit_confirm_msg"))
            except Exception:
                ok = True
            if not ok:
                self._log("on_close cancelled by user", level="warning")
                return

        self._test_running = False
        self.is_armed = False
        self.in_trial = False
        self.mode = "idle"

        self.running = False
        try:
            if self.gamepad is not None:
                self.gamepad.neutral()
        except Exception:
            self._log("on_close: neutral exception", level="warning")

        try:
            self._unregister_name_hotkeys()
        except Exception:
            pass

        # ✅ 日志只在程序关闭时停止
        self._stop_logger(reason="(on_close)")
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
