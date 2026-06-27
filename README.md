# Simple Lip Sync

Simple Lip Sync is a Blender add-on that extracts the lip sync feature from [hbr_mmd_tools](https://github.com/skys-mission/hbr_mmd_tools) into a focused add-on.

It generates shape-key animation from an audio file or a Video Sequence Editor audio strip. The add-on includes the original MMD and VRM lip sync presets and supports user preset creation, import, and export.

## Compatibility

- Blender 4.2 or newer, including Blender 5.1
- Python 3.11 through 3.13 in Blender
- Windows, Linux, and macOS

The add-on can use an optional native Rust audio analysis backend when a platform release archive includes it. If that backend is unavailable, it falls back to a Python standard-library analyzer. FFmpeg is used for audio conversion when available. If FFmpeg is not bundled with the add-on or available on `PATH`, only PCM WAV input can be analyzed directly.

## Install

Zip the `simple_lip_sync` directory or download a release archive, then install it in Blender with `Edit > Preferences > Add-ons > Install`.

## Use

1. Select the mesh or parent object that contains the target mouth shape keys.
2. Open `View3D > Sidebar > Simple Lip Sync`.
3. Choose an audio file or a timeline audio strip.
4. Choose the MMD or VRM preset, or create/import a custom preset.
5. Click `Generate Lip Sync`.

For tuning slower, softer, clearer, or less noisy mouth motion, see the Chinese
[Advanced Tuning Guide](docs/advanced_tuning_guide_zh.md).

## Presets

Preset JSON files map canonical visemes (`a`, `i`, `u`, `e`, `o`, `n`) to shape-key names and optionally tune their strength:

```json
{
  "name": "MMD Lip Sync",
  "description": "Standard MMD lip sync configuration",
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

User presets are stored in Blender's user scripts preset directory under `presets/simple_lip_sync/lip_sync`, for example `~/.config/blender/5.1/scripts/presets/simple_lip_sync/lip_sync` on Linux.
