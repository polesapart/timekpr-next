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

    def __init__(self, pIsDevActive):
        """Initialize stuff for connecting to timekpr server"""
        # dev
        self._isDevActive = pIsDevActive

        # times
        self._retryTimeoutSecs = 3
        self._retryCountLeft = 5
        self._initFailed = False

        # dbus (timekpr)
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        self._timekprObject = None
        self._timekprUserAdminInterface = None
        self._timekprAdminInterface = None

    def initTimekprConnection(self, pTryOnce, pRescheduleConnection=False):
        """Init dbus (connect to timekpr for info)"""
        # reschedule
        if pRescheduleConnection:
            # rescheduling means dropping existing state and try again
            self._timekprObject = None
            self._timekprUserAdminInterface = None
            self._timekprAdminInterface = None
            self._retryCountLeft = 5
            self._initFailed = False

        # only if notifications are ok
        if self._timekprObject is None:
            try:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # timekpr connection stuff
                self._timekprObject = self._timekprBus.get_object(cons.TK_DBUS_BUS_NAME, cons.TK_DBUS_SERVER_PATH)
                # measurement logging
                log.consoleOut("FYI: PERFORMANCE (DBUS), acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_BUS_NAME, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
            except Exception:
                self._timekprObject = None
                # logging
                log.consoleOut("FAILED to obtain connection to timekpr.\nPlease check that timekpr daemon is working and You have sufficient permissions to access it (either superuser or timekpr group)")

            # only if notifications are ok
        if self._timekprObject is not None and self._timekprUserAdminInterface is None:
            try:
                # getting interface
                self._timekprUserAdminInterface = dbus.Interface(self._timekprObject, cons.TK_DBUS_USER_ADMIN_INTERFACE)
                # measurement logging
                log.consoleOut("FYI: PERFORMANCE (DBUS), acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_ADMIN_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
            except Exception:
                self._timekprUserAdminInterface = None
                # logging
                log.consoleOut("FAILED to connect to timekpr user admin interface.\nPlease check that timekpr daemon is working and You have sufficient permissions to access it (either superuser or timekpr group)")

            # only if notifications are ok
        if self._timekprObject is not None and self._timekprAdminInterface is None:
            try:
                # getting interface
                self._timekprAdminInterface = dbus.Interface(self._timekprObject, cons.TK_DBUS_ADMIN_INTERFACE)
                # measurement logging
                log.consoleOut("FYI: PERFORMANCE (DBUS), acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_ADMIN_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
            except Exception:
                self._timekprAdminInterface = None
                # logging
                log.consoleOut("FAILED to connect to timekpr user admin interface.\nPlease check that timekpr daemon is working and You have sufficient permissions to access it (either superuser or timekpr group)")

        # if either of this fails, we keep trying to connect
        if self._timekprUserAdminInterface is None or self._timekprAdminInterface is None:
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
        return not (self._timekprUserAdminInterface is None or self._timekprAdminInterface is None), not self._initFailed

    def formatException(self, pExceptionStr):
        """Format exception and pass it back"""
        # check for permission error
        if "org.freedesktop.DBus.Error.AccessDenied" in pExceptionStr:
            result = -1
            message = msg.getTranslation("TK_MSG_DBUS_COMMUNICATION_COMMAND_FAILED")
        else:
            result = -1
            message = msg.getTranslation("TK_MSG_UNEXPECTED_ERROR") % (pExceptionStr)

        # result
        return result, message

    def initReturnCodes(self, pInit, pCall):
        """Initialize the return codes for calls"""
        return -2 if pInit else -1 if pCall else 0, msg.getTranslation("TK_MSG_STATUS_INTERFACE_NOTREADY") if pInit else msg.getTranslation("TK_MSG_DBUS_COMMUNICATION_COMMAND_NOT_ACCEPTED") if pCall else ""

    # --------------- user configuration info population / set methods --------------- #

    def getUserList(self):
        """Get user list from server"""
        # defaults
        result, message = self.initReturnCodes(pInit=True, pCall=False)
        userList = []

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, userList = self._timekprUserAdminInterface.getUserList()
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, userList

    def getUserConfig(self, pUserName):
        """Get user configuration from server"""
        # defaults
        result, message = self.initReturnCodes(pInit=True, pCall=False)
        userConfig = {}

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, userConfig = self._timekprUserAdminInterface.getUserConfiguration(pUserName)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, userConfig

    def setAllowedDays(self, pUserName, pDayList):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setAllowedDays(pUserName, pDayList)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setAllowedHours(pUserName, pDayNumber, pHourList)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForDays(self, pUserName, pDayLimits):
        """Set user allowed limit for days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLimitForDays(pUserName, pDayLimits)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForWeek(self, pUserName, pTimeLimitWeek):
        """Set user allowed limit for week"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLimitForWeek(pUserName, pTimeLimitWeek)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLimitForMonth(self, pUserName, pTimeLimitMonth):
        """Set user allowed limit for month"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLimitForMonth(pUserName, pTimeLimitMonth)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTrackInactive(self, pUserName, pTrackInactive):
        """Set user allowed days"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTrackInactive(pUserName, pTrackInactive)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set user time left"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLeft(pUserName, pOperation, pTimeLeft)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
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
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message, timekprConfig = self._timekprAdminInterface.getTimekprConfiguration()
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message, timekprConfig

    def setTimekprLogLevel(self, pLogLevel):
        """Set the logging level for server"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprLogLevel(pLogLevel)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprPollTime(self, pPollTimeSecs):
        """Set polltime for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprPollTime(pPollTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSaveTime(self, pSaveTimeSecs):
        """Set save time for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprSaveTime(pSaveTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprTrackInactive(self, pTrackInactive):
        """Set default value for tracking inactive sessions"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprTrackInactive(pTrackInactive)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprTerminationTime(self, pTerminationTimeSecs):
        """Set up user termination time"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprTerminationTime(pTerminationTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Set up final warning time for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSessionsCtrl(self, pSessionsCtrl):
        """Set accountable session types for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprSessionsCtrl(pSessionsCtrl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprSessionsExcl(self, pSessionsExcl):
        """Set NON-accountable session types for users"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprSessionsExcl(pSessionsExcl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message

    def setTimekprUsersExcl(self, pUsersExcl):
        """Set excluded usernames for timekpr"""
        # initial values
        result, message = self.initReturnCodes(pInit=True, pCall=False)

        # if we have end-point
        if self._timekprAdminInterface is not None:
            # defaults
            result, message = self.initReturnCodes(pInit=False, pCall=True)

            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprAdminInterface.setTimekprUsersExcl(pUsersExcl)
            except Exception as ex:
                # exception
                result, message = self.formatException(str(ex))

                # we can not send notif through dbus, we need to reschedule connecton
                self.initTimekprConnection(False, True)

        # result
        return result, message
