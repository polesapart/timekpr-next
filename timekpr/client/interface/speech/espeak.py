"""
Created on Aug 28, 2018

@author: mjasnik
"""

import locale

# init speech
try:
    from espeak import espeak as espeak
    _USE_SPEECH = True
except (ImportError, ValueError):
    _USE_SPEECH = False
    pass


class timekprSpeech(object):
    """Class will provide speech synth functionality"""

    def __init__(self):
        """Initialize config"""

    def initSpeech(self):
        """Initialize speech"""
        # set up speech synth
        espeak.set_voice(self.getDefaultLanguage())
        espeak.set_parameter(espeak.Parameter.Pitch, 1)
        espeak.set_parameter(espeak.Parameter.Rate, 145)
        espeak.set_parameter(espeak.Parameter.Range, 600)

    def getDefaultLanguage(self):
        """Get default language"""
        # no lang
        lang = ""
        try:
            lang = locale.getlocale()[0].split("_")[0]
        except Exception:
            pass

        # result
        return lang

    def saySmth(self, pMsg):
        """Say something"""
        # if supported
        if self.isSupported():
            # synth the speech
            espeak.synth(pMsg)

    def isSupported(self):
        """Return whether speech can be used"""
        global _USE_SPEECH
        # result
        return _USE_SPEECH
