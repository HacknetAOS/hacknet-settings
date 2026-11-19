"""Unit tests for compositor keybind & input config persistence."""

import os
import tempfile
import unittest

from hacknet_settings.compositor_cfg import (
    format_hypr_binds,
    format_hypr_input,
    format_sway_binds,
    format_sway_input,
    load_input_config,
    load_keybinds,
    save_and_apply_input,
    save_and_apply_keybinds,
)


class TestCompositorCfg(unittest.TestCase):
    def test_keybinds_formatting_and_roundtrip(self):
        binds = [
            {"mods": ["Super", "Alt"], "key": "t", "label": "Theme", "command": "hacknet-theme apply ente"},
            {"mods": ["Super", "Ctrl"], "key": "g", "label": "Gutter", "command": "hacknetctl toggle-gutter"},
        ]
        sway = format_sway_binds(binds)
        self.assertIn("bindsym $mod+Mod1+t exec hacknet-theme apply ente", sway)
        self.assertIn("bindsym $mod+Control+g exec hacknetctl toggle-gutter", sway)

        hypr = format_hypr_binds(binds)
        self.assertIn('hl.bind("SUPER + ALT + t", hl.dsp.exec_cmd("hacknet-theme apply ente"))', hypr)
        self.assertIn('hl.bind("SUPER + CTRL + g", hl.dsp.exec_cmd("hacknetctl toggle-gutter"))', hypr)

        with tempfile.TemporaryDirectory() as tmp:
            jpath = os.path.join(tmp, "keybinds.json")
            spath = os.path.join(tmp, "sway.conf")
            hpath = os.path.join(tmp, "hypr.lua")
            save_and_apply_keybinds(binds, json_path=jpath, sway_path=spath, hypr_path=hpath, reload=False)
            self.assertEqual(load_keybinds(jpath), binds)

    def test_input_formatting_and_roundtrip(self):
        cfg = {"layout": "de", "repeat_rate": 40, "repeat_delay": 250, "natural_scroll": True}
        sway = format_sway_input(cfg)
        self.assertIn("xkb_layout de", sway)
        self.assertIn("repeat_rate 40", sway)
        self.assertIn("natural_scroll enabled", sway)

        hypr = format_hypr_input(cfg)
        self.assertIn('kb_layout = "de"', hypr)
        self.assertIn("natural_scroll = true", hypr)

        with tempfile.TemporaryDirectory() as tmp:
            jpath = os.path.join(tmp, "input.json")
            spath = os.path.join(tmp, "input.conf")
            hpath = os.path.join(tmp, "input.lua")
            save_and_apply_input(cfg, json_path=jpath, sway_path=spath, hypr_path=hpath, reload=False)
            self.assertEqual(load_input_config(jpath), cfg)


if __name__ == "__main__":
    unittest.main()
