"""Internationalization support for Blender UI text."""

import bpy

ADDON_TRANSLATION_NAME = "simple_lip_sync"
CONTEXT = "*"

ZH_CN = {
    "Advanced": "高级",
    "A user preset named '{name}' already exists": "名为“{name}”的用户预设已存在",
    "A tuning preset named '{name}' already exists": "名为“{name}”的调参预设已存在",
    "Anticipation": "预判",
    "Applied tuning preset: {name}": "已应用调参预设：{name}",
    "Apply Tuning Preset": "应用调参预设",
    "Apply the selected tuning preset to the advanced values": "将当前调参预设应用到高级参数",
    "Audio Path": "音频路径",
    "Audio Source": "音频来源",
    "Audio starts at frame {frame}": "音频从第 {frame} 帧开始",
    "Audio Strip": "音频片段",
    "Built-in": "内置",
    "Channel {channel}": "通道 {channel}",
    "Choose the overall lip sync motion style": "选择整体口型运动风格",
    "Clear Audio Cache": "清除音频缓存",
    "Clear cached converted WAV files to force re-conversion on next generation": "清除已转换的 WAV 缓存，强制下次重新转换音频",
    "Clear Speech": "清晰语音",
    "Cleared audio cache": "已清除音频缓存",
    "Create Lip Sync Preset": "创建口型同步预设",
    "Create Preset": "创建预设",
    "Create a user preset from the mapping fields": "根据映射字段创建用户预设",
    "Created lip sync preset": "已创建口型同步预设",
    "Custom Lip Sync": "自定义口型同步",
    "Custom Tuning": "自定义调参",
    "DB Threshold": "分贝阈值",
    "Delayed Opening": "延迟张嘴",
    "Delete": "删除",
    "Delete Lip Sync Preset": "删除口型同步预设",
    "Delete Tuning Preset": "删除调参预设",
    "Delete the selected user preset": "删除当前用户预设",
    "Delete the selected user preset?": "要删除当前用户预设吗？",
    "Delete the selected tuning preset": "删除当前调参预设",
    "Delete the selected tuning preset?": "要删除当前调参预设吗？",
    "Deleted preset: {name}": "已删除预设：{name}",
    "Deleted tuning preset: {name}": "已删除调参预设：{name}",
    "Export": "导出",
    "Export Lip Sync Preset": "导出口型同步预设",
    "Export Selected Preset": "导出当前预设",
    "Export Preset": "导出预设",
    "Export path is empty": "导出路径为空",
    "Export the selected JSON preset": "导出当前 JSON 预设",
    "Exported preset: {path}": "已导出预设：{path}",
    "File": "文件",
    "Generate Lip Sync": "生成口型同步",
    "Generate lip sync keyframes for selected meshes": "为选中的网格生成口型同步关键帧",
    "Generated lip sync for {mesh_count} mesh object(s)": "已为 {mesh_count} 个网格对象生成口型同步",
    "Import": "导入",
    "Import Lip Sync Preset": "导入口型同步预设",
    "Import Preset": "导入预设",
    "Import a JSON lip sync preset into the user preset directory": "将 JSON 口型同步预设导入用户预设目录",
    "Imported lip sync preset": "已导入口型同步预设",
    "Lip Sync Preset": "口型同步预设",
    "MMD": "MMD",
    "Max Morph Value": "最大形态键值",
    "Motion": "运动风格",
    "Name": "名称",
    "Natural": "自然",
    "No audio file path specified": "未指定音频文件路径",
    "No audio strips found": "未找到音频片段",
    "No presets found": "未找到预设",
    "No selected mesh contains configured shape keys: {shape_keys}": "选中的网格不包含配置的形态键：{shape_keys}",
    "No timeline audio strip selected": "未选择时间线音频片段",
    "No tuning presets found": "未找到调参预设",
    "No user presets found": "未找到用户预设",
    "None": "无",
    "Open Lip Sync Preset Folder": "打开口型同步预设目录",
    "Open User Preset Folder": "打开用户预设目录",
    "Open the user preset folder": "打开用户预设目录",
    "Opened preset folder: {path}": "已打开预设目录：{path}",
    "Opening Speed": "张嘴速度",
    "Only user presets can be deleted": "只能删除用户预设",
    "Path to an audio file": "音频文件路径",
    "Please choose an export path": "请选择导出路径",
    "Please select a preset file to import": "请选择要导入的预设文件",
    "Please select a tuning preset": "请选择调参预设",
    "Please select a user preset": "请选择用户预设",
    "Please select a valid lip sync preset": "请选择有效的口型同步预设",
    "Please select an object first": "请先选择对象",
    "Preset": "预设",
    "Preset Name": "预设名称",
    "Preset name is empty": "预设名称为空",
    "Presets": "预设",
    "RMS Threshold": "RMS 阈值",
    "Save Tuning Preset": "保存调参预设",
    "Save current advanced tuning values as a reusable preset": "将当前高级调参参数保存为可复用预设",
    "Saved tuning preset": "已保存调参预设",
    "Selected": "选中项",
    "Selected strip '{name}' has no valid audio filepath": "选中的片段“{name}”没有有效的音频文件路径",
    "Select an audio strip from the timeline": "从时间线中选择音频片段",
    "Select the shape-key mapping preset": "选择形态键映射预设",
    "Select a user preset to manage": "选择要管理的用户预设",
    "Sharper mouth motion for clearer articulation": "更清晰、更锐利的嘴型运动",
    "Smooth and balanced motion for most dialogue": "适合大多数对白的平滑均衡运动",
    "Soft Motion": "柔和运动",
    "Smaller and softer mouth motion": "更小、更柔和的嘴型运动",
    "Start Frame": "起始帧",
    "Timeline": "时间线",
    "Tuning Preset": "调参预设",
    "Tuning Preset Name": "调参预设名称",
    "Tuning preset name is empty": "调参预设名称为空",
    "Tuning preset not found": "未找到调参预设",
    "Use MMD Mapping": "使用 MMD 映射",
    "Use VRM Mapping": "使用 VRM 映射",
    "Use Selected Shape Keys": "使用选中形态键",
    "Use an audio file from disk": "使用磁盘上的音频文件",
    "Use audio from the Video Sequence Editor timeline": "使用视频序列编辑器时间线中的音频",
    "Use manual tuning instead of the selected motion preset": "使用手动调参而不是所选运动预设",
    "Using generation preset": "正在使用生成预设",
    "User Preset": "用户预设",
    "VRM": "VRM",
    "Where to get the audio for lip sync generation": "口型同步生成使用的音频来源",
}

TRANSLATIONS = {
    "zh_CN": {(CONTEXT, key): value for key, value in ZH_CN.items()},
    "zh_HANS": {(CONTEXT, key): value for key, value in ZH_CN.items()},
}


def register():
    """Register add-on translations."""
    unregister()
    bpy.app.translations.register(ADDON_TRANSLATION_NAME, TRANSLATIONS)


def unregister():
    """Unregister add-on translations if they are present."""
    try:
        bpy.app.translations.unregister(ADDON_TRANSLATION_NAME)
    except RuntimeError:
        pass


def translate(text):
    """Translate UI text using Blender's active locale."""
    return bpy.app.translations.pgettext_iface(text)
