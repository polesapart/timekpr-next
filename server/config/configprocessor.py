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

    def __init__(self, pUserName, pTimekprConfig):
        """Initialize all stuff for user"""
        # set up initial variables
        self._configDir = pTimekprConfig.getTimekprConfigDir()
        self._workDir = pTimekprConfig.getTimekprWorkDir()
        self._userName = pUserName
        self._timekprUserConfig = None
        self._timekprUserControl = None

    def loadAndCheckUserConfiguration(self):
        """Load the user configuration (to verify whether user config exists and is readable)"""
        # result
        result = 0
        message = ""

        # user config
        self._timekprUserConfig = timekprUserConfig(self._configDir, self._userName)

        # result
        if not self._timekprUserConfig.loadUserConfiguration(True):
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
        self._timekprUserControl = timekprUserControl(self._workDir, self._userName)

        # result
        if not self._timekprUserControl.loadUserControl(True):
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_CONFIG_LOADER_USERCONTROL_NOTFOUND") % (self._userName)

        # result
        return result, message

    def calculateAdjustedDatesForUserControl(self, pCheckDate):
        """Calculate and save proper dates in control file, in case they wastly differ from what as saved"""
        # control date components changed
        dayChanged, weekChanged, monthChanged = self._timekprUserControl.getUserDateComponentChanges(pCheckDate)

        # set defaults in case day changed
        if dayChanged:
            # balance and day must be changed
            self._timekprUserControl.setUserTimeSpentDay(0)
            self._timekprUserControl.setUserTimeSpentBalance(0)
        # set defaults in case week changed
        if weekChanged:
            # balance and day must be changed
            self._timekprUserControl.setUserTimeSpentWeek(0)
        # set defaults in case month changed
        if monthChanged:
            # balance and day must be changed
            self._timekprUserControl.setUserTimeSpentMonth(0)

        # save user control file if dates changed
        if dayChanged or weekChanged or monthChanged:
            # last check date
            self._timekprUserControl.setUserLastChecked(pCheckDate)
            # save
            self._timekprUserControl.saveControl()

    def calculateTimeAvailableFromSavedConfiguration(self):
        """Calculate available time for today from saved config"""
        # current day
        currDay = str(datetime.now().isoweekday())
        # get available hours for today
        allowedHours = self._timekprUserConfig.getUserAllowedHours(currDay)
        # allowed week days
        allowedWeekDays = self._timekprUserConfig.getUserAllowedWeekdays()
        # limits per week days
        allowedWeekDayLimits = self._timekprUserConfig.getUserLimitsPerWeekdays()
        # time now
        dtn = datetime.now().replace(microsecond=0)
        #### normalize days
        # get max of days / limits
        limitLen = min(len(allowedWeekDays), len(allowedWeekDayLimits))
        # remove excess elements
        for i in range(limitLen, len(allowedWeekDays)):
            allowedWeekDays.pop()
        # remove excess elements
        for i in range(limitLen, len(allowedWeekDayLimits)):
            allowedWeekDayLimits.pop()

        # calc
        availableSeconds = 0
        availableSecondsAlt = 0
        # count available seconds for intervals starting this hour
        for rHour in range(dtn.hour, 24):
            # calc from now
            if str(rHour) in allowedHours:
                # for current hour we have to take care of time in progress at the moment
                if rHour == dtn.hour:
                    availableSeconds += max((max(allowedHours[str(rHour)][cons.TK_CTRL_EMIN], dtn.minute) - max(allowedHours[str(rHour)][cons.TK_CTRL_SMIN], dtn.minute)) * 60 - dtn.second, 0)
                # for the rest of hours, current secs and mins are not important
                else:
                    availableSeconds += ((allowedHours[str(rHour)][cons.TK_CTRL_EMIN] - allowedHours[str(rHour)][cons.TK_CTRL_SMIN]) * 60)
        # calculate available seconds from todays limit
        if currDay in allowedWeekDays:
            availableSecondsAlt = allowedWeekDayLimits[allowedWeekDays.index(currDay)]
        # calculate how much is actually left (from intervals left, time spent and available as well as max that's possible to have)
        availableSeconds = max(min(min(availableSeconds, availableSecondsAlt - self._timekprUserControl.getUserTimeSpentBalance()), cons.TK_LIMIT_PER_DAY), 0)

        # available seconds
        return availableSeconds

    def calculatePlayTimeAvailableFromSavedConfiguration(self):
        """Calculate available PlayTime for today from saved config"""
        # current day
        currDay = str(datetime.now().isoweekday())
        # calc
        availableSeconds = None
        # allowed week days
        allowedWeekDays = self._timekprUserConfig.getUserPlayTimeAllowedWeekdays()
        # only if we have PlayTime information
        if allowedWeekDays is not None:
            # calc
            availableSeconds = 0
            # limits per week days
            allowedWeekDayLimits = self._timekprUserConfig.getUserPlayTimeLimitsPerWeekdays()
            #### normalize days
            # get max of days / limits
            limitLen = min(len(allowedWeekDays), len(allowedWeekDayLimits))
            # remove excess elements
            for i in range(limitLen, len(allowedWeekDays)):
                allowedWeekDays.pop()
            # remove excess elements
            for i in range(limitLen, len(allowedWeekDayLimits)):
                allowedWeekDayLimits.pop()
            # calculate available seconds from todays limit
            if currDay in allowedWeekDays:
                availableSeconds = allowedWeekDayLimits[allowedWeekDays.index(currDay)]
            # calculate how much is actually left (from intervals left, time spent and avilable as well as max that's possible to have)
            availableSeconds = max(min(availableSeconds - self._timekprUserControl.getUserPlayTimeSpentBalance(), cons.TK_LIMIT_PER_DAY), 0)

        # available seconds
        return availableSeconds

    def getSavedUserInformation(self, pInfoLvl, pIsUserLoggedIn):
        """Get saved user configuration"""
        """This operates on saved user configuration, it will return all config as big dict"""
        # defaults
        result = 0
        message = ""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # initialize username storage
        userConfigurationStore = {}

        # if we are still fine
        if result != 0:
            # result
            pass
        # for full and saved info only
        else:
            # check if we have this user
            result, message = self.loadAndCheckUserControl()

            # if we are still fine
            if result != 0:
                # result
                pass
            else:
                # this goes for full information
                if pInfoLvl == cons.TK_CL_INF_FULL:
                    # allowed hours per weekdays
                    param = "ALLOWED_HOURS"
                    for rDay in cons.TK_ALLOWED_WEEKDAYS.split(";"):
                        # if there is a day
                        if rDay != "":
                            # fill up hours
                            allowedHours = self._timekprUserConfig.getUserAllowedHours(rDay)
                            userConfigurationStore["%s_%s" % (param, rDay)] = allowedHours if len(allowedHours) > 0 else dbus.Dictionary(signature="sv")
                    # allowed week days
                    allowedWeekDays = self._timekprUserConfig.getUserAllowedWeekdays()
                    userConfigurationStore["ALLOWED_WEEKDAYS"] = list(map(dbus.String, allowedWeekDays)) if len(allowedWeekDays) > 0 else dbus.Array(signature="s")
                    # limits per week days
                    allowedWeekDayLimits = self._timekprUserConfig.getUserLimitsPerWeekdays()
                    userConfigurationStore["LIMITS_PER_WEEKDAYS"] = list(map(dbus.Int32, allowedWeekDayLimits)) if len(allowedWeekDayLimits) > 0 else dbus.Array(signature="i")
                    # track inactive
                    userConfigurationStore["TRACK_INACTIVE"] = self._timekprUserConfig.getUserTrackInactive()
                    # hide icon
                    userConfigurationStore["HIDE_TRAY_ICON"] = self._timekprUserConfig.getUserHideTrayIcon()
                    # restriction / lockout type
                    userConfigurationStore["LOCKOUT_TYPE"] = self._timekprUserConfig.getUserLockoutType()
                    # add wake up intervals if type is wake
                    if userConfigurationStore["LOCKOUT_TYPE"] == cons.TK_CTRL_RES_W:
                        # wake up intervals
                        userConfigurationStore["WAKEUP_HOUR_INTERVAL"] = ";".join(self._timekprUserConfig.getUserWakeupHourInterval())
                    # limit per week
                    userConfigurationStore["LIMIT_PER_WEEK"] = self._timekprUserConfig.getUserWeekLimit()
                    # limit per month
                    userConfigurationStore["LIMIT_PER_MONTH"] = self._timekprUserConfig.getUserMonthLimit()
                    # ## PlayTime config (if enabled) ##
                    userConfigurationStore["PLAYTIME_ENABLED"] = self._timekprUserConfig.getUserPlayTimeEnabled()
                    # PlayTime override enabled
                    userConfigurationStore["PLAYTIME_LIMIT_OVERRIDE_ENABLED"] = self._timekprUserConfig.getUserPlayTimeOverrideEnabled()
                    # PlayTime allowed during unaccounted intervals
                    userConfigurationStore["PLAYTIME_UNACCOUNTED_INTERVALS_ENABLED"] = self._timekprUserConfig.getUserPlayTimeUnaccountedIntervalsEnabled()
                    # PlayTime allowed week days
                    allowedWeekDays = self._timekprUserConfig.getUserPlayTimeAllowedWeekdays()
                    userConfigurationStore["PLAYTIME_ALLOWED_WEEKDAYS"] = list(map(dbus.String, allowedWeekDays)) if len(allowedWeekDays) > 0 else dbus.Array(signature="s")
                    # PlayTime limits per week days
                    allowedWeekDayLimits = self._timekprUserConfig.getUserPlayTimeLimitsPerWeekdays()
                    userConfigurationStore["PLAYTIME_LIMITS_PER_WEEKDAYS"] = list(map(dbus.Int32, allowedWeekDayLimits)) if len(allowedWeekDayLimits) > 0 else dbus.Array(signature="i")
                    # PlayTime activities
                    playTimeActivities = self._timekprUserConfig.getUserPlayTimeActivities()
                    userConfigurationStore["PLAYTIME_ACTIVITIES"] = playTimeActivities if len(playTimeActivities) > 0 else dbus.Array(signature="aas")

                # this goes for full and saved info
                if pInfoLvl in (cons.TK_CL_INF_FULL, cons.TK_CL_INF_SAVED):
                    # before return results, we need to check whether user was active and dates did not change since then
                    # this makes sense only of user is NOT currently logged in
                    if not pIsUserLoggedIn:
                        # calculate
                        self.calculateAdjustedDatesForUserControl(datetime.now().replace(microsecond=0))
                    # get saved values
                    # time spent
                    userConfigurationStore["TIME_SPENT_BALANCE"] = self._timekprUserControl.getUserTimeSpentBalance()
                    # time spent
                    userConfigurationStore["TIME_SPENT_DAY"] = self._timekprUserControl.getUserTimeSpentDay()
                    # time spent
                    userConfigurationStore["TIME_SPENT_WEEK"] = self._timekprUserControl.getUserTimeSpentWeek()
                    # time spent
                    userConfigurationStore["TIME_SPENT_MONTH"] = self._timekprUserControl.getUserTimeSpentMonth()
                    # time available today
                    userConfigurationStore["TIME_LEFT_DAY"] = self.calculateTimeAvailableFromSavedConfiguration()
                    # PlayTime left
                    userConfigurationStore["PLAYTIME_LEFT_DAY"] = self.calculatePlayTimeAvailableFromSavedConfiguration()
                    # PlayTime spent
                    userConfigurationStore["PLAYTIME_SPENT_DAY"] = self._timekprUserControl.getUserPlayTimeSpentDay()

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
                    # empty
                    if str(rDay) != "":
                        # try to convert day
                        tmp = int(rDay)
                        # only if day is in proper interval
                        if rDay not in cons.TK_ALLOWED_WEEKDAYS:
                            tmp = 1/0
                        else:
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

        # pre-check day number
        isDayNumberValid = False
        # pre-check day number
        if pDayNumber is not None:
            # check
            for i in range(1, 7+1):
                if pDayNumber == str(i):
                    isDayNumberValid = True
                    break

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
        elif pDayNumber != "ALL" and not isDayNumberValid:
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
                    hourUnaccounted = pHourList[rHour][cons.TK_CTRL_UACC]

                    # get our dict done
                    dayLimits[dayNumber][rHour] = {cons.TK_CTRL_SMIN: minutesStart, cons.TK_CTRL_EMIN: minutesEnd, cons.TK_CTRL_UACC: hourUnaccounted}

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
                    # empty
                    if str(rLimit) != "":
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
        """Validate whether inactive user sessions are tracked
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
                if bool(pTrackInactive):
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

    def checkAndSetHideTrayIcon(self, pHideTrayIcon):
        """Validate and set hide tray icon for the user"""
        """Validate whether icon will be hidden from user
            true - icon and notifications are NOT shown to user
            false - icon and notifications are shown to user"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pHideTrayIcon is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_HIDETRAYICON_NONE") % (self._userName)
        else:
            # parse config
            try:
                if bool(pHideTrayIcon):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_HIDETRAYICON_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserHideTrayIcon(pHideTrayIcon)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_HIDETRAYICON_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetLockoutType(self, pLockoutType, pWakeFrom=None, pWakeTo=None):
        """Validate and set restriction / lockout type for the user"""
        """Validate the restricton / lockout type:
            lock - lock the screen
            suspend - suspend the computer
            suspendwake - suspend the computer
            terminate - terminate sessions (default)
            shutdown - shutdown computer"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pLockoutType is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_LOCKOUTTYPE_NONE") % (self._userName)
        # parse config
        elif pLockoutType not in (cons.TK_CTRL_RES_L, cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W, cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D) or not (pWakeFrom.isnumeric() if pWakeFrom is not None else True) or not (pWakeTo.isnumeric() if pWakeTo is not None else True):
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_LOCKOUTTYPE_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserLockoutType(pLockoutType)
                if pWakeFrom is not None and pWakeTo is not None:
                    self._timekprUserConfig.setUserWakeupHourInterval([pWakeFrom, pWakeTo])
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_LOCKOUTTYPE_INVALID_SET") % (self._userName)

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
        elif pOperation not in ("+", "-", "="):
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
                    # get actual time limit for this day
                    timeLimit = self._timekprUserConfig.getUserLimitsPerWeekdays()[datetime.date(datetime.now()).isoweekday()-1]
                    # decode time left (operations are actually technicall reversed, + for ppl is please add more time and minus is subtract,
                    #   but actually it's reverse, because we are dealing with time spent not time left)
                    if pOperation == "+":
                        setLimit = min(max(min(self._timekprUserControl.getUserTimeSpentBalance(), timeLimit) - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "-":
                        setLimit = min(max(min(self._timekprUserControl.getUserTimeSpentBalance(), timeLimit) + pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "=":
                        setLimit = min(max(timeLimit - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)

                    # set up config for day
                    self._timekprUserControl.setUserTimeSpentBalance(setLimit)
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

    # ## PlayTime methods ##

    def checkAndSetPlayTimeEnabled(self, pPlayTimeEnabled):
        """Validate and set whether PlayTime is available for the user"""
        """Validate whether PlayTime is available
            true - PlayTime enabled for the user
            false - PlayTime disabled for the user"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeEnabled is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ENABLE_FLAG_NONE") % (self._userName)
        else:
            # parse config
            try:
                if bool(pPlayTimeEnabled):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ENABLE_FLAG_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeEnabled(pPlayTimeEnabled)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ENABLE_FLAG_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeLimitOverride(self, pPlayTimeLimitOverride):
        """Validate and set whether PlayTime override is available for the user"""
        """Validate whether PlayTime override is available
            true - PlayTime override enabled for the user
            false - PlayTime override disabled for the user"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeLimitOverride is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_OVERRIDE_FLAG_NONE") % (self._userName)
        else:
            # parse config
            try:
                if bool(pPlayTimeLimitOverride):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_OVERRIDE_FLAG_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeOverrideEnabled(pPlayTimeLimitOverride)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_OVERRIDE_FLAG_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeUnaccountedIntervalsEnabled(self, pPlayTimeUnaccountedIntervalsEnabled):
        """Validate and set whether PlayTime is allowed during unaccounted intervals for the user"""
        """Validate whether PlayTime allowed during unaccounted intervals
            true - PlayTime allowed during unaccounted intervals enabled for the user
            false - PlayTime allowed during unaccounted intervals disabled for the user"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeUnaccountedIntervalsEnabled is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_UNACC_INT_FLAG_NONE") % (self._userName)
        else:
            # parse config
            try:
                if bool(pPlayTimeUnaccountedIntervalsEnabled):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_UNACC_INT_FLAG_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeUnaccountedIntervalsEnabled(pPlayTimeUnaccountedIntervalsEnabled)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_UNACC_INT_FLAG_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeAllowedDays(self, pPlayTimeAllowedDays):
        """Validate and set up allowed PlayTime days for the user"""
        """Validate allowed PlayTime days for the user
            server expects only the days that are allowed, sorted in ascending order"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeAllowedDays is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIST_NONE") % (self._userName)
        else:
            # days
            days = []

            # parse config
            try:
                for rDay in pPlayTimeAllowedDays:
                    # empty
                    if str(rDay) != "":
                        # try to convert day
                        tmp = int(rDay)
                        # only if day is in proper interval
                        if rDay not in cons.TK_ALLOWED_WEEKDAYS:
                            tmp = 1/0
                        else:
                            days.append(tmp)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIST_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeAllowedWeekdays(days)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIST_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeLimitsForDays(self, pPlayTimeLimits):
        """Validate and set up new PlayTime limits for each day for the user"""
        """Validate allowable PlayTime for the user
            server always expects 7 limits, for each day of the week, in the list"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeLimits is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIMITS_NONE") % (self._userName)
        else:
            # limits
            limits = []

            # parse config
            try:
                for rLimit in pPlayTimeLimits:
                    # empty
                    if str(rLimit) != "":
                        # try to convert seconds in day and normalize seconds in proper interval
                        limits.append(max(min(int(rLimit), cons.TK_LIMIT_PER_DAY), 0))
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIMITS_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeLimitsPerWeekdays(limits)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_DAYLIMITS_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeActivities(self, pPlayTimeActivities):
        """Validate and set up allowed PlayTime activities for the user"""
        """Validate allowed PlayTime activities for the user
            server expects array of array of masks/descriptions"""

        # check if we have this user
        result, message = self.loadAndCheckUserConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        # if we have no days
        elif pPlayTimeActivities is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ACTIVITIES_NONE") % (self._userName)
        else:
            # days
            activities = []

            # parse config
            try:
                for rAct in pPlayTimeActivities:
                    # set up act
                    act = (rAct[0], rAct[1])
                    # add to list
                    activities.append(act)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ACTIVITIES_INVALID") % (self._userName)

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprUserConfig.setUserPlayTimeAcitivityList(activities)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_ACTIVITIES_INVALID_SET") % (self._userName)

            # if we are still fine
            if result == 0:
                # save config
                self._timekprUserConfig.saveUserConfiguration()

        # result
        return result, message

    def checkAndSetPlayTimeLeft(self, pOperation, pTimeLeft):
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
        elif pOperation not in ("+", "-", "="):
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_TIMELIMIT_OPERATION_INVALID") % (self._userName)
        else:
            # parse config
            try:
                if int(pTimeLeft) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_TIMELIMIT_INVALID") % (self._userName)

            # if all is correct, we update the configuration
            if result == 0:
                # defaults
                setLimit = 0

                try:
                    # get actual time limit for this day
                    playTimeLimit = self._timekprUserConfig.getUserPlayTimeLimitsPerWeekdays()[datetime.date(datetime.now()).isoweekday()-1]
                    # decode time left (operations are actually technicall reversed, + for ppl is please add more time and minus is subtract,
                    #   but actually it's reverse, because we are dealing with time spent not time left)
                    if pOperation == "+":
                        setLimit = min(max(min(self._timekprUserControl.getUserPlayTimeSpentBalance(), playTimeLimit) - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "-":
                        setLimit = min(max(min(self._timekprUserControl.getUserPlayTimeSpentBalance(), playTimeLimit) + pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
                    elif pOperation == "=":
                        setLimit = min(max(playTimeLimit - pTimeLeft, -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)

                    # set up config for day
                    self._timekprUserControl.setUserPlayTimeSpentBalance(setLimit)
                except Exception:
                    # result
                    result = -1
                    message = msg.getTranslation("TK_MSG_USER_ADMIN_CHK_PT_TIMELIMIT_INVALID_SET") % (self._userName)

                # if we are still fine
                if result == 0:
                    # save config
                    self._timekprUserControl.saveControl()

        # result
        return result, message


class timekprConfigurationProcessor(object):
    """Validate and update configuration data for timekpr server"""

    def __init__(self):
        """Initialize all stuff for user"""
        # configuration init
        self._timekprConfig = timekprConfig()

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
            # final notification time
            timekprConfigurationStore["TIMEKPR_FINAL_NOTIFICATION_TIME"] = self._timekprConfig.getTimekprFinalNotificationTime()
            # sessions to track
            timekprConfigurationStore["TIMEKPR_SESSION_TYPES_CTRL"] = self._timekprConfig.getTimekprSessionsCtrl()
            # sessions to exclude
            timekprConfigurationStore["TIMEKPR_SESSION_TYPES_EXCL"] = self._timekprConfig.getTimekprSessionsExcl()
            # users to exclude
            timekprConfigurationStore["TIMEKPR_USERS_EXCL"] = self._timekprConfig.getTimekprUsersExcl()
            # PlayTime enabled
            timekprConfigurationStore["TIMEKPR_PLAYTIME_ENABLED"] = self._timekprConfig.getTimekprPlayTimeEnabled()
            # PlayTime enhanced activity monitor enabled
            timekprConfigurationStore["TIMEKPR_PLAYTIME_ENHANCED_ACTIVITY_MONITOR_ENABLED"] = self._timekprConfig.getTimekprPlayTimeEnhancedActivityMonitorEnabled()

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
                if bool(pTrackInactive):
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

    def checkAndSetTimekprFinalNotificationTime(self, pFinalNotificationTimeSecs):
        """Check and set up final notification time for users"""
        """ Final notification time is the time prior to ending sessions when final notification is sent out"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pFinalNotificationTimeSecs is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALNOTIFTIME_NONE")
        else:
            # parse
            try:
                # try to convert
                if int(pFinalNotificationTimeSecs) > 0:
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALNOTIFTIME_INVALID") % (str(pFinalNotificationTimeSecs))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprFinalNotificationTime(pFinalNotificationTimeSecs)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_FINALNOTIFTIME_INVALID_SET") % (str(pFinalNotificationTimeSecs))

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

    def checkAndSetTimekprPlayTimeEnabled(self, pPlayTimeEnabled):
        """Check and set the PlayTime global switch"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pPlayTimeEnabled is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIMEENABLED_NONE")
        else:
            # parse
            try:
                # try to convert
                if bool(pPlayTimeEnabled):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIMEENABLED_INVALID") % (str(pPlayTimeEnabled))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprPlayTimeEnabled(pPlayTimeEnabled)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIMEENABLED_INVALID_SET") % (str(pPlayTimeEnabled))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message

    def checkAndSetTimekprPlayTimeEnhancedActivityMonitorEnabled(self, pPlayTimeAdvancedSearchEnabled):
        """Check and set the PlayTime global enhanced activity monitor switch"""
        # load config
        result, message = self.loadTimekprConfiguration()

        # if we are still fine
        if result != 0:
            # result
            pass
        elif pPlayTimeAdvancedSearchEnabled is None:
            # result
            result = -1
            message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIME_ENH_ACT_MON_ENABLED_NONE")
        else:
            # parse
            try:
                # try to convert
                if bool(pPlayTimeAdvancedSearchEnabled):
                    pass
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIME_ENH_ACT_MON_ENABLED_INVALID") % (str(pPlayTimeAdvancedSearchEnabled))

        # if all is correct, we update the configuration
        if result == 0:
            # set up config
            try:
                self._timekprConfig.setTimekprPlayTimeEnhancedActivityMonitorEnabled(pPlayTimeAdvancedSearchEnabled)
            except Exception:
                # result
                result = -1
                message = msg.getTranslation("TK_MSG_ADMIN_CHK_PLAYTIME_ENH_ACT_MON_ENABLED_INVALID_SET") % (str(pPlayTimeAdvancedSearchEnabled))

            # if we are still fine
            if result == 0:
                # save config
                self._timekprConfig.saveTimekprConfiguration()

        # result
        return result, message
