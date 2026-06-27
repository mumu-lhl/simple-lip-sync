"""Tests for preset validation and config management."""

import os
import json
import tempfile
import unittest

from simple_lip_sync.core.config_manager import ConfigManager
from simple_lip_sync.core.config_manager import CONFIG_SOURCE_PREDEFINED
from simple_lip_sync.core.schema import ConfigValidationError, validate_lip_sync_config


VALID_CONFIG = {
    "name": "Test",
    "description": "Test preset",
    "version": "1.0",
    "type": "lip_sync",
    "shape_keys": {
        "a": "あ",
        "i": "い",
        "u": "う",
        "e": "え",
        "o": "お",
        "n": "ん",
    },
}


class ConfigManagerTests(unittest.TestCase):
    """Preset tests."""

    def test_validate_accepts_aliases(self):
        config = dict(VALID_CONFIG)
        config["shape_keys"] = {
            "あ": "A",
            "い": "I",
            "う": "U",
            "え": "E",
            "お": "O",
            "ん": "N",
        }
        normalized = validate_lip_sync_config(config)
        self.assertEqual(normalized["shape_keys"]["a"], "A")
        self.assertEqual(normalized["shape_keys"]["n"], "N")

    def test_validate_requires_all_shape_keys(self):
        config = dict(VALID_CONFIG)
        config["shape_keys"] = {"a": "あ"}
        with self.assertRaises(ConfigValidationError):
            validate_lip_sync_config(config)

    def test_save_and_export_user_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)
            entry = manager.save_config("test.json", VALID_CONFIG)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["type"], "user")

            export_path = os.path.join(temp_dir, "exported.json")
            manager.export_config(entry["id"], export_path)
            self.assertTrue(os.path.exists(export_path))

    def test_user_configs_are_stored_in_blender_presets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)

            expected = os.path.join(
                temp_dir,
                "presets",
                "simple_lip_sync",
                "lip_sync",
            )
            self.assertEqual(manager.user_config_path, expected)

    def test_save_from_display_name_slugifies_file_and_can_delete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)

            entry = manager.save_config_from_display_name("My Preset", VALID_CONFIG)
            self.assertEqual(entry["name"], "my_preset.json")
            self.assertTrue(os.path.exists(entry["path"]))

            deleted = manager.delete_config(entry["id"])
            self.assertEqual(deleted["id"], entry["id"])
            self.assertFalse(os.path.exists(entry["path"]))

    def test_save_from_display_name_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)

            manager.save_config_from_display_name("My Preset", VALID_CONFIG)
            with self.assertRaises(ValueError):
                manager.save_config_from_display_name("My Preset", VALID_CONFIG)

    def test_import_rejects_duplicate_user_preset_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)
            manager.save_config_from_display_name("Imported Preset", VALID_CONFIG)

            import_path = os.path.join(temp_dir, "imported.json")
            config = dict(VALID_CONFIG)
            config["name"] = "Imported Preset"
            with open(import_path, "w", encoding="utf-8") as file:
                json.dump(config, file)

            with self.assertRaises(ValueError):
                manager.import_config(import_path)

    def test_delete_rejects_builtin_presets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(addon_dir, temp_dir)
            entry = next(
                item for item in manager.get_config_entries()
                if item["type"] == CONFIG_SOURCE_PREDEFINED
            )

            with self.assertRaises(ValueError):
                manager.delete_config(entry["id"])

    def test_source_labels_can_be_translated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            addon_dir = os.path.abspath("simple_lip_sync")
            manager = ConfigManager(
                addon_dir,
                temp_dir,
                translate_func=lambda text: {"Built-in": "内置", "User": "用户"}.get(text, text),
            )

            entries = manager.get_config_entries()
            built_in = [entry for entry in entries if entry["type"] == "predefined"]
            self.assertTrue(built_in)
            self.assertIn("[内置]", built_in[0]["display_name"])


if __name__ == "__main__":
    unittest.main()
