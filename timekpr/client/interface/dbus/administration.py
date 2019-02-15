"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import
import dbus
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
# from gettext import gettext as _s
# from gettext import ngettext as _n

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc
# from timekpr.client.interface.speech.espeak import timekprSpeech

# default loop
DBusGMainLoop(set_as_default=True)


# ## !!! WIP !!!
class timekprAdminConnector(object):
    """Main class for supporting indicator notifications"""

    def __init__(self, pIsDevActive):
        """Initialize stuff for connecting to timekpr server"""
        # dev
        self._isDevActive = pIsDevActive

        # times
        self._retryTimeoutSecs = 3
        self._retryCountLeft = 3
        self._initFailed = False

        # dbus (timekpr)
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        self._timekprObject = None
        self._timekprUserAdminInterface = None
        self._timekprAdminInterface = None

    def initTimekprConnection(self):
        """Init dbus (connect to timekpr for info)"""
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
            if self._retryCountLeft > 0:
                log.consoleOut("connection failed, %i attempts left, will retry in %i seconds" % (self._retryCountLeft, self._retryTimeoutSecs))
                self._retryCountLeft -= 1

                # if either of this fails, we keep trying to connect
                GLib.timeout_add_seconds(3, self.initTimekprConnection)
            else:
                self._initFailed = True

        # finish
        return False

    def isConnected(self):
        """Return status of connection to DBUS"""
        # if either of this fails, we keep trying to connect
        return not (self._notifyInterface is None or self._timekprUserAdminInterface is None or self._timekprAdminInterface is None), not self._initFailed

    def getUserList(self):
        """Get user list from server"""
        # defaults
        userList = []
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message, userList = self._timekprUserAdminInterface.getUserList()

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess, userList

    def getUserConfig(self, pUserName):
        """Get user configuration from server"""
        # defaults
        userConfig = {}
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message, userConfig = self._timekprUserAdminInterface.getUserConfiguration(pUserName)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess, userConfig

    def setAllowedDays(self, pUserName, pDayList):
        """Set user allowed days"""
        # defaults
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setAllowedDays(pUserName, pDayList)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess

    def setAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Set user allowed days"""
        # defaults
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setAllowedHours(pUserName, pDayNumber, pHourList)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess

    def setTimeLimitForDays(self, pUserName, pDayLimits):
        """Set user allowed limit for days"""
        # defaults
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLimitForDays(pUserName, pDayLimits)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess

    def setTrackInactive(self, pUserName, pTrackInactive):
        """Set user allowed days"""
        # defaults
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTrackInactive(pUserName, pTrackInactive)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess

    def setTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set user time left"""
        # defaults
        isSuccess = False

        # if we have end-point
        if self._timekprUserAdminInterface is not None:
            # notify through dbus
            try:
                # call dbus method
                result, message = self._timekprUserAdminInterface.setTimeLeft(pUserName, pOperation, pTimeLeft)

                # check call result
                if result != 0:
                    # show message to user as well
                    log.consoleOut("ERROR: %s" % (message))
                else:
                    # result
                    isSuccess = True
            except Exception:
                # we can not send notif through dbus
                self._timekprUserAdminInterface = None
                # we need to reschedule connecton (???????)

        # result
        return isSuccess
