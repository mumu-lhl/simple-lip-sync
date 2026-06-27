"""User tuning preset management."""

import json
import os
import re

from .profiles import LIP_SYNC_PRESETS

TUNING_PRESET_TYPE = "tuning"
TUNING_PRESET_FIELDS = (
    "buffer",
    "approach_speed",
    "db_threshold",
    "rms_threshold",
    "max_morph_value",
    "anticipation_scale",
)
TUNING_PRESET_LIMITS = {
    "buffer": (0.0, 1.0),
    "approach_speed": (0.1, 10.0),
    "db_threshold": (-80.0, 0.0),
    "rms_threshold": (0.0001, 1.0),
    "max_morph_value": (0.01, 1.0),
    "anticipation_scale": (0.2, 1.5),
}
USER_TUNING_DIR_NAME = "simple_lip_sync"


class TuningPresetError(ValueError):
    """Raised when a tuning preset is invalid."""


class TuningPresetManager:
    """Load, save, and delete user tuning presets."""

    def __init__(self, user_scripts_dir=None, translate_func=None):
        self.user_preset_path = self._ensure_user_preset_root(user_scripts_dir)
        self._translate = translate_func or (lambda text: text)

    def get_preset_entries(self):
        """Return valid user tuning preset entries."""
        if not os.path.isdir(self.user_preset_path):
            return []

        entries = []
        for file_name in sorted(os.listdir(self.user_preset_path)):
            if not file_name.endswith(".json"):
                continue
            preset_path = os.path.join(self.user_preset_path, file_name)
            preset = self._load_preset_from_path(preset_path)
            if preset is None:
                continue
            entries.append({
                "id": self._build_preset_id(file_name),
                "name": file_name,
                "path": preset_path,
                "display_name": preset["name"],
                "description": preset.get("description", preset["name"]),
            })
        return entries

    def resolve_preset_entry(self, selection):
        """Resolve an enum selection to a user tuning preset entry."""
        if not selection:
            return None

        entries = self.get_preset_entries()
        for entry in entries:
            if entry["id"] == selection:
                return entry

        if ":" not in selection:
            for entry in entries:
                if entry["name"] == selection:
                    return entry
        return None

    def load_preset(self, selection):
        """Load a selected tuning preset."""
        entry = self.resolve_preset_entry(selection)
        if entry is None:
            return None
        return self._load_preset_from_path(entry["path"])

    def save_preset_from_display_name(self, display_name, values):
        """Save current tuning values under a user-facing name."""
        preset_name = display_name.strip()
        if not preset_name:
            raise ValueError(self._translate("Tuning preset name is empty"))

        self._ensure_unique_user_preset_name(preset_name)
        preset = validate_tuning_preset({
            "name": preset_name,
            "description": "User-created Simple Lip Sync tuning preset",
            "version": "1.0",
            "type": TUNING_PRESET_TYPE,
            "values": values,
        })
        file_name = self._allocate_user_preset_name(
            self.user_preset_path,
            self._ensure_json_suffix(self._slugify_file_name(preset_name)),
        )
        preset_path = os.path.join(self.user_preset_path, file_name)
        with open(preset_path, "w", encoding="utf-8") as file:
            json.dump(preset, file, indent=2, ensure_ascii=False)
        return self.resolve_preset_entry(self._build_preset_id(file_name))

    def delete_preset(self, selection):
        """Delete a selected user tuning preset and return the deleted entry."""
        entry = self.resolve_preset_entry(selection)
        if entry is None:
            raise ValueError(self._translate("Tuning preset not found"))
        os.remove(entry["path"])
        return entry

    @staticmethod
    def _load_preset_from_path(preset_path):
        try:
            with open(preset_path, "r", encoding="utf-8") as file:
                return validate_tuning_preset(json.load(file))
        except (OSError, json.JSONDecodeError, TuningPresetError):
            return None

    @staticmethod
    def _build_preset_id(file_name):
        return f"user:{file_name}"

    def _ensure_unique_user_preset_name(self, preset_name):
        normalized_name = self._normalize_preset_name(preset_name)
        for entry in self.get_preset_entries():
            preset = self._load_preset_from_path(entry["path"])
            if preset and self._normalize_preset_name(preset["name"]) == normalized_name:
                raise ValueError(
                    self._translate("A tuning preset named '{name}' already exists").format(
                        name=preset_name,
                    )
                )

    @staticmethod
    def _ensure_json_suffix(file_name):
        return file_name if file_name.endswith(".json") else f"{file_name}.json"

    @staticmethod
    def _slugify_file_name(display_name):
        normalized = display_name.strip().lower()
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"[^0-9a-zA-Z_.-]+", "_", normalized)
        normalized = normalized.strip("._-")
        return normalized or "custom_tuning"

    @staticmethod
    def _normalize_preset_name(preset_name):
        return preset_name.strip()

    @staticmethod
    def _allocate_user_preset_name(target_dir, desired_name):
        base_name, extension = os.path.splitext(desired_name)
        candidate = desired_name
        index = 1
        while os.path.exists(os.path.join(target_dir, candidate)):
            candidate = f"{base_name}_{index}{extension}"
            index += 1
        return candidate

    @staticmethod
    def _ensure_user_preset_root(user_scripts_dir):
        if user_scripts_dir is None:
            user_scripts_dir = os.path.join(os.path.expanduser("~"), ".config", "blender")
        user_preset_dir = os.path.join(
            user_scripts_dir,
            "presets",
            USER_TUNING_DIR_NAME,
            "tuning",
        )
        os.makedirs(user_preset_dir, exist_ok=True)
        return user_preset_dir


def validate_tuning_preset(preset_data):
    """Validate and normalize a tuning preset dictionary."""
    if not isinstance(preset_data, dict):
        raise TuningPresetError("Tuning preset must be a JSON object")

    allowed_fields = {"name", "description", "version", "type", "values"}
    unknown_fields = sorted(set(preset_data.keys()) - allowed_fields)
    if unknown_fields:
        raise TuningPresetError(
            f"Unknown fields in tuning preset: {', '.join(unknown_fields)}"
        )

    preset_type = preset_data.get("type")
    if preset_type is not None and preset_type != TUNING_PRESET_TYPE:
        raise TuningPresetError(
            f"Preset field 'type' must be '{TUNING_PRESET_TYPE}', got '{preset_type}'"
        )

    normalized = {
        "name": _require_non_empty_string(preset_data.get("name"), "name"),
        "description": _require_non_empty_string(
            preset_data.get("description", "Tuning preset"),
            "description",
        ),
        "version": _require_non_empty_string(preset_data.get("version", "1.0"), "version"),
        "type": TUNING_PRESET_TYPE,
        "values": normalize_tuning_values(preset_data.get("values")),
    }
    return normalized


def normalize_tuning_values(values):
    """Validate and normalize tuning values."""
    if not isinstance(values, dict):
        raise TuningPresetError("Field 'values' must be an object")

    normalized = {}
    for field_name in TUNING_PRESET_FIELDS:
        if field_name not in values:
            raise TuningPresetError(f"Missing tuning value: {field_name}")
        minimum, maximum = TUNING_PRESET_LIMITS[field_name]
        normalized[field_name] = _validate_number(
            values[field_name],
            f"values.{field_name}",
            minimum,
            maximum,
        )
    return normalized


def built_in_tuning_preset(name):
    """Return built-in generation tuning values for fallback use."""
    return dict(LIP_SYNC_PRESETS[name])


def _require_non_empty_string(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise TuningPresetError(f"Field '{field_name}' must be a non-empty string")
    return value.strip()


def _validate_number(value, field_name, minimum, maximum):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TuningPresetError(f"Field '{field_name}' must be a number")

    normalized = float(value)
    if normalized < minimum:
        raise TuningPresetError(f"Field '{field_name}' must be >= {minimum}")
    if normalized > maximum:
        raise TuningPresetError(f"Field '{field_name}' must be <= {maximum}")
    return normalized
