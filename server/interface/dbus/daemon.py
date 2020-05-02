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
from timekpr.common.utils import misc
from timekpr.server.user.userdata import timekprUser
from timekpr.server.config.configprocessor import timekprUserConfigurationProcessor
from timekpr.server.config.configprocessor import timekprConfigurationProcessor
from timekpr.server.config.userhelper import timekprUserStore
from timekpr.server.config import userhelper
from timekpr.common.constants import messages as msg

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
        # set up tmp logging
        self._logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_INFO, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}
        # set up tmp logging
        log.setLogging(self._logging)
        # configuration init
        self._timekprConfigManager = timekprConfig(pIsDevActive=self._isDevActive, pLog=self._logging)
        self._timekprConfigManager.loadMainConfiguration()

        # save logging for later use in classes down tree
        self._logging = {cons.TK_LOG_L: self._timekprConfigManager.getTimekprLogLevel(), cons.TK_LOG_D: self._timekprConfigManager.getTimekprLogfileDir(), cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}
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
            time.sleep(self._timekprConfigManager.getTimekprPollTime())

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
            # login manager is system user, we do these checks only for system users
            if not userhelper.verifyNormalUserID(userDict[cons.TK_CTRL_UID]):
                # sys user
                log.log(cons.TK_LOG_LEVEL_DEBUG, "NOTE: system user \"%s\" explicitly excluded" % (userName))
                # try to get login manager VT (if not already found)
                self._timekprLoginManager.determineLoginManagerVT(userName, userDict[cons.TK_CTRL_UPATH])
            # if username is in exclusion list, additionally verify that username is not a sysuser / login manager (this is somewhat obsolete now)
            elif userName in self._timekprConfigManager.getTimekprUsersExcl() and userName not in userhelper.getTimekprLoginManagers():
                log.log(cons.TK_LOG_LEVEL_DEBUG, "NOTE: user \"%s\" explicitly excluded" % (userName))
            # if not in, we add it
            elif userName not in self._timekprUserList:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "NOTE: we have a new user \"%s\"" % (userName))
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
                self._timekprUserList[userName].adjustTimeSpentFromControl()

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
            # additional options
            killEvenIdle = True

            # adjust time spent
            isUserActive = self._timekprUserList[userName].adjustTimeSpentActual(self._timekprConfigManager.getTimekprSessionsCtrl(), self._timekprConfigManager.getTimekprSessionsExcl(), self._timekprConfigManager.getTimekprSaveTime())
            # recalculate time left
            self._timekprUserList[userName].recalculateTimeLeft()

            # if user is not active and we are not killing them even idle, we do not send them to death row (suspend the sentence for a while)
            if (not killEvenIdle and not isUserActive) and userName in self._timekprUserTerminationList:
                log.log(cons.TK_LOG_LEVEL_INFO, "saving user \"%s\" from certain death" % (userName))
                # remove from death list
                self._timekprUserTerminationList.pop(userName)

            # get stats for user
            timeLeftInARow = self._timekprUserList[userName].getTimeLeft()[1]

            log.log(cons.TK_LOG_LEVEL_DEBUG, "user \"%s\", active: %s, time left: %i" % (userName, str(isUserActive), timeLeftInARow))

            # if user has very few time, let's kill him softly + user sessions are not yet sentenced to death and user is active (or forced)
            if timeLeftInARow <= self._timekprConfigManager.getTimekprTerminationTime() + 1 and userName not in self._timekprUserTerminationList and (isUserActive or killEvenIdle):
                log.log(cons.TK_LOG_LEVEL_DEBUG, "INFO: user \"%s\" has to go..." % (userName))
                # how many users are on the death row
                killLen = len(self._timekprUserTerminationList)
                # add user to kill list (add dbus object path)
                self._timekprUserTerminationList[userName] = self._timekprUserList[userName].getUserPathOnBus()
                # initiate final countdown after which session is killed
                self._timekprUserList[userName]._finalCountdown = max(timeLeftInARow, self._timekprConfigManager.getTimekprTerminationTime())

                # in case this is first killing
                if killLen == 0:
                    # process users
                    GLib.timeout_add_seconds(1, self.killUsers)

            # process actual user session variable validation
            self._timekprUserList[userName].revalidateUserSessionAttributes()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish checkUsers")

    def killUsers(self):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start user killer")

        # session list to remove
        removableUsers = {}

        # loop through users to be killed
        for rUserName in self._timekprUserTerminationList:
            # inform user
            log.log(cons.TK_LOG_LEVEL_INFO, "death approaching in %s secs" % (str(self._timekprUserList[rUserName]._finalCountdown)))

            # send messages only when certain time is left
            if self._timekprUserList[rUserName]._finalCountdown <= self._timekprConfigManager.getTimekprFinalWarningTime():
                # final warning
                self._timekprUserList[rUserName].processFinalWarning()

            # time to die
            if self._timekprUserList[rUserName]._finalCountdown <= 0:
                # save user before kill
                self._timekprUserList[rUserName].saveSpent()
                # kill user
                try:
                    self._timekprLoginManager.terminateUserSessions(rUserName, self._timekprUserList[rUserName].getUserPathOnBus(), self._timekprConfigManager.getTimekprSessionsCtrl())
                except Exception:
                    log.log(cons.TK_LOG_LEVEL_INFO, "ERROR killing sessions: %s" % (traceback.format_exc()))

                # now we have one less (we hope he's killed)
                if rUserName not in removableUsers:
                    # collect removable
                    removableUsers[rUserName] = 0

            # decrease time to kill
            self._timekprUserList[rUserName]._finalCountdown -= 1

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish user killer")

        # get rid of users which left
        for userName in removableUsers:
            # remove from death list
            self._timekprUserTerminationList.pop(userName)

        # if there is nothing to kill
        if len(self._timekprUserTerminationList) < 1:
            return False
        else:
            return True

    # --------------- DBUS / communication methods --------------- #
    # --------------- simple user time limits methods accessible by any --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_LIMITS_INTERFACE, in_signature="s", out_signature="is")
    def requestTimeLimits(self, pUserName):
        """Request to send config to client (returns error in case no user and the like)"""
        # result
        result = -1
        message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USER_NOTFOUND") % (pUserName)

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
        message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USER_NOTFOUND") % (pUserName)

        # check if we have this user
        if pUserName in self._timekprUserList:
            # pass this to actual method
            self._timekprUserList[pUserName].getTimeLeft(True)

            # result
            result = 0
            message = ""

        # result
        return result, message

    # --------------- simple user session attributes accessible by any --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE, in_signature="ssss", out_signature="is")
    def processUserSessionAttributes(self, pUserName, pWhat, pKey, pValue):
        """Request to verify or set user session attributes (returns error in case no user and the like)"""
        # result
        result = -1
        message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USER_NOTFOUND") % (pUserName)

        # check if we have this user
        if pUserName in self._timekprUserList:
            # pass this to actual method
            self._timekprUserList[pUserName].processUserSessionAttributes(pWhat, pKey, pValue)

            # result
            result = 0
            message = ""

        # result
        return result, message

    # --------------- user admin methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="", out_signature="isas")
    def getUserList(self):
        """Get user list and their time left"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        # result
        result = 0
        message = ""
        userList = []

        try:
            # check if we have this user
            userList = timekprUserStore.getSavedUserList(self._logging, self._timekprConfigManager.getTimekprConfigDir())
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USERLIST_UNEXPECTED_ERROR")

        # result
        return result, message, userList

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="s", out_signature="isa{sv}")
    def getUserConfiguration(self, pUserName):
        """Get user configuration (saved)"""
        """  this retrieves stored configuration for the user"""
        # initialize username storage
        userConfigurationStore = {}

        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

            # load config
            result, message, userConfigurationStore = userConfigProcessor.getSavedUserConfiguration()
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USER_UNEXPECTED_ERROR")

        # result
        return result, message, userConfigurationStore

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sai", out_signature="is")
    def setAllowedDays(self, pUserName, pDayList):
        """Set up allowed days for the user"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

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
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="ssa{sa{si}}", out_signature="is")
    def setAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Set up allowed hours for the user"""
        """This sets allowed hours for user for particular day
            server expects only the hours that are needed, hours must be sorted in ascending order
            please note that this is using 24h format, no AM/PM nonsense expected
            minutes can be specified in brackets after hour, like: 16[00-45], which means until 16:45"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

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
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sai", out_signature="is")
    def setTimeLimitForDays(self, pUserName, pDayLimits):
        """Set up new timelimits for each day for the user"""
        """This sets allowable time to user
            server always expects 7 limits, for each day of the week, in the list"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

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
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

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
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

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
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="si", out_signature="is")
    def setTimeLimitForWeek(self, pUserName, pTimeLimitWeek):
        """Set up new timelimit for week for the user"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForWeek(pTimeLimitWeek)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="si", out_signature="is")
    def setTimeLimitForMonth(self, pUserName, pTimeLimitMonth):
        """Set up new timelimit for month for the user"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForMonth(pTimeLimitMonth)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

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
            userControlProcessor = timekprUserConfigurationProcessor(self._logging, pUserName, self._timekprConfigManager.getTimekprConfigDir(), self._timekprConfigManager.getTimekprWorkDir())

            # load config
            result, message = userControlProcessor.checkAndSetTimeLeft(pOperation, pTimeLeft)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustTimeSpentFromControl(False)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONTROL_UNEXPECTED_ERROR")

        # result
        return result, message

    # --------------- server admin methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="", out_signature="isa{sv}")
    def getTimekprConfiguration(self):
        """Get all timekpr configuration from server"""
        # default
        timekprConfig = {}
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message, timekprConfig = mainConfigurationProcessor.getSavedTimekprConfiguration()
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_UNEXPECTED_ERROR")

        # result
        return result, message, timekprConfig

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprLogLevel(self, pLogLevel):
        """Set the logging level for server"""
        """ restart needed to fully engage, but newly logged in users get logging properly"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprLogLevel(pLogLevel)

            # set in memory as well
            self._timekprConfigManager.setTimekprLogLevel(pLogLevel)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprPollTime(self, pPollTimeSecs):
        """Set polltime for timekpr"""
        """ set in-memory polling time (this is the accounting precision of the time"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprPollTime(pPollTimeSecs)

            # set in memory as well
            self._timekprConfigManager.setTimekprPollTime(pPollTimeSecs)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprSaveTime(self, pSaveTimeSecs):
        """Set save time for timekpr"""
        """Set the interval at which timekpr saves user data (time spent, etc.)"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSaveTime(pSaveTimeSecs)

            # set in memory as well
            self._timekprConfigManager.setTimekprSaveTime(pSaveTimeSecs)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="b", out_signature="is")
    def setTimekprTrackInactive(self, pTrackInactive):
        """Set default value for tracking inactive sessions"""
        """Note that this is just the default value which is configurable at user level"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprTrackInactive(pTrackInactive)

            # set in memory as well
            self._timekprConfigManager.setTimekprTrackInactive(pTrackInactive)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprTerminationTime(self, pTerminationTimeSecs):
        """Set up user termination time"""
        """ User temination time is how many seconds user is allowed in before he's thrown out
            This setting applies to users who log in at inappropriate time according to user config
        """
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprTerminationTime(pTerminationTimeSecs)

            # set in memory as well
            self._timekprConfigManager.setTimekprTerminationTime(pTerminationTimeSecs)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Set up final warning time for users"""
        """ Final warning time is the countdown lenght (in seconds) for the user before he's thrown out"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprFinalWarningTime(pFinalWarningTimeSecs)

            # set in memory as well
            self._timekprConfigManager.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="as", out_signature="is")
    def setTimekprSessionsCtrl(self, pSessionsCtrl):
        """Set accountable session types for users"""
        """ Accountable sessions are sessions which are counted as active, there are handful of them, but predefined"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSessionsCtrl(pSessionsCtrl)

            # set in memory as well
            self._timekprConfigManager.setTimekprSessionsCtrl(pSessionsCtrl)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="as", out_signature="is")
    def setTimekprSessionsExcl(self, pSessionsExcl):
        """Set NON-accountable session types for users"""
        """ NON-accountable sessions are sessions which are explicitly ignored during session evaluation, there are handful of them, but predefined"""
        try:
            # result
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSessionsExcl(pSessionsExcl)

            # set in memory as well
            self._timekprConfigManager.setTimekprSessionsExcl(pSessionsExcl)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="as", out_signature="is")
    def setTimekprUsersExcl(self, pUsersExcl):
        """Set excluded usernames for timekpr"""
        """ Excluded usernames are usernames which are excluded from accounting
            Pre-defined values containt all graphical login managers etc., please do NOT add actual end-users here,
            You can, but these users will never receive any notifications about time, icon will be in connecting state forever
        """
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor(self._logging, self._isDevActive)

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprUsersExcl(pUsersExcl)

            # set in memory as well
            self._timekprConfigManager.setTimekprUsersExcl(pUsersExcl)
        except Exception as unexpectedException:
            # set up logging
            log.setLogging(self._logging)
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message
