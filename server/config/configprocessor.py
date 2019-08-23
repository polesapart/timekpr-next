"""
Created on Jan 17, 2019

@author: mjasnik
"""

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl
from timekpr.common.utils.config import timekprConfig
from timekpr.common.constants import messages as msg

# imports
from datetime import datetime
import dbus


class timekprUserConfigurationProcessor(object):
    """Validate and update configuration data for timekpr user"""

    def __init__(self, pLog, pUserName, pConfigDir, pWorkDir):
        """Initialize all stuff for user"""
        # set up initial variables
        self._logging = pLog
        self._configDir = pConfigDir
        self._workDir = pWorkDir
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
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USERCONFIG_NOTFOUND") % (self._userName)

        # result
        return result, message

    def loadAndCheckUserControl(self):
        """Load the user control saved state (to verify whether user control exists and is readable)"""
        # result
        result = 0
        message = ""

        # user config
        self._timekprUserControl = timekprUserControl(self._logging, self._workDir, self._userName)

        # result
        if not self._timekprUserControl.loadControl(True):
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USERCONTROL_NOTFOUND") % (self._userName)

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
                    allowedHours = self._timekprUserConfig.getUserAllowedHours(str(i))
                    userConfigurationStore["%s_%s" % (param, str(i))] = allowedHours if len(allowedHours) > 0 else dbus.Dictionary(signature="sv")
                # allowed week days
                allowedWeekDays = self._timekprUserConfig.getUserAllowedWeekdays()
                userConfigurationStore["ALLOWED_WEEKDAYS"] = list(map(dbus.Int32, allowedWeekDays)) if len(allowedWeekDays) > 0 else dbus.Array(signature="i")
                # limits per week days
                allowedWeekDayLimits = self._timekprUserConfig.getUserLimitsPerWeekdays()
                userConfigurationStore["LIMITS_PER_WEEKDAYS"] = list(map(dbus.Int32, allowedWeekDayLimits)) if len(allowedWeekDayLimits) > 0 else dbus.Array(signature="i")
                # track inactive
                userConfigurationStore["TRACK_INACTIVE"] = self._timekprUserConfig.getUserTrackInactive()
                # limit per week
                userConfigurationStore["LIMIT_PER_WEEK"] = self._timekprUserConfig.getUserWeekLimit()
                # limit per month
                userConfigurationStore["LIMIT_PER_MONTH"] = self._timekprUserConfig.getUserMonthLimit()
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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAYLIST_NONE") % (self._userName)
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
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAYLIST_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserAllowedWeekdays(days)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAYLIST_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_DAY_NONE") % (self._userName)
        # if days are crazy
        elif pDayNumber != "ALL" and not 1 <= int(pDayNumber) <= 7:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_DAY_INVALID") % (self._userName)
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

            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_NONE") % (self._userName)
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
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserLimitsPerWeekdays(limits)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_NONE") % (self._userName)
        else:
            # parse config
            try:
                if pTrackInactive:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserTrackInactive(pTrackInactive)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_NONE") % (self._userName)
        else:
            # parse config
            try:
                # verification
                weekLimit = max(min(int(pTimeLimitWeek), cons.TK_LIMIT_PER_WEEK), 0)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserWeekLimit(weekLimit)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_NONE") % (self._userName)
        else:
            # parse config
            try:
                # verification
                monthLimit = max(min(int(pTimeLimitMonth), cons.TK_LIMIT_PER_MONTH), 0)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserMonthLimit(monthLimit)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_INVALID_SET") % (self._userName)

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
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TIMELIMIT_OPERATION_INVALID") % (self._userName)
        else:
            # parse config
            try:
                if int(pTimeLeft) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TIMELIMIT_INVALID") % (self._userName)

            # if all is correct, we update the configuration
            if result == 0:
                # defaults
                setLimit = 0

                try:
                    # decode time left (operations are actually technicall reversed, + for ppl is please add more time and minus is subtract,
                    #   but actually it's reverse, because we are dealing with time spent not time left)
                    if pOperation == "+":
                        setLimit = min(max(self._timekprUserControl.getUserTimeSpent() - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "-":
                        setLimit = min(max(self._timekprUserControl.getUserTimeSpent() + pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "=":
                        setLimit = min(max(self._timekprUserConfig.getUserLimitsPerWeekdays()[datetime.date(datetime.now()).isoweekday()-1] - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)

                    # set up config for day
                    self._timekprUserControl.setUserTimeSpent(setLimit)
                except Exception:
                    # result
                    result = -1
                    message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_TIMELIMIT_INVALID_SET") % (self._userName)

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

    def loadTimekprConfiguration(self):
        """Load timekpr config"""
        # configuration load
        self._configLoaded = self._timekprConfig.loadMainConfiguration()
        # if fail
        if not self._configLoaded:
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_ERROR_GENERIC")
        else:
            result = 0
            message = ""

        # result
        return result, message

    def getSavedTimekprConfiguration(self):
        """Get saved user configuration"""
        """This operates on saved user configuration, it will return all config as big dict"""
        # initialize username storage
        timekprConfigurationStore = {}

        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        else:
            # ## load config ##
            # log level
            timekprConfigurationStore["TIMEKPR_LOGLEVEL"] = self._timekprConfig.getTimekprLogLevel()
            # poll time
            timekprConfigurationStore["TIMEKPR_POLLTIME"] = self._timekprConfig.getTimekprPollTime()
            # save time
            timekprConfigurationStore["TIMEKPR_SAVE_TIME"] = self._timekprConfig.getTimekprSaveTime()
            # termination time
            timekprConfigurationStore["TIMEKPR_TERMINATION_TIME"] = self._timekprConfig.getTimekprTerminationTime()
            # final warning time
            timekprConfigurationStore["TIMEKPR_FINAL_WARNING_TIME"] = self._timekprConfig.getTimekprFinalWarningTime()
            # sessions to track
            timekprConfigurationStore["TIMEKPR_SESSION_TYPES_CTRL"] = self._timekprConfig.getTimekprSessionsCtrl()
            # sessions to exclude
            timekprConfigurationStore["TIMEKPR_SESSION_TYPES_EXCL"] = self._timekprConfig.getTimekprSessionsExcl()
            # users to exclude
            timekprConfigurationStore["TIMEKPR_USERS_EXCL"] = self._timekprConfig.getTimekprUsersExcl()

        # result
        return result, message, timekprConfigurationStore

    def checkAndSetTimekprLogLevel(self, pLogLevel):
        """Validate and set log level"""
        """ In case we have something to validate, we'll do it here"""

        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pLogLevel is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_LOGLEVEL_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pLogLevel) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_LOGLEVEL_INVALID") % (str(pLogLevel))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprLogLevel(pLogLevel)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_LOGLEVEL_INVALID_SET") % (str(pLogLevel))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprPollTime(self, pPollTimeSecs):
        """Validate and Set polltime for timekpr"""
        """ set in-memory polling time (this is the accounting precision of the time"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pPollTimeSecs is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_POLLTIME_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pPollTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_POLLTIME_INVALID") % (str(pPollTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprPollTime(pPollTimeSecs)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_POLLTIME_INVALID_SET") % (str(pPollTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSaveTime(self, pSaveTimeSecs):
        """Check and set save time for timekpr"""
        """Set the interval at which timekpr saves user data (time spent, etc.)"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pSaveTimeSecs is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_SAVETIME_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pSaveTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_SAVETIME_INVALID") % (str(pSaveTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSaveTime(pSaveTimeSecs)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_SAVETIME_INVALID_SET") % (str(pSaveTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprTrackInactive(self, pTrackInactive):
        """Check and set default value for tracking inactive sessions"""
        """Note that this is just the default value which is configurable at user level"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pTrackInactive is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_TRACKINACTIVE_NONE")
        else:
            # parse
            try:
                # try to convert
                if pTrackInactive:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_TRACKINACTIVE_INVALID") % (str(pTrackInactive))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprTrackInactive(pTrackInactive)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_TRACKINACTIVE_INVALID_SET") % (str(pTrackInactive))

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
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pTerminationTimeSecs is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_TERMTIME_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pTerminationTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_TERMTIME_INVALID") % (str(pTerminationTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprTerminationTime(pTerminationTimeSecs)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_TERMTIME_INVALID_SET") % (str(pTerminationTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Check and set up final warning time for users"""
        """ Final warning time is the countdown lenght (in seconds) for the user before he's thrown out"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pFinalWarningTimeSecs is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALWARNTIME_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pFinalWarningTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALWARNTIME_INVALID") % (str(pFinalWarningTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprFinalWarningTime(pFinalWarningTimeSecs)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALWARNTIME_INVALID_SET") % (str(pFinalWarningTimeSecs))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSessionsCtrl(self, pSessionsCtrl):
        """Check and set accountable session types for users"""
        """ Accountable sessions are sessions which are counted as active, there are handful of them, but predefined"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pSessionsCtrl is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_CTRLSESSIONS_NONE")
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
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID")

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSessionsCtrl(sessionsCtrl)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID_SET")

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprSessionsExcl(self, pSessionsExcl):
        """Check and set NON-accountable session types for users"""
        """ NON-accountable sessions are sessions which are explicitly ignored during session evaluation, there are handful of them, but predefined"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pSessionsExcl is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLSESSIONW_NONE")
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
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLSESSIONS_INVALID")

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprSessionsExcl(sessionsExcl)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLSESSIONS_INVALID_SET")

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
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pUsersExcl is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLUSERS_NONE")
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
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLUSERS_INVALID")

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprUsersExcl(usersExcl)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_EXCLUSERS_INVALID_SET")

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message
