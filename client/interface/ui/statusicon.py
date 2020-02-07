"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.ui.notificationarea import timekprNotificationArea
from timekpr.common.constants import messages as msg

# status icon stuff
_USE_STATUSICON = True


class timekprIndicator(timekprNotificationArea):
    """Support appindicator"""

    def __init__(self, pLog, pIsDevActive, pUserName, pTimekprConfigManager):
        """Init all required stuff for indicator"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start initTimekprSystrayIcon")

        # only if this is supported
        if self.isSupported():
            # init parent as well
            super().__init__(pLog, pIsDevActive, pUserName, pTimekprConfigManager)

            # this is our icon
            self._tray = None

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initTimekprSystrayIcon")

    def isSupported(self):
        """Get whether appindicator is supported"""
        global _USE_STATUSICON
        # returns whether we can use appindicator
        return _USE_STATUSICON

    def initTimekprIcon(self):
        """Initialize timekpr indicator"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start initTimekprStatusIcon")

        # define our popupmenu
        timekprMenu = """
        <ui>
            <popup name="timekprPopupMenu">
                <menuitem action="TimeLeft"/>
                <separator/>
                <menuitem action="Limits &amp; configuration"/>
                <separator/>
                <menuitem action="About"/>
            </popup>
        </ui>
        """
        # <menuitem action="Timekpr-GUI"/>
        # <separator/>

        # set up tray
        self._tray = Gtk.StatusIcon()
        self._tray.set_visible(True)

        # connect to methods
        self._tray.connect("activate", super().invokeTimekprTimeLeft)
        self._tray.connect("popup-menu", self.onTimekprMenu)

        # build up menu actiongroups
        timekprActionGroup = Gtk.ActionGroup("timekprActions")
        timekprActionGroup.add_actions([
             ("TimeLeft", Gtk.STOCK_INFO, msg.getTranslation("TK_MSG_MENU_TIME_LEFT"), None, None, super().invokeTimekprTimeLeft)
            ,("Limits & configuration", Gtk.STOCK_PROPERTIES, msg.getTranslation("TK_MSG_MENU_CONFIGURATION"), None, None, super().invokeTimekprUserProperties)
            ,("About", Gtk.STOCK_ABOUT, msg.getTranslation("TK_MSG_MENU_ABOUT"), None, None, super().invokeTimekprAbout)
        ])

        # build up menu
        timekprUIManager = Gtk.UIManager()
        timekprUIManager.add_ui_from_string(timekprMenu)
        timekprUIManager.insert_action_group(timekprActionGroup)
        self._popup = timekprUIManager.get_widget("/timekprPopupMenu")

        # initial config
        self._tray.set_from_file(os.path.join(self._timekprConfigManager.getTimekprSharedDir(), "icons", cons.TK_PRIO_CONF["client-logo"][cons.TK_ICON_STAT]))
        self.setTimeLeft("", None)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish initTimekprStatusIcon")

    def setTimeLeft(self, pPriority, pTimeLeft):
        """Set time left in the indicator"""
        # make strings to set
        timeLeft, icon = super().formatTimeLeft(pPriority, pTimeLeft)

        # if we have smth to set
        if timeLeft is not None:
            # set time left
            self._tray.set_tooltip_text(timeLeft)
            self._tray.set_title(timeLeft)

        # if we have smth to set
        if icon is not None:
            # set up the icon
            self._tray.set_from_file(icon)

    def onTimekprMenu(self, status, button, time):
        """Show popup menu for tray"""
        self._popup.popup(None, None, None, None, 0, time)
