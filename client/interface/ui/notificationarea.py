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

    def __init__(self, pUserName, pUserNameFull, pTimekprClientConfig):
        """Init all required stuff for indicator"""

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr indicator")

        # configuration
        self._timekprClientConfig = pTimekprClientConfig

        # set version
        self._timekprVersion = "-.-.-"
        # set username
        self._userName = pUserName
        # initialize priority
        self._lastUsedPriority = ""
        # priority level
        self._lastUsedPriorityLvl = -1
        # PlayTime priority level
        self._lastUsedPTPriorityLvl = -1
        # initialize time left
        self._timeLeftTotal = None
        # initialize time limit
        self._timeNotLimited = 0

        # init notificaction stuff
        self._timekprNotifications = timekprNotifications(self._userName, self._timekprClientConfig)

        # dbus
        self._timekprBus = None
        self._notifyObject = None
        self._notifyInterface = None

        # gui forms
        self._timekprGUI = timekprGUI(cons.TK_VERSION, self._timekprClientConfig, self._userName, pUserNameFull)

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

    def _determinePriority(self, pType, pPriority, pTimeLeft):
        """Determine priority based on client config"""
        # def
        finalPrio = pPriority
        finalLimitSecs = -1
        # keep in mind that this applies to timeLeft only and critical notifications can STILL be pushed from server
        if pTimeLeft is not None:
            # calculate
            for rPrio in self._timekprClientConfig.getClientNotificationLevels() if pType == "Time" else self._timekprClientConfig.getClientPlayTimeNotificationLevels():
                # determine which is the earliest priority level we need to use
                # it is determined as time left is less then this interval
                if rPrio[0] >= pTimeLeft and (finalLimitSecs > rPrio[0] or finalLimitSecs < 0):
                    # determine if this is the gratest level that is lower than limit
                    finalLimitSecs = rPrio[0]
                    finalPrio = cons.TK_PRIO_LVL_MAP[rPrio[1]]
        # final priority
        return finalPrio, finalLimitSecs

    def formatTimeLeft(self, pPriority, pTimeLeft, pTimeNotLimited):
        """Set time left in the indicator"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start formatTimeLeft")

        # prio
        prio = pPriority
        timekprIcon = None
        timeLeftStr = None

        # if time has changed
        if self._timeLeftTotal != pTimeLeft or pTimeLeft is None:
            # if there is no time left set yet, show --
            if pTimeLeft is None:
                # determine hours and minutes
                timeLeftStr = "--:--" + (":--" if self._timekprClientConfig.getClientShowSeconds() else "")
            else:
                # update time
                self._timeLeftTotal = pTimeLeft
                self._timeNotLimited = pTimeNotLimited

                # unlimited has special icon and text (if it's not anymore, these will change)
                if self._timeNotLimited > 0:
                    # unlimited!
                    timeLeftStr = "∞"
                    prio = "unlimited"
                else:
                    # determine hours and minutes
                    timeLeftStr = str((self._timeLeftTotal - cons.TK_DATETIME_START).days * 24 + self._timeLeftTotal.hour).rjust(2, "0")
                    timeLeftStr += ":" + str(self._timeLeftTotal.minute).rjust(2, "0")
                    timeLeftStr += ((":" + str(self._timeLeftTotal.second).rjust(2, "0")) if self._timekprClientConfig.getClientShowSeconds() else "")

                    # get user configured level and priority
                    prio, finLvl = self._determinePriority("Time", pPriority, (pTimeLeft - cons.TK_DATETIME_START).total_seconds())
                    # if level actually changed
                    if self._lastUsedPriorityLvl != finLvl:
                        # do not notify if this is the first invocation, because initial limits are already asked from server
                        # do not notify user in case icon is hidden and no notifications should be shown
                        if self._lastUsedPriorityLvl > 0 and self.getTrayIconEnabled():
                            # emit notification
                            self.notifyUser(cons.TK_MSG_CODE_TIMELEFT, None, prio, pTimeLeft, None)
                        # level this up
                        self._lastUsedPriorityLvl = finLvl

                # now, if priority changes, set up icon as well
                if self._lastUsedPriority != prio:
                    # set up last used prio
                    self._lastUsedPriority = prio
                    # get status icon
                    timekprIcon = os.path.join(self._timekprClientConfig.getTimekprSharedDir(), "icons", cons.TK_PRIO_CONF[cons.getNotificationPrioriy(prio)][cons.TK_ICON_STAT])

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish formatTimeLeft")

        # return time left and icon (if changed), so implementations can use it
        return timeLeftStr, timekprIcon

    def processPlayTimeNotifications(self, pTimeLimits):
        """Process PlayTime notifications (if there is PT info in limits)"""
        isPTInfoEnabled = self._timekprGUI.isPlayTimeAccountingInfoEnabled()
        # determine whether we actually need to process PlayTime
        if cons.TK_CTRL_PTLSTC in pTimeLimits and cons.TK_CTRL_PTLPD in pTimeLimits and cons.TK_CTRL_PTTLO in pTimeLimits:
            # only of not enabled
            if not isPTInfoEnabled:
                self._timekprGUI.setPlayTimeAccountingInfoEnabled(True)
            # get user configured level and priority
            prio, finLvl = self._determinePriority("PlayTime", cons.TK_PRIO_LOW, pTimeLimits[cons.TK_CTRL_PTLPD])
            # if any priority is effective, determine whether we need to inform user
            if finLvl > 0 and self._lastUsedPTPriorityLvl != finLvl:
                # adjust level too
                self._lastUsedPTPriorityLvl = finLvl
                # if icon is hidden, do not show any notifications
                if self.getTrayIconEnabled():
                    # notify user
                    self._timekprNotifications.notifyUser(cons.TK_MSG_CODE_TIMELEFT, "PlayTime", prio, cons.TK_DATETIME_START + timedelta(seconds=pTimeLimits[cons.TK_CTRL_PTLPD]), None)
        elif isPTInfoEnabled:
            # disbale info
            self._timekprGUI.setPlayTimeAccountingInfoEnabled(False)

    def notifyUser(self, pMsgCode, pMsgType, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Notify user (a wrapper call)"""
        # prio
        prio = pPriority
        # for time left, we need to determine final priority accoriding to user defined priority (if not defined, that will come from server)
        if pMsgCode == cons.TK_MSG_CODE_TIMELEFT:
            # get user configured level and priority
            prio, finLvl = self._determinePriority("Time", pPriority, (pTimeLeft - cons.TK_DATETIME_START).total_seconds())
        #  notify user
        self._timekprNotifications.notifyUser(pMsgCode, pMsgType, prio, pTimeLeft, pAdditionalMessage)

    def setStatus(self, pStatus):
        """Change status of timekpr"""
        return self._timekprGUI.setStatus(pStatus)

    # --------------- user clicked methods --------------- #

    def invokeTimekprTimeLeft(self, pEvent):
        """Inform user about (almost) exact time left"""
        # inform user about precise time
        self.notifyUser((cons.TK_MSG_CODE_TIMEUNLIMITED if self._timeNotLimited > 0 else cons.TK_MSG_CODE_TIMELEFT), None, self._lastUsedPriority, self._timeLeftTotal)

    def invokeTimekprUserProperties(self, pEvent):
        """Bring up a window for property editing"""
        # show limits and config
        self._timekprGUI.initConfigForm()

    def invokeTimekprAbout(self, pEvent):
        """Bring up a window for timekpr configration (this needs elevated privileges to do anything)"""
        # show about
        self._timekprGUI.initAboutForm()

    # --------------- configuration update methods --------------- #

    def renewUserLimits(self, pTimeInformation):
        """Call an update to renew time left"""
        # pass this to actual gui storage
        self._timekprGUI.renewLimits(pTimeInformation)

    def renewLimitConfiguration(self, pLimits):
        """Call an update on actual limits"""
        # pass this to actual gui storage
        self._timekprGUI.renewLimitConfiguration(pLimits)
