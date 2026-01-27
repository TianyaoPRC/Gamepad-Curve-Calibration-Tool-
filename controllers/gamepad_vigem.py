# -*- coding: utf-8 -*-
"""
ViGEm 虚拟手柄封装，支持 DS4 和 Xbox360
- UI 传 -1..1（y>0 向上）
- DS4 y 需反转（底层 y>0 向下）
- Xbox360 不反转
- 初始化和异常时都回中（防止摇杆卡死）
- keepalive 只点按钮，不动摇杆
- 支持按住按钮/扳机（长按）
"""

from __future__ import annotations

import time
import vgamepad as vg


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    if v is None:
        return 0.0
    try:
        v = float(v)
    except Exception:
        return 0.0
    return max(lo, min(hi, v))


def _clamp01(v: float) -> float:
    return _clamp(v, 0.0, 1.0)


def _to_short(x: float) -> int:
    # 转 -32767..32767
    x = _clamp(x)
    return int(round(x * 32767))


def _to_byte_0_255_from_minus1_1(x: float) -> int:
    # 转 0..255（某些 DS4 用这个）
    x = _clamp(x)
    return int(round((x + 1.0) * 0.5 * 255))


def _to_byte_0_255_from_0_1(x: float) -> int:
    # 转 0..255
    x = _clamp01(x)
    return int(round(x * 255))


class VirtualGamepad:
    """
    kind: "ds4" or "xbox360"
    """

    def __init__(self, kind: str = "ds4"):
        kind = (kind or "").lower().strip()
        if kind not in ("ds4", "xbox360"):
            kind = "ds4"
        self.kind = kind

        # DS4 需要反转 Y（底层 y 反向）
        self.ds4_invert_y = (self.kind == "ds4")

        if self.kind == "xbox360":
            self.pad = vg.VX360Gamepad()
        else:
            self.pad = vg.VDS4Gamepad()

        self._held_btn_code = None
        self._held_btn_pressed = False
        self._held_l2 = 0
        self._held_r2 = 0

        # 初始化时回中
        self.neutral()

    # -----摇杆-----
    def set_sticks(self, lx: float, ly: float, rx: float, ry: float):
        # 收到 -1..1（y>0 向上），DS4 需反转 y
        lx = _clamp(lx)
        ly = _clamp(ly)
        rx = _clamp(rx)
        ry = _clamp(ry)

        if self.ds4_invert_y:
            ly = -ly
            ry = -ry

        try:
            if self.kind == "xbox360":
                self.pad.left_joystick(x_value=_to_short(lx), y_value=_to_short(ly))
                self.pad.right_joystick(x_value=_to_short(rx), y_value=_to_short(ry))
                self.pad.update()
            else:
                # 优先用 float 接口（更稳）
                if hasattr(self.pad, "left_joystick_float"):
                    self.pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
                    self.pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
                else:
                    # 兼容旧版用 0..255
                    self.pad.left_joystick(
                        x_value=_to_byte_0_255_from_minus1_1(lx),
                        y_value=_to_byte_0_255_from_minus1_1(ly),
                    )
                    self.pad.right_joystick(
                        x_value=_to_byte_0_255_from_minus1_1(rx),
                        y_value=_to_byte_0_255_from_minus1_1(ry),
                    )
                self.pad.update()
        except Exception:
            # 异常就回中，防止摇杆失控
            self.neutral()

    def neutral(self):
        try:
            # 释放长按状态（按钮+扳机）
            self.release_hold()

            if self.kind == "xbox360":
                self.pad.left_joystick(x_value=0, y_value=0)
                self.pad.right_joystick(x_value=0, y_value=0)
                self.pad.left_trigger(value=0)
                self.pad.right_trigger(value=0)
                self.pad.update()
            else:
                if hasattr(self.pad, "left_joystick_float"):
                    self.pad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
                    self.pad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
                else:
                    self.pad.left_joystick(x_value=128, y_value=128)
                    self.pad.right_joystick(x_value=128, y_value=128)
                if hasattr(self.pad, "left_trigger"):
                    self.pad.left_trigger(value=0)
                if hasattr(self.pad, "right_trigger"):
                    self.pad.right_trigger(value=0)
                self.pad.update()
        except Exception:
            pass

    # -----keepalive: 点按钮不动摇杆-----
    def tap_keepalive_button(self, btn_code: str, ms: int = 30):
        # DS4/X360 按钮列表
        # DS4: square/cross/circle/triangle/l1/r1/share/options
        # X360: a/b/x/y/lb/rb/back/start
        btn_code = (btn_code or "").lower().strip()
        ms = int(ms or 30)
        ms = max(10, min(200, ms))

        try:
            if self.kind == "xbox360":
                mapping = {
                    "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    "lb": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    "rb": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    "back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                }
                b = mapping.get(btn_code, vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
                self.pad.press_button(button=b)
                self.pad.update()
                time.sleep(ms / 1000.0)
                self.pad.release_button(button=b)
                self.pad.update()
                return

            # DS4
            mapping = {
                "square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                "cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
                "circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                "triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                "l1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
                "r1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                "share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
                "options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
            }
            b = mapping.get(btn_code, vg.DS4_BUTTONS.DS4_BUTTON_SQUARE)
            self.pad.press_button(button=b)
            self.pad.update()
            time.sleep(ms / 1000.0)
            self.pad.release_button(button=b)
            self.pad.update()
        except Exception:
            pass

    # -----长按: 按钮/扳机-----
    def hold_button(self, btn_code: str, pressed: bool):
        # 持续按住某个按钮（不是扳机）
        # DS4: square/cross/circle/triangle/l1/r1/share/options
        # X360: a/b/x/y/lb/rb/back/start
        btn_code = (btn_code or "").lower().strip()
        pressed = bool(pressed)

        # 去抖：状态不变就不重复发
        if btn_code == self._held_btn_code and pressed == self._held_btn_pressed:
            return

        # 如果切换到另一个按钮，先释放旧的
        if self._held_btn_pressed and self._held_btn_code and self._held_btn_code != btn_code:
            try:
                self.hold_button(self._held_btn_code, False)
            except Exception:
                pass

        try:
            if self.kind == "xbox360":
                mapping = {
                    "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                    "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                    "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                    "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                    "lb": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                    "rb": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                    "back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                    "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                }
                b = mapping.get(btn_code)
                if b is None:
                    # 不认识就不处理
                    self._held_btn_code = btn_code
                    self._held_btn_pressed = pressed
                    return
                if pressed:
                    self.pad.press_button(button=b)
                else:
                    self.pad.release_button(button=b)
                self.pad.update()
            else:
                mapping = {
                    "square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                    "cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
                    "circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                    "triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                    "l1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
                    "r1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                    "share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
                    "options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
                }
                b = mapping.get(btn_code)
                if b is None:
                    self._held_btn_code = btn_code
                    self._held_btn_pressed = pressed
                    return
                if pressed:
                    self.pad.press_button(button=b)
                else:
                    self.pad.release_button(button=b)
                self.pad.update()
        except Exception:
            pass

        self._held_btn_code = btn_code
        self._held_btn_pressed = pressed

    def hold_triggers(self, l2: float = 0.0, r2: float = 0.0):
        # 持续按住扳机（0..1）
        l2b = _to_byte_0_255_from_0_1(l2)
        r2b = _to_byte_0_255_from_0_1(r2)

        # 去抖
        if l2b == self._held_l2 and r2b == self._held_r2:
            return

        try:
            if self.kind == "xbox360":
                self.pad.left_trigger(value=l2b)
                self.pad.right_trigger(value=r2b)
                self.pad.update()
            else:
                if hasattr(self.pad, "left_trigger"):
                    self.pad.left_trigger(value=l2b)
                if hasattr(self.pad, "right_trigger"):
                    self.pad.right_trigger(value=r2b)
                self.pad.update()
        except Exception:
            pass

        self._held_l2 = l2b
        self._held_r2 = r2b

    def release_hold(self):
        # 释放按钮
        try:
            if self._held_btn_code and self._held_btn_pressed:
                self.hold_button(self._held_btn_code, False)
        except Exception:
            pass
        self._held_btn_code = None
        self._held_btn_pressed = False

        # 释放扳机
        try:
            self.hold_triggers(0.0, 0.0)
        except Exception:
            pass
        self._held_l2 = 0
        self._held_r2 = 0
