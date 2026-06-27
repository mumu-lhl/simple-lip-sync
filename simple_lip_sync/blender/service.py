"""Blender-facing lip sync services."""

import os

import bpy

from ..audio.lips import Lips
from ..core.config_manager import ConfigManager
from ..core.profiles import get_lip_sync_preset_values
from ..core.schema import CANONICAL_LIP_SYNC_KEYS
from .i18n import translate as _

_CONFIG_MANAGER = None


def get_config_manager():
    """Return the add-on config manager."""
    global _CONFIG_MANAGER
    if _CONFIG_MANAGER is None:
        addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_scripts_dir = bpy.utils.user_resource("SCRIPTS")
        _CONFIG_MANAGER = ConfigManager(addon_dir, user_scripts_dir, translate_func=_)
    return _CONFIG_MANAGER


def get_timeline_audio_items(_self, context):
    """Build enum items for VSE sound strips."""
    scene = context.scene
    se = scene.sequence_editor
    if not se:
        return [("", _("None"), _("No audio strips found"))]

    items = []
    seen_ids = set()
    for strip in sorted(se.sequences, key=lambda item: item.channel, reverse=True):
        if strip.type == "SOUND":
            filepath = getattr(strip.sound, "filepath", None)
        elif strip.type == "MOVIE":
            filepath = getattr(getattr(strip, "sound", None), "filepath", None)
        else:
            continue
        if not filepath:
            continue
        uid = f"{strip.channel}:{strip.name}"
        if uid not in seen_ids:
            seen_ids.add(uid)
            items.append((
                uid,
                strip.name,
                _("Channel {channel}").format(channel=strip.channel),
            ))
    return items if items else [("", _("None"), _("No audio strips found"))]


def get_lip_sync_config_items(_self, _context):
    """Build enum items for lip sync presets."""
    entries = get_config_manager().get_config_entries()
    items = [
        (entry["id"], entry["display_name"], entry["description"])
        for entry in entries
    ]
    return items if items else [("", _("None"), _("No presets found"))]


def generate_lip_sync(context):
    """Generate lip sync shape-key keyframes for selected meshes."""
    scene = context.scene
    fps = scene.render.fps
    start_frame = scene.sls_start_frame

    if scene.sls_audio_source == "timeline":
        strip = find_timeline_audio_strip(scene)
        if strip is not None:
            start_frame = int(strip.frame_final_start)

    wav_path = resolve_audio_path(scene)
    config = get_config_manager().load_config(scene.sls_config_selection)
    if not config:
        raise ValueError(_("Please select a valid lip sync preset"))

    tuning = resolve_tuning(scene)
    lips = Lips.mmd_lips_gen(
        wav_path=wav_path,
        buffer=tuning["buffer"],
        approach_speed=tuning["approach_speed"],
        db_threshold=tuning["db_threshold"],
        rms_threshold=tuning["rms_threshold"],
        max_morph_value=tuning["max_morph_value"],
        start_frame=start_frame,
        fps=fps,
        anticipation_scale=tuning["anticipation_scale"],
    )

    meshes = find_meshes_with_config(context, config)
    for mesh in meshes:
        set_lips_to_mesh_with_config(mesh, lips, start_frame, config)
    return {"mesh_count": len(meshes), "lips": lips, "config": config}


def find_timeline_audio_strip(scene):
    """Find the selected timeline audio strip."""
    se = scene.sequence_editor
    if not se:
        return None
    selected_uid = scene.sls_timeline_audio_strip
    if not selected_uid:
        return None
    for strip in se.sequences:
        if f"{strip.channel}:{strip.name}" == selected_uid:
            return strip
    return None


def resolve_audio_path(scene):
    """Resolve audio file path from file or timeline settings."""
    if scene.sls_audio_source == "file":
        path = scene.sls_audio_path
        if not path:
            raise ValueError(_("No audio file path specified"))
        return bpy.path.abspath(path)

    strip = find_timeline_audio_strip(scene)
    if strip is None:
        raise ValueError(_("No timeline audio strip selected"))

    filepath = None
    if strip.type == "SOUND":
        filepath = getattr(strip.sound, "filepath", None)
    elif strip.type == "MOVIE":
        filepath = getattr(getattr(strip, "sound", None), "filepath", None)
    if not filepath:
        raise ValueError(
            _("Selected strip '{name}' has no valid audio filepath").format(name=strip.name)
        )
    return bpy.path.abspath(filepath)


def resolve_tuning(scene):
    """Resolve generation tuning from preset or custom scene values."""
    if getattr(scene, "sls_use_custom_tuning", False):
        return {
            "buffer": scene.sls_buffer,
            "approach_speed": scene.sls_approach_speed,
            "db_threshold": scene.sls_db_threshold,
            "rms_threshold": scene.sls_rms_threshold,
            "max_morph_value": scene.sls_max_morph_value,
            "anticipation_scale": scene.sls_anticipation_scale,
        }
    return get_lip_sync_preset_values(scene.sls_generation_preset)


def find_meshes_with_config(context, config):
    """Find selected meshes or selected object descendants with target shape keys."""
    shape_keys = list(config.get("shape_keys", {}).values())
    selected_objects = context.selected_objects
    if not selected_objects:
        raise ValueError(_("Please select an object first"))

    found_objects = []
    seen = set()
    for obj in selected_objects:
        collect_meshes_with_shape_keys(obj, shape_keys, found_objects, seen)

    if not found_objects:
        joined_shape_keys = ", ".join(shape_keys)
        raise ValueError(
            _("No selected mesh contains configured shape keys: {shape_keys}").format(
                shape_keys=joined_shape_keys,
            )
        )
    return found_objects


def collect_meshes_with_shape_keys(obj, shape_key_names, found_objects, seen):
    """Collect mesh objects under ``obj`` that contain any target shape key."""
    if obj.type == "MESH" and obj.data.shape_keys:
        existing_shape_keys = {key.name for key in obj.data.shape_keys.key_blocks}
        if any(name in existing_shape_keys for name in shape_key_names):
            object_id = obj.as_pointer()
            if object_id not in seen:
                seen.add(object_id)
                found_objects.append(obj)

    for child in obj.children:
        collect_meshes_with_shape_keys(child, shape_key_names, found_objects, seen)


def set_lips_to_mesh_with_config(mesh, lips, start_frame, config):
    """Apply generated lip tracks to one mesh using a preset mapping."""
    shape_key_mapping = config.get("shape_keys", {})
    adjustment_rules = config.get("adjustment_rules", {})
    target_tracks = build_target_tracks(lips, shape_key_mapping, adjustment_rules)

    start = float(max(start_frame, 1))
    end = start
    for track in target_tracks.values():
        for keyframe in track:
            end = max(end, float(keyframe["frame"]))

    existing_morphs = (
        {key.name for key in mesh.data.shape_keys.key_blocks}
        if mesh.data.shape_keys else set()
    )

    for morph_key in target_tracks:
        if morph_key in existing_morphs:
            clear_shape_key_keyframes_in_range(mesh, morph_key, start, end)

    for target_morph_key, morph_frames in target_tracks.items():
        if target_morph_key not in existing_morphs:
            continue
        for morph_frame in morph_frames:
            if morph_frame["frame"] < start:
                continue
            set_shape_key_value(
                mesh,
                target_morph_key,
                morph_frame["value"],
                morph_frame["frame"],
            )


def build_target_tracks(lips, shape_key_mapping, adjustment_rules):
    """Map canonical viseme tracks to configured target shape-key tracks."""
    target_tracks = {}
    for source_key in CANONICAL_LIP_SYNC_KEYS:
        target_morph_key = shape_key_mapping.get(source_key, source_key)
        target_track = target_tracks.setdefault(target_morph_key, {})
        adjustment_rule = adjustment_rules.get(source_key, {})

        for morph_frame in lips.get(source_key, []):
            adjusted_value = apply_adjustment_rule(morph_frame["value"], adjustment_rule)
            frame = round(float(morph_frame["frame"]), 3)
            frame_key = f"{frame:.3f}"
            existing_frame = target_track.get(frame_key)
            if existing_frame is None or adjusted_value >= existing_frame["value"]:
                target_track[frame_key] = {
                    "frame": frame,
                    "value": adjusted_value,
                    "frame_type": morph_frame.get("frame_type", "sample"),
                }

    return {
        target_key: sorted(frame_map.values(), key=lambda item: item["frame"])
        for target_key, frame_map in target_tracks.items()
    }


def apply_adjustment_rule(value, rule):
    """Apply preset priority and curve adjustment to a morph value."""
    base_value = max(0.0, float(value))
    if base_value <= 0.0:
        return 0.0

    priority = float(rule.get("priority", 1.0))
    adjustment_factor = float(rule.get("adjustment_factor", 1.0))
    if adjustment_factor > 0.0 and abs(adjustment_factor - 1.0) > 1e-6:
        base_value = base_value ** (1.0 / adjustment_factor)

    adjusted_value = base_value * priority
    return min(max(adjusted_value, 0.0), 0.99)


def clear_shape_key_keyframes_in_range(obj, shape_key_name, start_frame, end_frame):
    """Clear existing shape-key keyframes in the generated frame range."""
    if not obj or obj.type != "MESH":
        return

    shape_keys = obj.data.shape_keys
    if not shape_keys or shape_key_name not in shape_keys.key_blocks:
        return

    shape_key = shape_keys.key_blocks[shape_key_name]
    anim_data = shape_key.id_data.animation_data
    if not anim_data or not anim_data.action:
        return

    data_path = shape_key.path_from_id("value")
    for fcurve in list(anim_data.action.fcurves):
        if fcurve.data_path != data_path:
            continue
        for index in range(len(fcurve.keyframe_points) - 1, -1, -1):
            keyframe = fcurve.keyframe_points[index]
            if float(start_frame) <= keyframe.co[0] <= float(end_frame):
                fcurve.keyframe_points.remove(keyframe)
        if not fcurve.keyframe_points:
            anim_data.action.fcurves.remove(fcurve)
        else:
            fcurve.update()
        return


def set_shape_key_value(obj, shape_key_name, value, frame):
    """Set and keyframe one shape key value."""
    if not obj or obj.type != "MESH":
        raise ValueError("The object is not a mesh")

    shape_keys = obj.data.shape_keys
    if not shape_keys or shape_key_name not in shape_keys.key_blocks:
        raise ValueError(f"The shape key '{shape_key_name}' does not exist")

    shape_key = shape_keys.key_blocks[shape_key_name]
    shape_key.value = value
    shape_key.keyframe_insert(data_path="value", frame=frame)
