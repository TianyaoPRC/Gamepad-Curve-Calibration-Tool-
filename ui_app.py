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


# ================== App Meta ==================
APP_VERSION = "v1.6beta"
APP_TITLE = f"游戏摇杆曲线探测器 {APP_VERSION}  |  哔哩哔哩：刘云耀"


# ===== Matplotlib 中文支持 =====
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def clamp(v, lo=-1.0, hi=1.0):
    try:
        v = float(v)
    except Exception:
        return 0.0
    return max(lo, min(hi, v))


def tk_event_to_hotkey(event: tk.Event):
    """
    Tk 捕获按键，返回“键名模式”的 key name（给 keyboard.add_hotkey 用）
    注意：Tk 的 event.keycode 不是 keyboard 的 scan_code。
    """
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
        # 允许单字符（字母/数字/符号）在 UI 中显示；具体能否用于当前后端由后端决定
        return ch.lower()

    return ks.lower()


def pav_isotonic_increasing(y):
    """单调回归：强制 y 随 x 单调不减"""
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
    """把 print()/traceback 输出重定向进 logger"""

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
                except Exception:
                    pass

    def flush(self):
        if self._buf.strip():
            try:
                self.logger.log(self.level, f"[STD] {self._buf.strip()}")
            except Exception:
                pass
        self._buf = ""


class VirtualStick(tk.Canvas):
    """鼠标拖动的虚拟摇杆（仅做 UI 展示与输出）"""

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
    """右侧滚动区域"""

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
    """
    ✅ 已落实的3项改动：
      1) 日志不再在 reset_test / finish_and_save 提前 stop（保证后续也有日志）
      2) 键名注册失败 -> 自动切 scan 时，UI 文案不再误导为“检测到数字/符号键”
      3) 打包 spec 的 hiddenimports 在 spec 文件里改（见 stick_calibrator.spec）
    """

    def __init__(self):
        super().__init__()

        # ===== 日志（启动即记录，直到 on_close 才停止）=====
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

        # ===== 手柄模拟总开关 =====
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
        self.keepalive_btn_name = tk.StringVar(value="方块/ X")
        self._keepalive_last = 0.0

        # ===== 测试期间长按按键（默认关闭）=====
        self.hold_enabled = tk.BooleanVar(value=False)
        self.hold_key_name = tk.StringVar(value="左扳机（L2/ LT）")
        self._hold_applied = False

        # ===== 热键后端 =====
        self.hotkey_backend = tk.StringVar(value="keyboard_name")
        self._scan_hook_installed = False

        # 兼容性提示（显示在 UI 内，不弹窗）
        self.hotkey_compat_hint = tk.StringVar(value="")

        # ===== 热键（保存两份：name / scan_code）=====
        self.start_key = "f6"
        self.record_key = "f9"
        self.deadzone_key = "f10"
        self.deadzone_back_key = "f11"
        self.end_deadzone_key = "f12"

        # scan_code 版（None 表示未设置）
        self.start_scan = None
        self.record_scan = None
        self.deadzone_scan = None
        self.deadzone_back_scan = None
        self.end_deadzone_scan = None

        # keyboard.add_hotkey 返回的 handle
        self.hotkey_start = None
        self.hotkey_record = None
        self.hotkey_deadzone = None
        self.hotkey_deadzone_back = None
        self.hotkey_end_deadzone = None

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

        # ===== 运行锁 / 热键防抖 =====
        self._start_guard_lock = threading.Lock()
        self._test_running = False  # 硬锁：测试进行中禁止 start_test 重入
        self._hotkey_cooldown_ms = 250
        self._hotkey_last_ts = {}  # name -> perf_counter()

        # ===== UI =====
        self.status = tk.StringVar(value="提示：先点击【开启模拟手柄】。")
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

        # Tk 捕获（仅用于键名模式的“按键设置”；scan 模式用 keyboard.read_event 捕获）
        self.bind_all("<Key>", self._on_any_key)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.after(250, self._refresh_wraplengths)

        # 初次评估 + 注册热键
        self._auto_select_backend(reason="init")
        self._register_hotkeys()
        self._log("App init done.")

    # ================= 日志 =================
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
                messagebox.showwarning("日志初始化失败", str(e))
            except Exception:
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

        # 用户可读提示（只写一次）
        self.logger.info("[HINT] 这份日志给普通用户看的：遇到问题可先看包含 [CAUSE]/[ACTION] 的几行。")
        self.logger.info("[HINT] 重点关键词：HOTKEY / enable_emulation / start_test / record / finish_and_save。")

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
                title="日志目录不可写",
                cause="多半是系统权限/杀软拦截/路径不可写（用户环境问题）",
                action="建议把程序放到非系统盘的普通文件夹，或以管理员运行；或关闭拦截后再试。",
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
        """
        who:
          - USER_OP:   更像用户操作/设置导致
          - USER_ENV:  更像系统环境/权限/杀软/驱动
          - BUG:       更像代码 bug
          - UNKNOWN:   不确定
        """
        self._log(f"[HINT] {title}")
        self._log(f"[CAUSE] ({who}) {cause}")
        self._log(f"[ACTION] {action}")

    # ================= 热键：统一日志/防抖 =================
    def _now(self) -> float:
        return time.perf_counter()

    def _hotkey_debounced(self, name: str) -> bool:
        """True=允许触发；False=本次忽略（防抖）"""
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

    def _on_hotkey_start(self):
        self._hotkey_log("start")
        if not self._hotkey_debounced("start"):
            return
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

    # ================= 热键后端：自动选择逻辑 =================
    def _sanitize_hotkey_name(self, hk: str, fallback: str) -> str:
        """
        keyboard.add_hotkey 只吃键名，不吃 'scan code 5' 这种字符串；遇到就回退。
        """
        hk = (hk or "").strip()
        if not hk:
            return fallback
        if hk.lower().startswith("scan code"):
            self._log(f"hotkey '{hk}' is scan-code style -> fallback '{fallback}'", level="warning")
            return fallback
        return hk.lower()

    def _is_symbol_or_digit_single_key(self, hk_name: str) -> bool:
        """判断：是否为单字符数字/符号键（触发强制 scan 模式）"""
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
        return [self.start_key, self.record_key, self.deadzone_key, self.deadzone_back_key, self.end_deadzone_key]

    def _auto_select_backend(self, reason: str = ""):
        """
        - 只要任何热键绑定到数字/符号单字符 => keyboard_scan
        - 当全部都不是数字/符号单字符 => 自动切回 keyboard_name
        """
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
            self.hotkey_compat_hint.set(
                "检测到你绑定了【数字/符号键】（单字符）。\n"
                "✅ 已自动使用：keyboard_scan（更适合全屏游戏/数字符号键）。\n"
                "提示：把这些数字/符号键改成 F键/字母/方向键等后，会自动切回 keyboard_name。"
            )
        else:
            self.hotkey_compat_hint.set(
                "当前热键不包含数字/符号键。\n"
                "✅ 已自动使用：keyboard_name（更直观稳定，推荐 F键/字母）。\n"
                "若你改绑为数字/符号键，会自动切到 keyboard_scan。"
            )

        if self.lbl_hotkey_hint is not None:
            try:
                self.lbl_hotkey_hint.configure(textvariable=self.hotkey_compat_hint)
            except Exception:
                pass

    # ================= 热键后端：hook/注册 =================
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

    def _register_hotkeys(self):
        # 测试进行中禁止重绑热键
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
            self._install_scan_hook()
            return

        # ===== 键名模式：keyboard.add_hotkey =====
        start = self._sanitize_hotkey_name(self.start_key, "f6")
        record = self._sanitize_hotkey_name(self.record_key, "f9")
        dzp = self._sanitize_hotkey_name(self.deadzone_key, "f10")
        dzm = self._sanitize_hotkey_name(self.deadzone_back_key, "f11")
        dzend = self._sanitize_hotkey_name(self.end_deadzone_key, "f12")

        self.start_key = start
        self.record_key = record
        self.deadzone_key = dzp
        self.deadzone_back_key = dzm
        self.end_deadzone_key = dzend
        self.lbl_keys.configure(text=self._keys_text())

        try:
            self.hotkey_start = keyboard.add_hotkey(
                start, lambda: self.after(0, self._on_hotkey_start), trigger_on_release=True
            )
            self.hotkey_record = keyboard.add_hotkey(
                record, lambda: self.after(0, self._on_hotkey_record), trigger_on_release=True
            )
            self.hotkey_deadzone = keyboard.add_hotkey(
                dzp, lambda: self.after(0, self._on_hotkey_deadzone), trigger_on_release=True
            )
            self.hotkey_deadzone_back = keyboard.add_hotkey(
                dzm, lambda: self.after(0, self._on_hotkey_deadzone_back), trigger_on_release=True
            )
            self.hotkey_end_deadzone = keyboard.add_hotkey(
                dzend, lambda: self.after(0, self._on_hotkey_end_deadzone), trigger_on_release=True
            )
        except Exception as e:
            # 不允许异常炸穿
            self._log(f"register_hotkeys FAILED: {repr(e)}", level="error")
            self._log_user_hint(
                title="热键注册失败（键名模式）",
                cause="通常是全屏游戏环境/权限/杀软拦截/某些键名不被识别（偏环境问题）",
                action="程序会自动切到 keyboard_scan；建议优先绑定 F键/字母，必要时以管理员运行或关闭拦截。",
                who="USER_ENV",
            )

            # 自动切 scan 兜底（✅ 不再误导为“检测到数字/符号键”）
            self.hotkey_backend.set("keyboard_scan")
            self._install_scan_hook()

            self.hotkey_compat_hint.set(
                "⚠️ 键名模式热键注册失败，已自动切换到 keyboard_scan。\n"
                "可能原因：全屏游戏/权限不足/杀软拦截/某些键名不被 keyboard 识别。\n"
                "建议：优先绑定 F键/字母；必要时以管理员运行或关闭拦截。"
            )
            if self.lbl_hotkey_hint is not None:
                try:
                    self.lbl_hotkey_hint.configure(textvariable=self.hotkey_compat_hint)
                except Exception:
                    pass

            self.status.set("⚠️ 键名模式注册失败，已自动切换到 keyboard_scan（详情见日志）。")

    def _on_hotkey_backend_changed(self, _event=None):
        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set("⚠️ 测试进行中，禁止切换热键模式（请先停止/重置）。")
            return

        self._auto_select_backend(reason="user_changed_backend")
        self._register_hotkeys()
        self.status.set(f"✅ 热键模式：{self.hotkey_backend.get()}（按绑定按键自动适配）")

    # ================= UI =================
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

        ttk.Label(left, text="左摇杆（鼠标拖动）", font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=0, pady=(0, 6))
        ttk.Label(left, text="右摇杆（鼠标拖动）", font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=1, pady=(0, 6))

        self.left_stick = VirtualStick(left, size=360)
        self.right_stick = VirtualStick(left, size=360)
        self.left_stick.grid(row=1, column=0, padx=8, pady=8, sticky="n")
        self.right_stick.grid(row=1, column=1, padx=8, pady=8, sticky="n")

        info = ttk.LabelFrame(left, text="状态 / 操作流程")
        info.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=(10, 0))
        info.columnconfigure(0, weight=1)
        info.rowconfigure(1, weight=1)

        self.lbl_status = ttk.Label(info, textvariable=self.status, justify="left")
        self.lbl_status.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self.lbl_tip = ttk.Label(
            info,
            justify="left",
            foreground="#333",
            text=(
                "用途：测量“游戏对手柄做的输入优化曲线”（不是硬件死区）。\n\n"
                "操作流程：\n"
                "  1) 点击【开启模拟手柄】后，切回游戏。\n"
                "  2) 点击【开始测试】（或按开始键）。程序进入死区探测。\n"
                "  3) 死区探测：\n"
                "     - 视角不动：按【死区探测键】增加幅值。\n"
                "     - 动得过快：按【回退死区键】回退（可回到 0）。\n"
                "     - 视角开始缓慢移动：按【结束死区键】确认死区并进入曲线采样。\n"
                "  4) 曲线采样：\n"
                "     - 按【记录键】一次开始计时。\n"
                "     - 转满一圈后再按【记录键】一次结束并保存。\n"
                "  5) 完成后自动输出：曲线图、反曲线图、带坐标版本、CSV。\n\n"
                "热键提示：软件必须在后台运行（游戏在前台）。\n"
                "  - 你绑定数字/符号键时，本软件会自动切到【扫描码模式】。\n"
                "定位问题：程序会生成 logs/run_log_*.txt 详细日志（包含可读解释）。"
            ),
        )
        self.lbl_tip.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        right_scroll = ScrollableFrame(root)
        right_scroll.grid(row=0, column=1, sticky="nsew")
        right = right_scroll.inner
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="设置面板", font=("Microsoft YaHei", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10), padx=6)

        padfrm = ttk.LabelFrame(right, text="虚拟手柄")
        padfrm.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=6)
        padfrm.columnconfigure(0, weight=1)

        ttk.Label(padfrm, text="模拟类型：").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        self.cmb_pad = ttk.Combobox(padfrm, values=["ds4", "xbox360"], state="readonly", width=18, textvariable=self.gamepad_type)
        self.cmb_pad.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))

        btnrow = ttk.Frame(padfrm)
        btnrow.grid(row=2, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(btnrow, text="开启模拟手柄", command=self.enable_emulation).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btnrow, text="回中（不重启设备）", command=self.neutral_only).grid(row=0, column=1)

        self.lbl_emu = ttk.Label(padfrm, text="状态：未开启", foreground="#aa0000")
        self.lbl_emu.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        frm = ttk.LabelFrame(right, text="测试参数")
        frm.grid(row=2, column=0, sticky="ew", pady=(0, 10), padx=6)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="采样点数量（2~10：指需要测量的点数，不含第1固定点）：").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(frm, width=10, textvariable=self.sample_count).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(frm, text="每个采样点记录次数：").grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))
        ttk.Spinbox(frm, from_=1, to=50, width=10, textvariable=self.repeats_per_mag).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(frm, text="幅值范围（用于“非死区”起点到最大）：").grid(row=4, column=0, sticky="w", padx=8, pady=(0, 2))
        rng = ttk.Frame(frm)
        rng.grid(row=5, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rng, text="MIN").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rng, width=8, textvariable=self.min_mag).grid(row=0, column=1)
        ttk.Label(rng, text="MAX").grid(row=0, column=2, padx=(12, 6))
        ttk.Entry(rng, width=8, textvariable=self.max_mag).grid(row=0, column=3)

        ttk.Label(frm, text="测试方向（固定推右摇杆）：").grid(row=6, column=0, sticky="w", padx=8, pady=(0, 2))
        dirfrm = ttk.Frame(frm)
        dirfrm.grid(row=7, column=0, sticky="w", padx=8, pady=(0, 8))
        for i, d in enumerate(["right", "left", "up", "down"]):
            ttk.Radiobutton(dirfrm, text=d, value=d, variable=self.direction).grid(row=0, column=i, padx=6)

        dzfrm = ttk.LabelFrame(right, text="死区探测参数")
        dzfrm.grid(row=3, column=0, sticky="ew", pady=(0, 10), padx=6)
        dzfrm.columnconfigure(0, weight=1)
        ttk.Label(dzfrm, text="探测步长（仍不动时使用）：").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(dzfrm, width=10, textvariable=self.deadzone_step).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 6))
        ttk.Label(dzfrm, text="回退步长（动得过快时使用，可回到 0）：").grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))
        ttk.Entry(dzfrm, width=10, textvariable=self.deadzone_back_step).grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        axfrm = ttk.LabelFrame(right, text="曲线显示坐标（例如 0~100 / 0~350）")
        axfrm.grid(row=4, column=0, sticky="ew", pady=(0, 10), padx=6)
        axfrm.columnconfigure(0, weight=1)
        rowa = ttk.Frame(axfrm)
        rowa.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 8))
        ttk.Label(rowa, text="X轴最大值：").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rowa, width=10, textvariable=self.x_axis_max).grid(row=0, column=1)
        ttk.Label(rowa, text="Y轴最大值：").grid(row=0, column=2, padx=(12, 6))
        ttk.Entry(rowa, width=10, textvariable=self.y_axis_max).grid(row=0, column=3)

        kfrm = ttk.LabelFrame(right, text="保持手柄输入（防游戏切回键鼠）")
        kfrm.grid(row=5, column=0, sticky="ew", pady=(0, 10), padx=6)
        kfrm.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            kfrm,
            text="启用（死区探测与计时等待期间会周期性点按一个手柄按键）",
            variable=self.keepalive_enabled,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        rowk = ttk.Frame(kfrm)
        rowk.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rowk, text="间隔(ms)：").grid(row=0, column=0, padx=(0, 6))
        ttk.Entry(rowk, width=8, textvariable=self.keepalive_interval_ms).grid(row=0, column=1)

        ttk.Label(rowk, text="按键：").grid(row=0, column=2, padx=(12, 6))
        ttk.Combobox(
            rowk,
            values=["方块/ X", "叉/ A", "圆/ B", "三角/ Y", "L1/ LB", "R1/ RB", "Share/ Back", "Options/ Start"],
            textvariable=self.keepalive_btn_name,
            width=14,
            state="readonly",
        ).grid(row=0, column=3)

        hfrm = ttk.LabelFrame(right, text="测试期间长按按键（默认关闭）")
        hfrm.grid(row=6, column=0, sticky="ew", pady=(0, 10), padx=6)
        hfrm.columnconfigure(0, weight=1)

        ttk.Checkbutton(hfrm, text="启用（测试期间持续按住指定按键/扳机）", variable=self.hold_enabled).grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4)
        )

        rowh = ttk.Frame(hfrm)
        rowh.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(rowh, text="长按键：").grid(row=0, column=0, padx=(0, 6))
        ttk.Combobox(
            rowh,
            values=[
                "左扳机（L2/ LT）",
                "右扳机（R2/ RT）",
                "L1/ LB",
                "R1/ RB",
                "方块/ X",
                "叉/ A",
                "圆/ B",
                "三角/ Y",
            ],
            textvariable=self.hold_key_name,
            width=16,
            state="readonly",
        ).grid(row=0, column=1)

        # ===== 热键设置（将“热键模式”放在这里附近）=====
        hot = ttk.LabelFrame(right, text="热键设置（点击按钮后按键）")
        hot.grid(row=7, column=0, sticky="ew", pady=(0, 10), padx=6)
        hot.columnconfigure(0, weight=1)

        hk_backend_frm = ttk.Frame(hot)
        hk_backend_frm.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        hk_backend_frm.columnconfigure(2, weight=1)

        ttk.Label(hk_backend_frm, text="热键模式：").grid(row=0, column=0, sticky="w")
        self.cmb_hotkey_backend = ttk.Combobox(
            hk_backend_frm,
            values=["keyboard_name", "keyboard_scan"],
            textvariable=self.hotkey_backend,
            width=16,
            state="readonly",
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
        btns.grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8))

        row1 = ttk.Frame(btns)
        row1.grid(row=0, column=0, sticky="w")
        ttk.Button(row1, text="设置开始键", command=self.capture_start_key).grid(row=0, column=0, padx=(0, 8), pady=(0, 6))
        ttk.Button(row1, text="设置记录键", command=self.capture_record_key).grid(row=0, column=1, padx=(0, 8), pady=(0, 6))
        ttk.Button(row1, text="设置死区探测键", command=self.capture_deadzone_key).grid(row=0, column=2, padx=(0, 8), pady=(0, 6))

        row2 = ttk.Frame(btns)
        row2.grid(row=1, column=0, sticky="w")
        ttk.Button(row2, text="设置回退死区键", command=self.capture_deadzone_back_key).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(row2, text="设置结束死区键", command=self.capture_end_deadzone_key).grid(row=0, column=1)

        ctr = ttk.LabelFrame(right, text="控制")
        ctr.grid(row=8, column=0, sticky="ew", pady=(0, 10), padx=6)
        cbtn = ttk.Frame(ctr)
        cbtn.grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Button(cbtn, text="开始测试", command=self.start_test).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(cbtn, text="停止/重置", command=self.reset_test).grid(row=0, column=1)

        ttk.Label(
            right,
            text=f"作者署名：哔哩哔哩：刘云耀   |   版本：{APP_VERSION}",
            foreground="#888",
            font=("Microsoft YaHei", 9),
        ).grid(row=9, column=0, sticky="w", padx=10, pady=(0, 16))

    def _refresh_wraplengths(self):
        try:
            w = max(420, self.winfo_width() // 2 - 40)
            self.lbl_status.configure(wraplength=w)
            self.lbl_tip.configure(wraplength=w)
            if self.lbl_hotkey_hint:
                self.lbl_hotkey_hint.configure(wraplength=max(320, self.winfo_width() // 2 - 80))
        except Exception:
            pass
        self.after(350, self._refresh_wraplengths)

    # ================= 手柄模拟控制 =================
    def enable_emulation(self):
        self._log(f"enable_emulation: request kind={self.gamepad_type.get()}")
        if self.emu_enabled and self.gamepad is not None:
            self.status.set("模拟手柄已开启：不会重启设备。")
            self._log("enable_emulation: already enabled (no restart).")
            return
        try:
            self.gamepad = VirtualGamepad(kind=self.gamepad_type.get())
        except Exception as e:
            self._log(f"enable_emulation: FAIL err={repr(e)}", level="error")
            self._log_user_hint(
                title="开启虚拟手柄失败",
                cause="可能是 ViGEm 驱动/权限/杀软拦截/系统环境问题（偏环境问题）",
                action="建议：确认安装 ViGEmBus；以管理员运行；关闭拦截；重启后再试。",
                who="USER_ENV",
            )
            messagebox.showerror("开启失败", str(e))
            return
        self.emu_enabled = True
        self.lbl_emu.configure(text=f"状态：已开启（{self.gamepad_type.get()}）", foreground="#008800")
        self.status.set("✅ 已开启模拟手柄。请切回游戏后再开始测试。")
        self.cmb_pad.configure(state="disabled")
        self._log("enable_emulation: SUCCESS")

    def neutral_only(self):
        self._log("neutral_only")
        if not self.emu_enabled or self.gamepad is None:
            self.status.set("尚未开启模拟手柄。")
            self._log("neutral_only: ignored (emu not enabled).", level="warning")
            return
        try:
            self.gamepad.neutral()
        except Exception:
            self._log("neutral_only: gamepad.neutral exception", level="warning")
        self.left_stick.set_value(0.0, 0.0)
        self.right_stick.set_value(0.0, 0.0)
        self._hold_applied = False
        self.status.set("已回中（不会断开/重启虚拟手柄）。")

    # ================= 热键设置 =================
    def _keys_text(self):
        return (
            f"开始键：{self.start_key}    记录键：{self.record_key}\n"
            f"死区探测键：{self.deadzone_key}    回退死区键：{self.deadzone_back_key}\n"
            f"结束死区键：{self.end_deadzone_key}\n"
            f"当前热键模式：{self.hotkey_backend.get()}（会按绑定按键自动适配）"
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

    def _begin_capture(self):
        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set("⚠️ 测试进行中，禁止修改热键（请先停止/重置）。")
            self._log("hotkey capture blocked: test is running", level="warning")
            self._log_user_hint(
                title="尝试在测试中改热键",
                cause="测试中改热键会导致热键触发异常/丢失（用户操作问题）",
                action="先停止/重置，再设置热键。",
                who="USER_OP",
            )
            self.capture_mode = None
            return

        self.status.set("请按下你要绑定的键…（不会弹窗打断）")

        backend = (self.hotkey_backend.get() or "keyboard_name").strip()
        self.capture_target_backend = backend

        if backend == "keyboard_scan":
            self.status.set("等待按键：扫描码模式捕获中…（直接按键即可）")
            self._start_scan_capture_thread()
        else:
            self.status.set("等待按键：键名模式捕获中…（在窗口里按键即可）")

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
                    title="扫描码捕获失败",
                    cause="可能是系统权限/键盘钩子被拦截/杀软拦截（偏环境问题）",
                    action="建议：以管理员运行；关闭拦截；或换用键名模式 + F键。",
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

        self._auto_select_backend(reason=f"capture_{mode}")

        self.lbl_keys.configure(text=self._keys_text())
        self._register_hotkeys()

        self.status.set("✅ 热键已更新（模式会自动适配）")
        self._log(f"hotkeys updated: {self._keys_text()}")

        if self._is_symbol_or_digit_single_key(hk_name):
            self._log_user_hint(
                title="你绑定了数字/符号键",
                cause="数字/符号键在 keyboard_name 下经常兼容性差（不是代码bug，是常见环境限制）",
                action="已自动切换到 keyboard_scan；若你想回键名模式，把这些键改成 F键/字母即可。",
                who="USER_ENV",
            )

    def _on_any_key(self, event):
        if self.capture_mode is None:
            return
        if self.capture_target_backend != "keyboard_name":
            return

        if self.is_armed or self._test_running or self.mode != "idle":
            self.status.set("⚠️ 测试进行中，禁止修改热键（请先停止/重置）。")
            self._log("hotkey capture blocked: test is running", level="warning")
            self.capture_mode = None
            return

        hk = tk_event_to_hotkey(event)
        if not hk:
            return

        self._apply_captured_hotkey(hk, None)

    # ================= 参数与采样列表 =================
    def _parse_sample_count(self) -> int:
        s = (self.sample_count.get() or "").strip()
        try:
            n = int(s)
        except Exception:
            raise ValueError("采样点数量必须是整数（2~10）。")
        if n < 2 or n > 10:
            raise ValueError("采样点数量范围：2~10。")
        return n

    def _validate_ranges(self):
        mn = float(self.min_mag.get())
        mx = float(self.max_mag.get())
        if not (0.0 <= mn < mx <= 1.0):
            raise ValueError("幅值范围必须满足：0 <= MIN < MAX <= 1。")
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

    # ================= 测试控制 =================
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
                messagebox.showwarning("未开启模拟", "请先点击【开启模拟手柄】。")
                self._log("start_test: blocked (emu not enabled).", level="warning")
                self._log_user_hint(
                    title="未开启模拟手柄就开始测试",
                    cause="这是操作顺序问题（用户操作问题）",
                    action="先点【开启模拟手柄】，再开始测试。",
                    who="USER_OP",
                )
                return

            try:
                _ = self._parse_sample_count()
                _ = self._validate_ranges()
            except Exception as e:
                self._log(f"start_test: param error {repr(e)}", level="error")
                self._log_user_hint(
                    title="参数错误导致无法开始测试",
                    cause="输入的参数不合法（用户操作问题）",
                    action="按提示修正：采样点 2~10；且 0<=MIN<MAX<=1。",
                    who="USER_OP",
                )
                messagebox.showerror("参数错误", str(e))
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

            self.status.set(
                "✅ 已开始测试：进入【死区探测】。\n"
                f"当前幅值：m={self.deadzone_current_m:.4f}\n"
                "不动：按【死区探测键】继续增加。\n"
                "动得过快：按【回退死区键】回退（可回到 0）。\n"
                "开始缓慢移动：按【结束死区键】确认死区并进入曲线采样。"
            )
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

        self.right_stick.set_value(0.0, 0.0)

        try:
            if self.gamepad:
                self.gamepad.release_hold()
        except Exception:
            self._log("reset_test: release_hold exception", level="warning")
        self._hold_applied = False

        self.status.set("已停止并重置（虚拟手柄不会断开/重启）。")
        # ✅ v1.6beta：不再在 reset_test 停止日志（日志仅 on_close 停止）

    # ================= 死区阶段按键 =================
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
            self.status.set(
                f"【死区探测】仍不动：m → {self.deadzone_current_m:.4f}\n"
                "开始缓慢移动：按【结束死区键】。"
            )
        else:
            self.status.set(
                f"【第1点微调】已增加死区候选值：m → {self.deadzone_current_m:.4f}\n"
                "确认后继续按【记录键】开始计时。"
            )

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
            self.right_stick.set_value(0.0, 0.0)
        else:
            self._apply_test_stick(self.deadzone_current_m)

        self._log(f"deadzone -back => m={self.deadzone_current_m:.4f} mode={self.mode}")

        if self.mode == "deadzone":
            self.status.set(
                f"【死区探测】已回退：m → {self.deadzone_current_m:.4f}\n"
                "开始缓慢移动：按【结束死区键】。"
            )
        else:
            self.status.set(
                f"【第1点微调】已回退死区候选值：m → {self.deadzone_current_m:.4f}\n"
                "确认后继续按【记录键】开始计时。"
            )

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

        self.right_stick.set_value(0.0, 0.0)

        if self.deadzone_mag <= 0.0:
            first_point_text = "无死区：第1点固定为 (0,0)。"
        else:
            first_point_text = f"死区≈{self.deadzone_mag:.4f}：第1点固定为 (死区,0)。"

        nm = self.measure_mag_list[0] if self.measure_mag_list else float(self.max_mag.get())
        self.status.set(
            "✅ 已结束死区，进入【曲线采样】。\n"
            f"{first_point_text}\n"
            f"测量点数量：{len(self.measure_mag_list)}（最后一点=MAX）\n"
            f"下一次测量幅值：m={nm:.4f}\n"
            "按【记录键】一次开始计时，转满一圈后再按一次结束并保存。\n"
            "（仅在第1个点开始前：仍可用【死区探测/回退死区】微调一次）"
        )

    def _can_adjust_deadzone_in_curve(self) -> bool:
        if not self.allow_adjust_after_deadzone:
            return False
        if self.mag_index != 0 or self.rep_index != 0:
            return False
        return True

    # ================= 曲线采样：记录键 =================
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

            self.status.set(
                f"计时开始：m={m:.4f}（第 {self.rep_index + 1}/{int(self.repeats_per_mag.get())} 次）\n"
                f"点进度：{self.mag_index + 1}/{len(self.measure_mag_list)}\n"
                "转满一圈后再按【记录键】结束并保存。"
            )
            return

        t1 = time.perf_counter()
        dt = t1 - (self.t0 or t1)

        m = self.measure_mag_list[self.mag_index] if self.measure_mag_list else float(self.max_mag.get())
        self.results.append({"magnitude": float(m), "repeat_index": int(self.rep_index), "seconds": float(dt), "flag": ""})

        self._log(f"record END mag_index={self.mag_index} rep={self.rep_index} m={m:.4f} dt={dt:.6f}")

        self.rep_index += 1
        self.in_trial = False
        self.t0 = None
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
        self.status.set(
            f"已记录：m={m:.4f} 用时 {dt:.4f}s\n"
            f"下一步：m={nm:.4f}\n"
            f"点进度：{self.mag_index + 1}/{len(self.measure_mag_list)}\n"
            "按【记录键】开始下一圈。"
        )

    def _apply_test_stick(self, m):
        m = float(m)
        d = self.direction.get()
        if d == "right":
            self.right_stick.set_value(m, 0.0)
        elif d == "left":
            self.right_stick.set_value(-m, 0.0)
        elif d == "up":
            self.right_stick.set_value(0.0, m)
        elif d == "down":
            self.right_stick.set_value(0.0, -m)

    # ================= keepalive =================
    def _keepalive_btn_code(self):
        name = (self.keepalive_btn_name.get() or "").strip()
        mapping = {
            "方块/ X": ("square", "x"),
            "叉/ A": ("cross", "a"),
            "圆/ B": ("circle", "b"),
            "三角/ Y": ("triangle", "y"),
            "L1/ LB": ("l1", "lb"),
            "R1/ RB": ("r1", "rb"),
            "Share/ Back": ("share", "back"),
            "Options/ Start": ("options", "start"),
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
                title="keepalive 点按失败",
                cause="可能是虚拟手柄当前不可用/驱动异常（偏环境问题）",
                action="尝试停止测试并重新开启模拟手柄；或重启电脑后再试。",
                who="USER_ENV",
            )

    # ================= 测试期间长按 =================
    def _hold_target(self):
        name = (self.hold_key_name.get() or "").strip()

        if name.startswith("左扳机"):
            return ("trigger", "l2")
        if name.startswith("右扳机"):
            return ("trigger", "r2")

        mapping = {
            "L1/ LB": ("l1", "lb"),
            "R1/ RB": ("r1", "rb"),
            "方块/ X": ("square", "x"),
            "叉/ A": ("cross", "a"),
            "圆/ B": ("circle", "b"),
            "三角/ Y": ("triangle", "y"),
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
                title="长按按键应用失败",
                cause="虚拟手柄/驱动状态异常或接口不支持（偏环境问题）",
                action="先关闭长按功能；确认模拟手柄可用后再启用。",
                who="USER_ENV",
            )

    # ================= 输出曲线/反曲线（百分比交换点） =================
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
                    title="没有有效记录",
                    cause="通常是用户没按记录键完成“开始/结束”两次，或测试中断（用户操作问题）",
                    action="重新测试：每个点按一次开始计时，转满一圈后再按一次结束。",
                    who="USER_OP",
                )
                messagebox.showerror("失败", f"没有有效记录。\n\n日志：{self.log_path}")
                return

            df_ok = df[df["seconds"].notna()].copy()
            if df_ok.empty:
                self._log("_finish_and_save: df_ok empty", level="error")
                self._log_user_hint(
                    title="计时结果为空",
                    cause="可能是记录流程没有完成（用户操作问题）",
                    action="确保每次记录：先按一次开始，再按一次结束。",
                    who="USER_OP",
                )
                messagebox.showerror("失败", f"没有有效计时记录（seconds为空）。\n\n日志：{self.log_path}")
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
                    title="统计结果为空",
                    cause="数据不足或记录过程异常（更偏用户操作/中断）",
                    action="重新测试，确保每个点记录次数>0。",
                    who="USER_OP",
                )
                messagebox.showerror("失败", f"统计结果为空。\n\n日志：{self.log_path}")
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

            self._plot_curve(
                plot_x_disp,
                plot_y_disp,
                title="游戏实际灵敏度（显示坐标）",
                xlabel="摇杆偏移（显示坐标）",
                ylabel="游戏实际灵敏度（显示坐标）",
                filename="曲线图.png",
                with_coords=False,
                xlim_max=Xmax,
                ylim_max=Ymax,
            )
            self._log("save: 曲线图.png OK")

            self._plot_curve(
                plot_x_disp,
                plot_y_disp,
                title="游戏实际灵敏度（显示坐标）",
                xlabel="摇杆偏移（显示坐标）",
                ylabel="游戏实际灵敏度（显示坐标）",
                filename="带坐标曲线图.png",
                with_coords=True,
                xlim_max=Xmax,
                ylim_max=Ymax,
            )
            self._log("save: 带坐标曲线图.png OK")

            inv_x = []
            inv_y = []
            table = []

            for i, (x_d, y_d) in enumerate(zip(plot_x_disp, plot_y_disp), start=1):
                px = 0.0 if Ymax <= 1e-12 else float(y_d) / float(Ymax)
                py = 0.0 if Xmax <= 1e-12 else float(x_d) / float(Xmax)

                x_inv = px * Xmax
                y_inv = py * Ymax

                x_inv = max(0.0, min(Xmax, x_inv))
                y_inv = max(0.0, min(Ymax, y_inv))

                inv_x.append(x_inv)
                inv_y.append(y_inv)

                table.append(
                    {
                        "point_index(1-based)": i,
                        "forward_x": float(x_d),
                        "forward_y": float(y_d),
                        "inv_x": float(x_inv),
                        "inv_y": float(y_inv),
                        "note": "inv_x=(forward_y/Ymax)*Xmax ; inv_y=(forward_x/Xmax)*Ymax",
                    }
                )

            pd.DataFrame(table).to_csv("compensation_table.csv", index=False, encoding="utf-8-sig")
            self._log("save: compensation_table.csv OK (one-to-one percent swap)")

            self._plot_curve(
                inv_x,
                inv_y,
                title="反曲线（百分比交换：与正向点一一对应）",
                xlabel="反曲线 X（显示坐标）",
                ylabel="反曲线 Y（显示坐标）",
                filename="反曲线图.png",
                with_coords=False,
                xlim_max=Xmax,
                ylim_max=Ymax,
            )
            self._log("save: 反曲线图.png OK (one-to-one percent swap)")

            self._plot_curve(
                inv_x,
                inv_y,
                title="反曲线（百分比交换：与正向点一一对应）",
                xlabel="反曲线 X（显示坐标）",
                ylabel="反曲线 Y（显示坐标）",
                filename="带坐标反曲线图.png",
                with_coords=True,
                xlim_max=Xmax,
                ylim_max=Ymax,
            )
            self._log("save: 带坐标反曲线图.png OK (one-to-one percent swap)")

            try:
                if self.gamepad:
                    self.gamepad.release_hold()
            except Exception:
                self._log("_finish_and_save: release_hold exception", level="warning")
            self._hold_applied = False

            self.status.set(
                "✅ 完成：已输出\n"
                "  - 曲线图.png / 带坐标曲线图.png\n"
                "  - 反曲线图.png / 带坐标反曲线图.png\n"
                "  - results.csv / curve_summary.csv / compensation_table.csv\n"
                f"  - 日志：{self.log_path}\n\n"
                "说明：反曲线点数与正向曲线点数完全一致，并按“百分比交换”与每个正向点一一对应。"
            )
            messagebox.showinfo("完成", f"输出完成（文件在程序目录）。\n\n日志：{self.log_path}")
            self._log("_finish_and_save: SUCCESS")

        except Exception:
            if self.logger:
                self.logger.exception("_finish_and_save: EXCEPTION")
            self._log_user_hint(
                title="输出阶段异常",
                cause="更像代码/环境异常（需要看 traceback），用户很难仅靠操作解决",
                action="把日志发给作者（尤其是包含 Traceback 的那段）。",
                who="BUG",
            )
            try:
                messagebox.showerror("输出失败", f"输出阶段发生异常。\n\n日志：{self.log_path}")
            except Exception:
                pass
        finally:
            self._test_running = False
            self.is_armed = False
            self.in_trial = False
            self.mode = "idle"
            # ✅ v1.6beta：不再在 finish_and_save 停止日志（日志仅 on_close 停止）

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
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]

        plt.figure(figsize=(8.6, 5.6))
        plt.plot(x_list, y_list, "-", linewidth=2)

        for i, (x, y) in enumerate(zip(x_list, y_list), start=1):
            c = colors[(i - 1) % len(colors)]
            plt.scatter([x], [y], s=55, color=c, zorder=3)

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)

        if xlim_max is not None:
            plt.xlim(0, float(xlim_max))
        if ylim_max is not None:
            plt.ylim(0, float(ylim_max))

        if with_coords:
            x_text = 0.72
            y_text = 0.92
            dy = 0.055
            for idx, (x, y) in enumerate(zip(x_list, y_list), start=1):
                c = colors[(idx - 1) % len(colors)]
                s = f"{idx}: ({x:.1f}, {y:.1f})"
                plt.gcf().text(x_text, y_text, s, color=c, fontsize=10, ha="left", va="center")
                y_text -= dy
                if y_text < 0.06:
                    break

        plt.tight_layout()
        plt.savefig(filename, dpi=220)
        plt.close()

    # ================= 输出线程 =================
    def _output_loop(self):
        hz = 100.0
        interval = 1.0 / hz
        while self.running:
            try:
                if self.emu_enabled and self.gamepad is not None:
                    if self.mode == "deadzone" or self.in_trial:
                        self._maybe_keepalive()

                    self._apply_hold_state()

                    lx, ly = self.left_stick.get_value()
                    rx, ry = self.right_stick.get_value()
                    self.gamepad.set_sticks(lx, ly, rx, ry)
            except Exception:
                pass
            time.sleep(interval)

    def on_close(self):
        self._log("on_close")

        if self.is_armed or self._test_running or self.mode != "idle":
            try:
                ok = messagebox.askyesno("确认退出", "测试进行中，确定要退出吗？（将中止本次测试）")
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
