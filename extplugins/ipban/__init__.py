#
# IPban Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2014 Mark Weirath (xlr8or@xlr8or.com)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
# CHANGELOG
#
# 06-12-2014 : v1.0.0beta : xlr8or
# * First edition of ipban
# 23-02-2015 : v1.1.0beta : Fenix
# * Added missing 'settings' section in plugin configuration file
# * Fixed plugin not correctly loading maxlevel property
# * Correctly return list of banned ips in getBanIps and getTempBanIps
# * Optimized SQL quieries and IP ban check workflow
# * Updated plugin module structure for easier install
# * Fixed usage of deprecated method startup()

__version__ = '1.1.0beta'
__author__ = 'xlr8or'

import b3
import b3.events
import b3.lib
import b3.plugin

from time import time

try:
    # python 2.7
    from ConfigParser import NoOptionError
except ImportError:
    # python 2.6
    from b3.lib.configparser import NoOptionError


class IpbanPlugin(b3.plugin.Plugin):

    _adminPlugin = None
    _frostBiteGameNames = ['bfbc2', 'moh', 'bf3', 'bf4']

    def __init__(self, console, config=None):
        """
        Object constructor.
        :param console: The console instance
        :param config: The plugin configuration
        """
        self._adminPlugin = None          # admin plugin object reference
        self._maxLevel = 1                # initialize default max level
        self.query = None                 # shortcut to the storage.query function
        b3.plugin.Plugin.__init__(self, console, config)

    def onStartup(self):
        """
        Initialize plugin settings
        """
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False

        # define a shortcut to the storage.query function
        self.query = self.console.storage.query

        if self.console.gameName in self._frostBiteGameNames:
            event_id = self.console.getEventID('EVT_PUNKBUSTER_NEW_CONNECTION')
        else:
            event_id = self.console.getEventID('EVT_CLIENT_AUTH')

        try:
            # B3 1.10
            self.registerEvent(event_id, self.onPlayerConnect)
        except:
            # B3 1.9.x
            self.registerEvent(event_id)

        self.debug('Banned Ips: %s' % self.getBanIps())
        self.debug('Banned Ips: %s' % self.getTempBanIps())
        self.debug('Started')

    def onLoadConfig(self):
        """
        Load plugin configuration
        """
        try:
            self._maxLevel = self.console.getGroupLevel(self.config.get('settings', 'maxlevel'))
        except (NoOptionError, KeyError), err:
            self.error(err)
        self.debug('Maximum level affected: %s' % self._maxLevel)

    def onEvent(self, event):
        """
        Handle intercepted events
        """
        # EVT_CLIENT_AUTH is for q3a based games, EVT_PUNKBUSTER_NEW_CONNECTION is a PB related event for BF:BC2
        if event.type == self.console.getEventID('EVT_CLIENT_AUTH') or \
           event.type == self.console.getEventID('EVT_PUNKBUSTER_NEW_CONNECTION'):
            self.onPlayerConnect(event)

    def onPlayerConnect(self, event):
        """
        Examine players ip address and allow/deny connection.
        """
        client = event.client
        # check the level of the connecting client before applying the filters
        if client.maxLevel > self._maxLevel:
            self.debug('%s is a higher level user, and allowed to connect' % client.name)
            return

        self.debug('Checking player: %s, name: %s, ip: %s' % (client.cid, client.name, client.ip))

        # check for active bans and tempbans
        if client.ip in self.getBanIps():
            self.debug('Client refused: %s - %s' % (client.name, client.ip))
            message = 'Netblocker: Client refused: %s (%s) has an active Ban' % (client.ip, client.name)
            client.kick(message)
        elif client.ip in self.getTempBanIps():
            self.debug('Client refused: %s - %s' % (client.name, client.ip))
            message = 'Netblocker: Client refused: %s (%s) has an active TempBan' % (client.ip, client.name)
            client.kick(message)
        else:
            self.debug('Client accepted (not active Ban/TempBan found): %s - %s' % (client.name, client.ip))

    def getBanIps(self):
        """
        Returns a list of banned IPs
        """
        banned = []
        q = """SELECT clients.ip as target_ip FROM penalties INNER JOIN clients ON penalties.client_id = clients.id
               WHERE penalties.type = 'Ban' AND penalties.inactive = 0 AND penalties.time_expire = -1
               GROUP BY clients.ip"""
        cursor = self.query(q)
        if cursor:
            while not cursor.EOF:
                banned.append(cursor.getValue('target_ip'))
                cursor.moveNext()
        cursor.close()
        return banned

    def getTempBanIps(self):
        """
        Returns a list of TempBanned IPs
        """
        banned = []
        q = """SELECT clients.ip AS target_ip FROM penalties INNER JOIN clients ON penalties.client_id = clients.id
               WHERE penalties.type = 'TempBan' AND penalties.inactive = 0 AND penalties.time_expire > %s
               GROUP BY clients.ip""" % int(time())
        cursor = self.query(q)
        if cursor:
            while not cursor.EOF:
                banned.append(cursor.getValue('target_ip'))
                cursor.moveNext()
        cursor.close()
        return banned

if __name__ == '__main__':
    print '\nThis is version ' + __version__ + ' by ' + __author__ + ' for BigBrotherBot.\n'
