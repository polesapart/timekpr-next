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
        self._lastUsedPriority = self._lastUsedServerPriority = ""
        # priority level
        self._lastUsedPriorityLvl = -99
        # PlayTime priority level
        self._lastUsedPTPriorityLvl = -99
        # initialize time left
        self._timeLeftTotal = None
        # initialize PlayTime left
        self._playTimeLeftTotal = None
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

    def formatTimeLeft(self, pPriority, pTimeLeft, pTimeNotLimited, pPlayTimeLeft=None):
        """Set time left in the indicator"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start formatTimeLeft")

        # prio
        prio = pPriority
        timekprIcon = None
        timeLeftStr = None
        isTimeChanged = self._timeLeftTotal != pTimeLeft
        isPlayTimeChanged = self._playTimeLeftTotal != pPlayTimeLeft

        # determine hours and minutes for PlayTime (if there is such time)
        if (isTimeChanged or isPlayTimeChanged) and pPlayTimeLeft is not None and pTimeLeft is not None:
            # get the smallest one
            timeLeftPT = min(pPlayTimeLeft, pTimeLeft)
            # determine hours and minutes
            timeLeftStrPT = str((timeLeftPT - cons.TK_DATETIME_START).days * 24 + timeLeftPT.hour).rjust(2, "0")
            timeLeftStrPT += ":" + str(timeLeftPT.minute).rjust(2, "0")
            timeLeftStrPT += ((":" + str(timeLeftPT.second).rjust(2, "0")) if self._timekprClientConfig.getClientShowSeconds() else "")

        # execute time and icon changes + notifications only when there are changes
        if isTimeChanged or isPlayTimeChanged or pTimeLeft is None or self._lastUsedServerPriority != pPriority:
            # if there is no time left set yet, show --
            if pTimeLeft is None:
                # determine hours and minutes
                timeLeftStr = "--:--" + (":--" if self._timekprClientConfig.getClientShowSeconds() else "")
            else:
                # update time
                self._timeLeftTotal = pTimeLeft
                self._playTimeLeftTotal = pPlayTimeLeft
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

                    # notifications and icons only when time has changed
                    if isTimeChanged:
                        # get user configured level and priority
                        prio, finLvl = (pPriority, -1) if pPriority == cons.TK_PRIO_UACC else self._determinePriority("Time", pPriority, (pTimeLeft - cons.TK_DATETIME_START).total_seconds())

                        # if level actually changed
                        if self._lastUsedPriorityLvl != finLvl:
                            # do not notify if this is the first invocation, because initial limits are already asked from server
                            # do not notify user in case icon is hidden and no notifications should be shown
                            if self._lastUsedPriorityLvl > 0 and self.getTrayIconEnabled():
                                # emit notification
                                self.notifyUser(cons.TK_MSG_CODE_TIMELEFT, None, prio, pTimeLeft, None)
                            # level this up
                            self._lastUsedPriorityLvl = finLvl

                # determine hours and minutes for PlayTime (if there is such time)
                if pPlayTimeLeft is not None:
                    # format final time string
                    timeLeftStr = "%s / %s" % (timeLeftStr, timeLeftStrPT)

                # now, if priority changes, set up icon as well
                if isTimeChanged and self._lastUsedPriority != prio:
                    # log
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "changing icon for level, old: %s, new: %s" % (self._lastUsedPriority, prio))
                    # set up last used prio
                    self._lastUsedPriority = prio
                    # get status icon
                    timekprIcon = os.path.join(self._timekprClientConfig.getTimekprSharedDir(), "icons", cons.TK_PRIO_CONF[cons.getNotificationPrioriy(self._lastUsedPriority)][cons.TK_ICON_STAT])

            # adjust server priority: server sends all time left messages with low priority, except when there is no time left, then priority is critical
            self._lastUsedServerPriority = pPriority

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
            # log
            log.log(cons.TK_LOG_LEVEL_DEBUG, "process PT notif, prio: %s, prevLVL: %i, lvl: %i, icoena: %s" % (prio, self._lastUsedPTPriorityLvl, finLvl, self.getTrayIconEnabled()))
            # if any priority is effective, determine whether we need to inform user
            if (finLvl > 0 or self._lastUsedPTPriorityLvl < -1) and self._lastUsedPTPriorityLvl != finLvl and self.isTimekprConnected():
                # adjust level too
                self._lastUsedPTPriorityLvl = finLvl
                # if icon is hidden, do not show any notifications
                if self.getTrayIconEnabled():
                    # notify user
                    self._timekprNotifications.notifyUser(cons.TK_MSG_CODE_TIMELEFT, "PlayTime", prio, cons.TK_DATETIME_START + timedelta(seconds=min(pTimeLimits[cons.TK_CTRL_PTLPD], pTimeLimits[cons.TK_CTRL_LEFTD])), None)
        elif isPTInfoEnabled:
            # disable info (if it was enabled)
            log.log(cons.TK_LOG_LEVEL_DEBUG, "disable PT info tab")
            self._timekprGUI.setPlayTimeAccountingInfoEnabled(False)

    def notifyUser(self, pMsgCode, pMsgType, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Notify user (a wrapper call)"""
        # prio
        prio = pPriority
        timeLeft = cons.TK_DATETIME_START if pTimeLeft is None else pTimeLeft
        # for time left, we need to determine final priority accoriding to user defined priority (if not defined, that will come from server)
        if pMsgCode == cons.TK_MSG_CODE_TIMELEFT:
            # get user configured level and priority
            prio, finLvl = self._determinePriority("Time", pPriority, (timeLeft - cons.TK_DATETIME_START).total_seconds())
        #  notify user
        self._timekprNotifications.notifyUser(pMsgCode, pMsgType, prio, timeLeft, pAdditionalMessage)

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
