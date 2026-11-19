"""Main GTK4 Application and SettingsWindow router."""

import os
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from hacknet_settings.pages_desktop import (
    build_appearance_page,
    build_desktop_page,
    build_keybinds_page,
    build_notifications_page,
)
from hacknet_settings.pages_system import (
    build_audio_page,
    build_display_page,
    build_input_page,
    build_network_page,
    build_system_page,
)


def _load_css():
    candidates = [
        "/usr/share/hacknet-settings/style.css",
        os.path.join(os.path.dirname(__file__), "..", "data", "style.css"),
    ]
    provider = Gtk.CssProvider()
    for path in candidates:
        if os.path.isfile(path):
            provider.load_from_path(os.path.abspath(path))
            break
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


class SettingsWindow(Gtk.ApplicationWindow):
    """Main HacknetOS Settings window with lazy-loaded category pages."""

    def __init__(self, app):
        super().__init__(application=app, title="HacknetOS Settings")
        self.set_default_size(980, 680)
        _load_css()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.add_css_class("header-bar")
        title = Gtk.Label(label="HACKNETOS // SYSTEM SETTINGS", xalign=0)
        title.add_css_class("title-label")
        header.append(title)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        self.status_lbl = Gtk.Label(label="", xalign=1)
        self.status_lbl.add_css_class("muted")
        header.append(self.status_lbl)
        root.append(header)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body.set_vexpand(True)
        root.append(body)

        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.add_css_class("sidebar")
        sidebar_box.set_size_request(220, -1)
        self.nav_list = Gtk.ListBox()
        self.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        sidebar_box.append(self.nav_list)
        body.append(sidebar_box)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        body.append(self.stack)

        self._page_builders = {}
        pages = [
            ("appearance", "Appearance & Theme", build_appearance_page),
            ("desktop", "Desktop & Layout", build_desktop_page),
            ("keybinds", "Keybinds", build_keybinds_page),
            ("display", "Display & Monitors", build_display_page),
            ("audio", "Audio & Devices", build_audio_page),
            ("network", "Network & Bluetooth", build_network_page),
            ("input", "Keyboard & Mouse", build_input_page),
            ("notifications", "Notifications", build_notifications_page),
            ("system", "Date, Time & System", build_system_page),
        ]
        for name, label, builder in pages:
            self._register_page(name, label, builder)

        self.nav_list.connect("row-selected", self._on_nav_selected)
        self.nav_list.select_row(self.nav_list.get_row_at_index(0))

    def set_status(self, msg: str, ok: bool = True):
        self.status_lbl.set_text(msg)
        self.status_lbl.remove_css_class("status-ok")
        self.status_lbl.remove_css_class("status-warn")
        self.status_lbl.add_css_class("status-ok" if ok else "status-warn")

    def _register_page(self, name: str, label: str, builder_fn):
        holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        holder.set_hexpand(True)
        holder.set_vexpand(True)
        self.stack.add_named(holder, name)
        self._page_builders[name] = (holder, builder_fn)
        row = Gtk.ListBoxRow()
        row.page_name = name
        row.set_child(Gtk.Label(label=label, xalign=0))
        self.nav_list.append(row)

    def _on_nav_selected(self, _, row):
        if row is not None:
            if row.page_name in self._page_builders:
                holder, builder_fn = self._page_builders.pop(row.page_name)
                holder.append(builder_fn(self.set_status))
            self.stack.set_visible_child_name(row.page_name)


def main():
    app = Gtk.Application(application_id="org.hacknetos.settings")
    app.connect("activate", lambda a: SettingsWindow(a).present())
    return app.run(None)
