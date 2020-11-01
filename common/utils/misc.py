"""
Created on Aug 28, 2018

@author: mjasnik
"""

# defaults
_START_TIME = None
_END_TIME = None
_RESULT = 0

# imports
from datetime import datetime
import os
import pwd
import inspect
try:
    import psutil
    _PSUTIL = True
except (ImportError, ValueError):
    _PSUTIL = False
    pass

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log


# this is needed for debugging purposes
def whoami():
    """Return callers name from the call stack, the 0 is this function, prev is the one needd"""
    return inspect.stack()[1][3]


def getNormalizedUserNames(pUID=None, pUser=None):
    """Get usernames and/or normalize them"""
    user = pUser
    userName = None
    userNameFull = ""

    try:
        # if we need to get one
        if pUID is not None:
            # user
            user = pwd.getpwuid(pUID)
        # we have user
        if user is not None:
            # username
            userName = user.pw_name
            userNameFull = user.pw_gecos
        # workaround for distros that have one or more "," at the end of user full name
        userNameFull = userNameFull.rstrip(",")
        # if username is exactly the same as full name, no need to show it separately
        userNameFull = userNameFull if userNameFull != userName else ""
    except KeyError:
        pass

    # full username
    return userName, userNameFull


def measureTimeElapsed(pStart=False, pStop=False, pResult=False):
    """Calculate the time difference in the simplest manner"""
    # init globals (per import)
    global _START_TIME
    global _END_TIME
    global _RESULT

    # set up start
    if pStart:
        _START_TIME = datetime.now()
    # set up end
    if pStop:
        _END_TIME = datetime.now()
        _RESULT = (_END_TIME - _START_TIME).total_seconds()
        _START_TIME = _END_TIME

    # return
    return _RESULT


def checkAndSetRunning(pAppName):
    """Check whether application is already running"""
    # set up pidfile
    pidFile = os.path.join(cons.TK_LOG_TEMP_DIR, pAppName + cons.TK_LOG_PID_EXT)
    processPid = "0"
    processCmd = ""
    isAlreadyRunning = False

    # check if we have pid file for the app
    if os.path.isfile(pidFile):
        # if we have a file, we read the pid from there
        with open(pidFile, "r") as pidfile:
            processPid = pidfile.readline().rstrip("\n").rstrip("\r")

    # so we have a running app, now we check whether its our app
    if processPid != "0":
        # get process commandline
        procPidFile = os.path.join("/proc", processPid, "cmdline")

        # check whether we have a process running with this pid
        if os.path.isfile(procPidFile):
            # we wrap this with try in case pid is very short-lived
            try:
                with open(procPidFile, "r") as pidfile:
                    processCmd = pidfile.readline()
            except Exception:
                processCmd = ""

    # check if this is our process
    if pAppName in processCmd:
        # we are running
        isAlreadyRunning = True
        # print this to console as well
        print("Timekpr-nExT \"%s\" is already running" % (pAppName))
    else:
        # set our pid
        with open(pidFile, "w") as pidfile:
            processCmd = pidfile.write(str(os.getpid()))

    # return whether we are running
    return isAlreadyRunning


def killLeftoverUserProcesses(pLog, pUserName, pSessionTypes):
    """Kill leftover processes for user"""
    # if psutil is not available, do nothing
    global _PSUTIL
    if not _PSUTIL:
        return
    # set logging
    log.setLogging(pLog)

    # determine which sessions we are going to kill (either graphical or tty)
    # this is somewhat interesting as for processes we cannot exactly tell whether it's graphical or not, but we check terminal sessions,
    # if terminal is not set, then it's assumed graphical or so
    killTty = False
    killGUI = False

    # check for graphical
    for sessionType in cons.TK_SESSION_TYPES_CTRL.split(";"):
        # check for kill
        if sessionType in pSessionTypes:
            killGUI = True
            break
    # check for graphical
    for sessionType in cons.TK_SESSION_TYPES_EXCL.split(";"):
        # check for kill
        if sessionType in pSessionTypes:
            killTty = True
            break

    # get all processes for this user
    for userProc in psutil.process_iter():
        # process info
        procInfo = userProc.as_dict(attrs=["pid", "ppid", "name", "username", "terminal"])
        # check for username and for processes that originates from init (the rest should be terminated along with the session)
        if procInfo["username"] == pUserName and procInfo["ppid"] in (0, 1):
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "INFO: got leftover process, pid: %s, ppid: %s, username: %s, name: %s, terminal: %s" % (procInfo["pid"], procInfo["ppid"], procInfo["username"], procInfo["name"], procInfo["terminal"]))
            # kill processes if they are terminal and terminals are tracked or they are not terminal processes
            if (procInfo["terminal"] is not None and killTty) or (procInfo["terminal"] is None and killGUI):
                try:
                    # get process and kill it
                    userPrc = psutil.Process(procInfo["pid"])
                    # killing time
                    if cons.TK_DEV_ACTIVE:
                        log.log(cons.TK_LOG_LEVEL_INFO, "DEVELOPMENT ACTIVE, not killing my own processes, sorry...")
                    else:
                        # asking process to terminate
                        userPrc.terminate()
                except psutil.Error:
                    log.log(cons.TK_LOG_LEVEL_INFO, "ERROR: killing %s failed" % (procInfo["pid"]))
                    pass
                else:
                    log.log(cons.TK_LOG_LEVEL_INFO, "INFO: process %s killed" % (procInfo["pid"]))
            else:
                # do not kill terminal sessions if ones are not tracked
                log.log(cons.TK_LOG_LEVEL_INFO, "INFO: NOT killing process %s as it's from sessions which are not being tracked" % (procInfo["pid"]))


def findHourStartEndMinutes(pStr):
    """Separate name and desription in brackets"""
    # hour, start, end
    hour = None
    sMin = None
    eMin = None
    uacc = None

    # is hour unaccounted
    uacc = True if pStr[0] == "!" else False

    # get hour
    if len(pStr) <= 3:
        # hour, start, end
        hour = pStr[1:] if uacc else pStr
        sMin = 0
        eMin = 60
    else:
        # find minutes
        beg = 1 if uacc else 0
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
                hour = int(pStr[beg:st])
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
                uacc = None

    # return
    return hour, sMin, eMin, uacc


def splitConfigValueNameParam(pStr):
    """Separate value and param in brackets"""
    # name and its value
    value = None
    param = None

    # nothing
    if len(pStr) < 2:
        # can not be a normal value
        pass
    else:
        try:
            # find description ("") is for backwards compatibility
            st = pStr.find("(\"")  # compatibility description start
            en = pStr.find("\")")  # compatibility description end
            ln = 1 if st < 0 else 2  # compatility case searches for 2 letters, new one 1
            # new style config
            st = pStr.find("[") if st < 0 else st  # new style config
            en = pStr.find("]") if en < 0 else en  # new style config
            st = en if st < 0 else st  # no description, we'll get just pattern
            # process and its description
            value = pStr[0:st if st > 0 else len(pStr)]
            param = "" if st < 0 else pStr[st+ln:en if en >= 0 else len(pStr)]
        except:
            # it doesn't matter which error occurs
            value = None
            param = None

    # return
    return value, param
