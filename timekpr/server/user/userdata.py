"""
Created on Aug 28, 2018

@author: mjasnik
"""

# import section
from datetime import datetime, timedelta

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

    def deInitUser(self):
        # deinit
        self._timekprUserNotification.deInitUser()

    def adjustLimitsFromConfig(self, pSilent=True):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustLimitsFromConfig")

        # init config
        self._timekprUserConfig.loadConfiguration()

        # load the configuration into working structures
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()
        limitsPerWeekday = self._timekprUserConfig.getUserLimitsPerWeekdays()
        # there might be less than 7 days allowed, so we care about exising days only
        limitLen = len(limitsPerWeekday)

        # for allowed weekdays
        for rDay in range(1, 7+1):
            # set up limits
            self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMIT] = float(limitsPerWeekday[rDay-1]) if limitLen >= rDay else 0
            # only if not initialized
            if self._timekprUserData[str(rDay)][cons.TK_CTRL_LEFT] < 0:
                # initialize left as limit, since we just loaded the configuration
                self._timekprUserData[str(rDay)][cons.TK_CTRL_LEFT] = self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMIT]

            # get hours for particular day
            allowedHours = self._timekprUserConfig.getUserAllowedHours(rDay)

            # check if it is enabled as per config
            if str(rDay) in allowedDays:
                dayAllowed = True
            else:
                dayAllowed = False

            # loop through all days
            for rHour in range(0, 23+1):
                # if day is disabled, it does not matter whether hour is
                if not dayAllowed:
                    hourAllowed = False
                # if hour is allowed
                elif str(rHour) in allowedHours:
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

    def adjustTimeSpentExplicit(self, pSilent=True):
        """Adjust limits as per loaded configuration"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustTimeSpentExplicit")

        # read from config
        self._timekprUserControl.loadControl()

        # import that into runtime config (if last check day is the same as current)
        self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMIT] - (self._timekprUserControl.getUserTimeSpent() if self._timekprUserControl.getUserLastChecked().date() == self._effectiveDatetime.date() else 0)

        # update last file mod time
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserLastModified()

        # inform user about change
        if not pSilent:
            # inform
            self._timekprUserNotification.timeLeftChangedNotification(cons.TK_PRIO_IMPORTANT_INFO)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish adjustTimeSpentExplicit")

    def adjustTimeSpentActual(self, pSessionTypes, pSessionTypesExcl, pTimekprSaveInterval):
        """Adjust time spent (and save it)"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start adjustTimeSpentActual")

        # get last checked DOW
        lastCheckDOW = str(datetime.date(self._timekprUserData[cons.TK_CTRL_LCHECK]).isoweekday())
        # get time spent
        timeSpent = (self._effectiveDatetime - self._timekprUserData[cons.TK_CTRL_LCHECK]).total_seconds()

        # if time spent is very much higher than the default polling time, computer might went to sleep?
        if timeSpent >= cons.TK_POLLTIME * 15:
            timeSpent = 0

        # determine if active
        isUserActive = self.isUserActive(pSessionTypes)

        # get time spent for this hour (if hour passed in between checks, we need to properly adjust this hour)
        # adjust previous hour (not that we need it)
        if timeSpent > self._secondsInHour and self._currentHOD != 0:
            self._timekprUserData[self._currentDOW][str(self._currentHOD-1)][cons.TK_CTRL_SPENT] += timeSpent - self._secondsInHour

        # adjust time spent for this hour
        timeSpent = min(timeSpent, self._secondsInHour)

        # how long user has been sleeping
        if not isUserActive:
            # track sleep time
            self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SLEEP] += timeSpent

        # adjust time spent only if user is active
        if isUserActive:
            # decrease the limit
            # self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] = min(self._secondsLeftDay, max(self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] - timeSpent, 0))
            self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] = max(self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] - timeSpent, 0)
            # adjust time spent
            self._timekprUserData[self._currentDOW][str(self._currentHOD)][cons.TK_CTRL_SPENT] += timeSpent

        # adjust last time checked
        self._timekprUserData[cons.TK_CTRL_LCHECK] = self._effectiveDatetime

        # if there is a day change, we need to adjust time for this day and day after
        if lastCheckDOW != self._currentDOW:
            # set previous day (that is - it was previous day couple of seconds ago) as not initialized
            self._timekprUserData[lastCheckDOW][cons.TK_CTRL_LEFT] = -1
            # set limit as not initialized for today, so new limits will apply properly
            self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT] = -1
            # load limits starting from today
            self.adjustLimitsFromConfig()
            # adjust time spent from control file
            self.adjustTimeSpentExplicit()

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

        # default
        timeLeftHour = 0
        timeLeftToday = 0
        timeLeftInARow = 0
        timeLeftInARowCalculated = False
        timeLeft2days = 0
        timeSpentThisBoot = 0
        timeInactiveThisBoot = 0

        # defaults
        currentHOD = self._currentHOD

        # go through days
        for i in [self._currentDOW, self._timekprUserData[self._currentDOW][cons.TK_CTRL_NDAY]]:
            # how many seconds left for that day
            secondsLeft = self._timekprUserData[i][cons.TK_CTRL_LEFT]

            # go through hours for this day
            for j in range(0, 23+1):
                # count inactive time
                timeInactiveThisBoot += self._timekprUserData[i][str(j)][cons.TK_CTRL_SLEEP]
                timeSpentThisBoot += self._timekprUserData[i][str(j)][cons.TK_CTRL_SPENT]

                # starting this hour we need to calculate a lot of stuff
                if j >= currentHOD or self._currentDOW != i:
                    # determine current hod
                    if self._currentDOW == i and self._currentHOD == j:
                        # enable current values
                        currentHOD = self._currentHOD
                        currentMOH = self._currentMOH
                        currentSOM = self._effectiveDatetime.second
                        secondsLeftHour = self._secondsLeftHour
                    else:
                        # enable defaults which represents start of hour
                        currentHOD = 0
                        currentMOH = 0
                        currentSOM = 0
                        secondsLeftHour = 3600

                    # calculate seconds to add
                    secondsToAdd = 0

                    # calculate only if hour is enabled
                    if self._timekprUserData[i][str(j)][cons.TK_CTRL_ACT]:
                        # if we are in the right minute, we need to set up correct seconds
                        if not self._timekprUserData[i][str(j)][cons.TK_CTRL_SMIN] <= currentMOH <= self._timekprUserData[i][str(j)][cons.TK_CTRL_EMIN]:
                            # if we are not in the right minute, there is a break in countinous interval
                            timeLeftInARowCalculated = True

                        # calculate how many seconds are actually left taking account minutes configuration
                        secondsLeftHourLimit = max((self._timekprUserData[i][str(j)][cons.TK_CTRL_EMIN] - max(self._timekprUserData[i][str(j)][cons.TK_CTRL_SMIN], currentMOH)) * 60 - currentSOM, 0)

                        # calculate seconds to add
                        secondsToAdd = min(secondsLeftHour, secondsLeftHourLimit, secondsLeft)

                        # debug
                        if j >= currentHOD:
                            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "per-day variables: %s, %i, %i, %i, %i, %i" % (i, j, secondsLeftHour, secondsLeftHourLimit, secondsLeft, currentSOM))

                        # if this is today
                        if self._currentDOW == i:
                            # time left today
                            timeLeftToday += secondsToAdd
                            # and current hour
                            if currentHOD == j:
                                # time left today
                                timeLeftHour += secondsToAdd

                        # calculate continous interval
                        if timeLeftInARowCalculated is not True:
                            # add in a row
                            timeLeftInARow += secondsToAdd

                        # decrease the limit
                        secondsLeft -= secondsToAdd

                        # this is the case when we have no more time left this hour, but there are still time left in a day or we do not have continous interval
                        if (secondsLeft <= 0 and self._secondsLeftDay > timeLeftInARow) or self._timekprUserData[i][str(j)][cons.TK_CTRL_EMIN] < 60:
                            # continoues interval breaks
                            timeLeftInARowCalculated = True
                    else:
                        # continoues interval breaks
                        timeLeftInARowCalculated = True

                    # for 2 days
                    timeLeft2days += secondsToAdd

        # debug
        log.log(cons.TK_LOG_LEVEL_DEBUG, "user: %s, timeLeftToday: %s, timeLeftInARow: %s, timeSpentThisBoot: %s, timeInactiveThisBoot: %s" % (self._timekprUserData[cons.TK_CTRL_UNAME], timeLeftToday, timeLeftInARow, timeSpentThisBoot, timeInactiveThisBoot))
        log.log(cons.TK_LOG_LEVEL_DEBUG, "timeLeftHour: %s, timeLeft2days: %s" % (timeLeftHour, timeLeft2days))

        # process notifications, if needed
        self._timekprUserNotification.processTimeLeft(pForce, timeSpentThisBoot, timeInactiveThisBoot, timeLeftToday, timeLeftInARow, self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMIT], self._timekprUserConfig.getUserTrackInactive())

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish getTimeLeft")

        # return calculated
        return timeLeftHour, timeLeftToday, timeLeftInARow, timeLeft2days, timeSpentThisBoot, timeInactiveThisBoot

    def getTimeLimits(self):
        """Calculate time limits for sendout to clients"""
        # main container
        timeLimits = {}

        # check allowed days
        allowedDays = self._timekprUserConfig.getUserAllowedWeekdays()

        # traverse the config and get intervals
        for rDay in range(1, 7+1):
            # if day is ok, then check hours
            if str(rDay) in allowedDays:
                # assign a time limit for the day
                timeLimits[str(rDay)] = {cons.TK_CTRL_LIMIT: self._timekprUserData[str(rDay)][cons.TK_CTRL_LIMIT], cons.TK_CTRL_INT: list()}

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

        # debug
        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "TL: %s" % (str(timeLimits)))

        # process notifications, if needed
        self._timekprUserNotification.processTimeLimits(timeLimits)

    def initUserLimits(self):
        """Initialize default limits for the user"""
        # the config works as follows:
        #    we have cons.LIMIT, this limit is either time allowed per day or if that is not used, all seconds in allowed hours
        #    in hour section (0 is the sample in config), we have whether one is allowed to work in particular hour and then we have time spent (which can be paused as well)
        #    the rest must be easy

        # define structure for limits
        # day: next day | limit | left per day + hours 0 - 23 (0 hour sample included)
        limits = {
             "1"                 : {cons.TK_CTRL_NDAY: "2", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"2"                 : {cons.TK_CTRL_NDAY: "3", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"3"                 : {cons.TK_CTRL_NDAY: "4", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"4"                 : {cons.TK_CTRL_NDAY: "5", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"5"                 : {cons.TK_CTRL_NDAY: "6", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"6"                 : {cons.TK_CTRL_NDAY: "7", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,"7"                 : {cons.TK_CTRL_NDAY: "1", cons.TK_CTRL_LIMIT: -1, cons.TK_CTRL_LEFT: -1, "0": {cons.TK_CTRL_ACT: True, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}}
            ,cons.TK_CTRL_LWK    : 0  # this is limit per week (not used yet)
            ,cons.TK_CTRL_LMON   : 0  # this is limit per month (not used yet)
            ,cons.TK_CTRL_LCHECK : datetime.now().replace(microsecond=0)  # this is last checked time
            ,cons.TK_CTRL_LSAVE  : datetime.now().replace(microsecond=0)  # this is last save time (physical save will be less often as check)
            ,cons.TK_CTRL_LMOD   : datetime.now().replace(microsecond=0)  # this is last control save time
            ,cons.TK_CTRL_LCMOD  : datetime.now().replace(microsecond=0)  # this is last config save time
            ,cons.TK_CTRL_UID    : -1  # user id (not used, but still saved)
            ,cons.TK_CTRL_UNAME  : ""  # user name, this is the one we need
            ,cons.TK_CTRL_UPATH  : ""  # this is for DBUS communication purposes
        }

        # fill up every hour
        # loop through days
        for i in range(1, 7+1):
            # loop through hours
            for j in range(0, 23+1):
                # initial limit is whole hour
                limits[str(i)][str(j)] = {cons.TK_CTRL_ACT: False, cons.TK_CTRL_SPENT: 0, cons.TK_CTRL_SLEEP: 0, cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # return limits
        return limits

    def getUserPathOnBus(self):
        """Return user DBUS path"""
        return self._timekprUserData[cons.TK_CTRL_UPATH]

    def getUserName(self):
        """Return user name"""
        return self._timekprUserData[cons.TK_CTRL_UNAME]

    def getTrackInactive(self):
        """Return whether track inactive sessions for this user"""
        return self._timekprUserConfig.getUserTrackInactive()

    def isUserActive(self, pSessionTypes):
        """Whether user is active"""
        return self._timekprUserManager.isUserActive(pSessionTypes, self.getTrackInactive())

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
            self.adjustTimeSpentExplicit(pSilent=False)

        # spent
        timeSpent = self._timekprUserData[self._currentDOW][cons.TK_CTRL_LIMIT] - self._timekprUserData[self._currentDOW][cons.TK_CTRL_LEFT]

        # adjust save time as well
        self._timekprUserData[cons.TK_CTRL_LSAVE] = self._effectiveDatetime

        # save spent time
        self._timekprUserControl.setUserTimeSpent(timeSpent)
        self._timekprUserControl.setUserLastChecked(self._effectiveDatetime)
        self._timekprUserControl.saveControl()
        # renew last modified
        self._timekprUserData[cons.TK_CTRL_LMOD] = self._timekprUserControl.getUserLastModified()

        # if debug
        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "save spent structure: %s" % (str(self._timekprUserData[self._currentDOW])))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish saveSpent")

    def processFinalWarning(self):
        """Process emergency message about killing"""
        self._timekprUserNotification.processEmergencyNotification(max(self._finalCountdown, 0))
