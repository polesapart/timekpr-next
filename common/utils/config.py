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


def _findHourStartEndMinutes(pStr):
    """Separate name and desription in brackets"""
    # hour, start, end
    hour = None
    sMin = None
    eMin = None

    # get hour
    if len(pStr) <= 2:
        # hour, start, end
        hour = pStr
        sMin = 0
        eMin = 60
    else:
        # find minutes
        st = pStr.find("[")
        sep = pStr.find("-")
        en = pStr.find("]")
        # in case user config is broken, we cannot determine stuff
        if st < 0 or en < 0 or sep < 0 or not st < sep < en:
            # nothing
            pass
        else:
            # hour, start, end
            try:
                # determine hour and minutes (and check for errors as well)
                hour = int(pStr[0:st])
                sMin = int(pStr[st+1:sep])
                eMin = int(pStr[sep+1:en])
                # checks for errors (and raise one if there is an error)
                hour = hour if 0 <= hour <= 23 else 1/0
                sMin = sMin if 0 <= sMin <= 60 else 1/0
                eMin = eMin if 0 <= eMin <= 60 else 1/0
                eMin = eMin if sMin < eMin else 1/0
            except (ValueError, ZeroDivisionError):
                # hour, start, end
                hour = None
                sMin = None
                eMin = None

    # return
    return hour, sMin, eMin


def _saveConfigFile(pConfigFile, pKeyValuePairs):
    """Save the config file using custom helper function"""
    # edit control file (using alternate method because configparser looses comments in the process)
    # make a backup of the file
    shutil.copy(pConfigFile, pConfigFile + cons.TK_BACK_EXT)
    # read backup and write actual config file
    with open(pConfigFile + cons.TK_BACK_EXT, "r") as srcFile, open(pConfigFile, "w") as dstFile:
        # read line and do manipulations
        for rLine in srcFile:
            # check if we have proper line
            for rKey, rValue in pKeyValuePairs.items():
                # check if we have to change value
                if re.match("%s%s%s" % ("^", rKey, " *="), rLine):
                    # replace key = value pairs
                    line = re.sub("%s%s%s" % ("^", rKey, " *=.*$"), "%s%s%s" % (rKey, " = ", rValue), rLine)
                    # first replacement is enough
                    break
                else:
                    # line does not need a replacement
                    line = rLine

            # save file line back to file
            dstFile.write(line)


def _loadAndPrepareConfigFile(pConfigFileParser, pConfigFile, pLoadOnly=False):
    """Try to load config file, if that fails, try to read backup file"""
    # by default fail
    result = False
    # process primary and backup files
    for rFile in (pConfigFile, pConfigFile + cons.TK_BACK_EXT):
        # if file is ok
        if os.path.isfile(rFile) and os.path.getsize(rFile) != 0:
            # copy file back to original (if this is backup file)
            if rFile != pConfigFile and not pLoadOnly:
                shutil.copy(rFile, pConfigFile)
            # read config
            try:
                # read config file
                pConfigFileParser.read(pConfigFile)
                # success
                result = True
                break
            except Exception:
                # not load only
                if not pLoadOnly:
                    # fail, move corrupted file
                    os.rename(rFile, rFile + ".invalid")
        else:
            # we do not need empty files
            if os.path.isfile(rFile) and not pLoadOnly:
                # remove empty file
                os.remove(rFile)

    # result
    return result


def _readAndNormalizeValue(pConfigFileParserFn, pSection, pParam, pDefaultValue, pCheckValue, pOverallSuccess):
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

    def __init__(self, pLog=None):
        """Initialize stuff"""
        if pLog is not None:
            log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "initializing configuration manager")

        # config
        self._timekprConfig = {}

        # in dev
        self._configDirPrefix = os.getcwd() if cons.TK_DEV_ACTIVE else ""
        # main config
        self._timekprConfig["TIMEKPR_MAIN_CONFIG_DIR"] = os.path.join(self._configDirPrefix, (cons.TK_MAIN_CONFIG_DIR_DEV if cons.TK_DEV_ACTIVE else cons.TK_MAIN_CONFIG_DIR))
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
        result = _loadAndPrepareConfigFile(self._timekprConfigParser, self._configFile)
        # value read result
        resultValue = True

        # read config failed, we need to initialize
        if not result:
            # logging
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
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_LOG_LEVEL_INFO, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_POLLTIME"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_POLLTIME, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_SAVE_TIME"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_SAVE_INTERVAL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_TRACK_INACTIVE"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getboolean, section, param, pDefaultValue=cons.TK_TRACK_INACTIVE, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_TERMINATION_TIME"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_TERMINATION_TIME, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_FINAL_WARNING_TIME"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.getint, section, param, pDefaultValue=cons.TK_FINAL_COUNTDOWN_TIME, pCheckValue=None, pOverallSuccess=resultValue)

        # session section
        section = "SESSION"
        # read
        param = "TIMEKPR_SESSION_TYPES_CTRL"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SESSION_TYPES_CTRL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_SESSION_TYPES_EXCL"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SESSION_TYPES_EXCL, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "TIMEKPR_USERS_EXCL"
        resultValue, self._timekprConfig[param] = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_USERS_EXCL, pCheckValue=None, pOverallSuccess=resultValue)

        # directory section (! in case directories are not correct, they are not overwritten with defaults !)
        section = "DIRECTORIES"
        # read
        param = "TIMEKPR_CONFIG_DIR"
        result, value = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_CONFIG_DIR, pCheckValue=None, pOverallSuccess=result)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_CONFIG_DIR_DEV if cons.TK_DEV_ACTIVE else value))
        # read
        param = "TIMEKPR_WORK_DIR"
        result, value = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_WORK_DIR, pCheckValue=None, pOverallSuccess=result)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_WORK_DIR_DEV if cons.TK_DEV_ACTIVE else value))
        # read
        param = "TIMEKPR_SHARED_DIR"
        result, value = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_SHARED_DIR, pCheckValue=None, pOverallSuccess=result)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if cons.TK_DEV_ACTIVE else value))
        # read
        param = "TIMEKPR_LOGFILE_DIR"
        result, value = _readAndNormalizeValue(self._timekprConfigParser.get, section, param, pDefaultValue=cons.TK_LOGFILE_DIR, pCheckValue=None, pOverallSuccess=result)
        self._timekprConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_LOGFILE_DIR_DEV if cons.TK_DEV_ACTIVE else value))

        # if we could not read some values, save what we could + defaults
        if not resultValue:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "WARNING: some values in main config file (%s) could not be read or new configuration option was introduced, valid values and defaults are used / saved instead" % (self._configFile))
            # save what we could
            self.initDefaultConfiguration(True)

        # if we could not read some values, report that (directories only)
        if not result:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: some directory values in main config file (%s) could not be read, valid values and defaults used (config NOT overwritten)" % (self._configFile))

        # clear parser
        self._timekprConfigParser.clear()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading configuration")

        # result
        return True

    def initDefaultConfiguration(self, pReuseValues=False):
        """Save config file (if someone messed up config file, we have to write new one)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start saving default configuration")

        # clear parser
        self._timekprConfigParser.clear()

        # save default config
        section = "DOCUMENTATION"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this is the main configuration file for timekpr-next")
        self._timekprConfigParser.set(section, "#### if this file cannot be read properly, it will be overwritten with defaults")

        section = "GENERAL"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### general configuration section")
        # set up param
        param = "TIMEKPR_LOGLEVEL"
        self._timekprConfigParser.set(section, "# this defines logging level of the timekpr (1 - normal, 2 - debug, 3 - extra debug)")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_LOG_LEVEL_INFO))
        # set up param
        param = "TIMEKPR_POLLTIME"
        self._timekprConfigParser.set(section, "# this defines polling time (in memory) in seconds")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_POLLTIME))
        # set up param
        param = "TIMEKPR_SAVE_TIME"
        self._timekprConfigParser.set(section, "# this defines a time for saving user time control file (polling and accounting is done in memory more often, but saving is not)")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_SAVE_INTERVAL))
        # set up param
        param = "TIMEKPR_TRACK_INACTIVE"
        self._timekprConfigParser.set(section, "# this defines whether to account sessions which are inactive (locked screen, user switched away from desktop, etc.), this defines the default value for new users")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_TRACK_INACTIVE))
        # set up param
        param = "TIMEKPR_TERMINATION_TIME"
        self._timekprConfigParser.set(section, "# this defines a time interval in seconds prior to assign user a termination sequence")
        self._timekprConfigParser.set(section, "#   15 seconds before time ends nothing can be done to avoid killing a session")
        self._timekprConfigParser.set(section, "#   this also is the time before initiating a termination sequence if user has logged in inappropriate time")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_TERMINATION_TIME))
        # set up param
        param = "TIMEKPR_FINAL_WARNING_TIME"
        self._timekprConfigParser.set(section, "# this defines a time interval when timekpr will send continous final warnings until the termination of user sessions")
        self._timekprConfigParser.set(section, "%s" % (param), str(self._timekprConfig[param]) if pReuseValues else str(cons.TK_FINAL_COUNTDOWN_TIME))

        section = "SESSION"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this section contains configuration about sessions")
        # set up param
        param = "TIMEKPR_SESSION_TYPES_CTRL"
        self._timekprConfigParser.set(section, "# session types timekpr will track")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_SESSION_TYPES_CTRL)
        # set up param
        param = "TIMEKPR_SESSION_TYPES_EXCL"
        self._timekprConfigParser.set(section, "# session types timekpr will ignore explicitly")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_SESSION_TYPES_EXCL)
        # set up param
        param = "TIMEKPR_USERS_EXCL"
        self._timekprConfigParser.set(section, "# users timekpr will ignore explicitly")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_USERS_EXCL)

        section = "DIRECTORIES"
        self._timekprConfigParser.add_section(section)
        self._timekprConfigParser.set(section, "#### this section contains directory configuration")
        # set up param
        param = "TIMEKPR_CONFIG_DIR"
        self._timekprConfigParser.set(section, "# runtime directory for timekpr user configuration files")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_CONFIG_DIR)
        # set up param
        param = "TIMEKPR_WORK_DIR"
        self._timekprConfigParser.set(section, "# runtime directory for timekpr time control files")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_WORK_DIR)
        # set up param
        param = "TIMEKPR_SHARED_DIR"
        self._timekprConfigParser.set(section, "# directory for shared files (images, gui definitions, etc.)")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_SHARED_DIR)
        # set up param
        param = "TIMEKPR_LOGFILE_DIR"
        self._timekprConfigParser.set(section, "# directory for log files")
        self._timekprConfigParser.set(section, "%s" % (param), self._timekprConfig[param] if pReuseValues else cons.TK_LOGFILE_DIR)

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprConfigParser.write(fp)
        # clear parser
        self._timekprConfigParser.clear()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish saving default configuration")

    def saveTimekprConfiguration(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start saving timekpr configuration")

        # init dict
        values = {}

        # server loglevel
        param = "TIMEKPR_LOGLEVEL"
        values[param] = str(self._timekprConfig[param])
        # in-memory polling time
        param = "TIMEKPR_POLLTIME"
        values[param] = str(self._timekprConfig[param])
        # time interval to save user spent time
        param = "TIMEKPR_SAVE_TIME"
        values[param] = str(self._timekprConfig[param])
        # track inactive (default value)
        param = "TIMEKPR_TRACK_INACTIVE"
        values[param] = str(self._timekprConfig[param])
        # termination time (allowed login time when there is no time left before user is thrown out)
        param = "TIMEKPR_TERMINATION_TIME"
        values[param] = str(self._timekprConfig[param])
        # final warning time (countdown to 0 before terminating session)
        param = "TIMEKPR_FINAL_WARNING_TIME"
        values[param] = str(self._timekprConfig[param])
        # which session types to control
        param = "TIMEKPR_SESSION_TYPES_CTRL"
        values[param] = str(self._timekprConfig[param])
        # explicitly excludeds ession types (do not count time in these sessions)
        param = "TIMEKPR_SESSION_TYPES_EXCL"
        values[param] = str(self._timekprConfig[param])
        # which users to exclude from time accounting
        param = "TIMEKPR_USERS_EXCL"
        values[param] = str(self._timekprConfig[param])

        # edit client config file (using alternate method because configparser looses comments in the process)
        _saveConfigFile(self._configFile, values)

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

        # user config section
        section = self._userName
        # try to load config file
        result = _loadAndPrepareConfigFile(self._timekprUserConfigParser, self._configFile)
        # value read result
        resultValue = True
        # if we still are fine (and not just checking)
        if not pValidateOnly or (pValidateOnly and result):
            # read config failed, we need to initialize
            if not result:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the main configuration file (%s) properly, will use default values" % (self._configFile))
                # init config
                self.initUserConfiguration()
                # re-read the file
                self._timekprUserConfigParser.read(self._configFile)

            # read
            param = "ALLOWED_HOURS"
            for i in range(1, 7+1):
                resultValue, self._timekprUserConfig["%s_%s" % (param, str(i))] = _readAndNormalizeValue(self._timekprUserConfigParser.get, section, ("%s_%s" % (param, str(i))), pDefaultValue=cons.TK_ALLOWED_HOURS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "ALLOWED_WEEKDAYS"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_ALLOWED_WEEKDAYS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMITS_PER_WEEKDAYS"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_LIMITS_PER_WEEKDAYS, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMIT_PER_WEEK"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.getint, section, param, pDefaultValue=cons.TK_LIMIT_PER_WEEK, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LIMIT_PER_MONTH"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.getint, section, param, pDefaultValue=cons.TK_LIMIT_PER_MONTH, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "TRACK_INACTIVE"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.getboolean, section, param, pDefaultValue=cons.TK_TRACK_INACTIVE, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "HIDE_TRAY_ICON"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.getboolean, section, param, pDefaultValue=cons.TK_HIDE_TRAY_ICON, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "LOCKOUT_TYPE"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_CTRL_RES_T, pCheckValue=None, pOverallSuccess=resultValue)
            # read
            param = "WAKEUP_HOUR_INTERVAL"
            resultValue, self._timekprUserConfig[param] = _readAndNormalizeValue(self._timekprUserConfigParser.get, section, param, pDefaultValue=cons.TK_CTRL_RES_T, pCheckValue=None, pOverallSuccess=resultValue)

            # if we could not read some values, save what we could + defaults
            if not resultValue:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "WARNING: some values in user config file (%s) could not be read or new configuration option was introduced, valid values and defaults are used / saved instead" % (self._configFile))
                # init config with partial values read and save what we could
                self.initUserConfiguration(True)

        # clear parser
        self._timekprUserConfigParser.clear()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish load user configuration")

        # result
        return result

    def initUserConfiguration(self, pReuseValues=False):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_INFO, "init default user (%s) configuration" % (self._userName))

        # clear parser
        self._timekprUserConfigParser.clear()

        # save default config
        section = "DOCUMENTATION"
        self._timekprUserConfigParser.add_section(section)
        self._timekprUserConfigParser.set(section, "#### this is the user configuration file for timekpr-next")
        self._timekprUserConfigParser.set(section, "#### if this file cannot be read properly, it will be overwritten with defaults")
        self._timekprUserConfigParser.set(section, "#### all numeric time values are specified in seconds")
        self._timekprUserConfigParser.set(section, "#### days and hours should be configured as per ISO 8601 (i.e. Monday is the first day of week (1-7) and hours are in 24h format (0-23))")

        # add new user section
        section = self._userName
        self._timekprUserConfigParser.add_section(section)
        self._timekprUserConfigParser.set(section, "# this defines which hours are allowed (remove or add hours to limit access), configure limits for start/end minutes for hour in brackets, example: 22[00-15]")
        # set up param
        param = "ALLOWED_HOURS"
        # set hours for all days
        for i in range(1, 7+1):
            self._timekprUserConfigParser.set(section, "%s_%s" % (param, str(i)), self._timekprUserConfig["%s_%s" % (param, str(i))] if pReuseValues else cons.TK_ALLOWED_HOURS)
        # set up param
        param = "ALLOWED_WEEKDAYS"
        self._timekprUserConfigParser.set(section, "# this defines which days of the week a user can use computer (remove or add days to limit access)")
        self._timekprUserConfigParser.set(section, "%s" % (param), self._timekprUserConfig[param] if pReuseValues else cons.TK_ALLOWED_WEEKDAYS)
        # set up param
        param = "LIMITS_PER_WEEKDAYS"
        self._timekprUserConfigParser.set(section, "# this defines allowed time in seconds per week day a user can use the computer")
        self._timekprUserConfigParser.set(section, "%s" % (param), self._timekprUserConfig[param] if pReuseValues else cons.TK_LIMITS_PER_WEEKDAYS)
        # set up param
        param = "LIMIT_PER_WEEK"
        self._timekprUserConfigParser.set(section, "# this defines allowed time per week in seconds (in addition to other limits)")
        self._timekprUserConfigParser.set(section, "%s" % (param), str(self._timekprUserConfig[param]) if pReuseValues else str(cons.TK_LIMIT_PER_WEEK))
        # set up param
        param = "LIMIT_PER_MONTH"
        self._timekprUserConfigParser.set(section, "# this defines allowed time per month in seconds (in addition to other limits)")
        self._timekprUserConfigParser.set(section, "%s" % (param), str(self._timekprUserConfig[param]) if pReuseValues else str(cons.TK_LIMIT_PER_MONTH))
        # set up param
        param = "TRACK_INACTIVE"
        self._timekprUserConfigParser.set(section, "# this defines whether to account sessions which are inactive (locked screen, user switched away from desktop, etc.)")
        self._timekprUserConfigParser.set(section, "%s" % (param), str(self._timekprUserConfig[param]) if pReuseValues else str(cons.TK_TRACK_INACTIVE))
        # set up param
        param = "HIDE_TRAY_ICON"
        self._timekprUserConfigParser.set(section, "# this defines whether to show icon and notifications for user")
        self._timekprUserConfigParser.set(section, "%s" % (param), str(self._timekprUserConfig[param]) if pReuseValues else str(cons.TK_HIDE_TRAY_ICON))
        # set up param
        param = "LOCKOUT_TYPE"
        self._timekprUserConfigParser.set(section, "# this defines user restriction / lockout mode: lock - lock screen, suspend - put computer to sleep, suspendwake - put computer to sleep and wake it up, terminate - terminate sessions")
        self._timekprUserConfigParser.set(section, "%s" % (param), self._timekprUserConfig[param] if pReuseValues else cons.TK_CTRL_RES_T)
        # set up param
        param = "WAKEUP_HOUR_INTERVAL"
        self._timekprUserConfigParser.set(section, "# this defines wakeup hour interval (wakeup itself must be supported by BIOS / UEFI) as hours from;to (format: 0-23), this is effective only when lockout type is suspendwake")
        self._timekprUserConfigParser.set(section, "%s" % (param), self._timekprUserConfig[param] if pReuseValues else "0;23")

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprUserConfigParser.write(fp)

        # clear parser
        self._timekprUserConfigParser.clear()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init default user configuration")

    def saveUserConfiguration(self):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start saving new user (%s) configuration" % (self._userName))

        # init dict
        values = {}

        # allowed weekdays
        param = "ALLOWED_WEEKDAYS"
        values[param] = self._timekprUserConfig[param]
        # allowed hours for every week day
        for rDay in range(1, 7+1):
            param = "ALLOWED_HOURS_%s" % (str(rDay))
            values[param] = self._timekprUserConfig[param]
        # limits per weekdays
        param = "LIMITS_PER_WEEKDAYS"
        values[param] = self._timekprUserConfig[param]
        # limits per week
        param = "LIMIT_PER_WEEK"
        values[param] = str(self._timekprUserConfig[param])
        # limits per month
        param = "LIMIT_PER_MONTH"
        values[param] = str(self._timekprUserConfig[param])
        # track inactive
        param = "TRACK_INACTIVE"
        values[param] = str(self._timekprUserConfig[param])
        # try icon
        param = "HIDE_TRAY_ICON"
        values[param] = str(self._timekprUserConfig[param])
        # restriction / lockout type
        param = "LOCKOUT_TYPE"
        values[param] = self._timekprUserConfig[param]
        # wakeup hour interval
        param = "WAKEUP_HOUR_INTERVAL"
        values[param] = self._timekprUserConfig[param]

        # edit client config file (using alternate method because configparser looses comments in the process)
        _saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish saving new user configuration")

    def getUserAllowedHours(self, pDay=1):
        """Get allowed hours"""
        # this is the dict for hour config
        allowedHours = {}

        # get allowed hours for all of the week days
        param = "ALLOWED_HOURS_%s" % (str(pDay))
        # minutes can be specified in brackets after hour
        if self._timekprUserConfig[param] != "":
            for rHour in self._timekprUserConfig[param].split(";"):
                # determine hour and minutes
                hour, sMin, eMin = _findHourStartEndMinutes(rHour)
                # hour is correct
                if hour is not None:
                    # get our dict done
                    allowedHours[str(hour)] = {cons.TK_CTRL_SMIN: sMin, cons.TK_CTRL_EMIN: eMin}

        # result
        return allowedHours

    def getUserAllowedWeekdays(self):
        """Get allowed week days"""
        # param
        param = "ALLOWED_WEEKDAYS"
        # result
        return [int(result.strip(None)) for result in self._timekprUserConfig[param].split(";") if self._timekprUserConfig[param] != ""]

    def getUserLimitsPerWeekdays(self):
        """Get allowed limits per week day"""
        # param
        param = "LIMITS_PER_WEEKDAYS"
        # result
        return [int(result.strip(None)) for result in self._timekprUserConfig[param].split(";") if self._timekprUserConfig[param] != ""]

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

    def getUserHideTrayIcon(self):
        """Get whether to hide icon and notifications"""
        # result
        return self._timekprUserConfig["HIDE_TRAY_ICON"]

    def getUserLockoutType(self):
        """Get user restriction / lockout type"""
        # result
        return self._timekprUserConfig["LOCKOUT_TYPE"]

    def getUserWakeupHourInterval(self):
        """Get user wakeup hour intervals"""
        # result
        return [result.strip(None) for result in self._timekprUserConfig["WAKEUP_HOUR_INTERVAL"].split(";") if self._timekprUserConfig["WAKEUP_HOUR_INTERVAL"] != ""]

    def getUserLastModified(self):
        """Get last file modification time for user"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setUserAllowedHours(self, pAllowedHours):
        """Set allowed hours"""
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
                    minutes = ("[%i-%i]" % (rHours[hour][cons.TK_CTRL_SMIN], rHours[hour][cons.TK_CTRL_EMIN])) if (rHours[hour][cons.TK_CTRL_SMIN] > 0 or rHours[hour][cons.TK_CTRL_EMIN] < 60) else ""
                    # build up this hour
                    hours.append("%s%s" % (hour, minutes))

            # add this hour to allowable list
            self._timekprUserConfig["ALLOWED_HOURS_%s" % (str(rDay))] = ";".join(hours)

    def setUserAllowedWeekdays(self, pAllowedWeekdays):
        """Set allowed week days"""
        # set up weekdays
        self._timekprUserConfig["ALLOWED_WEEKDAYS"] = ";".join(map(str, pAllowedWeekdays))

    def setUserLimitsPerWeekdays(self, pLimits):
        """Set allowed limits per week day"""
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
        """Set whether to track inactive sessions"""
        # set track inactive
        self._timekprUserConfig["TRACK_INACTIVE"] = bool(pTrackInactive)

    def setUserHideTrayIcon(self, pHideTrayIcon):
        """Set whether to hide icon and notifications"""
        # result
        self._timekprUserConfig["HIDE_TRAY_ICON"] = bool(pHideTrayIcon)

    def setUserLockoutType(self, pLockoutType):
        """Set user restriction / lockout type"""
        # result
        self._timekprUserConfig["LOCKOUT_TYPE"] = pLockoutType

    def setUserWakeupHourInterval(self, pWakeupHourInterval):
        """Set user wake up hours from / to"""
        # result
        self._timekprUserConfig["WAKEUP_HOUR_INTERVAL"] = ";".join(pWakeupHourInterval)


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
        result = _loadAndPrepareConfigFile(self._timekprUserControlParser, self._configFile)
        # value read result
        resultValue = True

        # if we still are fine (and not just checking)
        if not pValidateOnly or (pValidateOnly and result):
            # read config failed, we need to initialize
            if not result:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the user control file (%s) properly, will recreate" % (self._configFile))
                # init config
                self.initUserControl()
                # re-read the file
                self._timekprUserControlParser.read(self._configFile)

            # read
            param = "TIME_SPENT_BALANCE"
            resultValue, self._timekprUserControl[param] = _readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_DAY, pOverallSuccess=resultValue)
            # read
            param = "TIME_SPENT_DAY"
            resultValue, self._timekprUserControl[param] = _readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_DAY, pOverallSuccess=resultValue)
            # read
            param = "TIME_SPENT_WEEK"
            resultValue, self._timekprUserControl[param] = _readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_WEEK, pOverallSuccess=resultValue)
            # read
            param = "TIME_SPENT_MONTH"
            resultValue, self._timekprUserControl[param] = _readAndNormalizeValue(self._timekprUserControlParser.getint, section, param, pDefaultValue=0, pCheckValue=cons.TK_LIMIT_PER_MONTH, pOverallSuccess=resultValue)
            # read
            param = "LAST_CHECKED"
            resultValue, self._timekprUserControl[param] = _readAndNormalizeValue(self._timekprUserControlParser.get, section, param, pDefaultValue=datetime.now().replace(microsecond=0), pCheckValue=None, pOverallSuccess=resultValue)

            # if we could not read some values, save what we could + defaults
            if not resultValue:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "WARNING: some values in user control file (%s) could not be read or new configuration option was introduced, valid values and defaults are used / saved instead" % (self._configFile))
                # save what we could
                self.initUserControl(True)

        # clear parser
        self._timekprUserControlParser.clear()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading user control")

        # result
        return result

    def initUserControl(self, pReuseValues=False):
        """Write new sections of the file"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init user (%s) control" % (self._userName))

        # clear parser
        self._timekprUserControlParser.clear()

        # add new user section
        section = self._userName
        self._timekprUserControlParser.add_section(section)
        # set up param
        param = "TIME_SPENT_BALANCE"
        self._timekprUserControlParser.set(section, "# total spent time balance for today")
        self._timekprUserControlParser.set(section, "%s" % (param), str(self._timekprUserControl[param]) if pReuseValues else "0")
        # set up param
        param = "TIME_SPENT_DAY"
        self._timekprUserControlParser.set(section, "# total actual spent for today")
        self._timekprUserControlParser.set(section, "%s" % (param), str(self._timekprUserControl[param]) if pReuseValues else "0")
        # set up param
        param = "TIME_SPENT_WEEK"
        self._timekprUserControlParser.set(section, "# total spent for this week")
        self._timekprUserControlParser.set(section, "%s" % (param), str(self._timekprUserControl[param]) if pReuseValues else "0")
        # set up param
        param = "TIME_SPENT_MONTH"
        self._timekprUserControlParser.set(section, "# total spent for this month")
        self._timekprUserControlParser.set(section, "%s" % (param), str(self._timekprUserControl[param]) if pReuseValues else "0")
        # set up param
        param = "LAST_CHECKED"
        self._timekprUserControlParser.set(section, "# last update time of the file")
        self._timekprUserControlParser.set(section, "%s" % (param), self._timekprUserControl[param].strftime(cons.TK_DATETIME_FORMAT) if pReuseValues else datetime.now().replace(microsecond=0).strftime(cons.TK_DATETIME_FORMAT))

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprUserControlParser.write(fp)

        # clear parser
        self._timekprUserControlParser.clear()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init user control")

    def saveControl(self):
        """Save configuration"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start save user (%s) control" % (self._userName))

        # init dict
        values = {}

        # spent day (including bonuses)
        param = "TIME_SPENT_BALANCE"
        values[param] = str(int(self._timekprUserControl[param]))
        # spent day
        param = "TIME_SPENT_DAY"
        values[param] = str(int(self._timekprUserControl[param]))
        # spent week
        param = "TIME_SPENT_WEEK"
        values[param] = str(int(self._timekprUserControl[param]))
        # spent month
        param = "TIME_SPENT_MONTH"
        values[param] = str(int(self._timekprUserControl[param]))
        # last checked
        param = "LAST_CHECKED"
        values[param] = self._timekprUserControl[param].strftime(cons.TK_DATETIME_FORMAT)

        # edit control file (using alternate method because configparser looses comments in the process)
        _saveConfigFile(self._configFile, values)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish save user control")

    def getUserSavedDateComponentChanges(self, pCheckDate):
        """Determine whether days / weeks / months changed since last change date in file"""
        # year changed
        yearChanged = (self.getUserLastChecked().date().year != pCheckDate.date().year)
        # month changed
        monthChanged = (yearChanged or self.getUserLastChecked().date().month != pCheckDate.date().month)
        # week changed
        weekChanged = (monthChanged or self.getUserLastChecked().date().isocalendar()[1] != pCheckDate.date().isocalendar()[1])
        # day changed
        dayChanged = (weekChanged or self.getUserLastChecked().date() != pCheckDate.date())

        # result (day / week / month)
        return dayChanged, weekChanged, monthChanged

    def getUserTimeSpentBalance(self):
        """Get time spent for day (including bonues)"""
        # result
        return self._timekprUserControl["TIME_SPENT_BALANCE"]

    def getUserTimeSpentDay(self):
        """Get time spent for day"""
        # result
        return self._timekprUserControl["TIME_SPENT_DAY"]

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

    def setUserTimeSpentBalance(self, pTimeSpent):
        """Set time spent for day (including bonuses)"""
        # result
        self._timekprUserControl["TIME_SPENT_BALANCE"] = pTimeSpent

    def setUserTimeSpentDay(self, pTimeSpentDay):
        """Set time spent for day"""
        # result
        self._timekprUserControl["TIME_SPENT_DAY"] = pTimeSpentDay

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

    def __init__(self):
        """Initialize config"""
        # config
        self._timekprClientConfig = {}
        # get home
        self._userHome = os.path.expanduser("~")

        # set up logging
        logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_INFO, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: cons.TK_LOG_OWNER_CLIENT, cons.TK_LOG_U: getpass.getuser()}
        # set up logging
        log.setLogging(logging)

        # set up log file name
        self._timekprClientConfig["TIMEKPR_LOGFILE_DIR"] = logging[cons.TK_LOG_D]

        log.log(cons.TK_LOG_LEVEL_INFO, "start initializing client configuration manager")

        # in dev
        self._configDirPrefix = os.getcwd() if cons.TK_DEV_ACTIVE else ""

        # main config
        self._timekprClientConfig["TIMEKPR_MAIN_CONFIG_DIR"] = os.path.join(self._configDirPrefix, (cons.TK_MAIN_CONFIG_DIR_DEV if cons.TK_DEV_ACTIVE else cons.TK_MAIN_CONFIG_DIR))
        self._configMainFile = os.path.join(self._timekprClientConfig["TIMEKPR_MAIN_CONFIG_DIR"], cons.TK_MAIN_CONFIG_FILE)

        # config
        self._configFile = os.path.join(self._userHome, ".config/timekpr", cons.TK_MAIN_CONFIG_FILE)

        # config parser
        self._timekprClientConfigParser = configparser.ConfigParser(allow_no_value=True)
        self._timekprClientConfigParser.optionxform = str

        log.log(cons.TK_LOG_LEVEL_INFO, "finish initializing client configuration manager")

    def __del__(self):
        """De-initialize config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "de-initialize client configuration manager")

    def loadClientConfiguration(self):
        """Read main timekpr config file"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start loading client configuration")

        # get directories from main config
        if "TIMEKPR_SHARED_DIR" not in self._timekprClientConfig:
            # load main config to get directories
            self.loadMinimalClientMainConfig()
            # clear out cp, we don't need to store all condfigs in minimal case
            self._timekprClientConfigParser.clear()

        # try to load config file
        result = _loadAndPrepareConfigFile(self._timekprClientConfigParser, self._configFile)
        # value read result
        resultValue = True

        # read config failed, we need to initialize
        if not result:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configFile))
            # write correct config file
            self.initClientConfig()
            # re-read the file
            self._timekprClientConfigParser.read(self._configFile)

        # config load time
        self._clientConfigModTime = self.getClientLastModified()

        # directory section
        section = "CONFIG"
        # read
        param = "SHOW_LIMIT_NOTIFICATION"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getboolean, section, param, pDefaultValue=True, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "SHOW_ALL_NOTIFICATIONS"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getboolean, section, param, pDefaultValue=True, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "USE_SPEECH_NOTIFICATIONS"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getboolean, section, param, pDefaultValue=False, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "SHOW_SECONDS"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getboolean, section, param, pDefaultValue=False, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "NOTIFICATION_TIMEOUT"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getint, section, param, pDefaultValue=cons.TK_CL_NOTIF_TMO, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "NOTIFICATION_TIMEOUT_CRITICAL"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getint, section, param, pDefaultValue=cons.TK_CL_NOTIF_CRIT_TMO, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "USE_NOTIFICATION_SOUNDS"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getboolean, section, param, pDefaultValue=False, pCheckValue=None, pOverallSuccess=resultValue)
        # read
        param = "LOG_LEVEL"
        resultValue, self._timekprClientConfig[param] = _readAndNormalizeValue(self._timekprClientConfigParser.getint, section, param, pDefaultValue=cons.TK_LOG_LEVEL_INFO, pCheckValue=None, pOverallSuccess=resultValue)

        # if we could not read some values, save what we could + defaults
        if not resultValue:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "WARNING: some values in client confguration file (%s) could not be read or new configuration option was introduced, valid values and defaults are used / saved instead" % (self._configFile))
            # save what we could
            self.initClientConfig(True)

        # check whether sound is supported
        self._timekprClientConfig["USE_NOTIFICATION_SOUNDS_SUPPORTED"] = (os.path.isfile(cons.TK_CL_NOTIF_SND_FILE_WARN) and os.path.isfile(cons.TK_CL_NOTIF_SND_FILE_CRITICAL))

        # check whether speech is supported
        try:
            # try importing speech
            from espeak import espeak
            # supported
            self._timekprClientConfig["USE_SPEECH_NOTIFICATIONS_SUPPORTED"] = True
        except:
            # NOT supported
            self._timekprClientConfig["USE_SPEECH_NOTIFICATIONS_SUPPORTED"] = False

        # clear parser
        self._timekprClientConfigParser.clear()

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
        result = _loadAndPrepareConfigFile(self._timekprClientConfigParser, self._configMainFile, True)
        # if file cannot be read
        if not result:
            # default value
            value = cons.TK_SHARED_DIR
        else:
            # read file
            result, value = _readAndNormalizeValue(self._timekprClientConfigParser.get, section, param, pDefaultValue=cons.TK_SHARED_DIR, pCheckValue=None, pOverallSuccess=True)

        # problems loading default config
        if not result:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: could not parse the configuration file (%s) properly, will use default values" % (self._configMainFile))

        # finalize directory
        self._timekprClientConfig[param] = os.path.join(self._configDirPrefix, (cons.TK_SHARED_DIR_DEV if cons.TK_DEV_ACTIVE else value))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish loading minimal main configuration")

        # result
        return True

    def initClientConfig(self, pReuseValues=False):
        """Write new config"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start init client configuration")

        # directory name
        dirName = os.path.dirname(self._configFile)

        # check file
        if not os.path.isdir(dirName):
            # make it
            os.makedirs(dirName)

        # clear parser
        self._timekprClientConfigParser.clear()

        # add new user section
        section = "CONFIG"
        self._timekprClientConfigParser.add_section(section)
        # set up param
        param = "SHOW_LIMIT_NOTIFICATION"
        self._timekprClientConfigParser.set(section, "# whether to show limit change notification")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else "True")
        # set up param
        param = "SHOW_ALL_NOTIFICATIONS"
        self._timekprClientConfigParser.set(section, "# whether to show all notifications or important ones only")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else "True")
        # set up param
        param = "SHOW_SECONDS"
        self._timekprClientConfigParser.set(section, "# whether to show seconds in label (if DE supports it)")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else "True")
        # set up param
        param = "USE_SPEECH_NOTIFICATIONS"
        self._timekprClientConfigParser.set(section, "# whether to use speech notifications")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else "False")
        # set up param
        param = "NOTIFICATION_TIMEOUT"
        self._timekprClientConfigParser.set(section, "# how long regular notifications should be displayed (in seconds)")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else str(cons.TK_CL_NOTIF_TMO))
        # set up param
        param = "NOTIFICATION_TIMEOUT_CRITICAL"
        self._timekprClientConfigParser.set(section, "# how long critical notifications should be displayed (in seconds)")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else str(cons.TK_CL_NOTIF_CRIT_TMO))
        # set up param
        param = "USE_NOTIFICATION_SOUNDS"
        self._timekprClientConfigParser.set(section, "# use notification sounds for notifications")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else "False")
        # set up param
        param = "LOG_LEVEL"
        self._timekprClientConfigParser.set(section, "# user logging level (1 - normal, 2 - debug, 3 - extra debug)")
        self._timekprClientConfigParser.set(section, "%s" % (param), str(self._timekprClientConfig[param]) if pReuseValues else str(cons.TK_LOG_LEVEL_INFO))

        # save the file
        with open(self._configFile, "w") as fp:
            self._timekprClientConfigParser.write(fp)

        # clear parser
        self._timekprClientConfigParser.clear()

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init client configuration")

    def saveClientConfig(self):
        """Save configuration (called from GUI)"""
        log.log(cons.TK_LOG_LEVEL_INFO, "start save client config")

        # init dict
        values = {}

        # first limit notification
        param = "SHOW_LIMIT_NOTIFICATION"
        values[param] = str(self._timekprClientConfig[param])
        # all notifications
        param = "SHOW_ALL_NOTIFICATIONS"
        values[param] = str(self._timekprClientConfig[param])
        # speech notifications
        param = "USE_SPEECH_NOTIFICATIONS"
        values[param] = str(self._timekprClientConfig[param])
        # show seconds
        param = "SHOW_SECONDS"
        values[param] = str(self._timekprClientConfig[param])
        # timeout for notifications
        param = "NOTIFICATION_TIMEOUT"
        values[param] = str(self._timekprClientConfig[param])
        # timeout for critical notifications
        param = "NOTIFICATION_TIMEOUT_CRITICAL"
        values[param] = str(self._timekprClientConfig[param])
        # notification sounds
        param = "USE_NOTIFICATION_SOUNDS"
        values[param] = str(self._timekprClientConfig[param])
        # last checked
        param = "LOG_LEVEL"
        values[param] = str(self._timekprClientConfig[param])

        # edit control file (using alternate method because configparser looses comments in the process)
        _saveConfigFile(self._configFile, values)

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

    def getIsNotificationSoundSupported(self):
        """Whether notification sounds are supported"""
        # result
        return self._timekprClientConfig["USE_NOTIFICATION_SOUNDS_SUPPORTED"]

    def getIsNotificationSpeechSupported(self):
        """Whether speech notifications are supported"""
        # result
        return self._timekprClientConfig["USE_SPEECH_NOTIFICATIONS_SUPPORTED"]

    def getClientShowLimitNotifications(self):
        """Get whether to show frst notification"""
        # result
        return self._timekprClientConfig["SHOW_LIMIT_NOTIFICATION"]

    def getClientShowAllNotifications(self):
        """Get whether to show all notifications"""
        # result
        return self._timekprClientConfig["SHOW_ALL_NOTIFICATIONS"]

    def getClientUseSpeechNotifications(self):
        """Get whether to use speech"""
        # result
        return self._timekprClientConfig["USE_SPEECH_NOTIFICATIONS"]

    def getClientShowSeconds(self):
        """Get whether to show seconds"""
        # result
        return self._timekprClientConfig["SHOW_SECONDS"]

    def getClientNotificationTimeout(self):
        """Get timeout for regular notifications"""
        # result
        return self._timekprClientConfig["NOTIFICATION_TIMEOUT"]

    def getClientNotificationTimeoutCritical(self):
        """Get timeout for critical notifications"""
        # result
        return self._timekprClientConfig["NOTIFICATION_TIMEOUT_CRITICAL"]

    def getClientUseNotificationSound(self):
        """Get whether to show use sound notifications"""
        # result
        return self._timekprClientConfig["USE_NOTIFICATION_SOUNDS"]

    def getClientLogLevel(self):
        """Get client log level"""
        # result
        return self._timekprClientConfig["LOG_LEVEL"]

    def getTimekprSharedDir(self):
        """Get shared dir"""
        # result
        return self._timekprClientConfig["TIMEKPR_SHARED_DIR"]

    def getClientLogfileDir(self):
        """Get shared dir"""
        # result
        return self._timekprClientConfig["TIMEKPR_LOGFILE_DIR"]

    def getClientLastModified(self):
        """Get last file modification time for user"""
        # result
        return datetime.fromtimestamp(os.path.getmtime(self._configFile))

    def setIsNotificationSoundSupported(self, pIsSupported):
        """Whether notification sounds are supported"""
        # result
        self._timekprClientConfig["USE_NOTIFICATION_SOUNDS_SUPPORTED"] = pIsSupported

    def setClientShowLimitNotifications(self, pClientShowLimitNotification):
        """Set whether to show frst notification"""
        # set
        self._timekprClientConfig["SHOW_LIMIT_NOTIFICATION"] = pClientShowLimitNotification

    def setClientShowAllNotifications(self, pClientShowAllNotifications):
        """Set whether to show all notifications"""
        # set
        self._timekprClientConfig["SHOW_ALL_NOTIFICATIONS"] = pClientShowAllNotifications

    def setClientUseSpeechNotifications(self, pClientUseSpeechNotifications):
        """Set whether to use speech"""
        # set
        self._timekprClientConfig["USE_SPEECH_NOTIFICATIONS"] = pClientUseSpeechNotifications

    def setClientShowSeconds(self, pClientShowSeconds):
        """Set whether to show seconds"""
        # set
        self._timekprClientConfig["SHOW_SECONDS"] = pClientShowSeconds

    def setClientNotificationTimeout(self, pClientNotificationTimeout):
        """Set timeout for regular notifications"""
        # set
        self._timekprClientConfig["NOTIFICATION_TIMEOUT"] = pClientNotificationTimeout

    def setClientNotificationTimeoutCritical(self, pClientNotificationTimeoutCritical):
        """Set timeout for critical notifications"""
        # set
        self._timekprClientConfig["NOTIFICATION_TIMEOUT_CRITICAL"] = pClientNotificationTimeoutCritical

    def setClientUseNotificationSound(self, pClientUseNotificationSound):
        """Set whether to use sound notifications"""
        # set
        self._timekprClientConfig["USE_NOTIFICATION_SOUNDS"] = pClientUseNotificationSound

    def setClientLogLevel(self, pClientLogLevel):
        """Set client log level"""
        # set
        self._timekprClientConfig["LOG_LEVEL"] = pClientLogLevel
