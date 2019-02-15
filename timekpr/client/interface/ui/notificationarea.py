"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
from datetime import datetime, timedelta
import os

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.dbus.notifications import timekprNotifications
from timekpr.client.gui.clientgui import timekprGUI


class timekprNotificationArea(object):
    """Support appindicator or other means of showing icon on the screen (this class is a parent for classes like indicator or staticon)"""

    def __init__(self, pLog, pIsDevActive, pUserName, pGUIResourcePath):
        """Init all required stuff for indicator"""
        # init logging firstly
        log.setLogging(pLog, pClient=True)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr indicator")

        # dev
        self._isDevActive = pIsDevActive

        # set version
        self._timekprVersion = "-.-.-"
        # set username
        self._userName = pUserName
        # initialize priority
        self._lastUsedPriority = ""
        # initialize time left
        self._timeLeftTotal = cons.TK_DATETIME_START + timedelta(seconds=cons.TK_MAX_DAY_SECS)
        # critical notification (to replace itself)
        self._criticalNotif = 0
        # whether to show secnds in systray
        self._showSeconds = False
        # no limit level
        self._noLimit = False
        self._noLimitSet = False

        # init notificaction stuff
        self._timekprNotifications = timekprNotifications(pLog, self._isDevActive, self._userName)
        self._timekprNotifications.initClientNotifications()
        self._resourcePathIcons = os.path.join(pGUIResourcePath, "icons")
        self._resourcePathGUI = os.path.join(pGUIResourcePath, "client/forms")

        # dbus
        self._timekprBus = None
        self._notifyObject = None
        self._notifyInterface = None

        # gui forms
        self._timekprGUI = timekprGUI(cons.TK_VERSION, self._resourcePathGUI, self._userName)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekpr indicator")

    def setTimeLeft(self, pPriority, pTimeLeft):
        """Set time left in the indicator"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start setTimeLeft")

        # prio
        prio = pPriority
        timekprIcon = None
        timeLeftStr = None

        # if time has chnaged
        if self._timeLeftTotal != pTimeLeft and not self._noLimitSet:
            # if there is no time left set yet, show --
            if pTimeLeft is None:
                # determine hours and minutes
                timeLeftStr = "--:--" + (":--" if self._showSeconds else "")
            else:
                # update time
                self._timeLeftTotal = pTimeLeft

                # if no limit there will be a no limit thing
                if self._noLimit:
                    if not self._noLimitSet:
                        # unlimited!
                        timeLeftStr = "∞"
                        prio = "unlimited"
                        self._noLimitSet = True
                else:
                    # determine hours and minutes
                    timeLeftStr = str((self._timeLeftTotal - cons.TK_DATETIME_START).days * 24 + self._timeLeftTotal.hour).rjust(2, "0") + ":" + str(self._timeLeftTotal.minute).rjust(2, "0") + ((":" + str(self._timeLeftTotal.second).rjust(2, "0")) if self._showSeconds else "")

            # now, if priority changes, set up icon as well
            if self._lastUsedPriority != prio:
                # set up last used prio
                self._lastUsedPriority = pPriority

                # get status icon
                timekprIcon = os.path.join(self._resourcePathIcons, cons.TK_PRIO_CONF[cons.getNotificationPrioriy(prio)][cons.TK_ICON_STAT])

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish setTimeLeft")

        # return time left and icon (if changed), so implementations can use it
        return timeLeftStr, timekprIcon

    def notifyUser(self, pMsgCode, pPriority, pTimeLeft=None):
        """Notify user (a wrapper call)"""
        # if we have dbus connection, let's do so
        self._timekprNotifications.notifyUser(pMsgCode, pPriority, pTimeLeft)

    def getUserConfigChanged(self):
        """Get whether config has changed"""
        # result
        return self._timekprGUI.getUserConfigChanged()

    def setSetShowSeconds(self, pShowSeconds):
        """Get whether to show seconds (needed to know if check is toggled)"""
        # renew seconds
        self._showSeconds = pShowSeconds

    def setStatus(self, pStatus):
        """Change status of timekpr"""
        return self._timekprGUI.setStatus(pStatus)

    # --------------- user clicked methods --------------- #

    def invokeTimekprTimeLeft(self, pEvent):
        """Inform user about (almost) exact time left"""
        # inform user about precise time
        self.notifyUser((cons.TK_MSG_TIMEUNLIMITED if self._noLimit else cons.TK_MSG_TIMELEFT), self._lastUsedPriority, self._timeLeftTotal)

    def invokeTimekprUserProperties(self, pEvent):
        """Bring up a window for property editing"""
        # show limits and config
        self._timekprGUI.initConfigForm()

    def invokeTimekprConfigurator(self, pEvent):
        """Bring up a window for timekpr configration (this needs elevated privileges to do anything)"""
        # edit properties
        self._timekprNotifications.requestTimeLeft()
        pass

    def invokeTimekprAbout(self, pEvent):
        """Bring up a window for timekpr configration (this needs elevated privileges to do anything)"""
        # show about
        self._timekprGUI.initAboutForm()

    # --------------- configuration update methods --------------- #

    def renewUserConfiguration(self, pShowFirstNotification, pShowAllNotifications, pUseSpeechNotifications, pShowSeconds, pLoggingLevel):
        """Call and update method to renew configuration in the GUI"""
        # renew seconds
        self._showSeconds = pShowSeconds

        # pass this to actual GUI storage
        self._timekprGUI.renewUserConfiguration(pShowFirstNotification, pShowAllNotifications, pUseSpeechNotifications, pShowSeconds, pLoggingLevel)

    def renewUserLimits(self, pTimeLeft):
        """Call an update to renew time left"""
        # pass this to actual gui storage
        self._timekprGUI.renewLimits(pTimeLeft)

    def renewLimitConfiguration(self, pLimits):
        """Call an update on actual limits"""
        # current day
        currDay = str(datetime.now().isoweekday())
        # we can check limits only when this day has configuration
        if currDay in pLimits:
            # check the limit
            if pLimits[currDay][cons.TK_CTRL_LIMITD] >= cons.TK_MAX_DAY_SECS:
                # reconfigure labels
                self._noLimit = True
            else:
                # we do have limit :(
                self._noLimit = False
                # cancel unlimited
                self._noLimitSet = False
                # last used prio changed to smth
                self._lastUsedPriority = ""

        # pass this to actual gui storage
        self._timekprGUI.renewLimitConfiguration(pLimits)
