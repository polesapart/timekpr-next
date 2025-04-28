"""
Created on Aug 28, 2018

@author: mjasnik
"""

# connection with ck
class timekprUserLoginManager(object):
    """Class enables the connection with ConsoleKit"""

    def __init__(self):
        """Initialize all stuff for consolekit"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def getUserList(self, pSilent=False):
        """Go through a list of logged in users"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def getUserSessionList(self, pUserName, pUserPath):
        """Get up-to-date user session list"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def determineLoginManagerVT(self, pUserName, pUserPath):
        """Get login manager session VTNr"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def switchTTY(self, pSeatId, pSessionTTY):
        """Swith TTY for login screen"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")

    def terminateUserSessions(self, pUserName, pUserPath, pTimekprConfig, pRestrictionType):
        """Terminate user sessions"""
        # NOT IMPLEMENTED
        raise NotImplementedError("ConsoleKit support is not implemented")
