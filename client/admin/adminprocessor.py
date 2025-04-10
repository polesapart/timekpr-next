"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import os
import getpass
from os import geteuid

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.dbus.administration import timekprAdminConnector
from timekpr.common.utils.config import timekprConfig
from timekpr.common.constants import messages as msg
from timekpr.common.utils.misc import findHourStartEndMinutes as findHourStartEndMinutes
from timekpr.common.utils.misc import splitConfigValueNameParam as splitConfigValueNameParam


class timekprAdminClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self):
        """Initialize admin client"""
        # get our connector
        self._timekprAdminConnector = timekprAdminConnector()

        # main object for GUI
        self._adminGUI = None

    def startTimekprAdminClient(self, *args):
        """Start up timekpr admin (choose gui or cli and start this up)"""
        # check whether we need CLI or GUI
        lastParam = args[len(args)-1]
        timekprForceCLI = False

        # configuration init
        _timekprConfig = timekprConfig()
        # load config
        _timekprConfig.loadMainConfiguration()

        # init logging
        log.setLogging(_timekprConfig.getTimekprLogLevel(), cons.TK_LOG_TEMP_DIR, (cons.TK_LOG_OWNER_ADMIN_SU if geteuid() == 0 else cons.TK_LOG_OWNER_ADMIN), getpass.getuser())

        # check for script
        if ("/timekpra" in lastParam or "timekpra.py" in lastParam):
            # whether we have X running or wayland?
            timekprX11Available = os.getenv("DISPLAY") is not None
            timekprWaylandAvailable = os.getenv("WAYLAND_DISPLAY") is not None
            timekprMirAvailable = os.getenv("MIR_SOCKET") is not None

            # if we are required to run graphical thing
            if (timekprX11Available or timekprWaylandAvailable or timekprMirAvailable):
                # resource dir
                _resourcePathGUI = os.path.join(_timekprConfig.getTimekprSharedDir(), "client/forms")
                # use GUI
                from timekpr.client.gui.admingui import timekprAdminGUI
                # load GUI and process from there
                self._adminGUI = timekprAdminGUI(cons.TK_VERSION, _resourcePathGUI, getpass.getuser())
                # start GUI
                self._adminGUI.startAdminGUI()
            # nor X nor wayland are available
            else:
                # print to console
                log.consoleOut("%s\n" % (msg.getTranslation("TK_MSG_CONSOLE_GUI_NOT_AVAILABLE")))
                # forced CLI"
                timekprForceCLI = True
        else:
            # CLI
            timekprForceCLI = True

        # for CLI connections
        if timekprForceCLI:
            # connect
            self._timekprAdminConnector.initTimekprConnection(True)
            # connected?
            if self._timekprAdminConnector.isConnected()[1]:
                # use CLI
                # validate possible parameters and their values, when fine - execute them as well
                self.checkAndExecuteAdminCommands(*args)
                log.flushLogFile()

    # --------------- initialization / helper methods --------------- #

    def finishTimekpr(self, signal=None, frame=None):
        """Exit timekpr admin GUI gracefully"""
        if self._adminGUI is not None:
            # finish main thread on GUI`
            self._adminGUI.finishTimekpr(signal, frame)

    # --------------- parameter validation methods --------------- #

    def checkAndExecuteAdminCommands(self, *args):
        """Init connection to timekpr dbus server"""
        # initial param len
        paramIdx = 0
        paramLen = len(args)
        adminCmdIncorrect = False
        tmpIdx = 0

        # determine parameter offset
        for rArg in args:
            # count offset
            tmpIdx += 1
            # check for script
            if "/timekpra" in rArg or "timekpra.py" in rArg:
                paramIdx = tmpIdx

        # this gets the command itself (args[0] is the script name)
        adminCmd = args[paramIdx] if paramLen > paramIdx else "timekpra"

        # now based on params check them out
        # this gets saved user list from the server
        if adminCmd == "--help":
            # fine
            pass
        # this gets saved user list from the server
        elif adminCmd == "--userlist":
            # check param len
            if paramLen != paramIdx + 1:
                # fail
                adminCmdIncorrect = True
            else:
                # get list
                result, message, userList = self._timekprAdminConnector.getUserList()

                # process
                if result == 0:
                    # process
                    self.printUserList(userList)
                else:
                    # log error
                    log.consoleOut(message)
        # this gets user configuration from the server
        elif adminCmd == "--userinfo":
            # check param len
            if paramLen != paramIdx + 2:
                # fail
                adminCmdIncorrect = True
            else:
                # get user config
                result, message, userConfig = self._timekprAdminConnector.getUserConfigurationAndInformation(args[paramIdx+1], cons.TK_CL_INF_FULL)

                # process
                if result == 0:
                    # process
                    self.printUserConfig(args[paramIdx+1], userConfig)
                else:
                    # log error
                    log.consoleOut(message)
        # this gets user configuration from the server
        elif adminCmd == "--userinfort":
            # check param len
            if paramLen != paramIdx + 2:
                # fail
                adminCmdIncorrect = True
            else:
                # get user config
                result, message, userConfig = self._timekprAdminConnector.getUserConfigurationAndInformation(args[paramIdx+1], cons.TK_CL_INF_RT)

                # process
                if result == 0:
                    # process
                    self.printUserConfig(args[paramIdx+1], userConfig)
                else:
                    # log error
                    log.consoleOut(message)
        # this sets allowed days for the user
        elif adminCmd == "--setalloweddays":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetAllowedDays(args[paramIdx+1], args[paramIdx+2])
        # this sets allowed hours per specified day or ALL for every day
        elif adminCmd == "--setallowedhours":
            # check param len
            if paramLen != paramIdx + 4:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetAllowedHours(args[paramIdx+1], args[paramIdx+2], args[paramIdx+3])
        # this sets time limits per allowed days
        elif adminCmd == "--settimelimits":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLimits(args[paramIdx+1], args[paramIdx+2])
        # this sets time limits per week
        elif adminCmd == "--settimelimitweek":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLimitWeek(args[paramIdx+1], args[paramIdx+2])
        # this sets time limits per month
        elif adminCmd == "--settimelimitmonth":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLimitMonth(args[paramIdx+1], args[paramIdx+2])
        # this sets whether to track inactive user sessions
        elif adminCmd == "--settrackinactive":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTrackInactive(args[paramIdx+1], args[paramIdx+2])
        # this sets whether to show tray icon
        elif adminCmd == "--sethidetrayicon":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetHideTrayIcon(args[paramIdx+1], args[paramIdx+2])
        # this sets lockout type for the user
        elif adminCmd == "--setlockouttype":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetLockoutType(args[paramIdx+1], args[paramIdx+2])
        # this sets whether PlayTime is enabled for user
        elif adminCmd == "--setplaytimeenabled":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeEnabled(args[paramIdx+1], args[paramIdx+2])
        # this sets playtime override for user
        elif adminCmd == "--setplaytimelimitoverride":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeLimitOverride(args[paramIdx+1], args[paramIdx+2])
        # this sets playtime allowed during unaccounted intervals for user
        elif adminCmd == "--setplaytimeunaccountedintervalsflag":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeUnaccountedIntervalsEnabled(args[paramIdx+1], args[paramIdx+2])
        # this sets allowed days for PlayTime for the user
        elif adminCmd == "--setplaytimealloweddays":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeAllowedDays(args[paramIdx+1], args[paramIdx+2])
        # this sets PlayTime limits for allowed days for the user
        elif adminCmd == "--setplaytimelimits":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeLimits(args[paramIdx+1], args[paramIdx+2])
        # this sets PlayTime activities for the user
        elif adminCmd == "--setplaytimeactivities":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeActivities(args[paramIdx+1], args[paramIdx+2])
        # this sets time left for the user at current moment
        elif adminCmd == "--settimeleft":
            # check param len
            if paramLen != paramIdx + 4:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLeft(args[paramIdx+1], args[paramIdx+2], args[paramIdx+3])
        # this sets time left for the user at current moment
        elif adminCmd == "--setplaytimeleft":
            # check param len
            if paramLen != paramIdx + 4:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetPlayTimeLeft(args[paramIdx+1], args[paramIdx+2], args[paramIdx+3])
        else:
            # out
            adminCmdIncorrect = True

        # check whether command is supported
        if (adminCmd not in cons.TK_USER_ADMIN_COMMANDS and adminCmd not in cons.TK_ADMIN_COMMANDS) or adminCmd == "--help" or adminCmdIncorrect:
            # fail
            if adminCmdIncorrect:
                log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_COMMAND_INCORRECT"), *args, "\n")

            # log notice
            log.consoleOut("%s\n*) %s\n*) %s\n*) %s\n" % (
                msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTICE_HEAD"),
                msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTICE_TIME"),
                msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTICE_HOURS"),
                msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTICE_DAYS"))
            )
            # log usage notes text
            log.consoleOut("%s\n" % (msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTES")))
            # initial order
            cmds = ["--help", "--userlist", "--userinfo"]
            # print initial commands as first
            for rCmd in cmds:
                log.consoleOut(" ", rCmd, cons.TK_USER_ADMIN_COMMANDS[rCmd], "\n")

            # print help
            for rCmd, rCmdDesc in cons.TK_USER_ADMIN_COMMANDS.items():
                # do not print already known commands
                if rCmd not in cmds:
                    log.consoleOut(" ", rCmd, rCmdDesc, "\n")

    # --------------- parameter execution methods --------------- #

    def printUserList(self, pUserList):
        """Format and print userlist"""
        # print to console
        log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_USERS_TOTAL", len(pUserList)))
        # loop and print
        for rUser in pUserList:
            log.consoleOut(rUser[0])

    def printUserConfig(self, pUserName, pPrintUserConfig):
        """Format and print user config"""
        # print to console
        log.consoleOut("# %s" % (msg.getTranslation("TK_MSG_CONSOLE_CONFIG_FOR") % (pUserName)))
        # loop and print the same format as ppl will use to set that
        for rUserKey, rUserConfig in pPrintUserConfig.items():
            # join the lists
            if rUserKey in ("ALLOWED_WEEKDAYS", "LIMITS_PER_WEEKDAYS", "PLAYTIME_ALLOWED_WEEKDAYS", "PLAYTIME_LIMITS_PER_WEEKDAYS"):
                # print join
                log.consoleOut("%s: %s" % (rUserKey, ";".join(list(map(str, rUserConfig)))))
            # join the lists
            elif "ALLOWED_HOURS_" in rUserKey:
                # hrs
                hrs = ""
                # print join
                if len(rUserConfig) > 0:
                    # process hours
                    for rUserHour in sorted(list(map(int, rUserConfig))):
                        # unaccounted hour
                        uacc = "!" if rUserConfig[str(rUserHour)][cons.TK_CTRL_UACC] else ""
                        # get config per hr
                        hr = "%s" % (rUserHour) if rUserConfig[str(rUserHour)][cons.TK_CTRL_SMIN] <= 0 and rUserConfig[str(rUserHour)][cons.TK_CTRL_EMIN] >= 60 else "%s[%s-%s]" % (rUserHour, rUserConfig[str(rUserHour)][cons.TK_CTRL_SMIN], rUserConfig[str(rUserHour)][cons.TK_CTRL_EMIN])
                        # empty
                        hrs = "%s%s" % (uacc, hr) if hrs == "" else "%s;%s%s" % (hrs, uacc, hr)
                log.consoleOut("%s: %s" % (rUserKey, hrs))
            elif rUserKey in ("TRACK_INACTIVE", "HIDE_TRAY_ICON", "PLAYTIME_ENABLED", "PLAYTIME_LIMIT_OVERRIDE_ENABLED", "PLAYTIME_UNACCOUNTED_INTERVALS_ENABLED"):
                log.consoleOut("%s: %s" % (rUserKey, bool(rUserConfig)))
            elif rUserKey in ("PLAYTIME_ACTIVITIES"):
                # result
                result = ""
                # loop thorhough activities
                for rActArr in rUserConfig:
                    # activity
                    act = "%s[%s]" % (rActArr[0], rActArr[1]) if rActArr[1] != "" else "%s" % (rActArr[0])
                    # gather activities
                    result = "%s" % (act) if result == "" else "%s;%s" % (result, act)
                log.consoleOut("%s: %s" % (rUserKey, result))
            else:
                log.consoleOut("%s: %s" % (rUserKey, str(rUserConfig)))

    def processSetAllowedDays(self, pUserName, pDayList):
        """Process allowed days"""
        # defaults
        dayMap = []
        result = 0

        # day map
        try:
            # try to parse parameters
            dayMap = pDayList.split(";")
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setAllowedDays(pUserName, dayMap)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Process allowed hours"""
        # this is the dict for hour config
        allowedHours = {}
        result = 0

        # allowed hours
        try:
            # check hours
            for rHour in str(pHourList).split(";"):
                # get hours and minutes
                hour, sMin, eMin, uacc = findHourStartEndMinutes(rHour)
                # raise any error in case we can not get parsing right
                if hour is None:
                    # raise
                    raise ValueError("this does not compute")
                # set hours
                allowedHours[str(hour)] = {cons.TK_CTRL_SMIN: sMin, cons.TK_CTRL_EMIN: eMin, cons.TK_CTRL_UACC: uacc}
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setAllowedHours(pUserName, pDayNumber, allowedHours)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetTimeLimits(self, pUserName, pDayLimits):
        """Process time limits for days"""
        # defaults
        dayLimits = []
        result = 0

        # day limists
        try:
            # allow empty limits too
            if str(pDayLimits) != "":
                # try to parse parameters
                dayLimits = list(map(int, pDayLimits.split(";")))
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTimeLimitForDays(pUserName, dayLimits)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetTimeLimitWeek(self, pUserName, pTimeLimitWeek):
        """Process time limits for week"""
        # defaults
        weekLimit = 0
        result = 0

        # week limit
        try:
            # try to parse parameters
            weekLimit = int(pTimeLimitWeek)
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTimeLimitForWeek(pUserName, weekLimit)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetTimeLimitMonth(self, pUserName, pTimeLimitMonth):
        """Process time limits for month"""
        # defaults
        monthLimit = 0
        result = 0

        # week limit
        try:
            # try to parse parameters
            monthLimit = int(pTimeLimitMonth)
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTimeLimitForMonth(pUserName, monthLimit)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetTrackInactive(self, pUserName, pTrackInactive):
        """Process track inactive"""
        # defaults
        trackInactive = None
        result = 0

        # check
        if str(pTrackInactive).lower() not in ("true", "false"):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            trackInactive = True if str(pTrackInactive).lower() == "true" else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTrackInactive(pUserName, trackInactive)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetHideTrayIcon(self, pUserName, pHideTrayIcon):
        """Process hide tray icon"""
        # defaults
        hideTrayIcon = None
        result = 0

        # check
        if str(pHideTrayIcon).lower() not in ("true", "false"):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            hideTrayIcon = True if str(pHideTrayIcon).lower() == "true" else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setHideTrayIcon(pUserName, hideTrayIcon)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetLockoutType(self, pUserName, pLockoutType):
        """Process lockout type"""
        # defaults
        result = 0
        # parse lockout
        lockout = pLockoutType.split(";")
        lockoutType = lockout[0]
        lockoutWakeFrom = lockout[1] if len(lockout) == 3 else '0'
        lockoutWakeTo = lockout[2] if len(lockout) == 3 else '23'

        # check
        if lockoutType not in (cons.TK_CTRL_RES_L, cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W, cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify one of these: %s, %s, %s, %s, %s, %s" % (cons.TK_CTRL_RES_L, cons.TK_CTRL_RES_S, cons.TK_CTRL_RES_W, cons.TK_CTRL_RES_T, cons.TK_CTRL_RES_K, cons.TK_CTRL_RES_D))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setLockoutType(pUserName, lockoutType, lockoutWakeFrom, lockoutWakeTo)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetTimeLeft(self, pUserName, pOperation, pLimit):
        """Process time left"""
        # defaults
        limit = 0
        result = 0

        # limit
        try:
            # try to parse parameters
            limit = int(pLimit)
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTimeLeft(pUserName, pOperation, limit)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    # --------------- parameter execution methods for PlayTime --------------- #

    def processSetPlayTimeEnabled(self, pUserName, pPlayTimeEnabled):
        """Process PlayTime enabled flag"""
        # defaults
        isPlayTimeEnabled = None
        result = 0

        # check
        if str(pPlayTimeEnabled).lower() not in ("true", "false"):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            isPlayTimeEnabled = True if str(pPlayTimeEnabled).lower() == "true" else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeEnabled(pUserName, isPlayTimeEnabled)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeLimitOverride(self, pUserName, pPlayTimeLimitOverride):
        """Process PlayTime override flag"""
        # defaults
        isPlayTimeLimitOverride = None
        result = 0

        # check
        if str(pPlayTimeLimitOverride).lower() not in ("true", "false"):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            isPlayTimeLimitOverride = True if str(pPlayTimeLimitOverride).lower() == "true" else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeLimitOverride(pUserName, isPlayTimeLimitOverride)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeUnaccountedIntervalsEnabled(self, pUserName, pPlayTimeUnaccountedIntervalsEnabled):
        """Process PlayTime allowed during unaccounted intervals flag"""
        # defaults
        isPlayTimeUnaccountedIntervalsEnabled = None
        result = 0

        # check
        if str(pPlayTimeUnaccountedIntervalsEnabled).lower() not in ("true", "false"):
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            isPlayTimeUnaccountedIntervalsEnabled = True if str(pPlayTimeUnaccountedIntervalsEnabled).lower() == "true" else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeUnaccountedIntervalsEnabled(pUserName, isPlayTimeUnaccountedIntervalsEnabled)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeAllowedDays(self, pUserName, pPlayTimeDayList):
        """Process allowed days for PlayTime"""
        # defaults
        dayMap = []
        result = 0

        # day map
        try:
            # try to parse parameters
            dayMap = pPlayTimeDayList.split(";")
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeAllowedDays(pUserName, dayMap)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeLimits(self, pUserName, pPlayTimeDayLimits):
        """Process time limits for allowed days for PlayTime"""
        # defaults
        dayLimits = []
        result = 0

        # day limists
        try:
            # allow empty limits too
            if pPlayTimeDayLimits != "":
                # try to parse parameters
                dayLimits = list(map(int, pPlayTimeDayLimits.split(";")))
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeLimitsForDays(pUserName, dayLimits)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeActivities(self, pUserName, pPlayTimeActivities):
        """Process PlayTime activities"""
        # defaults
        playTimeActivities = []
        result = 0

        # day limists
        try:
            # ## try to parse parameters ##
            if pPlayTimeActivities != "":
                # split activities
                for rAct in pPlayTimeActivities.split(";"):
                    # try parsing the names
                    mask, description = splitConfigValueNameParam(rAct)
                    # raise any error in case we can not get parsing right
                    if mask is None:
                        # raise
                        raise ValueError("this does not compute")
                    # set up activity list
                    playTimeActivities.append([mask, description])
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeActivities(pUserName, playTimeActivities)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)

    def processSetPlayTimeLeft(self, pUserName, pOperation, pLimit):
        """Process time left"""
        # defaults
        limit = 0
        result = 0

        # limit
        try:
            # try to parse parameters
            limit = int(pLimit)
        except Exception as ex:
            # fail
            result = -1
            message = msg.getTranslation("TK_MSG_PARSE_ERROR") % (str(ex))

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setPlayTimeLeft(pUserName, pOperation, limit)

        # process
        if result != 0:
            # log error
            log.consoleOut(message)
