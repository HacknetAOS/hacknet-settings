"""Shared system, compositor, theme, audio, network, and display helpers."""

import json
import os
import platform
import shutil
import subprocess

THEMES = [
    ("blue", "Hacknet Blue (Default)"),
    ("ente", "Ente (Cyan / Teal)"),
    ("hellhound", "Hellhound (Crimson / Amber)"),
    ("naix", "Naix (Matrix Emerald)"),
    ("hacknet", "Hacknet Classic"),
]
THEME_CFG_PATH = "/etc/hacknetos/theme.cfg"
SCALES = ["1.0", "1.25", "1.5", "2.0"]


def run_cmd(cmd, check=False, timeout=3):
    """Run a command with stdin closed and a bounded timeout."""
    try:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def run_detached(cmd):
    """Launch a command in the background without blocking."""
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def compositor_backend():
    """Detect active Wayland compositor ('sway', 'hyprland', or 'unknown')."""
    if os.environ.get("SWAYSOCK") or (shutil.which("swaymsg") and run_cmd(["swaymsg", "-t", "get_version"])[0] == 0):
        return "sway"
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") or (
        shutil.which("hyprctl") and run_cmd(["hyprctl", "version"])[0] == 0
    ):
        return "hyprland"
    return "unknown"


def reload_compositor():
    """Reload Sway or Hyprland configuration."""
    backend = compositor_backend()
    if backend == "sway":
        return run_cmd(["swaymsg", "reload"])
    if backend == "hyprland":
        return run_cmd(["hyprctl", "reload"])
    return 0, "", ""


def get_system_theme_default():
    if os.path.isfile(THEME_CFG_PATH):
        try:
            with open(THEME_CFG_PATH, "r", encoding="utf-8") as fh:
                return fh.read().strip() or "blue"
        except Exception:
            pass
    return "blue"


def apply_theme(theme_id):
    return run_cmd(["hacknet-theme", "apply", theme_id], timeout=5)


def get_displays():
    backend = compositor_backend()
    outputs, lines = [], []
    if backend == "sway":
        rc, out, _ = run_cmd(["swaymsg", "-t", "get_outputs"])
        if rc == 0 and out:
            try:
                for o in json.loads(out):
                    r = o.get("current_mode") or {}
                    outputs.append(o["name"])
                    lines.append(
                        f"• {o['name']}: {r.get('width')}x{r.get('height')} (scale {o.get('scale', 1.0)})"
                    )
            except Exception:
                pass
    elif backend == "hyprland":
        rc, out, _ = run_cmd(["hyprctl", "monitors", "-j"])
        if rc == 0 and out:
            try:
                for m in json.loads(out):
                    outputs.append(m["name"])
                    lines.append(
                        f"• {m['name']}: {m.get('width')}x{m.get('height')}@{m.get('refreshRate')}Hz (scale {m.get('scale', 1.0)})"
                    )
            except Exception:
                pass
    return outputs, lines


def apply_display_scale(outputs, scale_str):
    backend = compositor_backend()
    for name in outputs:
        if backend == "sway":
            run_cmd(["swaymsg", "output", name, "scale", scale_str])
        elif backend == "hyprland":
            run_cmd(["hyprctl", "keyword", "monitor", f"{name},preferred,auto,{scale_str}"])


def get_volume_pct():
    rc, out, _ = run_cmd(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
    if rc == 0 and "Volume:" in out:
        try:
            return round(float(out.split()[1]) * 100)
        except Exception:
            pass
    return 50


def set_volume_pct(pct):
    return run_cmd(["hacknetctl", "volume", str(int(pct))])


def get_sinks():
    rc, out, _ = run_cmd(["pactl", "list", "short", "sinks"])
    sinks = []
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                sinks.append(parts[1])
    return sinks


def set_default_sink(sink_name):
    return run_cmd(["pactl", "set-default-sink", sink_name])


def get_network_summary():
    rc, out, _ = run_cmd(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"])
    if rc == 0 and out:
        return out
    _, ip_out, _ = run_cmd(["ip", "-br", "addr"])
    return ip_out or "No network interfaces detected."


def set_hostname(hostname):
    return run_cmd(["pkexec", "hostnamectl", "set-hostname", hostname], timeout=15)


def get_datetime_status():
    rc, out, _ = run_cmd(["timedatectl", "status"])
    return out if rc == 0 else "timedatectl unavailable."


def set_timezone(tz):
    return run_cmd(["pkexec", "timedatectl", "set-timezone", tz], timeout=15)


def get_system_summary():
    _, mem_out, _ = run_cmd(["free", "-h"])
    _, df_out, _ = run_cmd(["df", "-h", "/"])
    return (
        f"User     : {os.environ.get('USER', 'unknown')}\n"
        f"Hostname : {platform.node()}\n"
        f"Kernel   : {platform.release()}\n"
        f"Arch     : {platform.machine()}\n\n"
        f"Memory:\n{mem_out}\n\n"
        f"Root Filesystem:\n{df_out}"
    )
