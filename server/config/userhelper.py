"""
Created on Feb 05, 2019

@author: mjasnik
"""

# imports
import fileinput
import re
import os
from glob import glob

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils.config import timekprConfig
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl


# user limits
_limitsConfig = {}
_loginManagers = [result.strip(None) for result in cons.TK_USERS_LOGIN_MANAGERS.split(";")]

# load limits
with fileinput.input(cons.TK_USER_LIMITS_FILE) as rLimitsFile:
    # read line and do manipulations
    for rLine in rLimitsFile:
        # get min/max uids
        if re.match("^UID_M(IN|AX)[ \t]+[0-9]+$", rLine):
            # find our config
            x = re.findall(r"^([A-Z_]+)[ \t]+([0-9]+).*$", rLine)
            # save min/max uuids
            _limitsConfig[x[0][0]] = int(x[0][1])


# this gets user limits
def verifyNormalUserID(pUserId):
    """Return min user id"""
    global _limitsConfig
    # to test in VMs default user for Ubuntu / Kubuntu has UID of 999 (-1 from limit), this should work fine for any other case
    return((_limitsConfig["UID_MIN"]-1 <= int(pUserId) <= _limitsConfig["UID_MAX"]))


def getTimekprLoginManagers():
    """Get login manager names"""
    global _loginManagers
    return(_loginManagers)


class timekprUserStore(object):
    """Class will privide methods to help managing users, like intialize the config for them"""

    def __init__(self):
        """Initialize timekprsystemusers"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "initializing timekprUserStore")

    def __del__(self):
        """Deinitialize timekprsystemusers"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "de-initializing timekprUserStore")

    def checkAndInitUsers(self):
        """Initialize all users present in the system as per particular config"""
        # config
        users = {}

        # load limits
        with fileinput.input(cons.TK_USERS_FILE) as rUsersFile:
            # read line and do manipulations
            for rLine in rUsersFile:
                # get our users splitted
                userDef = rLine.split(":")
                # get uuid
                uuid = int(userDef[2])
                # save our user, if it mactches
                if verifyNormalUserID(uuid):
                    # save
                    users[userDef[0]] = uuid

        # set up tmp logging
        logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_INFO, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}
        # set up logging
        log.setLogging(logging)
        # get user config
        timekprConfigManager = timekprConfig(pIsDevActive=cons.TK_DEV_ACTIVE, pLog=logging)
        # load user config
        timekprConfigManager.loadMainConfiguration()
        # set up logging
        logging = {cons.TK_LOG_L: timekprConfigManager.getTimekprLogLevel(), cons.TK_LOG_D: timekprConfigManager.getTimekprLogfileDir(), cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}

        # go through our users
        for rUser, rUserId in users.items():
            # get path of file
            file = os.path.join(timekprConfigManager.getTimekprConfigDir(), cons.TK_USER_CONFIG_FILE % (rUser))

            # check if we have config for them
            if not os.path.isfile(file):
                log.log(cons.TK_LOG_LEVEL_INFO, "setting up user \"%s\" with id %i" % (rUser, rUserId))
                # user config
                timekprUserConfig(logging, timekprConfigManager.getTimekprConfigDir(), rUser).initUserConfiguration()
                # user control
                timekprUserControl(logging, timekprConfigManager.getTimekprWorkDir(), rUser).initUserControl()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finishing setting up users")

    def getSavedUserList(self, pLog=None, pConfigDir=None):
        """
            Get user list, this will get user list from config files present in the system:
              no config - no user
              leftover config - please set up non-existent user (maybe pre-defined one?)
        """
        # initialize username storage
        userList = []

        # in case we don't have a dir yet
        if pConfigDir is None:
            # set up tmp logging
            logging = {cons.TK_LOG_L: cons.TK_LOG_LEVEL_INFO, cons.TK_LOG_D: cons.TK_LOG_TEMP_DIR, cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}
            # set up logging
            log.setLogging(logging)
            # get user config
            timekprConfigManager = timekprConfig(pIsDevActive=cons.TK_DEV_ACTIVE, pLog=logging)
            # load user config
            timekprConfigManager.loadMainConfiguration()
            # set up logging
            logging = {cons.TK_LOG_L: timekprConfigManager.getTimekprLogLevel(), cons.TK_LOG_D: timekprConfigManager.getTimekprLogfileDir(), cons.TK_LOG_W: cons.TK_LOG_OWNER_SRV, cons.TK_LOG_U: ""}
            # config dir
            configDir = timekprConfigManager.getTimekprConfigDir()
        else:
            # use passed value
            configDir = pConfigDir
            # log
            logging = pLog

        # set up logging
        log.setLogging(logging)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "listing user config files")

        # now list the config files
        userConfigFiles = glob(os.path.join(configDir, cons.TK_USER_CONFIG_FILE % ("*")))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "traversing user config files")

        # now walk the list
        for rUserConfigFile in sorted(userConfigFiles):
            # exclude standard sample file
            if "timekpr.USER.conf" not in rUserConfigFile:
                # first get filename and then from filename extract username part (as per cons.TK_USER_CONFIG_FILE)
                user = os.path.splitext(os.path.splitext(os.path.basename(rUserConfigFile))[0])[1].lstrip(".")
                # extract user name
                userList.append(user)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finishing user list")

        # finish
        return(userList)
