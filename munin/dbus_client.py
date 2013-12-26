import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


MUNIN_BUS_NAME = 'org.libmunin'
MUNIN_INTERFACE = 'org.libmunin.Session'


class SessionClient:
    def __init__(self, name):
        bus = dbus.SessionBus()
        self.service = bus.get_object(
            MUNIN_BUS_NAME,
            '/' + MUNIN_BUS_NAME.replace('.', '/')
        )

    def connect_signal(self, signal_name, callback):
        self.service.connect_to_signal(
            signal_name, callback,
            dbus_interface=MUNIN_INTERFACE
        )

    def __call__(self, name, *args, **kwargs):
        method = self.service.get_dbus_method(name, MUNIN_BUS_NAME)
        if kwargs.get('async') is not None:
            # Make dbus python-dbus call this method async
            kwargs['reply_handler'] = kwargs.get('async')
            kwargs['error_handler'] = lambda *_: _
        return method(*args, **kwargs)


if __name__ == '__main__':
    loop = DBusGMainLoop(set_as_default=True)
    sess = SessionClient('test')

    def hellower():
        print('... async call:', end='')
        sess('rebuild', 'full', async=lambda: print('client: finished'))
        print('... [DONE]')
        return True

    GLib.timeout_add(500, hellower)
    GLib.MainLoop().run()
    loop.run()
