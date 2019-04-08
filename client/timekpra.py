"""
Created on Jan 4, 2019

@author: mjasnik
"""
# imports
import os
import getpass
# set up our python path
import sys
sys.path.append("/usr/share/pyshared")

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.client.admin.adminprocessor import timekprAdminClient
from timekpr.common.utils import misc

# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0] + "." + getpass.getuser()):
        # get out
        sys.exit(0)

    # get our admin client
    _timekprAdminClient = timekprAdminClient(pIsDevActive=cons.TK_DEV_ACTIVE)

    # start up timekpr admin client
    _timekprAdminClient.startTimekprAdminClient(*sys.argv)
