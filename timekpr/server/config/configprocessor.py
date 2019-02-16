"""
Created on Jan 17, 2019

@author: mjasnik
"""

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl
from timekpr.common.utils.config import timekprConfig

# imports
from datetime import datetime


class timekprUserConfigurationProcessor(object):
    """Validate and update configuration data for timekpr user"""

    def __init__(self, pLog, pUserName, pConfigDir):
        """Initialize all stuff for user"""
        # set up initial variables
        self._logging = pLog
        self._configDir = pConfigDir
        self._userName = pUserName
        self._timekprUserConfig = None
        self._timekprUserControl = None

    def loadAndCheckUserConfiguration(self):
        """Load the user configuration (to verify whether user config exists and is readable)"""
        # result
        result = 0
        message = ""

        # user config
        self._timekprUserConfig = timekprUserConfig(self._logging, self._configDir, self._userName)

        # result
        if not self._timekprUserConfig.loadConfiguration(True):
            # result
            result = -1
            message = "User \"%s\" configuration is not found" % (self._userName)

        # result
        return result, message

    def loadAndCheckUserControl(self):
        """Load the user control saved state (to verify whether user control exists and is readable)"""
        # result
        result = 0
        message = ""

        # user config
        self._timekprUserControl = timekprUserControl(self._logging, self._configDir, self._userName)

        # result
        if not self._timekprUserControl.loadControl(True):
            # result
            result = -1
            message = "User \"%s\" configuration is not found" % (self._userName)

        # result
        return result, message

    def getSavedUserConfiguration(self):
        """Get saved user configuration"""
        """This operates on saved user configuration, it will return all config as big dict"""
        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # initialize username storage
        userConfigurationStore = {}

        # if we are still fine
        if result != 0:
            # result
            pass
        else:
            # check if we have this user
            result, message = self.loadAndCheckUserControl()

            # if we are still fine
            if result != 0:
                # result
                pass
            else:
                # allowed hours per weekdays
                param = "ALLOWED_HOURS"
                for i in range(1, 7+1):
                    userConfigurationStore["%s_%s" % (param, str(i))] = self._timekprUserConfig.getUserAllowedHours(str(i))
                # allowed week days
                userConfigurationStore["ALLOWED_WEEKDAYS"] = self._timekprUserConfig.getUserAllowedWeekdays()
                # limits per week days
                userConfigurationStore["LIMITS_PER_WEEKDAYS"] = self._timekprUserConfig.getUserLimitsPerWeekdays()
                # track inactive
                userConfigurationStore["TRACK_INACTIVE"] = self._timekprUserConfig.getUserTrackInactive()
                # time spent
                userConfigurationStore["TIME_SPENT"] = self._timekprUserControl.getUserTimeSpent()
                # time spent
                userConfigurationStore["TIME_SPENT_WEEK"] = self._timekprUserControl.getUserTimeSpentWeek()
                # time spent
                userConfigurationStore["TIME_SPENT_MONTH"] = self._timekprUserControl.getUserTimeSpentMonth()

        # result
        return result, message, userConfigurationStore

    def checkAndSetAllowedDays(self, pDayList):
        """Validate and set up allowed days for the user"""
        """Validate allowed days for the user
            server expects only the days that are allowed, sorted in ascending order"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pDayList is None:
            # result
            result = -1
            message = "User's \"%s\" day list is not passed" % (self._userName)
        else:
            # days
            days = []

            # parse config
            try:
                for rDay in pDayList:
                    # try to convert day
                    tmp = int(rDay)
                    # only if day is in proper interval
                    if 0 < tmp < 8:
                        days.append(tmp)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" day list is not correct" % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserAllowedWeekdays(days)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" day list is not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetAllowedHours(self, pDayNumber, pHourList):
        """Validate set up allowed hours for the user"""
        """Validate allowed hours for user for particular day
            server expects only the hours that are needed, hours must be sorted in ascending order
            please note that this is using 24h format, no AM/PM nonsense expected
            minutes can be specified in brackets after hour, like: 16[00-45], which means until 16:45"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pDayNumber is None:
            # result
            result = -1
            message = "User's \"%s\" day number must be present" % (self._userName)
        # if days are crazy
        elif pDayNumber != "ALL" and not 1 <= int(pDayNumber) <= 7:
            # result
            result = -1
            message = "User's \"%s\" day number must be between 1 and 7" % (self._userName)
        else:
            # parse config
            try:
                # check the days
                if pDayNumber != "ALL":
                    dayNumbers = []
                    dayNumber = str(pDayNumber)
                else:
                    dayNumbers = ["2", "3", "4", "5", "6", "7"]
                    dayNumber = "1"

                # create dict of specific day (maybe I'll support more days in a row at some point, though, I think it's a burden to users who'll use CLI)
                dayLimits = {dayNumber: {}}

                # minutes can be specified in brackets after hour
                for rHour in list(map(str, pHourList)):
                    # reset minuten
                    minutesStart = pHourList[rHour][cons.TK_CTRL_SMIN]
                    minutesEnd = pHourList[rHour][cons.TK_CTRL_EMIN]

                    # get our dict done
                    dayLimits[dayNumber][rHour] = {cons.TK_CTRL_SMIN: minutesStart, cons.TK_CTRL_EMIN: minutesEnd}

                # fill all days (if needed)
                for rDay in dayNumbers:
                    dayLimits[rDay] = dayLimits[dayNumber]

                # set up config
                # check and parse is happening in set procedure down there, so that's a validation and set in one call
                self._timekprUserConfig.setUserAllowedHours(dayLimits)

            except Exception as ex:
                print(str(ex))
                # result
                result = -1
                message = "User's \"%s\" allowed hours are not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetTimeLimitForDays(self, pDayLimits):
        """Validate and set up new timelimits for each day for the user"""
        """Validate allowable time to user
            server always expects 7 limits, for each day of the week, in the list"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pDayLimits is None:
            # result
            result = -1
            message = "User's \"%s\" day limits list is not passed" % (self._userName)
        else:
            # limits
            limits = []

            # parse config
            try:
                for rLimit in pDayLimits:
                    # try to convert seconds in day and normalize seconds in proper interval
                    limits.append(max(min(int(rLimit), cons.TK_LIMIT_PER_DAY), 0))
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" day limits list is not correct" % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserLimitsPerWeekdays(limits)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" day limits list is not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetTrackInactive(self, pTrackInactive):
        """Validate and set track inactive sessions for the user"""
        """Validate whehter inactive user sessions are tracked
            true - logged in user is always tracked (even if switched to console or locked or ...)
            false - user time is not tracked if he locks the session, session is switched to another user, etc."""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pTrackInactive is None:
            # result
            result = -1
            message = "User's \"%s\" track inactive flag is not passed" % (self._userName)
        else:
            # parse config
            try:
                if pTrackInactive:
                    pass
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" track inactive flag is not correct" % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserTrackInactive(pTrackInactive)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" track inactive flag is not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetTimeLimitForWeek(self, pTimeLimitWeek):
        """Validate and set up new timelimit for week for the user"""
        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pTimeLimitWeek is None:
            # result
            result = -1
            message = "User's \"%s\" weekly allowance is not passed" % (self._userName)
        else:
            # parse config
            try:
                if int(pTimeLimitWeek) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" weekly allowance is not correct" % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserWeekLimit(pTimeLimitWeek)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" weekly allowance is not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetTimeLimitForMonth(self, pTimeLimitMonth):
        """Validate and set up new timelimit for month for the user"""
        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pTimeLimitMonth is None:
            # result
            result = -1
            message = "User's \"%s\" monthly allowance is not passed" % (self._userName)
        else:
            # parse config
            try:
                if int(pTimeLimitMonth) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" monthly allowance is not correct" % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserMonthLimit(pTimeLimitMonth)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" monthly allowance is not correct and can not be set" % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetTimeLeft(self, pOperation, pTimeLeft):
        """Validate and set time left for today for the user"""
        """Validate time limits for user for this moment:
            if pOperation is "+" - more time left is addeed
            if pOperation is "-" time is subtracted
            if pOperation is "=" or empty, the time is set as it is"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result == 0:
            # check if we have this user
            result, message = self.loadAndCheckUserControl()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pOperation not in ["+", "-", "="]:
            # result
            result = -1
            message = "User's \"%s\" set time operation can be one of these: -+=" % (self._userName)
        else:
            # parse config
            try:
                if int(pTimeLeft) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" set time limit is not correct" % (self._userName)

            # if all is correct, we update the configuration
            if result == 0:
                # defaults
                setLimit = 0
                setLimitWeek = 0
                setLimitMonth = 0

                try:
                    # decode time left (operations are actually technicall reversed, + for ppl is please add more time and minus is subtract,
                    #   but actually it's reverse, because we are dealing with time spent not time left)
                    if pOperation == "+":
                        setLimit = min(max(self._timekprUserControl.getUserTimeSpent() - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                        # setLimitWeek = min(max(self._timekprUserControl.getUserTimeSpentWeek() - pTimeLeft, -cons.TK_LIMIT_PER_WEEK), cons.TK_LIMIT_PER_WEEK)
                        # setLimitMonth = min(max(self._timekprUserControl.getUserTimeSpentMonth() - pTimeLeft, -cons.TK_LIMIT_PER_MONTH), cons.TK_LIMIT_PER_MONTH)
                    elif pOperation == "-":
                        setLimit = min(max(self._timekprUserControl.getUserTimeSpent() + pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                        # setLimitWeek = min(max(self._timekprUserControl.getUserTimeSpentWeek() + pTimeLeft, -cons.TK_LIMIT_PER_WEEK), cons.TK_LIMIT_PER_WEEK)
                        # setLimitMonth = min(max(self._timekprUserControl.getUserTimeSpentMonth() + pTimeLeft, -cons.TK_LIMIT_PER_MONTH), cons.TK_LIMIT_PER_MONTH)
                    elif pOperation == "=":
                        setLimit = min(max(self._timekprUserConfig.getUserLimitsPerWeekdays()[datetime.date(datetime.now()).isoweekday()-1] - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)

                    # set up config for day
                    self._timekprUserControl.setUserTimeSpent(setLimit)
                    # set up config for week
                    self._timekprUserControl.setUserTimeSpentWeek(setLimitWeek)
                    # set up config for month
                    self._timekprUserControl.setUserTimeSpentMonth(setLimitMonth)
                except Exception:
                    # result
                    result = -1
                    message = "User's \"%s\" set time limit is not correct and can not be set" % (self._userName)

                # if we are still fine
                if result == 0:
                    # save config
                    self._timekprUserControl.saveControl()

        # result
        return result, message


class timekprConfigurationProcessor(object):
    """Validate and update configuration data for timekpr server"""

    def __init__(self, pLog, pIsDevActive):
        """Initialize all stuff for user"""
        # set up initial variables
        self._logging = pLog
        # configuration init
        self._timekprConfig = timekprConfig(pIsDevActive=pIsDevActive, pLog=self._logging)
        self._timekprConfig.loadMainConfiguration()

    def checkAndSetTimekprLogLevel(self, pLogLevel):
        """Validate and set log level"""
        """ In case we have something to validate, we'll do it here"""

        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pLogLevel is None:
            # result
            result = -1
            message = "Log level is not passed"
        else:
            # parse
            try:
                # try to convert
                if int(pLogLevel) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "Log level \"%s\"is not correct" % (str(pLogLevel))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprLogLevel(pLogLevel)
            except Exception:
                # result
                result = -1
                message = "Log level \"%s\" is not correct and can not be set" % (str(pLogLevel))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprPollTime(self, pPollTimeSecs):
        """Validate and Set polltime for timekpr"""
        """ set in-memory polling time (this is the accounting precision of the time"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pPollTimeSecs is None:
            # result
            result = -1
            message = "Poll time is not passed"
        else:
            # parse
            try:
                # try to convert
                if int(pPollTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "Poll time \"%s\"is not correct" % (str(pPollTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprPollTime(pPollTimeSecs)
            except Exception:
                # result
                result = -1
                message = "Poll time \"%s\" is not correct and can not be set" % (str(pPollTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSaveTime(self, pSaveTimeSecs):
        """Check and set save time for timekpr"""
        """Set the interval at which timekpr saves user data (time spent, etc.)"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pSaveTimeSecs is None:
            # result
            result = -1
            message = "Save time is not passed"
        else:
            # parse
            try:
                # try to convert
                if int(pSaveTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "Poll time \"%s\"is not correct" % (str(pSaveTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSaveTimeSecs(pSaveTimeSecs)
            except Exception:
                # result
                result = -1
                message = "Save time \"%s\" is not correct and can not be set" % (str(pSaveTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprTrackInactive(self, pTrackInactive):
        """Check and set default value for tracking inactive sessions"""
        """Note that this is just the default value which is configurable at user level"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pTrackInactive is None:
            # result
            result = -1
            message = "Track inactive is not passed"
        else:
            # parse
            try:
                # try to convert
                if pTrackInactive:
                    pass
            except Exception:
                # result
                result = -1
                message = "Track inactive \"%s\"is not correct" % (str(pTrackInactive))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprTrackInactive(pTrackInactive)
            except Exception:
                # result
                result = -1
                message = "Track inactive \"%s\" is not correct and can not be set" % (str(pTrackInactive))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprTerminationTime(self, pTerminationTimeSecs):
        """Check and set up user termination time"""
        """ User temination time is how many seconds user is allowed in before he's thrown out
            This setting applies to users who log in at inappropriate time according to user config
        """
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pTerminationTimeSecs is None:
            # result
            result = -1
            message = "Termination time is not passed"
        else:
            # parse
            try:
                # try to convert
                if int(pTerminationTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "Termination time \"%s\"is not correct" % (str(pTerminationTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprTerminationTime(pTerminationTimeSecs)
            except Exception:
                # result
                result = -1
                message = "Poll time \"%s\" is not correct and can not be set" % (str(pTerminationTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Check and set up final warning time for users"""
        """ Final warning time is the countdown lenght (in seconds) for the user before he's thrown out"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pFinalWarningTimeSecs is None:
            # result
            result = -1
            message = "Final warning time is not passed"
        else:
            # parse
            try:
                # try to convert
                if int(pFinalWarningTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = "Final warning time \"%s\"is not correct" % (str(pFinalWarningTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
            except Exception:
                # result
                result = -1
                message = "Final warning time \"%s\" is not correct and can not be set" % (str(pFinalWarningTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSessionsCtrl(self, pSessionsCtrl):
        """Check and set accountable session types for users"""
        """ Accountable sessions are sessions which are counted as active, there are handful of them, but predefined"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pSessionsCtrl is None:
            # result
            result = -1
            message = "Control sessions types are not passed"
        else:
            # limits
            sessionsCtrl = []

            # parse config
            try:
                for rSession in pSessionsCtrl:
                    # try to convert seconds in day and normalize seconds in proper interval
                    sessionsCtrl.append(rSession)
            except Exception:
                # result
                result = -1
                message = "Control sessions types list is not correct"

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSessionsCtrl(sessionsCtrl)
            except Exception:
                # result
                result = -1
                message = "Control sessions types list is not correct and can not be set"

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSessionsExcl(self, pSessionsExcl):
        """Check and set NON-accountable session types for users"""
        """ NON-accountable sessions are sessions which are explicitly ignored during session evaluation, there are handful of them, but predefined"""
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pSessionsExcl is None:
            # result
            result = -1
            message = "Excluded session types are not passed"
        else:
            # limits
            sessionsExcl = []

            # parse config
            try:
                for rSession in pSessionsExcl:
                    # try to convert seconds in day and normalize seconds in proper interval
                    sessionsExcl.append(rSession)
            except Exception:
                # result
                result = -1
                message = "Excluded session types list is not correct"

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSessionsExcl(sessionsExcl)
            except Exception:
                # result
                result = -1
                message = "Excluded session types list is not correct and can not be set"

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprUsersExcl(self, pUsersExcl):
        """Check and set excluded usernames for timekpr"""
        """ Excluded usernames are usernames which are excluded from accounting
            Pre-defined values containt all graphical login managers etc., please do NOT add actual end-users here,
            You can, but these users will never receive any notifications about time, icon will be in connecting state forever
        """
        # check if we have this user
        result, message = 0, ""

        # if we have no days
        if pUsersExcl is None:
            # result
            result = -1
            message = "Excluded user list is not passed"
        else:
            # limits
            usersExcl = []

            # parse config
            try:
                for rUser in pUsersExcl:
                    # try to convert seconds in day and normalize seconds in proper interval
                    usersExcl.append(rUser)
            except Exception:
                # result
                result = -1
                message = "Excluded user list is not correct"

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprUsersExcl(usersExcl)
            except Exception:
                # result
                result = -1
                message = "Excluded user list is not correct and can not be set"

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message
