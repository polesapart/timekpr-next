"""
Created on Aug 28, 2018

@author: mjasnik
"""

import gi
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gettext import gettext as _
from datetime import datetime, timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.utils.config import timekprClientConfig
from timekpr.client.interface.speech.espeak import timekprSpeech

# constant
_NO_TIME_LABEL = "--:--:--"
_NO_TIME_LABEL_SHORT = "--:--"
_NO_TIME_LIMIT_LABEL = "--:--:--:--"


class timekprGUI(object):
    """Main class for supporting timekpr forms"""

    def __init__(self, pTimekprVersion, pResourcePath, pUsername):
        """Initialize gui"""
        # init locale
        self.initLocale()

        # set up base variables
        self._userName = pUsername
        self._timekprVersion = pTimekprVersion
        self._resourcePath = pResourcePath

        # sets up limit variables
        self._timeSpent = None
        self._timeInactive = None
        self._timeLeftToday = None
        self._timeLeftContinous = None
        self._timeTrackInactive = True
        self._limitConfig = {}

        # sets up config options
        self._showLimitNotification = False
        self._showAllNotifications = False
        self._useSpeechNotifications = False
        self._showSeconds = False
        self._loggingLevel = 1

        # is speech supported
        self._isSpeechSupported = timekprSpeech().isSupported()

        # change tracking
        self._configChanged = False

        # ## forms builders ##
        # init about builder
        self._timekprAboutDialogBuilder = Gtk.Builder()
        # get our dialog
        self._timekprAboutDialogBuilder.add_from_file(os.path.join(self._resourcePath, "about.glade"))
        # get main form (to set various runtime things)
        self._timekprAboutDialog = self._timekprAboutDialogBuilder.get_object("timekprAboutDialog")

        # init config builder
        self._timekprConfigDialogBuilder = Gtk.Builder()
        # get our dialog
        self._timekprConfigDialogBuilder.add_from_file(os.path.join(self._resourcePath, "config.glade"))
        # get main form (to set various runtime things)
        self._timekprConfigDialog = self._timekprConfigDialogBuilder.get_object("timekprConfigDialog")

        self._timekprAboutDialogBuilder.connect_signals(self)
        self._timekprConfigDialogBuilder.connect_signals(self)

        # set up username (this does not change)
        self._timekprConfigDialogBuilder.get_object("timekprUsernameL").set_text(self._userName)

        # this sets up columns for list
        col = Gtk.TreeViewColumn("Day", Gtk.CellRendererText(), text=1)
        col.set_min_width(90)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").append_column(col)
        col = Gtk.TreeViewColumn("Limit", Gtk.CellRendererText(), text=2)
        col.set_min_width(35)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").append_column(col)

        # this sets up columns for list
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsTreeview").append_column(Gtk.TreeViewColumn("Intervals", Gtk.CellRendererText(), text=0))

        # initial config (everything is to the max)
        for i in range(0, 7):
            # set up default limits
            self._limitConfig[str(i+1)] = {cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_INT: [[None, None]]}

        # initialize week and month limits
        self._limitConfig[cons.TK_CTRL_LIMITW] = {cons.TK_CTRL_LIMITW: None}
        self._limitConfig[cons.TK_CTRL_LIMITM] = {cons.TK_CTRL_LIMITM: None}

        # status
        self.setStatus("Started")

    def renewUserConfiguration(self, pShowLimitNotification=None, pShowAllNotifications=None, pUseSpeechNotifications=None, pShowSeconds=None, pLoggingLevel=None):
        """Update configuration options"""
        # sets this up for local storage
        if pShowLimitNotification is not None:
            self._showLimitNotification = pShowLimitNotification
        if pShowAllNotifications is not None:
            self._showAllNotifications = pShowAllNotifications
        if pUseSpeechNotifications is not None:
            self._useSpeechNotifications = pUseSpeechNotifications
        if pShowSeconds is not None:
            self._showSeconds = pShowSeconds
            self._showSecondsChanged = False
        if pLoggingLevel is not None:
            self._loggingLevel = pLoggingLevel
        # if speech is not supported, we disable and uncheck the box
        if self._isSpeechSupported is False:
            self._useSpeechNotifications = False
            self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").set_sensitive(self._useSpeechNotifications)

        # user config
        self._timekprConfigDialogBuilder.get_object("timekprLimitChangeNotifCB").set_active(self._showLimitNotification)
        self._timekprConfigDialogBuilder.get_object("timekprShowAllNotifCB").set_active(self._showAllNotifications)
        self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").set_active(self._useSpeechNotifications)
        self._timekprConfigDialogBuilder.get_object("timekprShowSecondsCB").set_active(self._showSeconds)
        self._timekprConfigDialogBuilder.get_object("timekprLogLevelSB").set_value(self._loggingLevel)

    def renewLimits(self, pTimeLeft=None):
        """Renew information to be show for user in GUI"""
        # sets time left
        if pTimeLeft is not None:
            # limits
            self._timeSpent = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_SPENT])
            self._timeSpentWeek = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_SPENTW])
            self._timeSpentMonth = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_SPENTM])
            self._timeInactive = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_SLEEP])
            self._timeLeftToday = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_LEFTD])
            self._timeLeftContinous = cons.TK_DATETIME_START + timedelta(seconds=pTimeLeft[cons.TK_CTRL_LEFT])
            self._timeTrackInactive = True if pTimeLeft[cons.TK_CTRL_TRACK] else False

        # calculate strings to show (and show only those, which hava data)
        if self._timeSpent is not None:
            timeSpentStr = str((self._timeSpent - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeSpent.hour).rjust(2, "0") + ":" + str(self._timeSpent.minute).rjust(2, "0") + ":" + str(self._timeSpent.second).rjust(2, "0")
        else:
            timeSpentStr = _NO_TIME_LIMIT_LABEL
        if self._timeSpent is not None:
            timeSpentWeekStr = str((self._timeSpentWeek - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeSpentWeek.hour).rjust(2, "0") + ":" + str(self._timeSpentWeek.minute).rjust(2, "0") + ":" + str(self._timeSpentWeek.second).rjust(2, "0")
        else:
            timeSpentWeekStr = _NO_TIME_LIMIT_LABEL
        if self._timeSpent is not None:
            timeSpentMonthStr = str((self._timeSpentMonth - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeSpentMonth.hour).rjust(2, "0") + ":" + str(self._timeSpentMonth.minute).rjust(2, "0") + ":" + str(self._timeSpentMonth.second).rjust(2, "0")
        else:
            timeSpentMonthStr = _NO_TIME_LIMIT_LABEL
        if self._timeInactive is not None:
            timeSleepStr = str((self._timeInactive - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeInactive.hour).rjust(2, "0") + ":" + str(self._timeInactive.minute).rjust(2, "0") + ":" + str(self._timeInactive.second).rjust(2, "0")
        else:
            timeSleepStr = _NO_TIME_LIMIT_LABEL
        if self._timeLeftToday is not None:
            timeLeftTodayStr = str((self._timeLeftToday - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeLeftToday.hour).rjust(2, "0") + ":" + str(self._timeLeftToday.minute).rjust(2, "0") + ":" + str(self._timeLeftToday.second).rjust(2, "0")
        else:
            timeLeftTodayStr = _NO_TIME_LIMIT_LABEL
        if self._timeLeftContinous is not None:
            timeLeftTotalStr = str((self._timeLeftContinous - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(self._timeLeftContinous.hour).rjust(2, "0") + ":" + str(self._timeLeftContinous.minute).rjust(2, "0") + ":" + str(self._timeLeftContinous.second).rjust(2, "0")
        else:
            timeLeftTotalStr = _NO_TIME_LIMIT_LABEL

        # sets up stuff
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpentL").set_text(timeSpentStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpentWeekL").set_text(timeSpentWeekStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpentMonthL").set_text(timeSpentMonthStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeInactiveL").set_text(timeSleepStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeLeftTodayL").set_text(timeLeftTodayStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoContTimeLeftL").set_text(timeLeftTotalStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTrackInactiveCB").set_active(self._timeTrackInactive)

    def setStatus(self, pStatus):
        """Change status of timekpr"""
        if pStatus is not None:
            # get main status
            statusBar = self._timekprConfigDialogBuilder.get_object("timekprStatusBar")
            contextId = statusBar.get_context_id("status")
            # pop existing message and add new one
            statusBar.remove_all(contextId)
            statusBar.push(contextId, pStatus)

    def renewLimitConfiguration(self, pLimits=None):
        """Renew information to be show for user"""
        # if there is smth
        if pLimits is not None:
            self._limitConfig = pLimits

        # clear out days
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysLS").clear()

        # go in sorted order
        for rKey in sorted(self._limitConfig):
            # some of configuration needs different approach
            if rKey in [cons.TK_CTRL_LIMITW, cons.TK_CTRL_LIMITM]:
                # set locally
                if self._limitConfig[rKey][rKey] is not None:
                    # limit
                    timeLimitWKMON = cons.TK_DATETIME_START + timedelta(seconds=self._limitConfig[rKey][rKey])
                    # limit
                    timeLimitWKMONStr = str((timeLimitWKMON - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeLimitWKMON.hour).rjust(2, "0") + ":" + str(timeLimitWKMON.minute).rjust(2, "0") + ":" + str(timeLimitWKMON.second).rjust(2, "0")
                else:
                    timeLimitWKMONStr = _NO_TIME_LIMIT_LABEL

                # set week limit
                if rKey == cons.TK_CTRL_LIMITW:
                    # set up limits
                    self._timekprConfigDialogBuilder.get_object("timekprLimitForWeekL").set_text(timeLimitWKMONStr)
                elif rKey == cons.TK_CTRL_LIMITM:
                    # set up limits
                    self._timekprConfigDialogBuilder.get_object("timekprLimitForMonthL").set_text(timeLimitWKMONStr)
            else:
                # intervals
                if self._limitConfig[rKey][cons.TK_CTRL_LIMITD] is not None:
                    limit = cons.TK_DATETIME_START + timedelta(seconds=self._limitConfig[rKey][cons.TK_CTRL_LIMITD])
                    timeLimitStr = str((limit - cons.TK_DATETIME_START).days * 24 + limit.hour).rjust(2, "0") + ":" + str(limit.minute).rjust(2, "0")
                else:
                    timeLimitStr = _NO_TIME_LABEL_SHORT

                self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysLS").append([rKey, (cons.TK_DATETIME_START + timedelta(days=int(rKey)-1)).strftime("%A"), "%s" % (timeLimitStr)])

        # current day
        currDay = datetime.now().isoweekday()-1
        # determine curent day and point to it
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").set_cursor(currDay)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").scroll_to_cell(currDay)

    def initLocale(self):
        """Init translation stuff"""
        # init python gettext
        # gettext.bindtextdomain("timekpr-next", "/usr/share/locale")
        # gettext.textdomain("timekpr-next")
        pass

    def initAboutForm(self):
        """Initialize about form"""
        # version
        self._timekprAboutDialog.set_version(self._timekprVersion)
        # translation stuff
        self._timekprAboutDialog.set_translator_credits(_("please-enter-translator-credits"))
        # comment
        self._timekprAboutDialog.set_comments(_("Keep control of computer usage"))

        # show up all
        self._timekprAboutDialog.show_all()
        self._timekprAboutDialog.run()

        # hide for later use
        self._timekprAboutDialog.hide()

    def initConfigForm(self):
        """Initialize config form"""
        # refresh info
        self.renewUserConfiguration()
        self.renewLimits()
        self.renewLimitConfiguration()
        self.configPageSwitchSignal()

        # show up all
        self._timekprConfigDialog.show_all()
        self._timekprConfigDialog.run()

        # hide for later use
        self._timekprConfigDialog.hide()

    def daysChangedSignal(self, evt):
        """Refresh intervals when days change"""
        # refresh the child
        (tm, ti) = self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # clear out existing intervals
            self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").clear()
            # fill intervals only if that day exists
            if tm.get_value(ti, 0) in self._limitConfig:
                # fill the intervals
                for r in self._limitConfig[tm.get_value(ti, 0)][cons.TK_CTRL_INT]:
                    # if we have no data, we fill this up with nothing
                    if r[0] is None:
                        # fill in the intervals
                        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").append([("%s - %s") % (_NO_TIME_LABEL_SHORT, _NO_TIME_LABEL_SHORT)])
                    else:
                        start = (cons.TK_DATETIME_START + timedelta(seconds=r[0]))
                        end = (cons.TK_DATETIME_START + timedelta(seconds=r[1]))
                        # fill in the intervals
                        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").append([("%s:%s - %s:%s") % (str(start.hour).rjust(2, "0"), str(start.minute).rjust(2, "0"), str(end.hour).rjust(2, "0"), str(end.minute).rjust(2, "0"))])

    def saveUserConfigSignal(self, evt):
        """Save the configuration using config file manager"""
        # sets this up for local storage
        showLimitNotification = self._timekprConfigDialogBuilder.get_object("timekprLimitChangeNotifCB").get_active()
        showAllNotifications = self._timekprConfigDialogBuilder.get_object("timekprShowAllNotifCB").get_active()
        useSpeechNotifications = self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").get_active()
        loggingLevel = int(self._timekprConfigDialogBuilder.get_object("timekprLogLevelSB").get_value())
        showSeconds = self._timekprConfigDialogBuilder.get_object("timekprShowSecondsCB").get_active()

        # we need to track whether config has changed
        if (self._showLimitNotification != showLimitNotification
            or self._showAllNotifications != showAllNotifications
            or self._useSpeechNotifications != useSpeechNotifications
            or self._loggingLevel != loggingLevel
            or self._showSeconds != showSeconds
        ):
            # config is changed
            self._configChanged = True

        # assign for actual use
        self._showLimitNotification = showLimitNotification
        self._showAllNotifications = showAllNotifications
        self._useSpeechNotifications = useSpeechNotifications
        self._loggingLevel = loggingLevel
        self._showSeconds = showSeconds

        # get config and save it
        userConfig = timekprClientConfig(cons.TK_DEV_ACTIVE)

        # set config
        userConfig.setClientShowLimitNotifications(self._showLimitNotification)
        userConfig.setClientShowAllNotifications(self._showAllNotifications)
        userConfig.setClientUseSpeechNotifications(self._useSpeechNotifications)
        userConfig.setClientShowSeconds(self._showSeconds)
        userConfig.setClientLogLevel(self._loggingLevel)

        # save config
        userConfig.saveClientConfig()

    def configPageSwitchSignal(self, nb=None, pg=None, pgn=None):
        """Enable or disable apply on page change"""
        if pgn is None:
            ppgn = int(self._timekprConfigDialogBuilder.get_object("timekprConfigNotebook").get_current_page())
        else:
            ppgn = pgn

        # enable / disable apply when on config options page
        if int(ppgn) < 2:
            self._timekprConfigDialogBuilder.get_object("timekprSaveAndCloseBT").set_sensitive(False)
        else:
            self._timekprConfigDialogBuilder.get_object("timekprSaveAndCloseBT").set_sensitive(True)

    def getUserConfigChanged(self):
        """Get whether config has changed"""
        # save actual value and reset it after
        configChanged = self._configChanged
        self._configChanged = False
        # result
        return configChanged

    def closePropertiesSignal(self, evt):
        """Close the config form"""
        # close
        self._timekprConfigDialog.hide()
