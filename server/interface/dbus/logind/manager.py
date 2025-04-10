"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
import dbus
import time
import signal
from gi.repository import GLib

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc


class timekprUserLoginManager(object):
    """Class enables the connection with login1"""

    def __init__(self):
        """Initialize all stuff for login1"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start timekpr login1 manager")

        # variables
        self._login1Object = None
        self._login1ManagerInterface = None
        self._loginManagerVTNr = None
        self._loginManagerVTNrRetries = 0
        self._connectionRetryCount = 0

        # dbus initialization
        self._timekprBus = dbus.SystemBus()

        # init connections
        self._initDbusConnections()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish login1 manager")

    def _initDbusConnections(self):
        """Init connections to dbus"""
        # count retries
        self._connectionRetryCount += 1
        # if there was a connection before, give a big fat warning
        if self._login1ManagerInterface is not None:
            log.log(cons.TK_LOG_LEVEL_INFO, "IMPORTANT WARNING: connection to DBUS was lost, trying to establish it again, retry %i" % (self._connectionRetryCount))

        try:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "getting login1 object on DBUS")
            # dbus performance measurement
            misc.measureDBUSTimeElapsed(pStart=True)
            # try to get real connection to our objects and interface
            self._login1Object = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, cons.TK_DBUS_L1_PATH)
            # measurement logging
            misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_L1_OBJECT)

            log.log(cons.TK_LOG_LEVEL_DEBUG, "getting login1 interface on DBUS")

            # dbus performance measurement
            misc.measureDBUSTimeElapsed(pStart=True)
            # interface
            self._login1ManagerInterface = dbus.Interface(self._login1Object, cons.TK_DBUS_L1_MANAGER_INTERFACE)
            # measurement logging
            misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_L1_MANAGER_INTERFACE)

            log.log(cons.TK_LOG_LEVEL_DEBUG, "got interface, login1 successfully set up")

            # reset retries
            self._connectionRetryCount = 0
        except Exception as exc:
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting DBUS login manager: %s" % (exc))
            # reset connections
            self._login1ManagerInterface = None
            self._login1Object = None
            # raise error when too much retries
            if self._connectionRetryCount >= cons.TK_MAX_RETRIES:
                raise

    def _listUsers(self):
        """Exec ListUsers dbus methods (this is the only method which just has to succeed)"""
        # reset counter on retry
        self._connectionRetryCount = 0
        # def result
        loggedInUsersDBUS = None
        wasConnectionLost = False
        # try executing when there are retries left and there is no result
        while loggedInUsersDBUS is None and self._connectionRetryCount < cons.TK_MAX_RETRIES:
            # try get result
            try:
                # exec
                loggedInUsersDBUS = self._login1ManagerInterface.ListUsers()
            except Exception:
                # failure
                wasConnectionLost = True
                # no sleep on first retry
                if self._connectionRetryCount > 0:
                    # wait a little before retry
                    time.sleep(0.5)
                # retry connection
                self._initDbusConnections()
        # pass back the result
        return wasConnectionLost, loggedInUsersDBUS

    def getUserList(self, pSilent=False):
        """Go through a list of logged in users"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start getUserList") if not pSilent else True

        # get user list
        wasConnectionLost, loggedInUsersDBUS = self._listUsers()
        loggedInUsers = {}

        # loop through all users
        for rUser in loggedInUsersDBUS:
            # set up dict for every user
            loggedInUsers[str(rUser[1])] = {cons.TK_CTRL_UID: str(int(rUser[0])), cons.TK_CTRL_UNAME: str(rUser[1]), cons.TK_CTRL_UPATH: str(rUser[2])}

        # in case debug
        if not pSilent and log.isDebugEnabled():
            # get all properties
            for key, value in loggedInUsers.items():
                # optimize logging
                uNameLog = "USER: %s" % (key)
                # values and keys
                for keyx, valuex in value.items():
                    uNameLog = "%s, %s: %s" % (uNameLog, keyx, valuex)
                log.log(cons.TK_LOG_LEVEL_DEBUG, uNameLog)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish getUserList") if not pSilent else True

        # passing back user tuples
        return wasConnectionLost, loggedInUsers

    def getUserSessionList(self, pUserName, pUserPath):
        """Get up-to-date user session list"""
        # prepare return list
        userSessions = []

        # dbus performance measurement
        misc.measureDBUSTimeElapsed(pStart=True)
        # get dbus object
        login1UserObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, pUserPath)
        # measurement logging
        misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=pUserPath)

        # dbus performance measurement
        misc.measureDBUSTimeElapsed(pStart=True)
        # get dbus interface for properties
        login1UserInterface = dbus.Interface(login1UserObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
        # measurement logging
        misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_PROPERTIES_INTERFACE)

        # dbus performance measurement
        misc.measureDBUSTimeElapsed(pStart=True)
        # get all user sessions
        login1UserSessions = login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "Sessions")
        # measurement logging
        misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_USER_OBJECT)

        # go through all user sessions
        for rUserSession in login1UserSessions:
            # dbus performance measurement
            misc.measureDBUSTimeElapsed(pStart=True)
            # get dbus object
            login1SessionObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, str(rUserSession[1]))
            # measurement logging
            misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=str(rUserSession[1]))

            # dbus performance measurement
            misc.measureDBUSTimeElapsed(pStart=True)
            # get dbus interface for properties
            login1SessionInterface = dbus.Interface(login1SessionObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
            # measurement logging
            misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_PROPERTIES_INTERFACE)

            # get all user session properties
            try:
                # dbus performance measurement
                misc.measureDBUSTimeElapsed(pStart=True)
                # properties
                sessionType = str(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Type"))
                sessionVTNr = str(int(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "VTNr")))
                sessionSeat = str(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Seat")[0])
                sessionState = str(login1SessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "State"))
                # measurement logging
                misc.measureDBUSTimeElapsed(pStop=True, pDbusIFName=cons.TK_DBUS_SESSION_OBJECT)

                # add user session to return list
                userSessions.append({"sessionId": str(rUserSession[0]), "sessionPath": str(rUserSession[1]), "type": sessionType, "vtnr": sessionVTNr, "seat": sessionSeat, "state": sessionState})
            except Exception as exc:
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting session properties for session \"%s\" DBUS: %s" % (str(rUserSession[1]), exc))
            
            # free
            del login1SessionInterface, login1SessionObject

        # free
        del login1UserSessions, login1UserInterface, login1UserObject

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
                if loginSessionVTNr is not None and loginSessionVTNr != "":
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

    def switchTTY(self, pSeatId, pForce):
        """Swith TTY for login screen"""
        # defaults
        willSwitchTTY = True
        # switch to right TTY (if needed)
        if self._loginManagerVTNr is None:
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: switching TTY is not possible, login manager TTY was not found")
            willSwitchTTY = False
        elif pSeatId is not None and pSeatId != "":
            # get all necessary objects from DBUS to switch the TTY
            try:
                # it appears that sometimes seats are not available (RDP may not have it)
                seat = self._login1ManagerInterface.GetSeat(pSeatId)
            except Exception as exc:
                # cannot switch as we can't get seat
                willSwitchTTY = False
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting seat (%s) from DBUS: %s" % (str(pSeatId), exc))

            # only if we got the seat
            if willSwitchTTY:
                # seat object processing
                login1SeatObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, seat)
                login1SeatInterface = dbus.Interface(login1SeatObject, cons.TK_DBUS_SEAT_OBJECT)
                log.log(cons.TK_LOG_LEVEL_INFO, "INFO:%s switching TTY to %s" % (" (forced)" if pForce else "", self._loginManagerVTNr))
                # finally switching the TTY
                if cons.TK_DEV_ACTIVE:
                    log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not switching my sessions, sorry...")
                else:
                    # finally switching the TTY
                    login1SeatInterface.SwitchTo(self._loginManagerVTNr)
                # free
                del login1SeatInterface, login1SeatObject, seat
        else:
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: switching TTY is not needed")
            # will not switch
            willSwitchTTY = False

        # in case switch is needed, reschedule it (might not work from first try)
        if willSwitchTTY and not pForce:
            # schedule a switch
            GLib.timeout_add_seconds(cons.TK_POLLTIME, self.switchTTY, pSeatId, True)

        # return false for repeat schedule to be discarded
        return False

    def terminateUserSessions(self, pUserName, pUserPath, pTimekprConfig, pRestrictionType):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start terminateUserSessions")
        log.log(cons.TK_LOG_LEVEL_DEBUG, "inspecting \"%s\" userpath \"%s\" sessions" % (pUserName, pUserPath))

        # get user session list
        userSessionList = self.getUserSessionList(pUserName, pUserPath)
        # indication whether we are killing smth
        sessionsToKill = 0
        lastSeat = None
        userActive = False

        # go through all user sessions
        for rUserSession in userSessionList:
            # if we support this session type and it is not specifically excluded, only then we kill it
            if rUserSession["type"] in pTimekprConfig.getTimekprSessionsCtrl() and rUserSession["type"] not in pTimekprConfig.getTimekprSessionsExcl():
                log.log(cons.TK_LOG_LEVEL_INFO, "(delayed 0.1 sec) killing \"%s\" session \"%s\" (%s, %s)" % (pUserName, rUserSession["sessionPath"], rUserSession["sessionId"], rUserSession["type"]))
                # killing time
                if cons.TK_DEV_ACTIVE:
                    log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not killing myself, sorry...")
                elif pRestrictionType == cons.TK_CTRL_RES_K:
                    GLib.timeout_add_seconds(0.1, self._login1ManagerInterface.KillSession, rUserSession["sessionId"], "all", signal.SIGTERM)
                else:
                    GLib.timeout_add_seconds(0.1, self._login1ManagerInterface.TerminateSession, rUserSession["sessionId"])
                # get last seat
                lastSeat = rUserSession["seat"] if rUserSession["seat"] is not None and rUserSession["seat"] != "" and rUserSession["vtnr"] is not None and rUserSession["vtnr"] != "" and self._loginManagerVTNr != rUserSession["vtnr"] else lastSeat
                # determine whether user is active
                userActive = userActive or rUserSession["state"] == "active"
                # count sessions to kill
                sessionsToKill += 1
            else:
                log.log(cons.TK_LOG_LEVEL_INFO, "saving \"%s\" session %s (%s)" % (pUserName, rUserSession["sessionPath"], rUserSession["type"]))

        # kill leftover processes (if we are killing smth)
        if sessionsToKill > 0 and userActive and lastSeat is not None:
            # timeout
            tmo = cons.TK_POLLTIME - 1
            # switch TTY
            log.log(cons.TK_LOG_LEVEL_INFO, "scheduling a TTY switch sequence after %i seconds" % (tmo))
            # schedule a switch
            GLib.timeout_add_seconds(tmo, self.switchTTY, lastSeat, False)
        else:
            log.log(cons.TK_LOG_LEVEL_INFO, "TTY switch ommitted for user %s" % (pUserName))

        # cleanup
        if sessionsToKill > 0:
            # timeout
            tmo = cons.TK_POLLTIME * 2 + 1
            # dispatch a killer for leftovers
            log.log(cons.TK_LOG_LEVEL_INFO, "dipatching a killer for leftover processes after %i seconds" % (tmo))
            # schedule leftover processes to be killed (it's rather sophisticated killing and checks whether we need to kill gui or terminal processes)
            GLib.timeout_add_seconds(tmo, misc.killLeftoverUserProcesses, pUserName, pTimekprConfig)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish terminateUserSessions")

    def suspendComputer(self, pUserName):
        """Suspend computer"""
        # only if we are not in DEV mode
        if cons.TK_DEV_ACTIVE:
            log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not suspending myself, sorry...")
        else:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "start suspendComputer in the name of \"%s\"" % (pUserName))
            GLib.timeout_add_seconds(0.1, self._login1ManagerInterface.Suspend, False)

    def shutdownComputer(self, pUserName):
        """Shutdown computer"""
        # only if we are not in DEV mode
        if cons.TK_DEV_ACTIVE:
            log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not issuing shutdown for myself, sorry...")
        else:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "start shutdownComputer in the name of \"%s\"" % (pUserName))
            GLib.timeout_add_seconds(0.1, self._login1ManagerInterface.PowerOff, False)
