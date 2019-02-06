"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import gi
from dbus.mainloop.glib import DBusGMainLoop
from gettext import gettext as _s
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.ui.notificationarea import timekprNotificationArea

# set up dbus main loop
DBusGMainLoop(set_as_default=True)

# status icon stuff
_USE_STATUSICON = True


class timekprIndicator(timekprNotificationArea):
    """Support appindicator"""

    def __init__(self, pLog, pIsDevActive, pUserName, pGUIResourcePath):
        """Init all required stuff for indicator"""
        # init logging firstly
        log.setLogging(pLog, pClient=True)

        log.log(cons.TK_LOG_LEVEL_INFO, "start initTimekprSystrayIcon")

        # only if this is supported
        if self.isSupported():
            # init parent as well
            super().__init__(pLog, pIsDevActive, pUserName, pGUIResourcePath)

            # this is our icon
            self._tray = None

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initTimekprSystrayIcon")

    def isSupported(self):
        """Get whether appindicator is supported"""
        global _USE_STATUSICON
        # returns whether we can use appindicator
        return _USE_STATUSICON

    def initTimekprIcon(self, pShowSeconds):
        """Initialize timekpr indicator"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start initTimekprStatusIcon")

        # show secs
        self._showSeconds = pShowSeconds

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
             ("TimeLeft", Gtk.STOCK_INFO, _s("Time left..."), None, None, super().invokeTimekprTimeLeft)
            ,("Properties", Gtk.STOCK_PROPERTIES, None, None, None, super().invokeTimekprUserProperties)
            # ,("Timekpr-GUI", Gtk.STOCK_PREFERENCES, _s("Timekpr administration"), None, None, self.on_timekpr_gui)
            ,("About", Gtk.STOCK_ABOUT, None, None, None, super().invokeTimekprAbout)
        ])

        # build up menu
        timekprUIManager = Gtk.UIManager()
        timekprUIManager.add_ui_from_string(timekprMenu)
        timekprUIManager.insert_action_group(timekprActionGroup)
        self._popup = timekprUIManager.get_widget("/timekprPopupMenu")

        # initial config
        self.setTimeLeft("", None)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initTimekprStatusIcon")

    def setTimeLeft(self, pPriority, pTimeLeft):
        """Set time left in the indicator"""
        # make strings to set
        timeLeft, icon = super().setTimeLeft(pPriority, pTimeLeft)
        # change the label and icons
        self.changeTimeLeft(timeLeft, icon)

    def changeTimeLeft(self, pTimeLeftStr, pTimekprIcon):
        """Change time things for indicator"""
        # if we have smth to set
        if pTimeLeftStr is not None:
            # set time left (this works with indicator in unity and gnome)
            self._tray.set_tooltip_text(pTimeLeftStr)

        # if we have smth to set
        if pTimekprIcon is not None:
            # set up the icon
            self._tray.set_from_file(pTimekprIcon)

    def onTimekprMenu(self, status, button, time):
        """Show popup menu for tray"""
        self._popup.popup(None, None, None, None, 0, time)
