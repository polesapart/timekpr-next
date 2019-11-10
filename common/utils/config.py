"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import configparser
from datetime import datetime
import re
import os
import shutil
import getpass

# timekpr imports
from timekpr.common.log import log
from timekpr.common.constants import constants as cons


def saveConfigFile(pConfigFile, pKeyValuePairs):
    """Save the config file using custom helper function"""
    # edit control file (using alternate method because configparser looses comments in the process)
    # make a backup of the file
    shutil.copy(pConfigFile, pConfigFile + cons.TK_BACK_EXT)
    # read backup and write actual config file
    with open(pConfigFile + cons.TK_BACK_EXT, 'r') as srcFile, open(pConfigFile, 'w') as dstFile:
        # read line and do manipulations
        for rLine in srcFile:
            # check if we have proper line
            for rKey, rValue in pKeyValuePairs.items():
                # check if we have to use regexp
                if ("%s =" % (rKey)) in rLine or ("%s=" % (rKey)) in rLine:
                    # replace key = value pairs
                    line = re.sub(r"(?i)" + rKey + " *=.*$", rKey + " = " + rValue, rLine)
                    # first replacement is enough
                    break
                else:
                    # line does not need a replacement
                    line = rLine

            # save file line back to file
            dstFile.write(line)


def loadAndPrepareConfigFile(pConfigFileParser, pConfigFile):
    """Try to load config file, if that fails, try to read backup file"""
    # by default fail
    result = False
    # process primary and backup files
    for rFile in (pConfigFile, pConfigFile + cons.TK_BACK_EXT):
        # if file is ok
        if os.path.isfile(rFile) and os.path.getsize(rFile) != 0:
            # copy file back to original (if this is backup file)
            if rFile != pConfigFile:
                shutil.copy(rFile, pConfigFile)
            # read config
            try:
                # read config file
                pConfigFileParser.read(pConfigFile)
                # success
                result = True
                break
            except Exception:
                # fail, move corrupted file
                os.rename(rFile, rFile + ".invalid")
        else:
            # we do not need empty files
            if os.path.isfile(rFile):
                # remove empty file
                os.remove(rFile)

    # result
    return result


def readAndNormalizeValue(pConfigFileParserFn, pSection, pParam, pDefaultValue, pCheckValue, pOverallSuccess):
    """Read value from parser, if fails, then return default value"""
    # default values
    result = pOverallSuccess
    value = pDefaultValue
    try:
        # read value from parser
        value = pConfigFileParserFn(pSection, pParam)
        # check min / max if we have numbers
        if pCheckValue is not None and type(pDefaultValue).__name__ in ("int"):
            value = min(max(value, -pCheckValue), pCheckValue)
        # validate date format properly
        elif type(pDefaultValue).__name__ in ("date", "datetime"):
            value = datetime.strptime(value, cons.TK_DATETIME_FORMAT)
    except Exception:
        # default value
        value = pDefaultValue
        # failed
        result = False

    # return
    return result, value


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

        # try to load config file
        result = loadAndPrepareConfigFile(self._timekprConfigParser, self._configFile)
        # value read result
        resultValue = True

        # read config failed, we need to initialize
        if not result:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse main configuration file (%s) properly, will use default values" % (self._configFile))
            # init config
            self.initDefaultConfiguration()
            # re-read the file
            self._timekprConfigParser.read(self._configFile)
            # config initialized
            result = True

        # general section
        section = "GENERAL"
        # read
        param = "TIMEKPR_VERSION"
        self._timekprConfig[param] = cons.TK_VERSION
        # read
        param = "TIMEKPR_LOGLEVEL"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_LOG_LEVEL_INFO, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_POLLTIME"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_POLLTIME, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_SAVE_TIME"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_SAVE_INTERVAL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_TRACK_INACTIVE"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=cons.TK_TRACK_INACTIVE, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_TERMINATION_TIME"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_TERMINATION_TIME, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_FINAL_WARNING_TIME"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_FINAL_COUNTDOWN_TIME, pCheckValue=None, pOverallSuccess=resultValue)

        # session section
        section = "SESSION"
        # read
        param = "TIMEKPR_SESSION_TYPES_CTRL"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SESSION_TYPES_CTRL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_SESSION_TYPES_EXCL"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SESSION_TYPES_EXCL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_USERS_EXCL"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_USERS_EXCL, pCheckValue=None, pOverallSuccess=resultValue)

        # directory section (! in case directories are not correct, they are not overwritten with defaults !)
        section = "DIRECTORIES"
        # read
        param = "TIMEKPR_CONFIG_DIR"
        result, value = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_CONFIG_DIR, pCheckValue=None, pOverallSuccess=resultValue)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_CONFIG_DIR_DEV if self._isDevActive else value))
        # read
        param = "TIMEKPR_WORK_DIR"
        result, value = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_WORK_DIR, pCheckValue=None, pOverallSuccess=resultValue)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_WORK_DIR_DEV if self._isDevActive else value))
        # read
        param = "TIMEKPR_SHARED_DIR"
        result, value = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SHARED_DIR, pCheckValue=None, pOverallSuccess=resultValue)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if self._isDevActive else value))
        # read
        param = "TIMEKPR_LOGFILE_DIR"
        result, value = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_LOGFILE_DIR, pCheckValue=None, pOverallSuccess=resultValue)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_LOGFILE_DIR_DEV if self._isDevActive else value))

        # if we could not read some values, save what we could + defaults
        if not resultValue:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some of the values in main config file (%s) could not be read properly, defaults used and saved" % (self._configFile))
            # save what we could
            self.saveTimekprConfiguration()

        # if we could not read some values, report that (directories only)
        if not result:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some of the directory values in main config file (%s) could not be read properly, defaults used (config NOT overwritten)" % (self._configFile))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading configuration")

        # result
        return True

    def initDefaultConfiguration(self):
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
        """Read user timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start load user configuration")

        # directory section
        section = self._userName
        # try to load config file
        result = loadAndPrepareConfigFile(self._timekprUserConfigParser, self._configFile)
        # value read result
        resultValue = True
        # if we still are fine (and not just checking)
        if not pValidateOnly or (pValidateOnly and result):
            # read config failed, we need to initialize
            if not result:
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the main configuration file (%s) properly, will use default values" % (self._configFile))
                # init config
                self.initUserConfiguration()
                # re-read the file
                self._timekprUserConfigParser.read(self._configFile)

            # read
            param = "ALLOWED_HOURS"
            for i in range(1, 7+1):
                resultValue, self._timekprUserConfig["%s_%s" % (param, str(i))] = readAndNormalizeValue(self._timekprUserConfigParser.get, section, ("%s_%s" % (param, str(i))), pDefaultValue=cons.TK_ALLOWED_HOURS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "ALLOWED_WEEKDAYS"
            resultValue, self._timekprUserConfig[param] = readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_ALLOWED_WEEKDAYS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMITS_PER_WEEKDAYS"
            resultValue, self._timekprUserConfig[param] = readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_LIMITS_PER_WEEKDAYS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMIT_PER_WEEK"
            resultValue, self._timekprUserConfig[param] = readAndNormalizeValue(self._timekprUserConfigParser.getint, section, param, pDefaultValue=cons.TK_LIMIT_PER_WEEK, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMIT_PER_MONTH"
            resultValue, self._timekprUserConfig[param] = readAndNormalizeValue(self._timekprUserConfigParser.getint, section, param, pDefaultValue=cons.TK_LIMIT_PER_MONTH, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "TRACK_INACTIVE"
            resultValue, self._timekprUserConfig[param] = readAndNormalizeValue(self._timekprUserConfigParser.getboolean, section, param, pDefaultValue=cons.TK_TRACK_INACTIVE, pCheckValue=None, pOverallSuccess=resultValue)

            # if we could not read some values, save what we could + defaults
            if not resultValue:
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some of the values in user config file (%s) could not be read properly, defaults used and saved" % (self._configFile))
                # save what we could
                self.saveUserConfiguration()

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
        # try to load config file
        result = loadAndPrepareConfigFile(self._timekprUserControlParser, self._configFile)
        # value read result
        resultValue = True

        # if we still are fine (and not just checking)
        if not pValidateOnly or (pValidateOnly and result):
            # read config failed, we need to initialize
            if not result:
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the user control file (%s) properly, will recreate" % (self._configFile))
                # init config
                self.initUserControl()
                # re-read the file
                self._timekprUserControlParser.read(self._configFile)

            # read
            param = "TIME_SPENT"
            resultValue, self._timekprUserControl[param] = readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_DAY, pOverallSuccess=resultValue)
            # read
            param = "TIME_SPENT_WEEK"
            resultValue, self._timekprUserControl[param] = readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_WEEK, pOverallSuccess=resultValue)
            # read
            param = "TIME_SPENT_MONTH"
            resultValue, self._timekprUserControl[param] = readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_MONTH, pOverallSuccess=resultValue)
            # read
            param = "LAST_CHECKED"
            resultValue, self._timekprUserControl[param] = readAndNormalizeValue(self._timekprUserControlParser.get, section, param, pDefaultValue=datetime.now().replace(microsecond=0), pCheckValue=None, pOverallSuccess=resultValue)

            # if we could not read some values, save what we could + defaults
            if not resultValue:
                # report shit
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some of the values in user control file (%s) could not be read properly, defaults used and saved" % (self._configFile))
                # save what we could
                self.saveControl()

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
            self.loadMinimalClientMainConfig()
            # clear out cp, we don't need to store all condfigs in minimal case
            self._timekprConfigParser.clear()

        # try to load config file
        result = loadAndPrepareConfigFile(self._timekprConfigParser, self._configFile)
        # value read result
        resultValue = True

        # read config failed, we need to initialize
        if not result:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configFile))
            # write correct config file
            self.initClientConfig()
            # re-read the file
            self._timekprConfigParser.read(self._configFile)

        # config load time
        self._clientConfigModTime = self.getClientLastModified()

        # directory section
        section = "CONFIG"
        # read
        param = "SHOW_LIMIT_NOTIFICATION"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=True, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "SHOW_ALL_NOTIFICATIONS"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=True, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "USE_SPEECH_NOTIFICATIONS"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=False, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "SHOW_SECONDS"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=False, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "LOG_LEVEL"
        resultValue, self._timekprConfig[param] = readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_LOG_LEVEL_INFO, pCheckValue=None, pOverallSuccess=resultValue)

        # if we could not read some values, save what we could + defaults
        if not resultValue:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some of the values in client confguration file (%s) could not be read properly, defaults used and saved" % (self._configFile))
            # save what we could
            self.saveClientConfig()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading client configuration")

        # result
        return True

    def loadMinimalClientMainConfig(self):
        """Load main configuration file to get shared file locations"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading minimal main configuration")
        # defaults
        # directory section
        section = "DIRECTORIES"
        # read
        param = "TIMEKPR_SHARED_DIR"

        # try to load config file
        result = loadAndPrepareConfigFile(self._timekprConfigParser, self._configMainFile)
        # if file can not be read
        if not result:
            # default value
            value = cons.TK_SHARED_DIR
        else:
            # read file
            result, value = readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SHARED_DIR, pCheckValue=None, pOverallSuccess=True)

        # problems loading default config
        if not result:
            # report shit
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configMainFile))

        # finalize directory
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if self._isDevActive else value))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading minimal main configuration")

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
