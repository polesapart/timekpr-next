"""
Created on Jan 4, 2019

@author: mjasnik
"""
# imports
import os
import getpass
import sys
# set up our python path
if "/usr/lib/python3/dist-packages" not in sys.path:
    sys.path.append("/usr/lib/python3/dist-packages")

# timekpr imports
from timekpr.client.admin.adminprocessor import timekprAdminClient
from timekpr.common.utils import misc

# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0] + "." + getpass.getuser()):
        # get out
        sys.exit(0)

    # get our admin client
    _timekprAdminClient = timekprAdminClient()

    # start up timekpr admin client
    _timekprAdminClient.startTimekprAdminClient(*sys.argv)
