# Simple Lip Sync

Blender add-on for generating MMD-style lip sync shape-key animation from audio.

Install this folder as a Blender add-on or install the release zip. The panel is available at:

`View3D > Sidebar > Simple Lip Sync`

The add-on includes MMD and VRM mapping presets. User presets can be created, deleted, imported, exported, and opened from the Presets panel.

User presets are stored under Blender's user scripts preset directory: `presets/simple_lip_sync/lip_sync`.

FFmpeg is used for audio conversion when available. Put a bundled executable at `audio/lib/ffmpeg` or `audio/lib/ffmpeg.exe`, or install FFmpeg on `PATH`. PCM WAV input can be analyzed directly without FFmpeg.

Platform release archives may include a native Rust audio analysis backend under `audio/native`. If it cannot be loaded, the add-on automatically falls back to the pure Python analyzer.
