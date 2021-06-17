"""
Created on Aug 28, 2018

@author: mjasnik
"""
# imports
import os
import getpass
import sys
import signal
# set up our python path
if "/usr/lib/python3/dist-packages" not in sys.path:
    sys.path.append("/usr/lib/python3/dist-packages")

# timekpr imports
from timekpr.client.interface.dbus.daemon import timekprClient
from timekpr.common.utils import misc

# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0], getpass.getuser()):
        # get out
        sys.exit(0)

    # get our client
    _timekprClient = timekprClient()

    # this is needed for appindicator to react to ctrl+c
    signal.signal(signal.SIGINT, _timekprClient.finishTimekpr)
    signal.signal(signal.SIGTERM, _timekprClient.finishTimekpr)

    # start up timekpr client
    _timekprClient.startTimekprClient()
