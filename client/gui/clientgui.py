"""
Created on Aug 28, 2018

@author: mjasnik
"""

import gi
import os
import re
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from datetime import datetime, timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.common.constants import messages as msg

# constant
_NO_TIME_LABEL = "--:--:--"
_NO_TIME_LABEL_SHORT = "--:--"
_NO_TIME_LIMIT_LABEL = "--:--:--:--"
_HOUR_REGEXP = re.compile("^([0-9]{1,2})$")
_HOUR_MIN_REGEXP = re.compile("^([0-9]{1,2}):([0-9]{1,2})$")


class timekprGUI(object):
    """Main class for supporting timekpr forms"""

    def __init__(self, pTimekprVersion, pTimekprClientConfig, pUsername, pUserNameFull):
        """Initialize gui"""
        # set up base variables
        self._userName = pUsername
        self._timekprVersion = pTimekprVersion
        self._timekprClientConfig = pTimekprClientConfig
        self._timekprPTPageNr = 2

        # sets up limit variables
        self._timeSpent = None
        self._timeSpentWeek = None
        self._timeSpentMonth = None
        self._timeInactive = None
        self._timeLeftToday = None
        self._timeLeftContinous = None
        self._timeTrackInactive = True
        self._timeTimeLimitOverridePT = False
        self._timeUnaccountedIntervalsFlagPT = False
        self._timeSpentPT = None
        self._timeLeftPT = None
        self._timePTActivityCntStr = "0"
        self._limitConfig = {}

        # change tracking
        self._configChanged = False
        # ## forms builders ##
        # init about builder
        self._timekprAboutDialogBuilder = Gtk.Builder()
        # get our dialog
        self._timekprAboutDialogBuilder.add_from_file(os.path.join(self._timekprClientConfig.getTimekprSharedDir(), "client/forms", "about.glade"))
        # get main form (to set various runtime things)
        self._timekprAboutDialog = self._timekprAboutDialogBuilder.get_object("timekprAboutDialog")

        # init config builder
        self._timekprConfigDialogBuilder = Gtk.Builder()
        # get our dialog
        self._timekprConfigDialogBuilder.add_from_file(os.path.join(self._timekprClientConfig.getTimekprSharedDir(),  "client/forms", "client.glade"))
        # get main form (to set various runtime things)
        self._timekprConfigDialog = self._timekprConfigDialogBuilder.get_object("timekprConfigDialog")

        self._timekprAboutDialogBuilder.connect_signals(self)
        self._timekprConfigDialogBuilder.connect_signals(self)

        # set up username (this does not change)
        self._timekprConfigDialogBuilder.get_object("timekprUsernameLB").set_text("%s (%s)" % (self._userName, pUserNameFull) if pUserNameFull != "" else self._userName)

        # this sets up columns for days config
        col = Gtk.TreeViewColumn("Day", Gtk.CellRendererText(), text=1)
        col.set_min_width(100)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").append_column(col)
        col = Gtk.TreeViewColumn("Limit", Gtk.CellRendererText(), text=2)
        col.set_min_width(60)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").append_column(col)

        # this sets up columns for interval list
        # interval string
        col = Gtk.TreeViewColumn("Interval", Gtk.CellRendererText(), text=0)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsTreeview").append_column(col)
        # unaccountable interval column
        col = Gtk.TreeViewColumn("Unaccounted", Gtk.CellRendererText(), text=1)
        col.set_min_width(10)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsTreeview").append_column(col)

        # PlayTime
        # this sets up columns for limits list
        col = Gtk.TreeViewColumn("Day", Gtk.CellRendererText(), text=1)
        col.set_min_width(100)
        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysTreeview").append_column(col)
        col = Gtk.TreeViewColumn("Limit", Gtk.CellRendererText(), text=2)
        col.set_min_width(60)
        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysTreeview").append_column(col)
        # this sets up columns for process list
        col = Gtk.TreeViewColumn("Day", Gtk.CellRendererText(), text=0)
        col.set_min_width(140)
        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsApplsTreeview").append_column(col)

        # hide PT page by default
        self._timekprConfigDialogBuilder.get_object("timekprConfigNotebook").get_nth_page(self._timekprPTPageNr).set_visible(False)
        # hide PT config as well
        self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigPlayTimeGrid").set_visible(False)

        # initial config (everything is to the max)
        for i in range(0, 7):
            # set up default limits
            self._limitConfig[str(i+1)] = {cons.TK_CTRL_LIMITD: None, cons.TK_CTRL_INT: [[None, None, False]]}

        # initialize week and month limits
        self._limitConfig[cons.TK_CTRL_LIMITW] = {cons.TK_CTRL_LIMITW: None}
        self._limitConfig[cons.TK_CTRL_LIMITM] = {cons.TK_CTRL_LIMITM: None}

        # ## notification configuration ##
        # Less than
        rend = Gtk.CellRendererText()
        rend.set_property("editable", True)
        rend.set_property("placeholder-text", msg.getTranslation("TK_MSG_NOTIF_CONFIG_TIME_PHLD_LABEL"))
        rend.connect("edited", self.userTimeEdited)
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_NOTIF_CONFIG_TIME_LABEL"), rend, text=1)
        col.set_min_width(90)
        self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigTreeView").append_column(col)

        # importance
        rend = Gtk.CellRendererCombo()
        rend.set_property("editable", True)
        rend.set_property("placeholder-text", msg.getTranslation("TK_MSG_NOTIF_CONFIG_IMPORTANCE_PHLD_LABEL"))
        rend.set_property("model", self._timekprConfigDialogBuilder.get_object("TimekprNotificationPrioritiesLS"))
        rend.set_property("text-column", 1)
        rend.set_property("has-entry", False)
        rend.connect("edited", self.userPriorityEdited)
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_NOTIF_CONFIG_IMPORTANCE_LABEL"), rend, text=3)
        col.set_min_width(120)
        self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigTreeView").append_column(col)
        # clear
        self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS").clear()

        # ## PlayTime notification configuration ##
        # Less than
        rend = Gtk.CellRendererText()
        rend.set_property("editable", True)
        rend.set_property("placeholder-text", msg.getTranslation("TK_MSG_NOTIF_CONFIG_TIME_PHLD_LABEL"))
        rend.connect("edited", self.userPlayTimeEdited)
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_NOTIF_CONFIG_TIME_LABEL"), rend, text=1)
        col.set_min_width(90)
        self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigTreeView").append_column(col)

        # importance
        rend = Gtk.CellRendererCombo()
        rend.set_property("editable", True)
        rend.set_property("placeholder-text", msg.getTranslation("TK_MSG_NOTIF_CONFIG_IMPORTANCE_PHLD_LABEL"))
        rend.set_property("model", self._timekprConfigDialogBuilder.get_object("TimekprNotificationPrioritiesLS"))
        rend.set_property("text-column", 1)
        rend.set_property("has-entry", False)
        rend.connect("edited", self.userPlayTimePriorityEdited)
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_NOTIF_CONFIG_IMPORTANCE_LABEL"), rend, text=3)
        col.set_min_width(120)
        self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigTreeView").append_column(col)
        # clear
        self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigLS").clear()

        # status
        self.setStatus(msg.getTranslation("TK_MSG_STATUS_STARTED"))

    # --------------- TMP (move to proper places later) --------------- #

    def userTimeEdited(self, widget, path, text):
        """Set internal representation of in-place edited value"""
        self.setTimeValue(path, text, pConfType="Time")

    def userPlayTimeEdited(self, widget, path, text):
        """Set internal representation of in-place edited value"""
        self.setTimeValue(path, text, pConfType="PlayTime")

    def userPriorityEdited(self, widget, path, text):
        """Set internal representation of in-place edited value"""
        self.setPriorityValue(path, text, "Time")

    def userPlayTimePriorityEdited(self, widget, path, text):
        """Set internal representation of in-place edited value"""
        self.setPriorityValue(path, text, "PlayTime")

    def setTimeValue(self, path, text, pConfType):
        """Verify and set time string values"""
        # element
        prioLs = "TimekprUserNotificationConfigLS" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigLS"
        # store
        timelSt = self._timekprConfigDialogBuilder.get_object(prioLs)
        # value before
        secsBefore = timelSt[path][0]
        secs = None
        # verify values
        if _HOUR_REGEXP.match(text):
            # calculate seconds
            secs = min(int(_HOUR_REGEXP.sub(r"\1", text)) * cons.TK_LIMIT_PER_HOUR, cons.TK_LIMIT_PER_DAY)
        elif _HOUR_MIN_REGEXP.match(text):
            # calculate seconds
            secs = min(int(_HOUR_MIN_REGEXP.sub(r"\1", text)) * cons.TK_LIMIT_PER_HOUR + int(_HOUR_MIN_REGEXP.sub(r"\2", text)) * cons.TK_LIMIT_PER_MINUTE, cons.TK_LIMIT_PER_DAY)

        # if we could calculate seconds (i.e. entered text is correct)
        if secs is not None:
            # only if changed
            if secsBefore != secs:
                # check if we have this interval already
                dupl = [rPrio for rPrio in timelSt if rPrio[0] == secs]
                # we can not allow duplicates
                if not len(dupl) > 0:
                    # format secs
                    textStr = self.formatTimeStr(cons.TK_DATETIME_START + timedelta(seconds=secs), "s")
                    # set values
                    timelSt[path][0] = secs
                    timelSt[path][1] = textStr
                    # sort
                    self.sortNotificationConfig(pConfType)
                    # verify controls too
                    self.processConfigChanged()

    def setPriorityValue(self, path, text, pConfType):
        """Verify and set time string values"""
        # element
        prioLs = "TimekprUserNotificationConfigLS" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigLS"
        # store
        priolSt = self._timekprConfigDialogBuilder.get_object(prioLs)
        # value before
        prioBefore = priolSt[path][3]
        # only if priority actuall changed
        if prioBefore != text:
            # find selected value
            val = [(rVal[0], rVal[1]) for rVal in self._timekprConfigDialogBuilder.get_object("TimekprNotificationPrioritiesLS") if rVal[1] == text]
            # set values
            priolSt[path][2] = val[0][0]
            priolSt[path][3] = val[0][1]
            # verify controls too
            self.processConfigChanged()

    def addNotificationConfigClicked(self, evt):
        """Add notification interval to the list"""
        self.addNotificationConf("Time")

    def addPlayTimeNotificationConfigClicked(self, evt):
        """Add notification interval to the list"""
        self.addNotificationConf("PlayTime")

    def removeNotificationConfigClicked(self, evt):
        """Remove notification interval"""
        self.removeNotificationConf("Time")

    def removePlayTimeNotificationConfigClicked(self, evt):
        """Remove notification interval"""
        self.removeNotificationConf("PlayTime")

    def addNotificationConf(self, pConfType):
        """Add notification interval to the list"""
        prioSt = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigLS")
        prioTw = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigTreeView" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigTreeView")
        prioLen = len(prioSt)
        # add
        addRow = True

        # check if the last one is not empty (no need to add more empty rows)
        if (prioLen > 0 and prioSt[prioLen-1][0] < 0):
            addRow = False
        # we can add the row
        if addRow:
            # add
            prioSt.append([-1, "", "", ""])
            # scroll to end
            prioTw.set_cursor(prioLen)
            prioTw.scroll_to_cell(prioLen)

    def removeNotificationConf(self, pConfType):
        """Remove notification interval"""
        # defaults
        prioSt = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigLS")
        # refresh the child
        (tm, ti) = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigTreeView" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigTreeView").get_selection().get_selected()
        # only if there is smth selected
        elemIdx = tm.get_path(ti)[0] if ti is not None else None
        # only if something is selected
        if elemIdx is not None:
            rIdx = 0
            # remove selected item
            for rIt in prioSt:
                if elemIdx == rIdx:
                    # remove
                    prioSt.remove(rIt.iter)
                # count further
                rIdx += 1
            # verify controls too
            self.processConfigChanged()

    def sortNotificationConfig(self, pConfType):
        """Sort notification config for ease of use"""
        # element
        prioSt = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS" if pConfType == "Time" else "TimekprUserPlayTimeNotificationConfigLS")
        # sort vairables
        prio = {}
        rIdx = 0
        # prepare sort
        for rIt in prioSt:
            prio[rIt[0]] = rIdx
            # count further
            rIdx += 1
        # set sort order
        sortedPrio = []
        # set up proper order
        for rKey in sorted(prio, reverse=True):
            # append to order
            sortedPrio.append(prio[rKey])
        # reorder rows in liststore
        prioSt.reorder(sortedPrio)

    # --------------- helper methods --------------- #

    def formatTimeStr(self, pTime, pFormatType="f"):
        """Format time for output on form"""
        # f - full, s - short, t - time
        # final result
        timeStr = None
        if pTime is None:
            timeStr = _NO_TIME_LABEL_SHORT if pFormatType == "s" else _NO_TIME_LABEL if pFormatType == "t" else _NO_TIME_LIMIT_LABEL
        else:
            # calculate days
            days = (pTime - cons.TK_DATETIME_START).days
            # calculate hours and mins
            hrMin = "%s:%s" % (("24" if pFormatType != "f" and days >= 1 else str(pTime.hour)).rjust(2, "0"), str(pTime.minute).rjust(2, "0"))
            # calculate secs
            secs = str(pTime.second).rjust(2, "0")
            # final composition
            # for limit time (h:m:s)
            if pFormatType == "t":
                timeStr = "%s:%s" % (hrMin, secs)
            # for full time (d:h:m:s)
            else:
                timeStr = "%s:%s:%s" % (str(days).rjust(2, "0"), hrMin, secs) if pFormatType != "s" else hrMin
        # return
        return timeStr

    def renewUserConfiguration(self):
        """Update configuration options"""
        # if speech is not supported, we disable and uncheck the box
        self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").set_sensitive(self._timekprClientConfig.getIsNotificationSpeechSupported())
        # if sound is not supported by libnotify implementation, we disable and uncheck the box
        self._timekprConfigDialogBuilder.get_object("timekprUseNotificationSoundCB").set_sensitive(self._timekprClientConfig.getIsNotificationSoundSupported())

        # user config
        self._timekprConfigDialogBuilder.get_object("timekprLimitChangeNotifCB").set_active(self._timekprClientConfig.getClientShowLimitNotifications())
        self._timekprConfigDialogBuilder.get_object("timekprShowAllNotifCB").set_active(self._timekprClientConfig.getClientShowAllNotifications())
        self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").set_active(self._timekprClientConfig.getClientUseSpeechNotifications())
        self._timekprConfigDialogBuilder.get_object("timekprShowSecondsCB").set_active(self._timekprClientConfig.getClientShowSeconds())
        self._timekprConfigDialogBuilder.get_object("timekprUseNotificationSoundCB").set_active(self._timekprClientConfig.getClientUseNotificationSound())
        self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutSB").set_value(self._timekprClientConfig.getClientNotificationTimeout())
        self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutCriticalSB").set_value(self._timekprClientConfig.getClientNotificationTimeoutCritical())
        self._timekprConfigDialogBuilder.get_object("timekprLogLevelSB").set_value(self._timekprClientConfig.getClientLogLevel())
        # priority config
        prioConfSt = self._timekprConfigDialogBuilder.get_object("TimekprNotificationPrioritiesLS")
        # load notification priorities
        prioSt = self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS")
        prioSt.clear()
        for rPrio in self._timekprClientConfig.getClientNotificationLevels():
            # append intervals
            val = [(rVal[0], rVal[1]) for rVal in prioConfSt if rVal[0] == cons.TK_PRIO_LVL_MAP[rPrio[1]]]
            prioSt.append([rPrio[0], self.formatTimeStr(cons.TK_DATETIME_START + timedelta(seconds=rPrio[0]), "s"), val[0][0], val[0][1]])
        # sort configd
        self.sortNotificationConfig("Time")
        # load PlayTime notification priorities
        prioSt = self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigLS")
        prioSt.clear()
        for rPrio in self._timekprClientConfig.getClientPlayTimeNotificationLevels():
            # append intervals
            val = [(rVal[0], rVal[1]) for rVal in prioConfSt if rVal[0] == cons.TK_PRIO_LVL_MAP[rPrio[1]]]
            prioSt.append([rPrio[0], self.formatTimeStr(cons.TK_DATETIME_START + timedelta(seconds=rPrio[0]), "s"), val[0][0], val[0][1]])
        # sort config
        self.sortNotificationConfig("PlayTime")
        # verify controls too
        self.processConfigChanged()

    def renewLimits(self, pTimeInformation=None):
        """Renew information to be show for user in GUI"""
        # sets time left
        if pTimeInformation is not None:
            # limits
            self._timeSpent = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_SPENT])
            self._timeSpentWeek = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_SPENTW])
            self._timeSpentMonth = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_SPENTM])
            self._timeInactive = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_SLEEP])
            self._timeLeftToday = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_LEFTD])
            self._timeLeftContinous = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_LEFT])
            self._timeTrackInactive = True if pTimeInformation[cons.TK_CTRL_TRACK] else False
            self._timeTimeLimitOverridePT = bool(pTimeInformation[cons.TK_CTRL_PTTLO]) if cons.TK_CTRL_PTTLO in pTimeInformation else False
            self._timeUnaccountedIntervalsFlagPT = bool(pTimeInformation[cons.TK_CTRL_PTAUH]) if cons.TK_CTRL_PTAUH in pTimeInformation else False
            self._timeSpentPT = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_PTSPD]) if cons.TK_CTRL_PTSPD in pTimeInformation else None
            self._timeLeftPT = cons.TK_DATETIME_START + timedelta(seconds=pTimeInformation[cons.TK_CTRL_PTLPD]) if cons.TK_CTRL_PTLPD in pTimeInformation else None
            self._timePTActivityCntStr = str(pTimeInformation[cons.TK_CTRL_PTLSTC] if cons.TK_CTRL_PTLSTC in pTimeInformation else 0)

        # calculate strings to show (and show only those, which have data)
        timeSpentStr = self.formatTimeStr(self._timeSpent)
        timeSpentWeekStr = self.formatTimeStr(self._timeSpentWeek)
        timeSpentMonthStr = self.formatTimeStr(self._timeSpentMonth)
        timeSleepStr = self.formatTimeStr(self._timeInactive)
        timeLeftTodayStr = self.formatTimeStr(self._timeLeftToday)
        timeLeftTotalStr = self.formatTimeStr(self._timeLeftContinous)
        timeSpentPTStr = self.formatTimeStr(self._timeSpentPT)
        timeLeftPTStr = self.formatTimeStr(self._timeLeftPT if self._timeLeftPT is None else min(self._timeLeftPT, self._timeLeftToday)) if not self._timeTimeLimitOverridePT else _NO_TIME_LABEL

        # sets up stuff
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpeneLB").set_text(timeSpentStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpentWeeeLB").set_text(timeSpentWeekStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeSpentMonteLB").set_text(timeSpentMonthStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeInactiveLB").set_text(timeSleepStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTimeLeftTodaeLB").set_text(timeLeftTodayStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoContTimeLefeLB").set_text(timeLeftTotalStr)
        self._timekprConfigDialogBuilder.get_object("timekprLimitInfoTrackInactiveCB").set_active(self._timeTrackInactive)
        self._timekprConfigDialogBuilder.get_object("timekprPTLimitInfoTimeLimitOverrideLB").set_active(self._timeTimeLimitOverridePT)
        self._timekprConfigDialogBuilder.get_object("timekprPTLimitInfoUnaccountedIntervalsFlagLB").set_active(self._timeUnaccountedIntervalsFlagPT)
        self._timekprConfigDialogBuilder.get_object("timekprPTLimitInfoTimeSpentTodayLB").set_text(timeSpentPTStr)
        self._timekprConfigDialogBuilder.get_object("timekprPTLimitInfoTimeLeftTodayLB").set_text(timeLeftPTStr)
        self._timekprConfigDialogBuilder.get_object("timekprPTLimitInfoActivityCountLB").set_text(self._timePTActivityCntStr)

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
            # new limits appeared
            self._limitConfig = pLimits

        # hide PT page by default
        enablePT = False
        # clear out days / limits / processes
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysLS").clear()
        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysLS").clear()
        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsActsLS").clear()

        # go in sorted order
        for rKey in sorted(self._limitConfig):
            # some of configuration needs different approach
            if rKey in (cons.TK_CTRL_LIMITW, cons.TK_CTRL_LIMITM):
                # set locally
                if self._limitConfig[rKey][rKey] is not None:
                    # limit
                    timeLimitWKMON = cons.TK_DATETIME_START + timedelta(seconds=self._limitConfig[rKey][rKey])
                    # limit
                    timeLimitWKMONStr = self.formatTimeStr(timeLimitWKMON)
                else:
                    timeLimitWKMONStr = _NO_TIME_LIMIT_LABEL

                # set week limit
                if rKey == cons.TK_CTRL_LIMITW:
                    # set up limits
                    self._timekprConfigDialogBuilder.get_object("timekprLimitForWeeeLB").set_text(timeLimitWKMONStr)
                elif rKey == cons.TK_CTRL_LIMITM:
                    # set up limits
                    self._timekprConfigDialogBuilder.get_object("timekprLimitForMonteLB").set_text(timeLimitWKMONStr)
            # check for override
            elif rKey == cons.TK_CTRL_PTTLO:
                # if enabled
                self._timeTimeLimitOverridePT = True if bool(self._limitConfig[rKey][rKey]) else False
            # check for allowed during unaccounted intervals
            elif rKey == cons.TK_CTRL_PTAUH:
                # if enabled
                self._timeUnaccountedIntervalsFlagPT = True if bool(self._limitConfig[rKey][rKey]) else False
            # for the days limits
            elif rKey in ("1", "2", "3", "4", "5", "6", "7"):
                # get time limit string
                timeLimitStr = self.formatTimeStr(cons.TK_DATETIME_START + timedelta(seconds=self._limitConfig[rKey][cons.TK_CTRL_LIMITD]) if self._limitConfig[rKey][cons.TK_CTRL_LIMITD] is not None else None, "t")
                # add limit to the list
                self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysLS").append([rKey, (cons.TK_DATETIME_START + timedelta(days=int(rKey)-1)).strftime("%A"), "%s" % (timeLimitStr)])

        # current day
        currDay = datetime.now().isoweekday()-1
        # calculate day index for scrolling
        dayIdx = 0
        finalDayIdx = None

        # PT limits are processed separately due to override detection
        if cons.TK_CTRL_PTLMT in self._limitConfig and cons.TK_CTRL_PTLST in self._limitConfig and cons.TK_CTRL_PTTLE in self._limitConfig:
            # PlayTime
            for rKey in (cons.TK_CTRL_PTLMT, cons.TK_CTRL_PTLST, cons.TK_CTRL_PTTLE):
                # PT enable
                if rKey == cons.TK_CTRL_PTTLE:
                    # enable PT
                    enablePT = bool(self._limitConfig[rKey][cons.TK_CTRL_PTTLE])
                # PT limits
                elif rKey == cons.TK_CTRL_PTLMT:
                    # for all days
                    for rDay in self._limitConfig[rKey][cons.TK_CTRL_PTLMT]:
                        # count
                        dayIdx += 1
                        # if override enabled, we do not show limits because that's not meaningful
                        timeLimitStr = self.formatTimeStr(cons.TK_DATETIME_START + timedelta(seconds=rDay[1]) if not self._timeTimeLimitOverridePT else None, "t")
                        # add to the list
                        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysLS").append([rDay[0], (cons.TK_DATETIME_START + timedelta(days=int(rDay[0])-1)).strftime("%A"), "%s" % (timeLimitStr)])
                        # if alllowed list has current day
                        if currDay == int(rDay[0]) + 1:
                            # index
                            finalDayIdx = dayIdx
                # PT process list
                elif rKey == cons.TK_CTRL_PTLST:
                    # all activities (source array format: 0 - friendly name, 1 - process name)
                    for rAppl in self._limitConfig[rKey][cons.TK_CTRL_PTLST]:
                        # add process to the list
                        self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsActsLS").append(["%s" % (rAppl[1] if rAppl[1] != "" else rAppl[0])])

        # determine curent day and point to it
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").set_cursor(currDay)
        self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").scroll_to_cell(currDay)
        # do the same for PT
        if finalDayIdx is not None:
            # scroll to current day
            self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysTreeview").set_cursor(currDay)
            self._timekprConfigDialogBuilder.get_object("timekprPTAllowedDaysLimitsDaysTreeview").scroll_to_cell(currDay)

    def processConfigChanged(self):
        """Determine whether config has been changed and enable / disable apply"""
        # initial
        configChanged = False
        # determine what's changed
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprLimitChangeNotifCB").get_active() != self._timekprClientConfig.getClientShowLimitNotifications()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprShowAllNotifCB").get_active() != self._timekprClientConfig.getClientShowAllNotifications()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").get_active() != self._timekprClientConfig.getClientUseSpeechNotifications()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprShowSecondsCB").get_active() != self._timekprClientConfig.getClientShowSeconds()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprUseNotificationSoundCB").get_active() != self._timekprClientConfig.getClientUseNotificationSound()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutSB").get_value_as_int() != self._timekprClientConfig.getClientNotificationTimeout()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutCriticalSB").get_value_as_int() != self._timekprClientConfig.getClientNotificationTimeoutCritical()
        configChanged = configChanged or self._timekprConfigDialogBuilder.get_object("timekprLogLevelSB").get_value_as_int() != self._timekprClientConfig.getClientLogLevel()
        # interval changes
        tmpVal = [[rVal[0], cons.TK_PRIO_LVL_MAP[rVal[2]]] for rVal in self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS") if rVal[2] in cons.TK_PRIO_LVL_MAP and rVal[0] > 0]
        configChanged = configChanged or self._timekprClientConfig.getClientNotificationLevels() != tmpVal
        # interval changes
        tmpVal = [[rVal[0], cons.TK_PRIO_LVL_MAP[rVal[2]]] for rVal in self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigLS") if rVal[2] in cons.TK_PRIO_LVL_MAP and rVal[0] > 0]
        configChanged = configChanged or self._timekprClientConfig.getClientPlayTimeNotificationLevels() != tmpVal

        # this is it
        self._timekprConfigDialogBuilder.get_object("timekprSaveBT").set_sensitive(configChanged)

    # --------------- init methods --------------- #

    def initAboutForm(self):
        """Initialize about form"""
        # version
        self._timekprAboutDialog.set_version(self._timekprVersion)
        # comment
        self._timekprAboutDialog.set_comments(msg.getTranslation("TK_MSG_LOGO_LABEL"))

        # show up all
        self._timekprAboutDialog.show()
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
        self._timekprConfigDialog.show()
        self._timekprConfigDialog.run()

        # hide for later use
        self._timekprConfigDialog.hide()

    # --------------- user clicked methods --------------- #

    def clientConfigChangedSignal(self, evt):
        """Process config changed signal"""
        self.processConfigChanged()

    def daysChangedSignal(self, evt):
        """Refresh intervals when days change"""
        # refresh the child
        (tm, ti) = self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysDaysTreeview").get_selection().get_selected()
        # only if there is smth selected
        if ti is not None:
            # get current seconds
            dt = datetime.now().replace(microsecond=0)
            dtd = str(datetime.date(dt).isoweekday())
            dts = int((dt - datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)).total_seconds())
            idx = 0
            selIdx = 0
            # clear out existing intervals
            self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").clear()
            # fill intervals only if that day exists
            if tm.get_value(ti, 0) in self._limitConfig:
                # if no intervals
                if not self._limitConfig[tm.get_value(ti, 0)][cons.TK_CTRL_INT]:
                    # fill in the intervals with empty values
                    self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").append([("%s - %s") % (_NO_TIME_LABEL_SHORT, _NO_TIME_LABEL_SHORT), ""])
                else:
                    # fill the intervals
                    for r in self._limitConfig[tm.get_value(ti, 0)][cons.TK_CTRL_INT]:
                        # determine which is the current hour
                        selIdx = idx if r[0] is not None and r[0] <= dts <= r[1] and dtd == tm.get_value(ti, 0) else selIdx
                        # if we have no data, we fill this up with nothing
                        if r[0] is None or (r[0] == 0 and r[1] == 0):
                            # fill in the intervals with empty values
                            self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").append([("%s - %s") % (_NO_TIME_LABEL_SHORT, _NO_TIME_LABEL_SHORT), ""])
                        else:
                            start = (cons.TK_DATETIME_START + timedelta(seconds=r[0]))
                            end = (cons.TK_DATETIME_START + timedelta(seconds=r[1]))
                            uacc = "∞" if r[2] else ""
                            # fill in the intervals
                            self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsLS").append([("%s:%s - %s:%s") % (str(start.hour).rjust(2, "0"), str(start.minute).rjust(2, "0"), str(end.hour).rjust(2, "0") if r[1] < cons.TK_LIMIT_PER_DAY else "24", str(end.minute).rjust(2, "0")), uacc])
                        # count
                        idx += 1
                # set selection to found row
                self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsTreeview").set_cursor(selIdx)
                self._timekprConfigDialogBuilder.get_object("timekprAllowedDaysIntervalsTreeview").scroll_to_cell(selIdx)

    def configPageSwitchSignal(self, nb=None, pg=None, pgn=None):
        """Enable or disable apply on page change"""
        # nothing here
        pass

    def saveUserConfigSignal(self, evt):
        """Save the configuration using config file manager"""
        # get config, set config to manager and save it
        self._timekprClientConfig.setClientShowLimitNotifications(self._timekprConfigDialogBuilder.get_object("timekprLimitChangeNotifCB").get_active())
        self._timekprClientConfig.setClientShowAllNotifications(self._timekprConfigDialogBuilder.get_object("timekprShowAllNotifCB").get_active())
        self._timekprClientConfig.setClientUseSpeechNotifications(self._timekprConfigDialogBuilder.get_object("timekprUseSpeechNotifCB").get_active())
        self._timekprClientConfig.setClientShowSeconds(self._timekprConfigDialogBuilder.get_object("timekprShowSecondsCB").get_active())
        self._timekprClientConfig.setClientUseNotificationSound(self._timekprConfigDialogBuilder.get_object("timekprUseNotificationSoundCB").get_active())
        self._timekprClientConfig.setClientNotificationTimeout(self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutSB").get_value_as_int())
        self._timekprClientConfig.setClientNotificationTimeoutCritical(self._timekprConfigDialogBuilder.get_object("timekprNotificationTimeoutCriticalSB").get_value_as_int())
        self._timekprClientConfig.setClientLogLevel(self._timekprConfigDialogBuilder.get_object("timekprLogLevelSB").get_value_as_int())
        # save notification priorities
        tmpVal = [[rVal[0], cons.TK_PRIO_LVL_MAP[rVal[2]]] for rVal in self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigLS") if rVal[2] in cons.TK_PRIO_LVL_MAP and rVal[0] > 0]
        self._timekprClientConfig.setClientNotificationLevels(tmpVal)
        # save PlayTime notification priorities
        tmpVal = [[rVal[0], cons.TK_PRIO_LVL_MAP[rVal[2]]] for rVal in self._timekprConfigDialogBuilder.get_object("TimekprUserPlayTimeNotificationConfigLS") if rVal[2] in cons.TK_PRIO_LVL_MAP and rVal[0] > 0]
        self._timekprClientConfig.setClientPlayTimeNotificationLevels(tmpVal)

        # save config
        self._timekprClientConfig.saveClientConfig()
        # disable apply for now
        self._timekprConfigDialogBuilder.get_object("timekprSaveBT").set_sensitive(False)
        # enable as well
        log.setLogLevel(self._timekprClientConfig.getClientLogLevel())

    def closePropertiesSignal(self, evt):
        """Close the config form"""
        # close
        self._timekprConfigDialog.hide()

    def preventDestroyingDialogSignal(self, evt, bs):
        """Prevent destroying the dialog"""
        return False

    # --------------- helper methods --------------- #

    def isPlayTimeAccountingInfoEnabled(self):
        """Whether PlayTime controls are enabled"""
        return self._timekprConfigDialogBuilder.get_object("timekprConfigNotebook").get_nth_page(self._timekprPTPageNr).get_visible()

    def setPlayTimeAccountingInfoEnabled(self, pState):
        """Whether PlayTime controls are enabled"""
        # enable page
        self._timekprConfigDialogBuilder.get_object("timekprConfigNotebook").get_nth_page(self._timekprPTPageNr).set_visible(pState)
        # enable config
        self._timekprConfigDialogBuilder.get_object("TimekprUserNotificationConfigPlayTimeGrid").set_visible(pState)
