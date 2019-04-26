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
        print("Timekpr \"%s\" is already running" % (pAppName))
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
    # this is somewhat interesting as for processes we can not exactly tell whether it's graphical or not, but we check terminal sessions,
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
