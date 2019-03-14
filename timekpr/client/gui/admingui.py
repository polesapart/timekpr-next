"""
Created on Aug 28, 2018

@author: mjasnik
"""

import gi
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
import time
from gettext import gettext as _
from datetime import datetime, timedelta

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.client.interface.dbus.administration import timekprAdminConnector

from timekpr.common.utils.config import timekprClientConfig
from timekpr.client.interface.speech.espeak import timekprSpeech

# constant
_NO_TIME_LABEL = "--:--:--"
_NO_TIME_LABEL_SHORT = "--:--"
_NO_TIME_LIMIT_LABEL = "--:--:--:--"


class timekprAdminGUI(object):
    """Main class for supporting timekpr forms"""

    def __init__(self, pTimekprVersion, pResourcePath, pUsername, pIsDevActive):
        """Initialize gui"""
        # init locale
        self.initLocale()

        # set up base variables
        self._userName = pUsername
        self._timekprVersion = pTimekprVersion
        self._resourcePath = pResourcePath
        self._timekprAdminConnector = None
        self._isDevActive = pIsDevActive
        self._isConnected = False

        # ## forms builders ##
        # init config builder
        self._timekprAdminFormBuilder = Gtk.Builder()
        # get our dialog
        self._timekprAdminFormBuilder.add_from_file(os.path.join(self._resourcePath, "admin.glade"))
        # connect signals, so they get executed
        self._timekprAdminFormBuilder.connect_signals(self)
        # get window
        self._timekprAdminForm = self._timekprAdminFormBuilder.get_object("TimekprApplicationWindow")

        # set up GUI elements
        self.initGUIElements()

        # initialize internal stuff
        self.initInternalConfiguration()
        # disable all buttons firstly
        self.toggleControls(False)
        # status
        self.setStatus(True, "Started")

        # initialize internal stuff
        GLib.timeout_add_seconds(1, self.initTimekprAdmin)

        # loop
        self._mainLoop = GLib.MainLoop()

        # show up all
        self._timekprAdminForm.show_all()

        # this seems to be needed
        self.dummyPageChanger()

        # start main loop
        self._mainLoop.run()

    # --------------- initialization methods --------------- #

    def dummyPageChanger(self):
        # change pages (so objects get initialized, w/o this, spin butons don't get values when set :O)
        for rIdx in [1, 0]:
            self._timekprAdminFormBuilder.get_object("TimekprMainTabBar").set_current_page(rIdx)
        for rIdx in [1, 2, 0]:
            self._timekprAdminFormBuilder.get_object("TimekprConfigurationTabBar").set_current_page(rIdx)

    # init timekpr admin client
    def initTimekprAdmin(self):
        """Initialize admin client"""
        # get our connector
        self._timekprAdminConnector = timekprAdminConnector(self._isDevActive)
        # connect
        GLib.timeout_add_seconds(0, self._timekprAdminConnector.initTimekprConnection, False)
        # check connection
        GLib.timeout_add_seconds(0.1, self.checkConnection)
        # user config retriever
        GLib.timeout_add_seconds(cons.TK_SAVE_INTERVAL / 2, self.userSelectionChanged, None)

    def checkConnection(self):
        """Check connection on the fly"""
        # connection statuses
        interfacesOk, connecting = self._timekprAdminConnector.isConnected()

        # if not connected, give up and get out
        if interfacesOk and connecting:
            # status
            self.setStatus(True, "Connected")
            # connected
            self._isConnected = True
            # get users
            GLib.timeout_add_seconds(0, self.getUserList)
        elif not interfacesOk and connecting:
            # status
            self.setStatus(True, "Connecting...")
            # invoke again
            GLib.timeout_add_seconds(1, self.checkConnection)
        else:
            # status
            self.setStatus(True, "Failed to connect")

    def initLocale(self):
        """Init translation stuff"""
        # init python gettext
        # gettext.bindtextdomain("timekpr-next", "/usr/share/locale")
        # gettext.textdomain("timekpr-next")
        pass

    def initGUIElements(self):
        """Initialize all GUI elements for stores"""
        # ## days ##

        # day name
        col = Gtk.TreeViewColumn("Day", Gtk.CellRendererText(), text=1)
        col.set_min_width(90)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # day enabled
        rend = Gtk.CellRendererToggle()
        rend.connect("toggled", self.dayAvailabilityChanged)
        col = Gtk.TreeViewColumn("Enabled", rend, active=2)
        col.set_min_width(35)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # final col
        rend = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Limit", rend, text=4)
        col.set_min_width(60)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # final col
        col = Gtk.TreeViewColumn("", Gtk.CellRendererText())
        col.set_min_width(10)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # ## intervals ##

        # from hour
        col = Gtk.TreeViewColumn("From", Gtk.CellRendererText(), text=1)
        col.set_min_width(40)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)

        # to hour
        col = Gtk.TreeViewColumn("To", Gtk.CellRendererText(), text=2)
        col.set_min_width(40)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)

        # to hour
        col = Gtk.TreeViewColumn("", Gtk.CellRendererText())
        col.set_min_width(10)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)

        # clear out existing intervals
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS").clear()

        # lets prepare week days
        for rDay in range(1, 7+1):
            # fill in the intervals
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS").append([str(rDay), (cons.TK_DATETIME_START + timedelta(days=rDay-1)).strftime("%A"), False, 0, _NO_TIME_LABEL])

    def initInternalConfiguration(self):
        """This initializes the internal configuration for admin form"""
        self._controlButtons = [
            # combo
            "TimekprUserSelectionCB"
            # combom refresh
            ,"TimekprUserSelectionRefreshBT"
            # check box
            ,"TimekprUserConfTodaySettingsTrackInactiveCB"
            ,"TimekprUserConfMONCB"
            ,"TimekprUserConfWKCB"
            # control buttons
            ,"TimekprUserConfTodaySettingsSetAddBT"
            ,"TimekprUserConfTodaySettingsSetSubractBT"
            ,"TimekprUserConfTodaySettingsSetSetBT"
            ,"TimekprUserConfTodaySettingsTrackInactiveSetBT"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsAddBT"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsSubtractBT"
            ,"TimekprUserConfDaySettingsApplyBT"
            ,"TimekprUserConfWKMONApplyBT"
            ,"TimekprTrackingSessionsAddBT"
            ,"TimekprTrackingSessionsRemoveBT"
            ,"TimekprExcludedSessionsAddBT"
            ,"TimekprExcludedSessionsRemoveBT"
            ,"TimekprExcludedUsersAddBT"
            ,"TimekprExcludedUsersRemoveBT"
            ,"TimekprConfigurationApplyBT"
            ,"TimekprUserConfDaySettingsConfDayApplyBT"
            # spin buttons for adjustments
            ,"TimekprUserConfTodaySettingsSetMinSB"
            ,"TimekprUserConfTodaySettingsSetHrSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsToHrSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"
            ,"TimekprUserConfWKDaySB"
            ,"TimekprUserConfWKHrSB"
            ,"TimekprUserConfWKMinSB"
            ,"TimekprUserConfMONDaySB"
            ,"TimekprUserConfMONHrSB"
            ,"TimekprUserConfMONMinSB"
            ,"TimekprConfigurationLoglevelSB"
            ,"TimekprConfigurationWarningTimeSB"
            ,"TimekprConfigurationPollIntervalSB"
            ,"TimekprConfigurationSaveTimeSB"
            ,"TimekprConfigurationTerminationTimeSB"
            ,"TimekprUserConfDaySettingsConfDaySetHrSB"
            ,"TimekprUserConfDaySettingsConfDaySetMinSB"
            # entry fields
            ,"TimekprTrackingSessionsEntryEF"
            ,"TimekprExcludedSessionsEntryEF"
            ,"TimekprExcludedUsersEntryEF"
            # lists
            ,"TimekprWeekDaysTreeView"
            ,"TimekprHourIntervalsTreeView"
            ,"TimekprTrackingSessionsTreeView"
            ,"TimekprExcludedSessionsTreeView"
            ,"TimekprExcludedUsersTreeView"
        ]

        # sets up limit variables
        self._timeTrackInactive = False
        self._timeLimitWeek = 0
        self._timeLimitMonth = 0
        self._timeLimitDays = []
        self._timeLimitDaysLimits = []
        self._timeLimitDaysHoursActual = {}
        for rDay in range(1, 7+1):
            self._timeLimitDaysHoursActual[str(rDay)] = {}
            for rHour in range(1, 23+1):
                self._timeLimitDaysHoursActual[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}
        # saved means from server, actual means modified in form
        self._timeLimitDaysHoursSaved = self._timeLimitDaysHoursActual.copy()

    # --------------- control  / helper methods --------------- #

    def getSelectedUserName(self):
        """Get selected username"""
        # result
        userName = None
        # get username
        if self._isConnected:
            userCombobox = self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB")
            # get chosen index, model and actual id of the item
            userIdx = userCombobox.get_active()
            userModel = userCombobox.get_model()
            # only if we have selection
            if userIdx is not None and userModel is not None:
                # get username
                userName = userModel[userIdx][0]

        # result
        return userName

    def toggleControls(self, pEnable=True, pLeaveUserList=False):
        """Enable or disable all controls for the form"""
        # apply settings to all buttons`
        for rButton in self._controlButtons:
            # if we need to leave user selection intact
            if not (pLeaveUserList and rButton == "TimekprUserSelectionCB"):
                # get the button
                self._timekprAdminFormBuilder.get_object(rButton).set_sensitive(pEnable)

        # if disable
        if not pEnable:
            self.clearAdminForm()

    def setStatus(self, pConnectionStatus, pStatus):
        """Change status of timekpr admin client"""
        if pStatus is not None:
            # connection
            if pConnectionStatus is True:
                # get main status
                statusBar = self._timekprAdminFormBuilder.get_object("TimekprConnectionStatusbar")
            else:
                # get message status
                statusBar = self._timekprAdminFormBuilder.get_object("TimekprMessagesStatusbar")

            # get context
            contextId = statusBar.get_context_id("status")
            # pop existing message and add new one
            statusBar.remove_all(contextId)
            statusBar.push(contextId, pStatus)

    def clearAdminForm(self):
        """This default everything to default values"""
        # clear form
        for rCtrl in ["TimekprUserConfTodayInfoSpentTodayLB", "TimekprUserConfTodayInfoSpentWeekLB", "TimekprUserConfTodayInfoSpentMonthLB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_text(_NO_TIME_LIMIT_LABEL)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_active(False)
        for rDay in range(1, 7+1):
            # clear list store
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][2] = False
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][3] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][4] = _NO_TIME_LABEL

            # clear day config
            for rHour in range(1, 23+1):
                self._timeLimitDaysHoursActual[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # clear up the intervals
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()

        # this clears hours for week and month
        for rCtrl in ["TimekprUserConfWKDaySB", "TimekprUserConfWKHrSB", "TimekprUserConfWKHrSB", "TimekprUserConfMONDaySB", "TimekprUserConfMONDaySB", "TimekprUserConfMONHrSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")

        # TODO: eventually we'll need to add a lot of stuff here

    def formatInterval(self, pTotalSeconds):
        """This just formats the intervals"""
        # get time out of seconds
        time = cons.TK_DATETIME_START + timedelta(seconds=pTotalSeconds)
        # value
        return str(24 if pTotalSeconds >= cons.TK_LIMIT_PER_DAY else time.hour).rjust(2, "0") + ":" + str(0 if pTotalSeconds >= cons.TK_LIMIT_PER_DAY else time.minute).rjust(2, "0")

    def getIntervalList(self, pDay):
        """Get intervals for use in GUI"""
        # init hours for intervals
        timeLimits = []
        startTimeStr = None
        endTimeStr = None
        startSeconds = None
        endSeconds = None

        # loop through all days
        for rHour in range(0, 23+1):
            # define intervals
            if startTimeStr is not None and endTimeStr is not None:
                if str(rHour) not in self._timeLimitDaysHoursActual[pDay] or self._timeLimitDaysHoursActual[pDay][str(rHour)][cons.TK_CTRL_SMIN] != 0:
                    timeLimits.append([startTimeStr, endTimeStr, startSeconds, endSeconds])
                    startTimeStr = None
                    endTimeStr = None

            # we process only hours that are available
            if str(rHour) in self._timeLimitDaysHoursActual[pDay]:
                # if start hour is not yet defined
                if startTimeStr is None:
                    # first avaiable hour
                    startSeconds = rHour * cons.TK_LIMIT_PER_HOUR + self._timeLimitDaysHoursActual[pDay][str(rHour)][cons.TK_CTRL_SMIN] * cons.TK_LIMIT_PER_MINUTE
                    startTimeStr = self.formatInterval(startSeconds)

                # define end hour
                endDate = cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timeLimitDaysHoursActual[str(pDay)][str(rHour)][cons.TK_CTRL_EMIN])
                endSeconds = (endDate - cons.TK_DATETIME_START).total_seconds()
                endTimeStr = self.formatInterval(endSeconds)

                # define intervals
                if self._timeLimitDaysHoursActual[pDay][str(rHour)][cons.TK_CTRL_EMIN] != 60 or rHour == 23:
                    timeLimits.append([startTimeStr, endTimeStr, startSeconds, endSeconds])
                    startTimeStr = None
                    endTimeStr = None

        # return
        return timeLimits

    def getWeekLimitSecs(self):
        # count secs
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").get_text()) * cons.TK_LIMIT_PER_DAY
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # return
        return totalSecs

    def getMonthLimitSecs(self):
        # count secs
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfMONDaySB").get_text()) * cons.TK_LIMIT_PER_DAY
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfMONHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfMONMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # return
        return totalSecs

    def getSelectedDay(self):
        """Get selected day from day list"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # idx
            dayIdx = tm.get_path(ti)[0]
            dayNumber = str(tm.get_value(ti, 0))
        else:
            # nothing
            dayIdx = None
            dayNumber = None

        # return
        return dayIdx, dayNumber

    def getSelectedHourInterval(self):
        """Get selected hour interval from hour interval list"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # idx
            hourIdx = tm.get_path(ti)[0]
            hourNumber = str(tm.get_value(ti, 0))
        else:
            # nothing
            hourIdx = None
            hourNumber = None

        # return
        return hourIdx, hourNumber

    def sortHourIntervals(self):
        # sort vairables
        hours = {}
        rIdx = 0

        # prepare sort
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS"):
            hours[rIt[4]] = rIdx
            # count further
            rIdx += 1

        # set sort order
        sortedHours = []
        # set up proper order
        for rKey in sorted(hours):
            # append to order
            sortedHours.append(hours[rKey])

        # reorder rows in liststore
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").reorder(sortedHours)

    def applyUserConfig(self):
        # ## track inactive ##
        # set value
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_active(self._timeTrackInactive)
        # enable field & set button
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_sensitive(True)

        # enable refresh
        self._timekprAdminFormBuilder.get_object("TimekprUserSelectionRefreshBT").set_sensitive(True)

        # ## allowed days ###
        for rDay in range(1, 7+1):
            # if we have a day
            if rDay in self._timeLimitDays:
                # enable certain days
                self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][2] = True
            else:
                # disable certain days
                self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][2] = False

        # enable editing
        for rCtrl in ["TimekprWeekDaysTreeView", "TimekprHourIntervalsTreeView", "TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(True)

        # ## limits per allowed days ###
        for rDay in range(0, len(self._timeLimitDaysLimits)):
            # calculate time
            limitTime = cons.TK_DATETIME_START + timedelta(seconds=self._timeLimitDaysLimits[int(rDay)])
            limit = "%s:%s:%s" % ("24" if self._timeLimitDaysLimits[int(rDay)] >= cons.TK_LIMIT_PER_DAY else str(limitTime.hour).rjust(2, "0"), str(limitTime.minute).rjust(2, "0"), str(limitTime.second).rjust(2, "0"))

            # enable certain days
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][3] = self._timeLimitDaysLimits[int(rDay)]
            # set appropriate label as well
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][4] = limit if rDay + 1 in self._timeLimitDays else _NO_TIME_LABEL

        # ## limit per week ##
        timeLimitWeek = cons.TK_DATETIME_START + timedelta(seconds=self._timeLimitWeek)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").set_text(str((timeLimitWeek - cons.TK_DATETIME_START).days))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKHrSB").set_text(str(timeLimitWeek.hour))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMinSB").set_text(str(timeLimitWeek.minute))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_sensitive(True)
        # enable box only when days are less than total limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_active(self._timeLimitWeek != cons.TK_LIMIT_PER_WEEK)

        # ## limit per month ##
        timeLimitMonth = cons.TK_DATETIME_START + timedelta(seconds=self._timeLimitMonth)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONDaySB").set_text(str((timeLimitMonth - cons.TK_DATETIME_START).days))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONHrSB").set_text(str(timeLimitMonth.hour))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONMinSB").set_text(str(timeLimitMonth.minute))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_sensitive(True)
        # enable box only when days are less than total limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_active(self._timeLimitMonth != cons.TK_LIMIT_PER_MONTH)

        # set selection to first row
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").set_cursor(0)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

    def calculateControlAvailability(self):
        # ## add time today ##
        enabled = (int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").get_text()) != 0 or int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetMinSB").get_text()))
        for rCtrl in ["TimekprUserConfTodaySettingsSetAddBT", "TimekprUserConfTodaySettingsSetSubractBT", "TimekprUserConfTodaySettingsSetSetBT"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(enabled)

        # ## track inactive ##
        # enable field if different from what is set
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveSetBT").set_sensitive(self._timeTrackInactive != self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").get_active())

        # ## day config ##
        enabledDays = 0
        # enable field if different from what is set
        for rDay in range(1, 7+1):
            # check whether day and config is different
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)-1][2]:
                enabledDays += 1
        # days are the same, no need to enable button
        enabled = (len(self._timeLimitDays) != enabledDays)

        # ## limits per allowed days ###
        for rDay in range(0, len(self._timeLimitDaysLimits)):
            # check if different
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)][3] != self._timeLimitDaysLimits[int(rDay)]:
                # enable apply
                enabled = True
                # this is it
                break

        # ## hour intervals ###
        if not enabled:
            for rDay in range(0, len(self._timeLimitDaysLimits)):
                # check if different
                if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)][3] != self._timeLimitDaysLimits[int(rDay)]:
                    # enable apply
                    enabled = True
                    # this is it
                    break

        # ## hour intervals ###
        # comapre saved and actual lists
        enabled = enabled or self._timeLimitDaysHoursSaved != self._timeLimitDaysHoursActual

        # enable apply
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsApplyBT").set_sensitive(enabled)

        # ## limit per week ##
        timeLimitWeek = self.getWeekLimitSecs()
        timeLimitMonth = self.getMonthLimitSecs()
        # enable apply
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMONApplyBT").set_sensitive(timeLimitWeek != self._timeLimitWeek or timeLimitMonth != self._timeLimitMonth)

        # ## add new day limits ##
        # check whether to enable add/remove intervals
        enabled = False
        for rCtrl in ["TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
            enabled = enabled or int(self._timekprAdminFormBuilder.get_object(rCtrl).get_text()) > 0
        # enable / disable
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDayApplyBT").set_sensitive(enabled)

        # ## add new hour intervals ##
        # check whether to enable add/remove intervals
        enabled = False
        for rCtrl in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB", "TimekprUserConfDaySettingsConfDaysIntervalsToHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"]:
            enabled = enabled or int(self._timekprAdminFormBuilder.get_object(rCtrl).get_text()) > 0
        # is enabled
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsAddBT").set_sensitive(enabled)

    def enableTimeControlToday(self, pEnable=True):
        """Enable buttons to add time today"""
        for rCtrl in ["TimekprUserConfTodaySettingsSetHrSB", "TimekprUserConfTodaySettingsSetMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(pEnable)

    # --------------- info population / set methods --------------- #

    def getUserList(self):
        """Get user list via dbus"""
        # store
        userStore = self._timekprAdminFormBuilder.get_object("TimekprUserSelectionLS")
        # clear up
        userStore.clear()
        userStore.append(["", ""])

        # get list
        result, message, userList = self._timekprAdminConnector.getUserList()

        # all ok
        if result == 0:
            # loop and print
            for rUser in userList:
                # add user
                userStore.append([rUser, rUser])

            # status
            self.setStatus(False, "User list retrieved")
            # enable
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").set_sensitive(True)
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionRefreshBT").set_sensitive(self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").get_sensitive())
            # init first selection
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").set_active(0)
        else:
            # status
            self.setStatus(False, message)

    def retrieveUserConfig(self, pUserName, pFull):
        """Get user configuration from server"""
        # clear before user
        if pFull:
            # reset form
            self.clearAdminForm()

        # if nothing is passed, nothing is done
        if pUserName != "":
            # init
            userConfig = {}

            # get list
            result, message, userConfig = self._timekprAdminConnector.getUserConfig(pUserName)

            # all ok
            if result == 0:
                # loop and print
                for rKey, rValue in userConfig.items():
                    # check all by keys
                    if rKey == "TIME_SPENT":
                        # spent
                        timeSpent = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentStr = str((timeSpent - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpent.hour).rjust(2, "0") + ":" + str(timeSpent.minute).rjust(2, "0") + ":" + str(timeSpent.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentTodayLB").set_text(timeSpentStr)
                    elif rKey == "TIME_SPENT_WEEK":
                        # spent week
                        timeSpentWeek = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentWeekStr = str((timeSpentWeek - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpentWeek.hour).rjust(2, "0") + ":" + str(timeSpentWeek.minute).rjust(2, "0") + ":" + str(timeSpentWeek.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentWeekLB").set_text(timeSpentWeekStr)
                    elif rKey == "TIME_SPENT_MONTH":
                        # spent month
                        timeSpentMonth = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentMonthStr = str((timeSpentMonth - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpentMonth.hour).rjust(2, "0") + ":" + str(timeSpentMonth.minute).rjust(2, "0") + ":" + str(timeSpentMonth.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentMonthLB").set_text(timeSpentMonthStr)

                    # the rest of info is needed when full refresh requested
                    if pFull:
                        if rKey == "TRACK_INACTIVE":
                            # track inactive
                            self._timeTrackInactive = bool(rValue)
                        elif rKey == "ALLOWED_WEEKDAYS":
                            # empty the values
                            self._timeLimitDays = []
                            # allowed weekdays
                            for rDay in rValue:
                                # set values
                                self._timeLimitDays.append(rDay)
                        elif rKey == "LIMITS_PER_WEEKDAYS":
                            # limits per allowed weekdays
                            self._timeLimitDaysLimits = []
                            # allowed weekdays
                            for rDay in range(0, len(rValue)):
                                # add the value
                                self._timeLimitDaysLimits.append(int(rValue[rDay]))
                        elif rKey == "LIMIT_PER_WEEK":
                            # value
                            self._timeLimitWeek = int(rValue)
                        elif rKey == "LIMIT_PER_MONTH":
                            # value
                            self._timeLimitMonth = int(rValue)
                        elif "ALLOWED_HOURS_" in rKey:
                            # determine the day
                            day = rKey[-1:]
                            self._timeLimitDaysHoursActual[day] = {}
                            # loop through available hours
                            for rHour, rHourMinutes in rValue.items():
                                # add config
                                self._timeLimitDaysHoursActual[day][str(rHour)] = {cons.TK_CTRL_SMIN: int(rHourMinutes[cons.TK_CTRL_SMIN]), cons.TK_CTRL_EMIN: int(rHourMinutes[cons.TK_CTRL_EMIN])}
                            # set up saved config as well
                            self._timeLimitDaysHoursSaved[day] = self._timeLimitDaysHoursActual[day].copy()

                # config was updated only when full
                if pFull:
                    # status
                    self.setStatus(False, "User config retrieved")
                    # apply config
                    self.applyUserConfig()
                    # determine control state
                    self.calculateControlAvailability()
                    # enable adding hours as well
                    self.enableTimeControlToday()
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

    def adjustTrackInactive(self):
        """Adjust track inactive sessions for user"""
        # get username
        userName = self.getSelectedUserName()

        # if we have username
        if userName is not None:
            # get time to add
            trackInactive = self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").get_active()

            # set time
            result, message = self._timekprAdminConnector.setTrackInactive(userName, trackInactive)

            # all ok
            if result == 0:
                # status
                self.setStatus(False, "Track inactive for user has been processed")

                # set values to internal config
                self._timeTrackInactive = trackInactive
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").emit("toggled")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

    def adjustTimeForToday(self, pOperation):
        """Process actual call to set time for user"""
        # get username
        userName = self.getSelectedUserName()

        # if we have username
        if userName is not None:
            # get time to add
            timeToAdjust = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").get_text()) * 3600
            timeToAdjust += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetMinSB").get_text()) * 60

            # set time
            result, message = self._timekprAdminConnector.setTimeLeft(userName, pOperation, timeToAdjust)

            # all ok
            if result == 0:
                # status
                self.setStatus(False, "Additional time for user has been processed")

                # set values to form
                for rCtrl in ["TimekprUserConfTodaySettingsSetHrSB", "TimekprUserConfTodaySettingsSetMinSB"]:
                    self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").emit("value-changed")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

    def adjustWKMONLimit(self):
        """Process actual call to set time for user"""
        # get username
        userName = self.getSelectedUserName()

        # if we have username
        if userName is not None:
            # weekly limit calc
            weeklyLimit = self.getWeekLimitSecs()
            # monthly limit calc
            monthlyLimit = self.getMonthLimitSecs()

            # set time
            result, message = self._timekprAdminConnector.setTimeLimitForWeek(userName, weeklyLimit)

            # all ok
            if result == 0:
                # set time
                result, message = self._timekprAdminConnector.setTimeLimitForMonth(userName, monthlyLimit)

            # if all ok
            if result == 0:
                # status
                self.setStatus(False, "Weekly and monthly limits for user have been processed")

                # set values to form
                self._timeLimitWeek = weeklyLimit
                self._timeLimitMonth = monthlyLimit
                for rCtrl in ["TimekprUserConfWKDaySB", "TimekprUserConfMONDaySB"]:
                    self._timekprAdminFormBuilder.get_object(rCtrl).emit("value-changed")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

    def applyDayAndHourIntervalChanges(self):
        """Apply all configuration changes to days and hours to server"""
        # initial flags about changes
        changedDayEnable = []
        enablementChanged = False
        changedDayLimits = []
        limitsChanged = False
        changedDayHours = []

        # ## check days enabled ##
        for rDay in range(0, 7):
            # get day number
            day = int(self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][0])
            enabled = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][2]
            limit = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][3]

            # add enabled days
            if enabled:
                # add days
                changedDayEnable.append(day)
                # add limits
                changedDayLimits.append(limit)

            # check wheter day enablement has changed
            if not (enabled == (day in self._timeLimitDays)):
                # changed
                enablementChanged = True
            # the day may just be added
            if rDay < len(self._timeLimitDaysLimits):
                # check whether day limits has changed
                if limit != self._timeLimitDaysLimits[rDay]:
                    # changed
                    limitsChanged = True
            else:
                # added
                limitsChanged = True

            # check for interval changes
            if self._timeLimitDaysHoursSaved[str(rDay + 1)] != self._timeLimitDaysHoursActual[str(rDay + 1)]:
                # changed
                changedDayHours.append(rDay)

        # get username
        userName = self.getSelectedUserName()

        # initial values
        result = 0
        message = ""

        # days were enabled / disabled
        if enablementChanged and result == 0:
            # set time
            result, message = self._timekprAdminConnector.setAllowedDays(userName, changedDayEnable)
            # if all ok
            if result == 0:
                # set to internal arrays as well
                self._timeLimitDays = changedDayEnable.copy()
                # status
                self.setStatus(False, "Allowed days for user have been processed")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

        # limits were changed
        if limitsChanged and result == 0:
            # set time
            result, message = self._timekprAdminConnector.setTimeLimitForDays(userName, changedDayLimits)
            # if all ok
            if result == 0:
                # set to internal arrays as well
                self._timeLimitDaysLimits = changedDayLimits.copy()
                # status
                self.setStatus(False, "Time limits for days for user have been processed")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

        # hour limits were changed
        if len(changedDayHours) > 0 and result == 0:
            # loop through changed day hours
            for rDayIdx in changedDayHours:
                # day
                day = str(rDayIdx + 1)
                print(day, self._timeLimitDaysHoursActual[day])
                # set time
                result, message = self._timekprAdminConnector.setAllowedHours(userName, day, self._timeLimitDaysHoursActual[day])
                # if all ok
                if result == 0:
                    # set to internal arrays as well
                    self._timeLimitDaysHoursSaved[day] = self._timeLimitDaysHoursActual[day].copy()
                    # status
                    self.setStatus(False, "Allowed hours for user have been processed")
                else:
                    # disable all but choser
                    self.toggleControls(False, True)
                    # status
                    self.setStatus(False, message)

        # recalc control availability
        self.calculateControlAvailability()

        # if OK
        if result == 0:
            # status
            self.setStatus(False, "Time limits for days for user have been processed")
        else:
            # status
            self.setStatus(False, message)

    # --------------- GTK signal methods --------------- #

    def userSelectionChanged(self, evt):
        """User selected"""
        # get username
        userName = self.getSelectedUserName()
        # only if connected
        if userName is not None and userName != "":
            # get user config
            self.retrieveUserConfig(userName, True if evt is not None else False)
        else:
            # disable all
            self.toggleControls(False, True)

        # return
        return True

    def userConfigurationRefreshActivated(self, evt):
        """User requested config restore from server"""
        self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").emit("changed")

    def dayAvailabilityChanged(self, widget, path):
        """Changed minutes depending on day availability"""
        # flip the checkbox
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2] = not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]
        # reset hours & minutes
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3] = 0

        # if day was disabled, reset hours and minutes
        if not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]:
            # reset hours & minutes
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] = _NO_TIME_LABEL

            # change interval selection as well
            #if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][0] in self._timeLimitDays:
            # clear day config
            for rHour in range(1, 23+1):
                self._timeLimitDaysHoursActual[self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][0]][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}
            # clear stuff and disable intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()
            # disable
            for rCtrl in ["TimekprHourIntervalsTreeView", "TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
                self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(False)
        else:
            # enable intervals
            for rCtrl in ["TimekprHourIntervalsTreeView", "TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
                self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(True)
            # enable interval refresh
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

        # recalc control availability
        self.calculateControlAvailability()

    def dayTotalLimitClicked(self, path):
        """Recalc total seconds"""
        # calculate todays limit
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # calculate time
        limitTime = cons.TK_DATETIME_START + timedelta(seconds=totalSecs)
        limit = "%s:%s:%s" % ("24" if totalSecs >= cons.TK_LIMIT_PER_DAY else str(limitTime.hour).rjust(2, "0"), str(limitTime.minute).rjust(2, "0"), str(limitTime.second).rjust(2, "0"))
        # get selected day
        dayIdx, dayNumber = self.getSelectedDay()
        # set the limit
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][3] = totalSecs
        # set appropriate label as well
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][4] = limit if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][2] else _NO_TIME_LABEL
        # reset time
        for rCtrl in ["TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")

        # inform intervals
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

        # recalc control availability
        self.calculateControlAvailability()

    def addHourIntervalClicked(self, evt):
        # seconds from
        secondsFrom = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        secondsFrom += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # seconds to
        secondsTo = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        secondsTo += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE

        # len
        intervalsLen = len(self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS"))

        # whether interval is valid
        intervalOverlaps = False
        intervalHourConflict = False
        # get liststore
        for rIdx in range(0, intervalsLen):
            # interval boundaries
            fromSecs = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[rIdx][4]
            toSecs = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[rIdx][5]
            # check whether start is betwen existing interval
            if fromSecs <= secondsFrom <= toSecs or fromSecs <= secondsTo <= toSecs:
                # this is it
                intervalOverlaps = True
                break
            # check whether user tries to insert iterval in existing hour
            elif int(fromSecs/cons.TK_LIMIT_PER_HOUR) <= int(secondsFrom/cons.TK_LIMIT_PER_HOUR) <= int(toSecs/cons.TK_LIMIT_PER_HOUR):
                # this is it
                intervalHourConflict = True
                break
            # check whether user tries to insert iterval in existing hour
            elif int(fromSecs/cons.TK_LIMIT_PER_HOUR) < int(secondsTo/cons.TK_LIMIT_PER_HOUR) < int(toSecs/cons.TK_LIMIT_PER_HOUR):
                # this is it
                intervalHourConflict = True
                break

        # set status message if fail
        if intervalOverlaps:
            self.setStatus(False, "Interval overlaps with existing one")
        elif intervalHourConflict:
            self.setStatus(False, "Interval conflicts with with existing one")
        elif secondsFrom == secondsTo:
            self.setStatus(False, "Interval start can not be the same as end")
        else:
            # get day to which add the interval
            day = self.getSelectedDay()[1]

            # now append the interval
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").append([intervalsLen + 1, self.formatInterval(secondsFrom), self.formatInterval(secondsTo), day, secondsFrom, secondsTo])

            # reset intervals (the last steps)
            for rCtrl in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB", "TimekprUserConfDaySettingsConfDaysIntervalsToHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"]:
                self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")

            # sort intervals
            self.sortHourIntervals()
            # status change
            self.setStatus(False, "Interval added")
            # adjust internal representation
            self.rebuildHoursFromIntervals()
            # recalc control availability
            self.calculateControlAvailability()

    def removeHourIntervalClicked(self, evt):
        """Handle remove hour interval"""
        hourIdx = self.getSelectedHourInterval()[0]
        rIdx = 0

        # remove selected item
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS"):
            # check what to remove
            if hourIdx == rIdx:
                # remove
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").remove(rIt.iter)
                # this is it
                break

            # count further
            rIdx += 1

        # sort intervals
        self.sortHourIntervals()
        # status change
        self.setStatus(False, "Interval removed")
        # adjust internal representation
        self.rebuildHoursFromIntervals()
        # recalc control availability
        self.calculateControlAvailability()

    def rebuildHoursFromIntervals(self):
        """Rebuild hours from intervals in GUI, representation to user is different than actual config"""
        # get day
        day = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[0][3] if len(self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")) > 0 else None
        # day is here
        if day is not None:
            # clear internal hour representation
            self._timeLimitDaysHoursActual[day] = {}

            # remove selected item
            for rIt in self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS"):
                # start time
                time = cons.TK_DATETIME_START + timedelta(seconds=rIt[4])
                # total seconds
                totalSeconds = rIt[5] - rIt[4]

                # now loop through time in interval
                while totalSeconds > 0:
                    # hour
                    hour = str(time.hour)
                    # build up hour
                    self._timeLimitDaysHoursActual[day][hour] = {cons.TK_CTRL_SMIN: time.minute, cons.TK_CTRL_EMIN: None}
                    # add to time
                    time += timedelta(seconds=min(cons.TK_LIMIT_PER_HOUR, totalSeconds))
                    # add end hour
                    self._timeLimitDaysHoursActual[day][hour][cons.TK_CTRL_EMIN] = 60 if totalSeconds >= cons.TK_LIMIT_PER_HOUR else time.minute
                    # subtract hour
                    totalSeconds -= min(cons.TK_LIMIT_PER_HOUR, totalSeconds)

                    #print(hour, self._timeLimitDaysHoursActual[day][hour][cons.TK_CTRL_SMIN], self._timeLimitDaysHoursActual[day][hour][cons.TK_CTRL_EMIN])

    def weekAvailabilityChanged(self, evt):
        """Change in minutes depending on week availability"""
        # whether there should be a week limit
        enabled = self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").get_active()
        for rCtrl in ["TimekprUserConfWKDaySB", "TimekprUserConfWKHrSB", "TimekprUserConfWKMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(enabled)

    def monthAvailabilityChanged(self, evt):
        """Change in minutes depending on week availability"""
        # whether there should be a month limit
        enabled = self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").get_active()
        for rCtrl in ["TimekprUserConfMONDaySB", "TimekprUserConfMONHrSB", "TimekprUserConfMONMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(enabled)

    def weeklyLimitDayHrMinChanged(self, evt, pCheckEnabled=True):
        # check whether user has not went too far
        totalSecs = self.getWeekLimitSecs()

        # if it's not enabled, set max values
        if totalSecs > cons.TK_LIMIT_PER_WEEK:
            # max values
            self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").set_text("7")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfWKHrSB").set_text("0")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMinSB").set_text("0")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_active(False)

        # enable / disable checkbox
        if totalSecs != cons.TK_LIMIT_PER_WEEK:
            self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_active(totalSecs != cons.TK_LIMIT_PER_WEEK)

        # recalc control availability
        self.calculateControlAvailability()

    def monthlyLimitDayHrMinChanged(self, evt, pCheckEnabled=True):
        # check whether user has not went too far
        totalSecs = self.getMonthLimitSecs()

        # if it's not enabled, set max values
        if totalSecs > cons.TK_LIMIT_PER_MONTH:
            # max values
            self._timekprAdminFormBuilder.get_object("TimekprUserConfMONDaySB").set_text("31")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfMONHrSB").set_text("0")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfMONMinSB").set_text("0")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_active(False)

        # enable / disable checkbox
        if totalSecs != cons.TK_LIMIT_PER_MONTH:
            self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_active(totalSecs != cons.TK_LIMIT_PER_MONTH)

        # recalc control availability
        self.calculateControlAvailability()

    def dailyLimitDayHrMinChanged(self, evt, pCheckEnabled=True):
        # check whether user has not went too far
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE

        # if it's not enabled, set max values
        if totalSecs > cons.TK_LIMIT_PER_DAY:
            # max values
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetHrSB").set_text("24")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetMinSB").set_text("0")

        # set or not
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDayApplyBT").set_sensitive(totalSecs > 0)

        # recalc control availability
        self.calculateControlAvailability()

    def dailyLimitDayHrIntervalsChanged(self, evt, pCheckEnabled=True):
        # check whether user has not went too far
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE

        # if it's not enabled, set max values
        if totalSecs > cons.TK_LIMIT_PER_DAY:
            # max values
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB").set_text("24")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB").set_text("0")

        # check whether user has not went too far
        totalSecsAlt = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecsAlt += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE

        # if it's not enabled, set max values
        if totalSecsAlt > cons.TK_LIMIT_PER_DAY:
            # max values
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToHrSB").set_text("24")
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToMinSB").set_text("0")

        # set or not
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsAddBT").set_sensitive(totalSecs > 0 or totalSecsAlt > 0)

        # from - to must be in correlation
        if totalSecsAlt < totalSecs:
            # adjust from the same as to
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToHrSB").set_text(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB").get_text())
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsToMinSB").set_text(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB").get_text())

        # recalc control availability
        self.calculateControlAvailability()

    def trackInactiveChanged(self, evt):
        # recalc control availability
        self.calculateControlAvailability()

    def todayAddTimeChanged(self, evt):
        # recalc control availability
        self.calculateControlAvailability()

    def dailyLimitsDaySelectionChanged(self, evt):
        # refresh the child
        dayIdx, dayNum = self.getSelectedDay()

        # only if there is smth selected
        if dayNum is not None:
            # whether day is enabled
            enabled = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][2]
            limit = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][3]

            # clear out existing intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()

            # reset intervals
            for rSB in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB", "TimekprUserConfDaySettingsConfDaysIntervalsToHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"]:
                self._timekprAdminFormBuilder.get_object(rSB).set_text("0")

            # enable & disable controls
            for rSB in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB"
                ,"TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB"
                ,"TimekprUserConfDaySettingsConfDaysIntervalsToHrSB"
                ,"TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"
                ,"TimekprHourIntervalsTreeView"
            ]:
                # whether we can change hours
                self._timekprAdminFormBuilder.get_object(rSB).set_sensitive(enabled and limit > 0)

            # enable & disable controls
            for rSB in ["TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
                # whether we can change hours
                self._timekprAdminFormBuilder.get_object(rSB).set_sensitive(enabled)

            # fill intervals only if that day exists
            if dayNum in self._timeLimitDaysHoursActual and enabled and limit > 0:
                # idx
                idx = 0
                # fill the intervals
                for rInterval in self.getIntervalList(dayNum):
                    # fill in the intervals
                    self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").append([idx, rInterval[0], rInterval[1], dayNum, rInterval[2], rInterval[3]])
                    idx += 1

    def todayAddTimeClicked(self, evt):
        """Add time to user"""
        self.adjustTimeForToday("+")

    def todaySubtractTimeClicked(self, evt):
        """Subtract time from user"""
        self.adjustTimeForToday("-")

    def todaySetTimeClicked(self, evt):
        """Set exact time for user"""
        self.adjustTimeForToday("=")

    def trackInactiveClicked(self, evt):
        """Set track inactive"""
        self.adjustTrackInactive()

    def WKMONLimitSetClicked(self, evt):
        """Adjust weekly and monthly limits"""
        self.adjustWKMONLimit()

    def hourIntervalSelectionChanged(self, evt):
        """When hour interval selection changed"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # clear out existing intervals
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsSubtractBT").set_sensitive(True)
        else:
            # clear out existing intervals
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsSubtractBT").set_sensitive(False)

    def weeklyLimitDayHrMinChanged(self, evt):
        # recalc control availability
        self.calculateControlAvailability()

    def applyDaysHourIntervalsClicked(self, evt):
        """Call set methods for changes"""
        self.applyDayAndHourIntervalChanges()

    def closePropertiesSignal(self, evt, smth):
        """Close the config form"""
        # close
        self._mainLoop.quit()
