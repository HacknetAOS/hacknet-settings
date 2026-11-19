"""Display, Audio, Network, Input, and Date/Time/System settings pages."""

import platform
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from hacknet_settings.compositor_cfg import (
    KEYMAP_LAYOUTS,
    load_input_config,
    save_and_apply_input,
)
from hacknet_settings.system_ctl import (
    SCALES,
    apply_display_scale,
    get_datetime_status,
    get_displays,
    get_network_summary,
    get_sinks,
    get_system_summary,
    get_volume_pct,
    run_cmd,
    run_detached,
    set_default_sink,
    set_hostname,
    set_timezone,
    set_volume_pct,
)
from hacknet_settings.widgets import add_action_row, make_card, scrolled_page


def build_display_page(set_status):
    scroll, box = scrolled_page()
    card = make_card("Connected Displays")
    disp_info = Gtk.Label(xalign=0, wrap=True)
    card.append(disp_info)
    outputs = []

    def refresh(*_):
        nonlocal outputs
        outputs, lines = get_displays()
        disp_info.set_text("\n".join(lines) if lines else "No compositor output information available.")

    scale_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    scale_row.append(Gtk.Label(label="Display Scale:", xalign=0))
    scale_combo = Gtk.DropDown.new_from_strings(SCALES)
    scale_row.append(scale_combo)

    def on_apply(*_):
        sc = SCALES[scale_combo.get_selected()]
        apply_display_scale(outputs, sc)
        refresh()
        set_status(f"Applied display scale {sc}", True)

    apply_btn = Gtk.Button(label="Apply Scale")
    apply_btn.add_css_class("primary")
    apply_btn.connect("clicked", on_apply)
    scale_row.append(apply_btn)

    ref_btn = Gtk.Button(label="Refresh")
    ref_btn.add_css_class("secondary")
    ref_btn.connect("clicked", refresh)
    scale_row.append(ref_btn)

    card.append(scale_row)
    box.append(card)
    refresh()
    return scroll


def build_audio_page(set_status):
    scroll, box = scrolled_page()
    card = make_card("Volume & Audio Outputs")

    vol_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    vol_row.append(Gtk.Label(label="Output Volume (%):", xalign=0))
    vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 2)
    vol_scale.set_hexpand(True)
    vol_scale.set_value(get_volume_pct())
    vol_scale.connect("value-changed", lambda s: set_volume_pct(s.get_value()))
    vol_row.append(vol_scale)
    card.append(vol_row)

    add_action_row(
        card,
        set_status,
        [
            ("Toggle Output Mute", ["hacknetctl", "volume", "mute"]),
            ("Toggle Mic Mute", ["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"]),
        ],
    )

    sink_lbl = Gtk.Label(label="Available Audio Sinks (pactl):", xalign=0)
    sink_lbl.add_css_class("muted")
    card.append(sink_lbl)

    sink_names = get_sinks()
    sink_combo = Gtk.DropDown.new_from_strings(sink_names or ["No audio sinks detected"])
    sink_combo.set_hexpand(True)

    def on_set_sink(*_):
        if not sink_names:
            return
        sink = sink_names[sink_combo.get_selected()]
        rc, _, err = set_default_sink(sink)
        set_status(f"Default sink: {sink}" if rc == 0 else err, rc == 0)

    sink_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    sink_row.append(sink_combo)
    set_btn = Gtk.Button(label="Set Default")
    set_btn.add_css_class("primary")
    set_btn.connect("clicked", on_set_sink)
    sink_row.append(set_btn)
    card.append(sink_row)

    box.append(card)
    return scroll


def build_network_page(set_status):
    scroll, box = scrolled_page()

    net_card = make_card("Network Interfaces & Radios")
    net_info = Gtk.Label(xalign=0, wrap=True)
    net_card.append(net_info)

    def refresh(*_):
        net_info.set_text(get_network_summary())

    def radio_action(cmd, label):
        rc, _, err = run_cmd(cmd)
        refresh()
        set_status(label if rc == 0 else err, rc == 0)

    radio_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for label, cmd in [
        ("Wi-Fi On", ["nmcli", "radio", "wifi", "on"]),
        ("Wi-Fi Off", ["nmcli", "radio", "wifi", "off"]),
        ("Bluetooth On", ["bluetoothctl", "power", "on"]),
        ("Bluetooth Off", ["bluetoothctl", "power", "off"]),
    ]:
        btn = Gtk.Button(label=label)
        btn.add_css_class("secondary")
        btn.connect("clicked", lambda _, c=cmd, l=label: radio_action(c, l))
        radio_row.append(btn)

    ref_btn = Gtk.Button(label="Refresh")
    ref_btn.add_css_class("secondary")
    ref_btn.connect("clicked", refresh)
    radio_row.append(ref_btn)
    net_card.append(radio_row)
    box.append(net_card)

    host_card = make_card("System Hostname")
    hrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    host_entry = Gtk.Entry(text=platform.node())
    host_entry.set_hexpand(True)
    hrow.append(host_entry)

    def on_set_host(*_):
        hn = host_entry.get_text().strip()
        if not hn:
            return
        rc, _, err = set_hostname(hn)
        set_status(f"Hostname set to {hn}" if rc == 0 else err, rc == 0)

    hbtn = Gtk.Button(label="Set Hostname")
    hbtn.add_css_class("primary")
    hbtn.connect("clicked", on_set_host)
    hrow.append(hbtn)
    host_card.append(hrow)
    box.append(host_card)

    refresh()
    return scroll


def build_input_page(set_status):
    scroll, box = scrolled_page()
    cfg = load_input_config()

    card = make_card("Keyboard & Pointer Settings")
    grid = Gtk.Grid(column_spacing=12, row_spacing=10)

    grid.attach(Gtk.Label(label="Keyboard Layout:", xalign=0), 0, 0, 1, 1)
    kb_layout = Gtk.DropDown.new_from_strings(KEYMAP_LAYOUTS)
    if cfg["layout"] in KEYMAP_LAYOUTS:
        kb_layout.set_selected(KEYMAP_LAYOUTS.index(cfg["layout"]))
    grid.attach(kb_layout, 1, 0, 1, 1)

    grid.attach(Gtk.Label(label="Repeat Rate (keys/sec):", xalign=0), 0, 1, 1, 1)
    rep_rate = Gtk.SpinButton.new_with_range(10, 100, 5)
    rep_rate.set_value(cfg["repeat_rate"])
    grid.attach(rep_rate, 1, 1, 1, 1)

    grid.attach(Gtk.Label(label="Repeat Delay (ms):", xalign=0), 0, 2, 1, 1)
    rep_delay = Gtk.SpinButton.new_with_range(150, 1000, 50)
    rep_delay.set_value(cfg["repeat_delay"])
    grid.attach(rep_delay, 1, 2, 1, 1)

    nat_scroll = Gtk.CheckButton(label="Natural Scrolling (Touchpad / Pointer)")
    nat_scroll.set_active(bool(cfg["natural_scroll"]))
    grid.attach(nat_scroll, 0, 3, 2, 1)
    card.append(grid)

    def on_apply(*_):
        new_cfg = {
            "layout": KEYMAP_LAYOUTS[kb_layout.get_selected()],
            "repeat_rate": int(rep_rate.get_value()),
            "repeat_delay": int(rep_delay.get_value()),
            "natural_scroll": nat_scroll.get_active(),
        }
        save_and_apply_input(new_cfg)
        set_status(f"Applied input settings (layout={new_cfg['layout']})", True)

    apply_btn = Gtk.Button(label="Apply Input Settings")
    apply_btn.add_css_class("primary")
    apply_btn.connect("clicked", on_apply)
    card.append(apply_btn)

    box.append(card)
    return scroll


def build_system_page(set_status):
    scroll, box = scrolled_page()

    dt_card = make_card("Date, Time & Timezone")
    tz_lbl = Gtk.Label(label=get_datetime_status(), xalign=0, wrap=True)
    dt_card.append(tz_lbl)

    tz_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    tz_row.append(Gtk.Label(label="Timezone:", xalign=0))
    tz_entry = Gtk.Entry(placeholder_text="America/New_York or UTC")
    tz_entry.set_hexpand(True)
    tz_row.append(tz_entry)

    def on_set_tz(*_):
        tz = tz_entry.get_text().strip()
        if not tz:
            return
        rc, _, err = set_timezone(tz)
        tz_lbl.set_text(get_datetime_status())
        set_status(f"Timezone set to {tz}" if rc == 0 else err, rc == 0)

    tz_btn = Gtk.Button(label="Set Timezone")
    tz_btn.add_css_class("primary")
    tz_btn.connect("clicked", on_set_tz)
    tz_row.append(tz_btn)
    dt_card.append(tz_row)
    box.append(dt_card)

    sys_card = make_card("System & User Info")
    sys_card.append(Gtk.Label(label=get_system_summary(), xalign=0, wrap=True))

    pw_btn = Gtk.Button(label="Change Account Password (Terminal)")
    pw_btn.add_css_class("secondary")
    pw_btn.connect(
        "clicked",
        lambda *_: run_detached(["foot", "bash", "-lc", "passwd; read -rp 'Press Enter to close...'"]),
    )
    sys_card.append(pw_btn)
    box.append(sys_card)

    return scroll
