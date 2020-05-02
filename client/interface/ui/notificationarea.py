"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
from datetime import timedelta
import os

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.dbus.notifications import timekprNotifications
from timekpr.client.gui.clientgui import timekprGUI


class timekprNotificationArea(object):
    """Support appindicator or other means of showing icon on the screen (this class is a parent for classes like indicator or staticon)"""

    def __init__(self, pLog, pIsDevActive, pUserName, pTimekprConfigManager):
        """Init all required stuff for indicator"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr indicator")

        # dev
        self._isDevActive = pIsDevActive
        # configuration
        self._timekprConfigManager = pTimekprConfigManager

        # set version
        self._timekprVersion = "-.-.-"
        # set username
        self._userName = pUserName
        # initialize priority
        self._lastUsedPriority = ""
        # initialize time left
        self._timeLeftTotal = cons.TK_DATETIME_START + timedelta(seconds=cons.TK_LIMIT_PER_DAY - cons.TK_POLLTIME - 1)

        # init notificaction stuff
        self._timekprNotifications = timekprNotifications(pLog, self._isDevActive, self._userName, self._timekprConfigManager)

        # dbus
        self._timekprBus = None
        self._notifyObject = None
        self._notifyInterface = None

        # gui forms
        self._timekprGUI = timekprGUI(cons.TK_VERSION, self._timekprConfigManager, self._userName)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekpr indicator")

    def initClientConnections(self):
        """Proxy method for initialization"""
        # initalize DBUS connections to every additional module
        self._timekprNotifications.initClientConnections()

    def isTimekprConnected(self):
        """Proxy method for initialization status"""
        # check if main connection to timekpr is up
        return self._timekprNotifications.isTimekprConnected()

    def verifySessionAttributes(self, pWhat, pKey):
        """Proxy method for receive the signal and process the data"""
        self._timekprNotifications.verifySessionAttributes(pWhat, pKey)

    def requestTimeLimits(self):
        """Proxy method for request time limits from server"""
        self._timekprNotifications.requestTimeLimits()

    def requestTimeLeft(self):
        """Proxy method for request time left from server"""
        self._timekprNotifications.requestTimeLeft()

    def formatTimeLeft(self, pPriority, pTimeLeft):
        """Set time left in the indicator"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start formatTimeLeft")

        # prio
        prio = pPriority
        timekprIcon = None
        timeLeftStr = None

        # if time has changed
        if self._timeLeftTotal != pTimeLeft:
            # if there is no time left set yet, show --
            if pTimeLeft is None:
                # determine hours and minutes
                timeLeftStr = "--:--" + (":--" if self._timekprConfigManager.getClientShowSeconds() else "")
            else:
                # determine whether we have an unlimited mode
                isUnlimited = self.isWholeDayAvailable(self._timeLeftTotal) == self.isWholeDayAvailable(pTimeLeft) and self.isWholeDayAvailable(pTimeLeft)

                # update time
                self._timeLeftTotal = pTimeLeft

                # if unlimited, we do not need to chnage anything
                if isUnlimited:
                    # just pass
                    pass
                # if no limit there will be a no limit thing
                elif self.isWholeDayAvailable(self._timeLeftTotal):
                    # unlimited!
                    timeLeftStr = "∞"
                    prio = "unlimited"
                else:
                    # determine hours and minutes
                    timeLeftStr = str((self._timeLeftTotal - cons.TK_DATETIME_START).days * 24 + self._timeLeftTotal.hour).rjust(2, "0")
                    timeLeftStr += ":" + str(self._timeLeftTotal.minute).rjust(2, "0")
                    timeLeftStr += ((":" + str(self._timeLeftTotal.second).rjust(2, "0")) if self._timekprConfigManager.getClientShowSeconds() else "")

            # now, if priority changes, set up icon as well
            if self._lastUsedPriority != prio:
                # set up last used prio
                self._lastUsedPriority = pPriority

                # get status icon
                timekprIcon = os.path.join(self._timekprConfigManager.getTimekprSharedDir(), "icons", cons.TK_PRIO_CONF[cons.getNotificationPrioriy(prio)][cons.TK_ICON_STAT])

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish formatTimeLeft")

        # return time left and icon (if changed), so implementations can use it
        return timeLeftStr, timekprIcon

    def notifyUser(self, pMsgCode, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Notify user (a wrapper call)"""
        # if we have dbus connection, let's do so
        self._timekprNotifications.notifyUser(pMsgCode, pPriority, pTimeLeft, pAdditionalMessage)

    def setStatus(self, pStatus):
        """Change status of timekpr"""
        return self._timekprGUI.setStatus(pStatus)

    def isWholeDayAvailable(self, pTimeLeft):
        """Check if whole day is available from timeleft"""
        return (pTimeLeft - cons.TK_DATETIME_START).total_seconds() >= (cons.TK_LIMIT_PER_DAY - cons.TK_POLLTIME)

    # --------------- user clicked methods --------------- #

    def invokeTimekprTimeLeft(self, pEvent):
        """Inform user about (almost) exact time left"""
        # inform user about precise time
        self.notifyUser((cons.TK_MSG_CODE_TIMEUNLIMITED if self.isWholeDayAvailable(self._timeLeftTotal) else cons.TK_MSG_CODE_TIMELEFT), self._lastUsedPriority, self._timeLeftTotal)

    def invokeTimekprUserProperties(self, pEvent):
        """Bring up a window for property editing"""
        # show limits and config
        self._timekprGUI.initConfigForm()

    def invokeTimekprAbout(self, pEvent):
        """Bring up a window for timekpr configration (this needs elevated privileges to do anything)"""
        # show about
        self._timekprGUI.initAboutForm()

    # --------------- configuration update methods --------------- #

    def renewUserLimits(self, pTimeLeft):
        """Call an update to renew time left"""
        # pass this to actual gui storage
        self._timekprGUI.renewLimits(pTimeLeft)

    def renewLimitConfiguration(self, pLimits):
        """Call an update on actual limits"""
        # pass this to actual gui storage
        self._timekprGUI.renewLimitConfiguration(pLimits)
