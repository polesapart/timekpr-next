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

# timekpr imports
from timekpr.common.constants import constants as cons


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
    if pStart: _START_TIME = datetime.now()
    # set up end
    if pStop: _END_TIME = datetime.now(); _RESULT = (_END_TIME - _START_TIME).total_seconds(); _START_TIME = _END_TIME

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
