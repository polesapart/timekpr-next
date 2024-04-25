"""
Created on Feb 05, 2019

@author: mjasnik
"""

# imports
import fileinput
import re
import os
import pwd
import re
from glob import glob

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.utils.config import timekprConfig
from timekpr.common.utils.config import timekprUserConfig
from timekpr.common.utils.config import timekprUserControl
from timekpr.common.utils.misc import getNormalizedUserNames

# user limits
_limitsConfig = {}
_loginManagers = [result.strip(None) for result in cons.TK_USERS_LOGIN_MANAGERS.split(";")]

# defaults
_limitsConfig["UID_MIN"] = 1000
_limitsConfig["UID_MAX"] = 60000
# username pattern:
#   all users, max 101 chars
#   linux users, extended with uppercase characters and first numeric or "." character
#   domain users, extended with uppercase characters and first numeric or ".", and "@" symbol
_userNameRegexp = re.compile("^[a-zA-Z0-9_\.]([a-zA-Z0-9_\.@-]{0,101}|[a-zA-Z0-9_\.@-]{0,100}\$)$")


# some distros are "different", login.defs may be in different dir, config reflects multiple dirs to check for the file
for rFile in cons.TK_USER_LIMITS_FILE:
    # check if file exists
    if os.path.isfile(rFile):
        # load limits
        with fileinput.input(rFile) as rLimitsFile:
            # read line and do manipulations
            for rLine in rLimitsFile:
                # get min/max uids
                if re.match("^UID_M(IN|AX)[ \t]+[0-9]+$", rLine):
                    # find our config
                    x = re.findall(r"^([A-Z_]+)[ \t]+([0-9]+).*$", rLine)
                    # save min/max uuids
                    _limitsConfig[x[0][0]] = int(x[0][1])
            # fin
            break


def isUserValid(pUserId, pUserName=None, pUserShell=None):
    """Validate user ID, name and shell"""
    # vars
    global _limitsConfig
    global _userNameRegexp
    isUIDOK = False

    # check user id
    if pUserId is not None and pUserId != "":
        # check normal users and to test in VMs default user (it may have UID of 999, -1 from limit)
        isUIDOK = (int(pUserId) >= _limitsConfig["UID_MIN"] - 1)
        # check shell (if provided)
        if isUIDOK and pUserShell is not None:
            # uid is ok and shell is passed
            if "/nologin" in pUserShell or "/false" in pUserShell or "" == pUserShell:
                # user is not ours
                isUIDOK = False
        # check if username is ok
        if isUIDOK and pUserName is not None:
            # uid is ok and name is passed
            if not _userNameRegexp.match(pUserName):
                # user is not ours
                isUIDOK = False
    # fin
    return(isUIDOK)


def getTimekprLoginManagers():
    """Get login manager names"""
    global _loginManagers
    return(_loginManagers)


def setWakeUpByRTC(pWkeUpTimeEpoch):
    """Set wakeup time for computer"""
    res = False
    # first check that we can access rtc
    if os.path.isfile(cons.TK_CTRL_WKUPF):
        try:
            # now write wakeup timer
            with open(cons.TK_CTRL_WKUPF, "w") as wakeFile:
                # write time
                wakeFile.write(str(pWkeUpTimeEpoch))
                # success
                res = True
        except:
            # we only care about this, at least for now, if it succeeds
            res = False
    # result
    return res


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

        # iterate through all usernames
        for rUser in pwd.getpwall():
            # save our user, if it mactches
            if isUserValid(rUser.pw_uid, rUser.pw_name, rUser.pw_shell):
                # get processed usernames
                userFName = getNormalizedUserNames(pUser=rUser)[1]
                # save ()
                users[rUser.pw_name] = [rUser.pw_uid, userFName]

        # get user config
        timekprConfigManager = timekprConfig()
        # load user config
        timekprConfigManager.loadMainConfiguration()

        # go through our users
        for rUser in users:
            # get path of file
            file = os.path.join(timekprConfigManager.getTimekprConfigDir(), cons.TK_USER_CONFIG_FILE % (rUser))

            # check if we have config for them
            if not os.path.isfile(file):
                log.log(cons.TK_LOG_LEVEL_INFO, "setting up user \"%s\" with id %i" % (rUser, users[rUser][0]))
                # user config
                timekprUserConfig(timekprConfigManager.getTimekprConfigDir(), rUser).initUserConfiguration()
                # user control
                timekprUserControl(timekprConfigManager.getTimekprWorkDir(), rUser).initUserControl()

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finishing setting up users")

        # user list
        return users

    def getSavedUserList(self, pConfigDir=None):
        """
            Get user list, this will get user list from config files present in the system:
              no config - no user
              leftover config - please set up non-existent user (maybe pre-defined one?)
        """
        # initialize username storage
        filterExistingOnly = False  # this is to filter only existing local users (currently just here, not decided on what to do)
        userList = []

        # prepare all users in the system
        users = self.checkAndInitUsers()

        # in case we don't have a dir yet
        if pConfigDir is None:
            # get user config
            timekprConfigManager = timekprConfig()
            # load user config
            timekprConfigManager.loadMainConfiguration()
            # config dir
            configDir = timekprConfigManager.getTimekprConfigDir()
        else:
            # use passed value
            configDir = pConfigDir

        log.log(cons.TK_LOG_LEVEL_DEBUG, "listing user config files")

        # now list the config files
        userConfigFiles = glob(os.path.join(configDir, cons.TK_USER_CONFIG_FILE % ("*")))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "traversing user config files")

        # now walk the list
        for rUserConfigFile in sorted(userConfigFiles):
            # exclude standard sample file
            if "timekpr.USER.conf" not in rUserConfigFile:
                # first get filename and then from filename extract username part (as per cons.TK_USER_CONFIG_FILE)
                user = re.sub(cons.TK_USER_CONFIG_FILE.replace(".%s.", r"\.(.*)\."), r"\1", os.path.basename(rUserConfigFile))
                # whether user is valid in config file
                userNameValidated = False
                # try to read the first line with username
                with open(rUserConfigFile, "r") as confFile:
                    # read first (x) lines and try to get username
                    for i in range(0, cons.TK_UNAME_SRCH_LN_LMT):
                        # check whether we have correct username
                        if "[%s]" % (user) in confFile.readline():
                            # user validated
                            userNameValidated = True
                            # found
                            break
                # validate user against valid (existing) users in the system
                if userNameValidated and (not filterExistingOnly or user in users):
                    # get actual user name
                    if user in users:
                        # add user name and full name
                        userList.append([user, users[user][1]])
                    else:
                        # add user name and full name
                        userList.append([user, ""])

        log.log(cons.TK_LOG_LEVEL_DEBUG, "finishing user list")

        # finish
        return(userList)
