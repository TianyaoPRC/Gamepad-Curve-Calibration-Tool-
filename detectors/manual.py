import keyboard
from .base import AngleDetector


class ManualKeyDetector(AngleDetector):
    def __init__(self, start_key: str = "F7", stop_key: str = "F8", abort_key: str = "ESC"):
        self.start_key = start_key
        self.stop_key = stop_key
        self.abort_key = abort_key

    def wait_start(self) -> None:
        print(f"[手动模式] 按 {self.start_key} 开始计时；按 {self.abort_key} 退出。")
        while True:
            if keyboard.is_pressed(self.abort_key):
                raise KeyboardInterrupt
            if keyboard.is_pressed(self.start_key):
                keyboard.wait(self.start_key)
                return

    def wait_stop(self) -> None:
        print(f"[手动模式] 观察到转回起始方向后按 {self.stop_key} 停止计时。")
        while True:
            if keyboard.is_pressed(self.abort_key):
                raise KeyboardInterrupt
            if keyboard.is_pressed(self.stop_key):
                keyboard.wait(self.stop_key)
                return
