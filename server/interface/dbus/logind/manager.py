"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
import dbus
from gi.repository import GLib

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc


class timekprUserLoginManager(object):
    """Class enables the connection with login1"""

    def __init__(self, pLog):
        """Initialize all stuff for login1"""
        # init logging firstly
        self._logging = pLog
        log.setLogging(self._logging)

        log.log(cons.TK_LOG_LEVEL_INFO, "start timekpr login1 manager")

        # variables
        self._login1Object = None
        self._login1ManagerInterface = None

        # dbus initialization
        self._timekprBus = dbus.SystemBus()

        try:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "getting login1 object on DBUS")
            # dbus performance measurement
            misc.measureTimeElapsed(pStart=True)

            # try to get real connection to our objects and interface
            self._login1Object = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, cons.TK_DBUS_L1_PATH)
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_L1_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            log.log(cons.TK_LOG_LEVEL_DEBUG, "getting login1 interface on DBUS")

            self._login1ManagerInterface = dbus.Interface(self._login1Object, cons.TK_DBUS_L1_MANAGER_INTERFACE)
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_L1_MANAGER_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            log.log(cons.TK_LOG_LEVEL_DEBUG, "got interface, login1 successfully set up")
        except Exception as exc:
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting DBUS: %s" % (exc))
            raise

        log.log(cons.TK_LOG_LEVEL_INFO, "finish login1 manager")

    def getUserList(self):
        """Go through a list of logged in users"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start getUserList")

        # get user list
        loggedInUsersDBUS = self._login1ManagerInterface.ListUsers()
        loggedInUsers = {}

        # loop through all users
        for rUser in loggedInUsersDBUS:
            # set up dict for every user
            loggedInUsers[str(rUser[1])] = {cons.TK_CTRL_UID: str(rUser[0]), cons.TK_CTRL_UNAME: str(rUser[1]), cons.TK_CTRL_UPATH: str(rUser[2])}

        # in case debug
        if log.isDebug():
            for key, value in loggedInUsers.items():
                log.log(cons.TK_LOG_LEVEL_DEBUG, "userid: %s" % (key))
                for keyx, valuex in value.items():
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "    %s: %s" % (keyx, valuex))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish getUserList")

        # passing back user tuples
        return loggedInUsers

    def terminateUserSessions(self, pUser, pUserPath, pSessionTypes):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start terminateUserSessions")
        log.log(cons.TK_LOG_LEVEL_DEBUG, "inspecting \"%s\" userpath \"%s\" sessions" % (pUser, pUserPath))

        # dbus performance measurement
        misc.measureTimeElapsed(pStart=True)

        # get dbus object
        login1UserObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, pUserPath)
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (pUserPath, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # get dbus interface for properties
        login1UserInterface = dbus.Interface(login1UserObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_PROPERTIES_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # dbus performance measurement
        misc.measureTimeElapsed(pStart=True)

        # get all user sessions
        userSessions = login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "Sessions")
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting sessions for \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # go through all user sessions
        for userSession in userSessions:
            # dbus performance measurement
            misc.measureTimeElapsed(pStart=True)

            # get dbus object
            login1SessionObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, str(userSession[1]))
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (str(userSession[1]), misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            # get dbus interface for properties
            login1SessionInterface = dbus.Interface(login1SessionObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_PROPERTIES_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            # get all user sessions
            sessionType = str(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Type"))
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting \"%s\" took too long (%is)" % (cons.TK_DBUS_SESSION_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            log.log(cons.TK_LOG_LEVEL_DEBUG, "got session type: %s" % (sessionType))

            # if excludeTTY and sessionType not in ("unspecified", "tty"):
            if sessionType in pSessionTypes:
                log.log(cons.TK_LOG_LEVEL_INFO, "killing %s session %s (%s)" % (pUser, str(userSession[1]), str(userSession[0])))
                self._login1ManagerInterface.TerminateSession(userSession[0])
            else:
                log.log(cons.TK_LOG_LEVEL_INFO, "saving %s session %s" % (pUser, str(userSession[1])))

        # kill leftover processes
        GLib.timeout_add_seconds(cons.TK_POLLTIME, misc.killLeftoverUserProcesses, self._logging, pUser, pSessionTypes)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish terminateUserSessions")
