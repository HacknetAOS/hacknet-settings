"""Desktop, Appearance, Keybinds, and Notifications settings pages."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from hacknet_settings.compositor_cfg import (
    KEYBIND_PRESET_ACTIONS,
    load_keybinds,
    save_and_apply_keybinds,
)
from hacknet_settings.system_ctl import THEMES, apply_theme, get_system_theme_default
from hacknet_settings.widgets import add_action_row, make_card, scrolled_page


def build_appearance_page(set_status):
    scroll, box = scrolled_page()
    card = make_card("HacknetOS Color Theme")

    desc = Gtk.Label(
        label="Select a preset to update Quickshell, terminal, and desktop accent colors.",
        xalign=0,
        wrap=True,
    )
    desc.add_css_class("muted")
    card.append(desc)

    flow = Gtk.FlowBox()
    flow.set_selection_mode(Gtk.SelectionMode.NONE)
    flow.set_row_spacing(8)
    flow.set_column_spacing(8)

    def on_select(theme_id, theme_name):
        rc, _, err = apply_theme(theme_id)
        set_status(f"Applied theme: {theme_name}" if rc == 0 else err, rc == 0)

    for tid, tname in THEMES:
        btn = Gtk.Button(label=tname)
        btn.add_css_class("secondary")
        btn.connect("clicked", lambda _, t=tid, n=tname: on_select(t, n))
        flow.append(btn)
    card.append(flow)

    default_lbl = Gtk.Label(
        label=f"System default (/etc/hacknetos/theme.cfg): {get_system_theme_default()}",
        xalign=0,
    )
    default_lbl.add_css_class("muted")
    card.append(default_lbl)

    box.append(card)
    return scroll


def build_desktop_page(set_status):
    scroll, box = scrolled_page()

    layout_card = make_card("Workspace & Shell Layout")
    add_action_row(
        layout_card,
        set_status,
        [
            ("Toggle RAM Gutter", ["hacknetctl", "toggle-gutter"]),
            ("Toggle Console (Full / Bottom)", ["hacknetctl", "toggle-terminal-bottom"]),
            ("Reset Layout", ["hacknet-layout"]),
        ],
    )
    box.append(layout_card)

    ws_card = make_card("Virtual Desktops")
    add_action_row(
        ws_card,
        set_status,
        [
            ("Previous Desktop", ["hacknetctl", "desktop-switch-prev"]),
            ("Next Desktop", ["hacknetctl", "desktop-switch-next"]),
            ("New Desktop (+)", ["hacknetctl", "desktop-add"]),
            ("Remove Desktop (-)", ["hacknetctl", "desktop-remove"]),
        ],
    )
    box.append(ws_card)
    return scroll


def build_keybinds_page(set_status):
    scroll, box = scrolled_page()
    binds = load_keybinds()

    add_card = make_card("Add Keybind (Desktop Environment & Custom Actions)")
    grid = Gtk.Grid(column_spacing=10, row_spacing=10)

    mod_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    kb_super = Gtk.CheckButton(label="Super", active=True)
    kb_ctrl = Gtk.CheckButton(label="Ctrl")
    kb_alt = Gtk.CheckButton(label="Alt")
    kb_shift = Gtk.CheckButton(label="Shift")
    for cb in (kb_super, kb_ctrl, kb_alt, kb_shift):
        mod_box.append(cb)

    grid.attach(Gtk.Label(label="Modifiers:", xalign=0), 0, 0, 1, 1)
    grid.attach(mod_box, 1, 0, 1, 1)

    kb_key = Gtk.Entry(placeholder_text="e.g. v, g, t, F2, Return, space")
    kb_key.set_hexpand(True)
    grid.attach(Gtk.Label(label="Key:", xalign=0), 0, 1, 1, 1)
    grid.attach(kb_key, 1, 1, 1, 1)

    kb_action = Gtk.DropDown.new_from_strings([a[0] for a in KEYBIND_PRESET_ACTIONS])
    grid.attach(Gtk.Label(label="Action:", xalign=0), 0, 2, 1, 1)
    grid.attach(kb_action, 1, 2, 1, 1)

    kb_custom = Gtk.Entry(placeholder_text="Custom shell command...")
    kb_custom.set_visible(False)
    grid.attach(Gtk.Label(label="Command:", xalign=0), 0, 3, 1, 1)
    grid.attach(kb_custom, 1, 3, 1, 1)
    kb_action.connect(
        "notify::selected",
        lambda *_: kb_custom.set_visible(KEYBIND_PRESET_ACTIONS[kb_action.get_selected()][1] == "__custom__"),
    )
    add_card.append(grid)

    list_card = make_card("Custom User Keybinds")
    kb_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    list_card.append(kb_list_box)

    def refresh_list():
        while child := kb_list_box.get_first_child():
            kb_list_box.remove(child)
        if not binds:
            lbl = Gtk.Label(label="No custom keybinds yet. Add one above.", xalign=0)
            lbl.add_css_class("muted")
            kb_list_box.append(lbl)
            return
        for idx, b in enumerate(binds):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            combo = "+".join(b.get("mods", []) + [b["key"]])
            txt = Gtk.Label(label=f"{combo}  →  {b['label']} ({b['command']})", xalign=0, wrap=True)
            txt.set_hexpand(True)
            row.append(txt)
            rm = Gtk.Button(label="Remove")
            rm.add_css_class("danger")
            rm.connect("clicked", lambda _, i=idx: remove_bind(i))
            row.append(rm)
            kb_list_box.append(row)

    def remove_bind(idx):
        if 0 <= idx < len(binds):
            binds.pop(idx)
            save_and_apply_keybinds(binds)
            refresh_list()
            set_status("Removed keybind & reloaded compositor", True)

    def on_add(*_):
        key = kb_key.get_text().strip()
        if not key:
            set_status("Enter a key name first", False)
            return
        mods = [m for m, cb in (("Super", kb_super), ("Ctrl", kb_ctrl), ("Alt", kb_alt), ("Shift", kb_shift)) if cb.get_active()]
        label, cmd = KEYBIND_PRESET_ACTIONS[kb_action.get_selected()]
        if cmd == "__custom__":
            cmd = kb_custom.get_text().strip()
            label = cmd
        if not cmd:
            set_status("Enter a custom command", False)
            return
        binds[:] = [b for b in binds if not (b.get("mods") == mods and b.get("key") == key)]
        binds.append({"mods": mods, "key": key, "label": label, "command": cmd})
        save_and_apply_keybinds(binds)
        refresh_list()
        set_status(f"Saved keybind ({'+'.join(mods + [key])}) & reloaded compositor", True)

    save_btn = Gtk.Button(label="Add & Apply Keybind")
    save_btn.add_css_class("primary")
    save_btn.connect("clicked", on_add)
    add_card.append(save_btn)

    box.append(add_card)
    box.append(list_card)

    defaults_card = make_card("Built-in HacknetOS Shortcuts")
    defaults_lbl = Gtk.Label(
        label=(
            "Super (tap): App Search Bar  |  Super+Enter: New Terminal  |  Super+Shift+Enter: Stage Terminal\n"
            "Super+Tab: Cycle Stage  |  Super+F: Fullscreen  |  Super+Q/W: Close Window\n"
            "Super+1..5 / Left / Right: Switch Desktop  |  Super+Shift+N: New Desktop  |  Super+L: Lock"
        ),
        xalign=0,
        wrap=True,
    )
    defaults_lbl.add_css_class("muted")
    defaults_card.append(defaults_lbl)
    box.append(defaults_card)

    refresh_list()
    return scroll


def build_notifications_page(set_status):
    scroll, box = scrolled_page()
    card = make_card("Notification Controls")
    add_action_row(
        card,
        set_status,
        [
            ("Enable Do Not Disturb", ["hacknetctl", "dnd", "on"]),
            ("Disable Do Not Disturb", ["hacknetctl", "dnd", "off"]),
            ("Send Test Notification", ["hacknetctl", "notify", "HacknetOS Settings", "Test notification delivered"]),
        ],
    )
    box.append(card)
    return scroll
