"""Built-in and user preset management."""

import json
import os
import re

from .schema import ConfigValidationError, validate_lip_sync_config

CONFIG_SOURCE_PREDEFINED = "predefined"
CONFIG_SOURCE_USER = "user"
USER_CONFIG_DIR_NAME = "simple_lip_sync"


class ConfigManager:
    """Load, save, import, and export lip sync presets."""

    def __init__(self, addon_dir, user_scripts_dir=None, translate_func=None):
        self.addon_dir = addon_dir
        self.config_base_path = os.path.join(addon_dir, "configs", "lip_sync")
        self.user_config_path = self._ensure_user_config_root(user_scripts_dir)
        self._translate = translate_func or (lambda text: text)

    def get_config_entries(self):
        """Return all valid built-in and user preset entries."""
        entries = []
        for source, config_dir in (
            (CONFIG_SOURCE_PREDEFINED, self.config_base_path),
            (CONFIG_SOURCE_USER, self.user_config_path),
        ):
            if not os.path.isdir(config_dir):
                continue
            for file_name in sorted(os.listdir(config_dir)):
                if not file_name.endswith(".json"):
                    continue
                config_path = os.path.join(config_dir, file_name)
                config_data = self._load_config_from_path(config_path)
                if config_data is None:
                    continue
                entries.append({
                    "id": self._build_config_id(source, file_name),
                    "name": file_name,
                    "path": config_path,
                    "type": source,
                    "display_name": self._build_display_name(config_data, source),
                    "description": self._build_description(config_data, source),
                })
        return entries

    def resolve_config_entry(self, selection):
        """Resolve an enum selection or legacy file name to a config entry."""
        if not selection:
            return None

        entries = self.get_config_entries()
        for entry in entries:
            if entry["id"] == selection:
                return entry

        if ":" not in selection:
            for source in (CONFIG_SOURCE_USER, CONFIG_SOURCE_PREDEFINED):
                for entry in entries:
                    if entry["type"] == source and entry["name"] == selection:
                        return entry
        return None

    def load_config(self, selection):
        """Load a selected preset."""
        entry = self.resolve_config_entry(selection)
        if entry is None:
            return None
        return self._load_config_from_path(entry["path"])

    def save_config(self, config_file, config_data):
        """Save a preset to the user preset directory and return its entry."""
        normalized_config = validate_lip_sync_config(config_data)
        self._ensure_unique_user_preset_name(normalized_config["name"])
        config_name = self._allocate_user_config_name(
            self.user_config_path,
            self._ensure_json_suffix(config_file),
        )
        config_path = os.path.join(self.user_config_path, config_name)
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(normalized_config, file, indent=2, ensure_ascii=False)
        return self.resolve_config_entry(self._build_config_id(CONFIG_SOURCE_USER, config_name))

    def save_config_from_display_name(self, display_name, config_data):
        """Save a preset using a user-facing preset name."""
        preset_name = display_name.strip()
        if not preset_name:
            raise ValueError(self._translate("Preset name is empty"))
        config_data = dict(config_data)
        config_data["name"] = preset_name
        return self.save_config(self._slugify_file_name(preset_name), config_data)

    def import_config(self, source_path, config_name=None):
        """Import a JSON preset into the user preset directory."""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        with open(source_path, "r", encoding="utf-8") as file:
            normalized_config = validate_lip_sync_config(json.load(file))
        self._ensure_unique_user_preset_name(normalized_config["name"])

        desired_name = config_name or os.path.splitext(os.path.basename(source_path))[0]
        target_name = self._allocate_user_config_name(
            self.user_config_path,
            self._ensure_json_suffix(desired_name),
        )
        target_path = os.path.join(self.user_config_path, target_name)
        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(normalized_config, file, indent=2, ensure_ascii=False)
        return self.resolve_config_entry(self._build_config_id(CONFIG_SOURCE_USER, target_name))

    def export_config(self, selection, target_path):
        """Export a selected preset to a JSON file path."""
        config = self.load_config(selection)
        if config is None:
            raise ValueError(f"Preset not found: {selection}")
        if not target_path:
            raise ValueError("Export path is empty")
        target_path = self._ensure_json_suffix(target_path)
        target_dir = os.path.dirname(os.path.abspath(target_path))
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=2, ensure_ascii=False)
        return target_path

    def delete_config(self, selection):
        """Delete a selected user preset and return the deleted entry."""
        entry = self.resolve_config_entry(selection)
        if entry is None:
            raise ValueError(f"Preset not found: {selection}")
        if entry["type"] != CONFIG_SOURCE_USER:
            raise ValueError(self._translate("Only user presets can be deleted"))
        os.remove(entry["path"])
        return entry

    @staticmethod
    def _load_config_from_path(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                return validate_lip_sync_config(json.load(file))
        except (OSError, json.JSONDecodeError, ConfigValidationError):
            return None

    @staticmethod
    def _build_config_id(source, file_name):
        return f"{source}:{file_name}"

    def _build_display_name(self, config_data, source):
        source_label = self._translate(
            "Built-in" if source == CONFIG_SOURCE_PREDEFINED else "User"
        )
        return f"{config_data['name']} [{source_label}]"

    def _build_description(self, config_data, source):
        source_label = self._translate(
            "Built-in" if source == CONFIG_SOURCE_PREDEFINED else "User"
        )
        return f"{config_data['name']} ({source_label})"

    def _ensure_unique_user_preset_name(self, preset_name):
        normalized_name = self._normalize_preset_name(preset_name)
        for entry in self.get_config_entries():
            if entry["type"] != CONFIG_SOURCE_USER:
                continue
            config = self._load_config_from_path(entry["path"])
            if config and self._normalize_preset_name(config["name"]) == normalized_name:
                raise ValueError(
                    self._translate("A user preset named '{name}' already exists").format(
                        name=preset_name,
                    )
                )

    @staticmethod
    def _ensure_json_suffix(file_name):
        if file_name.endswith(".json"):
            return file_name
        return f"{file_name}.json"

    @staticmethod
    def _slugify_file_name(display_name):
        normalized = display_name.strip().lower()
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"[^0-9a-zA-Z_.-]+", "_", normalized)
        normalized = normalized.strip("._-")
        return normalized or "custom_lip_sync"

    @staticmethod
    def _normalize_preset_name(preset_name):
        return preset_name.strip()

    @staticmethod
    def _allocate_user_config_name(target_dir, desired_name):
        base_name, extension = os.path.splitext(desired_name)
        candidate = desired_name
        index = 1
        while os.path.exists(os.path.join(target_dir, candidate)):
            candidate = f"{base_name}_{index}{extension}"
            index += 1
        return candidate

    def _ensure_user_config_root(self, user_scripts_dir):
        if user_scripts_dir is None:
            user_scripts_dir = os.path.join(os.path.expanduser("~"), ".config", "blender")
        user_config_dir = os.path.join(
            user_scripts_dir,
            "presets",
            USER_CONFIG_DIR_NAME,
            "lip_sync",
        )
        os.makedirs(user_config_dir, exist_ok=True)
        return user_config_dir
