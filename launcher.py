# -*- coding: utf-8 -*-
from __future__ import annotations

import runpy
import os
import sys
import json
import shutil

from prereqs_installer import ensure_prereqs_or_exit


def _get_user_languages_dir() -> str:
    """
    获取用户语言文件目录（仅使用外部语言文件）

    需求：
    - 打包后的程序同目录下生成 `languages/` 文件夹
    - 程序仅使用外部语言文件；若不存在则创建中文模板
    """
    base_dir = _get_app_base_dir()
    return os.path.join(base_dir, "languages")


def _get_app_base_dir() -> str:
    """获取应用基础目录"""
    try:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        else:
            return os.getcwd()
    except Exception:
        return os.getcwd()


def _ensure_default_language_files() -> None:
    """
    确保用户语言文件夹存在，且包含完整的语言文件
    首次启动时，将内置的语言模板文件复制到用户可访问的目录
    
    优先级：
    1. 首先查找内置的 languages/ 目录并复制文件
    2. 如果内置目录不存在，从内存生成完整模板写入用户目录
    这样确保即使 PyInstaller 没有打包 languages/，也能有完整翻译
    """
    user_lang_dir = _get_user_languages_dir()
    
    # 创建用户语言文件夹
    try:
        os.makedirs(user_lang_dir, exist_ok=True)
    except Exception:
        return
    
    # 从内置资源复制语言文件（PyInstaller 会解压到 _MEIPASS）
    app_base = _get_app_base_dir()
    source_lang_dir = None

    # 优先：PyInstaller 解压目录
    try:
        meipass_dir = getattr(sys, "_MEIPASS", None)
        if meipass_dir:
            meipass_lang = os.path.join(meipass_dir, "languages")
            if os.path.isdir(meipass_lang):
                source_lang_dir = meipass_lang
    except Exception:
        pass

    # 其次：当前模块旁的 languages（开发环境）
    if source_lang_dir is None:
        module_lang_dir = os.path.join(os.path.dirname(__file__), "languages")
        if os.path.isdir(module_lang_dir):
            source_lang_dir = module_lang_dir
    
    # 最后：应用目录下的 languages（如果用户提前放置了一份）
    if source_lang_dir is None:
        bundled_lang_dir = os.path.join(app_base, "languages")
        if os.path.isdir(bundled_lang_dir):
            source_lang_dir = bundled_lang_dir
    
    # 需要确保至少有中文和英文两个完整的语言文件
    files_copied = []
    
    if source_lang_dir is not None:
        # 复制内置语言文件到用户目录
        try:
            for filename in os.listdir(source_lang_dir):
                if filename.endswith(".json"):
                    src = os.path.join(source_lang_dir, filename)
                    dst = os.path.join(user_lang_dir, filename)
                    
                    # 只在用户目录中的文件不存在时才复制
                    # 这样保护用户已有的自定义翻译
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        files_copied.append(filename)
        except Exception as e:
            print(f"复制语言文件时出错: {e}")  # 调试输出
    
    # 检查是否已有完整的中文和英文文件
    zh_cn_path = os.path.join(user_lang_dir, "zh_CN.json")
    en_us_path = os.path.join(user_lang_dir, "en_US.json")
    
    # 如果缺少任何一个必要的语言文件，使用生成的模板补充
    if not os.path.exists(zh_cn_path) or not os.path.exists(en_us_path):
        print("未找到完整的语言文件，使用内存模板生成...")  # 调试输出
        _generate_default_language_templates(user_lang_dir)


def _generate_default_language_templates(lang_dir: str) -> None:
    """生成默认的中文和英文语言模板"""
    # 完整的中文语言模板
    zh_cn_template = {
        "_language_name": "中文（简体）",
        "_language_code": "zh_CN",
        "_translator_note": "这是本软件的多语言模板文件。用户可以复制此文件，改名为其他语言（如 en_US.json），并翻译所有的文本值。软件启动时会自动检测此文件夹中的所有 JSON 文件，用户可在软件中选择使用的语言。",

        "app": {
            "name": "游戏摇杆曲线探测器",
            "author": "刘云耀",
            "version": "v1.7beta"
        },

        "ui": {
            "settings_panel": "设置面板",
            "language_select": "界面语言",
            "language_label": "选择语言：",
            "gamepad": "虚拟手柄",
            "gamepad_type": "模拟类型：",
            "enable_emulation": "开启模拟手柄",
            "neutral": "回中（不重启设备）",
            "status": "状态：",
            "status_disabled": "未开启",
            "test_params": "测试参数",
            "sample_count": "采样点数量（2~100：指需要测量的点数，不含第1固定点）：",
            "repeats_per_mag": "每个采样点记录次数：",
            "magnitude_range": "幅值范围（用于\"非死区\"起点到最大）：",
            "min": "MIN",
            "max": "MAX",
            "test_direction": "测试方向（固定推右摇杆）：",
            "axis_config": "曲线显示坐标（例如 0~100 / 0~350）",
            "x_axis_max": "X轴最大值：",
            "y_axis_max": "Y轴最大值：",
            "deadzone_params": "死区探测参数",
            "deadzone_step": "探测步长（仍不动时使用）：",
            "deadzone_back_step": "回退步长（动得过快时使用，可回到 0）：",
            "keepalive": "保持手柄输入（防游戏切回键鼠）",
            "keepalive_enable": "启用（死区探测与计时等待期间会周期性点按一个手柄按键）",
            "keepalive_interval": "间隔(ms)：",
            "keepalive_button": "按键：",
            "hold": "测试期间长按按键（默认关闭）",
            "hold_enable": "启用（测试期间持续按住指定按键/扳机）",
            "hold_key": "长按键：",
            "hotkey": "热键设置（点击按钮后按键）",
            "hotkey_mode": "热键模式：",
            "set_start_key": "设置开始键",
            "set_record_key": "设置记录键",
            "set_deadzone_key": "设置死区探测键",
            "set_deadzone_back_key": "设置回退死区键",
            "set_end_deadzone_key": "设置结束死区键",
            "set_retry_key": "设置重测键",
            "control": "控制",
            "start_test": "开始测试",
            "stop_reset": "停止/重置",
            "export_and_charts": "导出与图表",
            "generate_charts": "生成曲线图（当前）",
            "generate_from_csv": "从CSV生成曲线图",
            "generate_charts_prompt_title": "图表待生成",
            "generate_charts_prompt_body": "CSV 已保存。点击【生成曲线图】立即出图，或稍后用【从CSV生成】。",
            "select_csv_title": "选择CSV文件生成曲线图",
            "all_files": "所有文件",
            "author_footer": "作者署名：哔哩哔哩：{author}   |   版本：{version}",
            "left_stick": "左摇杆（鼠标拖动）",
            "right_stick": "右摇杆（鼠标拖动）",
            "info_title": "状态 / 操作流程",
            "direction_right": "右",
            "direction_left": "左",
            "direction_up": "上",
            "direction_down": "下",
            "info_description": "用途：测量\"游戏对手柄做的输入优化曲线\"（不是硬件死区）。\n\n操作流程：\n  1) 点击【开启模拟手柄】后，切回游戏。\n  2) 在【鼠标拖动虚拟摇杆】上完成测试（需要多次完整推圆周）。\n  3) 点击【开始测试】，app会自动采样、计时、输出结果。\n  4) 【保存CSV】导出，可用 Excel 查看或进一步处理。\n\n快捷键：F6=开始、F7=记录点、F8=死区探测、F9=回退、F10=结束死区、F11=重测。\n\n常见问题：摇杆坐标\"抖动\"\"不顺滑\" → 检查游戏本身是否有硬件死区 / 增益。",
            "button_square": "方块/ X",
            "button_cross": "叉/ A",
            "button_circle": "圆/ B",
            "button_triangle": "三角/ Y",
            "button_l1": "L1/ LB",
            "button_r1": "R1/ RB",
            "button_share": "Share/ Back",
            "button_options": "Options/ Start",
            "trigger_l2": "左扳机（L2/ LT）",
            "trigger_r2": "右扳机（R2/ RT）",
            "hotkey_hint_symbol": "检测到你绑定了【数字/符号键】（单字符）。\n✅ 已自动使用：keyboard_scan（更适合全屏游戏/数字符号键）。\n提示：把这些数字/符号键改成 F键/字母/方向键等后，会自动切回 keyboard_name。",
            "hotkey_hint_normal": "当前热键不包含数字/符号键。\n✅ 已自动使用：keyboard_name（更直观稳定，推荐 F键/字母）。\n若你改绑为数字/符号键，会自动切到 keyboard_scan。",
            "hotkey_hint_failed": "⚠️ 键名模式热键注册失败，已自动切换到 keyboard_scan。\n可能原因：全屏游戏/权限不足/杀软拦截/某些键名不被 keyboard 识别。\n建议：优先绑定 F键/字母；必要时以管理员运行或关闭拦截。",
            "hotkey_keys_label": "开始键：{start_key}    记录键：{record_key}    重测键：{retry_key}\n死区探测键：{deadzone_key}    回退死区键：{deadzone_back_key}\n结束死区键：{end_deadzone_key}\n当前热键模式：{mode}（会按绑定按键自动适配）"
        },

        "status": {
            "emulation_enabled": "状态：已开启（{type}）",
            "emulation_already_enabled": "模拟手柄已开启：不会重启设备。",
            "emulation_enabled_success": "✅ 已开启模拟手柄。请切回游戏后再开始测试。",
            "emulation_not_enabled": "尚未开启模拟手柄。",
            "neutral_success": "已回中（不会断开/重启虚拟手柄）。"
        },

        "charts": {
            "curve_title": "游戏实际灵敏度（显示坐标）",
            "curve_xlabel": "摇杆偏移（显示坐标）",
            "curve_ylabel": "游戏实际灵敏度（显示坐标）",
            "inverse_title": "反曲线（百分比交换：与正向点一一对应）",
            "inverse_xlabel": "反曲线 X（显示坐标）",
            "inverse_ylabel": "反曲线 Y（显示坐标）"
        },

        "messages": {
            "initial_hint": "提示：先点击【开启模拟手柄】。",
            "emulation_already_on": "模拟手柄已开启：不会重启设备。",
            "emulation_enabled": "✅ 已开启模拟手柄。请切回游戏后再开始测试。",
            "emulation_not_enabled": "尚未开启模拟手柄。",
            "neutral_done": "已回中（不会断开/重启虚拟手柄）。",
            "hotkey_mode_changed": "✅ 热键模式：{mode}（按绑定按键自动适配）",
            "hotkey_mode_forbidden": "⚠️ 测试进行中，禁止切换热键模式（请先停止/重置）。",
            "hotkey_registration_failed": "⚠️ 键名模式注册失败，已自动切换到 keyboard_scan（详情见日志）。",
            "hotkey_capture_waiting": "请按下你要绑定的键…（不会弹窗打断）",
            "hotkey_capture_scan": "等待按键：扫描码模式捕获中…（直接按键即可）",
            "hotkey_capture_name": "等待按键：键名模式捕获中…（在窗口里按键即可）",
            "hotkey_capture_forbidden": "⚠️ 测试进行中，禁止修改热键（请先停止/重置）。",
            "hotkey_updated": "✅ 热键已更新（模式会自动适配）",
            "test_stopped": "已停止并重置（虚拟手柄不会断开/重启）。",
            "test_started": "✅ 已开始测试：进入【死区探测】。\n当前幅值：m={magnitude:.4f}\n不动：按【死区探测键】继续增加。\n动得过快：按【回退死区键】回退（可回到 0）。\n开始缓慢移动：按【结束死区键】确认死区并进入曲线采样。",
            "deadzone_increased": "【死区探测】仍不动：m → {magnitude:.4f}\n开始缓慢移动：按【结束死区键】。",
            "deadzone_adjust": "【第1点微调】已增加死区候选值：m → {magnitude:.4f}\n确认后继续按【记录键】开始计时。",
            "deadzone_decreased": "【死区探测】已回退：m → {magnitude:.4f}\n开始缓慢移动：按【结束死区键】。",
            "deadzone_adjust_back": "【第1点微调】已回退死区候选值：m → {magnitude:.4f}\n确认后继续按【记录键】开始计时。",
            "deadzone_ended": "✅ 已结束死区，进入【曲线采样】。\n{first_point_text}\n测量点数量：{point_count}\n下一次测量幅值：m={next_mag:.4f}\n按【记录键】一次开始计时，转满一圈后再按一次结束并保存。\n（仅在第1个点开始前：仍可用【死区探测/回退死区】微调一次）",
            "record_start": "计时开始：m={magnitude:.4f}（第 {repeat}/{total} 次）\n点进度：{current}/{total_points}\n转满一圈后再按【记录键】结束并保存。",
            "record_saved": "已记录：m={magnitude:.4f} 用时 {time:.4f}s\n下一步：m={next_mag:.4f}\n点进度：{current}/{total_points}\n按【记录键】开始下一圈。",
            "retry_no_test": "⚠️ 还未开始任何测试，无法重测。",
            "test_not_enabled": "请先点击【开启模拟手柄】。",
            "ready_to_generate_charts": "✅ CSV 已保存，可生成曲线图。",
            "param_error": "按提示修正：采样点 2~10；且 0<=MIN<MAX<=1。",
            "retry_reset_message": "【重新测试】已重置当前点（m={magnitude:.4f}）\\n需重测次数：{repeat_count}\\n按【记录键】开始重新测试。",
            "first_point_text_no_deadzone": "无死区：第1点固定为 (0,0)。",
            "first_point_text_with_deadzone": "死区≈{magnitude:.4f}：第1点固定为 (死区,0)。",
            "log_path_prefix": "日志：",
            "no_valid_records_msg": "没有有效记录。"
        },

        "hints": {
            "log_init_failed_title": "日志初始化失败",
            "log_write_failed_title": "日志目录不可写",
            "log_write_failed_cause": "多半是系统权限/杀软拦截/路径不可写（用户环境问题）",
            "log_write_failed_action": "建议把程序放到非系统盘的普通文件夹，或以管理员运行；或关闭拦截后再试。",
            "log_header_msg1": "这份日志给普通用户看的：遇到问题可先看包含 [CAUSE]/[ACTION] 的几行。",
            "log_header_msg2": "重点关键词：HOTKEY / enable_emulation / start_test / record / finish_and_save。",
            "log_write_test_failed": "[WRITE_TEST] FAILED (目录不可写/被拦截)",
            "hotkey_during_test_title": "测试过程中无法重绑热键",
            "hotkey_during_test_cause": "测试中改热键会导致热键触发异常/丢失（用户操作问题）",
            "hotkey_during_test_action": "先停止/重置，再设置热键。",
            "hotkey_bind_fail_title": "尝试在测试中改热键",
            "hotkey_capture_fail_title": "扫描码捕获失败",
            "hotkey_capture_fail_cause": "可能是特殊键/系统拦截/权限问题（环境问题）",
            "hotkey_capture_fail_action": "尝试绑定其他键，或以管理员运行。",
            "enable_gamepad_fail_title": "开启虚拟手柄失败",
            "enable_gamepad_fail_dialog": "开启失败",
            "enable_gamepad_fail_cause": "可能是 ViGEm 驱动/权限/杀软拦截/系统环境问题（偏环境问题）",
            "enable_gamepad_fail_action": "建议：确认安装 ViGEmBus；以管理员运行；关闭拦截；重启后再试。",
            "no_emulation_start_title": "未开启模拟手柄就开始测试",
            "no_emulation_start_dialog_title": "未开启模拟",
            "no_emulation_start_dialog_msg": "请先点击【开启模拟手柄】。",
            "no_emulation_start_cause": "用户操作顺序错误（用户操作问题）",
            "no_emulation_start_action": "先开启模拟手柄，再开始测试。",
            "param_error_title": "参数错误导致无法开始测试",
            "param_error_dialog": "参数错误",
            "param_error_cause": "输入的参数不合法（用户操作问题）",
            "param_error_action": "按提示修正：采样点 2~10；且 0<=MIN<MAX<=1。",
            "hold_key_fail_title": "长按按键应用失败",
            "hold_key_fail_cause": "虚拟手柄状态异常或驱动问题（环境问题）",
            "hold_key_fail_action": "尝试重新开启/停止模拟手柄，或检查驱动。",
            "no_valid_records_title": "没有有效记录",
            "no_valid_records_cause": "测试过程中没有记录任何数据（用户操作问题）",
            "no_valid_records_action": "重新开始测试，按【记录键】保存数据。",
            "no_valid_records_dialog": "失败",
            "no_timing_records_title": "计时结果为空",
            "no_timing_records_cause": "记录数据中没有有效的计时信息（用户操作或软件问题）",
            "no_timing_records_action": "检查记录数据，或重新进行测试。",
            "no_analysis_title": "统计结果为空",
            "no_analysis_cause": "数据分析失败（可能是参数问题或软件bug）",
            "no_analysis_action": "检查测试数据是否完整，或查看日志获取更多信息。",
            "export_success_title": "完成",
            "export_success_msg": "输出完成（文件在程序目录）。",
            "export_fail_title": "输出失败",
            "export_fail_cause": "输出过程中发生异常（可能是权限或环境问题）",
            "export_fail_action": "检查程序目录权限，或查看日志获取更多信息。",
            "exit_confirm_title": "确认退出",
            "exit_confirm_msg": "测试进行中，确定要退出吗？（将中止本次测试）",
            "keepalive_tap_fail_title": "keepalive 点按失败",
            "keepalive_tap_fail_cause": "可能是虚拟手柄当前不可用/驱动异常（偏环境问题）",
            "keepalive_tap_fail_action": "尝试停止测试并重新开启模拟手柄；或重启电脑后再试。",
            "hold_key_apply_fail_title": "长按按键应用失败",
            "hold_key_apply_fail_cause": "虚拟手柄/驱动状态异常或接口不支持（偏环境问题）",
            "hold_key_apply_fail_action": "先关闭长按功能；确认模拟手柄可用后再启用。",
            "timing_result_empty_title": "计时结果为空",
            "timing_result_empty_cause": "可能是记录流程没有完成（用户操作问题）",
            "timing_result_empty_action": "确保每次记录：先按一次开始，再按一次结束。",
            "timing_result_empty_dialog": "没有有效计时记录（seconds为空）",
            "output_phase_error_title": "输出阶段异常",
            "output_phase_error_cause": "更像代码/环境异常（需要看 traceback），用户很难仅靠操作解决",
            "output_phase_error_action": "把日志发给作者（尤其是包含 Traceback 的那段）。",
            "output_phase_error_dialog": "输出阶段发生异常。",
            "stats_result_empty_title": "统计结果为空",
            "stats_result_empty_cause": "数据不足或记录过程异常（更偏用户操作/中断）",
            "stats_result_empty_action": "重新测试，确保每个点记录次数>0。",
            "stats_result_empty_dialog": "统计结果为空",
            "export_complete_status": "✅ 完成：已输出\\n  - 曲线图.png / 带坐标曲线图.png\\n  - 反曲线图.png / 带坐标反曲线图.png\\n  - results.csv / curve_summary.csv / compensation_table.csv\\n  - 日志：{log_path}\\n\\n说明：反曲线点数与正向曲线点数完全一致，并按\\\"百分比交换\\\"与每个正向点一一对应。",
            "language_switched_status": "✅ 语言已切换到：{lang_code}（图表将使用新语言）"
        },

        "errors": {
            "sample_count_invalid_type": "采样点数量必须是整数（2~100）。",
            "sample_count_out_of_range": "采样点数量范围：2~100。",
            "magnitude_range_invalid": "幅值范围必须满足：0 <= MIN < MAX <= 1。",
            "csv_format_not_supported": "CSV 格式不支持（需 results.csv 或 curve_summary.csv 结构）。"
        }
    }

    # 完整的英文语言模板
    en_us_template = {
        "_language_name": "English (US)",
        "_language_code": "en_US",
        "_translator_note": "This is the multilingual template file for the software. Users can copy this file, rename it to other languages (such as en_US.json), and translate all text values. The software will automatically detect all JSON files in this folder, and users can select the language to use in the software.",

        "app": {
            "name": "Game Joystick Curve Detector",
            "author": "Liu Yunyao",
            "version": "v1.7beta"
        },

        "ui": {
            "settings_panel": "Settings",
            "language_select": "Interface Language",
            "language_label": "Select Language:",
            "gamepad": "Virtual Gamepad",
            "gamepad_type": "Emulation Type:",
            "enable_emulation": "Enable Emulation",
            "neutral": "Neutral (No Restart)",
            "status": "Status:",
            "status_disabled": "Disabled",
            "test_params": "Test Parameters",
            "sample_count": "Sample Points (2~100: measurement points excluding 1st fixed point):",
            "repeats_per_mag": "Records Per Sample Point:",
            "magnitude_range": "Magnitude Range (from \"non-deadzone\" start to max):",
            "min": "MIN",
            "max": "MAX",
            "test_direction": "Test Direction (fixed push right stick):",
            "axis_config": "Curve Display Coordinates (e.g. 0~100 / 0~350)",
            "x_axis_max": "X Axis Max:",
            "y_axis_max": "Y Axis Max:",
            "deadzone_params": "Deadzone Detection Parameters",
            "deadzone_step": "Detection Step (when no movement):",
            "deadzone_back_step": "Retreat Step (when moving too fast, can go to 0):",
            "keepalive": "Keep Gamepad Input Active (prevent switching to mouse/keyboard)",
            "keepalive_enable": "Enable (periodically tap a button during deadzone detection & timing wait)",
            "keepalive_interval": "Interval(ms):",
            "keepalive_button": "Button:",
            "hold": "Hold Button During Test (disabled by default)",
            "hold_enable": "Enable (continuously hold specified button/trigger during test)",
            "hold_key": "Hold Button:",
            "hotkey": "Hotkey Settings (press key after clicking)",
            "hotkey_mode": "Hotkey Mode:",
            "set_start_key": "Set Start Key",
            "set_record_key": "Set Record Key",
            "set_deadzone_key": "Set Deadzone Key",
            "set_deadzone_back_key": "Set Deadzone Retreat Key",
            "set_end_deadzone_key": "Set End Deadzone Key",
            "set_retry_key": "Set Retry Key",
            "control": "Control",
            "start_test": "Start Test",
            "stop_reset": "Stop/Reset",
            "export_and_charts": "Export & Charts",
            "generate_charts": "Generate Charts (current)",
            "generate_from_csv": "Generate Charts from CSV",
            "generate_charts_prompt_title": "Charts pending",
            "generate_charts_prompt_body": "CSV saved. Click [Generate Charts] to render images now (or use [Generate from CSV] later).",
            "select_csv_title": "Select CSV to generate charts",
            "all_files": "All Files",
            "author_footer": "Author: Bilibili: {author}   |   Version: {version}",
            "left_stick": "Left Stick (Mouse Drag)",
            "right_stick": "Right Stick (Mouse Drag)",
            "info_title": "Status / Operation Process",
            "direction_right": "Right",
            "direction_left": "Left",
            "direction_up": "Up",
            "direction_down": "Down",
            "info_description": "Purpose: Measure the \"input optimization curve made by the game on the controller\" (not hardware deadzone).\n\nOperation Process:\n  1) Click [Enable Emulation], then switch back to game.\n  2) Complete the test on [Mouse Drag Virtual Sticks] (requires multiple complete rotations).\n  3) Click [Start Test], the app will automatically sample, time, and output results.\n  4) [Save CSV] to export, can be viewed in Excel or processed further.\n\nHotkeys: F6=Start, F7=Record Point, F8=Deadzone Test, F9=Retreat, F10=End Deadzone, F11=Retry.\n\nCommon Issues: Stick coordinates \"jitter\"\"not smooth\" → Check if the game itself has hardware deadzone / assist.",
            "button_square": "Square/ X",
            "button_cross": "Cross/ A",
            "button_circle": "Circle/ B",
            "button_triangle": "Triangle/ Y",
            "button_l1": "L1/ LB",
            "button_r1": "R1/ RB",
            "button_share": "Share/ Back",
            "button_options": "Options/ Start",
            "trigger_l2": "Left Trigger (L2/ LT)",
            "trigger_r2": "Right Trigger (R2/ RT)",
            "hotkey_hint_symbol": "Detected number/symbol key binding.\n✅ Auto-switched to keyboard_scan mode (better for fullscreen/symbol keys).\n Tip: Change symbol keys to F-keys/letters to auto-switch back to keyboard_name.",
            "hotkey_hint_normal": "No number/symbol keys detected.\n✅ Using keyboard_name mode (more intuitive, F-keys/letters recommended).\n If you bind symbol keys, will auto-switch to keyboard_scan.",
            "hotkey_hint_failed": "⚠️ keyboard_name mode registration failed, auto-switched to keyboard_scan.\n Possible causes: fullscreen game / insufficient permissions / antivirus / unrecognized key names.\n Suggestion: bind F-keys/letters; if needed, run as admin or disable antivirus hooks.",
            "hotkey_keys_label": "Start Key: {start_key}    Record Key: {record_key}    Retry Key: {retry_key}\nDeadzone Key: {deadzone_key}    Retreat Key: {deadzone_back_key}\nEnd Deadzone Key: {end_deadzone_key}\nCurrent Hotkey Mode: {mode} (will auto-adapt by bound key)"
        },

        "status": {
            "emulation_enabled": "Status: Enabled ({type})",
            "emulation_already_enabled": "Emulation already enabled: no device restart.",
            "emulation_enabled_success": "✅ Emulation enabled. Switch back to game before starting test.",
            "emulation_not_enabled": "Emulation not yet enabled.",
            "neutral_success": "Neutralized (no disconnect/restart of virtual gamepad)."
        },

        "charts": {
            "curve_title": "Game Actual Sensitivity (Display Coordinates)",
            "curve_xlabel": "Joystick Offset (Display Coordinates)",
            "curve_ylabel": "Game Actual Sensitivity (Display Coordinates)",
            "inverse_title": "Inverse Curve (Percentage Swap: One-to-One Correspondence with Forward Points)",
            "inverse_xlabel": "Inverse Curve X (Display Coordinates)",
            "inverse_ylabel": "Inverse Curve Y (Display Coordinates)"
        },

        "messages": {
            "initial_hint": "Hint: Click [Enable Emulation] first.",
            "emulation_already_on": "Emulation already enabled: no device restart.",
            "emulation_enabled": "✅ Emulation enabled. Switch back to game before starting test.",
            "emulation_not_enabled": "Emulation not yet enabled.",
            "neutral_done": "Neutralized (no disconnect/restart of virtual gamepad).",
            "hotkey_mode_changed": "✅ Hotkey Mode: {mode} (auto-adapt by bound key)",
            "hotkey_mode_forbidden": "⚠️ Test in progress, cannot switch hotkey mode (stop/reset first).",
            "hotkey_registration_failed": "⚠️ keyboard_name mode registration failed, auto-switched to keyboard_scan (see logs).",
            "hotkey_capture_waiting": "Press the key you want to bind… (no popup interrupt)",
            "hotkey_capture_scan": "Waiting for key: scan code mode capture… (press key directly)",
            "hotkey_capture_name": "Waiting for key: key name mode capture… (press key in window)",
            "hotkey_capture_forbidden": "⚠️ Test in progress, cannot modify hotkey (stop/reset first).",
            "hotkey_updated": "✅ Hotkey updated (mode will auto-adapt)",
            "test_stopped": "Stopped and reset (virtual gamepad will not disconnect/restart).",
            "test_started": "✅ Test started: entering [Deadzone Detection].\nCurrent magnitude: m={magnitude:.4f}\nNo movement: press [Deadzone Key] to increase.\nMoving too fast: press [Retreat Key] to retreat (can go to 0).\nStarting slow movement: press [End Deadzone Key] to confirm and enter curve sampling.",
            "deadzone_increased": "[Deadzone Detection] still no movement: m → {magnitude:.4f}\nStart slow movement: press [End Deadzone Key].",
            "deadzone_adjust": "[Point 1 Fine-tune] increased deadzone value: m → {magnitude:.4f}\nAfter confirm, press [Record Key] to start timing.",
            "deadzone_decreased": "[Deadzone Detection] retreated: m → {magnitude:.4f}\nStart slow movement: press [End Deadzone Key].",
            "deadzone_adjust_back": "[Point 1 Fine-tune] retreated deadzone value: m → {magnitude:.4f}\nAfter confirm, press [Record Key] to start timing.",
            "deadzone_ended": "✅ Deadzone ended, entering [Curve Sampling].\n{first_point_text}\nMeasurement points: {point_count}\nNext magnitude: m={next_mag:.4f}\nPress [Record Key] once to start timing, press again after full circle to save.\n(Before first point: can still fine-tune with [Deadzone/Retreat Key] once)",
            "record_start": "Timing started: m={magnitude:.4f} (repeat {repeat}/{total})\nPoint progress: {current}/{total_points}\nPress [Record Key] again after full circle to save.",
            "record_saved": "Recorded: m={magnitude:.4f} took {time:.4f}s\nNext: m={next_mag:.4f}\nPoint progress: {current}/{total_points}\nPress [Record Key] to start next round.",
            "retry_no_test": "⚠️ No test started yet, cannot retry.",
            "test_not_enabled": "Please click [Enable Emulation] first.",
            "ready_to_generate_charts": "✅ CSV saved. Ready to generate charts.",
            "param_error": "Fix as prompted: sample points 2~10; and 0<=MIN<MAX<=1.",
            "retry_reset_message": "Retry Test - Reset current point (m={magnitude:.4f})\\nRetries needed: {repeat_count}\\nPress [Record Key] to start retesting.",
            "first_point_text_no_deadzone": "No deadzone: 1st point fixed at (0,0).",
            "first_point_text_with_deadzone": "Deadzone≈{magnitude:.4f}: 1st point fixed at (deadzone,0).",
            "log_path_prefix": "Log:",
            "no_valid_records_msg": "No valid records."
        },

        "hints": {
            "log_init_failed_title": "Log initialization failed",
            "log_write_failed_title": "Log directory not writable",
            "log_write_failed_cause": "Likely system permissions / antivirus blocking / path not writable (environment issue)",
            "log_write_failed_action": "Suggest placing the program in a normal folder on non-system drive, running as admin, or disabling antivirus blocking.",
            "log_header_msg1": "This log is for general users: if you have problems, first check lines containing [CAUSE]/[ACTION].",
            "log_header_msg2": "Key keywords: HOTKEY / enable_emulation / start_test / record / finish_and_save.",
            "log_write_test_failed": "[WRITE_TEST] FAILED (directory not writable / blocked)",
            "hotkey_during_test_title": "Cannot rebind hotkey during test",
            "hotkey_during_test_cause": "Changing hotkey during test causes trigger anomalies / loss (user operation issue)",
            "hotkey_during_test_action": "Stop/reset first, then set hotkey.",
            "hotkey_bind_fail_title": "Attempted to change hotkey during test",
            "hotkey_capture_fail_title": "Scan code capture failed",
            "hotkey_capture_fail_cause": "Possibly special key / system blocking / permission issue (environment issue)",
            "hotkey_capture_fail_action": "Try binding other keys, or run as admin.",
            "enable_gamepad_fail_title": "Failed to enable virtual gamepad",
            "enable_gamepad_fail_dialog": "Enable failed",
            "enable_gamepad_fail_cause": "Possibly ViGEm driver / permissions / antivirus blocking / system environment issue (environment issue)",
            "enable_gamepad_fail_action": "Suggest: verify ViGEmBus installation; run as admin; disable blocking; restart and try again.",
            "no_emulation_start_title": "Starting test without enabling gamepad emulation",
            "no_emulation_start_dialog_title": "Emulation not enabled",
            "no_emulation_start_dialog_msg": "Please click [Enable Emulation] first.",
            "no_emulation_start_cause": "Incorrect user operation sequence (user operation issue)",
            "no_emulation_start_action": "Enable emulation first, then start test.",
            "param_error_title": "Parameter error preventing test start",
            "param_error_dialog": "Parameter error",
            "param_error_cause": "Invalid input parameters (user operation issue)",
            "param_error_action": "Fix as prompted: sample points 2~10; and 0<=MIN<MAX<=1.",
            "hold_key_fail_title": "Failed to apply button hold",
            "hold_key_fail_cause": "Virtual gamepad status anomaly or driver issue (environment issue)",
            "hold_key_fail_action": "Try re-enabling/disabling emulation, or check driver.",
            "no_valid_records_title": "No valid records",
            "no_valid_records_cause": "No data recorded during test (user operation issue)",
            "no_valid_records_action": "Start test again and press [Record Key] to save data.",
            "no_valid_records_dialog": "Failed",
            "no_timing_records_title": "No timing records",
            "no_timing_records_cause": "No valid timing information in records (user operation or software issue)",
            "no_timing_records_action": "Check record data or perform test again.",
            "no_analysis_title": "No analysis results",
            "no_analysis_cause": "Data analysis failed (possibly parameter issue or software bug)",
            "no_analysis_action": "Check if test data is complete, or check logs for more info.",
            "export_success_title": "Complete",
            "export_success_msg": "Export complete (files in program directory).",
            "export_fail_title": "Export failed",
            "export_fail_cause": "Exception occurred during export (possibly permission or environment issue)",
            "export_fail_action": "Check program directory permissions, or check logs for more info.",
            "exit_confirm_title": "Confirm exit",
            "exit_confirm_msg": "Test in progress, are you sure you want to exit? (will abort current test)",
            "keepalive_tap_fail_title": "Keepalive tap failed",
            "keepalive_tap_fail_cause": "Virtual gamepad may be unavailable/driver error (likely environment issue)",
            "keepalive_tap_fail_action": "Try stopping the test and restarting the virtual gamepad; or restart your computer.",
            "hold_key_apply_fail_title": "Hold key application failed",
            "hold_key_apply_fail_cause": "Virtual gamepad/driver state is abnormal or interface not supported (likely environment issue)",
            "hold_key_apply_fail_action": "First disable hold key feature; then enable after confirming virtual gamepad is available.",
            "timing_result_empty_title": "Timing result is empty",
            "timing_result_empty_cause": "Record process may not be completed (user operation issue)",
            "timing_result_empty_action": "Ensure each record: press start once, then press end once.",
            "timing_result_empty_dialog": "No valid timing records (seconds is empty)",
            "output_phase_error_title": "Output phase error",
            "output_phase_error_cause": "Likely a code/environment error (need to check traceback); hard for user to resolve via operation",
            "output_phase_error_action": "Send the log to the author (especially the traceback section).",
            "output_phase_error_dialog": "An error occurred during the output phase.",
            "stats_result_empty_title": "Statistics result is empty",
            "stats_result_empty_cause": "Insufficient data or abnormal record process (more likely user operation/interruption)",
            "stats_result_empty_action": "Re-test, ensure each point has more than 0 records.",
            "stats_result_empty_dialog": "Statistics result is empty",
            "export_complete_status": "✅ Complete: Output finished\\n  - Curve.png / Curve with coords.png\\n  - Inverse curve.png / Inverse curve with coords.png\\n  - results.csv / curve_summary.csv / compensation_table.csv\\n  - Log: {log_path}\\n\\nNote: Inverse curve point count matches forward curve point count exactly, mapped one-to-one via \\'percentage swap\\'.",
            "language_switched_status": "✅ Language switched to: {lang_code} (charts will use new language)"
        },

        "errors": {
            "sample_count_invalid_type": "Sample count must be an integer (2~100).",
            "sample_count_out_of_range": "Sample count range: 2~100.",
            "magnitude_range_invalid": "Magnitude range must satisfy: 0 <= MIN < MAX <= 1.",
            "csv_format_not_supported": "CSV format not supported (need results.csv or curve_summary.csv structure)."
        }
    }

    # 写入中文模板文件（强制覆盖，确保始终完整）
    zh_cn_path = os.path.join(lang_dir, "zh_CN.json")
    try:
        with open(zh_cn_path, 'w', encoding='utf-8') as f:
            json.dump(zh_cn_template, f, ensure_ascii=False, indent=2)
        print(f"生成/更新中文语言文件: {zh_cn_path}")  # 调试输出
    except Exception as e:
        print(f"生成中文文件失败: {e}")

    # 写入英文模板文件（强制覆盖，确保始终完整）
    en_us_path = os.path.join(lang_dir, "en_US.json")
    try:
        with open(en_us_path, 'w', encoding='utf-8') as f:
            json.dump(en_us_template, f, ensure_ascii=False, indent=2)
        print(f"生成/更新英文语言文件: {en_us_path}")  # 调试输出
    except Exception as e:
        print(f"生成英文文件失败: {e}")

    # 写入洪荒古言模板文件（彩蛋语言，内置字典防止缺失模块导致不生成）
    try:
        hong_huang_template = {
            "_language_name": "洪荒古言",
            "_language_code": "hong_huang_gu_yan",
            "_translator_note": "此文乃天地初开，鸿蒙未判之时，所撰奇书。若欲洞悉其中奥秘，须得心怀鸿蒙之力，得以破解其中玄机。此为奇书多语之模板，用户可自取更名，如将其命名为 en_US.json，便可随心所欲翻译为他言。软件启示时，必会感应此目录内之秘文，用户可选取所需语言之卷轴。",
            "app": {
                "name": "游戏之摇杆秘境探测器",
                "author": "刘云耀，掌控虚拟与现实的至高存在 🌑",
                "version": "v1.7beta，未曾显现之伟业 ✨"
            },
            "ui": {
                "settings_panel": "设定之秘境 🔮",
                "language_select": "界面之语言符号 ⚡",
                "language_label": "汝欲选何言：",
                "gamepad": "虚拟掌控之神器 ☯️",
                "gamepad_type": "模拟之类型：",
                "enable_emulation": "启用模拟掌控之术 🌀",
                "neutral": "归位之力（无须重启之神通） 🧘‍♂️",
                "status": "状态：",
                "status_disabled": "未启之符咒 ✨",
                "test_params": "试验之法则 ⚔️",
                "sample_count": "采样之点数（2~100，非首固定点之测量点）：",
                "repeats_per_mag": "每一采样点之重试次数 ♻️：",
                "magnitude_range": "幅度之极限（自'非死区'起始至极限） 🔥：",
                "min": "微极",
                "max": "极盛",
                "test_direction": "试炼方向（固守右摇杆之轨迹） 🔮",
                "axis_config": "曲线坐标之配置（如 0~100 / 0~350） 🪐",
                "x_axis_max": "X轴极限：",
                "y_axis_max": "Y轴极限：",
                "deadzone_params": "死区之探测之秘术 ☯️",
                "deadzone_step": "探测步伐（若静止不动时所用） ⏳：",
                "deadzone_back_step": "回退步伐（若动作过急时，可使其归零） 🔄：",
                "keepalive": "维持操控输入（防止游戏切换至键鼠之境） 🌙",
                "keepalive_enable": "启用（死区探测与计时等待期间，周期性按下掌控器之键） ⚡",
                "keepalive_interval": "间隔（毫秒）：",
                "keepalive_button": "按键：",
                "hold": "试炼期间，长按按键（默认关闭） ✋",
                "hold_enable": "启用（持续按住指定之键或触发器，直至试炼完成） 🌀",
                "hold_key": "长按之键：",
                "hotkey": "快捷键之秘术（点击按钮后，依指示按键） 🔑",
                "hotkey_mode": "快捷键模式：",
                "set_start_key": "设定启始之符钥 🀄",
                "set_record_key": "设定记录之符钥 🔑",
                "set_deadzone_key": "设定死区探测之符钥 🌓",
                "set_deadzone_back_key": "设定回退死区之符钥 🔮",
                "set_end_deadzone_key": "设定终结死区之符钥 🔴",
                "set_retry_key": "设定重试之符钥 🔄",
                "control": "掌控 ⚡",
                "start_test": "开启试炼 🔥",
                "stop_reset": "止息/重启 ⏸️",
                "export_and_charts": "导出与图谱之匣 🌌",
                "generate_charts": "炼制曲线图（当前试炼） 🔥",
                "generate_from_csv": "由CSV再炼曲线图 📜",
                "generate_charts_prompt_title": "图谱待炼成 ⚡",
                "generate_charts_prompt_body": "CSV 已封存。点击【炼制曲线图】立刻绘制；或稍后以【由CSV再炼】取之。 🔮",
                "select_csv_title": "择取CSV以炼图 📜",
                "all_files": "万物之卷 🌠",
                "author_footer": "作者铭文：哔哩哔哩：{author}   |   版本：{version} ✨",
                "left_stick": "左摇杆（鼠标拖动之秘术） 🌀",
                "right_stick": "右摇杆（鼠标拖动之秘术） 🔮",
                "info_title": "状态 / 操作流程 ⚡",
                "direction_right": "右 ↘️",
                "direction_left": "左 ↖️",
                "direction_up": "上 ⬆️",
                "direction_down": "下 ⬇️",
                "info_description": "用途：测量\"游戏操控器所塑之输入优化曲线\"（非硬件死区之限界）。\n\n操作流程：\n  1) 点击【启用模拟掌控器】后，回归游戏之境。\n  2) 在【鼠标拖动虚拟摇杆】上完成试炼（需多次彻底推动圆周）。\n  3) 点击【开始试炼】，系统将自动采样、计时并呈现结果。\n  4) 【保存CSV】以导出，得以使用 Excel 查阅或进一步处理。\n\n快捷键：F6=开始、F7=记录点、F8=死区探测、F9=回退、F10=结束死区、F11=重试。\n\n常见问题：若摇杆之坐标有\"抖动\"或\"不顺滑\"，请检查游戏是否存在硬件死区或增益。 🌓",
                "button_square": "方块/ X 🀄",
                "button_cross": "叉/ A 🌑",
                "button_circle": "圆/ B 🔵",
                "button_triangle": "三角/ Y 🔺",
                "button_l1": "L1/ LB ⚡",
                "button_r1": "R1/ RB 🔋",
                "button_share": "分享/ 返回 🌙",
                "button_options": "选项/ 启动 🧭",
                "trigger_l2": "左触发器（L2/ LT） 🔥",
                "trigger_r2": "右触发器（R2/ RT） 🌟",
                "hotkey_hint_symbol": "已侦测至【数字/符号键】（单字符）。\\n✅ 已自动启用：keyboard_scan（更适合全屏游戏及数字符号键）。\\n若将此类数字/符号键变更为 F 键/字母/方向键等，则系统将自动切换回 keyboard_name。",
                "hotkey_hint_normal": "当前快捷键并不含数字/符号键。\\n✅ 自动使用：keyboard_name（直观且稳定，建议使用 F 键/字母键）。\\n若改绑为数字/符号键，系统将自动切换至 keyboard_scan。",
                "hotkey_hint_failed": "⚠️ 键名模式注册失败，已自动切换为 keyboard_scan。\\n原因：全屏游戏/权限不足/杀软拦截/某些键名无法被识别。\\n建议：优先绑定 F 键或字母键；若有必要，可以管理员身份运行或关闭拦截。",
                "hotkey_keys_label": "开始键：{start_key}    记录键：{record_key}    重试键：{retry_key}\\n死区探测键：{deadzone_key}    回退死区键：{deadzone_back_key}\\n结束死区键：{end_deadzone_key}\\n当前快捷键模式：{mode}（按绑定键自动适配）"
            },
            "status": {
                "emulation_enabled": "状态：已启用（{type}） 🌑",
                "emulation_already_enabled": "模拟掌控器已启用：设备不再重启。",
                "emulation_enabled_success": "✅ 已启用模拟掌控器。请回归游戏后开始试炼。",
                "emulation_not_enabled": "模拟掌控器尚未启用。",
                "neutral_success": "已归位（虚拟掌控器未被断开或重启）。 🔮"
            },
            "charts": {
                "curve_title": "游戏之实际灵敏度（显示坐标） 🌟",
                "curve_xlabel": "摇杆偏移（显示坐标） 🌀",
                "curve_ylabel": "游戏之实际灵敏度（显示坐标） ✨",
                "inverse_title": "逆曲线（百分比交换：与正向点一一对应） ⚡",
                "inverse_xlabel": "逆曲线 X（显示坐标） 🔥",
                "inverse_ylabel": "逆曲线 Y（显示坐标） 🔮"
            },
            "messages": {
                "initial_hint": "提示：请先点击【启用模拟掌控器】。",
                "emulation_already_on": "模拟掌控器已启用：设备不再重启。",
                "emulation_enabled": "✅ 已启用模拟掌控器。请回归游戏后开始试炼。",
                "emulation_not_enabled": "模拟掌控器尚未启用。",
                "neutral_done": "已归位（虚拟掌控器未被断开或重启）。",
                "hotkey_mode_changed": "✅ 快捷键模式：{mode}（按绑定键自动适配）",
                "hotkey_mode_forbidden": "⚠️ 测试进行中，禁止切换快捷键模式（请先停止或重置）。",
                "hotkey_registration_failed": "⚠️ 键名模式注册失败，已自动切换为 keyboard_scan（详见日志）。",
                "hotkey_capture_waiting": "请按下欲绑定之键……（不打断）",
                "hotkey_capture_scan": "等待按键：扫描模式捕捉中……（按键即可）",
                "hotkey_capture_name": "等待按键：键名模式捕捉中……（窗口内按键即可）",
                "hotkey_capture_forbidden": "⚠️ 测试进行中，禁止修改快捷键（请先停止或重置）。",
                "hotkey_updated": "✅ 快捷键已更新（模式自动适配）",
                "test_stopped": "已停止并重置（虚拟掌控器未被断开或重启）。",
                "test_started": "✅ 已开始试炼：进入【死区探测】。\\n当前幅值：m={magnitude:.4f}\\n若未动：按【死区探测键】继续增加。\\n若动得过急：按【回退死区键】回退（可回归零）。\\n开始缓慢移动：按【结束死区键】确认死区并进入曲线采样。",
                "deadzone_increased": "【死区探测】仍未动：m → {magnitude:.4f}\\n缓慢移动：按【结束死区键】。",
                "deadzone_adjust": "【第一点微调】已增加死区候选值：m → {magnitude:.4f}\\n确认后按【记录键】开始计时。",
                "deadzone_decreased": "【死区探测】已回退：m → {magnitude:.4f}\\n缓慢移动：按【结束死区键】。",
                "deadzone_adjust_back": "【第一点微调】已回退死区候选值：m → {magnitude:.4f}\\n确认后按【记录键】开始计时。",
                "deadzone_ended": "✅ 已结束死区，进入【曲线采样】。\\n{first_point_text}\\n测量点数：{point_count}\\n下一次测量幅值：m={next_mag:.4f}\\n按【记录键】开始计时，一圈后按一次结束并保存。\\n（仅限第一点开始前：仍可微调【死区探测/回退死区】）",
                "record_start": "计时开始：m={magnitude:.4f}（第 {repeat}/{total} 次）\\n点进度：{current}/{total_points}\\n转满一圈后再按【记录键】结束并保存。",
                "record_saved": "已记录：m={magnitude:.4f} 用时 {time:.4f}s\\n下一步：m={next_mag:.4f}\\n点进度：{current}/{total_points}\\n按【记录键】开始下一圈。",
                "retry_no_test": "⚠️ 还未开始任何试炼，无法重试。",
                "test_not_enabled": "请先点击【启用模拟掌控器】。",
                "ready_to_generate_charts": "✅ CSV 已封存，可炼曲线图。 🌟",
                "param_error": "按提示修正：采样点 2~10；且 0<=MIN<MAX<=1。",
                "retry_reset_message": "【重新测试】已重置当前点（m={magnitude:.4f}）\\n需重试次数：{repeat_count}\\n按【记录键】开始重新测试。",
                "first_point_text_no_deadzone": "无死区：第一个点固定为 (0,0)。",
                "first_point_text_with_deadzone": "死区≈{magnitude:.4f}：第一个点固定为 (死区,0)。",
                "log_path_prefix": "日志：",
                "no_valid_records_msg": "没有有效记录。"
            },
            "hints": {
                "log_init_failed_title": "日志初始化失败",
                "log_write_failed_title": "日志目录无法写入",
                "log_write_failed_cause": "多半由系统权限/杀软拦截/路径不可写所致（用户环境问题）",
                "log_write_failed_action": "建议将程序放至非系统盘的普通文件夹，或以管理员身份运行；或关闭拦截后再试。",
                "log_header_msg1": "此日志为普通用户所见：遇问题时，可先查阅包含[CAUSE]/[ACTION]的行。",
                "log_header_msg2": "关键字：HOTKEY / enable_emulation / start_test / record / finish_and_save。",
                "log_write_test_failed": "[WRITE_TEST] 失败（目录不可写/被拦截）",
                "hotkey_during_test_title": "测试期间无法重设快捷键",
                "hotkey_during_test_cause": "测试时更改快捷键会导致触发异常/丢失（用户操作问题）",
                "hotkey_during_test_action": "请先停止/重试，再设置快捷键。",
                "hotkey_bind_fail_title": "测试中试图更改快捷键",
                "hotkey_capture_fail_title": "扫描码捕获失败",
                "hotkey_capture_fail_cause": "可能是特殊键/系统拦截/权限问题（环境问题）",
                "hotkey_capture_fail_action": "尝试绑定其他键，或以管理员身份运行。",
                "enable_gamepad_fail_title": "启用虚拟掌控器失败",
                "enable_gamepad_fail_dialog": "开启失败",
                "enable_gamepad_fail_cause": "可能是 ViGEm 驱动/权限/杀软拦截/系统环境问题（环境问题）",
                "enable_gamepad_fail_action": "确认安装 ViGEmBus；以管理员身份运行；关闭拦截；重启后再试。",
                "no_emulation_start_title": "未启用模拟掌控器即开始测试",
                "no_emulation_start_dialog_title": "未启用模拟",
                "no_emulation_start_dialog_msg": "请先点击【启用模拟掌控器】。",
                "no_emulation_start_cause": "操作顺序错误（用户操作问题）",
                "no_emulation_start_action": "先启用模拟掌控器，再开始测试。",
                "param_error_title": "参数错误导致无法开始测试",
                "param_error_dialog": "参数错误",
                "param_error_cause": "输入的参数不合法（用户操作问题）",
                "param_error_action": "按提示修正：采样点 2~10；且 0<=MIN<MAX<=1。",
                "hold_key_fail_title": "长按按键应用失败",
                "hold_key_fail_cause": "虚拟掌控器状态异常或驱动问题（环境问题）",
                "hold_key_fail_action": "尝试重新启用/停止模拟掌控器，或检查驱动。",
                "no_valid_records_title": "没有有效记录",
                "no_valid_records_cause": "测试过程中没有记录任何数据（用户操作问题）",
                "no_valid_records_action": "重新开始测试，按【记录键】保存数据。",
                "no_valid_records_dialog": "失败",
                "no_timing_records_title": "计时结果为空",
                "no_timing_records_cause": "记录数据中没有有效的计时信息（用户操作或软件问题）",
                "no_timing_records_action": "检查记录数据，或重新进行测试。",
                "no_analysis_title": "统计结果为空",
                "no_analysis_cause": "数据分析失败（可能是参数问题或软件bug）",
                "no_analysis_action": "检查测试数据是否完整，或查看日志获取更多信息。",
                "export_success_title": "完成",
                "export_success_msg": "输出完成（文件在程序目录）。",
                "export_fail_title": "输出失败",
                "export_fail_cause": "输出过程中发生异常（可能是权限或环境问题）",
                "export_fail_action": "检查程序目录权限，或查看日志获取更多信息。",
                "exit_confirm_title": "确认退出",
                "exit_confirm_msg": "测试进行中，确定要退出吗？（将中止本次测试）",
                "keepalive_tap_fail_title": "keepalive 点按失败",
                "keepalive_tap_fail_cause": "可能是虚拟掌控器当前不可用/驱动异常（偏环境问题）",
                "keepalive_tap_fail_action": "尝试停止测试并重新启用模拟掌控器；或重启电脑后再试。",
                "hold_key_apply_fail_title": "长按按键应用失败",
                "hold_key_apply_fail_cause": "虚拟掌控器/驱动状态异常或接口不支持（偏环境问题）",
                "hold_key_apply_fail_action": "先关闭长按功能；确认模拟掌控器可用后再启用。",
                "timing_result_empty_title": "计时结果为空",
                "timing_result_empty_cause": "可能是记录流程没有完成（用户操作问题）",
                "timing_result_empty_action": "确保每次记录：先按一次开始，再按一次结束。",
                "timing_result_empty_dialog": "没有有效计时记录（seconds为空）",
                "output_phase_error_title": "输出阶段异常",
                "output_phase_error_cause": "更像代码/环境异常（需要看 traceback），用户很难仅靠操作解决",
                "output_phase_error_action": "把日志发给作者（尤其是包含 Traceback 的那段）。",
                "output_phase_error_dialog": "输出阶段发生异常。",
                "stats_result_empty_title": "统计结果为空",
                "stats_result_empty_cause": "数据不足或记录过程异常（更偏用户操作/中断）",
                "stats_result_empty_action": "重新测试，确保每个点记录次数>0。",
                "stats_result_empty_dialog": "统计结果为空",
                "export_complete_status": "✅ 完成：已输出\n  - 曲线图.png / 带坐标曲线图.png\n  - 反曲线图.png / 带坐标反曲线图.png\n  - results.csv / curve_summary.csv / compensation_table.csv\n  - 日志：{log_path}\n\n说明：反曲线点数与正向曲线点数完全一致，并按\"百分比交换\"与每个正向点一一对应。",
                "language_switched_status": "✅ 语言已切换到：{lang_code}（图表将使用新语言）"
            },
            "errors": {
                "sample_count_invalid_type": "采样点数量必须为整数（2~100）。",
                "sample_count_out_of_range": "采样点数量范围：2~100。",
                "magnitude_range_invalid": "幅值范围须满足：0 <= MIN < MAX <= 1。",
                "csv_format_not_supported": "CSV 格式不合（需 results.csv 或 curve_summary.csv 之形）。 ⚠️"
            }
        }

        hong_huang_path = os.path.join(lang_dir, "洪荒古言.json")
        with open(hong_huang_path, 'w', encoding='utf-8') as f:
            json.dump(hong_huang_template, f, ensure_ascii=False, indent=2)
        print(f"生成/更新洪荒古言语言文件: {hong_huang_path}")  # 调试输出
    except Exception as e:
        print(f"生成洪荒古言文件失败: {e}")


def _start_app() -> None:
    # 初始化 i18n 系统，使用用户可访问的语言目录
    from i18n import init_i18n
    lang_dir = _get_user_languages_dir()
    # is_lang_dir=True 表示直接使用 lang_dir 作为语言文件目录，而不是 lang_dir/languages/
    init_i18n(base_dir=lang_dir, default_lang="zh_CN", is_lang_dir=True)
    
    # 尝试找 main/run 入口，都没有就当脚本跑
    try:
        import ui_app  # type: ignore

        if hasattr(ui_app, "main") and callable(ui_app.main):
            ui_app.main()
            return
        if hasattr(ui_app, "run") and callable(ui_app.run):
            ui_app.run()
            return

        # 都没找到，脚本方式跑
        runpy.run_module("ui_app", run_name="__main__")
    except Exception:
        # 实在不行再跑一遍
        runpy.run_module("ui_app", run_name="__main__")


def main() -> None:
    # 先装前置（缺就退出提示装）
    ensure_prereqs_or_exit()
    
    # 首次启动时生成语言文件
    _ensure_default_language_files()
    
    # 启动 UI
    _start_app()


if __name__ == "__main__":
    main()