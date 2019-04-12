"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import gi
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.ui.notificationarea import timekprNotificationArea
from timekpr.common.constants import messages as msg

# indicator stuff
try:
    # try to load appindicator
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator

    # if successful, mar it so
    _USE_INDICATOR = True
except (ImportError, ValueError):
    # no indictor
    _USE_INDICATOR = False
    pass


class timekprIndicator(timekprNotificationArea):
    """Support appindicator"""

    def __init__(self, pLog, pIsDevActive, pUserName, pClientConfigManager):
        """Init all required stuff for indicator"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start initTimekprIndicator")

        # only if this is supported
        if self.isSupported():
            # init parent as well
            super().__init__(pLog, pIsDevActive, pUserName, pClientConfigManager)

            # this is our icon
            self._indicator = None

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initTimekprIndicator")

    def isSupported(self):
        """Get whether appindicator is supported"""
        global _USE_INDICATOR
        # returns whether we can use appindicator
        return _USE_INDICATOR

    def initTimekprIcon(self):
        """Initialize timekpr indicator"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start initTimekprIndicatorIcon")

        # init indicator itself (icon will be set later)
        self._indicator = AppIndicator.Indicator.new("indicator-timekpr", os.path.join(self._timekprConfigManager.getTimekprSharedDir(), "icons", cons.TK_PRIO_CONF["client-logo"][cons.TK_ICON_STAT]), AppIndicator.IndicatorCategory.APPLICATION_STATUS)
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        # define empty menu
        self._timekprMenu = Gtk.Menu()

        # add menu items
        self._timekprMenuItemTimeLeft = Gtk.MenuItem(msg.getTranslation("TK_MSG_MENU_TIME_LEFT"))
        self._timekprMenu.append(self._timekprMenuItemTimeLeft)
        self._timekprMenu.append(Gtk.SeparatorMenuItem())
        self._timekprMenuItemProperties = Gtk.MenuItem(msg.getTranslation("TK_MSG_MENU_CONFIGURATION"))
        self._timekprMenu.append(self._timekprMenuItemProperties)
        self._timekprMenu.append(Gtk.SeparatorMenuItem())
        self._timekprMenuItemAbout = Gtk.MenuItem(msg.getTranslation("TK_MSG_MENU_ABOUT"))
        self._timekprMenu.append(self._timekprMenuItemAbout)

        # enable all
        self._timekprMenu.show_all()

        # connect signal to code
        self._timekprMenuItemTimeLeft.connect("activate", super().invokeTimekprTimeLeft)
        self._timekprMenuItemProperties.connect("activate", super().invokeTimekprUserProperties)
        self._timekprMenuItemAbout.connect("activate", super().invokeTimekprAbout)

        # set menu to indicator
        self._indicator.set_menu(self._timekprMenu)

        # initial config
        self.setTimeLeft("", None)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initTimekprIndicatorIcon")

    def setTimeLeft(self, pPriority, pTimeLeft):
        """Set time left in the indicator"""
        # make strings to set
        timeLeft, icon = super().formatTimeLeft(pPriority, pTimeLeft)

        # if we have smth to set
        if timeLeft is not None:
            # set time left (this works with indicator in unity and gnome)
            self._indicator.set_label(timeLeft, "")

            # set time left (this works with indicator in kde5)
            self._indicator.set_title(timeLeft)

        # if we have smth to set
        if icon is not None:
            # set up the icon
            self._indicator.set_icon(icon)
