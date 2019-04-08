"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import dbus
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
        """Initialize notificaitions"""
        # init logging firstly
        log.setLogging(pLog, pClient=True)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekpr notifications")

        # dev
        self._isDevActive = pIsDevActive

        # uname
        self._userName = pUserName
        self._timekprConfigManager = pTimekprConfigManager

        # critical notification (to replace itself)
        self._criticalNotif = 0

        # dbus (notifications)
        self._notifyBus = dbus.SessionBus()
        self._notifyObject = None
        self._notifyInterface = None

        # dbus (timekpr)
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        self._timekprObject = None
        self._timekprInterface = None

        # speech init
        self._timekprSpeechManager = None

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekpr notifications")

    def initClientNotifications(self):
        """Init dbus (connect to session bus for notification)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start initClientNotifications")

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
            try:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # notification stuff
                self._notifyObject = self._notifyBus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % ("org.freedesktop.Notifications (o)", misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # getting interface
                self._notifyInterface = dbus.Interface(self._notifyObject, "org.freedesktop.Notifications")
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % ("org.freedesktop.Notifications (i)", misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                log.log(cons.TK_LOG_LEVEL_DEBUG, "connected to DBUS notification interface")
            except Exception as dbusEx:
                self._notifyInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating dbus connection ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating dbus connection ===---")

            # only if notifications are ok
        if self._timekprInterface is None:
            try:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # timekpr notification stuff
                self._timekprObject = self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_BUS_NAME, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # getting interface
                self._timekprInterface = dbus.Interface(self._timekprObject, cons.TK_DBUS_USER_LIMITS_INTERFACE)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_LIMITS_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                log.log(cons.TK_LOG_LEVEL_DEBUG, "connected to DBUS timekpr interface")
            except Exception as dbusEx:
                self._timekprInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating timekpr dbus connection ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR initiating timekpr dbus connection ===---")

        # if either of this fails, we keep trying to connect
        if self._notifyInterface is None or self._timekprInterface is None:
            if self._notifyInterface is None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "failed to connect to notifications dbus, trying again...")
            elif self._timekprInterface is None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "failed to connect to timekpr dbus, trying again...")

            # if either of this fails, we keep trying to connect
            GLib.timeout_add_seconds(3, self.initClientNotifications)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish initClientNotifications")

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
            self.initClientNotifications()

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

    def requestTimeLeft(self):
        """Request time left from server"""
        # if we have dbus connection, let"s do so
        if self._timekprInterface is None:
            # init
            self.initClientNotifications()

        # if we have end-point
        if self._timekprInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timeleft")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprInterface.requestTimeLeft(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._timekprInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))

    def requestTimeLimits(self):
        """Request time limits from server"""
        # if we have dbus connection, let"s do so
        if self._timekprInterface is None:
            # init
            self.initClientNotifications()

        # if we have end-point
        if self._timekprInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "requesting timelimits")
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprInterface.requestTimeLimits(self._userName)

                # check call result
                if result != 0:
                    # show message to user as well
                    self.notifyUser(cons.TK_MSG_CODE_REMOTE_INVOCATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=message)
            except Exception as dbusEx:
                # we can not send notif through dbus
                self._timekprInterface = None
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
                log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through timekpr dbus ===---")

                # show message to user as well
                self.notifyUser(cons.TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR, cons.TK_PRIO_CRITICAL, pAdditionalMessage=msg.getTranslation("TK_MSG_NOTIFICATION_CONNECTION_ERROR"))
