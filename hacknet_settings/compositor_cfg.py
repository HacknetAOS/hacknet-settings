"""Persistent keybind and input configuration for Sway & Hyprland."""

import json
import os
from hacknet_settings.system_ctl import reload_compositor

CONFIG_DIR = os.path.expanduser("~/.config/hacknet")
KEYBINDS_JSON = os.path.join(CONFIG_DIR, "keybinds.json")
INPUT_JSON = os.path.join(CONFIG_DIR, "input.json")
SWAY_BINDS = os.path.expanduser("~/.config/sway/hacknet-user-binds.conf")
SWAY_INPUT = os.path.expanduser("~/.config/sway/hacknet-user-input.conf")
HYPR_BINDS = os.path.expanduser("~/.config/hypr/hacknet-user-binds.lua")
HYPR_INPUT = os.path.expanduser("~/.config/hypr/hacknet-user-input.lua")

KEYMAP_LAYOUTS = ["us", "gb", "de", "fr", "es", "it", "pt", "br", "jp", "se", "no", "dk"]

KEYBIND_PRESET_ACTIONS = [
    ("Toggle RAM Gutter", "hacknetctl toggle-gutter"),
    ("Toggle Console (Full / Bottom)", "hacknetctl toggle-terminal-bottom"),
    ("Apply Theme: Blue", "hacknet-theme apply blue"),
    ("Apply Theme: Ente", "hacknet-theme apply ente"),
    ("Apply Theme: Hellhound", "hacknet-theme apply hellhound"),
    ("Apply Theme: Naix", "hacknet-theme apply naix"),
    ("Apply Theme: Hacknet", "hacknet-theme apply hacknet"),
    ("New Virtual Desktop", "hacknetctl desktop-add"),
    ("Next Virtual Desktop", "hacknetctl desktop-switch-next"),
    ("Previous Virtual Desktop", "hacknetctl desktop-switch-prev"),
    ("Toggle Fullscreen", "hacknetctl fullscreen-toggle"),
    ("Open App Launcher", "hacknet-launcher"),
    ("Open HacknetOS Settings", "hacknet-settings"),
    ("Open File Manager", "thunar"),
    ("Open Dock Terminal", "hacknet-dock-term"),
    ("Lock Screen", "sh -c 'mkdir -p ~/.local/state/hacknet && touch ~/.local/state/hacknet/locked'"),
    ("Custom Command...", "__custom__"),
]

_SWAY_MOD_MAP = {"Super": "$mod", "Ctrl": "Control", "Alt": "Mod1", "Shift": "Shift"}


def load_keybinds(path=KEYBINDS_JSON):
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def format_sway_binds(binds):
    lines = ["# Managed by hacknet-settings"]
    for b in binds:
        mods = [_SWAY_MOD_MAP.get(m, m) for m in b.get("mods", [])]
        combo = "+".join(mods + [b["key"]])
        lines.append(f"bindsym {combo} exec {b['command']}")
    return "\n".join(lines) + "\n"


def format_hypr_binds(binds):
    lines = ["-- Managed by hacknet-settings", "local hl = require('hyprland')"]
    for b in binds:
        mods = [m.upper() for m in b.get("mods", [])]
        combo = " + ".join(mods + [b["key"]])
        cmd_escaped = b["command"].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'hl.bind("{combo}", hl.dsp.exec_cmd("{cmd_escaped}"))')
    return "\n".join(lines) + "\n"


def save_and_apply_keybinds(
    binds, json_path=KEYBINDS_JSON, sway_path=SWAY_BINDS, hypr_path=HYPR_BINDS, reload=True
):
    for p, content in (
        (json_path, json.dumps(binds, indent=2)),
        (sway_path, format_sway_binds(binds)),
        (hypr_path, format_hypr_binds(binds)),
    ):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
    if reload:
        reload_compositor()


def load_input_config(path=INPUT_JSON):
    cfg = {"layout": "us", "repeat_rate": 25, "repeat_delay": 300, "natural_scroll": False}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except Exception:
            pass
    return cfg


def format_sway_input(cfg):
    nat = "enabled" if cfg.get("natural_scroll") else "disabled"
    return (
        "# Managed by hacknet-settings\n"
        f"input type:keyboard {{\n"
        f"    xkb_layout {cfg['layout']}\n"
        f"    repeat_rate {int(cfg['repeat_rate'])}\n"
        f"    repeat_delay {int(cfg['repeat_delay'])}\n"
        f"}}\n"
        f"input type:pointer {{\n    natural_scroll {nat}\n}}\n"
        f"input type:touchpad {{\n    natural_scroll {nat}\n}}\n"
    )


def format_hypr_input(cfg):
    nat_lua = "true" if cfg.get("natural_scroll") else "false"
    return (
        "-- Managed by hacknet-settings\n"
        "local hl = require('hyprland')\n"
        "hl.config({\n  input = {\n"
        f'    kb_layout = "{cfg["layout"]}",\n'
        f'    repeat_rate = {int(cfg["repeat_rate"])},\n'
        f'    repeat_delay = {int(cfg["repeat_delay"])},\n'
        f"    touchpad = {{ natural_scroll = {nat_lua} }},\n"
        "  },\n})\n"
    )


def save_and_apply_input(
    cfg, json_path=INPUT_JSON, sway_path=SWAY_INPUT, hypr_path=HYPR_INPUT, reload=True
):
    for p, content in (
        (json_path, json.dumps(cfg, indent=2)),
        (sway_path, format_sway_input(cfg)),
        (hypr_path, format_hypr_input(cfg)),
    ):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
    if reload:
        reload_compositor()
