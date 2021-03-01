"""
Created on Aug 28, 2018

@author: mjasnik
"""

# connection with ck
class timekprUserManager(object):
    # init
    def __init__(self, pUserName, pUserPathOnBus):
        """Initialize manager for ConsoleKit."""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def cacheUserSessionList(self):
        """Determine user sessions and cache session objects for further reference."""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def isUserActive(self, pSessionTypes, pTrackInactive, pIsScreenLocked):
        """Check if user is active."""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")
