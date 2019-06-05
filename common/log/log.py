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
LOG_LEVEL = cons.TK_LOG_LEVEL_INFO
# logging to file
LOG_FILE = None


def getLogLevel():
    """Return log level"""
    global LOG_LEVEL
    # return
    return LOG_LEVEL


# log names
def getLogFile(pWho, pUserName):
    """Get log file"""
    # log file
    logFile = (cons.TK_LOG_FILE_CLIENT if pWho == cons.TK_LOG_OWNER_CLIENT else (cons.TK_LOG_FILE_ADMIN if pWho == cons.TK_LOG_OWNER_ADMIN else (cons.TK_LOG_FILE_ADMIN_SU if pWho == cons.TK_LOG_OWNER_ADMIN_SU else cons.TK_LOG_FILE)))
    # replace user in log file
    return(logFile.replace(cons.TK_LOG_USER, pUserName, 1))


def setLogging(pLog):
    """Set up logging (this function expects 4 tuples: log level, log directory, log owner and username"""
    # set up level
    setLogLevel(pLog[cons.TK_LOG_L])
    # set up file
    setLogFile(pLog[cons.TK_LOG_D], pLog[cons.TK_LOG_W], pLog[cons.TK_LOG_U])


def setLogLevel(pLvl):
    """Set up log level"""
    global LOG_LEVEL
    # set
    LOG_LEVEL = pLvl


def setLogFile(pLogDir, pWho, pUserName):
    """Set up log file"""
    global LOG_FILE
    # log  file
    logFile = os.path.join(pLogDir, getLogFile(pWho, pUserName))

    # change log file from default to smth
    if pLogDir is not None and pLogDir != cons.TK_LOG_TEMP_DIR:
        # construct tmp file name
        tmpLogFile = os.path.join(cons.TK_LOG_TEMP_DIR, cons.TK_LOG_FILE)

        # find old log file (if that exists and transfer contents to real
        if os.path.isfile(tmpLogFile):
            # transfer
            with open(logFile, "a") as fTo, open(tmpLogFile, "r") as fFrom:
                fTo.writelines(fLine for fLine in fFrom)

            # we don't need tmp file anymore
            os.remove(tmpLogFile)

    # set
    LOG_FILE = logFile


def isDebug():
    """Is debug enabled"""
    global LOG_LEVEL
    # check whether debug is enabled
    if cons.TK_LOG_LEVEL_DEBUG <= LOG_LEVEL:
        return True


def log(pLvl, pText):
    """Print to console"""
    global LOG_LEVEL
    # check debug level and output
    if pLvl <= LOG_LEVEL:
        # redirect to output
        output(pText)


def output(pText):
    """Print to console and/or file"""
    global LOG_FILE
    # we have to log somewhere even log file is not set up
    if LOG_FILE is None:
        logFile = os.path.join(cons.TK_LOG_TEMP_DIR, cons.TK_LOG_FILE)
    else:
        logFile = LOG_FILE

    # format text
    logText = "%s: %s" % (datetime.now().strftime(cons.TK_LOG_DATETIME_FORMAT), pText)

    # write to file
    print(logText, file=open(logFile, "a"))

    # in development mode, we spit out in console as well
    if cons.TK_DEV_ACTIVE:
        print(logText)


def consoleOut(*args):
    """Print everything passed to console"""
    # currently just output the stuff
    print(*args)
