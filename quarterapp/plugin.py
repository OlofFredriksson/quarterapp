#
#  Copyright (c) 2013 Markus Eliasson, http://www.quarterapp.com/
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


class HandlerPlugin(object):
    """
    A handler plugin represents a single RequestHandler mounted under
    the given name.
    """

    def __init__(self, path, handler):
        """
        Creates the plugin

        Args: 
            path: Is the name under which this RequestHandler should be mounted.
            handler: The class derived from tornado.web.RequestHandler implementing the handler.
        """
        self.path = path
        self.handler = handler


class ViewPlugin(object):
    """
    A view is a complete page in quarterapp that also has an entry in the top
    menu.

    If you just want a view without a meny item, create a HandlerPlugin instead.
    """

    def __init__(self, path, handler, name):
        """
        Creates the plugin.

        Args: 
            path: Is the name under which this RequestHandler should be mounted.
            handler: The class derived from tornado.web.RequestHandler implementing the handler.
            name: The name of the view that will be used in the menu
        """
        self.path = path
        self.handler = handler
        self.name = name


class StoragePlugin(object):
    """
    Used to implements an alternative storage module to the SQLite included in quarterapp.

    To activate a storage plugin (there can only be one active storage plugin) the name
    of the plugin has to be entered as value for the setting "storage" in quarterapp.conf
    """
    
    def __init__(self, name, plugin):
        """
        Creates the plugin.

        Args:
            name: The plugin name (used in configuration file).
            plugin: Pointer to the class implementing quarterapp.storage.Storage class.
        """
        self.name = name
        self.plugin = plugin
