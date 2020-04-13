"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import dbus
import os
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc
from timekpr.client.interface.speech.espeak import timekprSpeech
from timekpr.common.constants import messages as msg

# default loop
DBusGMainLoop(set_as_default=True)


class timekprNotifications(object):
    """Main class for supporting indicator notifications"""

    def __init__(self, pLog, pIsDevActive, pUserName, pTimekprConfigManager):
        """Initialize notifications"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr notifications")

        # dev
        self._isDevActive = pIsDevActive

        # uname
        self._userName = pUserName
        self._timekprConfigManager = pTimekprConfigManager

        # critical notification (to replace itself)
        self._criticalNotif = 0

        # session bus
        self._userSessionBus = dbus.SessionBus()

        # dbus (notifications)
        self._notifyInterface = None
        # dbus (screensaver)
        self._screenSaverInterface = None
        self._screenSaverStateChangedSignal = None

        # dbus (timekpr)
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        self._timekprLimitsInterface = None
        self._timekprAttributesInterface = None

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

        # only if notifications are ok
        if self._notifyInterface is None:
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
                    self._notifyInterface = dbus.Interface(self._userSessionBus.get_object(iNames[idx], iPaths[idx]), iNames[idx])
                    # measurement logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (iNames[idx], misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                    # first sucess is enough
                    break
                except Exception as dbusEx:
                    self._notifyInterface = None
                    # logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection ===---")
                    log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection ===---")

            # connection successful
            if self._notifyInterface is not None:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "connected to DBUS notification interface")

        # only if screensaver are ok
        if self._screenSaverInterface is None:
            # define inames (I hope "revolutionary company" won't sue me for using i in front of variable names)
            iNames = []
            iPaths = []
            chosenIdx = None

            # workarounds per desktop
            for rDesk in cons.TK_SCR_XDGCD_OVERRIDE:
                if rDesk in os.getenv("XDG_CURRENT_DESKTOP", "SUPERDESKTOP").upper():
                    log.log(cons.TK_LOG_LEVEL_INFO, "INFO: using gnome screensaver dbus interface as a workaround")
                    # use gnome stuff
                    iNames.extend(["org.gnome.ScreenSaver"])
                    iPaths.extend(["/org/gnome/ScreenSaver"])
                    # first match is enough
                    break

            # if there are no workarounds add default section, the preference is freedesktop standard, the rest is added in case standard can not be used
            if len(iNames) < 1:
                # add default section
                iNames.extend(["org.freedesktop.ScreenSaver", "org.gnome.ScreenSaver"])
                iPaths.extend(["/org/freedesktop/ScreenSaver", "/org/gnome/ScreenSaver"])

            # go through inames
            for idx in range(0, len(iNames)):
                # go through all possible interfaces
                try:
                    # dbus performance measurement
                    misc.measureTimeElapsed(pStart=True)
                    # getting interface
                    self._screenSaverInterface = dbus.Interface(self._userSessionBus.get_object(iNames[idx], iPaths[idx]), iNames[idx])
                    # verification (Gnome has not implemented freedesktop methods, we need to verify this actually works)
                    self._screenSaverInterface.GetActive()
                    # measurement logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (iNames[idx], misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                    # first sucess is enough
                    chosenIdx = idx
                    break
                except Exception as dbusEx:
                    self._screenSaverInterface = None
                    # logging
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection ===---")
                    log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                    log.log(cons.TK_LOG_LEVEL_INFO, "--=== WARNING initiating dbus connection ===---")

            # connection successful
            if self._screenSaverInterface is not None:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "connected to DBUS screensaver interface")
                # add a connection to signal
                self._screenSaverStateChangedSignal = self._userSessionBus.add_signal_receiver(
                     path             = iPaths[chosenIdx]
                    ,handler_function = self.receiveScreenSaverActivityChange
                    ,dbus_interface   = iNames[chosenIdx]
                    ,signal_name      = "ActiveChanged")

            # only if notifications are ok
        if self._timekprLimitsInterface is None:
            try:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)
                # getting interface
                self._timekprLimitsInterface = dbus.Interface(self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH), cons.TK_DBUS_USER_LIMITS_INTERFACE)
                # getting interface
                self._timekprAttributesInterface = dbus.Interface(self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH), cons.TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_LIMITS_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                log.log(cons.TK_LOG_LEVEL_DEBUG, "connected to DBUS timekpr interface")
            except Exception as dbusEx:
                self._timekprLimitsInterface = None
                self._timekprAttributesInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating timekpr dbus connection ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating timekpr dbus connection ===---")

        # if either of this fails, we keep trying to connect
        if self._notifyInterface is None or self._timekprLimitsInterface is None or self._screenSaverInterface is None:
            if self._notifyInterface is None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: failed to connect to notifications dbus, trying again...")
            if self._screenSaverInterface is None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: failed to connect to screensaver dbus, trying again...")
            if self._timekprLimitsInterface is None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: failed to connect to timekpr dbus, trying again...")

            # if either of this fails, we keep trying to connect
            GLib.timeout_add_seconds(3, self.initClientConnections)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish initClientConnections")

        # finish
        return False

    def prepareNotification(self, pMsgCode, pPriority, pTimeLeft=None, pAdditionalMessage=None):
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
            msgStr = " ".join((msg.getTranslation("TK_MSG_NOTIFICATION_TIME_LEFT_1", timeLeftHours), msg.getTranslation("TK_MSG_NOTIFICATION_TIME_LEFT_2", pTimeLeft.minute), msg.getTranslation("TK_MSG_NOTIFICATION_TIME_LEFT_3", pTimeLeft.second)))
        elif pMsgCode == cons.TK_MSG_CODE_TIMECRITICAL:
            # msg
            msgStr = " ".join((msg.getTranslation("TK_MSG_NOTIFICATION_TIME_IS_UP_1"), msg.getTranslation("TK_MSG_NOTIFICATION_TIME_IS_UP_2", pTimeLeft.second)))
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

        # save notification ID
        notifId = self._criticalNotif

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish prepareNotification")

        # pass this back
        return notifId, timekprIcon, msgStr, timekprPrio

    def notifyUser(self, pMsgCode, pPriority, pTimeLeft=None, pAdditionalMessage=None):
        """Notify the user."""
        # if we have dbus connection, let"s do so
        if self._notifyInterface is None:
            # init
            self.initClientConnections()

        # can we notify user
        if self._notifyInterface is not None:
            # prepare notification
            notifId, timekprIcon, msgStr, timekprPrio = self.prepareNotification(pMsgCode, pPriority, pTimeLeft, pAdditionalMessage)

            # notify through dbus
            try:
                # call dbus method
                notifId = self._notifyInterface.Notify("Timekpr", notifId, timekprIcon, msg.getTranslation("TK_MSG_NOTIFICATION_TITLE"), msgStr, "", {"urgency": timekprPrio}, 2500)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._notifyInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")

            # save notification ID (to replace it)
            self._criticalNotif = notifId

            # user wants to hear things
            if self._timekprConfigManager.getClientUseSpeechNotifications():
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
            value = str(bool(self._screenSaverInterface.GetActive()))

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
        if self._timekprLimitsInterface is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._timekprLimitsInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timeleft")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprLimitsInterface.requestTimeLeft(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._timekprLimitsInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))

    def requestTimeLimits(self):
        """Request time limits from server"""
        # if we have dbus connection, let"s do so
        if self._timekprLimitsInterface is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._timekprLimitsInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timelimits")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprLimitsInterface.requestTimeLimits(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._timekprLimitsInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))

    def processUserSessionAttributes(self, pWhat, pKey=None, pValue=None):
        """Request time limits from server"""
        # if we have dbus connection, let"s do so
        if self._timekprAttributesInterface is None:
            # init
            self.initClientConnections()

        # if we have end-point
        if self._timekprAttributesInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "%s session attributes" % ("requesting" if pKey is None else "verifying"))
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAttributesInterface.processUserSessionAttributes(
                    self._userName
                    ,dbus.String(pWhat if pWhat is not None else "")
                    ,dbus.String(pKey if pKey is not None else "")
                    ,dbus.String(pValue if pValue is not None else ""))

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._timekprLimitsInterface = None
                self._timekprAttributesInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))
