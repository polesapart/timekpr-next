"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
# from datetime import timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.client.interface.dbus.administration import timekprAdminConnector


# !!! WIP !!!
class timekprAdminClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self, pIsDevActive=False):
        """Initialize admin client"""
        # dev
        self._isDevActive = pIsDevActive

        # get our connector
        self._timekprAdminConnector = timekprAdminConnector(self._isDevActive)

    def startTimekprAdminClient(self, *args):
        """Start up timekpr admin (choose gui or cli and start this up)"""
        # check whether we need CLI or GUI
        if len(args) < 2:
            # use GUI
            # load GUI and process from there
            pass
        else:
            # use CLI
            # validate possible parameters and their values, when fine execute them as well
            self.checkAndExecuteAdminCommands(*args)

    # --------------- parameter validation methods --------------- #

    def checkAndExecuteAdminCommands(self, *args):
        """Init connection to timekpr dbus server"""
        # initial param len
        paramIdx = 1
        paramLen = len(args)
        adminCmdIncorrect = False

        # this gets the command itself (args[0] is the script name)
        adminCmd = args[paramIdx]

        # connect
        self._timekprAdminConnector.initTimekprConnection()

        # now based on params check them out
        # this gets saved user list from the server
        if adminCmd == "-help":
            # fine
            pass
        # this gets saved user list from the server
        elif adminCmd == "-userlist":
            # check param len
            if paramLen != paramIdx + 1:
                # fail
                adminCmdIncorrect = True
            else:
                # get list
                result, userList = self._timekprAdminConnector.getUserList()

                # process
                self.printUserList(userList) if result else log.consoleOut("FAILED")

        # this gets user configuration from the server
        elif adminCmd == "-userconfig":
            # check param len
            if paramLen != paramIdx + 2:
                # fail
                adminCmdIncorrect = True
            else:
                # get user config
                result, userConfig = self._timekprAdminConnector.getUserConfig(args[paramIdx+1])

                # process
                self.printUserConfig(args[paramIdx+1], userConfig) if result else log.consoleOut("FAILED")

        # this sets allowed days for the user
        elif adminCmd == "-setalloweddays":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetAllowedDays(args[paramIdx+1], args[paramIdx+2])

        # this sets allowed hours per specified day or ALL for every day
        elif adminCmd == "-setallowedhours":
            # check param len
            if paramLen != paramIdx + 4:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetAllowedHours(args[paramIdx+1], args[paramIdx+2], args[paramIdx+3])

        # this sets time limits per allowed days
        elif adminCmd == "-settimelimits":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTimeLimits(args[paramIdx+1], args[paramIdx+2])

        # this sets whether to track inactive user sessions
        elif adminCmd == "-settrackinactive":
            # check param len
            if paramLen != paramIdx + 3:
                # fail
                adminCmdIncorrect = True
            else:
                # set days
                self.processSetTrackInactive(args[paramIdx+1], args[paramIdx+2])

        # this sets time left for the user at current moment
        elif adminCmd == "-settimeleft":
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
        if (adminCmd not in cons.TK_USER_ADMIN_COMMANDS and adminCmd not in cons.TK_ADMIN_COMMANDS) or adminCmd == "-help" or adminCmdIncorrect:
            # fail
            if adminCmdIncorrect:
                log.consoleOut("The command is incorrect:", *args)
            log.consoleOut("\nThe usage of timekpr admin client is as follows:")
            # print help
            for rCmd, rCmdDesc in cons.TK_USER_ADMIN_COMMANDS.items():
                log.consoleOut(" ", rCmd, rCmdDesc)

    # --------------- parameter execution methods --------------- #

    def printUserList(self, pUserList):
        """Format and print userlist"""
        # print to console
        log.consoleOut("%i users in total:" % (len(pUserList)))
        # loop and print
        for rUser in pUserList:
            log.consoleOut(rUser)

    def printUserConfig(self, pUserName, pPrintUserConfig):
        """Format and print user config"""
        # print to console
        log.consoleOut("Config for %s:" % (pUserName))
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
        # invoke
        result = self._timekprAdminConnector.setAllowedDays(pUserName, list(map(int, pDayList.split(";"))))

        # process
        if not result:
            log.consoleOut("FAILED")

    def processSetAllowedHours(self, pUserName, pDayNumber, pHourList):
        """Process allowed hours"""
        # this is the dict for hour config
        allowedHours = {}
        # check hours
        for rHour in str(pHourList).split(";"):
            # if we have advanced config (minutes)
            if "[" in rHour and "]" in rHour and "-" in rHour:
                # get minutes
                minutes = rHour.split("[", 1)[1].split("]")[0].split("-")
                # get our dict done
                allowedHours[rHour.split("[", 1)[0]] = {cons.TK_CTRL_SMIN: min(max(int(minutes[0]), 0), 60), cons.TK_CTRL_EMIN: min(max(int(minutes[1]), 0), 60)}
            else:
                # get our dict done
                allowedHours[rHour.split("[", 1)[0]] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # invoke
        result = self._timekprAdminConnector.setAllowedHours(pUserName, pDayNumber, allowedHours)

        # process
        if not result:
            log.consoleOut("FAILED")

    def processSetTimeLimits(self, pUserName, pDayLimits):
        """Process time limits for days"""
        # invoke
        result = self._timekprAdminConnector.setTimeLimitForDays(pUserName, list(map(int, pDayLimits.split(";"))))

        # process
        if not result:
            log.consoleOut("FAILED")

    def processSetTrackInactive(self, pUserName, pTrackInactive):
        """Process track inactive"""
        # invoke
        result = self._timekprAdminConnector.setTrackInactive(pUserName, True if pTrackInactive in ["true", "True"] else False)

        # process
        if not result:
            log.consoleOut("FAILED")

    def processSetTimeLeft(self, pUserName, pOperation, pLimit):
        """Process time left"""
        # invoke
        result = self._timekprAdminConnector.setTimeLeft(pUserName, pOperation, int(pLimit))

        # process
        if not result:
            log.consoleOut("FAILED")
