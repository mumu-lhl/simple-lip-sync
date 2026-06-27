"""Blender UI and operators."""

import os
import subprocess
import sys

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ..core.config_manager import CONFIG_SOURCE_USER
from ..core.profiles import DEFAULT_LIP_SYNC_PRESET, get_lip_sync_preset_values
from .i18n import translate as _
from .service import (
    find_timeline_audio_strip,
    generate_lip_sync,
    get_config_manager,
    get_lip_sync_config_items,
    get_timeline_audio_items,
    get_tuning_preset_manager,
    get_user_tuning_preset_entries,
    get_user_lip_sync_config_items,
    get_user_tuning_preset_items,
    NO_LIP_SYNC_CONFIG_ID,
    NO_USER_LIP_SYNC_CONFIG_ID,
    NO_USER_TUNING_PRESET_ID,
    resolve_tuning_preset_entry,
)

DEFAULT_ADJUSTMENT_RULES = {
    "a": {"priority": 1.0, "adjustment_factor": 1.2},
    "o": {"priority": 1.0, "adjustment_factor": 1.2},
    "i": {"priority": 0.9, "adjustment_factor": 0.9},
    "u": {"priority": 0.9, "adjustment_factor": 0.9},
    "e": {"priority": 0.9, "adjustment_factor": 0.9},
    "n": {"priority": 0.3, "adjustment_factor": 1.0},
}

MMD_DEFAULT_MAPPING = {
    "a": "あ",
    "i": "い",
    "u": "う",
    "e": "え",
    "o": "お",
    "n": "ん",
}

VRM_DEFAULT_MAPPING = {
    "a": "A",
    "i": "I",
    "u": "U",
    "e": "E",
    "o": "O",
    "n": "N",
}


class SIMPLE_LIP_SYNC_PT_main(bpy.types.Panel):
    """Main lip sync panel."""

    bl_label = "Simple Lip Sync"
    bl_idname = "SIMPLE_LIP_SYNC_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simple Lip Sync"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "sls_audio_source")
        if scene.sls_audio_source == "file":
            layout.prop(scene, "sls_audio_path")
        else:
            layout.prop(scene, "sls_timeline_audio_strip")
            strip = find_timeline_audio_strip(scene)
            if strip is not None:
                layout.label(
                    text=_("Audio starts at frame {frame}").format(
                        frame=int(strip.frame_final_start),
                    ),
                    icon="INFO",
                )

        layout.prop(scene, "sls_start_frame")
        layout.prop(scene, "sls_generation_preset")
        layout.prop(scene, "sls_config_selection", text=_("Preset"))
        layout.operator("simple_lip_sync.generate", text=_("Generate Lip Sync"), icon="SOUND")


class SIMPLE_LIP_SYNC_PT_tuning(bpy.types.Panel):
    """Advanced tuning panel."""

    bl_label = "Advanced"
    bl_idname = "SIMPLE_LIP_SYNC_PT_tuning"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simple Lip Sync"
    bl_parent_id = "SIMPLE_LIP_SYNC_PT_main"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "sls_use_custom_tuning")
        if not scene.sls_use_custom_tuning:
            layout.label(text=_("Using generation preset"), icon="INFO")
            return

        selected_entry = resolve_tuning_preset_entry(scene.sls_tuning_preset_selection)
        row = layout.row(align=True)
        row.prop(scene, "sls_tuning_preset_selection", text=_("Tuning Preset"))
        apply_row = row.row(align=True)
        apply_row.enabled = selected_entry is not None
        apply_row.operator("simple_lip_sync.apply_tuning_preset", text="", icon="FILE_TICK")
        delete_row = row.row(align=True)
        delete_row.enabled = selected_entry is not None
        delete_row.operator("simple_lip_sync.delete_tuning_preset", text="", icon="TRASH")

        layout.prop(scene, "sls_db_threshold")
        layout.prop(scene, "sls_rms_threshold")
        layout.prop(scene, "sls_buffer")
        layout.prop(scene, "sls_approach_speed")
        layout.prop(scene, "sls_max_morph_value")
        layout.prop(scene, "sls_anticipation_scale")
        layout.operator(
            "simple_lip_sync.create_tuning_preset",
            text=_("Save Tuning Preset"),
            icon="ADD",
        )


class SIMPLE_LIP_SYNC_PT_presets(bpy.types.Panel):
    """Preset management panel."""

    bl_label = "Presets"
    bl_idname = "SIMPLE_LIP_SYNC_PT_presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Simple Lip Sync"
    bl_parent_id = "SIMPLE_LIP_SYNC_PT_main"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        config_manager = get_config_manager()
        selected_entry = config_manager.resolve_config_entry(scene.sls_user_config_selection)

        row = layout.row(align=True)
        row.prop(scene, "sls_user_config_selection", text=_("User Preset"))
        delete_row = row.row(align=True)
        delete_row.enabled = selected_entry is not None and selected_entry["type"] == CONFIG_SOURCE_USER
        delete_row.operator(
            "simple_lip_sync.delete_preset",
            text="",
            icon="TRASH",
        )

        row = layout.row(align=True)
        row.operator("simple_lip_sync.autofill_mmd", text=_("MMD"), icon="PRESET")
        row.operator("simple_lip_sync.autofill_vrm", text=_("VRM"), icon="PRESET")
        row.operator("simple_lip_sync.autofill_selected", text=_("Selected"), icon="EYEDROPPER")

        grid = layout.grid_flow(columns=2, align=True)
        grid.prop(scene, "sls_shape_key_a", text="A")
        grid.prop(scene, "sls_shape_key_i", text="I")
        grid.prop(scene, "sls_shape_key_u", text="U")
        grid.prop(scene, "sls_shape_key_e", text="E")
        grid.prop(scene, "sls_shape_key_o", text="O")
        grid.prop(scene, "sls_shape_key_n", text="N")

        layout.operator("simple_lip_sync.create_preset", text=_("Create Preset"), icon="ADD")

        layout.separator()
        layout.operator("simple_lip_sync.import_preset", text=_("Import Preset"), icon="IMPORT")
        layout.operator("simple_lip_sync.export_preset", text=_("Export Selected Preset"), icon="EXPORT")
        layout.operator(
            "simple_lip_sync.open_config_folder",
            text=_("Open User Preset Folder"),
            icon="FILE_FOLDER",
        )


class SIMPLE_LIP_SYNC_OT_generate(bpy.types.Operator):
    """Generate lip sync keyframes."""

    bl_idname = "simple_lip_sync.generate"
    bl_label = "Generate Lip Sync"
    bl_description = "Generate lip sync keyframes for selected meshes"

    def execute(self, context):
        window = context.window
        context.window_manager.progress_begin(0, 100)
        if window:
            window.cursor_modal_set("WAIT")
        try:
            context.window_manager.progress_update(10)
            result = generate_lip_sync(context)
            context.window_manager.progress_update(100)
        except Exception as exc:
            context.window_manager.progress_end()
            if window:
                window.cursor_modal_restore()
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        context.window_manager.progress_end()
        if window:
            window.cursor_modal_restore()
        self.report(
            {"INFO"},
            _("Generated lip sync for {mesh_count} mesh object(s)").format(
                mesh_count=result["mesh_count"],
            ),
        )
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_create_preset(bpy.types.Operator):
    """Create a user lip sync preset."""

    bl_idname = "simple_lip_sync.create_preset"
    bl_label = "Create Lip Sync Preset"
    bl_description = "Create a user preset from the mapping fields"

    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        default="Custom Lip Sync",
        maxlen=128,
    )

    def invoke(self, context, _event):
        self.preset_name = context.scene.sls_create_config_name or "Custom Lip Sync"
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        self.layout.prop(self, "preset_name", text=_("Name"))

    def execute(self, context):
        scene = context.scene
        mapping = {
            "a": scene.sls_shape_key_a,
            "i": scene.sls_shape_key_i,
            "u": scene.sls_shape_key_u,
            "e": scene.sls_shape_key_e,
            "o": scene.sls_shape_key_o,
            "n": scene.sls_shape_key_n,
        }
        config = {
            "name": self.preset_name or "Custom Lip Sync",
            "description": "User-created Simple Lip Sync preset",
            "version": "1.0",
            "author": "User",
            "type": "lip_sync",
            "shape_keys": mapping,
            "adjustment_rules": DEFAULT_ADJUSTMENT_RULES,
        }
        try:
            entry = get_config_manager().save_config_from_display_name(self.preset_name, config)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        _refresh_preset_ui(context)
        if entry:
            scene.sls_config_selection = entry["id"]
            scene.sls_user_config_selection = entry["id"]
        scene.sls_create_config_name = self.preset_name
        _tag_ui_redraw(context)
        self.report({"INFO"}, _("Created lip sync preset"))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_delete_preset(bpy.types.Operator):
    """Delete the selected user lip sync preset."""

    bl_idname = "simple_lip_sync.delete_preset"
    bl_label = "Delete Lip Sync Preset"
    bl_description = "Delete the selected user preset"

    def invoke(self, context, event):
        entry = get_config_manager().resolve_config_entry(context.scene.sls_user_config_selection)
        if entry is None:
            self.report({"ERROR"}, _("Please select a user preset"))
            return {"CANCELLED"}
        if entry["type"] != CONFIG_SOURCE_USER:
            self.report({"ERROR"}, _("Only user presets can be deleted"))
            return {"CANCELLED"}
        return context.window_manager.invoke_confirm(
            self,
            event,
            title=_("Delete Lip Sync Preset"),
            message=_("Delete the selected user preset?"),
            confirm_text=_("Delete"),
            icon="ERROR",
        )

    def execute(self, context):
        scene = context.scene
        deleted_selection = scene.sls_user_config_selection
        active_generation_selection = scene.sls_config_selection
        try:
            deleted_entry = get_config_manager().delete_config(deleted_selection)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        _refresh_preset_ui(context)
        all_entries = get_config_manager().get_config_entries()
        user_entries = [
            entry for entry in all_entries
            if entry["type"] == CONFIG_SOURCE_USER
        ]
        scene.sls_user_config_selection = (
            user_entries[0]["id"] if user_entries else NO_USER_LIP_SYNC_CONFIG_ID
        )
        if active_generation_selection == deleted_entry["id"]:
            scene.sls_config_selection = (
                all_entries[0]["id"] if all_entries else NO_LIP_SYNC_CONFIG_ID
            )
        _tag_ui_redraw(context)
        self.report(
            {"INFO"},
            _("Deleted preset: {name}").format(name=deleted_entry["name"]),
        )
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_create_tuning_preset(bpy.types.Operator):
    """Create a user tuning preset."""

    bl_idname = "simple_lip_sync.create_tuning_preset"
    bl_label = "Save Tuning Preset"
    bl_description = "Save current advanced tuning values as a reusable preset"

    preset_name: bpy.props.StringProperty(
        name="Tuning Preset Name",
        default="Custom Tuning",
        maxlen=128,
    )

    def invoke(self, context, _event):
        self.preset_name = context.scene.sls_create_tuning_preset_name or "Custom Tuning"
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context):
        self.layout.prop(self, "preset_name", text=_("Name"))

    def execute(self, context):
        scene = context.scene
        try:
            entry = get_tuning_preset_manager().save_preset_from_display_name(
                self.preset_name,
                _current_tuning_values(scene),
            )
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        _refresh_tuning_preset_ui(context)
        if entry:
            scene.sls_tuning_preset_selection = entry["id"]
        scene.sls_create_tuning_preset_name = self.preset_name
        _tag_ui_redraw(context)
        self.report({"INFO"}, _("Saved tuning preset"))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_apply_tuning_preset(bpy.types.Operator):
    """Apply the selected user tuning preset."""

    bl_idname = "simple_lip_sync.apply_tuning_preset"
    bl_label = "Apply Tuning Preset"
    bl_description = "Apply the selected tuning preset to the advanced values"

    def execute(self, context):
        scene = context.scene
        try:
            preset = get_tuning_preset_manager().load_preset(scene.sls_tuning_preset_selection)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        if preset is None:
            self.report({"ERROR"}, _("Please select a tuning preset"))
            return {"CANCELLED"}

        _set_tuning_values(scene, preset["values"])
        scene.sls_use_custom_tuning = True
        _tag_ui_redraw(context)
        self.report({"INFO"}, _("Applied tuning preset: {name}").format(name=preset["name"]))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_delete_tuning_preset(bpy.types.Operator):
    """Delete the selected user tuning preset."""

    bl_idname = "simple_lip_sync.delete_tuning_preset"
    bl_label = "Delete Tuning Preset"
    bl_description = "Delete the selected tuning preset"

    def invoke(self, context, event):
        entry = resolve_tuning_preset_entry(context.scene.sls_tuning_preset_selection)
        if entry is None:
            self.report({"ERROR"}, _("Please select a tuning preset"))
            return {"CANCELLED"}
        return context.window_manager.invoke_confirm(
            self,
            event,
            title=_("Delete Tuning Preset"),
            message=_("Delete the selected tuning preset?"),
            confirm_text=_("Delete"),
            icon="ERROR",
        )

    def execute(self, context):
        scene = context.scene
        try:
            deleted_entry = get_tuning_preset_manager().delete_preset(
                scene.sls_tuning_preset_selection
            )
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        _refresh_tuning_preset_ui(context)
        entries = get_user_tuning_preset_entries()
        scene.sls_tuning_preset_selection = (
            entries[0]["id"] if entries else NO_USER_TUNING_PRESET_ID
        )
        _tag_ui_redraw(context)
        self.report(
            {"INFO"},
            _("Deleted tuning preset: {name}").format(name=deleted_entry["display_name"]),
        )
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_import_preset(bpy.types.Operator, ImportHelper):
    """Import a lip sync preset."""

    bl_idname = "simple_lip_sync.import_preset"
    bl_label = "Import Lip Sync Preset"
    bl_description = "Import a JSON lip sync preset into the user preset directory"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
    )

    def execute(self, context):
        scene = context.scene
        if not self.filepath:
            self.report({"ERROR"}, _("Please select a preset file to import"))
            return {"CANCELLED"}

        try:
            source_path = bpy.path.abspath(self.filepath)
            entry = get_config_manager().import_config(source_path)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        _refresh_preset_ui(context)
        if entry:
            scene.sls_config_selection = entry["id"]
            scene.sls_user_config_selection = entry["id"]
        _tag_ui_redraw(context)
        self.report({"INFO"}, _("Imported lip sync preset"))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_export_preset(bpy.types.Operator, ExportHelper):
    """Export the selected lip sync preset."""

    bl_idname = "simple_lip_sync.export_preset"
    bl_label = "Export Lip Sync Preset"
    bl_description = "Export the selected JSON preset"

    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={"HIDDEN"},
    )

    def invoke(self, context, event):
        selected_entry = get_config_manager().resolve_config_entry(
            context.scene.sls_user_config_selection
        )
        if selected_entry is None or selected_entry["type"] != CONFIG_SOURCE_USER:
            self.report({"ERROR"}, _("Please select a user preset"))
            return {"CANCELLED"}

        config = get_config_manager().load_config(selected_entry["id"])
        if config:
            self.filepath = _ensure_json_suffix(config["name"])
        return super().invoke(context, event)

    def execute(self, context):
        selected_entry = get_config_manager().resolve_config_entry(
            context.scene.sls_user_config_selection
        )
        if selected_entry is None or selected_entry["type"] != CONFIG_SOURCE_USER:
            self.report({"ERROR"}, _("Please select a user preset"))
            return {"CANCELLED"}
        if not self.filepath:
            self.report({"ERROR"}, _("Please choose an export path"))
            return {"CANCELLED"}

        try:
            target_path = bpy.path.abspath(self.filepath)
            exported_path = get_config_manager().export_config(
                selected_entry["id"],
                target_path,
            )
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, _("Exported preset: {path}").format(path=exported_path))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_open_config_folder(bpy.types.Operator):
    """Open the user preset folder."""

    bl_idname = "simple_lip_sync.open_config_folder"
    bl_label = "Open Lip Sync Preset Folder"
    bl_description = "Open the user preset folder"

    def execute(self, _context):
        config_dir = get_config_manager().user_config_path
        os.makedirs(config_dir, exist_ok=True)
        try:
            _open_path_non_blocking(config_dir)
        except OSError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, _("Opened preset folder: {path}").format(path=config_dir))
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_autofill_mmd(bpy.types.Operator):
    """Fill mapping fields with MMD names."""

    bl_idname = "simple_lip_sync.autofill_mmd"
    bl_label = "Use MMD Mapping"

    def execute(self, context):
        _set_mapping(context.scene, MMD_DEFAULT_MAPPING)
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_autofill_vrm(bpy.types.Operator):
    """Fill mapping fields with VRM names."""

    bl_idname = "simple_lip_sync.autofill_vrm"
    bl_label = "Use VRM Mapping"

    def execute(self, context):
        _set_mapping(context.scene, VRM_DEFAULT_MAPPING)
        return {"FINISHED"}


class SIMPLE_LIP_SYNC_OT_autofill_selected(bpy.types.Operator):
    """Fill mapping fields from selected mesh shape keys."""

    bl_idname = "simple_lip_sync.autofill_selected"
    bl_label = "Use Selected Shape Keys"

    def execute(self, context):
        names = _selected_shape_key_names(context)
        mapping = {}
        for key, candidates in {
            "a": ("あ", "A", "a"),
            "i": ("い", "I", "i"),
            "u": ("う", "U", "u"),
            "e": ("え", "E", "e"),
            "o": ("お", "O", "o"),
            "n": ("ん", "N", "n"),
        }.items():
            mapping[key] = next((candidate for candidate in candidates if candidate in names), candidates[0])
        _set_mapping(context.scene, mapping)
        return {"FINISHED"}


def _selected_shape_key_names(context):
    names = set()
    for obj in context.selected_objects:
        if obj.type == "MESH" and obj.data.shape_keys:
            names.update(key.name for key in obj.data.shape_keys.key_blocks)
    return names


def _set_mapping(scene, mapping):
    scene.sls_shape_key_a = mapping["a"]
    scene.sls_shape_key_i = mapping["i"]
    scene.sls_shape_key_u = mapping["u"]
    scene.sls_shape_key_e = mapping["e"]
    scene.sls_shape_key_o = mapping["o"]
    scene.sls_shape_key_n = mapping["n"]


def _current_tuning_values(scene):
    return {
        "buffer": scene.sls_buffer,
        "approach_speed": scene.sls_approach_speed,
        "db_threshold": scene.sls_db_threshold,
        "rms_threshold": scene.sls_rms_threshold,
        "max_morph_value": scene.sls_max_morph_value,
        "anticipation_scale": scene.sls_anticipation_scale,
    }


def _set_tuning_values(scene, values):
    scene.sls_buffer = values["buffer"]
    scene.sls_approach_speed = values["approach_speed"]
    scene.sls_db_threshold = values["db_threshold"]
    scene.sls_rms_threshold = values["rms_threshold"]
    scene.sls_max_morph_value = values["max_morph_value"]
    scene.sls_anticipation_scale = values["anticipation_scale"]


def _ensure_json_suffix(file_name):
    return file_name if file_name.endswith(".json") else f"{file_name}.json"


def _refresh_preset_ui(context):
    get_lip_sync_config_items(None, context)
    get_user_lip_sync_config_items(None, context)


def _refresh_tuning_preset_ui(context):
    get_user_tuning_preset_items(None, context)


def _tag_ui_redraw(context):
    if context.area is not None:
        context.area.tag_redraw()
    screen = getattr(context, "screen", None)
    if screen is None:
        return
    for area in screen.areas:
        area.tag_redraw()


def _open_path_non_blocking(path):
    if os.name == "nt":
        startfile = getattr(os, "startfile", None)
        if not callable(startfile):
            raise OSError("os.startfile is unavailable")
        startfile(path)
        return

    command = ["open", path] if sys.platform == "darwin" else ["xdg-open", path]
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


CLASSES = (
    SIMPLE_LIP_SYNC_PT_main,
    SIMPLE_LIP_SYNC_PT_presets,
    SIMPLE_LIP_SYNC_PT_tuning,
    SIMPLE_LIP_SYNC_OT_generate,
    SIMPLE_LIP_SYNC_OT_create_preset,
    SIMPLE_LIP_SYNC_OT_delete_preset,
    SIMPLE_LIP_SYNC_OT_create_tuning_preset,
    SIMPLE_LIP_SYNC_OT_apply_tuning_preset,
    SIMPLE_LIP_SYNC_OT_delete_tuning_preset,
    SIMPLE_LIP_SYNC_OT_import_preset,
    SIMPLE_LIP_SYNC_OT_export_preset,
    SIMPLE_LIP_SYNC_OT_open_config_folder,
    SIMPLE_LIP_SYNC_OT_autofill_mmd,
    SIMPLE_LIP_SYNC_OT_autofill_vrm,
    SIMPLE_LIP_SYNC_OT_autofill_selected,
)

SCENE_PROPS = (
    "sls_audio_source",
    "sls_timeline_audio_strip",
    "sls_audio_path",
    "sls_start_frame",
    "sls_generation_preset",
    "sls_use_custom_tuning",
    "sls_tuning_preset_selection",
    "sls_buffer",
    "sls_approach_speed",
    "sls_db_threshold",
    "sls_rms_threshold",
    "sls_max_morph_value",
    "sls_anticipation_scale",
    "sls_config_selection",
    "sls_user_config_selection",
    "sls_create_config_name",
    "sls_create_tuning_preset_name",
    "sls_shape_key_a",
    "sls_shape_key_i",
    "sls_shape_key_u",
    "sls_shape_key_e",
    "sls_shape_key_o",
    "sls_shape_key_n",
)


def register():
    """Register UI classes and scene properties."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    register_scene_properties()


def unregister():
    """Unregister UI classes and scene properties."""
    for prop_name in reversed(SCENE_PROPS):
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


def register_scene_properties():
    """Register Scene properties used by the add-on."""
    defaults = get_lip_sync_preset_values(DEFAULT_LIP_SYNC_PRESET)

    bpy.types.Scene.sls_audio_source = bpy.props.EnumProperty(
        name="Audio Source",
        description="Where to get the audio for lip sync generation",
        items=(
            ("file", "File", "Use an audio file from disk"),
            ("timeline", "Timeline", "Use audio from the Video Sequence Editor timeline"),
        ),
        default="file",
    )
    bpy.types.Scene.sls_timeline_audio_strip = bpy.props.EnumProperty(
        name="Audio Strip",
        description="Select an audio strip from the timeline",
        items=get_timeline_audio_items,
    )
    bpy.types.Scene.sls_audio_path = bpy.props.StringProperty(
        name="Audio Path",
        description="Path to an audio file",
        default="",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    bpy.types.Scene.sls_start_frame = bpy.props.IntProperty(
        name="Start Frame",
        default=1,
        min=1,
    )
    bpy.types.Scene.sls_generation_preset = bpy.props.EnumProperty(
        name="Motion",
        description="Choose the overall lip sync motion style",
        items=(
            ("natural", "Natural", "Smooth and balanced motion for most dialogue"),
            ("clear", "Clear Speech", "Sharper mouth motion for clearer articulation"),
            ("soft", "Soft Motion", "Smaller and softer mouth motion"),
        ),
        default=DEFAULT_LIP_SYNC_PRESET,
    )
    bpy.types.Scene.sls_use_custom_tuning = bpy.props.BoolProperty(
        name="Custom Tuning",
        description="Use manual tuning instead of the selected motion preset",
        default=False,
    )
    bpy.types.Scene.sls_tuning_preset_selection = bpy.props.EnumProperty(
        name="Tuning Preset",
        description="Select a saved tuning preset to apply or delete",
        items=get_user_tuning_preset_items,
    )
    bpy.types.Scene.sls_buffer = bpy.props.FloatProperty(
        name="Delayed Opening",
        default=defaults["buffer"],
        min=0.0,
        max=1.0,
    )
    bpy.types.Scene.sls_approach_speed = bpy.props.FloatProperty(
        name="Opening Speed",
        default=defaults["approach_speed"],
        min=0.1,
        max=10.0,
    )
    bpy.types.Scene.sls_db_threshold = bpy.props.FloatProperty(
        name="DB Threshold",
        default=defaults["db_threshold"],
        min=-80.0,
        max=0.0,
    )
    bpy.types.Scene.sls_rms_threshold = bpy.props.FloatProperty(
        name="RMS Threshold",
        default=defaults["rms_threshold"],
        min=0.0001,
        max=1.0,
    )
    bpy.types.Scene.sls_max_morph_value = bpy.props.FloatProperty(
        name="Max Morph Value",
        default=defaults["max_morph_value"],
        min=0.01,
        max=1.0,
    )
    bpy.types.Scene.sls_anticipation_scale = bpy.props.FloatProperty(
        name="Anticipation",
        default=defaults["anticipation_scale"],
        min=0.2,
        max=1.5,
    )
    bpy.types.Scene.sls_config_selection = bpy.props.EnumProperty(
        name="Lip Sync Preset",
        description="Select the shape-key mapping preset",
        items=get_lip_sync_config_items,
    )
    bpy.types.Scene.sls_user_config_selection = bpy.props.EnumProperty(
        name="User Preset",
        description="Select a user preset to manage",
        items=get_user_lip_sync_config_items,
    )
    bpy.types.Scene.sls_create_config_name = bpy.props.StringProperty(
        name="Preset Name",
        default="Custom Lip Sync",
        maxlen=128,
    )
    bpy.types.Scene.sls_create_tuning_preset_name = bpy.props.StringProperty(
        name="Tuning Preset Name",
        default="Custom Tuning",
        maxlen=128,
    )
    bpy.types.Scene.sls_shape_key_a = bpy.props.StringProperty(name="A", default="あ")
    bpy.types.Scene.sls_shape_key_i = bpy.props.StringProperty(name="I", default="い")
    bpy.types.Scene.sls_shape_key_u = bpy.props.StringProperty(name="U", default="う")
    bpy.types.Scene.sls_shape_key_e = bpy.props.StringProperty(name="E", default="え")
    bpy.types.Scene.sls_shape_key_o = bpy.props.StringProperty(name="O", default="お")
    bpy.types.Scene.sls_shape_key_n = bpy.props.StringProperty(name="N", default="ん")
