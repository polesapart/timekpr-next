"""
Created on Aug 28, 2018

@author: mjasnik
"""

import locale
import time

# init speech
try:
    from espeak import espeak as espeak
    _USE_SPEECH = True
except (ImportError, ValueError):
    _USE_SPEECH = False
    # init speech-ng
    if not _USE_SPEECH:
        try:
            from espeakng import ESpeakNG as espeakng
            _USE_SPEECH_NG = True
        except (ImportError, ValueError):
            _USE_SPEECH_NG = False
            pass
    pass

def isSupported():
    """Return whether speech can be used"""
    # result
    return (_USE_SPEECH or _USE_SPEECH_NG)

class timekprSpeech(object):
    """Class will provide speech synth functionality"""

    def __init__(self):
        """Initialize config"""

    def initSpeech(self):
        """Initialize speech"""
        # set up speech synth
        if _USE_SPEECH:
            # espeak
            espeak.set_voice(self.getDefaultSpeechLanguage())
            espeak.set_parameter(espeak.Parameter.Pitch, 1)
            espeak.set_parameter(espeak.Parameter.Rate, 135)
            espeak.set_parameter(espeak.Parameter.Range, 600)
        elif _USE_SPEECH_NG:
            # ng espeak
            self.espeak = espeakng()
            self.espeak.voice = self.getDefaultSpeechLanguage();
            self.espeak.pitch = 1
            self.espeak.speed = 135
            self.espeak.range = 600

    def getDefaultSpeechLanguage(self):
        """Get default language"""
        # no lang
        lang = "en"
        try:
            if _USE_SPEECH:
                lang = locale.getlocale()[0].split("_")[0]
            elif _USE_SPEECH_NG:
                lang = locale.getlocale()[0].replace("_", "-").lower()
        except Exception:
            pass
        # result
        return lang

    def saySmth(self, pMsg):
        """Say something"""
        # if supported
        if self.isSpeechSupported():
            if _USE_SPEECH:
                # synth the speech
                espeak.synth(pMsg)
            elif _USE_SPEECH_NG:
                # say
                self.espeak.say(pMsg)

    def isSpeechSupported(self):
        """Return whether speech can be used"""
        # result
        return isSupported()
