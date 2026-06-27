# Simple Lip Sync 高级参数调节指南

这份文档面向已经能成功生成口型动画，但觉得效果“不太对”的用户。最常见的问题是：口型动得太快、太碎、太夸张，或者没有声音时也在动。

## 先从预设开始

在生成面板里有一个 `Motion` 选项：

- `Natural`：默认选项，适合大多数对白。
- `Clear Speech`：嘴型更清楚、更利落，但也更容易显得快。
- `Soft Motion`：嘴型更柔和、更慢、更小，适合想减少抖动或夸张感的情况。

如果你只是觉得口型太快，建议先试 `Soft Motion`。如果还是不满意，再打开 `Advanced` 里的 `Custom Tuning` 手动调参数。

## 调参前要知道的一件事

高级参数不会改变你的预设里 A/I/U/E/O/N 对应哪个形态键。预设负责“哪个口型对应哪个 shape key”，高级参数负责“什么时候动、动多快、动多大”。

打开 `Custom Tuning` 后，插件会使用高级面板里的数值，而不是 `Motion` 预设里的默认数值。

每次修改参数后，需要重新点击 `Generate Lip Sync` 生成动画，才能看到新效果。

## 保存和复用调参预设

如果你调出了一组常用参数，可以在 `Advanced` 面板里点击 `Save Tuning Preset` 保存。保存时会弹出命名窗口，输入一个容易识别的名字即可。

以后想复用这组参数时：

1. 打开 `Advanced`。
2. 勾选 `Custom Tuning`。
3. 在 `Tuning Preset` 下拉框里选择保存过的调参预设。
4. 点击旁边的应用按钮。
5. 再点击 `Generate Lip Sync` 重新生成口型动画。

调参预设只保存高级参数，例如 `Delayed Opening`、`Opening Speed`、阈值和最大形态键值。它不会保存 A/I/U/E/O/N 对应的 shape key。shape key 映射仍然由 `Presets` 面板里的口型同步预设管理。

如果某个调参预设不再需要，可以在 `Tuning Preset` 下拉框里选中它，然后点击删除按钮。删除前会弹出确认窗口。

## 口型动得太快时怎么调

优先按这个顺序调：

1. 增大 `Delayed Opening`
2. 降低 `Opening Speed`
3. 降低 `Anticipation`
4. 必要时降低 `Max Morph Value`

推荐从下面这组值开始：

```text
Delayed Opening: 0.24
Opening Speed: 1.8
Anticipation: 0.7
Max Morph Value: 0.82
DB Threshold: -45
RMS Threshold: 0.045
```

如果你觉得还是快，把 `Opening Speed` 再降到 `1.4` 到 `1.6`。如果嘴型已经慢了但还是跳得明显，把 `Delayed Opening` 加到 `0.28` 左右。

## 参数说明

### Delayed Opening

控制口型变化的缓冲感。数值越大，嘴型越不急着切换，看起来更慢、更平滑。

可以把它理解成“嘴巴动作的惯性”。值太小，嘴型会紧跟声音快速跳动；值大一些，嘴型会有一点拖尾和过渡。

常用范围：

```text
0.10: 反应快，适合清晰念词，但可能偏碎
0.18: 默认自然值
0.24: 更柔和，适合口型太快时
0.30: 明显变慢，可能会有点跟不上快语速
```

如果你的问题是“每个音节都动得太急”，先调这个。

### Opening Speed

控制嘴巴接近目标口型的速度。数值越高，嘴巴越快张到目标形状；数值越低，动作越慢。

常用范围：

```text
1.4 - 2.0: 慢，适合柔和或不想太跳的口型
2.4 - 3.0: 自然对白
3.5 以上: 清晰但偏快，适合需要夸张读唇的效果
```

如果你的问题是“嘴巴张开和闭合太突然”，降低这个值。

### Anticipation

控制口型提前预测后面声音的程度。数值越高，嘴型越会提前向下一个音靠近；数值越低，嘴型越少提前变化。

适当的提前会让口型更自然，因为人说话时嘴形通常会提前准备下一个音。但如果数值过高，就会感觉嘴巴“抢拍”，也就是声音还没到，嘴型已经变了。

常用范围：

```text
0.5 - 0.7: 更稳，不容易抢拍
0.7 - 0.9: 自然
1.0 以上: 更清楚，但容易显得快或提前
```

如果你觉得口型比声音早，降低这个值。

### Max Morph Value

控制形态键最大强度。数值越大，嘴张得越大；数值越小，嘴张得越小。

它不会直接改变速度，但嘴张得太大时，人眼会觉得动作更猛、更快。所以口型太夸张时，降低它通常会让整体观感变稳。

常用范围：

```text
0.70 - 0.82: 柔和、小幅度
0.85 - 0.95: 自然
1.00: 完全使用形态键最大值
```

如果你的模型形态键本身就很夸张，建议不要用 `1.0`，可以从 `0.82` 到 `0.90` 试起。

### DB Threshold

控制插件把多小的声音当成“有效声音”。它是分贝阈值，数值越接近 0，要求声音越大才会触发口型。

简单说：

- 值更低，比如 `-55`：更敏感，小声音也会动。
- 值更高，比如 `-42`：更不敏感，只有较明显的声音才会动。

常用范围：

```text
-55: 很敏感，适合干净、音量小的录音
-47: 默认自然值
-42: 降低背景噪声和细碎动作
```

如果没有说话时嘴也在动，或者呼吸声、底噪让嘴型乱跳，把它调高一点，例如从 `-47` 改到 `-44`。

如果轻声说话时嘴不动，把它调低一点，例如从 `-47` 改到 `-52`。

### RMS Threshold

也是声音触发阈值，但它看的是整体音量能量。数值越高，越不容易触发口型；数值越低，越容易触发。

它和 `DB Threshold` 的效果相近，但更直接影响“音量多大才算张嘴”。

常用范围：

```text
0.015 - 0.025: 敏感，适合干净小声的音频
0.035: 默认自然值
0.045 - 0.060: 更稳，适合有噪声或口型太碎
```

如果口型太碎，可以把它从 `0.035` 调到 `0.045`。如果很多轻声词没有口型，可以调到 `0.025`。

## 常见问题和推荐调法

### 口型动得太快

推荐：

```text
Delayed Opening: 增大到 0.24 - 0.30
Opening Speed: 降低到 1.6 - 2.0
Anticipation: 降低到 0.6 - 0.8
```

如果嘴张得也很大，再把 `Max Morph Value` 降到 `0.80 - 0.88`。

### 口型太碎、一直抖

推荐：

```text
Delayed Opening: 增大
DB Threshold: 调高，例如 -47 到 -44
RMS Threshold: 调高，例如 0.035 到 0.045
```

这通常发生在音频有底噪、呼吸声、混响，或者语速很快的时候。

### 口型跟不上声音

推荐：

```text
Delayed Opening: 降低
Opening Speed: 增大
Anticipation: 稍微增大
```

比如：

```text
Delayed Opening: 0.12
Opening Speed: 3.2
Anticipation: 0.9
```

### 嘴张得太大

推荐：

```text
Max Morph Value: 降低到 0.75 - 0.88
```

如果降低后仍然夸张，说明模型的口型 shape key 本身幅度较大，需要继续降低这个值。

### 嘴张得太小

推荐：

```text
Max Morph Value: 增大
DB Threshold: 调低
RMS Threshold: 调低
```

如果音频本身音量很小，先把音频音量处理正常，通常比把阈值调得很极端更稳定。

### 没说话时嘴也动

推荐：

```text
DB Threshold: 调高
RMS Threshold: 调高
```

例如：

```text
DB Threshold: -44
RMS Threshold: 0.050
```

如果音频里有明显背景音乐、环境声或混响，自动口型同步会更容易误判。最好使用尽量干净的人声轨道。

### 轻声、气声、句尾没有口型

推荐：

```text
DB Threshold: 调低
RMS Threshold: 调低
```

例如：

```text
DB Threshold: -52
RMS Threshold: 0.025
```

但不要调得太低，否则无声部分也可能开始动。

## 推荐起点

### 更慢、更柔和

适合你现在描述的“口型动得太快”。

```text
Delayed Opening: 0.26
Opening Speed: 1.7
DB Threshold: -45
RMS Threshold: 0.045
Max Morph Value: 0.82
Anticipation: 0.65
```

### 更清楚、更适合读唇

```text
Delayed Opening: 0.10
Opening Speed: 3.6
DB Threshold: -49
RMS Threshold: 0.025
Max Morph Value: 0.98
Anticipation: 1.0
```

### 噪声多、想减少误触发

```text
Delayed Opening: 0.24
Opening Speed: 1.8
DB Threshold: -42
RMS Threshold: 0.055
Max Morph Value: 0.80
Anticipation: 0.70
```

## 建议的调参流程

不要一次改很多参数。建议这样做：

1. 先选择最接近的 `Motion`：太快选 `Soft Motion`，不清楚选 `Clear Speech`。
2. 打开 `Custom Tuning`。
3. 如果太快，先只改 `Delayed Opening` 和 `Opening Speed`。
4. 如果抢拍，再改 `Anticipation`。
5. 如果幅度太大或太小，再改 `Max Morph Value`。
6. 如果无声处乱动或轻声不动，再改 `DB Threshold` 和 `RMS Threshold`。
7. 每次只改一到两个参数，然后重新生成，比较效果。

这样更容易知道哪个参数产生了变化，也更容易调回去。

## 一个实用判断

如果你觉得“嘴型切换太快”，主要调：

```text
Delayed Opening
Opening Speed
Anticipation
```

如果你觉得“嘴动得太频繁”，主要调：

```text
DB Threshold
RMS Threshold
Delayed Opening
```

如果你觉得“嘴张得太夸张”，主要调：

```text
Max Morph Value
```

如果你不确定从哪里开始，就使用“更慢、更柔和”那组推荐值，然后一点点往回调快。
