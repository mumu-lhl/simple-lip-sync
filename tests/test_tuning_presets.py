"""Tests for user tuning preset management."""

import os
import tempfile
import unittest

from simple_lip_sync.core.tuning_presets import (
    TuningPresetError,
    TuningPresetManager,
    validate_tuning_preset,
)


VALID_VALUES = {
    "buffer": 0.26,
    "approach_speed": 1.7,
    "db_threshold": -45.0,
    "rms_threshold": 0.045,
    "max_morph_value": 0.82,
    "anticipation_scale": 0.65,
}


class TuningPresetTests(unittest.TestCase):
    """Tuning preset tests."""

    def test_user_tuning_presets_are_stored_in_blender_presets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TuningPresetManager(temp_dir)

            expected = os.path.join(
                temp_dir,
                "presets",
                "simple_lip_sync",
                "tuning",
            )
            self.assertEqual(manager.user_preset_path, expected)

    def test_save_load_and_delete_tuning_preset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TuningPresetManager(temp_dir)
            entry = manager.save_preset_from_display_name("Slow Talk", VALID_VALUES)

            self.assertIsNotNone(entry)
            self.assertEqual(entry["name"], "slow_talk.json")
            self.assertTrue(os.path.exists(entry["path"]))

            preset = manager.load_preset(entry["id"])
            self.assertEqual(preset["name"], "Slow Talk")
            self.assertEqual(preset["values"], VALID_VALUES)

            deleted = manager.delete_preset(entry["id"])
            self.assertEqual(deleted["id"], entry["id"])
            self.assertFalse(os.path.exists(entry["path"]))

    def test_save_tuning_preset_rejects_duplicate_display_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TuningPresetManager(temp_dir)
            manager.save_preset_from_display_name("Slow Talk", VALID_VALUES)

            with self.assertRaises(ValueError):
                manager.save_preset_from_display_name("Slow Talk", VALID_VALUES)

    def test_validate_tuning_preset_rejects_missing_values(self):
        preset = {
            "name": "Incomplete",
            "description": "Missing values",
            "version": "1.0",
            "type": "tuning",
            "values": {"buffer": 0.2},
        }
        with self.assertRaises(TuningPresetError):
            validate_tuning_preset(preset)

    def test_validate_tuning_preset_rejects_out_of_range_values(self):
        preset = {
            "name": "Invalid",
            "description": "Out of range",
            "version": "1.0",
            "type": "tuning",
            "values": dict(VALID_VALUES, approach_speed=20.0),
        }
        with self.assertRaises(TuningPresetError):
            validate_tuning_preset(preset)


if __name__ == "__main__":
    unittest.main()
