"""
Created on Aug 28, 2018.

@author: mjasnik
"""

# import section
import dbus
import os
import stat

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils import misc


class timekprUserManager(object):
    """A connection with login1 and other DBUS servers."""

    def __init__(self, pLog, pUserName, pUserPathOnBus):
        """Initialize manager."""
        # init logging firstly
        log.setLogging(pLog)

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

    def cacheUserSessionList(self):
        """Determine user sessions and cache session objects for further reference."""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== start cacheUserSessionList for \"%s\" ===---" % (self._userName))
        # dbus performance measurement
        misc.measureTimeElapsed(pStart=True)
        # get all user sessions
        userSessions = self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "Sessions")
        # measurement logging
        log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - getting sessions for \"%s\" took too long (%is)" % (cons.TK_DBUS_USER_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

        log.log(cons.TK_LOG_LEVEL_DEBUG, "got %i sessions, start loop" % (len(userSessions)))
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, str(userSessions))

        # init active sessions
        activeSessions = {}

        # go through all user sessions
        for userSession in userSessions:
            # sessionId & sessionPath on dbus
            sessionId = str(userSession[0])
            sessionPath = str(userSession[1])
            # save active sessions
            activeSessions[sessionId] = 0

            # if we have not yet saved a user session, let's do that to improve interaction with dbus
            if sessionId not in self._timekprUserSessions:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "adding session: %s" % (sessionId))
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # get object and interface to save it
                sessionObject = self._timekprBus.get_object(cons.TK_DBUS_L1_OBJECT, sessionPath)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_L1_OBJECT, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # get object and interface to save it
                sessionInterface = dbus.Interface(sessionObject, cons.TK_DBUS_PROPERTIES_INTERFACE)
                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - acquiring \"%s\" took too long (%is)" % (cons.TK_DBUS_PROPERTIES_INTERFACE, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True

                # cache sessions
                self._timekprUserSessions[sessionId] = {cons.TK_CTRL_DBUS_SESS_OBJ: sessionObject, cons.TK_CTRL_DBUS_SESS_IF: sessionInterface, cons.TK_CTRL_DBUS_SESS_PROP: {}}

                # add static properties
                self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["Type"] = str(sessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Type"))
                self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["VTNr"] = str(int(sessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "VTNr")))
                self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["Seat"] = str(sessionInterface.Get(cons.TK_DBUS_SESSION_OBJECT, "Seat")[0])
            else:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "session already cached: %s" % (sessionId))

        # list of sessions to delete
        removableSesssions = {}

        # collect sessions not on the list
        for userSession in self._timekprUserSessions:
            # user session is not found
            if userSession not in activeSessions:
                removableSesssions[userSession] = 0

        # get rid of sessions not on the list
        for userSession in removableSesssions:
            log.log(cons.TK_LOG_LEVEL_DEBUG, "removing session: %s" % (userSession))
            self._timekprUserSessions.pop(userSession)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== finish cacheUserSessionList for \"%s\" ===---" % (self._userName))

    def cacheUserDBUSSession(self):
        """
        Connect to user DBUS (a hackinsh and no-welcome way, but what can we do).

        This bascially switches timekpr to actual user id for a small amount of time, but since
        python standard implementation runs just one thread at a time, this, theoretically, should not be a problem.
        """
        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== start cacheUserDBUSSession for \"%s\" ===---" % (self._userName))

        # check whether we are already connected to user DBUS
        if cons.TK_DBUS_USER_SCR_OBJECT_NAME not in self._timekprUserObjects:
            # final socket path
            socketPath = None

            # determine user DBUS socket
            for path in cons.TK_DBUS_USER_PATHS:
                # determine if path is socket
                if stat.S_ISSOCK(os.stat(path % str(self._userId)).st_mode):
                    socketPath = "unix:path=%s" % (path % str(self._userId))
                    break

            # we have a socket
            if socketPath is not None:
                # temporarily we act as a user
                if not cons.TK_DEV_ACTIVE:
                    os.seteuid(self._userId)
                # when switched to non-root user, we need to save errors, otherwise we'll not be able to log them
                errors = []

                # try all paths possible
                for i in range(0, 1+1):
                    try:
                        # make a connection to user DBUS and try to get user screensaver object
                        self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME] = dbus.Interface(dbus.bus.BusConnection(socketPath).get_object(cons.TK_DBUS_USER_SCR_OBJECTS[i], cons.TK_DBUS_USER_SCR_PATHS[i]), cons.TK_DBUS_USER_SCR_OBJECTS[i])
                        # try get values (Gnome for instance, did not implement normal freedekstop spec and it returns "method not implemented" only when called)
                        self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME].GetActive()
                        # get out at first success
                        break
                    except Exception as exc:
                        # save errors
                        errors.append(str(exc))
                        # object is not found
                        self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME] = None

                # switch to SU mode
                if not cons.TK_DEV_ACTIVE:
                    # get back to root
                    os.seteuid(0)
                    os.setegid(0)

                # log errors
                for rErr in errors:
                    log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting USER DBUS: %s" % (rErr))
                # if have a successful connection
                if self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME] is not None:
                    log.log(cons.TK_LOG_LEVEL_INFO, "connected to user \"%s\" DBUS for screensaver status" % (self._userName))
            else:
                # no connection
                self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME] = None

            # warn
            if self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME] is None:
                # no connection
                self._timekprUserObjects.pop(cons.TK_DBUS_USER_SCR_OBJECT_NAME)
                log.log(cons.TK_LOG_LEVEL_INFO, "screen locking detection for user \"%s\" WILL NOT WORK" % (self._userName))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== finish cacheUserDBUSSession for \"%s\" ===---" % (self._userName))

    def isUserScreenSaverActive(self):
        """Check if user screensaver is active. This may fail, since user is unpredictable, so we need to try again."""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== start isUserScreenSaverActive for \"%s\" ===---" % (self._userName))
        # by default screensave is not acttive
        isActive = False

        # we do this only when retries allow us and we actuall have a connection
        if self._scrRetryCnt < cons.TK_MAX_RETRIES and cons.TK_DBUS_USER_SCR_OBJECT_NAME in self._timekprUserObjects:
            try:
                # try getting status from user DBUS
                isActive = self._timekprUserObjects[cons.TK_DBUS_USER_SCR_OBJECT_NAME].GetActive()
            except Exception as exc:
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: error getting screensaver status from USER DBUS for %d time: %s" % (self._scrRetryCnt, exc))
                # we do not have a connection and this time it will return False
                self._timekprUserObjects.pop(cons.TK_DBUS_USER_SCR_OBJECT_NAME)
                # add to retry
                self._scrRetryCnt += 1

        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== finish isUserScreenSaverActive for \"%s\" ===---" % (self._userName))

        # return whether user screensaver is active
        return isActive

    def isUserActive(self, pSessionTypes, pTrackInactive):
        """Check if user is active."""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== start isUserActive for \"%s\" ===---" % (self._userName))
        log.log(cons.TK_LOG_LEVEL_DEBUG, "supported session types: %s" % (str(pSessionTypes)))

        # get all user sessions
        userState = str(self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "State"))
        userIdleState = str(bool(self._login1UserInterface.Get(cons.TK_DBUS_USER_OBJECT, "IdleHint")))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "user stats, state: %s, idleState: %s" % (userState, userIdleState))

        # cache sessions
        self.cacheUserSessionList()
        # cache user screensaver objects
        self.cacheUserDBUSSession()

        # to determine if user is active for all sessions:
        #    session must not be "active"
        #    idlehint must be true
        #    special care must be taken for tty sessions
        #    screenlocker status from user DBUS session

        # init active sessions
        userActive = False

        # is user screensaver active
        screenLocked = self.isUserScreenSaverActive()

        # if user locked the computer
        if screenLocked and not pTrackInactive:
            # user is not active
            log.log(cons.TK_LOG_LEVEL_DEBUG, "session inactive (verified by user \"%s\" screensaver status), sessions won't be checked" % (self._userName))
        else:
            # go through all user sessions
            for sessionId in self._timekprUserSessions:
                # dbus performance measurement
                misc.measureTimeElapsed(pStart=True)

                # get needed static properties
                sessionType = self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["Type"]
                sessionVTNr = self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_PROP]["VTNr"]
                # get needed properties
                sessionState = str(self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "State"))
                sessionIdleState = str(bool(self._timekprUserSessions[sessionId][cons.TK_CTRL_DBUS_SESS_IF].Get(cons.TK_DBUS_SESSION_OBJECT, "IdleHint")))

                # measurement logging
                log.log(cons.TK_LOG_LEVEL_INFO, "PERFORMANCE (DBUS) - property get for session \"%s\" took too long (%is)" % (sessionId, misc.measureTimeElapsed(pResult=True))) if misc.measureTimeElapsed(pStop=True) >= cons.TK_DBUS_ANSWER_TIME else True
                log.log(cons.TK_LOG_LEVEL_DEBUG, "got session - type: %s, VTNr: %s, state: %s, idle: %s" % (sessionType, sessionVTNr, sessionState, sessionIdleState))

                # check if active
                if sessionState == "active" and sessionIdleState == "False":
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s active" % (sessionId))

                    # validate against session types we manage
                    if sessionType not in pSessionTypes:
                        # session is not on the list of session types we track
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "    session %s excluded (thus effectively inactive)" % (sessionId))
                    else:
                        # session is on the list of session types we track and session is active
                        userActive = True
                elif sessionType in pSessionTypes:
                    # user is not active
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s inactive" % (sessionId))

                    # if we track inactive
                    if pTrackInactive:
                        # we track inactive sessions
                        userActive = True

                        # session is not on the list of session types we track
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "    session %s included as active (we track inactive sessions)" % (sessionId))
                else:
                    # session is not on the list of session types we track
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "session %s not tracked" % (sessionId))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "---=== finish isUserActive: %s ===---" % (str(userActive)))

        # return whether user is active
        return userActive
