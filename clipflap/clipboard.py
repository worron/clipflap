#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

import os
import sys
import pickle
import shutil
from configparser import ConfigParser

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango


class Config(ConfigParser):
	"""
	Config settings manager.
	No data validation, be careful while config editing.
	"""
	def __init__(self, path):
		self.name = "config.ini"
		self.path = path
		self._setup()

		super().__init__()
		self.read(self.configfile)

	def _setup(self):
		self.default_configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", self.name)
		self.configfile = os.path.join(self.path, self.name)
		if not os.path.isfile(self.configfile):
			shutil.copyfile(self.default_configfile, self.configfile)


class HistoryWindow(Gtk.ApplicationWindow):
	"""Clipboard history widget"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# storage directory
		self.path = os.path.expanduser("~/.config/clipflap")
		if not os.path.exists(self.path):
			os.makedirs(self.path)

		# config
		self.config = Config(self.path)

		# history file
		self.datafile = os.path.join(self.path, "history.pkl")

		# base settings
		self.data = []
		self.search_text = ""
		self.bsize = int(self.config["Clipboard"]["size"])
		self.autosave = int(self.config["Clipboard"]["autosave"])
		self.size = (int(self.config["Window"]["width"]), int(self.config["Window"]["height"]))

		# window settings
		self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
		self.set_default_size(*self.size)
		self.set_skip_taskbar_hint(True)
		self.set_keep_above(True)

		# clipboard
		self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

		# store
		self.store = Gtk.ListStore(str)
		self.filtered = self.store.filter_new()
		self.filtered.set_visible_func(self.store_filter_func)

		# view
		self.treeview = Gtk.TreeView(headers_visible=False)
		self.selection = self.treeview.get_selection()
		self.scrollable = Gtk.ScrolledWindow()
		self.scrollable.add(self.treeview)

		column = Gtk.TreeViewColumn("Text", Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END), text=0)
		self.treeview.append_column(column)

		# search
		self.search = Gtk.SearchEntry()

		# pack
		box = Gtk.Box(spacing=12, orientation=Gtk.Orientation.VERTICAL, margin=4)
		box.pack_start(self.search, False, True, 0)
		box.pack_end(self.scrollable, True, True, 0)
		self.add(box)

		# accelerators
		self.accelerators = Gtk.AccelGroup()
		self.add_accel_group(self.accelerators)
		for keyname, value in self.config["Keys"].items():
			key, mod = Gtk.accelerator_parse(value)
			self.accelerators.connect(key, mod, Gtk.AccelFlags.VISIBLE, getattr(self, "_on_%s_key" % keyname))

		# signals
		self.connect("delete-event", self.hide_history)
		self.search.connect("activate", self.on_search_activated)
		self.treeview.connect("row-activated", self.on_item_activated)
		self.clipboard.connect("owner-change", self.on_buffer_change)

		if self.autosave > 0:
			GLib.timeout_add(self.autosave, self.save_history)

	def _on_down_key(self, *args):
		self.treeview.emit("move-cursor", Gtk.MovementStep.DISPLAY_LINES, 1)

	def _on_up_key(self, *args):
		self.treeview.emit("move-cursor", Gtk.MovementStep.DISPLAY_LINES, -1)

	def _on_escape_key(self, *args):
		if not self.search_text:
			self.hide_history()
		else:
			self.search.set_text("")
			self.on_search_activated()

	def _on_search_key(self, *args):
		self.search.grab_focus()

	def _on_delete_key(self, *args):
		self._delete_item()

	def _delete_item(self):
		model, treeiter = self.selection.get_selected()
		if treeiter is not None:
			text = self.filtered[treeiter][0]
			self.data.remove(text)
			self._rebuild_store()

	def _rebuild_store(self):
		self.treeview.set_model(None)

		self.store.clear()
		for text in self.data:
			self.store.append([text])

		self.treeview.set_model(self.filtered)
		if len(self.filtered) > 0:
			self.treeview.set_cursor(0)

	def _place_on_center(self):
		screen = self.get_screen()
		self.move((screen.get_width() - self.size[0]) / 2, (screen.get_height() - self.size[0]) / 2)

	def on_buffer_change(self, clipboard, event):
		text = self.clipboard.wait_for_text()
		if text is not None:
			if text in self.data:
				self.data.remove(text)
			self.data.insert(0, text)
			if len(self.data) > self.bsize:
				self.data = self.data[:self.bsize]
			self._rebuild_store()

	def on_item_activated(self, tree, path, colomn):
		treeiter = self.filtered.get_iter(path)
		text = self.filtered[treeiter][0]
		self.clipboard.set_text(text, -1)
		self.hide_history()

	def on_search_activated(self, *args):
		self.search_text = self.search.get_text()
		self.filtered.refilter()
		if len(self.filtered) > 0:
			self.treeview.set_cursor(0)
			self.treeview.grab_focus()

	def store_filter_func(self, model, treeiter, data):
		if not self.search_text:
			return True
		else:
			return self.search_text.lower() in model[treeiter][0].lower()

	def toggle(self):
		if not self.get_visible():
			self.show_history()
		else:
			self.hide_history()

	def show_history(self):
		self._rebuild_store()
		self._place_on_center()  # temporary fix
		self.show_all()
		self.treeview.grab_focus()

	def hide_history(self, *args):
		self.hide()
		return True

	def save_history(self):
		with open(self.datafile, "wb") as fp:
			pickle.dump(self.data, fp)

	def load_history(self):
		if os.path.isfile(self.datafile):
			with open(self.datafile, "rb") as fp:
				self.data = pickle.load(fp)


class Clipboard(Gtk.Application):
	"""Clipboard history application"""
	def __init__(self):
		super().__init__(flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, application_id="com.github.worron.clipflap")
		self.window = None

		# command line args
		self.add_main_option("show", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Show buffer history", None)
		self.add_main_option("clear", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Clear buffer history", None)
		self.add_main_option("quit", 0, GLib.OptionFlags.NONE, GLib.OptionArg.NONE, "Exit program", None)

	def do_startup(self):
		Gtk.Application.do_startup(self)

		# tray icon
		icon_name = "clipflap"
		icon_theme = Gtk.IconTheme.get_default()
		if icon_theme.has_icon(icon_name):
			tray_pb = icon_theme.load_icon(icon_name, 48, 0)
			self.trayicon = Gtk.StatusIcon(pixbuf=tray_pb)
		else:
			self.trayicon = Gtk.StatusIcon(stock=Gtk.STOCK_EDIT)

		self.trayicon.connect('popup-menu', self.on_tray_right_click)
		self.trayicon.connect('activate', self.on_tray_left_click)

		# menu
		self.menu = Gtk.Menu()
		for label, handler in (["Clear", self.on_clear], ["Quit", self.on_quit]):
			item = Gtk.MenuItem(label=label)
			item.connect("activate", handler)
			self.menu.append(item)
		self.menu.show_all()

	def do_activate(self):
		self.window = HistoryWindow(application=self, title="ClipFlap")
		self.window.load_history()

	def do_shutdown(self):
		self.window.save_history()
		Gtk.Application.do_shutdown(self)

	def do_command_line(self, command_line):
		if self.window is None:
			self.activate()

		options = command_line.get_options_dict()
		for arg in [a for a in ("show", "clear", "quit") if options.contains(a)]:
			action = getattr(self, "on_%s" % arg)
			action()
		return 0

	def on_tray_right_click(self, icon, button, time):
		self.menu.popup(None, None, None, icon, button, time)

	def on_tray_left_click(self, *args):
		self.window.toggle()

	def on_show(self, *args):
		self.window.toggle()

	def on_clear(self, *args):
		self.window.data = []
		self.window._rebuild_store()

	def on_quit(self, *args):
		self.quit()


def run():
	app = Clipboard()
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)

if __name__ == "__main__":
	run()
