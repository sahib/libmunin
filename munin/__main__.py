#!/usr/bin/env python
# encoding: utf-8


from munin.dbus_service import DBUSRemoteSession
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    DBUSRemoteSession()
    GLib.MainLoop().run()
