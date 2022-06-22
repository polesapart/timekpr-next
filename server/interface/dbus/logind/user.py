"""
Created on Aug 28, 2018.

@author: mjasnik
"""

# import section
import dbus

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc


class timekprUserManager(object):
    """A connection with login1 and other DBUS servers."""

    def __init__(self, pUserName, pUserPathOnBus):
        """Initialize manager."""

        # save the bus and user
        self._timekprBus = dbus.SystemBus()
        self._userName = pUserName

        # dbus performance measurement
        misc.measureTimeElapsed(pStart=True)

        # get dbus object
        self._login1UserObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, pUserPathOnBus)
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_L1_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # get dbus interface for properties
        self._login1UserInterface = dbus.Interface(self._login1UserObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_PROPERTIES_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        # user sessions & additional DBUS objects
        self._timekprUserSessions = {}
        self._timekprUserObjects = {}

        # get user ID
        self._userId = int(self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "UID"))
        self._scrRetryCnt = 0
        self._sessionLockedStateAvailable = None

    def cacheUserSessionList(self):
        """Determine user sessions and cache session objects for further reference."""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "---=== start cacheUserSessionList for \"%s\" ===---" % (self._userName))
        # dbus performance measurement
        misc.measureTimeElapsed(pStart=True)
        # get all user sessions
        userSessions = self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "Sessions")
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting sessions for \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "got %i sessions: %s, start loop" % (len(userSessions), str(userSessions)))

        # init active sessions
        activeSessions = []

        # go through all user sessions
        for rUserSession in userSessions:
            # sessionId & sessionPath on dbus
            sessionId = str(rUserSession[0])
            sessionPath = str(rUserSession[1])
            # save active sessions
            activeSessions.append(sessionId)

            # if we have not yet saved a user session, let's do that to improve interaction with dbus
            if sessionId not in self._timekprUserSessions:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "adding session: %s, %s" % (sessionId, sessionPath))
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # get object and interface to save it
                sessionObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, sessionPath)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_L1_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # get object and interface to save it
                sessionPropertiesInterface = dbus.Interface(sessionObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_PROPERTIES_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # get dbus interface for Session
                sessionInterface = dbus.Interface(sessionObject, cons.TK_DBUS_SESSION_OBJECT)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_SESSION_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # cache sessions
                self._timekprUserSessions[sessionId] = {cons.TK_CTRL_DBUS_SESS_OBJ: sessionObject, cons.TK_CTRL_DBUS_SESS_IF: sessionInterface, cons.TK_CTRL_DBUS_SESS_PROP_IF: sessionPropertiesInterface, cons.TK_CTRL_DBUS_SESS_PROP: {}}

                # add static properties
                self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["VTNr"] = str(int(sessionPropertiesInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "VTNr")))
                self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["Seat"] = str(sessionPropertiesInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Seat")[0])
            else:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "session already cached: %s" % (sessionId))

        # list of sessions to delete
        removableSesssions = [rUserSession for rUserSession in self._timekprUserSessions if rUserSession not in activeSessions]

        # get rid of sessions not on the list
        for userSession in removableSesssions:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "removing session: %s" % (userSession))
            self._timekprUserSessions.pop(userSession)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "---=== finish cacheUserSessionList for \"%s\" ===---" % (self._userName))

    def isUserActive(self, pTimekprConfig, pTimekprUserConfig, pIsScreenLocked):
        """Check if user is active."""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== start isUserActive for \"%s\" ===---" % (self._userName))
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "supported session types: %s" % (str(pTimekprConfig.getTimekprSessionsCtrl())))

        # get all user sessions
        userState = str(self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "State"))
        userIdleState = str(bool(self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "IdleHint")))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "user stats, ul1st: %s, ul1idlhnt: %s, uscrlck: %s" % (userState, userIdleState, str(pIsScreenLocked)))

        # cache sessions
        self.cacheUserSessionList()

        # to determine if user is active for all sessions:
        #    session must not be "active"
        #    idlehint must be true
        #    special care must be taken for tty sessions
        #    screenlocker status from user DBUS session

        # init active sessions
        userActive = userScreenLocked = False
        sessionLockedState = "False"

        # if user locked the computer
        if pIsScreenLocked and not pTimekprUserConfig.getUserTrackInactive():
            # user is not active
            log.log(cons.TK_LOG_LEVEL_DEBUG, "session inactive (verified by user \"%s\" screensaver status), sessions won't be checked" % (self._userName))
        else:
            # go through all user sessions
            for rSessionId in self._timekprUserSessions:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)
                sessionLockedState = "False"

                # get needed static properties
                sessionVTNr = self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP]["VTNr"]
                # get needed properties
                sessionType = str(self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "Type"))
                sessionState = str(self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "State"))
                sessionIdleState = str(bool(self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "IdleHint")))
                # get locked state, only if it's available
                if self._sessionLockedStateAvailable or self._sessionLockedStateAvailable is None:
                    try:
                        # get locked state
                        sessionLockedState = str(bool(self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "LockedHint")))
                        # locked state available
                        if self._sessionLockedStateAvailable is None:
                            # state used
                            self._sessionLockedStateAvailable = True
                            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: session locked state is available and will be used for idle state detection (if it works)")
                    except:
                        # locked state not used
                        self._sessionLockedStateAvailable = False
                        log.log(cons.TK_LOG_LEVEL_INFO, "INFO: session locked state is NOT available, will rely on client screensaver state (if it works)")

                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - property get for session \"%s\" took too long (%is)" % (rSessionId, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                log.log(cons.TK_LOG_LEVEL_DEBUG, "session stats, styp: %s, sVTNr: %s, sl1St: %s, sl1idlst: %s, sl1lckst: %s" % (sessionType, sessionVTNr, sessionState, sessionIdleState, sessionLockedState))

                # check if active
                if sessionState == "active" and sessionIdleState == "False" and sessionLockedState == "False":
                    # validate against session types we specifically do not track
                    if sessionType in pTimekprConfig.getTimekprSessionsExcl():
                        # session is on the list of session types we specifically do not track
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s is active, but session type \"%s\" is excluded from tracking (thus effectively inactive)" % (rSessionId, sessionType))
                    # validate against session types we manage
                    elif sessionType not in pTimekprConfig.getTimekprSessionsCtrl():
                        # session is not on the list of session types we track
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s is active, but session type \"%s\" is not on tracked type list (thus effectively inactive)" % (rSessionId, sessionType))
                    else:
                        # session is on the list of session types we track and session is active
                        userActive = True
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s active" % (rSessionId))
                elif sessionType in pTimekprConfig.getTimekprSessionsCtrl():
                    # do not count lingering and closing sessions as active either way
                    # lingering  - user processes are around, but user not logged in
                    # closing - user logged out, but some processes are still left
                    if sessionState in ("lingering", "closing"):
                        # user is not active
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s is inactive (not exactly logged in too)" % (rSessionId))
                    # if we track inactive
                    elif pTimekprUserConfig.getUserTrackInactive():
                        # we track inactive sessions
                        userActive = True
                        # session is not on the list of session types we track
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s included as active (track inactive sessions enabled)" % (rSessionId))
                    else:
                        # session is not active
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s inactive" % (rSessionId))
                else:
                    # session is not on the list of session types we track
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s is inactive and not tracked" % (rSessionId))

        # screen lock state
        userScreenLocked = (pIsScreenLocked or sessionLockedState == "True")

        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== finish isUserActive: %s ===---" % (str(userActive)))

        # return whether user is active
        return userActive, userScreenLocked

    def lockUserSessions(self):
        """Ask login manager to lock user sessions"""
        # go through all user sessions
        for rSessionId in self._timekprUserSessions:
            # we lock only GUI sessions
            if str(self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_PROP_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "Type")) in cons.TK_SESSION_TYPES_CTRL:
                # lock session
                self._timekprUserSessions[rSessionId][cons.TK_CTRL_DBUS_SESS_IF].Lock()
