"""
Created on Aug 28, 2018

@author: mjasnik
"""
# imports
import os
import getpass
# set up our python path
import sys
sys.path.append("/usr/share/pyshared")

# imports
import signal

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.client.interface.dbus.daemon import timekprClient
from timekpr.common.utils import misc

# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0] + "." + getpass.getuser()):
        # get out
        sys.exit(0)

    # get our client
    _timekprClient = timekprClient(pIsDevActive=cons.TK_DEV_ACTIVE)

    # this is needed for appindicator to react to ctrl+c
    signal.signal(signal.SIGINT, _timekprClient.finishTimekpr)
    signal.signal(signal.SIGTERM, _timekprClient.finishTimekpr)

    # start up timekpr client
    _timekprClient.startTimekprClient()
