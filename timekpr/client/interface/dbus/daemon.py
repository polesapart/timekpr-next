"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
from datetime import timedelta
import getpass
import dbus
import time
from gi.repository import GLib

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc
from timekpr.common.utils.config import timekprClientConfig
from timekpr.client.interface.ui.appindicator import timekprIndicator as appind_timekprIndicator
from timekpr.client.interface.ui.statusicon import timekprIndicator as statico_timekprIndicator


class timekprClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self, pIsDevActive=False):
        """Initialize client"""
        # dev
        self._isDevActive = pIsDevActive

        # set username , etc.
        self._userName = getpass.getuser()

        # get our bus
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())

        # loop
        self._mainLoop = GLib.MainLoop()

        # init logging (load config which has all the necessarry bits)
        self._timekprConfigManager = timekprClientConfig(pIsDevActive)
        self._timekprConfigManager.loadClientConfiguration()

        # save logging for later use in classes down tree
        self._logging = {cons.TK_LOG_L: self._timekprConfigManager.getClientLogLevel(), cons.TK_LOG_D: self._timekprConfigManager.getClientLogfileDir()}

        # logging init
        log.setLogging(self._logging, pClient=True)

    def startTimekprClient(self):
        """Start up timekpr (choose appropriate gui and start this up)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "starting up timekpr client")

        # check if appind is supported
        self._timekprClient = appind_timekprIndicator(self._logging, self._isDevActive, self._userName, self._timekprConfigManager.getTimekprSharedDir())

        # if not supported fall back to statico
        if not self._timekprClient.isSupported():
            # check if appind is supported
            self._timekprClient = statico_timekprIndicator(self._logging, self._isDevActive, self._userName, self._timekprConfigManager.getTimekprSharedDir())

            if not self._timekprClient.isSupported():
                # TODO : use w/o GUI or just exit? we need a notification anyway!
                pass

        # this will check whether we have an icon, if not, the rest goes through timekprClient anyway
        if self._timekprClient.isSupported():
            # init timekpr
            self._timekprClient.initTimekprIcon(self._timekprConfigManager.getClientShowSeconds())

            # set up defaults
            self._timekprClient.renewUserConfiguration(
                 self._timekprConfigManager.getClientShowLimitNotifications()
                ,self._timekprConfigManager.getClientShowAllNotifications()
                ,self._timekprConfigManager.getClientUseSpeechNotifications()
                ,self._timekprConfigManager.getClientShowSeconds()
                ,self._timekprConfigManager.getClientLogLevel())

        # connect signals to dbus
        self.connectTimekprSignalsDBUS()

        # init startup notification at default interval
        GLib.timeout_add_seconds(cons.TK_POLLTIME, self.requestInitialTimeValues)

        # start main loop
        self._mainLoop.run()

    def finishTimekpr(self, signal=None, frame=None):
        """Exit timekpr gracefully"""
        log.log(cons.TK_LOG_LEVEL_INFO, "Finishing up")
        # exit main loop
        self._mainLoop.quit()

    def requestInitialTimeValues(self):
        """Request initial config from server"""
        if self._notificationFromDBUS is not None:
            # get limits
            self._timekprClient._timekprNotifications.requestTimeLimits()
            # wait a little between limits and left
            time.sleep(0.25)
            # get left
            self._timekprClient._timekprNotifications.requestTimeLeft()
        else:
            # loop while not connected
            return True

    # --------------- DBUS / communication methods --------------- #

    def connectTimekprSignalsDBUS(self):
        """Init connections to dbus provided by server"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start connectTimekprSignalsDBUS")

        # trying to connect
        self._timekprClient.setStatus("Connecting...")

        try:
            # dbus performance measurement
            misc.measureTimeElapsed(pStart=True)

            # get dbus object
            self._notificationFromDBUS = self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName)

            # connect to signal
            self._timeLeftSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeLeft
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeLeft")

            # connect to signal
            self._timeLeftSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeLimits
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeLimits")

            # connect to signal
            self._timeLeftNotificatonSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeLeftNotification
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeLeftNotification")

            # connect to signal
            self._timeCriticalNotificatonSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeCriticalNotification
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeCriticalNotification")

            # connect to signal
            self._timeNoLimitNotificationSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeNoLimitNotification
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeNoLimitNotification")

            # connect to signal
            self._timeLeftChangedNotificationSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeLeftChangedNotification
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeLeftChangedNotification")

            # connect to signal
            self._timeConfigurationChangedNotificationSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeConfigurationChangedNotification
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeConfigurationChangedNotification")

            # connect to signal
            self._timeLimitConfigurationSignal = self._timekprBus.add_signal_receiver(
                 path             = cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userName
                ,handler_function = self.receiveTimeLimitConfiguration
                ,dbus_interface   = cons.TK_DBUS_USER_NOTIF_INTERFACE
                ,signal_name      = "timeLimitConfiguration")

            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - connecting signals \"%s\" took too long (%is)" % (cons.TK_DBUS_BUS_NAME, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            # set status
            self._timekprClient.setStatus("Connected")

            log.log(cons.TK_LOG_LEVEL_DEBUG, "DBUS signals connected")

        except Exception as dbusEx:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")
            log.log(cons.TK_LOG_LEVEL_INFO, str(dbusEx))
            log.log(cons.TK_LOG_LEVEL_INFO, "--=== ERROR sending message through dbus ===---")
            log.log(cons.TK_LOG_LEVEL_INFO, "failed to connect to timekpr dbus, trying again...")

            # did not connect (set connection to None) and schedule for reconnect at default interval
            self._notificationFromDBUS = None
            GLib.timeout_add_seconds(cons.TK_POLLTIME, self.connectTimekprSignalsDBUS)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish connectTimekprSignalsDBUS")

        # finish
        return False

    # --------------- worker methods --------------- #

    def receiveTimeLeft(self, pPriority, pTimeLeft):
        """Receive the signal and process the data to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive timeleft: %s, %i" % (pPriority, pTimeLeft[cons.TK_CTRL_LEFT]))
        # process time left
        self._timekprClient.setTimeLeft(pPriority, cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_LEFT]))
        # renew limits in GUI
        self._timekprClient.renewUserLimits(pTimeLeft)
        # if config changed
        if self._timekprClient.getUserConfigChanged():
            # load config
            if self._timekprConfigManager.isClientConfigChanged():
                # reload
                self._timekprConfigManager.loadClientConfiguration()
                # adjust indicator
                self._timekprClient.setSetShowSeconds(self._timekprConfigManager.getClientShowSeconds())

    def receiveTimeLimits(self, pPriority, pTimeLimits):
        """Receive the signal and process the data to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive timelimits: %s" % (pPriority))
        # renew limits in GUI
        self._timekprClient.renewLimitConfiguration(pTimeLimits)

    def receiveTimeLimitConfiguration(self, pPriority, pIntervalsToday, pIntervalsTomorrow, pTimeLeftTotal, pSleepTime, pTrackInactive):
        """Show configuration for user (intervals for today and tomorrow, once every save on the server side)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive config: %s, %s, %i, %i, %s" % (pIntervalsToday, pIntervalsTomorrow, pTimeLeftTotal, pSleepTime, pTrackInactive))

    # --------------- notification methods --------------- #

    def receiveTimeLeftNotification(self, pPriority, pTimeLeftTotal, pTimeLeftToday, pTimeLimitToday):
        """Receive time left and update GUI"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive tl notif: %s, %i" % (pPriority, pTimeLeftTotal))
        # process time left notification
        if self._timekprConfigManager.getClientShowAllNotifications():
            self._timekprClient.notifyUser(cons.TK_MSG_TIMELEFT, pPriority, cons.TK_DATETIME_START + timedelta(seconds=pTimeLeftTotal))

    def receiveTimeCriticalNotification(self, pPriority, pSecondsLeft):
        """Receive critical time left and show that to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive crit notif: %i" % (pSecondsLeft))
        # process time left
        self._timekprClient.notifyUser(cons.TK_MSG_TIMECRITICAL, pPriority, cons.TK_DATETIME_START + timedelta(seconds=pSecondsLeft))

    def receiveTimeNoLimitNotification(self, pPriority):
        """Receive no limit notificatona and show that to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive nl notif")
        # process time left
        if self._timekprConfigManager.getClientShowAllNotifications():
            self._timekprClient.notifyUser(cons.TK_MSG_TIMEUNLIMITED, pPriority)
            pass

    def receiveTimeLeftChangedNotification(self, pPriority):
        """Receive time left notification and show it to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive time left changed notif")
        # limits have changed and applied
        if self._timekprConfigManager.getClientShowLimitNotifications():
            self._timekprClient.notifyUser(cons.TK_MSG_TIMELEFTCHANGED, pPriority)

    def receiveTimeConfigurationChangedNotification(self, pPriority):
        """Receive notification about config change and show it to user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "receive config changed notif")
        # configuration has changed, new limits may have been applied
        if self._timekprConfigManager.getClientShowLimitNotifications():
            self._timekprClient.notifyUser(cons.TK_MSG_TIMECONFIGCHANGED, pPriority)
