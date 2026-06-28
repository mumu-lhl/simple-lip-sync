# Simple Lip Sync

[![Ruff](https://img.shields.io/github/check-runs/mumu-lhl/simple-lip-sync/main?nameFilter=Ruff&label=ruff&logo=github&style=flat-square)](https://github.com/mumu-lhl/simple-lip-sync/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/github/check-runs/mumu-lhl/simple-lip-sync/main?nameFilter=Python%20tests&label=tests&logo=github&style=flat-square)](https://github.com/mumu-lhl/simple-lip-sync/actions/workflows/ci.yml)
[![Bandit](https://img.shields.io/github/check-runs/mumu-lhl/simple-lip-sync/main?nameFilter=Bandit&label=bandit&logo=github&style=flat-square)](https://github.com/mumu-lhl/simple-lip-sync/actions/workflows/ci.yml)

[English](README.md)

Simple Lip Sync 是一个 Blender 插件，从 [hbr_mmd_tools](https://github.com/skys-mission/hbr_mmd_tools) 中提取口型同步功能并整合为独立插件。

它可以从音频文件或视频序列编辑器（VSE）的音频片段生成形态键动画。插件内置了 MMD 和 VRM 口型同步预设，并支持用户创建、导入和导出预设。

## 兼容性

- Blender 4.2 及以上版本，包括 Blender 5.1
- Blender 内置 Python 3.11 ~ 3.13
- Windows、Linux、macOS

插件可以使用可选的 Rust 原生音频分析后端（如果发布包中包含）。若不可用，会自动回退到 Python 标准库分析器。FFmpeg 用于音频格式转换；如果 FFmpeg 未随插件提供或不在 `PATH` 中，则只能直接分析 PCM WAV 输入文件。

## 安装

将 `simple_lip_sync` 目录打包成 zip 或下载发布版压缩包，然后在 Blender 中通过 `编辑 > 偏好设置 > 插件 > 安装` 进行安装。

## 使用

1. 选中包含目标嘴部形态键的网格或父级对象。
2. 打开 `3D视口 > 侧边栏 > Simple Lip Sync`。
3. 选择音频文件或时间线音频片段。
4. 选择 MMD 或 VRM 预设，或创建/导入自定义预设。
5. 点击 `生成口型同步`。

如需调整更慢、更柔和、更清晰或更少噪音的嘴部运动，请参阅[高级调参指南](docs/advanced_tuning_guide_zh.md)。

## 预设

预设 JSON 文件将标准 viseme（`a`、`i`、`u`、`e`、`o`、`n`）映射到形态键名称，并可选择调整其强度：

```json
{
  "name": "MMD Lip Sync",
  "description": "标准 MMD 口型同步配置",
  "version": "1.0",
  "type": "lip_sync",
  "shape_keys": {
    "a": "あ",
    "i": "い",
    "u": "う",
    "e": "え",
    "o": "お",
    "n": "ん"
  }
}
```

用户预设存储在 Blender 用户脚本预设目录的 `presets/simple_lip_sync/lip_sync` 下，例如 Linux 上的 `~/.config/blender/5.1/scripts/presets/simple_lip_sync/lip_sync`。
