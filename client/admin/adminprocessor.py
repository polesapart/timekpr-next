"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
#from datetime import timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
#from timekpr.common.log import log

# !!! WIP !!!
class timekprAdminClient(object):
    """Main class for holding all client logic (including dbus)"""

    # --------------- initialization / control methods --------------- #

    def __init__(self, pIsDevActive=False):
        """Initialize admin client"""
        # dev
        self._isDevActive = pIsDevActive

        # get our bus
        #self._timekprBus = (dbus.SessionBus() if (self._isDevActive and cons.TK_DEV_BUS == "ses") else dbus.SystemBus())

        # loop
        #self._mainLoop = GLib.MainLoop()

        # init logging (load config which has all the necessarry bits)
        #self._timekprConfigManager = timekprClientConfig(pIsDevActive)
        #self._timekprConfigManager.loadClientConfiguration()

        # save logging for later use in classes down tree
        #self._logging = {cons.TK_LOG_L: self._timekprConfigManager.getClientLogLevel(), cons.TK_LOG_D: self._timekprConfigManager.getClientLogfileDir()}

        # logging init
        #log.setLogging(self._logging, pClient=True)

    def startTimekprAdminClient(self, *args):
        """Start up timekpr admin (choose gui or cli and start this up)"""
        #log.log(cons.TK_LOG_LEVEL_INFO, "starting up timekpr client")

        # check whether we need CLI or GUI
        if len(args) == 0:
            # use GUI
            # load GUI and process from there
            pass
        else:
            # use CLI
            # validate possible parameters and their values, when fine execute them as well
            self.checkAndExecuteAdminCommands(*args)

    # --------------- parameter validation methods --------------- #

    def checkAndExecuteAdminCommands(self, *args):
        """Init connections to dbus provided by server"""
        #log.log(cons.TK_LOG_LEVEL_DEBUG, "start connectTimekprSignalsDBUS")
        # this gets the command itself (args[0] is the script name)
        adminCmd = args[1]

        # check whether command is supported
        if (adminCmd not in cons.TK_USER_ADMIN_COMMANDS and adminCmd not in cons.TK_ADMIN_COMMANDS) or adminCmd == "-help":
            print("The usage of timekpr admin client is as follows:")
            # print help
            for rCmd, rCmdDesc in cons.TK_USER_ADMIN_COMMANDS.items():
                print(" ", rCmd, rCmdDesc)
        ## now based on params check them out
        # add
        elif adminCmd == "a":
            pass
        elif adminCmd == "b":
            pass

    # --------------- parameter execution methods --------------- #
