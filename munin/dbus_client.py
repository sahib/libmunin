import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


MUNIN_BUS_NAME = 'org.libmunin'


def rebuild_finished_received():
    print('Client: Finished!')


DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
helloservice = bus.get_object(MUNIN_BUS_NAME, '/org/libmunin')
helloservice.connect_to_signal(
    'rebuild_finished',
    rebuild_finished_received,
    dbus_interface="org.libmunin.Session"
)
rebuild = helloservice.get_dbus_method('rebuild', MUNIN_BUS_NAME)


def hellower():
    print('beginning')
    rebuild('full', reply_handler=lambda *_: _, error_handler=lambda *_: _)
    print('-- not running, started async')
    print('...?')
    return True

GLib.timeout_add(500, hellower)
GLib.MainLoop().run()
