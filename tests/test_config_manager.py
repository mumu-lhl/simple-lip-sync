"""Tests for preset validation and config management."""

import os
import tempfile
import unittest

from simple_lip_sync.core.config_manager import ConfigManager
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


if __name__ == "__main__":
    unittest.main()

