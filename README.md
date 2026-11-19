# HacknetOS Settings (`hacknet-settings`)

Modular GTK4 system, desktop, theme, input, and keybind settings application for HacknetOS.

## Structure

- `bin/hacknet-settings` — CLI/desktop entrypoint
- `data/` — `style.css` and `hacknet-settings.desktop`
- `hacknet_settings/system_ctl.py` — Shared OS, compositor, theme, display, audio, network, and datetime helpers
- `hacknet_settings/compositor_cfg.py` — Keybinds and input persistence + Sway/Hyprland config writers
- `hacknet_settings/widgets.py` — Shared GTK4 UI builders
- `hacknet_settings/pages_desktop.py` — Appearance, Desktop & Layout, Keybinds, and Notifications pages
- `hacknet_settings/pages_system.py` — Display, Audio, Network & Bluetooth, Keyboard & Mouse, and Date/Time/System pages
- `hacknet_settings/app.py` — Main GTK4 application window and lazy page router
- `tests/` — Unit tests for compositor config generation and persistence
