# 🎮 Gamepad Curve Calibration Tool | 游戏摇杆曲线探测器

> **Professional Gamepad Calibration & Curve Detection Toolkit**
> **专业级游戏手柄曲线标定与检测工具**

![Version](https://img.shields.io/badge/version-1.8.6-blue)
![Platform](https://img.shields.io/badge/platform-Windows%207+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Languages](https://img.shields.io/badge/languages-EN%20%7C%20ZH%20%7C%20JA-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7+-blue)

**[中文版本](#-中文版本中文详细介绍) | [English](#-english-version) | [日本語](#-日本語版)**

---

## 🌍 中文版本：中文详细介绍

### 📖 什么是"游戏摇杆曲线探测器"？

这是一款**游戏手柄响应曲线优化测试工具**，专为游戏开发者和游戏运营方设计。它的核心用途是：

1. **游戏级曲线优化**：在游戏软件层面测试和优化手柄的响应曲线参数
2. **模拟测试**：无需物理硬件，完全在软件层面模拟各种手柄输入行为
3. **曲线参数调试**：精确调整游戏中手柄的加速度、死区、响应灵敏度等参数
4. **输入体验优化**：通过科学的采样和分析，找到最佳的游戏手柄操作曲线
5. **跨平台适配**：测试游戏在不同手柄类型（Xbox、PS、Nintendo等）上的表现

### 🎯 核心功能特性

| 功能模块 | 详细说明 |
|---------|--------|
| **软件级曲线测试** | 在游戏引擎层面测试手柄响应曲线，无需真实物理设备 |
| **采样点分析** | 支持1-100个采样点进行密集的响应特性采样和分析 |
| **实时曲线可视化** | 测试过程中实时显示手柄输入-输出映射曲线 |
| **多曲线类型支持** | 检测并拟合线性、指数、三次多项式等游戏优化曲线 |
| **死区和加速度调试** | 精确调整死区范围、加速度系数等游戏参数 |
| **响应延迟测量** | 测量游戏对手柄输入的响应延迟和稳定性 |
| **完整国际化系统** | 内置英文、简体中文、日文；支持用户自定义翻译 |
| **数据导出系统** | 导出优化后的曲线参数供游戏集成使用 |

### 🚀 为什么游戏开发者需要这个工具？

#### 游戏开发中的挑战
- ❌ **不同手柄差异大**：Xbox、PS、Switch手柄的硬件差异会影响游戏体验
- ❌ **玩家期望不同**：竞技游戏玩家期望快速响应，休闲玩家期望平缓曲线
- ❌ **参数调优困难**：手动调整死区、灵敏度、加速度参数费时费力
- ❌ **缺乏量化指标**：无法科学地评估曲线优化的效果
- ❌ **跨平台兼容**：需要为多个平台针对性优化

#### 本工具的解决方案
✅ **科学的软件测试**：在游戏软件层面进行严格的曲线分析和优化
✅ **标准化采样**：统一的测试方法确保所有手柄在同一标准下比较
✅ **可视化优化**：通过曲线图表清晰看到参数调整的效果
✅ **数据驱动**：基于采样数据和分析结果进行决策
✅ **快速迭代**：支持快速修改参数并重新测试

### 📦 安装与快速开始

#### 方式一：下载预编译版本（推荐 ⭐）
1. 访问 **[Releases 页面](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)**
2. 下载最新版本：`游戏摇杆曲线探测器_v1.8.6.exe`（约81MB）
3. 双击运行安装程序
   - 自动安装必要的依赖库
   - 约2-3分钟完成安装
4. 完成后在桌面或开始菜单找到应用，点击启动

#### 方式二：从源代码运行（开发者用）
```bash
git clone https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool.git
cd Gamepad-Curve-Calibration-Tool
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python ui_app.py
```

### 📖 游戏曲线优化工作流程

#### **第一步：配置测试参数**
- 选择要测试的手柄类型（Xbox / PS / Switch 等）
- 设置采样点数（20-100 点）
- 配置初始曲线参数

#### **第二步：运行模拟测试**
- 点击**"开始测试"**，系统开始模拟手柄输入
- 软件在游戏引擎层面进行完整的曲线采样
- 实时显示输入-输出映射关系

#### **第三步：分析结果**
- 查看生成的响应曲线图表
- 分析死区、加速度、灵敏度等参数
- 评估玩家操作体验

#### **第四步：参数优化迭代**
- 根据分析结果调整游戏参数
- 修改死区范围、加速系数等
- 重新运行测试验证改进效果

#### **第五步：数据导出**
- 导出优化后的曲线参数（JSON/CSV 格式）
- 用于游戏集成和发布
- 支持多平台导出不同参数

### 🌐 多语言本地化指南

本工具支持**完全的用户自定义多语言翻译**，无需编程知识！

#### 添加新语言的步骤

**步骤1：准备翻译文件**
```
languages/
├── en_US.json       (英文模板)
├── zh_CN.json       (中文)
└── your_lang.json   (你的新语言)
```

**步骤2：翻译JSON文件**
- 打开 `languages/en_US.json` 作为参考模板
- 创建新文件 `languages/语言代码.json`（例如 `de_DE.json` 德文、`fr_FR.json` 法文）
- 使用AI翻译工具（ChatGPT、Google翻译、DeepL等）翻译所有值
- 保持JSON结构完全相同，只翻译`"value"`部分

**示例：**
```json
{
  "app_title": "Gamepad Calibrator",
  "start_test": "Start Test",
  "select_device": "Select Device",
  "sampling_points": "Sampling Points",
  ...
}
```

**步骤3：应用翻译**
- 将翻译好的JSON文件保存到 `languages/` 文件夹
- 重启应用程序
- 在应用菜单 "Language" (语言) 中会出现你添加的语言
- 点击选择即可立即切换UI

### 📊 支持的游戏手柄类型

✅ **Xbox系列**：Xbox Controller、Xbox One Controller、Xbox Series X/S Controller
✅ **PlayStation系列**：DualShock 4、DualSense（PS5 手柄）
✅ **任天堂系列**：Pro Controller、Joy-Con
✅ **通用HID设备**：任何标准 HID 输入设备的软件模拟

### 🛠️ 系统要求 & 兼容性

| 项目 | 要求 |
|-----|-----|
| **操作系统** | Windows 7、8、8.1、10、11（32位或64位） |
| **运行时环境** | .NET Framework 4.7+（通常已预装）或 Python 3.7+ |
| **内存** | 最低100MB可用内存；推荐2GB+ |
| **磁盘** | 约200MB安装空间 |

### 🔧 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| **应用无法启动** | 缺少依赖库或Python环境 | 重新运行安装程序或更新Python版本 |
| **曲线数据异常** | 参数设置不当 | 检查初始参数配置，使用默认参数重试 |
| **导出失败** | 磁盘空间不足或权限问题 | 检查磁盘剩余空间>500MB，以管理员身份运行 |
| **UI显示异常** | 字体或显示缩放问题 | 尝试重启应用，切换语言，调整显示缩放 |

### 🎮 推荐使用场景

#### 🎮 游戏开发者
- 优化游戏中手柄的响应曲线参数
- 为多个平台调整适配参数
- 进行A/B测试不同曲线方案
- 验证游戏手柄输入系统的性能

#### 🎯 游戏运营方
- 针对不同玩家群体优化手柄感受
- 基于数据驱动进行游戏参数调优
- 跨平台统一玩家操作体验

#### 📊 QA/测试团队
- 系统化地测试游戏的手柄输入处理
- 生成测试报告和数据分析
- 验证不同曲线参数的实际效果

---

## 🌍 English Version
A comprehensive gamepad analog stick calibration and curve detection tool. This application allows users to precisely calibrate gamepad joysticks, detect their curve characteristics, and export calibration data for use in games and applications.

### Key Features
- **Precision Calibration**: Accurate analog stick calibration with up to 100 sampling points
- **Curve Detection**: Automatically detects joystick response curves (linear, exponential, cubic, etc.)
- **Real-time Visualization**: Live curve graph display during testing
- **Multi-language Support**: Full internationalization—users can translate language files (JSON) using AI tools
- **ViGEm Integration**: Virtual controller output support via ViGEmBus
- **Hotkey Support**: Quick access with customizable hotkeys
- **Cross-platform**: Works with various gamepad types and protocols

### Installation & Setup
1. Download the latest `.exe` from [Releases](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)
2. Run the installer (it will install required dependencies)
3. Launch the application and start calibrating

### Quick Start Guide
1. **Connect Gamepad**: Plug in your gamepad/controller
2. **Select Input Method**: Choose your gamepad/joystick from the device list
3. **Run Calibration**: 
   - Set sampling points (up to 100 for fine control)
   - Click "Start Test" and follow on-screen instructions
   - Move the analog stick in a circular motion
4. **Review Curve**: View the detected curve graph
5. **Export Data**: Save calibration data for your game/application
6. **Re-test**: Use "Re-test Previous Point" to validate specific points without restarting

### Localization
You can easily localize the UI in your language:
1. Open `languages/en_US.json` as a template
2. Duplicate it as `languages/your_language_code.json`
3. Translate all text values using AI translation tools (ChatGPT, DeepL, etc.)
4. Save and restart the application
5. Select your language from the UI language menu

### Supported Languages
- English (en_US)
- Simplified Chinese (zh_CN)
- (Add your own via JSON translation!)

### System Requirements
- Windows 7 or later
- .NET Framework 4.7+
- ViGEmBus (installed automatically)
- USB/Wireless gamepad with standard HID support

### Troubleshooting
- **Gamepad not detected**: Ensure device is connected and drivers are installed
- **ViGEm errors**: Reinstall ViGEmBus from `prereqs/ViGEmBus_Setup_x64.exe`
- **Visual glitches**: Try restarting the application

### Contributing
Contributions welcome! Please submit pull requests or open issues for bugs/feature requests.

### License
[Add your license here]

---

## 中文

### 项目介绍
一款专业级游戏摇杆曲线探测和标定工具。用户可以精确标定游戏手柄模拟摇杆、检测摇杆曲线特性，并导出标定数据用于游戏和应用。

### 核心功能
- **精确标定**：支持最多 100 个采样点的高精度模拟摇杆标定
- **曲线探测**：自动识别摇杆响应曲线（线性、指数、立方等）
- **实时可视化**：测试过程中实时显示曲线图形
- **完整国际化支持**：用户可自行翻译语言文件（JSON 格式），支持 AI 翻译工具
- **ViGEm 虚拟控制器**：支持通过 ViGEmBus 虚拟控制器输出
- **快捷键支持**：可自定义快捷键快速启动
- **多设备兼容**：支持各类游戏手柄和外设协议

### 安装与设置
1. 从 [Releases](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases) 下载最新 `.exe`
2. 运行安装程序（自动安装依赖）
3. 启动应用开始标定

### 快速开始
1. **连接手柄**：插入游戏手柄
2. **选择设备**：从设备列表选择你的摇杆
3. **开始标定**：
   - 设置采样点数（最多 100 个实现精细控制）
   - 点击"开始测试"按照屏幕提示操作
   - 按圆形轨迹转动摇杆
4. **查看曲线**：观察检测到的曲线图形
5. **导出数据**：保存标定数据供游戏/应用使用
6. **复测点位**：使用"重新测试上一个采样点"快速验证特定点位，无需重启整轮

### 本地化翻译
轻松为应用翻译成你的语言：
1. 打开 `languages/en_US.json` 作为模板
2. 复制并改名为 `languages/你的语言代码.json`
3. 用 AI 翻译工具（ChatGPT、Google Translate 等）翻译所有文本值
4. 保存并重启应用
5. 从 UI 语言菜单选择你的语言

### 已支持语言
- English (en_US)
- 简体中文 (zh_CN)
- （通过 JSON 翻译添加更多语言！）

### 系统要求
- Windows 7 及更高版本
- .NET Framework 4.7+
- ViGEmBus（自动安装）
- USB/无线游戏手柄（标准 HID 驱动支持）

### 常见问题排查
- **手柄未检测**：确保设备已连接且驱动已安装
- **ViGEm 错误**：从 `prereqs/ViGEmBus_Setup_x64.exe` 重新安装
- **显示异常**：尝试重启应用

### 贡献指南
欢迎提交 Pull Request 或反馈 Issue。

### 许可证
[添加你的许可证信息]

---

## 日本語

### プロジェクト概要
ゲームパッドアナログスティックの曲線検出と較正を行う専門ツール。ユーザーはジョイスティックの応答特性を検出し、キャリブレーションデータをゲームに出力できます。

### 主な機能
- **高精度較正**：最大 100 サンプルポイントによる精密な較正
- **曲線検出**：ジョイスティックの応答特性を自動認識（線形、指数関数、立方など）
- **リアルタイム表示**：テスト中に曲線グラフをリアルタイムで表示
- **完全な多言語対応**：JSON ファイルをユーザーが翻訳可能（AI 翻訳対応）
- **ViGEm 統合**：ViGEmBus を通じた仮想コントローラー出力
- **ホットキーサポート**：カスタマイズ可能なホットキー対応
- **マルチプラットフォーム対応**：各種ゲームパッドプロトコルに対応

### インストール＆セットアップ
1. [Releases](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases) から最新 `.exe` をダウンロード
2. インストーラーを実行（依存関係は自動インストール）
3. アプリケーション起動で較正開始

### 快速スタートガイド
1. **ゲームパッド接続**：ゲームパッドを接続
2. **デバイス選択**：デバイスリストからジョイスティックを選択
3. **較正開始**：
   - サンプルポイント数を設定（最大 100 で精密制御可能）
   - 「テスト開始」をクリック
   - 円形に沿ってアナログスティックを動かす
4. **曲線確認**：検出された曲線グラフを表示
5. **データ出力**：ゲーム/アプリ用に較正データを保存
6. **再テスト**：「前のポイントを再テスト」で全体を再起動せずに特定ポイントを検証

### 多言語化
アプリケーションを自分の言語に翻訳：
1. `languages/en_US.json` をテンプレートとして開く
2. `languages/your_language_code.json` としてコピー
3. AI 翻訳ツール（ChatGPT など）で翻訳
4. 保存してアプリ再起動
5. UI の言語メニューから選択

### 対応言語
- English (en_US)
- 簡体字中国語 (zh_CN)
- （JSON 翻訳で追加可能！）

### システム要件
- Windows 7 以上
- .NET Framework 4.7+
- ViGEmBus（自動インストール）
- USB/無線ゲームパッド（標準 HID ドライバー対応）

### トラブルシューティング
- **ゲームパッド未検出**：デバイス接続とドライバー確認
- **ViGEm エラー**：`prereqs/ViGEmBus_Setup_x64.exe` から再インストール
- **表示異常**：アプリケーション再起動を試行

### 貢献
プルリクエストとイシュー報告を歓迎します。

### ライセンス
[ライセンス情報を追加]

---

### Version
v1.8.6

---

## About

### Project Vision
Gamepad Curve Calibration Tool (游戏摇杆曲线探测器) aims to provide gamers and developers with a professional-grade solution for:
- **Precise Hardware Calibration**: Eliminate stick drift and inconsistent input responses
- **Curve Analysis**: Understand and optimize joystick response characteristics for competitive gaming
- **Cross-platform Compatibility**: Support diverse gamepad types and protocols
- **Global Accessibility**: Full multi-language support enabling worldwide adoption

### Why This Project?
Modern gaming demands precision. Whether you're a casual gamer dealing with analog stick drift or a developer optimizing controller input curves, this tool provides scientific calibration and detailed insights.

### Technical Highlights
- **ViGEm Integration**: Virtual gamepad output via ViGEmBus for game compatibility
- **Advanced Curve Detection**: Supports linear, exponential, cubic, and custom curve patterns
- **JSON-based Localization**: Easy community translations without code modifications
- **Real-time Visualization**: Live graphical feedback during calibration
- **Comprehensive Logging**: Detailed calibration records for debugging and optimization

### Who Should Use This?
- **Gamers**: Calibrate controllers for competitive titles (FPS, Racing, Fighting games)
- **Developers**: Test gamepad input curves for game development
- **Hardware Enthusiasts**: Analyze and optimize controller performance
- **Accessibility Users**: Customize controls for specific needs

### Community & Contributions
We actively welcome:
- Bug reports and feature suggestions via [Issues](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/issues)
- Language translations (any language via JSON translation)
- Code contributions and improvements
- Documentation enhancements

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Roadmap
- [ ] Support for controller pressure sensitivity calibration
- [ ] Advanced analytics dashboard
- [ ] Profile management system
- [ ] Mobile app companion
- [ ] Integration with popular game engines (Unity, Unreal)

### Support
- 📖 **Documentation**: See [README](#english) sections above
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/issues)
- 💬 **Discussions**: GitHub Discussions (coming soon)
- 🌐 **Website**: [Coming soon]

### Credits
- Built with Python and PyQt
- ViGEmBus integration for virtual gamepad support
- Community translations and contributions

### Legal
Licensed under MIT. See [LICENSE](LICENSE) for details.

---

**Developed by TianyaoPRC** | Updated: January 2026
