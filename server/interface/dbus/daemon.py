"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
import os
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import dbus.service
import time
import threading
import traceback
from datetime import datetime, timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.server.interface.dbus.logind import manager as l1_manager
from timekpr.common.utils.config import timekprConfig
from timekpr.common.utils import misc
from timekpr.server.user.userdata import timekprUser
from timekpr.server.user.playtime import timekprPlayTimeConfig
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
    def __init__(self):
        """Initialize daemon variables"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init dbus daemon")

        # get our bus
        self._timekprBus = (dbus.SessionBus() if (cons.TK_DEV_ACTIVE and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())
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
        self._timekprConfig = None
        # this will hold all timekpr users (collection of user class)
        self._timekprUserList = {}
        # this will hold collection of users to be terminated
        self._timekprUserTerminationList = {}
        # this will hold collection of users who have restrictions to use computer
        self._timekprUserRestrictionList = {}
        # PlayTime config
        self._timekprPlayTimeConfig = None

        # ## initialization ##
        # configuration init
        self._timekprConfig = timekprConfig()
        self._timekprConfig.loadMainConfiguration()
        # log
        self._timekprConfig.logMainConfiguration()

        # init logging
        log.setLogging(self._timekprConfig.getTimekprLogLevel(), self._timekprConfig.getTimekprLogfileDir(), cons.TK_LOG_OWNER_SRV, "")

        # in case we are dealing with logind
        if self._timekprLoginManagerName == "L1":
            self._timekprLoginManager = l1_manager.timekprUserLoginManager()
        # in case we are dealing with consolekit (WHICH IS NOT IMPLEMENTED YET and might NOT be AT ALL)
        elif self._timekprLoginManagerName == "CK":
            self._timekprLoginManager = None

        # PT config
        self._timekprPlayTimeConfig = timekprPlayTimeConfig(self._timekprConfig)
        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish init daemon data")

    def finishTimekpr(self, signal=None, frame=None):
        """Exit timekpr gracefully"""
        # show all threads that we are exiting
        self._finishExecution = True
        # exit main loop
        self._timekprMainLoop.quit()
        log.log(cons.TK_LOG_LEVEL_INFO, "main loop shut down")

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

        # finish logging
        log.flushLogFile()

    def executeTimekprWorker(self):
        """Execute all the logic of timekpr"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start up worker thread")
        # def
        execLen = timedelta(0, 0, 0)
        execCnt = 0
        # we execute tasks until not asked to stop
        while not self._finishExecution:
            # perf
            dtsm = time.time()
            dts = datetime.now()
            log.log(cons.TK_LOG_LEVEL_INFO, "--- start working on users ---")

            # do the actual work
            try:
                self.checkUsers()
            except Exception:
                log.log(cons.TK_LOG_LEVEL_INFO, "---=== ERROR in \"executeTimekprWorker\" working on users ===---")
                log.log(cons.TK_LOG_LEVEL_INFO, traceback.format_exc())
                log.log(cons.TK_LOG_LEVEL_INFO, "---=== ERROR in \"executeTimekprWorker\" working on users ===---")

            # periodically flush the file
            log.autoFlushLogFile()

            # perf
            lavg = os.getloadavg()
            perf = datetime.now() - dts
            execCnt += 1
            execLen += perf

            log.log(cons.TK_LOG_LEVEL_INFO, "--- end working on users (ela: %s) ---" % (str(perf)))
            log.log(cons.TK_LOG_LEVEL_DEBUG, "--- perf: avg ela: %s, loadavg: %s, %s, %s ---" % (str(execLen/execCnt), lavg[0], lavg[1], lavg[2]))
            # take a polling pause (try to do that exactly every 3 secs)
            time.sleep(self._timekprConfig.getTimekprPollTime() - min(time.time() - dtsm, self._timekprConfig.getTimekprPollTime() / 2))

        log.log(cons.TK_LOG_LEVEL_INFO, "worker shut down")
        # finish logging
        log.flushLogFile()

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
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start checkUsers")

        # get user list
        wasConnectionLost, userList = self._timekprLoginManager.getUserList()
        # if we had a disaster, remove all users because connection to DBUS was lost
        if wasConnectionLost:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "IMPORTANT WARNING: due to lost DBUS connection, all users are de-initialized (including from DBUS) and re-initalized from saved state")
            # remove them from dbus
            for rUser in self._timekprUserList:
                # remove from DBUS
                self._timekprUserList[rUser].deInitUser()
            # delete all users
            self._timekprUserList.clear()
            # delete termination list as well
            self._timekprUserRestrictionList.clear()

        # if global switch is enabled, we need to refresh processes at some iterval (method determines that by itself)
        if self._timekprConfig.getTimekprPlayTimeEnabled():
            # refresh PT process list
            self._timekprPlayTimeConfig.processPlayTimeActivities()

        # add new users to track
        for rUserName, userDict in userList.items():
            # login manager is system user, we do these checks only for system users
            if not userhelper.isUserValid(userDict[cons.TK_CTRL_UID], userDict[cons.TK_CTRL_UNAME]):
                # sys user
                log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: system or mismatched user \"%s\" explicitly excluded" % (rUserName))
                # try to get login manager VT (if not already found)
                self._timekprLoginManager.determineLoginManagerVT(rUserName, userDict[cons.TK_CTRL_UPATH])
            # if username is in exclusion list, additionally verify that username is not a sysuser / login manager (this is somewhat obsolete now)
            elif rUserName in self._timekprConfig.getTimekprUsersExcl() and rUserName not in userhelper.getTimekprLoginManagers():
                log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: user \"%s\" explicitly excluded" % (rUserName))
            # if not in, we add it
            elif rUserName not in self._timekprUserList:
                log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: we have a new user \"%s\"" % (rUserName))
                # add user
                self._timekprUserList[rUserName] = timekprUser(
                    self._timekprBusName,
                    userDict[cons.TK_CTRL_UID],
                    userDict[cons.TK_CTRL_UNAME],
                    userDict[cons.TK_CTRL_UPATH],
                    self._timekprConfig,
                    self._timekprPlayTimeConfig
                )

                # adjust config
                self._timekprUserList[rUserName].adjustLimitsFromConfig()
                # adjust time spent
                self._timekprUserList[rUserName].adjustTimeSpentFromControl()

        # session list to remove
        removableUsers = [rUserName for rUserName in self._timekprUserList if rUserName not in userList]

        # get rid of users which left
        for rUserName in removableUsers:
            log.log(cons.TK_LOG_LEVEL_INFO, "NOTE: user \"%s\" has gone" % (rUserName))
            # save everything for the user
            self._timekprUserList[rUserName].saveSpent()
            self._timekprUserList[rUserName].deInitUser()
            # delete users that left
            self._timekprUserList.pop(rUserName)
            # remove if exists
            if rUserName in self._timekprUserRestrictionList:
                # delete from killing list as well
                self._timekprUserRestrictionList.pop(rUserName)

        # go through all users
        for rUserName in self._timekprUserList:
            # init variables for user
            self._timekprUserList[rUserName].refreshTimekprRuntimeVariables()

            # adjust time spent
            userActiveEffective, userActiveActual, userScreenLocked = self._timekprUserList[rUserName].adjustTimeSpentActual(self._timekprConfig)
            # recalculate time left
            self._timekprUserList[rUserName].recalculateTimeLeft()
            # process actual user session variable validation
            self._timekprUserList[rUserName].revalidateUserSessionAttributes()

            # get stats for user
            timeLeftArray = self._timekprUserList[rUserName].getTimeLeft()
            timeLeftToday = timeLeftArray[0]
            timeLeftInARow = timeLeftArray[1]
            timeHourUnaccounted = timeLeftArray[6]
            timePTActivityCnt = 0

            # PlayTime left validation
            if self._timekprConfig.getTimekprPlayTimeEnabled():
                # get time left for PLayTime
                timeLeftPT, isPTEnabled, isPTAccounted, isPTActive = self._timekprUserList[rUserName].getPlayTimeLeft()
                # enabled and active for user
                if isPTEnabled and isPTActive:
                    # if there is no time left (compare to almost ultimate answer)
                    # or hour is unaccounted and PT is not allowed in those hours
                    if (isPTAccounted and timeLeftPT < 0.0042) or (timeHourUnaccounted and not self._timekprUserList[rUserName].getUserPlayTimeUnaccountedIntervalsEnabled()):
                        # killing processes
                        self._timekprPlayTimeConfig.killPlayTimeProcesses(self._timekprUserList[rUserName].getUserId())
                    else:
                        # active count
                        timePTActivityCnt = self._timekprPlayTimeConfig.getMatchedUserProcessCnt(self._timekprUserList[rUserName].getUserId())
            # set process count (in case PT was disable in-flight or it has changed)
            self._timekprUserList[rUserName].setPlayTimeActiveActivityCnt(timePTActivityCnt)

            # logging
            log.log(cons.TK_LOG_LEVEL_DEBUG, "user \"%s\", active: %s/%s/%s (act/eff/lck), huacc: %s, tleft: %i" % (rUserName, str(userActiveActual), str(userActiveEffective), str(userScreenLocked), str(timeHourUnaccounted), timeLeftInARow))

            # process actions if user is in the restrictions list
            if rUserName in self._timekprUserRestrictionList:
                # (internal idle killing switch) + user is not active + there is a time available today (opposing to in a row)
                if ((not userActiveActual and timeLeftToday > self._timekprConfig.getTimekprTerminationTime()) or timeHourUnaccounted) and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D):
                    log.log(cons.TK_LOG_LEVEL_INFO, "SAVING user \"%s\" from ending his sessions / shutdown" % (rUserName))
                    # remove from death list
                    self._timekprUserRestrictionList.pop(rUserName)
                # if restricted time has passed for hard restrictions, we need to lift the restriction
                elif (timeLeftInARow > self._timekprConfig.getTimekprTerminationTime() or timeHourUnaccounted) and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D):
                    log.log(cons.TK_LOG_LEVEL_INFO, "RELEASING terminate / kill / shutdown from user \"%s\"" % (rUserName))
                    # remove from restriction list
                    self._timekprUserRestrictionList.pop(rUserName)
                # if restricted time has passed for soft restrictions, we need to lift the restriction
                elif (timeLeftInARow > self._timekprConfig.getTimekprTerminationTime() or timeHourUnaccounted) and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_L, cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W):
                    log.log(cons.TK_LOG_LEVEL_INFO, "RELEASING lock / suspend from user \"%s\"" % (rUserName))
                    # remove from restriction list
                    self._timekprUserRestrictionList.pop(rUserName)
                # update restriction stats
                else:
                    # update active states for restriction routines
                    self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USACT] = userActiveActual
                    self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USLCK] = userScreenLocked
                    self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = max(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] - 1, 0)
                    # only if user is active / screen is not locked
                    if ((userActiveActual and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D))
                    or (not userScreenLocked and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_L, cons.TK_CTRL_RES_W))):
                        # update active states for restriction routines
                        self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] = max(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] - 1, 0)

            # ## FILL IN USER RESTRICTIONS ##

            # if user has very few time left, we need to enforce limits: Lock screen / Sleep computer / Shutdown computer / Terminate sessions
            if timeLeftInARow <= self._timekprConfig.getTimekprTerminationTime() and not timeHourUnaccounted and rUserName not in self._timekprUserRestrictionList and userActiveActual:
                log.log(cons.TK_LOG_LEVEL_DEBUG, "INFO: user \"%s\" has got restrictions..." % (rUserName))
                # add user to restrictions list
                self._timekprUserRestrictionList[rUserName] = {
                    cons.TK_CTRL_UPATH: self._timekprUserList[rUserName].getUserPathOnBus(),  # user path on dbus
                    cons.TK_CTRL_FCNTD: max(timeLeftInARow, self._timekprConfig.getTimekprTerminationTime()),  # final countdown
                    cons.TK_CTRL_RESTY: self._timekprUserList[rUserName].getUserLockoutType(),  # restricton type: lock, suspend, suspendwake, terminate, kill, shutdown
                    cons.TK_CTRL_RTDEL: 0,  # retry delay before next attempt to enforce restrictions
                    cons.TK_CTRL_RTDEA: 0,  # retry delay (additional delay for lock in case of suspend)
                    cons.TK_CTRL_USACT: userActiveActual,  # whether user is actually active
                    cons.TK_CTRL_USLCK: userScreenLocked,  # whether user screen is locked
                    cons.TK_CTRL_USWKU: self._timekprUserList[rUserName].findNextAvailableIntervalStart() if self._timekprUserList[rUserName].getUserLockoutType() == cons.TK_CTRL_RES_W and timeLeftToday > timeLeftInARow else None
                }
                # in case this is first restriction we need to initiate restriction process
                if len(self._timekprUserRestrictionList) == 1:
                    # process users
                    GLib.timeout_add_seconds(1, self._restrictUsers)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish checkUsers")

    def _restrictUsers(self):
        """Terminate user sessions"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start user killer")

        # final warn
        def _processFinalWarning(pUserName, pFinalNotificationType, pSecondsLeft):
            # process final warning with error catch (so it won't interfere with ending the sessions)
            try:
                self._timekprUserList[pUserName].processFinalWarning(pFinalNotificationType, pSecondsLeft)
            except Exception:
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR sending notification while terminating users:\n%s" % (traceback.format_exc()))

        # loop through users to be killed
        for rUserName in self._timekprUserRestrictionList:
            log.log(cons.TK_LOG_LEVEL_INFO, "RESTRICTIONS, usr: \"%s\", cntd: %i, del: %i, dea: %i" % (rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD], self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL], self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA]))
            # ## check which restriction is needed ##
            # we are going to TERMINATE user sessions
            if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D):
                # log that we are going to terminate user sessions
                if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] <= 0:
                    log.log(cons.TK_LOG_LEVEL_INFO, "%s approaching in %s secs" % ("TERMINATE" if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] == cons.TK_CTRL_RES_T else ("KILL" if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] == cons.TK_CTRL_RES_K else "SHUTDOWN"), str(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])))
                    # send messages only when certain time is left
                    if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= self._timekprConfig.getTimekprFinalWarningTime():
                        # final warning
                        _processFinalWarning(rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY], self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])
                    # time to die
                    if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= 0:
                        # set restriction for repetitive kill
                        self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] = cons.TK_CTRL_LCDEL * 5
                        # save user before kill
                        self._timekprUserList[rUserName].saveSpent()
                        # terminate user sessions
                        try:
                            # term
                            if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K):
                                # terminate
                                self._timekprLoginManager.terminateUserSessions(rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_UPATH], self._timekprConfig, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY])
                            # shut
                            elif self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] == cons.TK_CTRL_RES_D:
                                # shutdown
                                self._timekprLoginManager.shutdownComputer(rUserName)
                        except Exception:
                            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR killing sessions: %s" % (traceback.format_exc()))
            # we are going to LOCK user sessions
            elif self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] == cons.TK_CTRL_RES_L:
                # is user active
                isUserInactive = (not self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USACT] or self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USLCK])
                # check if user has locked the screen
                if isUserInactive and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] <= 0:
                    # we are going lock user sessions
                    log.log(cons.TK_LOG_LEVEL_INFO, "time is up, but user \"%s\" not active, not enforcing the lock" % (rUserName))
                    # set restriction for repetitive lock
                    self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = cons.TK_CTRL_LCDEL
                # lock must be enforced only if user is active
                elif not isUserInactive:
                    # continue if there is no delay
                    if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] <= 0:
                        # log
                        log.log(cons.TK_LOG_LEVEL_INFO, "LOCK approaching in %s secs" % (str(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])))
                        # send messages only when certain time is left
                        if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= self._timekprConfig.getTimekprFinalWarningTime():
                            # final warning
                            _processFinalWarning(rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY], self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])
                        # time to lock
                        if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= 0:
                            # set restriction for repetitive lock
                            self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = cons.TK_CTRL_LCDEL
                            # log lock
                            log.log(cons.TK_LOG_LEVEL_INFO, "time is up for user \"%s\", enforcing the LOCK" % (rUserName))
                            # lock computer
                            self._timekprUserList[rUserName].lockUserSessions()
            # we are going to SUSPEND user sessions
            elif self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY] in (cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W):
                # is user active
                isUserInactive = (not self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USACT] or self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USLCK])
                # check if user has locked the screen
                if isUserInactive and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] <= 0:
                    # we are going lock user sessions
                    log.log(cons.TK_LOG_LEVEL_INFO, "time is up, but user \"%s\" not active, not enforcing the suspend" % (rUserName))
                    # set restriction for repetitive lock when suspending
                    self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = cons.TK_CTRL_LCDEL
                # suspend / lock must be enforced only if user is active
                elif not isUserInactive:
                    # continue if there is no delay
                    if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] <= 0:
                        # log
                        log.log(cons.TK_LOG_LEVEL_INFO, "SUSPEND approaching in %s secs" % (str(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])))
                        # send messages only when certain time is left
                        if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= self._timekprConfig.getTimekprFinalWarningTime():
                            # final warning
                            _processFinalWarning(rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY], self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD])
                    # time to suspend
                    if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] <= 0:
                        # check if we have a delay before initiating actions
                        if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] <= 0:
                            # log suspend
                            log.log(cons.TK_LOG_LEVEL_INFO, "time is up for user \"%s\", enforcing the SUSPEND" % (rUserName))
                            # set restriction for repetitive lock when suspending
                            self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = cons.TK_CTRL_LCDEL
                            # set restriction for repetitive suspend
                            self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] = cons.TK_CTRL_SCDEL
                            # set up wake time if that was set
                            if self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU] is not None:
                                # set up
                                if userhelper.setWakeUpByRTC(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU]):
                                    log.log(cons.TK_LOG_LEVEL_INFO, "wake up time is SET at %i (%s) on behalf of user \"%s\"" % (self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU], datetime.fromtimestamp(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU]).strftime(cons.TK_LOG_DATETIME_FORMAT), rUserName))
                                else:
                                    log.log(cons.TK_LOG_LEVEL_INFO, "wake up time at %i (%s) could NOT be set on behalf of user \"%s\"" % (self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU], datetime.fromtimestamp(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_USWKU]).strftime(cons.TK_LOG_DATETIME_FORMAT), rUserName))
                            # suspend computer
                            self._timekprLoginManager.suspendComputer(rUserName)
                        # do not enforce lock right away after suspend, wait a little
                        elif cons.TK_CTRL_SCDEL - cons.TK_CTRL_LCDEL > self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL] > 0 and self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] <= 0:
                            # log suspend lock
                            log.log(cons.TK_LOG_LEVEL_INFO, "time is up for user \"%s\", enforcing the SUSPEND LOCK (SUSPEND in %i iterations)" % (rUserName, self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEL]))
                            # set restriction for repetitive lock when suspending
                            self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RTDEA] = cons.TK_CTRL_LCDEL
                            # if delay is still in place, just lock the screen
                            self._timekprUserList[rUserName].lockUserSessions()
            else:
                log.log(cons.TK_LOG_LEVEL_INFO, "WARN: unsupported restriction type \"%s\"" % (self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_RESTY]))

            # decrease time for restrictions
            self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] = max(self._timekprUserRestrictionList[rUserName][cons.TK_CTRL_FCNTD] - 1, 0)

        log.log(cons.TK_LOG_LEVEL_INFO, "RESTRICTIONS, completed with: %s" % (str(len(self._timekprUserRestrictionList) > 0)))

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish user killer")

        # return whether to keep trying to enforce restrictions
        return (len(self._timekprUserRestrictionList) > 0)

    # --------------- helper methods --------------- #

    def _getUserActualTimeInformation(self, pTimekprUser, pUserConfigurationStore):
        """Helper to provide actual (in memory information)"""
        # values from live session
        if pTimekprUser is not None:
            # get lefts
            timeLeftArray = pTimekprUser.getTimeLeft()
            # assign time lefts
            timeLeftToday = timeLeftArray[0]
            timeLeftInARow = timeLeftArray[1]
            timeSpentThisSession = timeLeftArray[2]
            timeInactiveThisSession = timeLeftArray[3]
            timeSpentBalance = timeLeftArray[4]
            timeSpentDay = timeLeftArray[5]

            # time spent session
            pUserConfigurationStore["ACTUAL_TIME_SPENT_SESSION"] = int(timeSpentThisSession)
            # time inactive this session
            pUserConfigurationStore["ACTUAL_TIME_INACTIVE_SESSION"] = int(timeInactiveThisSession)
            # time spent
            pUserConfigurationStore["ACTUAL_TIME_SPENT_BALANCE"] = int(timeSpentBalance)
            # time spent
            pUserConfigurationStore["ACTUAL_TIME_SPENT_DAY"] = int(timeSpentDay)
            # time left today
            pUserConfigurationStore["ACTUAL_TIME_LEFT_DAY"] = int(timeLeftToday)
            # time left in a row
            pUserConfigurationStore["ACTUAL_TIME_LEFT_CONTINUOUS"] = int(timeLeftInARow)
            # PlayTime
            playTimeLeft, playTimeEnabled, playTimeAccounted, _unused = pTimekprUser.getPlayTimeLeft(pCheckActive=False)
            playTimeLeft = max(playTimeLeft, 0) if playTimeEnabled and playTimeAccounted else 0
            # PlayTime left today
            pUserConfigurationStore["ACTUAL_PLAYTIME_LEFT_DAY"] = playTimeLeft
            # active PlayTime activity count
            pUserConfigurationStore["ACTUAL_ACTIVE_PLAYTIME_ACTIVITY_COUNT"] = pTimekprUser.getPlayTimeActiveActivityCnt()

    # ## --------------- DBUS / communication methods --------------- ## #
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

    # --------------- user information get methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="", out_signature="isaas")
    def getUserList(self):
        """Get user list and their time left"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        # result
        result = 0
        message = ""
        userList = []

        try:
            # init store
            timekprUStore = timekprUserStore()
            # check if we have this user
            userList = timekprUStore.getSavedUserList(self._timekprConfig.getTimekprConfigDir())
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USERLIST_UNEXPECTED_ERROR")

        # result
        return result, message, userList

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="ss", out_signature="isa{sv}")
    def getUserInformation(self, pUserName, pInfoLvl):
        """Get user configuration (saved)"""
        """  this retrieves stored configuration and some realtime inforamation for the user"""
        # initialize username storage
        userConfigurationStore = {}
        result = 0
        message = ""

        try:
            # only saved and full
            if pInfoLvl in (cons.TK_CL_INF_FULL, cons.TK_CL_INF_SAVED):
                # check the user and it's configuration
                userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)
                # load config
                result, message, userConfigurationStore = userConfigProcessor.getSavedUserInformation(pInfoLvl, pUserName in self._timekprUserList)

            # additionally, if realtime needed
            if pInfoLvl in (cons.TK_CL_INF_FULL, cons.TK_CL_INF_RT) and pUserName in self._timekprUserList:
                # get in-memory settings
                self._getUserActualTimeInformation(self._timekprUserList[pUserName], userConfigurationStore)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USER_UNEXPECTED_ERROR")

        # result
        return result, message, userConfigurationStore

    # --------------- user admin methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sas", out_signature="is")
    def setAllowedDays(self, pUserName, pDayList):
        """Set up allowed days for the user"""
        """Sets allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetAllowedDays(pDayList)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
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
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetAllowedHours(pDayNumber, pHourList)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
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
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForDays(pDayLimits)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setTrackInactive(self, pUserName, pTrackInactive):
        """Set track inactive sessions for the user"""
        """This sets whether inactive user sessions are tracked
            true - logged in user is always tracked (even if switched to console or locked or ...)
            false - user time is not tracked if he locks the session, session is switched to another user, etc."""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetTrackInactive(True if bool(pTrackInactive) else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setHideTrayIcon(self, pUserName, pHideTrayIcon):
        """Set hide tray icon for the user"""
        """This sets whether icon will be hidden from user
            true - icon and notifications are NOT shown to user
            false - icon and notifications are shown to user"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetHideTrayIcon(True if bool(pHideTrayIcon) else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="ssss", out_signature="is")
    def setLockoutType(self, pUserName, pLockoutType, pWakeFrom, pWakeTo):
        """Set restriction / lockout type for the user"""
        """Restricton / lockout types:
            lock - lock the screen
            suspend - suspend the computer
            suspendwake - suspend the computer and set wakeup timer
            terminate - terminate sessions (default)"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetLockoutType(pLockoutType, pWakeFrom, pWakeTo)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
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
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForWeek(pTimeLimitWeek)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
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
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetTimeLimitForMonth(pTimeLimitMonth)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
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
            userControlProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userControlProcessor.checkAndSetTimeLeft(pOperation, pTimeLeft)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustTimeSpentFromControl(pSilent=False, pPreserveSpent=(pOperation != "="))
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONTROL_UNEXPECTED_ERROR")

        # result
        return result, message

    # --------------- user PlayTime admin methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setPlayTimeEnabled(self, pUserName, pPlayTimeEnabled):
        """Set whether PlayTime is enabled for the user"""
        """PlayTime enablement flag
            true - PlayTime is enabled
            false - PlayTime is disabled"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeEnabled(True if bool(pPlayTimeEnabled) else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setPlayTimeLimitOverride(self, pUserName, pPlayTimeLimitOverride):
        """Set whether PlayTime override is enabled for the user"""
        """PlayTime override enablement flag
            true - PlayTime override is enabled
            false - PlayTime override is disabled"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeLimitOverride(True if bool(pPlayTimeLimitOverride) else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sb", out_signature="is")
    def setPlayTimeUnaccountedIntervalsEnabled(self, pUserName, pPlayTimeUnaccountedIntervalsEnabled):
        """Set whether PlayTime activities are allowed during unaccounted intervals for the user"""
        """PlayTime allowed during unaccounted intervals enablement flag
            true - PlayTime allowed during unaccounted intervals is enabled
            false - PlayTime allowed during unaccounted intervals is disabled"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeUnaccountedIntervalsEnabled(True if bool(pPlayTimeUnaccountedIntervalsEnabled) else False)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sas", out_signature="is")
    def setPlayTimeAllowedDays(self, pUserName, pPlayTimeAllowedDays):
        """Set up allowed PlayTime days for the user"""
        """Sets allowed PlayTime days for the user
            server expects only the days that are allowed, sorted in ascending order"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeAllowedDays(pPlayTimeAllowedDays)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="sai", out_signature="is")
    def setPlayTimeLimitsForDays(self, pUserName, pPlayTimeLimits):
        """Set up new PlayTime limits for each day for the user"""
        """This sets allowable PlayTime limits to user
            server always expects 7 limits, for each day of the week, in the list"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeLimitsForDays(pPlayTimeLimits)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="saas", out_signature="is")
    def setPlayTimeActivities(self, pUserName, pPlayTimeActivities):
        """Set up new PlayTime activities for the user"""
        """This sets PlayTime activities (executable masks) for the user"""
        try:
            # check the user and it's configuration
            userConfigProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userConfigProcessor.checkAndSetPlayTimeActivities(pPlayTimeActivities)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustLimitsFromConfig(False)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_USER_ADMIN_INTERFACE, in_signature="ssi", out_signature="is")
    def setPlayTimeLeft(self, pUserName, pOperation, pTimeLeft):
        """Set time left for today for the user"""
        """Sets time limits for user for this moment:
            if pOperation is "+" - more time left is addeed
            if pOperation is "-" time is subtracted
            if pOperation is "=" or empty, the time is set as it is"""
        try:
            # check the user and it's configuration
            userControlProcessor = timekprUserConfigurationProcessor(pUserName, self._timekprConfig)

            # load config
            result, message = userControlProcessor.checkAndSetPlayTimeLeft(pOperation, pTimeLeft)

            # check if we have this user
            if pUserName in self._timekprUserList:
                # inform the user immediately
                self._timekprUserList[pUserName].adjustTimeSpentFromControl(pSilent=False, pPreserveSpent=(pOperation != "="))
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONTROL_UNEXPECTED_ERROR")

        # result
        return result, message

    # --------------- server admin get methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="", out_signature="isa{sv}")
    def getTimekprConfiguration(self):
        """Get all timekpr configuration from server"""
        # default
        timekprConfig = {}
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message, timekprConfig = mainConfigurationProcessor.getSavedTimekprConfiguration()
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_UNEXPECTED_ERROR")

        # result
        return result, message, timekprConfig

    # --------------- server admin set methods accessible by privileged users (root and all in timekpr group) --------------- #

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprLogLevel(self, pLogLevel):
        """Set the logging level for server"""
        """ restart needed to fully engage, but newly logged in users get logging properly"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprLogLevel(pLogLevel)

            # set in memory as well
            self._timekprConfig.setTimekprLogLevel(pLogLevel)
            # set it effective immediately
            log.setLogLevel(pLogLevel)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprPollTime(pPollTimeSecs)

            # set in memory as well
            self._timekprConfig.setTimekprPollTime(pPollTimeSecs)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSaveTime(pSaveTimeSecs)

            # set in memory as well
            self._timekprConfig.setTimekprSaveTime(pSaveTimeSecs)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprTrackInactive(pTrackInactive)

            # set in memory as well
            self._timekprConfig.setTimekprTrackInactive(pTrackInactive)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprTerminationTime(pTerminationTimeSecs)

            # set in memory as well
            self._timekprConfig.setTimekprTerminationTime(pTerminationTimeSecs)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprFinalWarningTime(pFinalWarningTimeSecs)

            # set in memory as well
            self._timekprConfig.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="i", out_signature="is")
    def setTimekprFinalNotificationTime(self, pFinalNotificationTimeSecs):
        """Set up final warning time for users"""
        """ Final warning time is the countdown lenght (in seconds) for the user before he's thrown out"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprFinalNotificationTime(pFinalNotificationTimeSecs)

            # set in memory as well
            self._timekprConfig.setTimekprFinalNotificationTime(pFinalNotificationTimeSecs)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSessionsCtrl(pSessionsCtrl)

            # set in memory as well
            self._timekprConfig.setTimekprSessionsCtrl(pSessionsCtrl)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprSessionsExcl(pSessionsExcl)

            # set in memory as well
            self._timekprConfig.setTimekprSessionsExcl(pSessionsExcl)
        except Exception as unexpectedException:
            # logging
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
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprUsersExcl(pUsersExcl)

            # set in memory as well
            self._timekprConfig.setTimekprUsersExcl(pUsersExcl)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="b", out_signature="is")
    def setTimekprPlayTimeEnabled(self, pPlayTimeEnabled):
        """Set whether PlayTime is enabled globally"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprPlayTimeEnabled(pPlayTimeEnabled)

            # set in memory as well
            self._timekprConfig.setTimekprPlayTimeEnabled(pPlayTimeEnabled)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="b", out_signature="is")
    def setTimekprPlayTimeEnhancedActivityMonitorEnabled(self, pPlayTimeAdvancedSearchEnabled):
        """Set whether PlayTime is enabled globally"""
        try:
            # check the configuration
            mainConfigurationProcessor = timekprConfigurationProcessor()

            # check and set config
            result, message = mainConfigurationProcessor.checkAndSetTimekprPlayTimeEnhancedActivityMonitorEnabled(pPlayTimeAdvancedSearchEnabled)

            # set in memory as well
            self._timekprConfig.setTimekprPlayTimeEnhancedActivityMonitorEnabled(pPlayTimeAdvancedSearchEnabled)
        except Exception as unexpectedException:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "Unexpected ERROR (%s): %s" % (misc.whoami(), str(unexpectedException)))

            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR")

        # result
        return result, message

    # --------------- DBUS helper methods --------------- #

    @dbus.service.method(cons.TK_DBUS_ADMIN_INTERFACE, in_signature="s", out_signature="")
    def logCachedProcesses(self, pUserId):
        """Return cached PIDs and CMDLINEs"""
        # set up logging
        pids = self._timekprPlayTimeConfig.getCachedProcesses()
        log.log(cons.TK_LOG_LEVEL_INFO, "ALLPIDS (%i)" % (len(pids)))
        log.log(cons.TK_LOG_LEVEL_INFO, "----------------------------------------")
        for rPid in pids:
            log.log(cons.TK_LOG_LEVEL_INFO, rPid)
        pids = self._timekprPlayTimeConfig.getCachedUserProcesses(str(pUserId))
        log.log(cons.TK_LOG_LEVEL_INFO, "USERPIDS (%i)" % (len(pids)))
        log.log(cons.TK_LOG_LEVEL_INFO, "----------------------------------------")
        for rPid in pids:
            log.log(cons.TK_LOG_LEVEL_INFO, rPid)
        pids = self._timekprPlayTimeConfig.getMatchedUserProcesses(str(pUserId))
        log.log(cons.TK_LOG_LEVEL_INFO, "USERMATCHEDPIDS (%i)" % (len(pids)))
        log.log(cons.TK_LOG_LEVEL_INFO, "----------------------------------------")
        for rPid in pids:
            log.log(cons.TK_LOG_LEVEL_INFO, rPid)
        log.log(cons.TK_LOG_LEVEL_INFO, "----------------------------------------")
