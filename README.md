# Gamepad Curve Calibration Tool | 游戏摇杆曲线探测器

[English](#english) | [中文](#中文) | [日本語](#日本語)

---

## English

### Overview
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

### Contact & Support
For issues, feature requests, or questions, please open an issue on GitHub.
