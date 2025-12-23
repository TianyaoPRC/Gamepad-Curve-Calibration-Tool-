# -*- coding: utf-8 -*-
from __future__ import annotations

import runpy

from prereqs_installer import ensure_prereqs_or_exit


def _start_app() -> None:
    # 兼容不同入口写法：ui_app.main() / ui_app.run() / 直接运行 ui_app
    try:
        import ui_app  # type: ignore

        if hasattr(ui_app, "main") and callable(ui_app.main):
            ui_app.main()
            return
        if hasattr(ui_app, "run") and callable(ui_app.run):
            ui_app.run()
            return

        # 都没有的话：按脚本方式执行 ui_app 模块
        runpy.run_module("ui_app", run_name="__main__")
    except Exception:
        # 兜底：还是按模块方式跑一遍
        runpy.run_module("ui_app", run_name="__main__")


def main() -> None:
    # 1) 先确保驱动/前置依赖就绪（未就绪会引导安装并退出）
    ensure_prereqs_or_exit()

    # 2) 再启动你的程序
    _start_app()


if __name__ == "__main__":
    main()
