"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import os
# set up our python path
import sys
sys.path.append("/usr/share/pyshared")

# imports
import signal

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.server.interface.dbus.daemon import timekprDaemon
from timekpr.common.utils import misc
from timekpr.server.config.userhelper import timekprUserStore


# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0]):
        # get out
        sys.exit(0)

    log.log(cons.TK_LOG_LEVEL_INFO, "--- initiating timekpr v. %s ---" % (cons.TK_VERSION))

    # get daemon class
    _timekprDaemon = timekprDaemon(pIsDevActive=cons.TK_DEV_ACTIVE)

    # this is needed for appindicator to react to ctrl+c
    signal.signal(signal.SIGINT, _timekprDaemon.finishTimekpr)
    signal.signal(signal.SIGTERM, _timekprDaemon.finishTimekpr)

    # prepare all users in the system
    timekprUserStore().checkAndInitUsers()

    # init daemon
    _timekprDaemon.initTimekpr()

    # start daemon threads
    _timekprDaemon.startTimekprDaemon()
