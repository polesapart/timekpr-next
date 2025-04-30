"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
from datetime import datetime, timedelta, timezone
import random
import string
import math

# timekpr imports
from timekpr.common.log import log
from timekpr.common.constants import constants as cons
from timekpr.server.interface.dbus.logind.user import timekprUserManager
from timekpr.common.utils.notifications import timekprNotificationManager
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl


class timekprUser(object):
    """Contains all the data for timekpr user"""

    def __init__(self, pBusName, pUserId, pUserName, pUserPath, pTimekprConfig, pPlayTimeConfig):
        """Initialize all stuff for user"""

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekprUser")

        # init limit structure
        self._timekprUserData = self._initUserLimits()

        # set user data
        self._timekprUserData[cons.TK_CTRL_UID] = pUserId
        self._timekprUserData[cons.TK_CTRL_UNAME] = pUserName
        self._timekprUserData[cons.TK_CTRL_UPATH] = pUserPath
        # global server config
        self._timekprConfig = pTimekprConfig
        # PlayTime option
        self._timekprPlayTimeConfig = pPlayTimeConfig

        # set up user properties
        self._timekprUserData[cons.TK_CTRL_SCR_N] = False  # is screensaver running
        self._timekprUserData[cons.TK_CTRL_SCR_K] = None  # verification key

        # save the bus
        self._timekprUserManager = timekprUserManager(self._timekprUserData[cons.TK_CTRL_UNAME], self._timekprUserData[cons.TK_CTRL_UPATH])
        # user config
        self._timekprUserConfig = timekprUserConfig(self._timekprConfig.getTimekprConfigDir(), self._timekprUserData[cons.TK_CTRL_UNAME])
        # user control
        self._timekprUserControl = timekprUserControl(self._timekprConfig.getTimekprWorkDir(), self._timekprUserData[cons.TK_CTRL_UNAME])
        # user notification
        self._timekprUserNotification = timekprNotificationManager(pBusName, self._timekprUserData[cons.TK_CTRL_UNAME], pTimekprConfig)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekprUser")

    def refreshTimekprRuntimeVariables(self):
        """Calcualte variables before each method which uses them (idea is not to repeat the calculations)"""
        # establish current time
        self._effectiveDatetime = datetime.now().replace(microsecond=0)
        # get DOW
        self._currentDOW = str(datetime.date(self._effectiveDatetime).isoweekday())
        # get HOD
        self._currentHOD = self._effectiveDatetime.hour
        # get HOD
        self._currentMOH = self._effectiveDatetime.minute
        # get seconds left in day
        self._secondsLeftDay = int(((datetime(self._effectiveDatetime.year, self._effectiveDatetime.month, self._effectiveDatetime.day) + timedelta(days=1)) - self._effectiveDatetime).total_seconds())
        # get seconds left in hour
        self._secondsLeftHour = int(((self._effectiveDatetime + timedelta(hours=1)).replace(microsecond=0, second=0, minute=0) - self._effectiveDatetime).total_seconds())
        # how many seconds are in this hour
        self._secondsInHour = int((self._effectiveDatetime - self._effectiveDatetime.replace(microsecond=0, second=0, minute=0)).total_seconds())

    def _initUserLimits(self):
        """Initialize default limits for the user"""
        # init time variables
        self.refreshTimekprRuntimeVariables();

        # the config works as follows:
        #    we have cons.LIMIT, this limit is either time allowed per day or if that is not used, all seconds in allowed hours
        #    in hour section (0 is the sample in config), we have whether one is allowed to work in particular hour and then we have time spent (which can be paused as well)
        #    the rest must be easy
        # define structure for limits
        # day: next day | limit | left per day + hours 0 - 23 (0 hour sample included)
        limits = {
            # per day values
            # -- see the loop below initial assignment --
            # additional limits
            cons.TK_CTRL_LIMITW : None,  # this is limit per week
            cons.TK_CTRL_LIMITM : None,  # this is limit per month
            # global time acconting values
            cons.TK_CTRL_LEFT   : 0, # this is how much time left is countinously
            cons.TK_CTRL_LEFTW  : 0,  # this is left per week
            cons.TK_CTRL_LEFTM  : 0,  # this is left per month
            cons.TK_CTRL_SPENTD : 0,  # this is spent per day
            cons.TK_CTRL_SPENTW : 0,  # this is spent per week
            cons.TK_CTRL_SPENTM : 0,  # this is spent per month
            # total spent and sleep values for session (currently for reporting only)
            cons.TK_CTRL_SPENT  : 0,  # time spent while user was logged in and active
            cons.TK_CTRL_SLEEP  : 0,  # time spent while user was logged in and sleeping
            # checking values
            cons.TK_CTRL_LCHECK : self._effectiveDatetime,  # this is last checked time
            cons.TK_CTRL_LSAVE  : self._effectiveDatetime,  # this is last save time (physical save will be less often as check)
            cons.TK_CTRL_LMOD   : self._effectiveDatetime,  # this is last control save time
            cons.TK_CTRL_LCMOD  : self._effectiveDatetime,  # this is last config save time
            # user values
            cons.TK_CTRL_UID    : None,  # user id (not used, but still saved)
            cons.TK_CTRL_UNAME  : "",  # user name, this is the one we need
            cons.TK_CTRL_UPATH  : "",  # this is for DBUS communication purposes
            # user session values (comes directly from user session)
            cons.TK_CTRL_SCR_N  : False,  # actual value
            cons.TK_CTRL_SCR_K  : None,  # verification key value
            cons.TK_CTRL_SCR_R  : 0  # retry count for verification
        }

        # fill up every day and hour
        # loop through days
        for i in range(1, 7+1):
            # fill up day
            limits[str(i)] = {cons.TK_CTRL_NDAY: str(i + 1 if i < 7 else 1), cons.TK_CTRL_PDAY: str(i - 1 if i > 1 else 7), cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTBD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            # loop through hours
            for j in range(0, 23+1):
                # initial limit is whole hour
                limits[str(i)][str(j)] = {cons.TK_CTRL_ACT: False, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60, cons.TK_CTRL_UACC: False}

        # ## this section adds additional features ##
        # PlayTime
        limits[cons.TK_CTRL_PTCNT] = {}
        limits[cons.TK_CTRL_PTCNT][cons.TK_CTRL_PTLSTC] = 0
        # loop through days
        for i in range(1, 7+1):
            # adding days and allowances
            limits[cons.TK_CTRL_PTCNT][str(i)] = {cons.TK_CTRL_LIMITD: 0, cons.TK_CTRL_LEFTD: 0, cons.TK_CTRL_SPENTBD: 0, cons.TK_CTRL_SPENTD: 0}

        # return limits
        return limits

    def deInitUser(self):
        """De-initialize timekpr user"""
        # logging
        log.log(cons.TK_LOG_LEVEL_INFO, "de-initialization of \"%s\" DBUS connections" % (self.getUserName()))
        # deinit
        self._timekprUserNotification.deInitUser()

    def recalculateTimeLeft(self):
        """Recalculate time left based on spent and configuration"""
        # reset "lefts"
        self._timekprUserData[cons.TK_CTRL_LEFT] = 0
        # calculate time left for week
        self._timekprUserData[cons.TK_CTRL_LEFTW] = self._timekprUserData[cons.TK_CTRL_LIMITW] - self._timekprUserData[cons.TK_CTRL_SPENTW]
        # calculate time left for month
        self._timekprUserData[cons.TK_CTRL_LEFTM] = self._timekprUserData[cons.TK_CTRL_LIMITM] - self._timekprUserData[cons.TK_CTRL_SPENTM]
        # account PlayTime for this day
        self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_LEFTD] = self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_LIMITD] - self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTBD]

        # continous time
        contTime = True
        # calculate "lefts"
        timesLeft = {cons.TK_CTRL_LEFTD: 0, cons.TK_CTRL_LEFTW: self._timekprUserData[cons.TK_CTRL_LEFTW], cons.TK_CTRL_LEFTM: self._timekprUserData[cons.TK_CTRL_LEFTM]}

        # go through days
        for i in (self._currentDOW, self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]):
            # reset "lefts"
            self._timekprUserData[i][cons.TK_CTRL_LEFTD] = 0

            # how many seconds left for that day (not counting hours limits yet)
            timesLeft[cons.TK_CTRL_LEFTD] = self._timekprUserData[i][cons.TK_CTRL_LIMITD] - self._timekprUserData[i][cons.TK_CTRL_SPENTBD]

            # left is least of the limits
            secondsLeft = max(min(timesLeft[cons.TK_CTRL_LEFTD], timesLeft[cons.TK_CTRL_LEFTW], timesLeft[cons.TK_CTRL_LEFTM]), 0)

            # this is it (no time or there will be no continous time for this day)
            if secondsLeft <= 0 or not contTime:
                break

            # determine current HOD
            currentHOD = self._currentHOD if self._currentDOW == i else 0

            # go through hours for this day
            for j in range(currentHOD, 23+1):
                # reset seconds to add
                secondsToAddHour = secondsLeftHour = 0
                # calculate only if hour is enabled
                if self._timekprUserData[i][str(j)][cons.TK_CTRL_ACT]:
                    # certain values need to be calculated as per this hour
                    if self._currentDOW == i and self._currentHOD == j:
                        # this is how many seconds are actually left in hour (as per generic time calculations)
                        secondsLeftHour = self._secondsLeftHour
                        # calculate how many seconds are left in this hour as per configuration
                        secondsLeftHourLimit = (self._timekprUserData[i][str(j)][cons.TK_CTRL_EMIN] * 60 - self._currentMOH * 60 - self._effectiveDatetime.second) if (self._timekprUserData[i][str(j)][cons.TK_CTRL_SMIN] * 60 <= self._currentMOH * 60 + self._effectiveDatetime.second) else 0
                    else:
                        # full hour available
                        secondsLeftHour = 3600
                        # calculate how many seconds are left in this hour as per configuration
                        secondsLeftHourLimit = (self._timekprUserData[i][str(j)][cons.TK_CTRL_EMIN] - self._timekprUserData[i][str(j)][cons.TK_CTRL_SMIN]) * 60
                        # continous time check for start of the hour (needed to see whether any of next hours are continous before adding to available time)
                        contTime = (contTime and self._timekprUserData[i][str(j)][cons.TK_CTRL_SMIN] == 0)
                    # save seconds to subtract for this hour
                    secondsToAddHour = max(min(secondsLeftHour, secondsLeftHourLimit, secondsLeft), 0)

                    # debug
                    if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
                        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "currentDOW: %s, currentHOD: %i, secondsLeftHour: %i, currentMOH: %i, currentSOM: %i, secondsLeftHourLimit: %i, secondsToAddHour: %i, secondsLeft: %i" % (i, j, secondsLeftHour, self._currentMOH, self._effectiveDatetime.second, secondsLeftHourLimit, secondsToAddHour, secondsLeft))
                # hour is disabled
                else:
                    # time is over already from the start (it won't be added to current session, but we'll count the rest of hours allowed)
                    contTime = False

                # debug
                if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
                    log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "day: %s, hour: %i, enabled: %s, addToHour: %i, contTime: %i, leftD: %i, leftWk: %i, leftMon: %i" % (i, j, self._timekprUserData[i][str(j)][cons.TK_CTRL_ACT], secondsToAddHour, contTime, timesLeft[cons.TK_CTRL_LEFTD], self._timekprUserData[cons.TK_CTRL_LEFTW], self._timekprUserData[cons.TK_CTRL_LEFTM]))

                # adjust left continously
                self._timekprUserData[cons.TK_CTRL_LEFT] += secondsToAddHour if contTime else 0
                # adjust left this hour
                self._timekprUserData[i][cons.TK_CTRL_LEFTD] += secondsToAddHour

                # recalculate "lefts"
                timesLeft[cons.TK_CTRL_LEFTD] -= secondsToAddHour
                timesLeft[cons.TK_CTRL_LEFTW] -= secondsToAddHour
                timesLeft[cons.TK_CTRL_LEFTM] -= secondsToAddHour
                secondsLeft -= secondsToAddHour

                # recalculate whether time is continous after accounting the time (handles the end of hour)
                #   time previously was previously continous (no break)
                #   seconds to add must be at least equal to the seconds left in this hour (all hour is available)
                #   total seconds left this day cannot be 0 unless it's the end of the day (when seconds for the day ends, the only plausible case is the end of the day)
                contTime = True if (contTime and not secondsToAddHour < secondsLeftHour and not (secondsLeft <= 0 and j != 23)) else False

                # this is it (time over)
                if secondsLeft <= 0 or (not contTime and self._currentDOW != i):
                    # time is over
                    break

        # debug
        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "leftInRow: %i, leftDay: %i, lefDay+1: %i" % (self._timekprUserData[cons.TK_CTRL_LEFT], self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD], self._timekprUserData[self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]][cons.TK_CTRL_LEFTD]))

    def adjustLimitsFromConfig(self, pSilent=True):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start adjustLimitsFromConfig")

        # load config
        self._timekprUserConfig.loadUserConfiguration()
        # log config
        self._timekprUserConfig.logUserConfiguration()

        # load the configuration into working structures
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()
        limitsPerWeekday = self._timekprUserConfig.getUserLimitsPerWeekdays()

        # limits per week & day
        # we do not have value (yet) for week
        self._timekprUserData[cons.TK_CTRL_LIMITW] = self._timekprUserConfig.getUserWeekLimit()
        # we do not have value (yet) for month
        self._timekprUserData[cons.TK_CTRL_LIMITM] = self._timekprUserConfig.getUserMonthLimit()

        # load PlayTime configuration into working structures
        allowedDaysPT = self._timekprUserConfig.getUserPlayTimeAllowedWeekdays()
        limitsPerWeekdayPT = self._timekprUserConfig.getUserPlayTimeLimitsPerWeekdays()

        # for allowed weekdays
        for rDay in cons.TK_ALLOWED_WEEKDAYS.split(";"):
            # days index
            idx = allowedDays.index(rDay) if rDay in allowedDays else -1
            # limits index
            idx = idx if idx >= 0 and len(limitsPerWeekday) > idx else -1

            # set up limits
            self._timekprUserData[rDay][cons.TK_CTRL_LIMITD] = limitsPerWeekday[idx] if idx >= 0 else 0

            # we do not have value (yet) for day
            if self._timekprUserData[rDay][cons.TK_CTRL_SPENTBD] is None:
                # no value means 0
                self._timekprUserData[rDay][cons.TK_CTRL_SPENTBD] = 0

            # only if not initialized
            if self._timekprUserData[rDay][cons.TK_CTRL_LEFTD] is None:
                # initialize left as limit, since we just loaded the configuration
                self._timekprUserData[rDay][cons.TK_CTRL_LEFTD] = self._timekprUserData[rDay][cons.TK_CTRL_LIMITD] - self._timekprUserData[rDay][cons.TK_CTRL_SPENTBD]

            # get hours for particular day
            allowedHours = self._timekprUserConfig.getUserAllowedHours(rDay)

            # check if it is enabled as per config
            dayAllowed = rDay in allowedDays

            # loop through all days
            for rHour in range(0, 23+1):
                # if day is disabled, it does not matter whether hour is (order of this if is important)
                if not dayAllowed:
                    # disallowed
                    hourAllowed = False
                # if hour is allowed
                elif str(rHour) in allowedHours:
                    # disallowed
                    hourAllowed = True
                    # set up minutes
                    self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_SMIN] = allowedHours[str(rHour)][cons.TK_CTRL_SMIN]
                    self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_EMIN] = allowedHours[str(rHour)][cons.TK_CTRL_EMIN]
                    self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_UACC] = allowedHours[str(rHour)][cons.TK_CTRL_UACC]
                # disallowed
                else:
                    hourAllowed = False

                # set up in structure
                self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_ACT] = hourAllowed

            # days index
            idx = allowedDaysPT.index(rDay) if rDay in allowedDaysPT else -1
            # limits index
            idx = idx if idx >= 0 and len(limitsPerWeekdayPT) > idx else -1
            # set up PlayTime limits
            self._timekprUserData[cons.TK_CTRL_PTCNT][rDay][cons.TK_CTRL_LIMITD] = limitsPerWeekdayPT[idx] if idx >= 0 else 0

        # process filters only when PT enabled
        if self._timekprUserConfig.getUserPlayTimeEnabled():
            # set up process filters
            self._timekprPlayTimeConfig.processPlayTimeFilters(self._timekprUserData[cons.TK_CTRL_UID], self._timekprUserConfig.getUserPlayTimeActivities())

        # set up last config mod time
        self._timekprUserData[cons.TK_CTRL_LCMOD] = self._timekprUserConfig.getUserConfigLastModified()

        # debug
        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "adjustLimitsFromConfig structure: %s" % (str(self._timekprUserData)))

        # get time limits and send them out if needed
        self.getTimeLimits()

        # inform user about change
        if not pSilent:
            # inform
            self._timekprUserNotification.timeConfigurationChangedNotification(cons.TK_PRIO_IMPORTANT_INFO)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish adjustLimitsFromConfig")

    def adjustTimeSpentFromControl(self, pSilent=True, pPreserveSpent=False):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start adjustTimeSpentFromControl")

        def _getPlayTimeBalanceSpent(pTimeSpentBeforeReload):
            """Get PlayTime spent balance"""
            # def
            bal = spent = 0
            # in case day changed
            if dayChanged:
                # get PT status
                isPTEna, isPTAcc, isPTAct = self._isPlayTimeEnabledAccountedActive(pSilent=True, pCheckActive=True)
                # if PlayTime is enabled and active, we need to account spent for those seconds (if not active, it will be left as 0)
                if isPTEna and isPTAct:
                    # seconds in hour for spent
                    spent = spentHour
                    # balance is accounted only when not in override
                    if isPTAcc:
                        bal = spentHour
            else:
                # just get the balance
                bal = self._timekprUserControl.getUserPlayTimeSpentBalance()
                spent = self._timekprUserControl.getUserPlayTimeSpentDay() + pTimeSpentBeforeReload
                # balance is adjusted if PT is accounted (not in override mode)
                if self._isPlayTimeEnabledAccountedActive(pSilent=True)[1]:
                    bal += pTimeSpentBeforeReload
            # result
            return bal, spent

        # in case we force reload the file, we need to account the time which was spent before reload too
        if pPreserveSpent:
            # get time spent which was calculated
            timeSpentBeforeReload = max(self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD] - self._timekprUserControl.getUserTimeSpentBalance(), 0)
            # check whether we need to change PT as well
            timeSpentBeforeReloadPT = max(self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD] - self._timekprUserControl.getUserPlayTimeSpentDay(), 0)
        else:
            # no additional time
            timeSpentBeforeReload = timeSpentBeforeReloadPT = 0

        # read from config
        self._timekprUserControl.loadUserControl()
        # log
        self._timekprUserControl.logUserControl()

        # tmp use
        spentHour = int((self._effectiveDatetime - self._timekprUserControl.getUserLastChecked()).total_seconds())
        # if time has changed ahead for more than for 3 years this might be a result in CMOS time reset (a user reported this - after CMOS reset it was year 2080)
        # in this case we do not reset the values, just soak them up and use them
        if spentHour > 86400 * 365 * 3:
            # way too ahead of last check time, possible CMOS reset time bug
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: user was last checked a very long time ago (%i seconds ago), spent values are not reset to avoid inconsistencies from time resets" % (spentHour))

            # nothing has changed
            dayChanged = weekChanged = monthChanged = False
        else:
            # control date components changed
            dayChanged, weekChanged, monthChanged = self._timekprUserControl.getUserDateComponentChanges(self._effectiveDatetime)

        # spent this hour
        spentHour = self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SPENTH]

        # if day has changed adjust balance
        self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD] = spentHour if dayChanged else self._timekprUserControl.getUserTimeSpentBalance() + timeSpentBeforeReload
        # if day has changed
        self._timekprUserData[cons.TK_CTRL_SPENTD] = spentHour if dayChanged else self._timekprUserControl.getUserTimeSpentDay() + timeSpentBeforeReload
        # if week changed changed
        self._timekprUserData[cons.TK_CTRL_SPENTW] = spentHour if weekChanged else self._timekprUserControl.getUserTimeSpentWeek() + timeSpentBeforeReload
        # if month changed
        self._timekprUserData[cons.TK_CTRL_SPENTM] = spentHour if monthChanged else self._timekprUserControl.getUserTimeSpentMonth() + timeSpentBeforeReload
        # import that into runtime config (if last check day is the same as current)
        self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD] = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMITD] - self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD]
        # account PlayTime as well
        self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTBD], self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD] = _getPlayTimeBalanceSpent(timeSpentBeforeReloadPT)
        # update last file mod time
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserControlLastModified()

        # inform user about change
        if not pSilent:
            # inform
            self._timekprUserNotification.timeLeftChangedNotification(cons.TK_PRIO_IMPORTANT_INFO)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish adjustTimeSpentFromControl")

    def _isPlayTimeEnabledAccountedActive(self, pSilent=False, pCheckActive=False):
        """Return whether PlayTime is enabled, accounted and used at the moment"""
        # def
        isPTActive = False
        # account PlayTime as well (it makes sense to check PT activity only if user is active in the system)
        isPTEnabled = self._timekprConfig.getTimekprPlayTimeEnabled() and self._timekprUserConfig.getUserPlayTimeEnabled()
        # whether override mode is enabled
        isPTAccounted = not self._timekprUserConfig.getUserPlayTimeOverrideEnabled()
        # check whether active too
        if pCheckActive and isPTEnabled:
            # PT active
            isPTActive = self._timekprPlayTimeConfig.verifyPlayTimeActive(self.getUserId(), self.getUserName(), pSilent)
        # result
        return isPTEnabled, isPTAccounted, isPTActive

    def adjustTimeSpentActual(self, pTimekprConfig):
        """Adjust time spent (and save it)"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start adjustTimeSpentActual")

        def _adjustTimeSpentValues(pDay, pHOD, pSecs, pActive):
            """Adjust time spent values"""
            # if hour is not accounted, we do not account main time
            if not pActive or self._timekprUserData[pDay][pHOD][cons.TK_CTRL_UACC]:
                # track sleep time
                self._timekprUserData[pDay][pHOD][cons.TK_CTRL_SLEEP] += pSecs

                # adjust totals for reporting
                self._timekprUserData[cons.TK_CTRL_SLEEP] += pSecs
            else:
                # adjust time spent hour
                self._timekprUserData[pDay][pHOD][cons.TK_CTRL_SPENTH] += pSecs
                # adjust time spent day balance
                self._timekprUserData[pDay][cons.TK_CTRL_SPENTBD] += pSecs
                # adjust time spent day
                self._timekprUserData[cons.TK_CTRL_SPENTD] += pSecs
                # adjust time spent week
                self._timekprUserData[cons.TK_CTRL_SPENTW] += pSecs
                # adjust time spent month
                self._timekprUserData[cons.TK_CTRL_SPENTM] += pSecs

                # adjust totals for reporting
                self._timekprUserData[cons.TK_CTRL_SPENT] += pSecs

        # check if dates have changed
        dayChanged, weekChanged, monthChanged = self._timekprUserControl.getUserDateComponentChanges(self._effectiveDatetime, self._timekprUserData[cons.TK_CTRL_LCHECK])
        # currentHOD in str
        currentHODStr = str(self._currentHOD)
        # get time spent
        timeSpent = max(int((self._effectiveDatetime - self._timekprUserData[cons.TK_CTRL_LCHECK]).total_seconds()), 0)
        # adjust last time checked
        self._timekprUserData[cons.TK_CTRL_LCHECK] = self._effectiveDatetime

        # determine if active
        userActiveActual, userScreenLocked = self._timekprUserManager.isUserActive(pTimekprConfig, self._timekprUserConfig, self._timekprUserData[cons.TK_CTRL_SCR_N])
        userActiveEffective = userActiveActual
        # def PlayTime
        userActivePT = False

        # account PlayTime as well (it makes sense to check PT activity only if user is active in the system)
        if userActiveEffective:
            # PT status
            isPTEna, isPTAcc, isPTAct = self._isPlayTimeEnabledAccountedActive(pSilent=True, pCheckActive=True)
            # enabled, check actul activity
            if isPTEna:
                # PT active
                userActivePT = isPTAct
                # if override is enabled, then active is determined differently
                if not isPTAcc:
                    # override
                    userActiveEffective = userActivePT

        # if time spent is very much higher than the default polling time, computer might went to sleep?
        if timeSpent >= cons.TK_POLLTIME * 15:
            # sleeping time is added to inactive time (there is a question whether that's OK, disabled currently)
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: it appears that computer was put to sleep for %i secs" % (timeSpent))
            # effectively spent is 0 (we ignore +/- 3 seconds here)
            timeSpent = 0
        else:
            # set time spent for previous hour (this may be triggered only when day changes)
            if timeSpent > self._secondsInHour:
                # adjust time values (either inactive or actual time)
                _adjustTimeSpentValues(self._timekprUserData[self._currentDOW][cons.TK_CTRL_PDAY] if dayChanged else self._currentDOW,
                    "23" if self._currentHOD == 0 else currentHODStr,
                    timeSpent - self._secondsInHour,
                    userActiveEffective)

            # adjust time spent for this hour
            timeSpent = min(timeSpent, self._secondsInHour)

        # if there is a day change, we need to adjust time for this day and day after
        if dayChanged:
            ### handle day change
            for rDay in (self._currentDOW, self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]):
                # clean up hours for this day
                for rHour in range(0, 23+1):
                    # reset spent for hour
                    self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_SPENTH] = 0
                    # reset sleeping
                    self._timekprUserData[rDay][str(rHour)][cons.TK_CTRL_SLEEP] = 0
                # reset balance for day
                self._timekprUserData[rDay][cons.TK_CTRL_SPENTBD] = 0
                # reset time spent for this day
                self._timekprUserData[cons.TK_CTRL_SPENTD] = 0

                # reset PlayTime balance for this day
                self._timekprUserData[cons.TK_CTRL_PTCNT][rDay][cons.TK_CTRL_SPENTBD] = 0
                # reset PlayTime spent for this day
                self._timekprUserData[cons.TK_CTRL_PTCNT][rDay][cons.TK_CTRL_SPENTD] = 0

            ### handle week change
            if weekChanged:
                # set spent for week as not initialized for this week, so new limits will apply properly
                self._timekprUserData[cons.TK_CTRL_SPENTW] = 0
            ### handle month change
            if monthChanged:
                # set spent for month as not initialized for this month, so new limits will apply properly
                self._timekprUserData[cons.TK_CTRL_SPENTM] = 0

        # adjust time values (either sleep or inactive or actual time)
        _adjustTimeSpentValues(self._currentDOW, currentHODStr, timeSpent, userActiveEffective)

        # count PlayTime if enabled
        if userActiveEffective and userActivePT:
            # when override is enabled, only balance for regular time is accounted, PT balance is not
            # if override is not enabled, we count this only for spent, not for balance (i.e. it will not count towards limit)
            if not self._timekprUserConfig.getUserPlayTimeOverrideEnabled():
                # adjust PlayTime balance this day
                self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTBD] += timeSpent
            # adjust PlayTime spent this day
            self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD] += timeSpent

        # logging section
        if dayChanged:
            log.log(cons.TK_LOG_LEVEL_INFO, "day change, user: %s, tbal: %i, tsp: %i, ptbal: %i, ptsp: %i" % (self.getUserName(), self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD], self._timekprUserData[cons.TK_CTRL_SPENTD], self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTBD], self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD]))
            if weekChanged:
                log.log(cons.TK_LOG_LEVEL_INFO, "week change, user: %s, twk: %i" % (self.getUserName(), self._timekprUserData[cons.TK_CTRL_SPENTW]))
            if monthChanged:
                log.log(cons.TK_LOG_LEVEL_INFO, "month change, user: %s, tmon: %i" % (self.getUserName(), self._timekprUserData[cons.TK_CTRL_SPENTM]))

        # check if we need to save progress
        if abs((self._effectiveDatetime - self._timekprUserData[cons.TK_CTRL_LSAVE]).total_seconds()) >= pTimekprConfig.getTimekprSaveTime() or dayChanged:
            # save
            self.saveSpent()

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish adjustTimeSpentActual")

        # returns if user is active
        return userActiveEffective, userActiveActual, userScreenLocked

    def getTimeLeft(self, pForceNotifications=False):
        """Get how much time is left (for this day and in a row for max this and next day)"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start getTimeLeft")
        # time left in a row
        timeLeftToday = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD]
        # time left in a row
        timeLeftInARow = self._timekprUserData[cons.TK_CTRL_LEFT]
        # time spent this session / time inactive this session / time available from intervals
        timeSpentThisSession = timeInactiveThisSession = timeAvailableIntervals = 0

        # go through hours for this day
        for j in range(0, 23+1):
            # for current day (and enabled hours)
            if self._timekprUserData[self._currentDOW][str(j)][cons.TK_CTRL_ACT]:
                timeAvailableIntervals += ((self._timekprUserData[self._currentDOW][str(j)][cons.TK_CTRL_EMIN] - self._timekprUserData[self._currentDOW][str(j)][cons.TK_CTRL_SMIN]) * 60)

        # totals
        timeSpentThisSession = self._timekprUserData[cons.TK_CTRL_SPENT]
        timeInactiveThisSession = self._timekprUserData[cons.TK_CTRL_SLEEP]

        # time spent balance for the day
        timeSpentBalance = self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD]
        # time spent for the day
        timeSpentDay = self._timekprUserData[cons.TK_CTRL_SPENTD]
        # time spent for week
        timeSpentWeek = self._timekprUserData[cons.TK_CTRL_SPENTW]
        # time spent for week
        timeSpentMonth = self._timekprUserData[cons.TK_CTRL_SPENTM]
        # unaccounted hour
        isCurrentTimeBetweenInterval = self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SMIN] <= self._currentMOH <= self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_EMIN]
        timeUnaccountedHour = self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_UACC] if isCurrentTimeBetweenInterval else False
        # debug (bt = since boot / restart)
        log.log(cons.TK_LOG_LEVEL_INFO, "get time for \"%s\", tltd %i, tlrow: %i, tspbal: %i, tspbt: %i, tidbt: %i" % (self.getUserName(), timeLeftToday, timeLeftInARow, timeSpentBalance, timeSpentThisSession, timeInactiveThisSession))

        # set up values
        timeValues = {}
        timeValues[cons.TK_CTRL_LEFTD] = timeLeftToday
        timeValues[cons.TK_CTRL_LEFT] = timeLeftInARow
        timeValues[cons.TK_CTRL_SPENT] = timeSpentThisSession
        timeValues[cons.TK_CTRL_SPENTW] = timeSpentWeek
        timeValues[cons.TK_CTRL_SPENTM] = timeSpentMonth
        timeValues[cons.TK_CTRL_SLEEP] = timeInactiveThisSession
        timeValues[cons.TK_CTRL_TRACK] = self._timekprUserConfig.getUserTrackInactive()
        timeValues[cons.TK_CTRL_HIDEI] = self._timekprUserConfig.getUserHideTrayIcon()
        timeValues[cons.TK_CTRL_LIMITD] = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMITD]
        timeValues[cons.TK_CTRL_TNL] = (1 if self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMITD] >= cons.TK_LIMIT_PER_DAY and timeAvailableIntervals >= cons.TK_LIMIT_PER_DAY else 0)
        # PlayTime (only if enabled)
        if self._isPlayTimeEnabledAccountedActive(pSilent=True)[0]:
            # time and config for PlayTime
            timeValues[cons.TK_CTRL_PTTLO] = self._timekprUserConfig.getUserPlayTimeOverrideEnabled()
            timeValues[cons.TK_CTRL_PTAUH] = self._timekprUserConfig.getUserPlayTimeUnaccountedIntervalsEnabled()
            timeValues[cons.TK_CTRL_PTSPD] = self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD]
            timeValues[cons.TK_CTRL_PTLPD] = max(0, self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_LEFTD])
            timeValues[cons.TK_CTRL_PTLSTC] = self.getPlayTimeActiveActivityCnt()

        # pass uacc too, so notifications can be prevented when hour is unaccounted
        timeValues[cons.TK_CTRL_UACC] = timeUnaccountedHour

        # if debug
        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "force: %i, timeValues structure: %s" % (pForceNotifications, timeValues))

        # process notifications, if needed
        self._timekprUserNotification.processTimeLeft(pForceNotifications, timeValues)

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish getTimeLeft")

        # return calculated
        return timeLeftToday, timeLeftInARow, timeSpentThisSession, timeInactiveThisSession, timeSpentBalance, timeSpentDay, timeUnaccountedHour

    def getPlayTimeLeft(self, pCheckActive=True):
        """Return whether time is over for PlayTime"""
        # get time left
        timeLeftPT = self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_LEFTD]
        # get PT status
        isPTEnabled, isPTAccounted, isPTActive = self._isPlayTimeEnabledAccountedActive(pCheckActive=pCheckActive)
        # if PT is enabled, log the information
        if isPTEnabled:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "get PlayTime for \"%s\", ena: %s, acc: %s, tim: %i" % (self.getUserName(), isPTEnabled, isPTAccounted, timeLeftPT))
        # result
        return timeLeftPT, isPTEnabled, isPTAccounted, isPTActive

    def saveSpent(self):
        """Save the time spent by the user"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start saveSpent")

        # initial config loaded
        userConfigLastModified = self._timekprUserConfig.getUserConfigLastModified()
        userControlLastModified = self._timekprUserControl.getUserControlLastModified()

        # check whether we need to reload file (if externally modified)
        if self._timekprUserData[cons.TK_CTRL_LCMOD] != userConfigLastModified:
            log.log(cons.TK_LOG_LEVEL_INFO, "user \"%s\" config changed, prev/now: %s / %s" % (self.getUserName(), self._timekprUserData[cons.TK_CTRL_LCMOD].strftime(cons.TK_LOG_DATETIME_FORMAT), userConfigLastModified.strftime(cons.TK_LOG_DATETIME_FORMAT)))
            # load config
            self.adjustLimitsFromConfig(pSilent=False)

        # check whether we need to reload file (if externally modified)
        if self._timekprUserData[cons.TK_CTRL_LMOD] != userControlLastModified or self._timekprUserData[cons.TK_CTRL_LCMOD] != userConfigLastModified:
            # log the change
            if self._timekprUserData[cons.TK_CTRL_LMOD] != userControlLastModified:
                log.log(cons.TK_LOG_LEVEL_INFO, "user \"%s\" control changed, prev/now: %s / %s" % (self.getUserName(), self._timekprUserData[cons.TK_CTRL_LMOD].strftime(cons.TK_LOG_DATETIME_FORMAT), userControlLastModified.strftime(cons.TK_LOG_DATETIME_FORMAT)))
            # load config
            self.adjustTimeSpentFromControl(pSilent=False, pPreserveSpent=True)

        # adjust save time as well
        self._timekprUserData[cons.TK_CTRL_LSAVE] = self._effectiveDatetime

        # save spent time
        self._timekprUserControl.setUserTimeSpentBalance(self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTBD])
        self._timekprUserControl.setUserTimeSpentDay(self._timekprUserData[cons.TK_CTRL_SPENTD])
        self._timekprUserControl.setUserTimeSpentWeek(self._timekprUserData[cons.TK_CTRL_SPENTW])
        self._timekprUserControl.setUserTimeSpentMonth(self._timekprUserData[cons.TK_CTRL_SPENTM])
        self._timekprUserControl.setUserLastChecked(self._effectiveDatetime)
        self._timekprUserControl.setUserPlayTimeSpentBalance(self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTBD])
        self._timekprUserControl.setUserPlayTimeSpentDay(self._timekprUserData[cons.TK_CTRL_PTCNT][self._currentDOW][cons.TK_CTRL_SPENTD])
        self._timekprUserControl.saveControl()
        # renew last modified
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserControlLastModified()

        # if debug
        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "save spent structure: %s" % (str(self._timekprUserData[self._currentDOW])))

        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish saveSpent")

    def getTimeLimits(self):
        """Calculate time limits for sendout to clients"""
        # main container
        timeLimits = {}

        # check allowed days
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()

        # traverse the config and get intervals
        for rDay in cons.TK_ALLOWED_WEEKDAYS.split(";"):
            # if day is ok, then check hours
            if rDay in allowedDays:
                # assign a time limit for the day
                timeLimits[rDay] = {cons.TK_CTRL_LIMITD: self._timekprUserData[rDay][cons.TK_CTRL_LIMITD], cons.TK_CTRL_INT: list()}
                # init hours for intervals
                startHour  = endHour = uaccValue = None
                uaccChanged = False

                # loop through all days
                for rHour in range(0, 23+1):
                    # hour in str
                    hourStr = str(rHour)
                    # fill up start value
                    if self._timekprUserData[rDay][hourStr][cons.TK_CTRL_ACT]:
                        # no value (interval was changed)
                        uaccValue = self._timekprUserData[rDay][hourStr][cons.TK_CTRL_UACC] if uaccValue is None else uaccValue
                        # calc uacc changes
                        uaccChanged = self._timekprUserData[rDay][hourStr][cons.TK_CTRL_UACC] != uaccValue

                    # this is needed in case next hour starts with particular minutes, in which case continous interval ends
                    if startHour is not None and (self._timekprUserData[rDay][hourStr][cons.TK_CTRL_SMIN] != 0 or uaccChanged):
                        # fill interval with start and end (because hours are continous, we can count on sequential change)
                        timeLimits[rDay][cons.TK_CTRL_INT].append([int(startHour), int(endHour), uaccValue])
                        # restart hour intervals
                        startHour = uaccValue = None
                        uaccChanged = False

                    # if hour is enabled for use, we count the interval
                    if self._timekprUserData[rDay][hourStr][cons.TK_CTRL_ACT]:
                        # uacc value
                        uaccValue = self._timekprUserData[rDay][hourStr][cons.TK_CTRL_UACC]
                        # set start hour only if it has not beed set up, that is to start the interval
                        if startHour is None:
                            # start
                            startHour = int(((cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timekprUserData[rDay][hourStr][cons.TK_CTRL_SMIN])) - cons.TK_DATETIME_START).total_seconds())
                        # end
                        endHour = int(((cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timekprUserData[rDay][hourStr][cons.TK_CTRL_EMIN])) - cons.TK_DATETIME_START).total_seconds())

                    # interval ends if hour is not allowed or this is the end of the day
                    if (not self._timekprUserData[rDay][hourStr][cons.TK_CTRL_ACT] and startHour is not None) or self._timekprUserData[rDay][hourStr][cons.TK_CTRL_EMIN] != 60:
                        # fill interval with start and end (because end interval is unfinished (break in continuity))
                        timeLimits[rDay][cons.TK_CTRL_INT].append([int(startHour), int(endHour), uaccValue])
                        # restart hour intervals
                        startHour = uaccValue = None
                        uaccChanged = False

                # after we processed intervals, let's check whether we closed all, if not do it
                if startHour is not None:
                    # fill unfinished interval
                    timeLimits[rDay][cons.TK_CTRL_INT].append([int(startHour), int(endHour), uaccValue])

        # weekly and monthly limits
        timeLimits[cons.TK_CTRL_LIMITW] = self._timekprUserData[cons.TK_CTRL_LIMITW]
        # weekly and monthly limits
        timeLimits[cons.TK_CTRL_LIMITM] = self._timekprUserData[cons.TK_CTRL_LIMITM]

        # ## PlayTime ##
        # initialize limit and process list
        timeLimits[cons.TK_CTRL_PTLMT] = list()
        timeLimits[cons.TK_CTRL_PTLST] = list()
        # get PT days, limits and activities
        allowedDaysPT = self._timekprUserConfig.getUserPlayTimeAllowedWeekdays()
        allowedLimitsPT = self._timekprUserConfig.getUserPlayTimeLimitsPerWeekdays()
        allowedApplsPT = self._timekprUserConfig.getUserPlayTimeActivities()
        # fill in limits (keep this ordered for days)
        for rDay in cons.TK_ALLOWED_WEEKDAYS.split(";"):
            # days index
            idx = allowedDaysPT.index(rDay) if rDay in allowedDaysPT else -1
            # limits index
            idx = idx if idx >= 0 and len(allowedLimitsPT) > idx else -1
            # check if particular day is enabled
            if idx >= 0:
                # add day and limit to the list
                timeLimits[cons.TK_CTRL_PTLMT].append([rDay, allowedLimitsPT[idx]])
        # fill in activities
        for rAppl in allowedApplsPT:
            # add process (process and description) to the list
            timeLimits[cons.TK_CTRL_PTLST].append(rAppl)
        # add enable as well (exception in limits case)
        timeLimits[cons.TK_CTRL_PTTLE] = (1 if self._timekprUserConfig.getUserPlayTimeEnabled() else 0)
        # add override as well (exception in limits case)
        timeLimits[cons.TK_CTRL_PTTLO] = (1 if self._timekprUserConfig.getUserPlayTimeOverrideEnabled() else 0)
        # add allowed during unaccounted intervals as well (exception in limits case)
        timeLimits[cons.TK_CTRL_PTAUH] = (1 if self._timekprUserConfig.getUserPlayTimeUnaccountedIntervalsEnabled() else 0)

        # debug
        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "TL: %s" % (str(timeLimits)))

        # process notifications, if needed
        self._timekprUserNotification.processTimeLimits(timeLimits)

    def processUserSessionAttributes(self, pWhat, pKey, pValue):
        """This will set up request or verify actual request for user attribute changes"""
        # depends on what attribute
        if pWhat == cons.TK_CTRL_SCR_N:
            # set it to false, e.g. not in force
            self._timekprUserData[cons.TK_CTRL_SCR_N] = False
            # if there is no key, we need to set up validation key
            if pKey == "":
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "session attributes request: %s" % (pWhat))
                # generate random key
                self._timekprUserData[cons.TK_CTRL_SCR_K] = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                """
                Clarification about re-validation.
                    Theoretically it's not that hard to fake these, if one desires. Just write a sofware that responds to requests.
                    However, that is doable only for those who know what to do and those are mostly experienced users (I would say
                    xperienced a LOT (DBUS is not common to non-developers)), so maybe they should not be using timekpr in the first place?
                """
                # send verification request
                self._timekprUserNotification.procesSessionAttributes(pWhat, self._timekprUserData[cons.TK_CTRL_SCR_K])
            # if key set set up in server, we compare it
            elif pKey is not None and self._timekprUserData[cons.TK_CTRL_SCR_K] is not None:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "session attributes verify: %s,%s,%s" % (pWhat, "key", pValue))
                # if verification is successful
                if pKey == self._timekprUserData[cons.TK_CTRL_SCR_K]:
                    # set up valid property
                    self._timekprUserData[cons.TK_CTRL_SCR_N] = True if str(pValue).lower() in ("true", "1") else False
                # reset key anyway
                self._timekprUserData[cons.TK_CTRL_SCR_K] = None
            else:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "session attributes out of order: %s,%s,%s" % (pWhat, "key", pValue))
                # reset key anyway
                self._timekprUserData[cons.TK_CTRL_SCR_K] = None

    def revalidateUserSessionAttributes(self):
        """Actual user session attributes have to be revalidated from time to time. This will take care of that"""
        # increase stuff
        self._timekprUserData[cons.TK_CTRL_SCR_R] += 1

        # revalidate only when time has come
        if self._timekprUserData[cons.TK_CTRL_SCR_R] >= math.ceil(cons.TK_MAX_RETRIES / 2):
            # screensaver
            # revalidate only if active (that influences time accounting)
            if self._timekprUserData[cons.TK_CTRL_SCR_N]:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "send re-validation request to user \"%s\"" % (self.getUserName()))
                # send verification request
                self.processUserSessionAttributes(cons.TK_CTRL_SCR_N, "", None)

            # reset retries
            self._timekprUserData[cons.TK_CTRL_SCR_R] = 0

    def findNextAvailableIntervalStart(self):
        """Find next available interval start for user"""
        # result
        res = None
        # wakeup hours
        hrs = self._timekprUserConfig.getUserWakeupHourInterval()
        hrFrom = int(hrs[0])
        hrTo = int(hrs[1])
        # loop through all hours for today
        for rHour in range(self._currentHOD, 23+1):
            # check if hour is enabled
            if self._timekprUserData[self._currentDOW][str(rHour)][cons.TK_CTRL_ACT]:
                # if current hour, we need to check whether it's possible to use it (check +one minute ahead)
                if rHour == self._currentHOD and self._currentMOH + 1 >= self._timekprUserData[self._currentDOW][str(rHour)][cons.TK_CTRL_SMIN]:
                    # start can not be used as it is in the past
                    continue
                # only if wakeup interval is right
                elif hrFrom <= rHour <= hrTo:
                    # check if we have interval
                    res = int(datetime(self._effectiveDatetime.year, self._effectiveDatetime.month, self._effectiveDatetime.day, rHour, self._timekprUserData[self._currentDOW][str(rHour)][cons.TK_CTRL_SMIN]).strftime("%s"))
                # this is it
                break
        # msg if none found
        if res is None:
            log.log(cons.TK_LOG_LEVEL_INFO, "there is no next interval available today for user \"%s\"" % (self.getUserName()))
        # return
        return res

    def setPlayTimeActiveActivityCnt(self, pActiveActivityCnt):
        """This sets count of active activities"""
        self._timekprUserData[cons.TK_CTRL_PTCNT][cons.TK_CTRL_PTLSTC] = pActiveActivityCnt

    def getUserId(self):
        """Return user id"""
        return self._timekprUserData[cons.TK_CTRL_UID]

    def getUserName(self):
        """Return user name"""
        return self._timekprUserData[cons.TK_CTRL_UNAME]

    def getUserPathOnBus(self):
        """Return user DBUS path"""
        return self._timekprUserData[cons.TK_CTRL_UPATH]

    def getUserLockoutType(self):
        """Return user lockout type"""
        return self._timekprUserConfig.getUserLockoutType()

    def getPlayTimeActiveActivityCnt(self):
        """This returns count of active activities"""
        return self._timekprUserData[cons.TK_CTRL_PTCNT][cons.TK_CTRL_PTLSTC]

    def getUserPlayTimeUnaccountedIntervalsEnabled(self):
        """Return whether PlayTime activities are allowed during unlimited hours"""
        return self._timekprUserConfig.getUserPlayTimeUnaccountedIntervalsEnabled()

    def processFinalWarning(self, pFinalNotificationType, pSecondsLeft):
        """Process emergency message about killing"""
        self._timekprUserNotification.processEmergencyNotification(pFinalNotificationType, max(pSecondsLeft, 0))

    def lockUserSessions(self):
        """Lock all user sessions"""
        # only if we are not in DEV mode
        if cons.TK_DEV_ACTIVE:
            log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not locking myself, sorry...")
        else:
            # lock session
            self._timekprUserManager.lockUserSessions()
