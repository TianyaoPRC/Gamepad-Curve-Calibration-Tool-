# 🎮 Gamepad Curve Calibration Tool | 游戏摇杆曲线探测器

> **游戏手柄响应曲线检测工具**
> **Game Response Curve Detection Tool for Gamers**

![Version](https://img.shields.io/badge/version-1.8.6-blue)
![Platform](https://img.shields.io/badge/platform-Windows%207+-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Languages](https://img.shields.io/badge/languages-EN%20%7C%20ZH-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7+-blue)

**[中文版本](#-中文版本中文详细介绍) | [English](#-english-version) | [日本語参考](#-日本語翻訳版参考用)**

---

## 🌍 中文版本：中文详细介绍

### 📖 什么是"游戏摇杆曲线探测器"？

这是一款**游戏手柄响应曲线检测工具**，专为游戏玩家设计。它的核心用途是：

1. **检测游戏曲线**：测试不同游戏对手柄输入的响应曲线，了解每个游戏的手柄手感
2. **跨游戏手感统一**：帮助玩家在不同游戏之间找到统一的操作感受
3. **曲线对比分析**：对比多个游戏的手柄响应特性，找出手感差异
4. **灵敏度参考**：为调整游戏内灵敏度设置提供数据参考
5. **可视化展示**：通过曲线图直观看到不同游戏的手柄响应差异

**重要说明**：
- ⚠️ 本工具**仅用于检测和测试**，不会修改您的物理手柄
- ⚠️ 本工具**不会修改游戏参数**，只是测量和展示
- ⚠️ 本工具帮助您**了解游戏差异**，需要手动在游戏内调整灵敏度

### 🎯 核心功能特性

| 功能模块 | 详细说明 |
|---------|--------|
| **游戏曲线检测** | 测试您正在玩的游戏对手柄输入的实际响应曲线 |
| **采样点分析** | 支持1-100个采样点，精确测量游戏的手柄响应特性 |
| **实时曲线可视化** | 测试过程中实时显示游戏的手柄响应曲线图 |
| **多游戏对比** | 对比不同游戏的曲线差异，找出手感不一致的原因 |
| **灵敏度建议** | 基于曲线分析，建议游戏内灵敏度调整方向 |
| **完整国际化** | 内置英文、简体中文；支持用户自定义翻译 |
| **数据导出** | 导出测试结果供参考和对比 |

### 🚀 为什么玩家需要这个工具？

#### 玩家常见痛点
- ❌ **不同游戏手感不一致**：同样的手柄，在《使命召唤》和《战地》中操作感觉完全不同
- ❌ **难以调整灵敏度**：不知道该调高还是调低游戏内灵敏度
- ❌ **切换游戏不适应**：从一个游戏切到另一个游戏总要重新适应
- ❌ **无法量化差异**：只能"感觉"不同，说不清到底差在哪里
- ❌ **找不到最佳设置**：反复试探游戏灵敏度设置浪费时间

#### 本工具的价值
✅ **可视化差异**：用曲线图清晰展示不同游戏的手柄响应差异
✅ **量化分析**：精确数据告诉您哪个游戏更灵敏、哪个更迟钝
✅ **统一手感**：基于测试结果，在游戏内调整灵敏度以获得统一的操作体验
✅ **节省时间**：不再盲目试探，直接看数据调整
✅ **跨游戏适配**：帮助您在所有游戏中获得一致的手柄手感

### 📦 安装与快速开始

#### 方式一：下载预编译版本（推荐 ⭐）
1. 访问 **[Releases 页面](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)**
2. 下载最新版本：`游戏摇杆曲线探测器_v1.8.6.exe`（约81MB）
3. 双击运行安装程序
4. 完成安装后启动应用

#### 方式二：从源代码运行（开发者用）
```bash
git clone https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool.git
cd Gamepad-Curve-Calibration-Tool
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python ui_app.py
```

### 📖 使用步骤（玩家视角）

#### **第一步：启动游戏和工具**
- 打开您要测试的游戏（例如《使命召唤》）
- 同时运行本检测工具

#### **第二步：配置测试参数**
- 设置采样点数（建议20-50点）
- 选择要测试的摇杆（左摇杆/右摇杆）

#### **第三步：进行测试**
- 点击**"开始测试"**
- 在游戏中移动手柄摇杆
- 工具会实时显示游戏对摇杆的响应曲线

#### **第四步：查看结果**
- 查看生成的响应曲线图表
- 了解该游戏的手柄响应特性
- 保存测试结果

#### **第五步：对比游戏**
- 切换到另一个游戏（例如《战地》）
- 重复测试流程
- 对比两个游戏的曲线差异

#### **第六步：调整灵敏度**
- 根据曲线差异，在游戏内调整灵敏度
- 目标是让不同游戏的曲线尽可能一致
- 重新测试验证调整效果

## 📋 使用场景

### 场景1：统一跨游戏手感
**目标**：让不同游戏的手柄操作感受保持一致
- 使用工具测试您常玩的几款游戏的手柄响应曲线
- 对比各游戏的曲线差异，找出手感不一致的原因
- 根据测试数据，在各游戏内调整灵敏度设置
- 验证调整后不同游戏的手感是否趋于一致

### 场景2：新游戏快速适配
**目标**：快速将新游戏的手感调整到您熟悉的水平
- 测试新游戏的手柄响应曲线
- 对比与您最熟悉游戏的曲线差异
- 根据差异在新游戏中调整灵敏度
- 快速获得熟悉的操作手感

### 场景3：手感问题诊断
**目标**：定位某个游戏"手感不对"的具体原因
- 测试感觉"不对"的游戏和感觉"正常"的游戏
- 对比两者的曲线差异
- 找出具体是哪个轴向、哪个范围的响应不同
- 针对性调整游戏内设置解决问题

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
- 创建新文件 `languages/语言代码.json`
- 使用AI翻译工具翻译所有值
- 保持JSON结构完全相同

**步骤3：应用翻译**
- 将翻译好的JSON文件保存到 `languages/` 文件夹
- 重启应用程序
- 在语言菜单中选择新语言

### 🛠️ 系统要求

| 项目 | 要求 |
|-----|-----|
| **操作系统** | Windows 7/8/10/11 |
| **运行时** | Python 3.7+ 或预编译exe |
| **内存** | 最低100MB |
| **磁盘** | 约200MB |

### 🔧 常见问题

| 问题 | 解决方案 |
|------|--------|
| **手柄无法检测** | 确保手柄已连接并安装驱动 |
| **曲线显示异常** | 尝试增加采样点数量 |
| **数据导出失败** | 检查磁盘空间和权限 |

---

## 🌍 English Version

### 📖 What is "Gamepad Curve Calibration Tool"?

This is a **game response curve detection tool** designed for gamers. Its core purposes are:

1. **Detect Game Response**: Test how different games respond to gamepad input and understand each game's feel
2. **Cross-Game Consistency**: Help you achieve consistent control feel across different games
3. **Curve Comparison**: Compare gamepad response characteristics between games to identify differences
4. **Sensitivity Reference**: Provide data reference for adjusting in-game sensitivity settings
5. **Visual Representation**: Clearly display response differences through curve graphs

**Important Notes**:
- ⚠️ This tool is **for detection only** and does NOT modify your physical gamepad
- ⚠️ This tool does NOT modify game parameters, it only measures and displays
- ⚠️ You need to **manually adjust in-game sensitivity** based on the tool's findings

### 🎯 Core Features

| Feature | Description |
|---------|-------------|
| **Game Response Detection** | Test how games respond to your gamepad input |
| **Sampling Analysis** | 1-100 sampling points for precise measurement |
| **Real-time Visualization** | Display game response curves in real-time |
| **Multi-Game Comparison** | Compare curves between games |
| **Sensitivity Suggestions** | Recommend sensitivity adjustments |
| **Internationalization** | EN/ZH built-in, custom translations supported |
| **Data Export** | Export test results for reference |

### 🚀 Why Gamers Need This

#### Common Pain Points
- ❌ **Inconsistent feel across games**: Same gamepad feels different in Call of Duty vs Battlefield
- ❌ **Hard to adjust sensitivity**: Don't know if you should increase or decrease
- ❌ **Game switching adaptation**: Need to re-adapt when switching games
- ❌ **Can't quantify differences**: Can only "feel" it, can't explain the difference
- ❌ **Can't find best settings**: Waste time trying different settings

#### Value This Tool Provides
✅ **Visualize differences**: Show gamepad response differences with curve graphs
✅ **Quantitative analysis**: Data tells you which game is more sensitive
✅ **Unified feel**: Adjust in-game sensitivity based on test results
✅ **Save time**: No more blind trial-and-error
✅ **Cross-game adaptation**: Achieve consistent feel across all games

### 📦 Installation

#### Option 1: Download Pre-built (Recommended ⭐)
1. Visit **[Releases Page](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)**
2. Download: `游戏摇杆曲线探测器_v1.8.6.exe` (~81MB)
3. Run the installer
4. Launch the application

#### Option 2: Run from Source
```bash
git clone https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool.git
cd Gamepad-Curve-Calibration-Tool
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python ui_app.py
```

### 📖 Usage Steps (Player Perspective)

#### **Step 1: Launch Game and Tool**
- Start the game you want to test (e.g., Call of Duty)
- Run this detection tool simultaneously

#### **Step 2: Configure Test Parameters**
- Set sampling points (recommended 20-50)
- Select joystick to test (left/right stick)

#### **Step 3: Run Test**
- Click **"Start Test"**
- Move the gamepad stick in the game
- Tool displays real-time game response curve

#### **Step 4: Review Results**
- View the generated response curve graph
- Understand the game's gamepad response characteristics
- Save test results

#### **Step 5: Compare Games**
- Switch to another game (e.g., Battlefield)
- Repeat the test process
- Compare curves between the two games

#### **Step 6: Adjust Sensitivity**
- Based on curve differences, adjust in-game sensitivity
- Goal: make curves consistent across different games
- Re-test to verify adjustments

### 🌐 Localization

Add new languages easily:
1. Open `languages/en_US.json` as template
2. Create `languages/your_code.json`
3. Translate all values using AI tools
4. Save to `languages/` folder
5. Restart app and select language

### 🛠️ System Requirements

| Item | Requirement |
|------|------------|
| **OS** | Windows 7/8/10/11 |
| **Runtime** | Python 3.7+ or pre-built exe |
| **Memory** | 100MB minimum |
| **Disk** | ~200MB |

---

## 📝 日本語翻訳版（参考用）

### 📖 「ゲームパッドカーブキャリブレーションツール」とは？

これは、ゲーマーが異なるゲームのゲームパッド入力応答をテストするための**ゲーム応答カーブ検出ツール**です。主な用途：

1. **ゲーム応答検出**：各ゲームがゲームパッド入力をどのように処理するかをテスト
2. **クロスゲーム一貫性**：異なるゲーム間で一貫した操作感を実現
3. **カーブ比較**：ゲーム間のゲームパッド応答特性を比較
4. **感度リファレンス**：ゲーム内感度設定調整のためのデータ提供
5. **視覚的表示**：カーブグラフで応答差を明確に表示

**重要な注意事項**：
- ⚠️ このツールは**検出専用**で、物理ゲームパッドを変更しません
- ⚠️ ゲームパラメータを変更せず、測定と表示のみ
- ⚠️ ツールの結果に基づいて**ゲーム内で手動調整**が必要です

### 🎯 主な機能

| 機能 | 説明 |
|------|------|
| **ゲーム応答検出** | ゲームがゲームパッド入力にどう応答するかテスト |
| **サンプリング分析** | 1〜100サンプリングポイントで正確測定 |
| **リアルタイム可視化** | ゲーム応答カーブをリアルタイム表示 |
| **マルチゲーム比較** | ゲーム間のカーブ差を比較 |
| **感度推奨** | 感度調整の方向を提案 |
| **国際化** | EN/ZH内蔵、カスタム翻訳対応 |
| **データエクスポート** | テスト結果を参照用にエクスポート |

### 🚀 ゲーマーがこのツールを必要とする理由

#### よくある悩み
- ❌ **ゲーム間でフィールが異なる**：Call of DutyとBattlefieldで完全に違うフィール
- ❌ **感度調整が困難**：上げるべきか下げるべきかわからない
- ❌ **ゲーム切り替え適応**：ゲームを変えると常に再適応が必要
- ❌ **違いを定量化できない**：「感じる」だけで説明できない
- ❌ **最適設定が見つからない**：設定試行で時間を無駄にする

#### このツールの価値
✅ **差異の可視化**：カーブグラフで応答差を明確表示
✅ **定量的分析**：どのゲームが敏感かデータで判明
✅ **統一フィール**：テスト結果に基づいてゲーム内調整
✅ **時間節約**：盲目的な試行錯誤不要
✅ **クロスゲーム適応**：全ゲームで一貫したフィール実現

### 📦 インストール

1. **[リリースページ](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/releases)**から最新版をダウンロード
2. `游戏摇杆曲线探测器_v1.8.6.exe`を実行
3. インストール完了後、起動

### 🌐 ローカライゼーション

新しい言語を簡単に追加：
1. `languages/en_US.json`をテンプレートとして開く
2. `languages/your_code.json`を作成
3. AIツールで全ての値を翻訳
4. `languages/`フォルダに保存
5. アプリを再起動して言語選択

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md)

## 📞 Contact

- GitHub Issues: [Report bugs or request features](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/issues)
- Repository: https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool
