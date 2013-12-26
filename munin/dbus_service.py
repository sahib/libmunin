#!/usr/bin/env python
# encoding: utf-8

"""

Limitations
-----------

* No generator support for recommendations
* You always work with Song uids, you created yourself.

"""


MUNIN_BUS_NAME = 'org.libmunin'
MUNIN_INTERFACE = 'org.libmunin.Session'

# Stdlib:
import time
import json
import logging
LOGGER = logging.getLogger(__name__)

# Internal:
from munin.easy import EasySession


# External
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class MuninRemoteServer(dbus.service.Object):
    def __init__(self):
        # DBUS data:
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(MUNIN_BUS_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, '/org/libmunin')

    @dbus.service.method(MUNIN_BUS_NAME)
    def create(self, name):
        pass

    @dbus.service.method(MUNIN_BUS_NAME)
    def load(self, path):
        pass


class DBUSRemoteSession(dbus.service.Object):
    def __init__(self):
        # Application data:
        self._session = EasySession()

        # DBUS data:
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(MUNIN_BUS_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, '/org/libmunin')

    #####################
    #  Rebuild methods  #
    #####################

    @dbus.service.signal(dbus_interface=MUNIN_INTERFACE)
    def rebuild_finished(self):
        LOGGER.warning('Server: triggerred rebuild finished')

    @dbus.service.signal(dbus_interface=MUNIN_INTERFACE)
    def rebuild_started(self):
        LOGGER.warning('Server: rebuild was started')

    @dbus.service.method(MUNIN_BUS_NAME)
    def rebuild(self, strategy='full'):
        self.rebuild_started()
        time.sleep(2)
        self.rebuild_finished()

    @dbus.service.method(MUNIN_BUS_NAME)
    def fix_graph(self):
        self._session.fix_graph()

    #############
    #  Mapping  #
    #############

    @dbus.service.method(MUNIN_BUS_NAME, out_signature='a{uu}')
    def mapping(self):
        return dict(self._session.mapping)

    @dbus.service.method(MUNIN_BUS_NAME, out_signature='a{uu}')
    def inverse_mapping(self):
        return dict(~self._session.mapping)

    @dbus.service.method(MUNIN_BUS_NAME, out_signature='u')
    def forward_lookup(self, munin_id):
        return self._session.mapping[munin_id:]

    @dbus.service.method(MUNIN_BUS_NAME, out_signature='u')
    def inverse_lookup(self, user_id):
        return self._session.mapping[:user_id]

    ######################
    #  Song modifcation  #
    ######################

    @dbus.service.method(MUNIN_BUS_NAME, in_signature='su')
    def add(self, json_mapping, user_id):
        uid = self._session.add(json.loads(json_mapping))
        self._session.mapping[uid] = user_id

    @dbus.service.method(MUNIN_BUS_NAME, in_signature='su')
    def insert(self, json_mapping, user_id):
        uid = self._session.insert(json.loads(json_mapping))
        self._session.mapping[uid] = user_id

    @dbus.service.method(MUNIN_BUS_NAME, in_signature='su')
    def remove(self, json_mapping, user_id):
        uid = self._session.remove(json.loads(json_mapping))
        del self._session.mapping[uid]

    #####################
    #  Recommendations  #
    #####################

    @dbus.service.method(MUNIN_BUS_NAME, in_signature='uu')
    def recommendations_from_seed(self, song_id, number):
        uid = self._session.mapping[:song_id]
        self._session.recommendations_from_seed(uid, number)

    # TODO

    ####################
    #  Misc Functions  #
    ####################

    @dbus.service.method(MUNIN_BUS_NAME)
    def name(self):
        return self._session.name



if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    myservice = DBUSRemoteSession()
    GLib.MainLoop().run()
