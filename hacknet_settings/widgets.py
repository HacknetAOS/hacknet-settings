"""Shared GTK4 widget helpers for HacknetOS Settings."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from hacknet_settings.system_ctl import run_cmd  # noqa: E402


def make_card(title=None):
    """Create a styled card container with an optional section heading."""
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    card.add_css_class("card")
    if title:
        lbl = Gtk.Label(label=title, xalign=0)
        lbl.add_css_class("section-title")
        card.append(lbl)
    return card


def scrolled_page():
    """Create a vertically scrollable page container and inner content box."""
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.set_hexpand(True)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    box.set_margin_top(18)
    box.set_margin_bottom(24)
    box.set_margin_start(22)
    box.set_margin_end(22)
    scroll.set_child(box)
    return scroll, box


def run_ctl_action(set_status, cmd, label):
    """Run a control command and update the header status label."""
    rc, _, err = run_cmd(cmd)
    set_status(label if rc == 0 else (err or f"Command failed: {' '.join(cmd)}"), rc == 0)


def add_action_row(card, set_status, items):
    """Append a horizontal row of secondary action buttons to a card."""
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for label, cmd in items:
        btn = Gtk.Button(label=label)
        btn.add_css_class("secondary")
        btn.connect("clicked", lambda _, c=cmd, l=label: run_ctl_action(set_status, c, l))
        row.append(btn)
    card.append(row)
    return row
