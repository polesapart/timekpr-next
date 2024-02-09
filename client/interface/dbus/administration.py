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
from timekpr.common.constants import messages as msg

# default loop
DBusGMainLoop(set_as_default=True)


class timekprAdminConnector(object):
    """Main class for supporting indicator notifications"""

    def __init__(self):
        """Initialize stuff for connecting to timekpr server"""
        # times
        self._retryTimeoutSecs = 3
        self._retryCountLeft = 5
        self._initFailed = False

        # dbus (timekpr)
        self._timekprBus = (dbus.SessionBus() if (cons.TK_DEV_ACTIVE and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        self._timekprObject = None
        self._timekprUserAdminDbusInterface = None
        self._timekprAdminDbusInterface = None

    def initTimekprConnection(self, pTryOnce, pRescheduleConnection=False):
        """Init dbus (connect to timekpr for info)"""
        # reschedule
        if pRescheduleConnection:
            # rescheduling means dropping existing state and try again
            self._timekprObject = None
            self._timekprUserAdminDbusInterface = None
            self._timekprAdminDbusInterface = None
            self._retryCountLeft = 5
            self._initFailed = False

        # only if notifications are ok
        if self._timekprObject is None:
            try:
                # dbus performance measurement
                misc.measureDBUSTimeElapsed(pStart=True)
                # timekpr connection stuff
                self._timekprObject = self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH)
                # measurement logging
                misc.measureDBUSTimeElapsed(pStop=True, pPrintToConsole=True, pDbusIFName=cons.TK_DBUS_BUS_NAME)
            except Exception:
                self._timekprObject = None
                # logging
                log.consoleOut("FAILED to obtain connection to timekpr.\nPlease check that timekpr daemon is working and you have sufficient permissions to access it (either superuser or timekpr group)")

            # only if notifications are ok
        if self._timekprObject is not None and self._timekprUserAdminDbusInterface is None:
            try:
                # dbus performance measurement
                misc.measureDBUSTimeElapsed(pStart=True)
                # getting interface
                self._timekprUserAdminDbusInterface = dbus.Interface(self._timekprObject, cons.TK_DBUS_USER_ADMIN_INTERFACE)
                # measurement logging
                misc.measureDBUSTimeElapsed(pStop=True, pPrintToConsole=True, pDbusIFName=cons.TK_DBUS_USER_ADMIN_INTERFACE)
            except Exception:
                self._timekprUserAdminDbusInterface = None
                # logging
                log.consoleOut("FAILED to connect to timekpr user admin interface.\nPlease check that timekpr daemon is working and you have sufficient permissions to access it (either superuser or timekpr group)")

            # only if notifications are ok
        if self._timekprObject is not None and self._timekprAdminDbusInterface is None:
            try:
                # dbus performance measurement
                misc.measureDBUSTimeElapsed(pStart=True)
                # getting interface
                self._timekprAdminDbusInterface = dbus.Interface(self._timekprObject, cons.TK_DBUS_ADMIN_INTERFACE)
                # measurement logging
                misc.measureDBUSTimeElapsed(pStop=True, pPrintToConsole=True, pDbusIFName=cons.TK_DBUS_ADMIN_INTERFACE)
            except Exception:
                self._timekprAdminDbusInterface = None
                # logging
                log.consoleOut("FAILED to connect to timekpr user admin interface.\nPlease check that timekpr daemon is working and you have sufficient permissions to access it (either superuser or timekpr group)")

        # if either of this fails, we keep trying to connect
        if self._timekprUserAdminDbusInterface is None or self._timekprAdminDbusInterface is None:
            if self._retryCountLeft > 0 and not pTryOnce:
                log.consoleOut("connection failed, %i attempts left, will retry in %i seconds" % (self._retryCountLeft, self._retryTimeoutSecs))
                self._retryCountLeft -= 1

                # if either of this fails, we keep trying to connect
                GLib.timeout_add_seconds(3, self.initTimekprConnection, pTryOnce)
            else:
                # failed
                self._initFailed = True

    # --------------- helper methods --------------- #

    def isConnected(self):
        """Return status of connection to DBUS"""
        # if either of this fails, we keep trying to connect
        return not (self._timekprUserAdminDbusInterface is None or self._timekprAdminDbusInterface is None), not self._initFailed

    def formatException(self, pExceptionStr, pFPath, pFName):
        """Format exception and pass it back"""
        # check for permission error
        if "org.freedesktop.DBus.Error.AccessDenied" in pExceptionStr:
            result = -1
            message = msg.getTranslation("TK_MSG_DBUS_COMMUNICATION_COMMAND_FAILED")
        else:
            result = -1
            message = msg.getTranslation("TK_MSG_UNEXPECTED_ERROR") % (("\"%s\" in \"%s.%s\"") % (pExceptionStr, pFPath, pFName))
        # log error
        log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: \"%s\" in \"%s.%s\"" % (pExceptionStr, pFPath, pFName))
        # result
        return result, message

    def initReturnCodes(self, pInit, pCall):
        """Initialize the return codes for calls"""
        return -2 if pInit else -1 if pCall else 0, msg.getTranslation("TK_MSG_STATUS_INTERFACE_NOTREADY") if pInit else msg.getTranslation("TK_MSG_DBUS_COMMUNICATION_COMMAND_NOT_ACCEPTED") if pCall else ""

    # --------------- user configuration info population methods --------------- #

    def getUserList(self):
        """Get user list from server"""
        # defaults
        result, message = self.initReturnCodes(pInit=True, pCall=False)
        userList = []

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, userList = self._timekprUserAdminDbusInterface.getUserList()
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.getUserList.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, userList

    def getUserConfigurationAndInformation(self, pUserName, pInfoLvl):
        """Get user configuration from server"""
        # defaults
        result, message = self.initReturnCodes(pInit=True, pCall=False)
        userConfig = {}

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, userConfig = self._timekprUserAdminDbusInterface.getUserInformation(pUserName, pInfoLvl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.getUserConfigurationAndInformation.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, userConfig

    # --------------- user configuration set methods --------------- #

    def setAllowedDays(self, pUserName, pDayList):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setAllowedDays(pUserName, pDayList)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setAllowedDays.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setAllowedHours(pUserName, pDayNumber, pHourList)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setAllowedHours.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForDays(self, pUserName, pDayLimits):
        """Set user allowed limit for days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setTimeLimitForDays(pUserName, pDayLimits)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimeLimitForDays.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForWeek(self, pUserName, pTimeLimitWeek):
        """Set user allowed limit for week"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setTimeLimitForWeek(pUserName, pTimeLimitWeek)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimeLimitForWeek.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForMonth(self, pUserName, pTimeLimitMonth):
        """Set user allowed limit for month"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setTimeLimitForMonth(pUserName, pTimeLimitMonth)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimeLimitForMonth.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTrackInactive(self, pUserName, pTrackInactive):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setTrackInactive(pUserName, pTrackInactive)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.getUserList.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setHideTrayIcon(self, pUserName, pHideTrayIcon):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setHideTrayIcon(pUserName, pHideTrayIcon)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setHideTrayIcon.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setLockoutType(self, pUserName, pLockoutType, pWakeFrom, pWakeTo):
        """Set user restriction / lockout type"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setLockoutType(pUserName, pLockoutType, pWakeFrom, pWakeTo)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setLockoutType.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set user time left"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setTimeLeft(pUserName, pOperation, pTimeLeft)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimeLeft.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    # --------------- PlayTime user configuration info set methods --------------- #

    def setPlayTimeEnabled(self, pUserName, pPlayTimeEnabled):
        """Set PlayTime enabled flag for user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeEnabled(pUserName, pPlayTimeEnabled)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeEnabled.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeLimitOverride(self, pUserName, pPlayTimeLimitOverride):
        """Set PlayTime override flag for user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeLimitOverride(pUserName, pPlayTimeLimitOverride)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeLimitOverride.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeUnaccountedIntervalsEnabled(self, pUserName, pPlayTimeUnaccountedIntervalsEnabled):
        """Set PlayTime allowed during unaccounted intervals flag for user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeUnaccountedIntervalsEnabled(pUserName, pPlayTimeUnaccountedIntervalsEnabled)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeUnaccountedIntervalsEnabled.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeAllowedDays(self, pUserName, pPlayTimeAllowedDays):
        """Set allowed days for PlayTime for user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeAllowedDays(pUserName, pPlayTimeAllowedDays)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeAllowedDays.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeLimitsForDays(self, pUserName, pPlayTimeLimits):
        """Set PlayTime limits for the allowed days for the user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeLimitsForDays(pUserName, pPlayTimeLimits)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeLimitsForDays.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeActivities(self, pUserName, pPlayTimeActivities):
        """Set PlayTime limits for the allowed days for the user"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeActivities(pUserName, pPlayTimeActivities)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeActivities.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setPlayTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set user time left"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminDbusInterface.setPlayTimeLeft(pUserName, pOperation, pTimeLeft)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setPlayTimeLeft.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    # --------------- timekpr configuration info population / set methods --------------- #

    def getTimekprConfiguration(self):
        """Get configuration from server"""
        # defaults
        result, message = self.initReturnCodes(pInit=True, pCall=False)
        timekprConfig = {}

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, timekprConfig = self._timekprAdminDbusInterface.getTimekprConfiguration()
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.getTimekprConfiguration.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, timekprConfig

    def setTimekprLogLevel(self, pLogLevel):
        """Set the logging level for server"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprLogLevel(pLogLevel)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprLogLevel.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprPollTime(self, pPollTimeSecs):
        """Set polltime for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprPollTime(pPollTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprPollTime.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSaveTime(self, pSaveTimeSecs):
        """Set save time for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprSaveTime(pSaveTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprSaveTime.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprTrackInactive(self, pTrackInactive):
        """Set default value for tracking inactive sessions"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprTrackInactive(pTrackInactive)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprTrackInactive.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprTerminationTime(self, pTerminationTimeSecs):
        """Set up user termination time"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprTerminationTime(pTerminationTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprTerminationTime.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Set up final warning time for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprFinalWarningTime.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprFinalNotificationTime(self, pFinalNotificationTimeSecs):
        """Set up final notification time for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprFinalNotificationTime(pFinalNotificationTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprFinalNotificationTime.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSessionsCtrl(self, pSessionsCtrl):
        """Set accountable session types for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprSessionsCtrl(pSessionsCtrl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprSessionsCtrl.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSessionsExcl(self, pSessionsExcl):
        """Set NON-accountable session types for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprSessionsExcl(pSessionsExcl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprSessionsExcl.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprUsersExcl(self, pUsersExcl):
        """Set excluded usernames for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprUsersExcl(pUsersExcl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprUsersExcl.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprPlayTimeEnabled(self, pPlayTimeEnabled):
        """Set up global PlayTime enable switch"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprPlayTimeEnabled(pPlayTimeEnabled)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprPlayTimeEnabled.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprPlayTimeEnhancedActivityMonitorEnabled(self, pPlayTimeEnabled):
        """Set up global PlayTime enhanced activity monitor enable switch"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminDbusInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminDbusInterface.setTimekprPlayTimeEnhancedActivityMonitorEnabled(pPlayTimeEnabled)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex), __name__, self.setTimekprPlayTimeEnhancedActivityMonitorEnabled.__name__)

                # we cannot send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message
