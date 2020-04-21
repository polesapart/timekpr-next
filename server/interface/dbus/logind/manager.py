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
        self._loginManagerVTNr = None
        self._loginManagerVTNrRetries = 0

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

    def getUserList(self, pSilent=False):
        """Go through a list of logged in users"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start getUserList") if not pSilent else True

        # get user list
        loggedInUsersDBUS = self._login1ManagerInterface.ListUsers()
        loggedInUsers = {}

        # loop through all users
        for rUser in loggedInUsersDBUS:
            # set up dict for every user
            loggedInUsers[str(rUser[1])] = {cons.TK_CTRL_UID: str(int(rUser[0])), cons.TK_CTRL_UNAME: str(rUser[1]), cons.TK_CTRL_UPATH: str(rUser[2])}

        # in case debug
        if not pSilent and log.isDebug():
            # get all properties
            for key, value in loggedInUsers.items():
                # optimize logging
                uNameLog = "USER: %s" % (key)
                # values and keys
                for keyx, valuex in value.items():
                    uNameLog = "%s, %s: %s" % (uNameLog, keyx, valuex)
            log.log(cons.TK_LOG_LEVEL_DEBUG, uNameLog)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish getUserList") if not pSilent else True

        # passing back user tuples
        return loggedInUsers

    def getUserSessionList(self, pUserName, pUserPath):
        """Get up-to-date user session list"""
        # prepare return list
        userSessions = []

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
        login1UserSessions = login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "Sessions")
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting sessions for \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # go through all user sessions
        for userSession in login1UserSessions:
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
            sessionVTNr = str(int(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "VTNr")))
            sessionSeat = str(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Seat")[0])
            # measurement logging
            log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting \"%s\" took too long (%is)" % (cons.TK_DBUS_SESSION_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

            # add user session to return list
            userSessions.append({"session": userSession, "type": sessionType, "vtnr": sessionVTNr, "seat": sessionSeat})

        # return sessions
        return userSessions

    def determineLoginManagerVT(self, pUserName, pUserPath):
        """Get login manager session VTNr"""
        # if we did not yet find a login manager VTNr
        if self._loginManagerVTNr is None and self._loginManagerVTNrRetries < cons.TK_MAX_RETRIES:
            # def
            loginManager = None
            # loop through login managers
            for rLMan in cons.TK_USERS_LOGIN_MANAGERS.split(";"):
                # since we are checking this with UID less than 1K (or whatever is configured in limits file)
                # we can safely compare usernames or try to use LIKE operator on user name
                # exact match
                if rLMan == pUserName:
                    # we found one
                    loginManager = pUserName
                else:
                    # try to determine if we found one (according to "3.278 Portable Filename Character Set" additional symbols are ._-)
                    for rSymb in (".", "_", "-"):
                        # check for name
                        if "%s%s" % (rSymb, rLMan) in pUserName or "%s%s%s" % (rSymb, rLMan, rSymb) in pUserName or "%s%s" % (rLMan, rSymb) in pUserName:
                            # we found one
                            loginManager = pUserName
                            # first match is ok
                            break

            # determine if we have one like manager
            if loginManager is not None:
                # advance counter
                self._loginManagerVTNrRetries += 1
                # log
                log.log(cons.TK_LOG_LEVEL_DEBUG, "INFO: searching for login manager (%s) VTNr" % (pUserName))
                # VTNr (default)
                loginSessionVTNr = None
                # get user session list
                userSessionList = self.getUserSessionList(pUserName, pUserPath)
                # loop through users and try to guess login managers
                for rSession in userSessionList:
                    # check whether user seems to be login manager user
                    if rSession["type"] in cons.TK_SESSION_TYPES_CTRL:
                        # we got right session, save VTNr
                        loginSessionVTNr = rSession["vtnr"]
                        # done
                        break
                # if we found login manager VTNr
                if loginSessionVTNr is not None:
                    # return VTNr
                    self._loginManagerVTNr = loginSessionVTNr
                    # seat is found
                    log.log(cons.TK_LOG_LEVEL_INFO, "INFO: login manager (%s) TTY found: %s" % (pUserName, self._loginManagerVTNr))
            else:
                # log
                log.log(cons.TK_LOG_LEVEL_DEBUG, "INFO: searching for login manager, user (%s) does not look like one" % (pUserName))
        # in case we tried hard
        elif self._loginManagerVTNr is None and self._loginManagerVTNrRetries == cons.TK_MAX_RETRIES:
            # advance counter (so we never get here again)
            self._loginManagerVTNrRetries += 1
            # seat is NOT found and we'll not try to find it anymore
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: login manager (%s) TTY is NOT found, giving up until restart" % (pUserName))

    def switchTTY(self, pSeatId, pSessionTTY):
        """Swith TTY for login screen"""
        # switch to right TTY (if needed)
        if self._loginManagerVTNr is not None and pSessionTTY is not None and pSeatId is not None and pSessionTTY != self._loginManagerVTNr:
            # get all necessary objects from DBUS to switch the TTY
            seat = self._login1ManagerInterface.GetSeat(pSeatId)
            login1SeatObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, seat)
            login1SeatInterface = dbus.Interface(login1SeatObject, cons.TK_DBUS_SEAT_OBJECT)
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO:%s switching TTY to %s" % (" (forced)" if pSessionTTY == "999" else "", self._loginManagerVTNr))
            # finally switching the TTY
            login1SeatInterface.SwitchTo(self._loginManagerVTNr)
        else:
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: switching TTY is not needed")

    def terminateUserSessions(self, pUserName, pUserPath, pSessionTypes):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start terminateUserSessions")
        log.log(cons.TK_LOG_LEVEL_DEBUG, "inspecting \"%s\" userpath \"%s\" sessions" % (pUserName, pUserPath))

        # get user session list
        userSessionList = self.getUserSessionList(pUserName, pUserPath)
        # indication whether we are killing smth
        sessionsToKill = 0
        lastSeat = None

        # go through all user sessions
        for userSession in userSessionList:
            # if excludeTTY and sessionType not in ("unspecified", "tty"):
            if userSession["type"] in pSessionTypes:
                # switch TTY (it will switch only when needed)
                lastSeat = userSession["seat"]
                self.switchTTY(lastSeat, userSession["vtnr"])
                # killing time
                if cons.TK_DEV_ACTIVE:
                    log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not killing myself, sorry...")
                else:
                    log.log(cons.TK_LOG_LEVEL_INFO, "(delayed 1 sec) killing \"%s\" session %s (%s)" % (pUserName, str(userSession["session"][1]), str(userSession["type"])))
                    GLib.timeout_add_seconds(1, self._login1ManagerInterface.TerminateSession, userSession["session"][0])
                # count sessions to kill
                sessionsToKill += 1
            else:
                log.log(cons.TK_LOG_LEVEL_INFO, "saving \"%s\" session %s (%s)" % (pUserName, str(userSession["session"][1]), str(userSession["type"])))

        # kill leftover processes (if we are killing smth)
        if sessionsToKill > 0:
            # before this, try to switch TTY again (somehow sometimes it's not switched)
            self.switchTTY(lastSeat, "999")
            # schedule leftover processes to be killed (it's rather sophisticated killing and checks whether we need to kill gui or terminal processes)
            GLib.timeout_add_seconds(cons.TK_POLLTIME, misc.killLeftoverUserProcesses, self._logging, pUserName, pSessionTypes)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish terminateUserSessions")
