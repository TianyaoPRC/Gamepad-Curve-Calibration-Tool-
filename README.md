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

这是一款**专业级游戏手柄诊断和标定工具**。它的核心功能是：

1. **诊断摇杆问题**：自动检测手柄摇杆是否存在漂移、死区不均或响应延迟
2. **精确标定**：通过科学采样（最高100个采样点，精度达毫秒级）为您的手柄进行个性化标定
3. **曲线分析**：自动识别摇杆的实际响应特性（线性/指数/多项式等）
4. **导出配置**：生成可用于游戏或其他应用的标定数据文件
5. **虚拟控制器**：通过ViGEm技术为不兼容的旧游戏提供虚拟手柄支持

### 🎯 核心功能特性

| 功能模块 | 详细说明 |
|---------|--------|
| **精密采样系统** | 支持1-100个采样点，单点精度达毫秒级，覆盖摇杆完整活动范围 |
| **实时曲线可视化** | 标定过程中实时显示摇杆响应曲线，采样点分布图，响应延迟分析 |
| **多曲线算法支持** | 自动检测并拟合线性、指数、三次多项式、四次多项式等曲线类型 |
| **虚拟控制器输出** | ViGEmBus集成，为DirectInput/XInput不兼容的旧游戏提供支持层 |
| **完整国际化系统** | 内置英文、简体中文、日文；用户可自定义翻译任何语言（无需代码修改） |
| **快捷键系统** | 可自定义热键快速启动标定流程、导出数据、切换语言 |
| **多设备驱动** | 支持USB和无线游戏手柄、街机摇杆、赛车方向盘等所有HID标准设备 |
| **单点复测功能** | 支持在标定后快速复测任意点位，验证某个特定轴向的准确性，无需重启 |
| **数据导出系统** | 支持JSON、CSV、二进制等多种格式导出，可直接用于游戏开发 |

### 🚀 为什么需要这个工具？

#### 现实问题场景
- ❌ **摇杆漂移**：闲置时摇杆自动向某个方向移动（使用1-2年后常见）
- ❌ **死区不均**：中心区域完全无反应，但响应范围不对称
- ❌ **响应不一致**：左右或上下移动速度明显不同，导致游戏中转向偏斜
- ❌ **旧游戏兼容**：Win 10/11 中某些DirectInput游戏无法识别新型手柄
- ❌ **竞技精度需求**：FPS/格斗游戏对摇杆精度要求极高
- ❌ **长期使用磨损**：随着使用，摇杆物理特性会逐渐衰减

#### 本工具的解决方案
✅ **科学采样与拟合**：通过数学模型精确还原摇杆真实响应特性
✅ **个性化标定**：为您的特定手柄生成专属配置文件
✅ **兼容性适配**：虚拟控制器支持让旧游戏也能使用新设备
✅ **可视化诊断**：清晰的曲线图表让您看到问题所在
✅ **数据记录**：保留标定历史，跟踪手柄性能变化

### 📦 安装与快速开始

#### 方式一：下载预编译版本（推荐 ⭐）
1. 访问 **[Releases 页面](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)**
2. 下载最新版本：`游戏摇杆曲线探测器_v1.8.6.exe`（约81MB）
3. 双击运行安装程序
   - 会自动检测并安装 .NET Framework 4.7+（如未安装）
   - 自动安装 ViGEmBus 虚拟控制器驱动
   - 约2-3分钟完成安装
4. 完成后在桌面或开始菜单找到应用，点击启动

#### 方式二：从源代码运行（开发者用）
```bash
# 克隆仓库
git clone https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool.git
cd Gamepad-Curve-Calibration-Tool

# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt

# 启动应用
python ui_app.py
```

### 📖 详细使用教程

#### **第一步：准备阶段**
1. 将USB游戏手柄插入电脑USB口（或打开无线手柄接收器）
2. 等待Windows识别设备（通常5-10秒）
3. 打开"游戏摇杆曲线探测器"应用
4. 应用会自动扫描可用的输入设备并列在下拉菜单中

#### **第二步：配置标定参数**
```
设备选择 → 摇杆选择 → 参数配置
```
- **选择设备**：从列表中选择要标定的手柄
- **选择摇杆**：左摇杆 or 右摇杆
- **设置采样点**：
  - 快速检测：20-30点（用时2-3分钟）
  - 标准标定：50点（用时5-8分钟，推荐）
  - 精细标定：100点（用时10-15分钟，专业用）

#### **第三步：执行标定**
1. 点击**"开始测试"**按钮，进入标定模式
2. 屏幕上显示摇杆位置提示圆
3. **按照提示缓慢均匀转动摇杆**，形成完整圆形路径
4. **关键要点**：
   - 速度要慢（约2-3秒完成一圈）
   - 要覆盖摇杆的完整活动范围
   - 不要跳过任何区域
5. 过程中实时显示采样点分布图和响应曲线

#### **第四步：查看结果**
- 系统自动生成**拟合曲线图表**
- 显示曲线函数方程（R²拟合度）
- 列出检测到的曲线类型
- 显示任意轴的延迟、漂移等统计信息

#### **第五步：数据导出与应用**
- **导出格式**：JSON、CSV、二进制配置
- **应用方式**：
  - 兼容游戏：在游戏设置中导入配置文件
  - ViGEm虚拟手柄：自动生效，旧游戏无需额外配置
  - 开发者：JSON格式可直接整合到游戏代码
- **保存位置**：默认保存到用户文档文件夹

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

### 📊 支持的摇杆设备

✅ **Xbox系列**：Xbox Controller（一代）、Xbox One Controller、Xbox Series X/S Controller
✅ **PlayStation系列**：DualShock 4、DualSense（PS5手柄）
✅ **任天堂系列**：Pro Controller、Joy-Con（需驱动）
✅ **街机设备**：街机摇杆、格斗杆（8向摇杆）
✅ **赛车设备**：方向盘、油门踏板、制动器
✅ **飞行设备**：飞行摇杆、多轴手柄
✅ **其他**：任何标准HID USB输入设备

### 🛠️ 系统要求 & 兼容性

| 项目 | 要求 |
|-----|-----|
| **操作系统** | Windows 7、8、8.1、10、11（32位或64位） |
| **.NET运行时** | .NET Framework 4.7+（通常已预装，缺少时会自动提示安装） |
| **驱动程序** | 通用HID驱动（Windows原生支持，无需额外安装） |
| **硬件** | USB手柄或无线接收器；需要至少1个USB端口 |
| **内存** | 最低100MB可用内存；推荐2GB+ |
| **磁盘** | 约200MB安装空间 |

### 🔧 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| **手柄未被检测** | USB连接不良或驱动缺失 | 1. 检查USB连接 / 换USB口<br> 2. 右键"设备管理器"检查是否有黄色感叹号<br> 3. 重新安装手柄驱动 |
| **"ViGEm不可用"错误** | ViGEmBus驱动未安装 | 从 `prereqs/ViGEmBus_Setup_x64.exe` 运行安装程序 |
| **采样过程中无反应** | 摇杆可能卡住或接触死区 | 1. 检查摇杆是否活动灵活<br> 2. 确保转动时覆盖完整范围<br> 3. 尝试缓慢旋转 |
| **导出文件失败** | 磁盘空间不足或权限问题 | 1. 检查磁盘剩余空间>500MB<br> 2. 以管理员身份运行应用<br> 3. 检查目标文件夹权限 |
| **UI显示错乱或缺失部分** | 字体或显示缩放问题 | 1. 尝试重启应用<br> 2. 在语言菜单中切换语言<br> 3. 调整Windows显示缩放比例 |
| **图表无法正确显示** | 图表库问题 | 重新安装应用或更新至最新版本 |

### 🎮 推荐使用场景

#### 👾 竞技游戏玩家
- **CS:GO、Valorant**：需要毫秒级精度
- **格斗游戏（街霸、拳皇）**：对输入反应速度要求极高
- **赛车游戏（F1、GT赛车）**：方向盘精度至关重要
- **射击游戏**：摇杆漂移会严重影响准度

#### 🎮 游戏开发者
- 测试和验证控制器输入曲线
- 确保游戏对不同手柄的兼容性
- 优化手柄相关的游戏参数

#### 🔧 硬件维修人员
- 检测旧手柄是否存在硬件故障
- 评估维修前后的性能改善
- 生成维修报告数据

#### ♿ 无障碍用户
- 根据个人需求定制摇杆响应曲线
- 改善对特殊输入需求的支持

### 💡 高级特性（专业用户）

#### 批量标定
- 可连续标定多个摇杆
- 每个设备自动生成独立的配置文件
- 支持批量导出对比

#### 曲线对比分析
- 对比新旧手柄的性能差异
- 追踪手柄随时间推移的性能衰减
- 生成对比报告

#### 自定义曲线
- 高级用户可手动编辑响应曲线参数
- 支持从第三方导入标定参数
- 微调算法参数以获得最佳效果

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
