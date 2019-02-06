"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import time
import threading
import traceback

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.server.interface.dbus.logind import manager as l1_manager
from timekpr.common.utils.config import timekprConfig
from timekpr.server.user.user import timekprUser
from timekpr.server.user.configprocessor import timekprUserConfigurationProcessor

# default dbus
DBusGMainLoop(set_as_default=True)


class timekprDaemon(dbus.service.Object):
    """Main daemon class"""

    # --------------- initialization / control methods --------------- #
    def __init__(self, pIsDevActive=False):
        """Initialize daemon variables"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init dbus daemon")

        # is dev
        self._isDevActive = pIsDevActive
        # get our bus
        self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
        # get our bus name (where clients will find us)
        self._timekprBusName = dbus.service.BusName(cons.TK_DBUS_BUS_NAME, bus=self._timekprBus, replace_existing=True)
        # init DBUS
        super().__init__(self._timekprBusName, cons.TK_DBUS_SERVER_PATH)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init dbus daemon")

    def initTimekpr(self):
        """Init all the required attributes"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start init daemon data")

        # ## variables ##
        # init main loop
        self._timekprMainLoop = GLib.MainLoop()
        # init termination trigger
        self._finishExecution = False
        # this will define login manager
        self._timekprLoginManagerName = "L1"
        # this will define login manager
        self._timekprLoginManager = None
        # this will define main timekpr configuration loader
        self._timekprConfigManager = None
        # this will hold all timekpr users (collection of user class)
        self._timekprUserList = {}
        # this will hold collection of users to be terminated
        self._timekprUserTerminationList = {}

        # ## initialization ##
        # configuration init
        self._timekprConfigManager = timekprConfig(pIsDevActive=self._isDevActive)
        self._timekprConfigManager.loadMainConfiguration()

        # save logging for later use in classes down tree
        self._logging = {cons.TK_LOG_L: self._timekprConfigManager.getTimekprLoglevel(), cons.TK_LOG_D: self._timekprConfigManager.getTimekprLogfileDir()}

        # logging init
        log.setLogging(self._logging)

        # in case we are dealing with logind
        if self._timekprLoginManagerName == "L1":
            self._timekprLoginManager = l1_manager.timekprUserLoginManager(self._logging)
        # in case we are dealing with consolekit (WHICH IS NOT IMPLEMENTED YET and might NOT be AT ALL)
        elif self._timekprLoginManagerName == "CK":
            self._timekprLoginManager = None

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish init daemon data")

    def finishTimekpr(self, signal=None, frame=None):
        """Exit timekpr gracefully"""
        # show all threads that we are exiting
        self._finishExecution = True
        # exit main loop
        self._timekprMainLoop.quit()

    def executeTimekprMain(self):
        """Start up main loop"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start up main loop thread")

        # wrap in handlers, so we can finish gracefully
        try:
            self._timekprMainLoop.run()
        except KeyboardInterrupt:
            log.log(cons.TK_LOG_LEVEL_INFO, "asking everything to shut down")
            # set up finishing flag
            self.finishTimekpr()
            log.log(cons.TK_LOG_LEVEL_INFO, "main loop shut down")

    def executeTimekprWorker(self):
        """Execute all the logic of timekpr"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start up worker thread")

        # we execute tasks until not asked to stop
        while not self._finishExecution:
            log.log(cons.TK_LOG_LEVEL_INFO, "--- start working on users ---")

            # do the actual work
            try:
                self.checkUsers()
            except Exception:
                log.log(cons.TK_LOG_LEVEL_INFO, "---=== ERROR working on users ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, traceback.format_exc())
                log.log(cons.TK_LOG_LEVEL_INFO, "---=== ERROR working on users ===---")

            log.log(cons.TK_LOG_LEVEL_INFO, "--- end working on users ---")

            # take a polling pause
            time.sleep(cons.TK_POLLTIME)

        log.log(cons.TK_LOG_LEVEL_INFO, "worker shut down")

    def startTimekprDaemon(self):
        """Enable threading for all the tasks"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start daemons")

        # set up main loop
        self._timekprMainLoopTh = threading.Thread(target=self.executeTimekprMain)
        # set up worker
        self._timekprWorkTh = threading.Thread(target=self.executeTimekprWorker)

        # start both
        self._timekprMainLoopTh.start()
        self._timekprWorkTh.start()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish daemons, timekpr started")

    # --------------- worker methods --------------- #

    def checkUsers(self):
        """Entry point for user management logic"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start checkUsers")

        # get user list
        userList = self._timekprLoginManager.getUserList()

        # add new users to track
        for userName, userDict in userList.items():
            # if username is in exclusion list
            if userName in self._timekprConfigManager.getTimekprUsersExcl():
                log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: user \"%s\" explicitly excluded" % (userName))
            # if not in, we add it
            elif userName not in self._timekprUserList:
                log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: we have a new user \"%s\"" % (userName))
                # add user
                self._timekprUserList[userName] = timekprUser(
                     self._logging
                    ,self._timekprBusName
                    ,userDict[cons.TK_CTRL_UID]
                    ,userDict[cons.TK_CTRL_UNAME]
                    ,userDict[cons.TK_CTRL_UPATH]
                    ,self._timekprConfigManager.getTimekprConfigDir()
                    ,self._timekprConfigManager.getTimekprWorkDir())

                # init variables for user
                self._timekprUserList[userName].initTimekprVariables()
                # adjust config
                self._timekprUserList[userName].adjustLimitsFromConfig()
                # adjust time spent
                self._timekprUserList[userName].adjustTimeSpentExplicit()

        # session list to remove
        removableUsers = {}

        # collect users which left
        for userName in self._timekprUserList:
            # check if user is there
            if userName not in userList:
                # collect removable
                removableUsers[userName] = 0

        # get rid of users which left
        for userName in removableUsers:
            log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: user \"%s\" has gone" % (userName))
            # save everything for the user
            self._timekprUserList[userName].saveSpent()
            self._timekprUserList[userName].deInitUser()
            # delete users that left
            self._timekprUserList.pop(userName)
            # remove if exists
            if userName in self._timekprUserTerminationList:
                # delete from killing list as well
                self._timekprUserTerminationList.pop(userName)

        # go through all users
        for userName in self._timekprUserList:
            # init variables for user
            self._timekprUserList[userName].initTimekprVariables()
            # adjust time spent
            isUserActive = self._timekprUserList[userName].adjustTimeSpentActual(self._timekprConfigManager.getTimekprSessionsCtrl(), self._timekprConfigManager.getTimekprSessionsExcl())

            # if user is not active, we do not send them to death row (or suspend the sentence for a while)
            if not isUserActive and userName in self._timekprUserTerminationList:
                log.log(cons.TK_LOG_LEVEL_INFO, "saving user \"%s\" from certain death" % (self._timekprUserList[userName].getUserName()))

                # remove from death list
                self._timekprUserTerminationList.pop(userName)

            # get stats for user
            timeLeftInARow = self._timekprUserList[userName].getTimeLeft()[2]

            log.log(cons.TK_LOG_LEVEL_INFO, "user \"%s\", active: %s, time left: %i" % (userName, str(isUserActive), timeLeftInARow))

            # if user sessions are not yet sentenced to death and user is active
            if userName not in self._timekprUserTerminationList and isUserActive:
                # if user has very few time, let's kill him softly
                if timeLeftInARow <= cons.TK_TERMINATION_TIME:
                    # add user to kill list (add dbus object path)
                    self._timekprUserTerminationList[userName] = self._timekprUserList[userName].getUserPathOnBus()
                    # initiate final countdown after which session is killed
                    self._timekprUserList[userName]._finalCountdown = max(timeLeftInARow, cons.TK_TERMINATION_TIME)

                    # in case this is first killing
                    if len(self._timekprUserTerminationList) == 1:
                        # process users
                        GLib.timeout_add_seconds(1, self.killUsers)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish checkUsers")

    def killUsers(self):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start user killer")

        # loop through users to be killed
        for rUserName in self._timekprUserTerminationList:
            # inform user
            log.log(cons.TK_LOG_LEVEL_INFO, "death approaching in %s secs" % (str(self._timekprUserList[rUserName]._finalCountdown)))

            # send messages only when certain time is left
            if self._timekprUserList[rUserName]._finalCountdown <= cons.TK_FINAL_COUNTDOWN_TIME:
                # final warning
                self._timekprUserList[rUserName].processFinalWarning()

            # time to die
            if self._timekprUserList[rUserName]._finalCountdown <= 0:
                # save user before kill
                self._timekprUserList[rUserName].saveSpent()
                # kill user
                self._timekprLoginManager.terminateUserSessions(rUserName, self._timekprUserList[rUserName].getUserPathOnBus(), self._timekprConfigManager.getTimekprSessionsCtrl())

            # decrease time to kill
            self._timekprUserList[rUserName]._finalCountdown -= 1

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish user killer")

        # if there is nothing to kill
        if len(self._timekprUserTerminationList) == 0:
            return False
        else:
            return True

    # --------------- DBUS / communication methods --------------- #

    # TODO: check these comments !
    # these methods are in manager due to certain frontends (if any) could ask config for any user, this does not make client to loop through user objects in DBUS
    # this !initiates! configuration sending to client (this is due to if config changes we send configuration over, so not to duplicate delivery, we do it like this)

    # --------------- simple user methods accessible by any --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_LIMITS_INTERFACE, in_signature="s", out_signature="is")
    def requestTimeLimits(self, pUserName):
        """Request to send config to client (returns error in case no user and the like)"""
        # result
        result = -1
        message = "User \"%s\" is not found" % (pUserName)

        # check if we have this user
        if pUserName in self._timekprUserList:
            # pass this to actual method
            self._timekprUserList[pUserName].getTimeLimits()

            # result
            result = 0
            message = ""

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_LIMITS_INTERFACE, in_signature="s", out_signature="is")
    def requestTimeLeft(self, pUserName):
        """Request to send current state of time & limits for user (returns error in case no user and the like)"""
        # result
        result = -1
        message = "User \"%s\" is not found" % (pUserName)

        # check if we have this user
        if pUserName in self._timekprUserList:
            # pass this to actual method
            self._timekprUserList[pUserName].getTimeLeft(True)

            # result
            result = 0
            message = ""

        # result
        return result, message

    # --------------- user admin methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="", out_signature="is")
    def getUserList(self):
        """Get user list and their time left"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        # result
        result = -1
        message = ""

        # check if we have this user

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="s", out_signature="is")
    def getUserConfiguration(self, pUserName):
        """Get user list and their time left"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        # result
        result = -1
        message = ""

        # check if we have this user

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sai", out_signature="is")
    def setAllowedDays(self, pUserName, pDayList):
        """Set up allowed days for the user"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir())

            # load config
            result, message = userConfigProcessor.checkAndSetAllowedDays(pDayList)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR: %s" % (str(unexpectedException)))

            # result
            result = -1
            message = "Unexpected ERROR updating confguration. Please inspect timekpr log files"

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sias", out_signature="is")
    def setAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Set up allowed hours for the user"""
        """This sets allowed hours for user for particular day
            server expects only the hours that are needed, hours must be sorted in ascending order
            please note that this is using 24h format, no AM/PM nonsense expected
            minutes can be specified in brackets after hour, like: 16[00-45], which means until 16:45"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir())

            # load config
            result, message = userConfigProcessor.checkAndSetAllowedHours(pDayNumber, pHourList)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR: %s" % (str(unexpectedException)))

            # result
            result = -1
            message = "Unexpected ERROR updating confguration. Please inspect timekpr log files"

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sai", out_signature="is")
    def setTimeLimitForDays(self, pUserName, pDayLimits):
        """Set up new timelimits for each day for the user"""
        """This sets allowable time to user
            server always expects 7 limits, for each day of the week, in the list"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir())

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForDays(pDayLimits)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR: %s" % (str(unexpectedException)))

            # result
            result = -1
            message = "Unexpected ERROR updating confguration. Please inspect timekpr log files"

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setTrackInactive(self, pUserName, pTrackInactive):
        """Set track inactive sessions for the user"""
        """This sets whehter inactive user sessions are tracked
            true - logged in user is always tracked (even if switched to console or locked or ...)
            false - user time is not tracked if he locks the session, session is switched to another user, etc."""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir())

            # load config
            result, message = userConfigProcessor.checkAndSetTrackInactive(True if pTrackInactive else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR: %s" % (str(unexpectedException)))

            # result
            result = -1
            message = "Unexpected ERROR updating confguration. Please inspect timekpr log files"

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="ssi", out_signature="is")
    def setTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set time left for today for the user"""
        """Sets time limits for user for this moment:
            if pOperation is "+" - more time left is addeed
            if pOperation is "-" time is subtracted
            if pOperation is "=" or empty, the time is set as it is"""
        try:
            # check the user and it's configuration
            userControlProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir())

            # load config
            result, message = userControlProcessor.checkAndSetTimeLeft(pOperation, pTimeLeft)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustTimeSpentExplicit(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR: %s" % (str(unexpectedException)))

            # result
            result = -1
            message = "Unexpected ERROR updating control. Please inspect timekpr log files"

        # result
        return result, message
