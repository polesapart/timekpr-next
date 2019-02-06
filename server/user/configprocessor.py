"""
Created on Jan 17, 2019

@author: mjasnik
"""

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl


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
        elif not 0 <= pDayNumber <= 23:
            # result
            result = -1
            message = "User's \"%s\" day number must be between 0 and 23" % (self._userName)
        else:
            # parse config
            try:
                # create dict of specific day (maybe I'll support more days in a row at some point, though, I think it's a burden to users who'll use CLI)
                dayNumber = str(pDayNumber)
                dayLimits = {dayNumber: {}}

                # minutes can be specified in brackets after hour
                for rHour in list(map(str, pHourList)):
                    # reset minuten
                    minutesStart = 0
                    minutesEnd = 60

                    # if we have advanced config (minutes)
                    if "[" in rHour and "]" in rHour and "-" in rHour:
                        # get minutes
                        minutes = rHour.split("[", 1)[1].split("]")[0].split("-")

                        # calc and normalize minutes
                        minutesStart = min(max(int(minutes[0]), 0), 60)
                        minutesEnd = min(max(int(minutes[1]), 0), 60)

                    # get our dict done
                    dayLimits[dayNumber][rHour.split("[", 1)[0]] = {cons.TK_CTRL_SMIN: minutesStart, cons.TK_CTRL_EMIN: minutesEnd}

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
                    limits.append(max(min(int(rLimit), 0), 86400))
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
                tmp = bool(pTrackInactive)
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

    def checkAndSetTimeLeft(self, pOperation, pTimeLeft):
        """Validate and set time left for today for the user"""
        """Validate time limits for user for this moment:
            if pOperation is "+" - more time left is addeed
            if pOperation is "-" time is subtracted
            if pOperation is "=" or empty, the time is set as it is"""

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
                tmp = int(pTimeLeft)
            except Exception:
                # result
                result = -1
                message = "User's \"%s\" set time limit is not correct" % (self._userName)

            # if all is correct, we update the configuration
            if result == 0:
                # defaults
                setLimit = 0

                try:
                    # decode time left (operations are actually technicall reversed, + for ppl is please add more time and minus is subtract,
                    #   but actually it's reverse, because we are dealing with time spent not time left)
                    if pOperation == "+":
                        setLimit = self._timekprUserControl.getUserTimeSpent() - pTimeLeft
                    elif pOperation == "-":
                        setLimit = self._timekprUserControl.getUserTimeSpent() + pTimeLeft
                    elif pOperation == "=":
                        setLimit = pTimeLeft

                    # set up config
                    self._timekprUserControl.setUserTimeSpent(setLimit)
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
