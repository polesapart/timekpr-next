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


class timekprAdminClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self, pIsDevActive=False):
        """Initialize admin client"""
        # dev
        self._isDevActive = pIsDevActive

        # get our connector
        self._timekprAdminConnector = timekprAdminConnector(self._isDevActive)

        # main object for GUI
        self._adminGUI = None

    def startTimekprAdminClient(self, *args):
        """Start up timekpr admin (choose gui or cli and start this up)"""
        # check whether we need CLI or GUI
        lastParam = args[len(args)-1]
        timekprForceCLI = False

        # check for script
        if ("/timekpra" in lastParam or "timekpra.py" in lastParam):
            # whether we have X running or wayland?
            timekprX11Available = os.getenv("DISPLAY") is not None
            timekprWaylandAvailable = os.getenv("WAYLAND_DISPLAY") is not None
            timekprMirAvailable = os.getenv("MIR_SOCKET") is not None

            # if we are required to run graphical thing
            if (timekprX11Available or timekprWaylandAvailable or timekprMirAvailable):
                # save logging for later use in classes down tree
                self._logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_DEBUG, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: (cons.TK_LOG_OWNER_ADMIN_SU if geteuid() == 0 else cons.TK_LOG_OWNER_ADMIN), cons.TK_LOG_U: getpass.getuser()}
                # logging init
                log.setLogging(self._logging)

                # configuration init
                _timekprConfigManager = timekprConfig(pIsDevActive=self._isDevActive, pLog=self._logging)
                # load config
                _timekprConfigManager.loadMainConfiguration()
                # resource dir
                _resourcePathGUI = os.path.join(_timekprConfigManager.getTimekprSharedDir(), "client/forms")

                # use GUI
                from timekpr.client.gui.admingui import timekprAdminGUI
                # load GUI and process from there
                self._adminGUI = timekprAdminGUI(cons.TK_VERSION, _resourcePathGUI, getpass.getuser(), self._isDevActive)
            # nor X nor wayland are available
            else:
                # print to console
                log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_GUI_NOT_AVAILABLE") + "\n")
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
        elif adminCmd == "--userconfig":
            # check param len
            if paramLen != paramIdx + 2:
                # fail
                adminCmdIncorrect = True
            else:
                # get user config
                result, message, userConfig = self._timekprAdminConnector.getUserConfig(args[paramIdx+1])

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

        # this sets time left for the user at current moment
        elif adminCmd == "--settimeleft":
            # check param len
            if paramLen != paramIdx + 4:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLeft(args[paramIdx+1], args[paramIdx+2], args[paramIdx+3])

        else:
            # out
            adminCmdIncorrect = True

        # check whether command is supported
        if (adminCmd not in cons.TK_USER_ADMIN_COMMANDS and adminCmd not in cons.TK_ADMIN_COMMANDS) or adminCmd == "--help" or adminCmdIncorrect:
            # fail
            if adminCmdIncorrect:
                log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_COMMAND_INCORRECT"), *args)

            log.consoleOut("\n" + msg.getTranslation("TK_MSG_CONSOLE_USAGE_NOTES"))
            # initial order
            cmds = ["--help", "--userlist", "--userconfig"]
            # print initial commands as first
            for rCmd in cmds:
                log.consoleOut(" ", rCmd, cons.TK_USER_ADMIN_COMMANDS[rCmd])

            # put a little space in between
            log.consoleOut("")

            # print help
            for rCmd, rCmdDesc in cons.TK_USER_ADMIN_COMMANDS.items():
                # do not print already known commands
                if rCmd not in cmds:
                    log.consoleOut(" ", rCmd, rCmdDesc)

    # --------------- parameter execution methods --------------- #

    def printUserList(self, pUserList):
        """Format and print userlist"""
        # print to console
        log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_USERS_TOTAL", len(pUserList)))
        # loop and print
        for rUser in pUserList:
            log.consoleOut(rUser)

    def printUserConfig(self, pUserName, pPrintUserConfig):
        """Format and print user config"""
        # print to console
        log.consoleOut(msg.getTranslation("TK_MSG_CONSOLE_CONFIG_FOR") % (pUserName))
        # loop and print the same format as ppl will use to set that
        for rUserKey, rUserConfig in pPrintUserConfig.items():
            # join the lists
            if "ALLOWED_W" in rUserKey or "LIMITS_P" in rUserKey:
                # print join
                log.consoleOut("%s: %s" % (rUserKey, ";".join(list(map(str, rUserConfig)))))
            # join the lists
            elif "ALLOWED_H" in rUserKey:
                # hrs
                hrs = ""
                # print join
                if len(rUserConfig) > 0:
                    for rUserHour in sorted(list(map(int, rUserConfig))):
                        # get config per hr
                        hr = "%s" % (rUserHour) if rUserConfig[str(rUserHour)][cons.TK_CTRL_SMIN] <= 0 and rUserConfig[str(rUserHour)][cons.TK_CTRL_EMIN] >= 60 else "%s[%s-%s]" % (rUserHour, rUserConfig[str(rUserHour)][cons.TK_CTRL_SMIN], rUserConfig[str(rUserHour)][cons.TK_CTRL_EMIN])
                        # empty
                        if hrs == "":
                            hrs = "%s" % (hr)
                        else:
                            hrs = "%s;%s" % (hrs, hr)

                log.consoleOut("%s: %s" % (rUserKey, hrs))
            elif "TRACK_IN" in rUserKey:
                log.consoleOut("%s: %s" % (rUserKey, bool(rUserConfig)))
            else:
                log.consoleOut("%s: %s" % (rUserKey, str(rUserConfig)))

    def processSetAllowedDays(self, pUserName, pDayList):
        """Process allowed days"""
        # defaults
        dayMap = ()
        result = 0

        # day map
        try:
            # try to parse parameters
            dayMap = list(map(int, pDayList.split(";")))
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
                # verify hour
                hour = int(rHour.split("[", 1)[0])
                # if we have advanced config (minutes)
                if "[" in rHour and "]" in rHour and "-" in rHour:
                    # get minutes
                    minutes = rHour.split("[", 1)[1].split("]")[0].split("-")
                    # verify minutes
                    tmp = int(minutes[0])
                    tmp = int(minutes[1])
                    # get our dict done
                    allowedHours[str(hour)] = {cons.TK_CTRL_SMIN: min(max(int(minutes[0]), 0), 60), cons.TK_CTRL_EMIN: min(max(int(minutes[1]), 0), 60)}
                else:
                    # get our dict done
                    allowedHours[str(hour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}
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
        dayLimits = ()
        result = 0

        # day limists
        try:
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
        if pTrackInactive not in ["true", "True", "TRUE", "false", "False", "FALSE"]:
            # fail
            result = -1
            message =  msg.getTranslation("TK_MSG_PARSE_ERROR") % ("please specify true or false")
        else:
            trackInactive = True if pTrackInactive in ["true", "True", "TRUE"] else False

        # preprocess successful
        if result == 0:
            # invoke
            result, message = self._timekprAdminConnector.setTrackInactive(pUserName, trackInactive)

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
