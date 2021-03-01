"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
from datetime import datetime
import os

# timekpr imports
from timekpr.common.constants import constants as cons

# default logging
_LOG_LEVEL = cons.TK_LOG_LEVEL_INFO
# logging to file
_LOG_FILE = None
# logging buffer (before we know where to put log file)
_LOG_PEND_EVT_CNT = 0
_LOG_PEND_FLUSH_CNT = 0
_LOG_BUFFER = []

# log names
def _getLogFileName(pWho, pUserName):
    """Get log file"""
    # log file
    logFile = (cons.TK_LOG_FILE_CLIENT if pWho == cons.TK_LOG_OWNER_CLIENT else (cons.TK_LOG_FILE_ADMIN if pWho == cons.TK_LOG_OWNER_ADMIN else (cons.TK_LOG_FILE_ADMIN_SU if pWho == cons.TK_LOG_OWNER_ADMIN_SU else cons.TK_LOG_FILE)))
    # replace user in log file
    return(logFile.replace(cons.TK_LOG_USER, pUserName, 1))


def _output(pText):
    """Print to console and/or file"""
    global _LOG_FILE, _LOG_PEND_EVT_CNT, _LOG_BUFFER

    # format text
    logText = "%s: %s" % (datetime.now().strftime(cons.TK_LOG_DATETIME_FORMAT), pText)
    # prepare a line for file
    _LOG_BUFFER.append("%s\n" % (logText))

    # in development mode, we spit out in console as well
    if cons.TK_DEV_ACTIVE:
        print(logText)
    # log only if enough calls are passed to log
    if _LOG_PEND_EVT_CNT >= cons.TK_LOG_AUTO_FLUSH_EVT_CNT:
        # write buffers to log file
        flushLogFile()


def setLogging(pLogLevel, pLogDir, pWho, pUserName):
    """Set up logging (this function expects 4 tuples: log level, log directory, log owner and username"""
    global _LOG_FILE
    # set up level
    setLogLevel(pLogLevel)
    # set up file
    _LOG_FILE = os.path.join(pLogDir, _getLogFileName(pWho, pUserName))


def isLoggingActive():
    """Is debug enabled"""
    global _LOG_FILE
    # check whether debug is enabled
    return _LOG_FILE is not None


def isDebugEnabled(pDebugLevel=cons.TK_LOG_LEVEL_DEBUG):
    """Is debug enabled"""
    global _LOG_LEVEL
    # check whether debug is enabled
    if pDebugLevel <= _LOG_LEVEL:
        return True


def getLogLevel():
    """Return log level"""
    global _LOG_LEVEL
    # return
    return _LOG_LEVEL


def setLogLevel(pLvl):
    """Set up log level"""
    global _LOG_LEVEL
    # set
    _LOG_LEVEL = pLvl


def log(pLvl, pText):
    """Print to console"""
    global _LOG_LEVEL, _LOG_PEND_EVT_CNT
    # check debug level and output
    if pLvl <= _LOG_LEVEL:
        # add to pending event cnt
        _LOG_PEND_EVT_CNT += 1
        # redirect to output
        _output(pText)


def autoFlushLogFile():
    """This will flush the log file to file"""
    # iport globals
    global _LOG_PEND_FLUSH_CNT
    # reset flush
    _LOG_PEND_FLUSH_CNT += 1

    # when the time has come, just flush the log file
    if _LOG_PEND_FLUSH_CNT >= cons.TK_POLLTIME:
        # flush the log
        flushLogFile()


def flushLogFile():
    """This will flush the log file to file"""
    # iport globals
    global _LOG_FILE, _LOG_BUFFER, _LOG_PEND_EVT_CNT, _LOG_PEND_FLUSH_CNT
    # we can only flush if there is a file
    if _LOG_FILE is not None and len(_LOG_BUFFER) > 0:
        try:
            # open log file
            with open(_LOG_FILE, "a") as logFile:
                # write whole buffer to log file
                logFile.writelines(_LOG_BUFFER)
                # reset
                _LOG_PEND_EVT_CNT = 0
                _LOG_PEND_FLUSH_CNT = 0
                _LOG_BUFFER.clear()
        except Exception as ex:
            # spit out to console
            consoleOut("ERROR, CAN NOT WRITE TO LOG DUE TO:\n%s" % (ex))


def consoleOut(*args):
    """Print everything passed to console"""
    # currently just output the stuff
    print(*args)
