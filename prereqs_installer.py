# -*- coding: utf-8 -*-
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from typing import Optional, List, Tuple


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _base_dir() -> str:
    # onefile 模式下资源会解压到 sys._MEIPASS
    if _is_frozen() and hasattr(sys, "_MEIPASS"):
        return str(getattr(sys, "_MEIPASS"))
    return os.path.dirname(os.path.abspath(__file__))


def _prereqs_dir() -> str:
    return os.path.join(_base_dir(), "prereqs")


def _run_sc_query(service_name: str) -> Tuple[bool, str]:
    try:
        cp = subprocess.run(
            ["sc", "query", service_name],
            capture_output=True,
            text=True,
            shell=False,
        )
        out = (cp.stdout or "") + (cp.stderr or "")
        ok = (cp.returncode == 0) and ("SERVICE_NAME" in out or "STATE" in out)
        return ok, out
    except Exception as e:
        return False, repr(e)


def is_vigem_installed() -> bool:
    # ViGEmBus 服务名通常为 ViGEmBus
    ok, _ = _run_sc_query("ViGEmBus")
    return ok


def _find_exe_by_keywords(folder: str, keywords: List[str]) -> Optional[str]:
    if not os.path.isdir(folder):
        return None
    items = []
    for fn in os.listdir(folder):
        if not fn.lower().endswith(".exe"):
            continue
        low = fn.lower()
        if all(k.lower() in low for k in keywords):
            items.append(fn)
    if not items:
        return None
    items.sort()
    return os.path.join(folder, items[0])


def _find_vigem_installer(folder: str) -> Optional[str]:
    # 优先找名字包含 "vigem" 的 exe
    path = _find_exe_by_keywords(folder, ["vigem"])
    if path:
        return path
    # 兜底：如果只有一个 exe，就用它
    exes = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".exe")] if os.path.isdir(folder) else []
    exes = [p for p in exes if os.path.isfile(p)]
    if len(exes) == 1:
        return exes[0]
    return None


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _elevate_and_run(exe_path: str, args: Optional[List[str]] = None) -> int:
    """
    用 UAC 提权运行安装器。返回值是 ShellExecuteW 的结果（>32 表示成功启动）。
    """
    if args is None:
        args = []
    params = " ".join([_quote(a) for a in args])
    # 0: HWND
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, params, None, 1)
    return int(ret)


def _quote(s: str) -> str:
    if not s:
        return '""'
    if any(ch in s for ch in [' ', '\t', '"']):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _msgbox(title: str, message: str, kind: str = "info") -> None:
    # 避免你项目不想引入额外 GUI 库，这里用 tkinter 自带消息框
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        if kind == "askyesno":
            # 返回由调用者处理
            root.destroy()
            return
        if kind == "error":
            messagebox.showerror(title, message)
        elif kind == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        # 如果消息框失败，就退化为控制台输出
        print(f"[{title}] {message}")


def _ask_yes_no(title: str, message: str) -> bool:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        ok = messagebox.askyesno(title, message)
        root.destroy()
        return bool(ok)
    except Exception:
        # 无 GUI 就默认否，避免误安装
        print(f"[{title}] {message}")
        return False


def ensure_prereqs_or_exit() -> None:
    """
    检查 ViGEmBus。未安装则引导安装（会申请管理员权限）。
    - 安装器启动后，提示用户安装完成再重新打开程序（更稳）
    """
    prereqs = _prereqs_dir()

    if is_vigem_installed():
        return

    vigem_installer = _find_vigem_installer(prereqs)
    if not vigem_installer:
        _msgbox(
            "缺少依赖",
            "检测到未安装 ViGEmBus（虚拟手柄驱动），但在 prereqs/ 中未找到安装器 exe。\n"
            "请把 ViGEmBus 安装器放进 prereqs/ 后再运行。",
            kind="error",
        )
        raise SystemExit(2)

    ok = _ask_yes_no(
        "需要安装驱动",
        "首次运行需要安装 ViGEmBus（虚拟手柄驱动），否则无法创建虚拟手柄。\n\n"
        "点击“是”将以管理员权限启动安装器（会弹 UAC）。\n"
        "安装完成后请重新打开本程序。\n\n"
        "是否现在安装？",
    )
    if not ok:
        raise SystemExit(3)

    # 用 UAC 提权启动安装器
    ret = _elevate_and_run(vigem_installer, [])
    if ret <= 32:
        _msgbox(
            "启动安装器失败",
            f"无法启动安装器（ShellExecute 返回 {ret}）。\n"
            "可能被权限/策略阻止，请手动以管理员身份运行 prereqs 中的安装器。",
            kind="error",
        )
        raise SystemExit(4)

    # 这里不等待安装器结束（等待很容易卡死或权限边界问题），提示用户装完重开
    _msgbox(
        "请完成安装",
        "安装器已启动。\n\n请完成 ViGEmBus 安装后，关闭安装器并重新打开本程序。",
        kind="info",
    )
    raise SystemExit(0)
