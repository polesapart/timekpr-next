"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import configparser
from datetime import datetime
import fileinput
import re
import os
import getpass

# timekpr imports
from timekpr.common.log import log
from timekpr.common.constants import constants as cons


def saveConfigFile(pConfigFile, pKeyValuePairs):
    """Save the config file using custom helper function"""
    # edit control file (using alternate method because configparser looses comments in the process)
    with fileinput.FileInput(pConfigFile, inplace=True) as rControlFile:
        # read line and do manipulations
        for rLine in rControlFile:
            # check if we have proper line
            for rKey, rValue in pKeyValuePairs.items():
                # check if we have to use regexp
                if ("%s = " % (rKey)) in rLine:
                    # replace key = value pairs
                    line = re.sub(r"(?i)" + rKey + " *= .*$", rKey + " = " + rValue, rLine)
                    # first replacement is enough
                    break
                else:
                    # line does not need a replacement
                    line = rLine

            # save file line back to file
            print(line, end="")


class timekprConfig(object):
    """Main configuration class for the server"""

    def __init__(self, pIsDevActive=False, pLog=None):
        """Initialize stuff"""
        if pLog is not None:
            log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "initializing configuration manager")

        # config
        self._timekprConfig = {}
        self._isDevActive = pIsDevActive

        # in dev
        if self._isDevActive:
            self._configDirPrefix = os.getcwd()
        else:
            self._configDirPrefix = ""

        # main config
        self._timekprConfig["TIMEKPR_MAIN_CONFIG_DIR"] = os.path.join(self._configDirPrefix, (cons.TK_MAIN_CONFIG_DIR_DEV if self._isDevActive else cons.TK_MAIN_CONFIG_DIR))
        self._configFile = os.path.join(self._timekprConfig["TIMEKPR_MAIN_CONFIG_DIR"], cons.TK_MAIN_CONFIG_FILE)

        # config parser
        self._timekprConfigParser = configparser.ConfigParser(allow_no_value=True)
        self._timekprConfigParser.optionxform = str

        log.log(cons.TK_LOG_LEVEL_INFO, "finish configuration manager")

    def __del__(self):
        """De-initialize stuff"""
        log.log(cons.TK_LOG_LEVEL_INFO, "de-initializing configuration manager")

    def loadMainConfiguration(self):
        """Read main timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading configuration")

        # whether to use values from code
        useDefaults = False

        # check file
        if not os.path.isfile(self._configFile):
            # write correct config file
            self.saveDefaultConfiguration()

        # read config
        try:
            self._timekprConfigParser.read(self._configFile)
        except Exception:
            # we have a problem, will be using defaults
            useDefaults = True
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configFile))

        # general section
        section = "GENERAL"
        # read
        param = "TIMEKPR_VERSION"
        self._timekprConfig[param] = cons.TK_VERSION
        # read
        param = "TIMEKPR_LOGLEVEL"
        self._timekprConfig[param] = cons.TK_LOG_LEVEL_INFO if useDefaults else self._timekprConfigParser.getint(section, param)
        # read
        param = "TIMEKPR_POLLTIME"
        self._timekprConfig[param] = cons.TK_POLLTIME if useDefaults else self._timekprConfigParser.getint(section, param)
        # read
        param = "TIMEKPR_SAVE_TIME"
        self._timekprConfig[param] = cons.TK_SAVE_INTERVAL if useDefaults else self._timekprConfigParser.getint(section, param)
        # read
        param = "TIMEKPR_TRACK_INACTIVE"
        self._timekprConfig[param] = cons.TK_TRACK_INACTIVE if useDefaults else self._timekprConfigParser.getboolean(section, param)
        # read
        param = "TIMEKPR_TERMINATION_TIME"
        self._timekprConfig[param] = cons.TK_TERMINATION_TIME if useDefaults else self._timekprConfigParser.getint(section, param)
        # read
        param = "TIMEKPR_FINAL_WARNING_TIME"
        self._timekprConfig[param] = cons.TK_FINAL_COUNTDOWN_TIME if useDefaults else self._timekprConfigParser.getint(section, param)

        # session section
        section = "SESSION"
        # read
        param = "TIMEKPR_SESSION_TYPES_CTRL"
        self._timekprConfig[param] = cons.TK_SESSION_TYPES_CTRL if useDefaults else self._timekprConfigParser.get(section, param)
        # read
        param = "TIMEKPR_SESSION_TYPES_EXCL"
        self._timekprConfig[param] = cons.TK_SESSION_TYPES_EXCL if useDefaults else self._timekprConfigParser.get(section, param)
        # read
        param = "TIMEKPR_USERS_EXCL"
        self._timekprConfig[param] = cons.TK_USERS_EXCL if useDefaults else self._timekprConfigParser.get(section, param)

        # directory section
        section = "DIRECTORIES"
        # read
        param = "TIMEKPR_CONFIG_DIR"
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_CONFIG_DIR_DEV if self._isDevActive else (cons.TK_CONFIG_DIR if useDefaults else self._timekprConfigParser.get(section, param))))
        # read
        param = "TIMEKPR_WORK_DIR"
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_WORK_DIR_DEV if self._isDevActive else (cons.TK_WORK_DIR if useDefaults else self._timekprConfigParser.get(section, param))))
        # read
        param = "TIMEKPR_SHARED_DIR"
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if self._isDevActive else (cons.TK_SHARED_DIR if useDefaults else self._timekprConfigParser.get(section, param))))
        # read
        param = "TIMEKPR_LOGFILE_DIR"
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_LOGFILE_DIR_DEV if self._isDevActive else (cons.TK_LOGFILE_DIR if useDefaults else self._timekprConfigParser.get(section, param))))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading configuration")

        # result
        return True

    def saveDefaultConfiguration(self):
        """Save config file (if someone fucked up config file, we have to write new one)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start saving default configuration")

        # save default config
        section = "DOCUMENTATION"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this is the main configuration file for timekpr-next")
        self._timekprConfigParser.set(section, "#### if this file can not be read properly, it will be overwritten with defaults")

        section = "GENERAL"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### general configuration section")
        self._timekprConfigParser.set(section, "# this defines logging level of the timekpr (1 - normal, 2 - debug, 3 - extra debug)")
        self._timekprConfigParser.set(section, "TIMEKPR_LOGLEVEL", str(cons.TK_LOG_LEVEL_INFO))
        self._timekprConfigParser.set(section, "# this defines polling time (in memory) in seconds")
        self._timekprConfigParser.set(section, "TIMEKPR_POLLTIME", str(cons.TK_POLLTIME))
        self._timekprConfigParser.set(section, "# this defines a time for saving user time control file (polling and accounting is done in memory more often, but saving is not)")
        self._timekprConfigParser.set(section, "TIMEKPR_SAVE_TIME", str(cons.TK_SAVE_INTERVAL))
        self._timekprConfigParser.set(section, "# this defines whether to account sessions which are inactive (locked screen, user switched away from desktop, etc.), this defines the default value for new users")
        self._timekprConfigParser.set(section, "TIMEKPR_TRACK_INACTIVE", str(cons.TK_TRACK_INACTIVE))
        self._timekprConfigParser.set(section, "# this defines a time interval in seconds prior to assign user a termination sequence")
        self._timekprConfigParser.set(section, "#   15 seconds before time ends nothing can be done to avoid killing a session")
        self._timekprConfigParser.set(section, "#   this also is the time before initiating a termination sequence if user has logged in inappropriate time")
        self._timekprConfigParser.set(section, "TIMEKPR_TERMINATION_TIME", str(cons.TK_TERMINATION_TIME))
        self._timekprConfigParser.set(section, "# this defines a time interval when timekpr will send continous final warnings until the termination of user sessions")
        self._timekprConfigParser.set(section, "TIMEKPR_FINAL_WARNING_TIME", str(cons.TK_FINAL_COUNTDOWN_TIME))

        section = "SESSION"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this section contains configuration about sessions")
        self._timekprConfigParser.set(section, "# session types timekpr will track")
        self._timekprConfigParser.set(section, "TIMEKPR_SESSION_TYPES_CTRL", cons.TK_SESSION_TYPES_CTRL)
        self._timekprConfigParser.set(section, "# session types timekpr will ignore explicitly")
        self._timekprConfigParser.set(section, "TIMEKPR_SESSION_TYPES_EXCL", cons.TK_SESSION_TYPES_EXCL)
        self._timekprConfigParser.set(section, "# users timekpr will ignore explicitly")
        self._timekprConfigParser.set(section, "TIMEKPR_USERS_EXCL", cons.TK_USERS_EXCL)

        section = "DIRECTORIES"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this section contains directory configuration")
        self._timekprConfigParser.set(section, "# runtime directory for timekpr user configuration files")
        self._timekprConfigParser.set(section, "TIMEKPR_CONFIG_DIR", cons.TK_CONFIG_DIR)
        self._timekprConfigParser.set(section, "# runtime directory for timekpr time control files")
        self._timekprConfigParser.set(section, "TIMEKPR_WORK_DIR", cons.TK_WORK_DIR)
        self._timekprConfigParser.set(section, "# directory for shared files (images, gui definitions, etc.)")
        self._timekprConfigParser.set(section, "TIMEKPR_SHARED_DIR", cons.TK_SHARED_DIR)
        self._timekprConfigParser.set(section, "# directory for log files")
        self._timekprConfigParser.set(section, "TIMEKPR_LOGFILE_DIR", cons.TK_LOGFILE_DIR)

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprConfigParser.write(fp)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish saving default configuration")

    def saveTimekprConfiguration(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start saving timekpr configuration")

        # init dict
        values = {}

        # server loglevel
        values["TIMEKPR_LOGLEVEL"] = str(self._timekprConfig["TIMEKPR_LOGLEVEL"])
        # in-memory polling time
        values["TIMEKPR_POLLTIME"] = str(self._timekprConfig["TIMEKPR_POLLTIME"])
        # time interval to save user spent time
        values["TIMEKPR_SAVE_TIME"] = str(self._timekprConfig["TIMEKPR_SAVE_TIME"])
        # track inactive (default value)
        values["TIMEKPR_TRACK_INACTIVE"] = str(self._timekprConfig["TIMEKPR_TRACK_INACTIVE"])
        # termination time (allowed login time when there is no time left before user is thrown out)
        values["TIMEKPR_TERMINATION_TIME"] = str(self._timekprConfig["TIMEKPR_TERMINATION_TIME"])
        # final warning time (countdown to 0 before terminating session)
        values["TIMEKPR_FINAL_WARNING_TIME"] = str(self._timekprConfig["TIMEKPR_FINAL_WARNING_TIME"])
        # which session types to control
        values["TIMEKPR_SESSION_TYPES_CTRL"] = str(self._timekprConfig["TIMEKPR_SESSION_TYPES_CTRL"])
        # explicitly excludeds ession types (do not count time in these sessions)
        values["TIMEKPR_SESSION_TYPES_EXCL"] = str(self._timekprConfig["TIMEKPR_SESSION_TYPES_EXCL"])
        # which users to exclude from time accounting
        values["TIMEKPR_USERS_EXCL"] = str(self._timekprConfig["TIMEKPR_USERS_EXCL"])

        # edit client config file (using alternate method because configparser looses comments in the process)
        saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish saving timekpr configuration")

    def getTimekprVersion(self):
        """Get version"""
        # result
        return self._timekprConfig["TIMEKPR_VERSION"]

    def getTimekprLogLevel(self):
        """Get logging level"""
        # result
        return self._timekprConfig["TIMEKPR_LOGLEVEL"]

    def getTimekprPollTime(self):
        """Get polling time"""
        # result
        return self._timekprConfig["TIMEKPR_POLLTIME"]

    def getTimekprSaveTime(self):
        """Get save time"""
        # result
        return self._timekprConfig["TIMEKPR_SAVE_TIME"]

    def getTimekprTrackInactive(self):
        """Get tracking inactive"""
        # result
        return self._timekprConfig["TIMEKPR_TRACK_INACTIVE"]

    def getTimekprTerminationTime(self):
        """Get termination time"""
        # result
        return self._timekprConfig["TIMEKPR_TERMINATION_TIME"]

    def getTimekprFinalWarningTime(self):
        """Get final warning time"""
        # result
        return self._timekprConfig["TIMEKPR_FINAL_WARNING_TIME"]

    def getTimekprSessionsCtrl(self):
        """Get sessions to control"""
        return [result.strip(None) for result in self._timekprConfig["TIMEKPR_SESSION_TYPES_CTRL"].split(";") if self._timekprConfig["TIMEKPR_SESSION_TYPES_CTRL"] != ""]

    def getTimekprSessionsExcl(self):
        """Get sessions to exclude"""
        return [result.strip(None) for result in self._timekprConfig["TIMEKPR_SESSION_TYPES_EXCL"].split(";") if self._timekprConfig["TIMEKPR_SESSION_TYPES_EXCL"] != ""]

    def getTimekprUsersExcl(self):
        """Get sessions to exclude"""
        return [result.strip(None) for result in self._timekprConfig["TIMEKPR_USERS_EXCL"].split(";") if self._timekprConfig["TIMEKPR_USERS_EXCL"] != ""]

    def getTimekprConfigDir(self):
        """Get config dir"""
        # result
        return self._timekprConfig["TIMEKPR_CONFIG_DIR"]

    def getTimekprWorkDir(self):
        """Get working dir"""
        # result
        return self._timekprConfig["TIMEKPR_WORK_DIR"]

    def getTimekprSharedDir(self):
        """Get shared dir"""
        # result
        return self._timekprConfig["TIMEKPR_SHARED_DIR"]

    def getTimekprLogfileDir(self):
        """Get log file dir"""
        # result
        return self._timekprConfig["TIMEKPR_LOGFILE_DIR"]

    def getTimekprLastModified(self):
        """Get last file modification time"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setTimekprLogLevel(self, pLogLevel):
        """Set logging level"""
        # result
        self._timekprConfig["TIMEKPR_LOGLEVEL"] = pLogLevel

    def setTimekprPollTime(self, pPollingTimeSecs):
        """Set polling time"""
        # result
        self._timekprConfig["TIMEKPR_POLLTIME"] = pPollingTimeSecs

    def setTimekprSaveTime(self, pSaveTimeSecs):
        """Set save time"""
        # result
        self._timekprConfig["TIMEKPR_SAVE_TIME"] = pSaveTimeSecs

    def setTimekprTrackInactive(self, pTrackInactiveDefault):
        """Get tracking inactive"""
        # result
        self._timekprConfig["TIMEKPR_TRACK_INACTIVE"] = pTrackInactiveDefault

    def setTimekprTerminationTime(self, pTerminationTimeSecs):
        """Set termination time"""
        # result
        self._timekprConfig["TIMEKPR_TERMINATION_TIME"] = pTerminationTimeSecs

    def setTimekprFinalWarningTime(self, pFinalWarningTimeSecs):
        """Set final warning time"""
        # result
        self._timekprConfig["TIMEKPR_FINAL_WARNING_TIME"] = pFinalWarningTimeSecs

    def setTimekprSessionsCtrl(self, pSessionsCtrl):
        """Set sessions to control"""
        self._timekprConfig["TIMEKPR_SESSION_TYPES_CTRL"] = ";".join(pSessionsCtrl)

    def setTimekprSessionsExcl(self, pSessionsExcl):
        """Set sessions to exclude"""
        self._timekprConfig["TIMEKPR_SESSION_TYPES_EXCL"] = ";".join(pSessionsExcl)

    def setTimekprUsersExcl(self, pUsersExcl):
        """Set sessions to exclude"""
        self._timekprConfig["TIMEKPR_USERS_EXCL"] = ";".join(pUsersExcl)


class timekprUserConfig(object):
    """Class will contain and provide config related functionality"""

    def __init__(self, pLog, pDirectory, pUserName):
        """Initialize config"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "init user (%s) configuration manager" % (pUserName))

        # initialize class variables
        self._configFile = os.path.join(pDirectory, cons.TK_USER_CONFIG_FILE % (pUserName))
        self._userName = pUserName
        self._timekprUserConfig = {}

        # parser
        self._timekprUserConfigParser = configparser.ConfigParser(allow_no_value=True)
        self._timekprUserConfigParser.optionxform = str

        log.log(cons.TK_LOG_LEVEL_INFO, "finish user configuration manager")

    def __del__(self):
        """De-initialize config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "de-init user configuration manager")

    def loadConfiguration(self, pValidateOnly=False):
        """Read main timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start load user configuration")

        # defaults
        useDefaults = False
        result = True

        # check file
        if not os.path.isfile(self._configFile):
            # write correct config file (only if we are not checking whether user exists)
            if not pValidateOnly:
                self.initUserConfiguration()
            else:
                # file not found
                result = False

        # if we still are fine
        if result:
            # read config
            try:
                self._timekprUserConfigParser.read(self._configFile)
            except Exception:
                # we have a problem, will be using defaults
                useDefaults = True
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the user configuration file (%s) properly, will use default values" % (self._configFile))

            # directory section
            section = self._userName

            # read
            param = "ALLOWED_HOURS"
            for i in range(1, 7+1):
                self._timekprUserConfig["%s_%s" % (param, str(i))] = cons.TK_ALLOWED_HOURS if useDefaults else self._timekprUserConfigParser.get(section, ("%s_%s" % (param, str(i))))
            # read
            param = "ALLOWED_WEEKDAYS"
            self._timekprUserConfig[param] = cons.TK_ALLOWED_WEEKDAYS if useDefaults else self._timekprUserConfigParser.get(section, param)
            # read
            param = "LIMITS_PER_WEEKDAYS"
            self._timekprUserConfig[param] = cons.TK_LIMITS_PER_WEEKDAYS if useDefaults else self._timekprUserConfigParser.get(section, param)
            # read
            param = "LIMIT_PER_WEEK"
            self._timekprUserConfig[param] = cons.TK_LIMIT_PER_WEEK if useDefaults else self._timekprUserConfigParser.getint(section, param)
            # read
            param = "LIMIT_PER_MONTH"
            self._timekprUserConfig[param] = cons.TK_LIMIT_PER_MONTH if useDefaults else self._timekprUserConfigParser.getint(section, param)
            # read
            param = "TRACK_INACTIVE"
            self._timekprUserConfig[param] = cons.TK_TRACK_INACTIVE if useDefaults else self._timekprUserConfigParser.getboolean(section, param)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish load user configuration")

        # result
        return result

    def initUserConfiguration(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_INFO, "init default user (%s) configuration" % (self._userName))

        # save default config
        section = "DOCUMENTATION"
        self._timekprUserConfigParser.add_section(section)
        self._timekprUserConfigParser.set(section, "#### this is the user configuration file for timekpr-next")
        self._timekprUserConfigParser.set(section, "#### if this file can not be read properly, it will be overwritten with defaults")

        # add new user section
        section = self._userName
        self._timekprUserConfigParser.add_section(section)
        self._timekprUserConfigParser.set(section, "# this defines which hours are allowed (remove or add hours to limit access), configure limits for start/end minutes for hour in brackets, example: 22[00-15]")
        # set hours for all days
        for i in range(1, 7+1):
            self._timekprUserConfigParser.set(section, "ALLOWED_HOURS_%s" % (str(i)), cons.TK_ALLOWED_HOURS)
        self._timekprUserConfigParser.set(section, "# this defines which days of the week a user can use computer (remove or add days to limit access)")
        self._timekprUserConfigParser.set(section, "ALLOWED_WEEKDAYS", cons.TK_ALLOWED_WEEKDAYS)
        self._timekprUserConfigParser.set(section, "# this defines allowed time in seconds per week day a user can use the computer")
        self._timekprUserConfigParser.set(section, "LIMITS_PER_WEEKDAYS", cons.TK_LIMITS_PER_WEEKDAYS)
        self._timekprUserConfigParser.set(section, "# this defines allowed time per week in seconds (in addition to other limits)")
        self._timekprUserConfigParser.set(section, "LIMIT_PER_WEEK", str(cons.TK_LIMIT_PER_WEEK))
        self._timekprUserConfigParser.set(section, "# this defines allowed time per month in seconds (in addition to other limits)")
        self._timekprUserConfigParser.set(section, "LIMIT_PER_MONTH", str(cons.TK_LIMIT_PER_MONTH))
        self._timekprUserConfigParser.set(section, "# this defines whether to account sessions which are inactive (locked screen, user switched away from desktop, etc.)")
        self._timekprUserConfigParser.set(section, "TRACK_INACTIVE", str(cons.TK_TRACK_INACTIVE))

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprUserConfigParser.write(fp)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init default user configuration")

    def saveUserConfiguration(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start saving new user (%s) configuration" % (self._userName))

        # init dict
        values = {}

        # allowed weekdays
        values["ALLOWED_WEEKDAYS"] = self._timekprUserConfig["ALLOWED_WEEKDAYS"]
        # limits per weekdays
        values["LIMITS_PER_WEEKDAYS"] = self._timekprUserConfig["LIMITS_PER_WEEKDAYS"]
        # limits per week
        values["LIMIT_PER_WEEK"] = str(self._timekprUserConfig["LIMIT_PER_WEEK"])
        # limits per month
        values["LIMIT_PER_MONTH"] = str(self._timekprUserConfig["LIMIT_PER_MONTH"])
        # track inactive
        values["TRACK_INACTIVE"] = str(self._timekprUserConfig["TRACK_INACTIVE"])
        # allowed hours for every week day
        for rDay in range(1, 7+1):
            values["ALLOWED_HOURS_%s" % (str(rDay))] = self._timekprUserConfig["ALLOWED_HOURS_%s" % (str(rDay))]

        # edit client config file (using alternate method because configparser looses comments in the process)
        saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish saving new user configuration")

    def getUserAllowedHours(self, pDay=1):
        """Get allowed hours"""
        # this is the dict for hour config
        allowedHours = {}

        # get allowed hours for all of the week days
        # minutes can be specified in brackets after hour
        if self._timekprUserConfig["ALLOWED_HOURS_%s" % (str(pDay))] != "":
            for rHour in self._timekprUserConfig["ALLOWED_HOURS_%s" % (str(pDay))].split(";"):
                # if we have advanced config (minutes)
                if "[" in rHour and "]" in rHour and "-" in rHour:
                    # get minutes
                    minutes = rHour.split("[", 1)[1].split("]")[0].split("-")
                    # get our dict done
                    allowedHours[rHour.split("[", 1)[0]] = {cons.TK_CTRL_SMIN: min(max(int(minutes[0]), 0), 60), cons.TK_CTRL_EMIN: min(max(int(minutes[1]), 0), 60)}
                else:
                    # get our dict done
                    allowedHours[rHour.split("[", 1)[0]] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # result
        return allowedHours

    def getUserAllowedWeekdays(self):
        """Get allowed week days"""
        # result
        return [int(result.strip(None)) for result in self._timekprUserConfig["ALLOWED_WEEKDAYS"].split(";") if self._timekprUserConfig["ALLOWED_WEEKDAYS"] != ""]

    def getUserLimitsPerWeekdays(self):
        """Get allowed limits per week day"""
        # result
        return [int(result.strip(None)) for result in self._timekprUserConfig["LIMITS_PER_WEEKDAYS"].split(";") if self._timekprUserConfig["LIMITS_PER_WEEKDAYS"] != ""]

    def getUserWeekLimit(self):
        """Get limit per week"""
        # result
        return self._timekprUserConfig["LIMIT_PER_WEEK"]

    def getUserMonthLimit(self):
        """Get limit per month"""
        # result
        return self._timekprUserConfig["LIMIT_PER_MONTH"]

    def getUserTrackInactive(self):
        """Get whether to track inactive sessions"""
        # result
        return self._timekprUserConfig["TRACK_INACTIVE"]

    def getUserLastModified(self):
        """Get last file modification time for user"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setUserAllowedHours(self, pAllowedHours):
        """Get allowed hours"""
        # go through all days given for modifications
        for rDay, rHours in pAllowedHours.items():
            # inital hours
            hours = []

            # go through all hours (in correct order)
            for rHour in range(0, 23+1):
                # convert once
                hour = str(rHour)

                # do we have config for this hour
                if hour in rHours:
                    # do we have proper minuten
                    if rHours[hour][cons.TK_CTRL_SMIN] > 0 or rHours[hour][cons.TK_CTRL_EMIN] < 60:
                        minutes = "[%i-%i]" % (rHours[hour][cons.TK_CTRL_SMIN], rHours[hour][cons.TK_CTRL_EMIN])
                    else:
                        minutes = ""

                    # build up this hour
                    hours.append("%s%s" % (hour, minutes))

            # add this hour to allowable list
            self._timekprUserConfig["ALLOWED_HOURS_%s" % (str(rDay))] = ";".join(hours)

    def setUserAllowedWeekdays(self, pAllowedWeekdays):
        """Set allowed week days"""
        # set up weekdays
        self._timekprUserConfig["ALLOWED_WEEKDAYS"] = ";".join(map(str, pAllowedWeekdays))

    def setUserLimitsPerWeekdays(self, pLimits):
        """Get allowed limits per week day"""
        # set up limits for weekdays
        self._timekprUserConfig["LIMITS_PER_WEEKDAYS"] = ";".join(map(str, pLimits))

    def setUserWeekLimit(self, pWeekLimitSecs):
        """Set limit per week"""
        # result
        self._timekprUserConfig["LIMIT_PER_WEEK"] = int(pWeekLimitSecs)

    def setUserMonthLimit(self, pMonthLimitSecs):
        """Set limit per month"""
        # result
        self._timekprUserConfig["LIMIT_PER_MONTH"] = int(pMonthLimitSecs)

    def setUserTrackInactive(self, pTrackInactive):
        """Get whether to track inactive sessions"""
        # set track inactive
        self._timekprUserConfig["TRACK_INACTIVE"] = bool(pTrackInactive)


class timekprUserControl(object):
    """Class will provide time spent file management functionality"""

    def __init__(self, pLog, pDirectory, pUserName):
        """Initialize config"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "init user (%s) control" % (pUserName))

        # initialize class variables
        self._configFile = os.path.join(pDirectory, pUserName + ".time")
        self._userName = pUserName
        self._timekprUserControl = {}

        # parser
        self._timekprUserControlParser = configparser.ConfigParser(allow_no_value=True)
        self._timekprUserControlParser.optionxform = str

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init user control")

    def __del__(self):
        """De-initialize config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "de-init user control")

    def loadControl(self, pValidateOnly=False):
        """Read main timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading user control (%s)" % (self._userName))

        # directory section
        section = self._userName
        result = True

        # check file
        if not os.path.isfile(self._configFile) or os.path.getsize(self._configFile) == 0:
            # write correct config file (only if we are not checking whether user exists)
            if not pValidateOnly:
                # write correct config file
                self.initUserControl()
            else:
                # file not found
                result = False

        # if we still are fine
        if result:
            # read config
            try:
                self._timekprUserControlParser.read(self._configFile)
            except Exception:
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the user control file (%s) properly, will recreate" % (self._configFile))
                # init config
                self.initUserControl()

            # re-read the file
            self._timekprUserControlParser.read(self._configFile)

            # read
            param = "TIME_SPENT"
            self._timekprUserControl[param] = min(max(self._timekprUserControlParser.getint(section, param), -cons.TK_LIMIT_PER_DAY), cons.TK_LIMIT_PER_DAY)
            # read
            param = "TIME_SPENT_WEEK"
            self._timekprUserControl[param] = min(max(self._timekprUserControlParser.getint(section, param), -cons.TK_LIMIT_PER_WEEK), cons.TK_LIMIT_PER_WEEK)
            # read
            param = "TIME_SPENT_MONTH"
            self._timekprUserControl[param] = min(max(self._timekprUserControlParser.getint(section, param), -cons.TK_LIMIT_PER_MONTH), cons.TK_LIMIT_PER_MONTH)
            # read
            param = "LAST_CHECKED"
            self._timekprUserControl[param] = datetime.strptime(self._timekprUserControlParser.get(section, param), cons.TK_DATETIME_FORMAT)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading user control")

        # result
        return result

    def initUserControl(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init user (%s) control" % (self._userName))

        # add new user section
        section = self._userName
        self._timekprUserControlParser.add_section(section)
        self._timekprUserControlParser.set(section, "# total limit spent for today")
        self._timekprUserControlParser.set(section, "TIME_SPENT", "0")
        self._timekprUserControlParser.set(section, "# total limit spent for this week")
        self._timekprUserControlParser.set(section, "TIME_SPENT_WEEK", "0")
        self._timekprUserControlParser.set(section, "# total limit spent for this month")
        self._timekprUserControlParser.set(section, "TIME_SPENT_MONTH", "0")
        self._timekprUserControlParser.set(section, "# last update time of the file")
        self._timekprUserControlParser.set(section, "LAST_CHECKED", datetime.now().replace(microsecond=0).strftime(cons.TK_DATETIME_FORMAT))

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprUserControlParser.write(fp)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init user control")

    def saveControl(self):
        """Save configuration"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start save user (%s) control" % (self._userName))

        # init dict
        values = {}

        # spent day
        values["TIME_SPENT"] = str(int(self._timekprUserControl["TIME_SPENT"]))
        # spent week
        values["TIME_SPENT_WEEK"] = str(int(self._timekprUserControl["TIME_SPENT_WEEK"]))
        # spent month
        values["TIME_SPENT_MONTH"] = str(int(self._timekprUserControl["TIME_SPENT_MONTH"]))
        # last checked
        values["LAST_CHECKED"] = self._timekprUserControl["LAST_CHECKED"].strftime(cons.TK_DATETIME_FORMAT)

        # edit control file (using alternate method because configparser looses comments in the process)
        saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish save user control")

    def getUserTimeSpent(self):
        """Get time spent for day"""
        # result
        return self._timekprUserControl["TIME_SPENT"]

    def getUserTimeSpentWeek(self):
        """Get time spent for week"""
        # result
        return self._timekprUserControl["TIME_SPENT_WEEK"]

    def getUserTimeSpentMonth(self):
        """Get time spent for month"""
        # result
        return self._timekprUserControl["TIME_SPENT_MONTH"]

    def getUserLastChecked(self):
        """Get last check time for user"""
        # result
        return self._timekprUserControl["LAST_CHECKED"]

    def getUserLastModified(self):
        """Get last file modification time for user"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setUserTimeSpent(self, pTimeSpent):
        """Set time spent for day"""
        # result
        self._timekprUserControl["TIME_SPENT"] = pTimeSpent

    def setUserTimeSpentWeek(self, pTimeSpentWeek):
        """Set time spent for week"""
        # result
        self._timekprUserControl["TIME_SPENT_WEEK"] = pTimeSpentWeek

    def setUserTimeSpentMonth(self, pTimeSpentMonth):
        """Set time spent for month"""
        # result
        self._timekprUserControl["TIME_SPENT_MONTH"] = pTimeSpentMonth

    def setUserLastChecked(self, pEffectiveDatetime):
        """Set last check time for user"""
        # result
        self._timekprUserControl["LAST_CHECKED"] = pEffectiveDatetime


class timekprClientConfig(object):
    """Class will hold and provide config management for user"""

    def __init__(self, pIsDevActive=False):
        """Initialize config"""
        # config
        self._timekprConfig = {}
        self._isDevActive = pIsDevActive
        # get home
        self._userHome = os.path.expanduser("~")

        # set up logging
        logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_INFO, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: cons.TK_LOG_OWNER_CLIENT, cons.TK_LOG_U: getpass.getuser()}
        # set up logging
        log.setLogging(logging)

        # set up log file name
        self._timekprConfig["TIMEKPR_LOGFILE_DIR"] = logging[cons.TK_LOG_D]

        log.log(cons.TK_LOG_LEVEL_INFO, "start initializing client configuration manager")

        # in dev
        if self._isDevActive:
            self._configDirPrefix = os.getcwd()
        else:
            self._configDirPrefix = ""

        # main config
        self._timekprConfig["TIMEKPR_MAIN_CONFIG_DIR"] = os.path.join(self._configDirPrefix, (cons.TK_MAIN_CONFIG_DIR_DEV if self._isDevActive else cons.TK_MAIN_CONFIG_DIR))
        self._configMainFile = os.path.join(self._timekprConfig["TIMEKPR_MAIN_CONFIG_DIR"], cons.TK_MAIN_CONFIG_FILE)

        # config
        self._configFile = os.path.join(self._userHome, ".config/timekpr", cons.TK_MAIN_CONFIG_FILE)

        # config parser
        self._timekprConfigParser = configparser.ConfigParser(allow_no_value=True)
        self._timekprConfigParser.optionxform = str

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initializing client configuration manager")

    def __del__(self):
        """De-initialize config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "de-initialize client configuration manager")

    def loadClientConfiguration(self):
        """Read main timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading client configuration")

        # get directories from main config
        if "TIMEKPR_SHARED_DIR" not in self._timekprConfig:
            # load main config to get directories
            self.loadClientMainConfig()
            # clear out cp
            self._timekprConfigParser.clear()

        # we have a problem, will be using defaults
        useDefaults = False

        # check file
        if not os.path.isfile(self._configFile):
            # write correct config filetimekprUserControl
            self.initClientConfig()

        # config load time
        self._clientConfigModTime = self.getClientLastModified()

        # read config
        try:
            self._timekprConfigParser.read(self._configFile)
        except Exception:
            # we have a problem, will be using defaults
            useDefaults = True
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configFile))

        # directory section
        section = "CONFIG"
        # read
        param = "SHOW_LIMIT_NOTIFICATION"
        self._timekprConfig[param] = True if useDefaults else self._timekprConfigParser.getboolean(section, param)
        # read
        param = "SHOW_ALL_NOTIFICATIONS"
        self._timekprConfig[param] = True if useDefaults else self._timekprConfigParser.getboolean(section, param)
        # read
        param = "USE_SPEECH_NOTIFICATIONS"
        self._timekprConfig[param] = False if useDefaults else self._timekprConfigParser.getboolean(section, param)
        # read
        param = "SHOW_SECONDS"
        self._timekprConfig[param] = False if useDefaults else self._timekprConfigParser.getboolean(section, param)
        # read
        param = "LOG_LEVEL"
        self._timekprConfig[param] = cons.TK_LOG_LEVEL_INFO if useDefaults else self._timekprConfigParser.getint(section, param)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading client configuration")

        # result
        return True

    def loadClientMainConfig(self):
        """Load main configuration file to get shared file locations"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading main configuration")

        # whether to use values from code
        useDefaults = False

        # read config
        try:
            self._timekprConfigParser.read(self._configMainFile)
        except Exception:
            # we have a problem, will be using defaults
            useDefaults = True
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configMainFile))

        # directory section
        section = "DIRECTORIES"
        # read
        param = "TIMEKPR_SHARED_DIR"
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if self._isDevActive else (cons.TK_SHARED_DIR if useDefaults else self._timekprConfigParser.get(section, param))))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading main configuration")

        # result
        return True

    def initClientConfig(self):
        """Write new config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init client configuration")

        # directory name
        dirName = os.path.dirname(self._configFile)

        # check file
        if not os.path.isdir(dirName):
            # make it
            os.makedirs(dirName)

        # add new user section
        section = "CONFIG"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "# whether to show limit change notification")
        self._timekprConfigParser.set(section, "SHOW_LIMIT_NOTIFICATION", "True")
        self._timekprConfigParser.set(section, "# whether to show all notifications or important ones only")
        self._timekprConfigParser.set(section, "SHOW_ALL_NOTIFICATIONS", "True")
        self._timekprConfigParser.set(section, "# whether to show seconds in label (if DE supports it)")
        self._timekprConfigParser.set(section, "SHOW_SECONDS", "True")
        self._timekprConfigParser.set(section, "# whether to use speech notifications")
        self._timekprConfigParser.set(section, "USE_SPEECH_NOTIFICATIONS", "False")
        self._timekprConfigParser.set(section, "# user logging level (1 - normal, 2 - debug, 3 - extra debug)")
        self._timekprConfigParser.set(section, "LOG_LEVEL", str(cons.TK_LOG_LEVEL_INFO))

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprConfigParser.write(fp)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init client configuration")

    def saveClientConfig(self):
        """Save configuration (called from GUI)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start save client config")

        # init dict
        values = {}

        # spent
        values["SHOW_LIMIT_NOTIFICATION"] = str(self._timekprConfig["SHOW_LIMIT_NOTIFICATION"])
        # last checked
        values["SHOW_ALL_NOTIFICATIONS"] = str(self._timekprConfig["SHOW_ALL_NOTIFICATIONS"])
        # spent
        values["USE_SPEECH_NOTIFICATIONS"] = str(self._timekprConfig["USE_SPEECH_NOTIFICATIONS"])
        # spent
        values["SHOW_SECONDS"] = str(self._timekprConfig["SHOW_SECONDS"])
        # last checked
        values["LOG_LEVEL"] = str(self._timekprConfig["LOG_LEVEL"])

        # edit control file (using alternate method because configparser looses comments in the process)
        saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish save client config")

    def isClientConfigChanged(self):
        """Whether config has changed"""
        # defaults
        result = False

        # yes, is it changed?
        if self._clientConfigModTime != self.getClientLastModified():
            # changed
            self._clientConfigModTime = self.getClientLastModified()
            # load config
            self.loadClientConfiguration()
            # changed
            result = True

        # result
        return result

    def getClientShowLimitNotifications(self):
        """Get whether to show frst notification"""
        # result
        return self._timekprConfig["SHOW_LIMIT_NOTIFICATION"]

    def getClientShowAllNotifications(self):
        """Get whether to show all notifications"""
        # result
        return self._timekprConfig["SHOW_ALL_NOTIFICATIONS"]

    def getClientUseSpeechNotifications(self):
        """Get whether to use speech"""
        # result
        return self._timekprConfig["USE_SPEECH_NOTIFICATIONS"]

    def getClientShowSeconds(self):
        """Get whether to show seconds"""
        # result
        return self._timekprConfig["SHOW_SECONDS"]

    def getClientLogLevel(self):
        """Get client log level"""
        # result
        return self._timekprConfig["LOG_LEVEL"]

    def getTimekprSharedDir(self):
        """Get shared dir"""
        # result
        return self._timekprConfig["TIMEKPR_SHARED_DIR"]

    def getClientLogfileDir(self):
        """Get shared dir"""
        # result
        return self._timekprConfig["TIMEKPR_LOGFILE_DIR"]

    def getClientLastModified(self):
        """Get last file modification time for user"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setClientShowLimitNotifications(self, pClientShowLimitNotification):
        """Set whether to show frst notification"""
        # set
        self._timekprConfig["SHOW_LIMIT_NOTIFICATION"] = pClientShowLimitNotification

    def setClientShowAllNotifications(self, pClientShowAllNotifications):
        """Set whether to show all notifications"""
        # set
        self._timekprConfig["SHOW_ALL_NOTIFICATIONS"] = pClientShowAllNotifications

    def setClientUseSpeechNotifications(self, pClientUseSpeechNotifications):
        """Get whether to use speech"""
        # set
        self._timekprConfig["USE_SPEECH_NOTIFICATIONS"] = pClientUseSpeechNotifications

    def setClientShowSeconds(self, pClientShowSeconds):
        """Get whether to show seconds"""
        # set
        self._timekprConfig["SHOW_SECONDS"] = pClientShowSeconds

    def setClientLogLevel(self, pClientLogLevel):
        """Get client log level"""
        # set
        self._timekprConfig["LOG_LEVEL"] = pClientLogLevel
