"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
from datetime import timedelta
import os
import dbus
from gi.repository import GLib

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc
from timekpr.common.utils.config import timekprClientConfig
from timekpr.client.interface.ui.appindicator import timekprIndicator as appind_timekprIndicator
from timekpr.client.interface.ui.statusicon import timekprIndicator as statico_timekprIndicator
from timekpr.common.constants import messages as msg


class timekprClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self):
        """Initialize client"""
        # set username , etc.
        self._userName, self._userNameFull = misc.getNormalizedUserNames(pUID=os.getuid())
        self._userNameDBUS = self._userName.replace(".", "").replace("-", "")

        # get our bus
        self._timekprBus = (dbus.SessionBus() if (cons.TK_DEV_ACTIVE and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())

        # loop
        self._mainLoop = GLib.MainLoop()

        # init logging (load config which has all the necessarry bits)
        self._timekprClientConfig = timekprClientConfig()
        self._timekprClientConfig.loadClientConfiguration()

        # init logging
        log.setLogging(self._timekprClientConfig.getClientLogLevel(), cons.TK_LOG_TEMP_DIR, cons.TK_LOG_OWNER_CLIENT, self._userName)


    def startTimekprClient(self):
        """Start up timekpr (choose appropriate gui and start this up)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "starting up timekpr client")

        # check if appind is supported
        self._timekprClientIndicator = appind_timekprIndicator(self._userName, self._userNameFull, self._timekprClientConfig)

        # if not supported fall back to statico
        if not self._timekprClientIndicator.isSupported():
            # check if appind is supported
            self._timekprClientIndicator = statico_timekprIndicator(self._userName, self._userNameFull, self._timekprClientConfig)

        # this will check whether we have an icon, if not, the rest goes through timekprClient anyway
        if self._timekprClientIndicator.isSupported():
            # init timekpr
            self._timekprClientIndicator.initTimekprIcon()
        else:
            # process time left notification (notifications should be available in any of the icons, even of not supported)
            self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_ICON_INIT_ERROR, None, cons.TK_PRIO_CRITICAL, None, "cannot initialize the icon in any way")

        # connect to timekpr etc.
        self.connectTimekprSignalsDBUS()

        # init startup notification at default interval
        GLib.timeout_add_seconds(cons.TK_POLLTIME, self.requestInitialTimeValues)

        # periodic log flusher
        GLib.timeout_add_seconds(cons.TK_POLLTIME, self.autoFlushLogFile)

        # start main loop
        self._mainLoop.run()

    def autoFlushLogFile(self):
        """Periodically save file"""
        log.autoFlushLogFile()
        return True

    def finishTimekpr(self, signal=None, frame=None):
        """Exit timekpr gracefully"""
        log.log(cons.TK_LOG_LEVEL_INFO, "Finishing up")
        # exit main loop
        self._mainLoop.quit()
        log.log(cons.TK_LOG_LEVEL_INFO, "Finished")
        log.flushLogFile()

    def requestInitialTimeValues(self):
        """Request initial config from server"""
        # whether to process again
        result = False
        # check if connected
        if self._notificationFromDBUS is not None:
            # connect to DBUS for the rest of modules
            self._timekprClientIndicator.initClientConnections()
            # request values if connections are made successfully
            result = self._timekprClientIndicator.isTimekprConnected()
            # connected?
            if result:
                # get limits
                self._timekprClientIndicator.requestTimeLimits()
                # get left
                self._timekprClientIndicator.requestTimeLeft()

        # continue execution while not connected (this is called from glib exec)
        return not result

    # --------------- DBUS / communication methods --------------- #

    def connectTimekprSignalsDBUS(self):
        """Init connections to dbus provided by server"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start connectTimekprSignalsDBUS")

        # trying to connect
        self._timekprClientIndicator.setStatus(msg.getTranslation("TK_MSG_STATUS_CONNECTING"))

        try:
            # dbus performance measurement
            misc.measureDBUSTimeElapsed(pStart=True)

            # get dbus object
            self._notificationFromDBUS = self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS)

            # connect to signal
            self._sessionAttributeVerificationSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveSessionAttributeVerificationRequest,
                dbus_interface   = cons.TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE,
                signal_name      = "sessionAttributeVerification")

            # connect to signal
            self._timeLeftSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeLeft,
                dbus_interface   = cons.TK_DBUS_USER_LIMITS_INTERFACE,
                signal_name      = "timeLeft")

            # connect to signal
            self._timeLimitsSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeLimits,
                dbus_interface   = cons.TK_DBUS_USER_LIMITS_INTERFACE,
                signal_name      = "timeLimits")

            # connect to signal
            self._timeLeftNotificatonSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeLeftNotification,
                dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE,
                signal_name      = "timeLeftNotification")

            # connect to signal
            self._timeCriticalNotificatonSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeCriticalNotification,
                dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE,
                signal_name      = "timeCriticalNotification")

            # connect to signal
            self._timeNoLimitNotificationSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeNoLimitNotification,
                dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE,
                signal_name      = "timeNoLimitNotification")

            # connect to signal
            self._timeLeftChangedNotificationSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeLeftChangedNotification,
                dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE,
                signal_name      = "timeLeftChangedNotification")

            # connect to signal
            self._timeConfigurationChangedNotificationSignal = self._timekprBus.add_signal_receiver(
                path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS,
                handler_function = self.receiveTimeConfigurationChangedNotification,
                dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE,
                signal_name      = "timeConfigurationChangedNotification")

            # measurement logging
            misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_BUS_NAME)

            # set status
            self._timekprClientIndicator.setStatus(msg.getTranslation("TK_MSG_STATUS_CONNECTED"))

            log.log(cons.TK_LOG_LEVEL_DEBUG, "main DBUS signals connected")

        except Exception as dbusEx:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR (DBUS): \"%s\" in \"%s.%s\"" % (str(dbusEx), __name__, self.connectTimekprSignalsDBUS.__name__))
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: failed to connect to timekpr dbus, trying again...")

            # did not connect (set connection to None) and schedule for reconnect at default interval
            self._notificationFromDBUS = None

            # connect until successful
            GLib.timeout_add_seconds(cons.TK_POLLTIME, self.connectTimekprSignalsDBUS)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish connectTimekprSignalsDBUS")

        # finish
        return False

    # --------------- admininstration / verification methods (from dbus) --------------- #

    def receiveSessionAttributeVerificationRequest(self, pWhat, pKey):
        """Receive the signal and process the data"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive verification request: %s, %s" % (pWhat, "key"))
        # resend stuff to server
        self._timekprClientIndicator.verifySessionAttributes(pWhat, pKey)

    def processShowClientIcon(self, pTimeInformation):
        """Check wheter to show or hide tray icon"""
        # do we have information about show or hide icon
        if cons.TK_CTRL_HIDEI in pTimeInformation:
            # enable?
            iconStatus = (not bool(pTimeInformation[cons.TK_CTRL_HIDEI]))
            # check if those differ
            if self._timekprClientIndicator.getTrayIconEnabled() != iconStatus:
                # set it
                self._timekprClientIndicator.setTrayIconEnabled(iconStatus)

    # --------------- worker methods (from dbus) --------------- #

    def receiveTimeLeft(self, pPriority, pTimeInformation):
        """Receive the signal and process the data to user"""
        # check which options are available
        timeLeft = (pTimeInformation[cons.TK_CTRL_LEFT] if cons.TK_CTRL_LEFT in pTimeInformation else 0)
        playTimeLeft = (pTimeInformation[cons.TK_CTRL_PTLPD] if cons.TK_CTRL_PTLSTC in pTimeInformation and cons.TK_CTRL_PTLPD in pTimeInformation and cons.TK_CTRL_PTTLO in pTimeInformation else None)
        isTimeNotLimited = (pTimeInformation[cons.TK_CTRL_TNL] if cons.TK_CTRL_TNL in pTimeInformation else 0)
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive timeleft, prio: %s, tl: %i, ptl: %s, nolim: %i" % (pPriority, timeLeft, str(playTimeLeft), isTimeNotLimited))
        # process show / hide icon
        self.processShowClientIcon(pTimeInformation)
        # process time left
        self._timekprClientIndicator.setTimeLeft(pPriority, cons.TK_DATETIME_START + timedelta(seconds=timeLeft), isTimeNotLimited, cons.TK_DATETIME_START + timedelta(seconds=playTimeLeft) if playTimeLeft is not None else playTimeLeft)
        # renew limits in GUI
        self._timekprClientIndicator.renewUserLimits(pTimeInformation)
        # process PlayTime notifications as well
        self._timekprClientIndicator.processPlayTimeNotifications(pTimeInformation)

    def receiveTimeLimits(self, pPriority, pTimeLimits):
        """Receive the signal and process the data to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive timelimits: %s" % (pPriority))
        # renew limits in GUI
        self._timekprClientIndicator.renewLimitConfiguration(pTimeLimits)

    # --------------- notification methods (from dbus) --------------- #

    def receiveTimeLeftNotification(self, pPriority, pTimeLeftTotal, pTimeLeftToday, pTimeLimitToday):
        """Receive time left and update GUI"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive tl notif: %s, %i" % (pPriority, pTimeLeftTotal))
        # if notifications are turned on
        if (self._timekprClientConfig.getClientShowAllNotifications() and self._timekprClientIndicator.getTrayIconEnabled()) or pPriority == cons.TK_PRIO_CRITICAL:
            # process time left notification
            self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_TIMELEFT, None, pPriority, cons.TK_DATETIME_START + timedelta(seconds=pTimeLeftTotal))

    def receiveTimeCriticalNotification(self, pFinalNotificationType, pPriority, pSecondsLeft):
        """Receive critical time left and show that to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive crit notif: %s, %i" % (pFinalNotificationType, pSecondsLeft))
        # process time left (this shows in any case)
        self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_TIMECRITICAL, pFinalNotificationType, pPriority, cons.TK_DATETIME_START + timedelta(seconds=pSecondsLeft))

    def receiveTimeNoLimitNotification(self, pPriority):
        """Receive no limit notificaton and show that to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive nl notif")
        # if notifications are turned on
        if self._timekprClientConfig.getClientShowAllNotifications() and self._timekprClientIndicator.getTrayIconEnabled():
            # process time left
            self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_TIMEUNLIMITED, None, pPriority)

    def receiveTimeLeftChangedNotification(self, pPriority):
        """Receive time left notification and show it to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive time left changed notif")
        # if notifications are turned on
        if self._timekprClientConfig.getClientShowLimitNotifications() and self._timekprClientIndicator.getTrayIconEnabled():
            # limits have changed and applied
            self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_TIMELEFTCHANGED, None, pPriority)

    def receiveTimeConfigurationChangedNotification(self, pPriority):
        """Receive notification about config change and show it to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive config changed notif")
        # if notifications are turned on
        if self._timekprClientConfig.getClientShowLimitNotifications() and self._timekprClientIndicator.getTrayIconEnabled():
            # configuration has changed, new limits may have been applied
            self._timekprClientIndicator.notifyUser(cons.TK_MSG_CODE_TIMECONFIGCHANGED, None, pPriority)
