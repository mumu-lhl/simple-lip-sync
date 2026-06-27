# hbr_mmd_tools 口型同步原理分析

本文基于本仓库中的 `hbr_mmd_tools` 源码整理，重点文件包括：

- `hbr_mmd_tools/src/services/lip_sync_service.py`
- `hbr_mmd_tools/src/audio/lips.py`
- `hbr_mmd_tools/src/audio/rosa.py`
- `hbr_mmd_tools/src/audio/viseme_curve.py`
- `hbr_mmd_tools/src/core/config_schema.py`
- `hbr_mmd_tools/src/core/lip_sync_profiles.py`
- `hbr_mmd_tools/configs/lip_sync/mmd.json`
- `hbr_mmd_tools/configs/lip_sync/vrm.json`

## 总体流程

`hbr_mmd_tools` 的口型同步功能把音频转换为 6 个标准口型通道，再把这些通道映射到模型形态键：

1. 从文件路径或 VSE 时间线音频条解析音频源。
2. 使用 FFmpeg 把任意音频转为 16 kHz 单声道 WAV。
3. 使用音频分析器按短帧读取音频，计算每帧的 RMS、dB 和频谱特征。
4. 根据能量计算嘴巴开合度，根据共振峰特征估计 `a/i/u/e/o/n` 六类 viseme 权重。
5. 对权重做前瞻、攻击/释放平滑和总量限制，得到连续但不会过度叠加的口型曲线。
6. 把曲线简化为稀疏关键帧。
7. 使用预设 JSON 把标准口型映射到目标形态键名，并写入 shape key `value` 关键帧。

## 音频分析

原插件的 `Lips.mmd_lips_gen()` 是口型生成入口。它先调用 `convert_to_wav_16000()`，再调用 `rosa()` 生成 viseme 样本，最后调用 `build_viseme_keyframes()` 生成关键帧。

`rosa()` 的分析窗口为：

- `frame_length = 1024`
- `hop_length = 160`
- 采样率 16 kHz

这相当于约 64 ms 的分析窗口和 10 ms 的步进。每一帧会乘 Hann 窗，然后计算：

- RMS：表示该帧能量。
- dB：从 RMS 转换出的分贝值。
- openness：由 dB 阈值和 RMS 阈值共同映射出的嘴巴开合度。

当 openness 足够大时，原插件用 FFT 在 180 Hz 到 3200 Hz 之间寻找频谱峰值，并粗略估计第一、第二共振峰 `f1/f2`。

## Viseme 打分

原插件内置 6 个标准口型：

- `a`
- `i`
- `u`
- `e`
- `o`
- `n`

每个口型都有一组经验共振峰原型。例如 `a` 的 `f1` 较高，`i` 的 `f2` 较高，`u/o` 的 `f2` 较低。`score_visemes()` 会计算当前 `f1/f2` 到每个原型的距离，并用高斯权重转成 6 个口型的相对概率。之后会做少量偏置修正，例如高 `f2` 会偏向 `i`，低 `f2` 会偏向 `u/o`。

## 曲线平滑和关键帧稀疏化

`build_viseme_keyframes()` 将逐帧样本变成动画曲线。核心处理包括：

- 前瞻混合：当前帧混入后续 1 到 2 帧的权重，让口型提前准备，减少声音和嘴型的滞后。
- 对比度：通过指数运算让主导口型更突出。
- 攻击/释放：张嘴时使用更快的追踪系数，闭嘴或减小时使用更慢的释放系数。
- 开合度包络：所有口型的权重总和不能超过当前 openness，避免多个形态键叠加过量。
- 尾部释放：音频末尾追加若干归零样本，保证嘴巴闭合。
- 稀疏化：保留起止点、转折点、跨越静音点和长间隔点，删除对曲线形状影响很小的中间点。

最终每个标准口型都会得到一组 `{frame, value, frame_type}` 关键帧。

## 预设映射

口型预设是 JSON 文件。内置 MMD 预设将标准口型映射为日文形态键：

- `a -> あ`
- `i -> い`
- `u -> う`
- `e -> え`
- `o -> お`
- `n -> ん`

内置 VRM 预设将标准口型映射为大写英文字母：

- `a -> A`
- `i -> I`
- `u -> U`
- `e -> E`
- `o -> O`
- `n -> N`

`adjustment_rules` 用于修正不同口型的相对强弱：

- `priority`：整体乘法权重。
- `adjustment_factor`：通过指数曲线调整形态键响应。

写入 Blender 之前，服务层会按预设把标准口型轨道合并到目标形态键。如果多个标准口型映射到同一个目标形态键，同一帧会保留较大的值。

## 写入形态键

`set_lips_to_mesh_with_config()` 会在选中对象及其子对象中查找包含目标形态键的网格。写入前会先清理生成范围内已有的对应 shape key 关键帧，再逐帧设置 `shape_key.value` 并调用 `keyframe_insert(data_path="value", frame=...)`。

这样做的好处是重新生成同一段音频时不会和旧关键帧叠加，但不会删除其他形态键或范围外的动画。

## Simple Lip Sync 的实现取舍

新插件 `Simple Lip Sync` 复用了上述数据流、预设格式、调参预设、曲线平滑和形态键写入原则，但为了兼容 Blender 5.1 / Python 3.13，音频分析层没有直接依赖 `librosa` 和 `numpy`。

新实现使用：

- FFmpeg 或系统 PATH 中的 FFmpeg 做音频转码。
- Python 标准库 `wave` 读取 PCM WAV。
- Python 标准库 `math` 实现 Hann 窗、RMS、dB 和 Goertzel 频点能量分析。

这保持了“能量控制开合度、共振峰原型控制口型类别、平滑曲线写入 shape key”的核心原理，同时避免 Blender 5.1 中第三方二进制包与 Python 3.13 的兼容风险。

