"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import dbus
import os
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
from datetime import datetime

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc
from timekpr.client.interface.speech.espeak import timekprSpeech
from timekpr.common.constants import messages as msg

# default loop
DBusGMainLoop(set_as_default=True)


class timekprNotifications(object):
    """Main class for supporting indicator notifications, connect to request methods for timekpr and connections to other DBUS modules"""

    def __init__(self, pUserName, pTimekprClientConfig):
        """Initialize notifications"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr notifications")

        # uname
        self._userName = pUserName
        self._timekprClientConfig = pTimekprClientConfig

        # notification (to replace itself in case they are incoming fast)
        self._lastNotifId = 0
        self._lastNotifDT = datetime.now()
        self._lastPTNotifId = 0
        self._lastPTNotifDT = datetime.now()

        # session bus
        self._userSessionBus = dbus.SessionBus()
        # timekpr bus
        self._timekprBus = (dbus.SessionBus() if (cons.TK_DEV_ACTIVE and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())

        # DBUS client connections
        # connection types
        self.CL_CONN_TK = "timekpr"
        self.CL_CONN_NOTIF = "notifications"
        self.CL_CONN_SCR = "screensaver"
        # constants
        self.CL_IF = "primary interface"
        self.CL_IFA = "attributes interface"
        self.CL_SI = "signal"
        self.CL_CNT = "retry_count"
        self.CL_DEL = "delay_times"

        # object collection for DBUS connections
        self._dbusConnections = {
            self.CL_CONN_TK: {self.CL_IF: None, self.CL_IFA: None, self.CL_SI: None, self.CL_CNT: 999, self.CL_DEL: 0},
            self.CL_CONN_NOTIF: {self.CL_IF: None, self.CL_IFA: None, self.CL_SI: None, self.CL_CNT: 99, self.CL_DEL: 0},
            self.CL_CONN_SCR: {self.CL_IF: None, self.CL_IFA: None, self.CL_SI: None, self.CL_CNT: 5, self.CL_DEL: 1}
        }

        # WORKAROUNDS section start
        # adjust even bigger delay with unity + 18.04 + HDD
        if "UNITY" in os.getenv("XDG_CURRENT_DESKTOP", "SUPERDESKTOP").upper():
            # more delay, race condition with screensaver?
            self._dbusConnections[self.CL_CONN_SCR][self.CL_DEL] += cons.TK_POLLTIME - 1
        # WORKAROUNDS section end

        # speech init
        self._timekprSpeechManager = None

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekpr notifications")

    def initClientConnections(self):
        """Init dbus (connect to session bus for notification)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start initClientConnections")

        # speech
        if self._timekprSpeechManager is None:
            # initialize
            self._timekprSpeechManager = timekprSpeech()
            # check if supported, if it is, initialize
            if self._timekprSpeechManager.isSupported():
                # initialize if supported
                self._timekprSpeechManager.initSpeech()

        # only if notifications are not ok
        if self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] is None and self._dbusConnections[self.CL_CONN_NOTIF][self.CL_CNT] > 0 and not self._dbusConnections[self.CL_CONN_NOTIF][self.CL_DEL] > 0:
            # define inames (I hope "revolutionary company" won't sue me for using i in front of variable names)
            iNames = ["org.freedesktop.Notifications"]
            iPaths = ["/org/freedesktop/Notifications"]

            # go through inames
            for idx in range(0, len(iNames)):
                # go through all possible interfaces
                try:
                    # dbus performance measurement
                    misc.measureTimeElapsed(pStart=True)
                    # getting interface
                    self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] = dbus.Interface(self._userSessionBus.get_object(iNames[idx], iPaths[idx]), iNames[idx])
                    # measurement logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (iNames[idx], misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                    # first sucess is enough
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "CONNECTED to DBUS %s interface" % (self.CL_CONN_NOTIF))
                    # check capabilities
                    if "sound" not in self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF].GetCapabilities():
                        # sound is not available
                        self._timekprClientConfig.setIsNotificationSoundSupported(False)
                    # finish
                    break
                except Exception as dbusEx:
                    self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] = None
                    # logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection (%s, %s) ===---" % (self.CL_CONN_NOTIF, iNames[idx]))
                    log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING ===---")

        # only if screensaver is not ok
        if self._dbusConnections[self.CL_CONN_SCR][self.CL_IF] is None and self._dbusConnections[self.CL_CONN_SCR][self.CL_CNT] > 0 and not self._dbusConnections[self.CL_CONN_SCR][self.CL_DEL] > 0:
            # define inames (I hope "revolutionary company" won't sue me for using i in front of variable names :) )
            iNames = []
            iPaths = []
            chosenIdx = None

            # THIS WHOLE SECTION IS WORKAROUNDS FOR MULTIPLE VARIETIES OF SCREENSAVER IMPLEMENTATIONS - START
            # they must be compatible to freedekstop standard, e.g. have corect naming and at least GetActive method

            # get current DE
            currentDE = os.getenv("XDG_CURRENT_DESKTOP", "SUPERDESKTOP").upper()
            # workarounds per desktop
            for rIdx in range(0, len(cons.TK_SCR_XDGCD_OVERRIDE)):
                # check desktops
                if cons.TK_SCR_XDGCD_OVERRIDE[rIdx][0] in currentDE:
                    log.log(cons.TK_LOG_LEVEL_INFO, "INFO: using %s screensaver dbus interface as a workaround" % (cons.TK_SCR_XDGCD_OVERRIDE[rIdx][1]))
                    # use gnome stuff
                    iNames.extend(["org.%s.ScreenSaver" % (cons.TK_SCR_XDGCD_OVERRIDE[rIdx][1])])
                    iPaths.extend(["/org/%s/ScreenSaver" % (cons.TK_SCR_XDGCD_OVERRIDE[rIdx][1])])
                    # first match is enough
                    break

            # add default section with the actual standard
            iNames.extend(["org.freedesktop.ScreenSaver"])
            iPaths.extend(["/org/freedesktop/ScreenSaver"])

            # if only freedesktop is in the list, try one more fallback to gnome
            if len(iNames) < 2:
                # add default section
                iNames.extend(["org.gnome.ScreenSaver"])
                iPaths.extend(["/org/gnome/ScreenSaver"])

            # THIS WHOLE SECTION IS WORKAROUNDS FOR MULTIPLE VARIETIES OF SCREENSAVER IMPLEMENTATIONS - END

            # go through inames
            for idx in range(0, len(iNames)):
                # go through all possible interfaces
                try:
                    # dbus performance measurement
                    misc.measureTimeElapsed(pStart=True)
                    # getting interface
                    self._dbusConnections[self.CL_CONN_SCR][self.CL_IF] = dbus.Interface(self._userSessionBus.get_object(iNames[idx], iPaths[idx]), iNames[idx])
                    # verification (Gnome has not implemented freedesktop methods, we need to verify this actually works)
                    self._dbusConnections[self.CL_CONN_SCR][self.CL_IF].GetActive()
                    # measurement logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (iNames[idx], misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                    # first sucess is enough
                    chosenIdx = idx
                    # finish
                    break
                except Exception as dbusEx:
                    self._dbusConnections[self.CL_CONN_SCR][self.CL_IF] = None
                    # logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection (%s, %s) ===---" % (self.CL_CONN_SCR, iNames[idx]))
                    log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING ===---")

            # connection successful
            if self._dbusConnections[self.CL_CONN_SCR][self.CL_IF] is not None:
                # log
                log.log(cons.TK_LOG_LEVEL_DEBUG, "CONNECTED to DBUS %s (%s) interface" % (self.CL_CONN_SCR, iNames[chosenIdx]))
                # add a connection to signal
                self._dbusConnections[self.CL_CONN_SCR][self.CL_SI] = self._userSessionBus.add_signal_receiver(
                    path             = iPaths[chosenIdx],
                    handler_function = self.receiveScreenSaverActivityChange,
                    dbus_interface   = iNames[chosenIdx],
                    signal_name      = "ActiveChanged")

        # only if screensaver is not ok
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is None and self._dbusConnections[self.CL_CONN_TK][self.CL_CNT] > 0 and not self._dbusConnections[self.CL_CONN_TK][self.CL_DEL] > 0:
            try:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)
                # getting interface
                self._dbusConnections[self.CL_CONN_TK][self.CL_IF] = dbus.Interface(self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH), cons.TK_DBUS_USER_LIMITS_INTERFACE)
                # log
                log.log(cons.TK_LOG_LEVEL_DEBUG, "CONNECTED to %s DBUS %s interface" % (self.CL_CONN_TK, self.CL_IF))
                # getting interface
                self._dbusConnections[self.CL_CONN_TK][self.CL_IFA] = dbus.Interface(self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH), cons.TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE)
                # log
                log.log(cons.TK_LOG_LEVEL_DEBUG, "CONNECTED to %s DBUS %s interface" % (self.CL_CONN_TK, self.CL_IFA))

                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_LIMITS_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
            except Exception as dbusEx:
                # reset
                self._dbusConnections[self.CL_CONN_TK][self.CL_IF] = None
                self._dbusConnections[self.CL_CONN_TK][self.CL_IFA] = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection (%s, %s) ===---" % (self.CL_CONN_TK, cons.TK_DBUS_BUS_NAME))
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING ===---")

        # retry?
        doRetry = False
        # all variants
        for rConn in (self.CL_CONN_TK, self.CL_CONN_NOTIF, self.CL_CONN_SCR):
            # if either of this fails, we keep trying to connect
            if self._dbusConnections[rConn][self.CL_IF] is None:
                # max retries
                if self._dbusConnections[rConn][self.CL_CNT] > 0:
                    # only if delay is ended
                    if not self._dbusConnections[rConn][self.CL_DEL] > 0:
                        # decrease retries
                        self._dbusConnections[rConn][self.CL_CNT] -= 1
                    # continue if more retries available
                    if self._dbusConnections[rConn][self.CL_CNT] > 0:
                        # retry
                        doRetry = True
                        # do not take into account delay
                        if self._dbusConnections[rConn][self.CL_DEL] > 0:
                            # connection delayed
                            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: dbus connection to %s delayed for %d more times" % (rConn, self._dbusConnections[rConn][self.CL_DEL]))
                            # decrease delay
                            self._dbusConnections[rConn][self.CL_DEL] -= 1
                        else:
                            # logging
                            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: failed to connect to %s dbus, trying again..." % (rConn))
                    else:
                        # connection aborted
                        log.log(cons.TK_LOG_LEVEL_INFO, "WARNING: dbus connection to %s failed, some functionality will not be available" % (rConn))

        # retry
        if doRetry:
            # if either of this fails, we keep trying to connect
            GLib.timeout_add_seconds(cons.TK_POLLTIME, self.initClientConnections)
        # prepare notifications in case smth is not ok
        else:
            # let's inform user in case screensaver is not connected
            if self._dbusConnections[self.CL_CONN_SCR][self.CL_IF] is None and self._timekprClientConfig.getClientShowAllNotifications():
                # prepare notification
                self.notifyUser(cons.TK_MSG_CODE_FEATURE_SCR_NOT_AVAILABLE_ERROR, None, cons.TK_PRIO_WARNING, pAdditionalMessage=self.CL_CONN_SCR)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish initClientConnections")

        # finish
        return False

    def isTimekprConnected(self):
        """Return status of timekpr connection (nothing else, just timekpr itself)"""
        return self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is not None

    def _prepareNotification(self, pMsgCode, pMsgType, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Prepare the message to be sent to dbus notifications"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start prepareNotification")

        # determine icon to use
        timekprIcon = cons.TK_PRIO_CONF[cons.getNotificationPrioriy(pPriority)][cons.TK_ICON_NOTIF]
        timekprPrio = cons.TK_PRIO_CONF[cons.getNotificationPrioriy(pPriority)][cons.TK_DBUS_PRIO]

        # calculate hours in advance
        if pTimeLeft is not None:
            timeLeftHours = (pTimeLeft - cons.TK_DATETIME_START).days * 24 + pTimeLeft.hour

        # determine the message to pass
        if pMsgCode == cons.TK_MSG_CODE_TIMEUNLIMITED:
            # no limit
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_NOT_LIMITED")
        elif pMsgCode == cons.TK_MSG_CODE_TIMELEFT:
            # msg
            msgStr = " ".join((msg.getTranslation("TK_MSG_NOTIFICATION_TIME_LEFT_1", timeLeftHours), msg.getTranslation("TK_MSG_NOTIFICATION_TIME_LEFT_2", pTimeLeft.minute), msg.getTranslation("TK_MSG_NOTIFICATION_PLAYTIME_LEFT_3" if pMsgType == "PlayTime" else "TK_MSG_NOTIFICATION_TIME_LEFT_3", pTimeLeft.second)))
        elif pMsgCode == cons.TK_MSG_CODE_TIMECRITICAL:
            # depending on type
            if pMsgType == cons.TK_CTRL_RES_L:
                msgCode = "TK_MSG_NOTIFICATION_TIME_IS_UP_1L"
            elif pMsgType in (cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W):
                msgCode = "TK_MSG_NOTIFICATION_TIME_IS_UP_1S"
            elif pMsgType == cons.TK_CTRL_RES_D:
                msgCode = "TK_MSG_NOTIFICATION_TIME_IS_UP_1D"
            else:
                msgCode = "TK_MSG_NOTIFICATION_TIME_IS_UP_1T"
            # msg
            msgStr = " ".join((msg.getTranslation(msgCode), msg.getTranslation("TK_MSG_NOTIFICATION_TIME_IS_UP_2", pTimeLeft.second)))
        elif pMsgCode == cons.TK_MSG_CODE_TIMELEFTCHANGED:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_ALLOWANCE_CHANGED")
        elif pMsgCode == cons.TK_MSG_CODE_TIMECONFIGCHANGED:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_CONFIGURATION_CHANGED")
        elif pMsgCode == cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_CANNOT_CONNECT") % (pAdditionalMessage)
        elif pMsgCode == cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_CANNOT_COMMUNICATE") % (pAdditionalMessage)
        elif pMsgCode == cons.TK_MSG_CODE_ICON_INIT_ERROR:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_CANNOT_INIT_ICON") % (pAdditionalMessage)
        elif pMsgCode == cons.TK_MSG_CODE_FEATURE_SCR_NOT_AVAILABLE_ERROR:
            # msg
            msgStr = msg.getTranslation("TK_MSG_NOTIFICATION_SCR_FEATURE_NOT_AVAILABLE") % (pAdditionalMessage)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish prepareNotification")

        # pass this back
        return timekprIcon, msgStr, timekprPrio

    def notifyUser(self, pMsgCode, pMsgType, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Notify the user."""
        # if we have dbus connection, let"s do so
        if self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] is None:
            # init
            self.initClientConnections()

        # can we notify user
        if self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] is not None:
            # prepare notification
            timekprIcon, msgStr, timekprPrio = self._prepareNotification(pMsgCode, pMsgType, pPriority, pTimeLeft, pAdditionalMessage)

            # defaults
            hints = {"urgency": timekprPrio}

            # notification params based on criticality
            if pPriority in (cons.TK_PRIO_CRITICAL, cons.TK_PRIO_IMPORTANT):
                # timeout
                notificationTimeout = self._timekprClientConfig.getClientNotificationTimeoutCritical()
                # sound
                if self._timekprClientConfig.getIsNotificationSoundSupported() and self._timekprClientConfig.getClientUseNotificationSound():
                    # add sound hint
                    hints["sound-file"] = cons.TK_CL_NOTIF_SND_FILE_CRITICAL
            else:
                # timeout
                notificationTimeout = self._timekprClientConfig.getClientNotificationTimeout()
                # sound
                if self._timekprClientConfig.getIsNotificationSoundSupported() and self._timekprClientConfig.getClientUseNotificationSound():
                    # add sound hint
                    hints["sound-file"] = cons.TK_CL_NOTIF_SND_FILE_WARN

            # calculate last time notification is shown (if this is too recent - replace, otherwise add new notification)
            if pMsgType == "PlayTime" and self._lastPTNotifId != 0 and (datetime.now() - self._lastPTNotifDT).total_seconds() >= notificationTimeout:
                self._lastPTNotifId = 0
            elif pMsgType != "PlayTime" and self._lastNotifId != 0 and (datetime.now() - self._lastNotifDT).total_seconds() >= notificationTimeout:
                self._lastNotifId = 0

            # calculate notification values
            notificationTimeout = min(cons.TK_CL_NOTIF_MAX, max(0, notificationTimeout)) * 1000

            # notification value of 0 means "forever"
            actions = ["Dismiss", "Dismiss"] if notificationTimeout == 0 else []

            log.log(cons.TK_LOG_LEVEL_DEBUG, "preshow: %s, %s, %i" % (msg.getTranslation("TK_MSG_NOTIFICATION_PLAYTIME_TITLE" if pMsgType == "PlayTime" else "TK_MSG_NOTIFICATION_TITLE"), msgStr, notificationTimeout))

            # notify through dbus
            try:
                # call dbus method
                notifId = self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF].Notify(
                    "Timekpr"
                    ,self._lastNotifId if pMsgType != "PlayTime" else self._lastPTNotifId
                    ,timekprIcon
                    ,msg.getTranslation("TK_MSG_NOTIFICATION_PLAYTIME_TITLE" if pMsgType == "PlayTime" else "TK_MSG_NOTIFICATION_TITLE")
                    ,msgStr
                    ,actions
                    ,hints
                    ,notificationTimeout
                )
            except Exception as dbusEx:
                # we cannot send notif through dbus
                self._dbusConnections[self.CL_CONN_NOTIF][self.CL_IF] = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")

            # save notification ID (only if message is not about PlayTime, otherwise it may dismiss standard time or vice versa)
            if pMsgType == "PlayTime":
                self._lastPTNotifId = notifId
                self._lastPTNotifDT = datetime.now()
            else:
                self._lastNotifId = notifId
                self._lastNotifDT = datetime.now()

            # user wants to hear things
            if self._timekprClientConfig.getIsNotificationSpeechSupported() and self._timekprClientConfig.getClientUseSpeechNotifications():
                # say that out loud
                self._timekprSpeechManager.saySmth(msgStr)

    # --------------- admininstration / verification methods --------------- #

    def verifySessionAttributes(self, pWhat, pKey):
        """Receive the signal and process the data"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "prepare verification of attributes for server: %s, %s" % (pWhat, "key"))
        # def
        value = None

        # for screensaver status
        if pWhat == cons.TK_CTRL_SCR_N:
            # value
            value = str(bool(self._dbusConnections[self.CL_CONN_SCR][self.CL_IF].GetActive()))

        # resend stuff to server
        self.processUserSessionAttributes(pWhat, pKey, value)

    # --------------- admininstration / verification signals --------------- #

    def receiveScreenSaverActivityChange(self, pIsActive):
        """Receive the signal and process the data"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive screensaver activity changes: %s" % (str(bool(pIsActive))))

        # request to server for verification
        self.processUserSessionAttributes(cons.TK_CTRL_SCR_N)

    # --------------- request methods to timekpr --------------- #

    def requestTimeLeft(self):
        """Request time left from server"""
        # if we have dbus connection, let"s do so
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timeleft")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._dbusConnections[self.CL_CONN_TK][self.CL_IF].requestTimeLeft(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, None, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we cannot send notif through dbus
                self._dbusConnections[self.CL_CONN_TK][self.CL_IF] = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, None, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))

    def requestTimeLimits(self):
        """Request time limits from server"""
        # if we have dbus connection, let"s do so
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IF] is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timelimits")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._dbusConnections[self.CL_CONN_TK][self.CL_IF].requestTimeLimits(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, None, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we cannot send notif through dbus
                self._dbusConnections[self.CL_CONN_TK][self.CL_IF] = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, None, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))

    def processUserSessionAttributes(self, pWhat, pKey=None, pValue=None):
        """Process user session attributes from server"""
        # if we have dbus connection, let"s do so
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IFA] is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._dbusConnections[self.CL_CONN_TK][self.CL_IFA] is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "%s session attributes" % ("requesting" if pKey is None else "verifying"))
            # notify through dbus
            try:
                # call dbus method
                result, message = self._dbusConnections[self.CL_CONN_TK][self.CL_IFA].processUserSessionAttributes(
                    self._userName,
                    dbus.String(pWhat if pWhat is not None else ""),
                    dbus.String(pKey if pKey is not None else ""),
                    dbus.String(pValue if pValue is not None else ""))

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, None, cons.TK_PRIO_CRITICAL, None, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we cannot send notif through dbus
                self._dbusConnections[self.CL_CONN_TK][self.CL_IF] = None
                self._dbusConnections[self.CL_CONN_TK][self.CL_IFA] = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, None, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))
