"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
from datetime import datetime, timedelta
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
    """Contain all the data for timekpr user"""

    def __init__(self, pLog, pBusName, pUserId, pUserName, pUserPath, pConfigDir, pWorkDir):
        """Initialize all stuff for user"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekprUser")

        # deatch sentence
        self._finalCountdown = 0

        # init limit structure
        self._timekprUserData = self.initUserLimits()

        # set user data
        self._timekprUserData[cons.TK_CTRL_UID] = pUserId
        self._timekprUserData[cons.TK_CTRL_UNAME] = pUserName
        self._timekprUserData[cons.TK_CTRL_UPATH] = pUserPath
        # set up user properties
        self._timekprUserData[cons.TK_CTRL_SCR_N] = False  # is screensaver running
        self._timekprUserData[cons.TK_CTRL_SCR_K] = None  # verification key

        # save the bus
        self._timekprUserManager = timekprUserManager(pLog, self._timekprUserData[cons.TK_CTRL_UNAME], self._timekprUserData[cons.TK_CTRL_UPATH])
        # user config
        self._timekprUserConfig = timekprUserConfig(pLog, pConfigDir, self._timekprUserData[cons.TK_CTRL_UNAME])
        # user control
        self._timekprUserControl = timekprUserControl(pLog, pWorkDir, self._timekprUserData[cons.TK_CTRL_UNAME])
        # user notification
        self._timekprUserNotification = timekprNotificationManager(pLog, pBusName, self._timekprUserData[cons.TK_CTRL_UNAME])

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekprUser")

    def initTimekprVariables(self):
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
        self._secondsLeftDay = ((datetime(self._effectiveDatetime.year, self._effectiveDatetime.month, self._effectiveDatetime.day) + timedelta(days=1)) - self._effectiveDatetime).total_seconds()
        # get seconds left in hour
        self._secondsLeftHour = ((self._effectiveDatetime + timedelta(hours=1)).replace(microsecond=0, second=0, minute=0) - self._effectiveDatetime).total_seconds()
        # how many seconds are in this hour
        self._secondsInHour = (self._effectiveDatetime - self._effectiveDatetime.replace(microsecond=0, second=0, minute=0)).total_seconds()

    def initUserLimits(self):
        """Initialize default limits for the user"""
        # the config works as follows:
        #    we have cons.LIMIT, this limit is either time allowed per day or if that is not used, all seconds in allowed hours
        #    in hour section (0 is the sample in config), we have whether one is allowed to work in particular hour and then we have time spent (which can be paused as well)
        #    the rest must be easy
        # define structure for limits
        # day: next day | limit | left per day + hours 0 - 23 (0 hour sample included)
        limits = {
            # per day values
             "1"                 : {cons.TK_CTRL_NDAY: "2", cons.TK_CTRL_PDAY: "7", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"2"                 : {cons.TK_CTRL_NDAY: "3", cons.TK_CTRL_PDAY: "1", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"3"                 : {cons.TK_CTRL_NDAY: "4", cons.TK_CTRL_PDAY: "2", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"4"                 : {cons.TK_CTRL_NDAY: "5", cons.TK_CTRL_PDAY: "3", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"5"                 : {cons.TK_CTRL_NDAY: "6", cons.TK_CTRL_PDAY: "4", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"6"                 : {cons.TK_CTRL_NDAY: "7", cons.TK_CTRL_PDAY: "5", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"7"                 : {cons.TK_CTRL_NDAY: "1", cons.TK_CTRL_PDAY: "6", cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_SPENTD: None, cons.TK_CTRL_LEFTD: None, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            # additional limits
            ,cons.TK_CTRL_LIMITW : None  # this is limit per week (not used yet)
            ,cons.TK_CTRL_LIMITM : None  # this is limit per month (not used yet)
            # global time acconting values
            ,cons.TK_CTRL_LEFT   : 0 # this is how much time left is countinously
            ,cons.TK_CTRL_LEFTW  : 0  # this is left per week (not used yet)
            ,cons.TK_CTRL_LEFTM  : 0  # this is left per month (not used yet)
            ,cons.TK_CTRL_SPENTW : 0  # this is spent per week (not used yet)
            ,cons.TK_CTRL_SPENTM : 0  # this is spent per month (not used yet)
            # checking values
            ,cons.TK_CTRL_LCHECK : datetime.now().replace(microsecond=0)  # this is last checked time
            ,cons.TK_CTRL_LSAVE  : datetime.now().replace(microsecond=0)  # this is last save time (physical save will be less often as check)
            ,cons.TK_CTRL_LMOD   : datetime.now().replace(microsecond=0)  # this is last control save time
            ,cons.TK_CTRL_LCMOD  : datetime.now().replace(microsecond=0)  # this is last config save time
            # user values
            ,cons.TK_CTRL_UID    : None  # user id (not used, but still saved)
            ,cons.TK_CTRL_UNAME  : ""  # user name, this is the one we need
            ,cons.TK_CTRL_UPATH  : ""  # this is for DBUS communication purposes
            # user session values (comes directly from user session)
            ,cons.TK_CTRL_SCR_N  : False  # actual value
            ,cons.TK_CTRL_SCR_K  : None  # verification key value
            ,cons.TK_CTRL_SCR_R  : 0  # retry count for verification
        }

        # fill up every hour
        # loop through days
        for i in range(1, 7+1):
            # loop through hours
            for j in range(0, 23+1):
                # initial limit is whole hour
                limits[str(i)][str(j)] = {cons.TK_CTRL_ACT: False, cons.TK_CTRL_SPENTH: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # return limits
        return limits

    def deInitUser(self):
        """De-initialize timekpr user"""
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
        # continous time
        contTime = True

        # calculate "lefts"
        timesLeft = {cons.TK_CTRL_LEFTD: 0, cons.TK_CTRL_LEFTW: self._timekprUserData[cons.TK_CTRL_LEFTW], cons.TK_CTRL_LEFTM: self._timekprUserData[cons.TK_CTRL_LEFTM]}

        # go through days
        for i in [self._currentDOW, self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]]:
            # reset "lefts"
            self._timekprUserData[i][cons.TK_CTRL_LEFTD] = 0

            # how many seconds left for that day (not counting hours limits yet)
            timesLeft[cons.TK_CTRL_LEFTD] = self._timekprUserData[i][cons.TK_CTRL_LIMITD] - self._timekprUserData[i][cons.TK_CTRL_SPENTD]

            # left is least of the limits
            secondsLeft = max(min(timesLeft[cons.TK_CTRL_LEFTD], timesLeft[cons.TK_CTRL_LEFTW], timesLeft[cons.TK_CTRL_LEFTM]), 0)

            # determine current HOD
            currentHOD = self._currentHOD if self._currentDOW == i else 0

            # go through hours for this day
            for j in range(currentHOD, 23+1):
                # reset seconds to add
                secondsToAddHour = 0
                secondsLeftHour = 0

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
                    # save seconds to subtract for this hour
                    secondsToAddHour = max(min(secondsLeftHour, secondsLeftHourLimit, secondsLeft), 0)

                    # debug
                    if log.isDebug():
                        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "currentDOW: %s, currentHOD: %s, secondsLeftHour: %s, currentMOH: %s, currentSOM: %s, secondsLeftHourLimit: %s, secondsToAddHour: %s, secondsLeft: %s" % (str(i), str(j), secondsLeftHour, self._currentMOH, self._effectiveDatetime.second, secondsLeftHourLimit, secondsToAddHour, secondsLeft))
                # hour is disabled
                else:
                    # time is over already from the start (it won't be added to current session, but we'll count the rest of hours allowed)
                    contTime = False

                # debug
                if log.isDebug():
                    log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "day: %s, hour: %s, enabled: %s, addToHour: %s, contTime: %s, left: %s, leftWk: %s, leftMon: %s" % (i, str(j), self._timekprUserData[i][str(j)][cons.TK_CTRL_ACT], secondsToAddHour, contTime, timesLeft[cons.TK_CTRL_LEFTD], self._timekprUserData[cons.TK_CTRL_LEFTW], self._timekprUserData[cons.TK_CTRL_LEFTM]))

                # adjust left continously
                self._timekprUserData[cons.TK_CTRL_LEFT] += secondsToAddHour if contTime else 0
                # adjust left this hour
                self._timekprUserData[i][cons.TK_CTRL_LEFTD] += secondsToAddHour
                # recalculate whether time is continous
                contTime = True if (contTime and not secondsToAddHour < secondsLeftHour) else False

                # recalculate "lefts"
                timesLeft[cons.TK_CTRL_LEFTD] -= secondsToAddHour
                timesLeft[cons.TK_CTRL_LEFTW] -= secondsToAddHour
                timesLeft[cons.TK_CTRL_LEFTM] -= secondsToAddHour
                secondsLeft -= secondsToAddHour

                # this is it (time over)
                if secondsLeft <= 0:
                    break

            # this is it (no time or there will be no continous time for this day)
            if secondsLeft <= 0 or not contTime:
                break

        # debug
        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "leftInRow: %s, leftDay: %s, lefDay+1: %s" % (self._timekprUserData[cons.TK_CTRL_LEFT], self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD], self._timekprUserData[self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]][cons.TK_CTRL_LEFTD]))

    def adjustLimitsFromConfig(self, pSilent=True):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustLimitsFromConfig")

        # init config
        self._timekprUserConfig.loadConfiguration()

        # load the configuration into working structures
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()
        limitsPerWeekday = self._timekprUserConfig.getUserLimitsPerWeekdays()

        # limits per week & day
        # we do not have value (yet) for week
        self._timekprUserData[cons.TK_CTRL_LIMITW] = self._timekprUserConfig.getUserWeekLimit()
        # we do not have value (yet) for month
        self._timekprUserData[cons.TK_CTRL_LIMITM] = self._timekprUserConfig.getUserMonthLimit()

        # for allowed weekdays
        for rDay in range(1, 7+1):
            # set up limits
            self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMITD] = limitsPerWeekday[allowedDays.index(rDay)] if rDay in allowedDays else 0

            # we do not have value (yet) for day
            if self._timekprUserData[str(rDay)][cons.TK_CTRL_SPENTD] is None:
                self._timekprUserData[str(rDay)][cons.TK_CTRL_SPENTD] = 0

            # only if not initialized
            if self._timekprUserData[str(rDay)][cons.TK_CTRL_LEFTD] is None:
                # initialize left as limit, since we just loaded the configuration
                self._timekprUserData[str(rDay)][cons.TK_CTRL_LEFTD] = self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMITD] - self._timekprUserData[str(rDay)][cons.TK_CTRL_SPENTD]

            # get hours for particular day
            allowedHours = self._timekprUserConfig.getUserAllowedHours(rDay)

            # check if it is enabled as per config
            if rDay in allowedDays:
                dayAllowed = True
            else:
                dayAllowed = False

            # loop through all days
            for rHour in range(0, 23+1):
                # if day is disabled, it does not matter whether hour is
                if not dayAllowed:
                    # disallowed
                    hourAllowed = False
                # if hour is allowed
                elif str(rHour) in allowedHours:
                    # disallowed
                    hourAllowed = True
                    # set up minutes
                    self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_SMIN] = allowedHours[str(rHour)][cons.TK_CTRL_SMIN]
                    self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_EMIN] = allowedHours[str(rHour)][cons.TK_CTRL_EMIN]
                # disallowed
                else:
                    hourAllowed = False

                # set up in structure
                self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_ACT] = hourAllowed

        # set up last config mod time
        self._timekprUserData[cons.TK_CTRL_LCMOD] = self._timekprUserConfig.getUserLastModified()

        # debug
        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "adjustLimitsFromConfig structure: %s" % (str(self._timekprUserData)))

        # get time limits and send them out if needed
        self.getTimeLimits()

        # inform user about change
        if not pSilent:
            # inform
            self._timekprUserNotification.timeConfigurationChangedNotification(cons.TK_PRIO_IMPORTANT_INFO)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish adjustLimitsFromConfig")

    def adjustTimeSpentFromControl(self, pSilent=True):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustTimeSpentFromControl")

        # read from config
        self._timekprUserControl.loadControl()
        # spent this hour
        spentHour = self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SPENTH]
        # day changed
        dayChanged = self._timekprUserControl.getUserLastChecked().date() != self._effectiveDatetime.date()
        weekChanged = self._timekprUserControl.getUserLastChecked().date().isocalendar()[1] != self._effectiveDatetime.date().isocalendar()[1]
        monthChanged = self._timekprUserControl.getUserLastChecked().date().month != self._effectiveDatetime.date().month

        # if day has changed
        self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTD] = spentHour if dayChanged else self._timekprUserControl.getUserTimeSpent()
        # if week changed changed
        self._timekprUserData[cons.TK_CTRL_SPENTW] = spentHour if weekChanged else self._timekprUserControl.getUserTimeSpentWeek()
        # if month changed
        self._timekprUserData[cons.TK_CTRL_SPENTM] = spentHour if monthChanged else self._timekprUserControl.getUserTimeSpentMonth()

        # import that into runtime config (if last check day is the same as current)
        self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD] = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMITD] - self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTD]

        # update last file mod time
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserLastModified()

        # inform user about change
        if not pSilent:
            # inform
            self._timekprUserNotification.timeLeftChangedNotification(cons.TK_PRIO_IMPORTANT_INFO)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish adjustTimeSpentFromControl")

    def adjustTimeSpentActual(self, pSessionTypes, pSessionTypesExcl, pTimekprSaveInterval):
        """Adjust time spent (and save it)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustTimeSpentActual")

        # calendar
        isoCalendar = datetime.date(self._timekprUserData[cons.TK_CTRL_LCHECK]).isocalendar()
        # get last checked DOW
        lastCheckDOW = str(isoCalendar[2])
        # get last checked WEEK
        lastCheckWeek = isoCalendar[1]
        # get last checked MONTH
        lastCheckMonth = self._timekprUserData[cons.TK_CTRL_LCHECK].month
        # get time spent
        timeSpent = (self._effectiveDatetime - self._timekprUserData[cons.TK_CTRL_LCHECK]).total_seconds()

        # determine if active
        isUserActive = self.isUserActive(pSessionTypes)

        # if time spent is very much higher than the default polling time, computer might went to sleep?
        if timeSpent >= cons.TK_POLLTIME * 15:
            # sleeping time is added to inactive time (there is a question whether that's OK, disabled currently)
            log.log(cons.TK_LOG_LEVEL_DEBUG, "INFO: sleeping for %s" % (timeSpent))
            # effectively spent is 0 (we ignore +/- 3 seconds here)
            timeSpent = 0
        else:
            # get time spent for this hour (if hour passed in between checks and it's not the first hour, we need to properly adjust this hour)
            if timeSpent > self._secondsInHour and self._currentHOD != 0:
                # adjust previous hour
                self._timekprUserData[self._currentDOW][str(self._currentHOD-1)][cons.TK_CTRL_SPENTH] += timeSpent - self._secondsInHour

            # adjust time spent for this hour
            timeSpent = min(timeSpent, self._secondsInHour)

        # how long user has been sleeping
        if not isUserActive:
            # track sleep time
            self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SLEEP] += timeSpent
        # adjust time spent only if user is active
        elif isUserActive:
            # adjust time spent this hour
            self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SPENTH] += timeSpent
            # adjust time spent this day
            self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTD] += timeSpent
            # adjust time spent this week
            self._timekprUserData[cons.TK_CTRL_SPENTW] += timeSpent
            # adjust time spent this month
            self._timekprUserData[cons.TK_CTRL_SPENTM] += timeSpent

        # adjust last time checked
        self._timekprUserData[cons.TK_CTRL_LCHECK] = self._effectiveDatetime

        # if there is a day change, we need to adjust time for this day and day after
        if lastCheckDOW != self._currentDOW:
            # only if this is not the end of the day (this should not happen)
            if self._currentHOD != 23:
                # clean up hours for this day
                for j in range(self._currentHOD+1, 23+1):
                    # reset spent for this hour
                    self._timekprUserData[self._currentDOW][str(j)][cons.TK_CTRL_SPENTH] = 0
                    # reset sleeping
                    self._timekprUserData[self._currentDOW][str(j)][cons.TK_CTRL_SLEEP] = 0
                    # TODO: do we need to clean next day as well? (think)

            # reset spent for this hour
            self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SPENTH] = timeSpent
            # set spent as not initialized for today, so new limits will apply properly
            self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTD] = timeSpent

            # check if week changed
            if lastCheckWeek != datetime.date(self._effectiveDatetime).isocalendar()[1]:
                # set spent for week as not initialized for this week, so new limits will apply properly
                self._timekprUserData[cons.TK_CTRL_SPENTW] = timeSpent
            # check if month changed
            if lastCheckMonth != self._effectiveDatetime.month:
                # set spent for month as not initialized for this month, so new limits will apply properly
                self._timekprUserData[cons.TK_CTRL_SPENTM] = timeSpent

        # check if we need to save progress
        if (self._effectiveDatetime - self._timekprUserData[cons.TK_CTRL_LSAVE]).total_seconds() >= pTimekprSaveInterval or lastCheckDOW != self._currentDOW:
            # save
            self.saveSpent()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish adjustTimeSpentActual")

        # returns if user is isUserActive
        return isUserActive

    def getTimeLeft(self, pForce=False):
        """Get how much time is left (for this day and in a row for max this and next day)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start getTimeLeft")
        # time left in a row
        timeLeftToday = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFTD]
        # time left in a row
        timeLeftInARow = self._timekprUserData[cons.TK_CTRL_LEFT]
        # time spent this session
        timeSpentThisSession = 0
        # time inactive this session
        timeInactiveThisSession = 0

        # go through days
        for i in [self._timekprUserData[self._currentDOW][cons.TK_CTRL_PDAY], self._currentDOW, self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]]:
            # sleep is counted for hours, spent is day and hours
            # go through hours for this day
            for j in range(0, 23+1):
                # time spent this session (but not more then prev, current, past days)
                timeSpentThisSession += self._timekprUserData[i][str(j)][cons.TK_CTRL_SPENTH]
                # time inactive this session (but not more then prev, current, past days)
                timeInactiveThisSession += self._timekprUserData[i][str(j)][cons.TK_CTRL_SLEEP]

        # time spent for week
        timeSpentWeek = self._timekprUserData[cons.TK_CTRL_SPENTW]
        # time spent for week
        timeSpentMonth = self._timekprUserData[cons.TK_CTRL_SPENTM]

        # debug
        log.log(cons.TK_LOG_LEVEL_DEBUG, "user: %s, timeLeftToday: %s, timeLeftInARow: %s, timeSpentThisBoot: %s, timeInactiveThisBoot: %s" % (self._timekprUserData[cons.TK_CTRL_UNAME], timeLeftToday, timeLeftInARow, timeSpentThisSession, timeInactiveThisSession))

        # process notifications, if needed
        self._timekprUserNotification.processTimeLeft(pForce, timeSpentThisSession, timeSpentWeek, timeSpentMonth, timeInactiveThisSession, timeLeftToday, timeLeftInARow, self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMITD], self._timekprUserConfig.getUserTrackInactive())

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish getTimeLeft")

        # return calculated
        return timeLeftToday, timeLeftInARow, timeSpentThisSession, timeInactiveThisSession

    def saveSpent(self):
        """Save the time spent by the user"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start saveSpent")

        # initial config loaded
        timekprConfigLoaded = False

        # check whether we need to reload file (if externally modified)
        if self._timekprUserData[cons.TK_CTRL_LCMOD] != self._timekprUserConfig.getUserLastModified():
            # load config
            self.adjustLimitsFromConfig(pSilent=False)
            # config loaded, we need to adjust time spent as well
            timekprConfigLoaded = True

        # check whether we need to reload file (if externally modified)
        if self._timekprUserData[cons.TK_CTRL_LMOD] != self._timekprUserControl.getUserLastModified() or timekprConfigLoaded:
            # load config
            self.adjustTimeSpentFromControl(pSilent=False)

        # adjust save time as well
        self._timekprUserData[cons.TK_CTRL_LSAVE] = self._effectiveDatetime

        # save spent time
        self._timekprUserControl.setUserTimeSpent(self._timekprUserData[self._currentDOW][cons.TK_CTRL_SPENTD])
        self._timekprUserControl.setUserTimeSpentWeek(self._timekprUserData[cons.TK_CTRL_SPENTW])
        self._timekprUserControl.setUserTimeSpentMonth(self._timekprUserData[cons.TK_CTRL_SPENTM])
        self._timekprUserControl.setUserLastChecked(self._effectiveDatetime)
        self._timekprUserControl.saveControl()
        # renew last modified
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserLastModified()

        # if debug
        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "save spent structure: %s" % (str(self._timekprUserData[self._currentDOW])))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish saveSpent")

    def getTimeLimits(self):
        """Calculate time limits for sendout to clients"""
        # main container
        timeLimits = {}

        # check allowed days
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()

        # traverse the config and get intervals
        for rDay in range(1, 7+1):
            # if day is ok, then check hours
            if rDay in allowedDays:
                # assign a time limit for the day
                timeLimits[str(rDay)] = {cons.TK_CTRL_LIMITD: self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMITD], cons.TK_CTRL_INT: list()}

                # init hours for intervals
                startHour = None
                endHour = None

                # loop through all days
                for rHour in range(0, 23+1):
                    # this is needed in case next hour starts with particular minutes, in which case continous interval ends
                    if startHour is not None and self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_SMIN] != 0:
                        timeLimits[str(rDay)][cons.TK_CTRL_INT].append([int(startHour), int(endHour)])
                        startHour = None

                    # if hour is enabled for use, we count the interval
                    if self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_ACT]:
                        # set start hour only if it has not beed set up, that is to start the interval
                        if startHour is None:
                            startHour = ((cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_SMIN])) - cons.TK_DATETIME_START).total_seconds()

                        # end
                        endHour = ((cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_EMIN])) - cons.TK_DATETIME_START).total_seconds()

                    # interval ends if hour is not allowed or this is the end of the day
                    if (not self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_ACT] and startHour is not None) or self._timekprUserData[str(rDay)][str(rHour)][cons.TK_CTRL_EMIN] != 60:
                        timeLimits[str(rDay)][cons.TK_CTRL_INT].append([int(startHour), int(endHour)])
                        startHour = None

                # after we processed intervals, let's check whether we closed all, if not do it
                if startHour is not None:
                    timeLimits[str(rDay)][cons.TK_CTRL_INT].append([int(startHour), int(endHour)])

        # weekly and monthly limits
        timeLimits[cons.TK_CTRL_LIMITW] = self._timekprUserData[cons.TK_CTRL_LIMITW]
        # weekly and monthly limits
        timeLimits[cons.TK_CTRL_LIMITM] = self._timekprUserData[cons.TK_CTRL_LIMITM]

        # debug
        if log.isDebug():
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
                    self._timekprUserData[cons.TK_CTRL_SCR_N] = True if pValue in ("True", "true", "1") else False
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
                log.log(cons.TK_LOG_LEVEL_INFO, "send re-validation request to user \"%s\"" % (self._timekprUserData[cons.TK_CTRL_UNAME]))
                # send verification request
                self.processUserSessionAttributes(cons.TK_CTRL_SCR_N, "", None)

            # reset retries
            self._timekprUserData[cons.TK_CTRL_SCR_R] = 0

    def getUserPathOnBus(self):
        """Return user DBUS path"""
        return self._timekprUserData[cons.TK_CTRL_UPATH]

    def isUserActive(self, pSessionTypes):
        """Whether user is active"""
        # check sessions (adding user attributes as well (screenclocked))
        return self._timekprUserManager.isUserActive(pSessionTypes, self._timekprUserConfig.getUserTrackInactive(), self._timekprUserData[cons.TK_CTRL_SCR_N])

    def processFinalWarning(self):
        """Process emergency message about killing"""
        self._timekprUserNotification.processEmergencyNotification(max(self._finalCountdown, 0))
