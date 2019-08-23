"""
Created on Aug 28, 2018

@author: mjasnik
"""

import gi
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from datetime import timedelta, datetime

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.client.interface.dbus.administration import timekprAdminConnector
from timekpr.common.constants import messages as msg

# constant
_NO_TIME_LABEL = "--:--:--"
_NO_TIME_LABEL_SHORT = "--:--"
_NO_TIME_LIMIT_LABEL = "--:--:--:--"


class timekprAdminGUI(object):
    """Main class for supporting timekpr forms"""

    def __init__(self, pTimekprVersion, pResourcePath, pUsername, pIsDevActive):
        """Initialize gui"""
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
        # disable all user config buttons firstly
        self.toggleUserConfigControls(False)
        # disable all timekpr config buttons firstly
        self.toggleTimekprConfigControls(False)
        # status
        self.setTimekprStatus(True, msg.getTranslation("TK_MSG_STATUS_STARTED"))

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

    # --------------- initialization / helper methods --------------- #

    def dummyPageChanger(self):
        """Switch tabs back and forth"""
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
            self.setTimekprStatus(True, msg.getTranslation("TK_MSG_STATUS_CONNECTED"))
            # in case we are connected, do not retrieve config again
            if not self._isConnected:
                # connected
                self._isConnected = True
                # get users
                GLib.timeout_add_seconds(0, self.getUserList)
                GLib.timeout_add_seconds(0.1, self.retrieveTimekprConfig)
        elif not interfacesOk and connecting:
            # status
            self.setTimekprStatus(True, msg.getTranslation("TK_MSG_STATUS_CONNECTING"))
            # invoke again
            GLib.timeout_add_seconds(1, self.checkConnection)
            # not connected
            self._isConnected = False
        else:
            # status
            self.setTimekprStatus(True, msg.getTranslation("TK_MSG_STATUS_CONNECTION_FAILED"))
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_CONNECTION_ACCESS_DENIED"))
            # not connected
            self._isConnected = False

    def initGUIElements(self):
        """Initialize all GUI elements for stores"""
        # ## days ##
        # day name
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_DAY_LIST_DAY_LABEL"), Gtk.CellRendererText(), text=1)
        col.set_min_width(90)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)
        # day enabled
        rend = Gtk.CellRendererToggle()
        rend.connect("toggled", self.dayAvailabilityChanged)
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_DAY_LIST_ENABLED_LABEL"), rend, active=2)
        col.set_min_width(35)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)
        # limit
        rend = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_DAY_LIST_LIMIT_LABEL"), rend, text=4)
        col.set_min_width(60)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)
        # final col
        col = Gtk.TreeViewColumn("", Gtk.CellRendererText())
        col.set_min_width(10)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # ## intervals ##
        # from hour
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_DAY_INTERVALS_FROM_LABEL"), Gtk.CellRendererText(), text=1)
        col.set_min_width(40)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)
        # to hour
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_DAY_INTERVALS_TO_LABEL"), Gtk.CellRendererText(), text=2)
        col.set_min_width(40)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)
        # final col
        col = Gtk.TreeViewColumn("", Gtk.CellRendererText())
        col.set_min_width(10)
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").append_column(col)
        # clear out existing intervals
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS").clear()
        # lets prepare week days
        for rDay in range(1, 7+1):
            # fill in the intervals
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS").append([str(rDay), (cons.TK_DATETIME_START + timedelta(days=rDay-1)).strftime("%A"), False, 0, _NO_TIME_LABEL])

        # ## tracked session types ##
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_TRACKED_SESSIONS_LABEL"), Gtk.CellRendererText(), text=0)
        col.set_min_width(90)
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsTreeView").append_column(col)
        # clear
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS").clear()

        # ## excluded session types ##
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_UNTRACKED_SESSIONS_LABEL"), Gtk.CellRendererText(), text=0)
        col.set_min_width(90)
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsTreeView").append_column(col)
        # clear
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS").clear()

        # ## excluded users ##
        col = Gtk.TreeViewColumn(msg.getTranslation("TK_MSG_EXCLUDED_USERS_LABEL"), Gtk.CellRendererText(), text=0)
        col.set_min_width(90)
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersTreeView").append_column(col)
        # clear
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS").clear()

    def initInternalConfiguration(self):
        """Initialize the internal configuration for admin form"""
        self._userConfigControlElements = [
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
            ,"TimekprUserConfDaySettingsConfDaySetHrSB"
            ,"TimekprUserConfDaySettingsConfDaySetMinSB"
            # lists
            ,"TimekprWeekDaysTreeView"
            ,"TimekprHourIntervalsTreeView"
        ]

        self._timekprConfigControlElements = [
            # control buttons
            "TimekprTrackingSessionsAddBT"
            ,"TimekprTrackingSessionsRemoveBT"
            ,"TimekprExcludedSessionsAddBT"
            ,"TimekprExcludedSessionsRemoveBT"
            ,"TimekprExcludedUsersAddBT"
            ,"TimekprExcludedUsersRemoveBT"
            ,"TimekprConfigurationApplyBT"
            # spin buttons for adjustments
            ,"TimekprConfigurationLoglevelSB"
            ,"TimekprConfigurationWarningTimeSB"
            ,"TimekprConfigurationPollIntervalSB"
            ,"TimekprConfigurationSaveTimeSB"
            ,"TimekprConfigurationTerminationTimeSB"
            # entry fields
            ,"TimekprTrackingSessionsEntryEF"
            ,"TimekprExcludedSessionsEntryEF"
            ,"TimekprExcludedUsersEntryEF"
            # lists
            ,"TimekprTrackingSessionsTreeView"
            ,"TimekprExcludedSessionsTreeView"
            ,"TimekprExcludedUsersTreeView"
        ]

        # sets up limit variables for user configuration
        self._timeTrackInactive = False
        self._timeLimitWeek = 0
        self._timeLimitMonth = 0
        self._timeLimitDays = []
        self._timeLimitDaysLimits = []
        self._timeLimitDaysHoursActual = {}
        for rDay in range(1, 7+1):
            self._timeLimitDaysHoursActual[str(rDay)] = {}
            for rHour in range(0, 23+1):
                self._timeLimitDaysHoursActual[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}
        # saved means from server, actual means modified in form
        self._timeLimitDaysHoursSaved = self._timeLimitDaysHoursActual.copy()

        # sets up limit variables for timekpr configuration
        self._timekprWarningTime = 0
        self._timekprPollingInterval = 0
        self._timekprSaveTime = 0
        self._timekprTerminationTime = 0
        self._timekprLogLevel = 0
        self._timekprTrackingSessions = []
        self._timekprExcludedSessions = []
        self._timekprExcludedUsers = []

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

    def toggleUserConfigControls(self, pEnable=True, pLeaveUserList=False):
        """Enable or disable all user controls for the form"""
        # apply settings to all buttons`in user configuration
        for rButton in self._userConfigControlElements:
            # if we need to leave user selection intact
            if not (pLeaveUserList and rButton == "TimekprUserSelectionCB"):
                # get the button and set availability
                self._timekprAdminFormBuilder.get_object(rButton).set_sensitive(pEnable)
        # if disable
        if not pEnable:
            self.clearAdminForm()

    def toggleTimekprConfigControls(self, pEnable=True, pAll=True):
        """Enable or disable all timekpr controls for the form"""
        # enable for timekpr can be done only in admin mode
        enable = pEnable and (os.getuid() == 0 or self._isDevActive)
        # apply settings to all buttons`in user configuration
        for rButton in self._timekprConfigControlElements:
            if not enable:
                # get the button and set availability
                self._timekprAdminFormBuilder.get_object(rButton).set_sensitive(enable)
            else:
                # when enable, then check whether we need to enable all or just main controls
                if (("Add" in rButton or "Remove" in rButton) and not pAll):
                    # get the button and set availability
                    self._timekprAdminFormBuilder.get_object(rButton).set_sensitive(not enable)
                else:
                    # get the button and set availability
                    self._timekprAdminFormBuilder.get_object(rButton).set_sensitive(enable)

    def setTimekprStatus(self, pConnectionStatus, pStatus):
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
            statusBar.push(contextId, pStatus[:80])

    def clearAdminForm(self):
        """Clear and default everything to default values"""
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
            for rHour in range(0, 23+1):
                self._timeLimitDaysHoursActual[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

        # clear up the intervals
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()

        # this clears hours for week and month
        for rCtrl in ["TimekprUserConfWKDaySB", "TimekprUserConfWKHrSB", "TimekprUserConfWKHrSB", "TimekprUserConfMONDaySB", "TimekprUserConfMONDaySB", "TimekprUserConfMONHrSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")

    def formatIntervalStr(self, pTotalSeconds, pFormatSecs=False):
        """Format the time intervals as string label"""
        # get time out of seconds
        time = cons.TK_DATETIME_START + timedelta(seconds=pTotalSeconds)
        # limit
        limit = str(24 if pTotalSeconds >= cons.TK_LIMIT_PER_DAY else time.hour).rjust(2, "0")
        limit += ":" + str(0 if pTotalSeconds >= cons.TK_LIMIT_PER_DAY else time.minute).rjust(2, "0")
        limit += (":" + str(0 if pTotalSeconds >= cons.TK_LIMIT_PER_DAY else time.second).rjust(2, "0")) if pFormatSecs else ""
        # value
        return limit

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
                    startTimeStr = self.formatIntervalStr(startSeconds)

                # define end hour
                endDate = cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timeLimitDaysHoursActual[str(pDay)][str(rHour)][cons.TK_CTRL_EMIN])
                endSeconds = (endDate - cons.TK_DATETIME_START).total_seconds()
                endTimeStr = self.formatIntervalStr(endSeconds)

                # define intervals
                if self._timeLimitDaysHoursActual[pDay][str(rHour)][cons.TK_CTRL_EMIN] != 60 or rHour == 23:
                    timeLimits.append([startTimeStr, endTimeStr, startSeconds, endSeconds])
                    startTimeStr = None
                    endTimeStr = None

        # return
        return timeLimits

    def getWeekLimitSecs(self):
        """Get week limit in seconds"""
        # count secs
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").get_text()) * cons.TK_LIMIT_PER_DAY
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # return
        return totalSecs

    def getMonthLimitSecs(self):
        """Get month limit in seconds"""
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

    def getSelectedConfigElement(self, pElementName):
        """Get selected config element"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object(pElementName).get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # idx
            elemIdx = tm.get_path(ti)[0]
        else:
            # nothing
            elemIdx = None

        # return
        return elemIdx

    def sortHourIntervals(self):
        """Sort hour intervals for ease of use"""
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
        """Apply user configuration after getting it from server"""
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
        dayLimitIdx = -1
        # loop through all days
        for rDay in range(1, 7+1):
            # day index
            dayIdx = rDay - 1
            # check whether this day is enabled
            if rDay in self._timeLimitDays:
                # advance index
                dayLimitIdx += 1
            else:
                continue

            # calculate time
            limit = self.formatIntervalStr(self._timeLimitDaysLimits[dayLimitIdx], True)

            # enable certain days
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][3] = self._timeLimitDaysLimits[dayLimitIdx]
            # set appropriate label as well
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[dayIdx][4] = limit if rDay in self._timeLimitDays else _NO_TIME_LABEL

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

        # current day
        currDay = datetime.now().isoweekday()-1
        # determine curent day and point to it
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").set_cursor(currDay)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").scroll_to_cell(currDay)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

    def applyTimekprConfig(self):
        """Apply user configuration after getting it from server"""
        # ## log level ##
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationLoglevelSB").set_text(str(self._timekprLogLevel))
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationLoglevelSB").set_sensitive(True)

        # ## poll time ##
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationPollIntervalSB").set_text(str(self._timekprPollingInterval))
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationPollIntervalSB").set_sensitive(True)

        # ## save time ##
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationSaveTimeSB").set_text(str(self._timekprSaveTime))
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationSaveTimeSB").set_sensitive(True)

        # ## termination time ##
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationTerminationTimeSB").set_text(str(self._timekprTerminationTime))
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationTerminationTimeSB").set_sensitive(True)

        # ## final warning time ##
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationWarningTimeSB").set_text(str(self._timekprWarningTime))
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationWarningTimeSB").set_sensitive(True)

        # ## tracking session types ###
        for rSessionType in self._timekprTrackingSessions:
            # add config
            self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS").append([str(rSessionType)])
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsTreeView").set_sensitive(True)

        # ## exclusion session types ##
        for rSessionType in self._timekprExcludedSessions:
            # add config
            self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS").append([str(rSessionType)])
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsTreeView").set_sensitive(True)

        # ## excluded users ##
        for rUser in self._timekprExcludedUsers:
            # add config
            self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS").append([str(rUser)])
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersTreeView").set_sensitive(True)

        # enable / disable controls
        self.toggleTimekprConfigControls(True, False)

    def calculateUserConfigControlAvailability(self):
        """Calculate user config control availability"""
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
        for rDay in range(0, 7):
            # check whether day and config is different
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][2]:
                enabledDays += 1
        # days are the same, no need to enable button
        enabled = (len(self._timeLimitDays) != enabledDays)

        # ## limits per allowed days ###
        dayIdx = -1
        limitLen = len(self._timeLimitDaysLimits)
        # go through all days
        for rDay in range(0, 7):
            # day found
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][2]:
                dayIdx += 1
            else:
                continue

            # check if different
            if dayIdx >= limitLen or self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][3] != self._timeLimitDaysLimits[dayIdx]:
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

    def calculateTimekprConfigControlAvailability(self, pApplyControls=True):
        """Calculate main control availability"""
        # this duplicates diff control as well
        changeControl = {}
        # ## log level ##
        control = "TimekprConfigurationLoglevelSB"
        value = int(self._timekprAdminFormBuilder.get_object(control).get_text())
        changeControl[control] = {"st": value != self._timekprLogLevel, "val": value}

        # ## poll time ##
        control = "TimekprConfigurationPollIntervalSB"
        value = int(self._timekprAdminFormBuilder.get_object(control).get_text())
        changeControl[control] = {"st": value != self._timekprPollingInterval, "val": value}

        # ## save time ##
        control = "TimekprConfigurationSaveTimeSB"
        value = int(self._timekprAdminFormBuilder.get_object(control).get_text())
        changeControl[control] = {"st": value != self._timekprSaveTime, "val": value}

        # ## termination time ##
        control = "TimekprConfigurationTerminationTimeSB"
        value = int(self._timekprAdminFormBuilder.get_object(control).get_text())
        changeControl[control] = {"st": value != self._timekprTerminationTime, "val": value}

        # ## final warning time ##
        control = "TimekprConfigurationWarningTimeSB"
        value = int(self._timekprAdminFormBuilder.get_object(control).get_text())
        changeControl[control] = {"st": value != self._timekprWarningTime, "val": value}

        # ## tracking session types ###
        tmpArray = []
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS"):
            tmpArray.append(str(rIt[0]))
        control = "TimekprTrackingSessionsLS"
        changeControl[control] = {"st": tmpArray != self._timekprTrackingSessions, "val": tmpArray}

        # ## exclusion session types ##
        tmpArray = []
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS"):
            tmpArray.append(str(rIt[0]))
        control = "TimekprExcludedSessionsLS"
        changeControl[control] = {"st": tmpArray != self._timekprExcludedSessions, "val": tmpArray}

        # ## excluded users ##
        tmpArray = []
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS"):
            tmpArray.append(str(rIt[0]))
        control = "TimekprExcludedUsersLS"
        changeControl[control] = {"st": tmpArray != self._timekprExcludedUsers, "val": tmpArray}

        # if at least one is changed
        enable = False
        if pApplyControls:
            for rKey, rVal in changeControl.items():
                # one thing changed
                if rVal["st"]:
                    # no need to search further
                    enable = rVal["st"]
                    break
            # enabled or not
            self._timekprAdminFormBuilder.get_object("TimekprConfigurationApplyBT").set_sensitive(enable)

        # return
        return changeControl

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
            self.setTimekprStatus(False, "User list retrieved")
            # enable
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").set_sensitive(True)
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionRefreshBT").set_sensitive(self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").get_sensitive())
            # init first selection
            self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").set_active(0)
        else:
            # status
            self.setTimekprStatus(False, message)
            # check the connection
            self.checkConnection()

    def retrieveUserConfig(self, pUserName, pFull):
        """Retrieve user configuration"""
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
                        timeSpent = cons.TK_DATETIME_START + timedelta(seconds=abs(rValue))
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
                                self._timeLimitDays.append(int(rDay))
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
                    self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_USER_CONFIG_RETRIEVED"))
                    # apply config
                    self.applyUserConfig()
                    # determine control state
                    self.calculateUserConfigControlAvailability()
                    # enable adding hours as well
                    self.enableTimeControlToday()
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)
                # check the connection
                self.checkConnection()

    def retrieveTimekprConfig(self):
        """Retrieve timekpr configuration"""
        # init
        timekprConfig = {}
        result = 0
        message = ""

        # get list
        result, message, timekprConfig = self._timekprAdminConnector.getTimekprConfiguration()

        # all ok
        if result == 0:
            # loop and print
            for rKey, rValue in timekprConfig.items():
                # check all by keys
                if rKey == "TIMEKPR_LOGLEVEL":
                    # log level
                    self._timekprLogLevel = int(rValue)
                elif rKey == "TIMEKPR_POLLTIME":
                    # poll time
                    self._timekprPollingInterval = int(rValue)
                elif rKey == "TIMEKPR_SAVE_TIME":
                    # save time
                    self._timekprSaveTime = int(rValue)
                elif rKey == "TIMEKPR_TERMINATION_TIME":
                    # termination time
                    self._timekprTerminationTime = int(rValue)
                elif rKey == "TIMEKPR_FINAL_WARNING_TIME":
                    # final warning time
                    self._timekprWarningTime = int(rValue)
                elif rKey == "TIMEKPR_SESSION_TYPES_CTRL":
                    # init
                    self._timekprTrackingSessions = []
                    # loop through available session types
                    for rSessionType in rValue:
                        # add config
                        self._timekprTrackingSessions.append(str(rSessionType))
                elif rKey == "TIMEKPR_SESSION_TYPES_EXCL":
                    # init
                    self._timekprExcludedSessions = []
                    # loop through available session types
                    for rSessionType in rValue:
                        # add config
                        self._timekprExcludedSessions.append(str(rSessionType))
                elif rKey == "TIMEKPR_USERS_EXCL":
                    # init
                    self._timekprExcludedUsers = []
                    # loop through available users
                    for rUser in rValue:
                        # add config
                        self._timekprExcludedUsers.append(str(rUser))

            # apply config
            self.applyTimekprConfig()
            # determine control state
            self.calculateTimekprConfigControlAvailability()
            # status
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_CONFIG_RETRIEVED"))
        else:
            # disable all but choser
            self.toggleUserConfigControls(False, True)
            # status
            self.setTimekprStatus(False, message)
            # check the connection
            self.checkConnection()

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
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_TRACKINACTIVE_PROCESSED"))

                # set values to internal config
                self._timeTrackInactive = trackInactive
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").emit("toggled")
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)
                # check the connection
                self.checkConnection()

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
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_ADJUSTTIME_PROCESSED"))

                # set values to form
                for rCtrl in ["TimekprUserConfTodaySettingsSetHrSB", "TimekprUserConfTodaySettingsSetMinSB"]:
                    self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").emit("value-changed")
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)
                # check the connection
                self.checkConnection()

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
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_WKMONADJUSTTIME_PROCESSED"))

                # set values to form
                self._timeLimitWeek = weeklyLimit
                self._timeLimitMonth = monthlyLimit
                for rCtrl in ["TimekprUserConfWKDaySB", "TimekprUserConfMONDaySB"]:
                    self._timekprAdminFormBuilder.get_object(rCtrl).emit("value-changed")
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)
                # check the connection
                self.checkConnection()

    def applyDayAndHourIntervalChanges(self):
        """Apply configuration changes to days and hours to server"""
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
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_ALLOWEDDAYS_PROCESSED"))
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)

        # limits were changed
        if limitsChanged and result == 0:
            # set time
            result, message = self._timekprAdminConnector.setTimeLimitForDays(userName, changedDayLimits)
            # if all ok
            if result == 0:
                # set to internal arrays as well
                self._timeLimitDaysLimits = changedDayLimits.copy()
                # status
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_TIMELIMITS_PROCESSED"))
            else:
                # disable all but choser
                self.toggleUserConfigControls(False, True)
                # status
                self.setTimekprStatus(False, message)

        # hour limits were changed
        if len(changedDayHours) > 0 and result == 0:
            # loop through changed day hours
            for rDayIdx in changedDayHours:
                # day
                day = str(rDayIdx + 1)

                # set time
                result, message = self._timekprAdminConnector.setAllowedHours(userName, day, self._timeLimitDaysHoursActual[day])
                # if all ok
                if result == 0:
                    # set to internal arrays as well
                    self._timeLimitDaysHoursSaved[day] = self._timeLimitDaysHoursActual[day].copy()
                    # status
                    self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_ALLOWEDHOURS_PROCESSED"))
                else:
                    # disable all but choser
                    self.toggleUserConfigControls(False, True)
                    # status
                    self.setTimekprStatus(False, message)

        # recalc control availability
        self.calculateUserConfigControlAvailability()

        # if OK
        if result == 0:
            # status
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_ALLTIMELIMITS_PROCESSED"))
        else:
            # status
            self.setTimekprStatus(False, message)
            # check the connection
            self.checkConnection()

    def applyTimekprConfigurationChanges(self, evt):
        """Apply configuration changes to server"""
        # get what's changed
        changeControl = self.calculateTimekprConfigControlAvailability(False)

        # initial values
        result = 0
        message = ""

        # loop through all changes
        for rKey, rVal in changeControl.items():
            # changed
            if rVal["st"]:
                # check what element we have, depending on that call different interface
                # ## poll time ##
                if rKey == "TimekprConfigurationLoglevelSB":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprLogLevel(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprLogLevel = rVal["val"]
                # ## poll time ##
                elif rKey == "TimekprConfigurationPollIntervalSB":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprPollTime(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprPollingInterval = rVal["val"]
                # ## save time ##
                elif rKey == "TimekprConfigurationSaveTimeSB":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprSaveTime(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprSaveTime = rVal["val"]
                # ## termination time ##
                elif rKey == "TimekprConfigurationTerminationTimeSB":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprTerminationTime(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprTerminationTime = rVal["val"]
                # ## final warning time ##
                elif rKey == "TimekprConfigurationWarningTimeSB":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprFinalWarningTime(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprWarningTime = rVal["val"]
                # ## tracking session types ###
                elif rKey == "TimekprTrackingSessionsLS":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprSessionsCtrl(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprTrackingSessions = rVal["val"].copy()
                # ## exclusion session types ##
                elif rKey == "TimekprExcludedSessionsLS":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprSessionsExcl(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprExcludedSessions = rVal["val"].copy()
                # ## excluded users ##
                elif rKey == "TimekprExcludedUsersLS":
                    # call server
                    result, message = self._timekprAdminConnector.setTimekprUsersExcl(rVal["val"])
                    # set internal state
                    if result == 0:
                        self._timekprExcludedUsers = rVal["val"].copy()

                # if all ok
                if result != 0:
                    # status
                    self.setTimekprStatus(False, message)
                    # that's it
                    break

        # fine
        if result == 0:
            # status
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_CONFIGURATION_SAVED"))
        else:
            # check the connection
            self.checkConnection()

        # recalc the control state
        self.calculateTimekprConfigControlAvailability()

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
            self.toggleUserConfigControls(False, True)

        # return
        return True

    def userConfigurationRefreshActivated(self, evt):
        """User requested config restore from server"""
        self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").emit("changed")

    def dayAvailabilityChanged(self, widget, path):
        """Change minutes depending on day availability"""
        # flip the checkbox
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2] = not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]
        # reset hours & minutes
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3] = 0

        # if day was disabled, reset hours and minutes
        if not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]:
            # enabled
            enabled = False
            # reset hours & minutes
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] = _NO_TIME_LABEL
            # change interval selection as well
            for rHour in range(0, 23+1):
                self._timeLimitDaysHoursActual[self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][0]][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

            # clear stuff and disable intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()
        else:
            # enabled
            enabled = True
            # label
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] = self.formatIntervalStr(self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3], True)
            # enable interval refresh
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

        # enable/disable intervals
        for rCtrl in ["TimekprUserConfDaySettingsConfDaySetHrSB", "TimekprUserConfDaySettingsConfDaySetMinSB"]:
            self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(enabled)
        # disable only
        if not enabled:
            for rCtrl in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB", "TimekprUserConfDaySettingsConfDaysIntervalsToHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"]:
                self._timekprAdminFormBuilder.get_object(rCtrl).set_sensitive(enabled)

        # recalc control availability
        self.calculateUserConfigControlAvailability()

    def dayTotalLimitClicked(self, path):
        """Recalc total seconds"""
        # calculate todays limit
        totalSecs = int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetHrSB").get_text()) * cons.TK_LIMIT_PER_HOUR
        totalSecs += int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaySetMinSB").get_text()) * cons.TK_LIMIT_PER_MINUTE
        # calculate time
        limit = self.formatIntervalStr(totalSecs, True)

        # get selected day
        dayIdx, dayNumber = self.getSelectedDay()

        # if it's not selected
        if dayIdx is None:
            # status
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_NODAY_SELECTED"))
        else:
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
        self.calculateUserConfigControlAvailability()

    def addHourIntervalClicked(self, evt):
        """Process addition of hour interval"""
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
        intervalHourConflictStart = False
        intervalHourConflictEnd = False
        intervalDuplicate = False
        # get liststore
        for rIdx in range(0, intervalsLen):
            # interval boundaries
            fromSecs = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[rIdx][4]
            toSecs = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[rIdx][5]

            # check whether start is betwen existing interval
            if secondsFrom < fromSecs < secondsTo or secondsFrom < toSecs < secondsTo:
                # this is it
                intervalOverlaps = True
                break
            # check whether start is betwen existing interval
            elif fromSecs < secondsFrom < toSecs or fromSecs < secondsTo < toSecs:
                # this is it
                intervalOverlaps = True
                break
            # check whether user tries to insert iterval in existing hour
            elif int(fromSecs/cons.TK_LIMIT_PER_HOUR) <= int(secondsFrom/cons.TK_LIMIT_PER_HOUR) <= int(toSecs/cons.TK_LIMIT_PER_HOUR) and int(toSecs/cons.TK_LIMIT_PER_HOUR) * cons.TK_LIMIT_PER_HOUR not in (toSecs, secondsFrom):
                # this is it
                intervalHourConflictStart = True
                break
            # check whether user tries to insert iterval in existing hour (end of previous and start of next can be equal)
            elif int(fromSecs/cons.TK_LIMIT_PER_HOUR) <= int(secondsTo/cons.TK_LIMIT_PER_HOUR) <= int(toSecs/cons.TK_LIMIT_PER_HOUR) and int(fromSecs/cons.TK_LIMIT_PER_HOUR) * cons.TK_LIMIT_PER_HOUR not in (fromSecs, secondsTo):
                # this is it
                intervalHourConflictEnd = True
                break
            # check whether user tries to insert duplicate iterval
            elif fromSecs == secondsFrom or toSecs == secondsTo:
                # this is it
                intervalDuplicate = True
                break

        # set status message if fail
        if intervalOverlaps:
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVAL_OVERLAP_DETECTED"))
        elif intervalHourConflictStart:
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVALSTART_CONFLICT_DETECTED"))
        elif intervalHourConflictEnd:
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVALEND_CONFLICT_DETECTED"))
        elif intervalDuplicate:
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVAL_DUPLICATE_DETECTED"))
        elif secondsFrom == secondsTo:
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVAL_STARTENDEQUAL_DETECTED"))
        else:
            # get day to which add the interval
            day = self.getSelectedDay()[1]

            # if it's not selected
            if day is None:
                # status
                self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_NODAY_SELECTED"))
            else:
                # now append the interval
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").append([intervalsLen + 1, self.formatIntervalStr(secondsFrom), self.formatIntervalStr(secondsTo), day, secondsFrom, secondsTo])

                # reset intervals (the last steps)
                for rCtrl in ["TimekprUserConfDaySettingsConfDaysIntervalsFromHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsFromMinSB", "TimekprUserConfDaySettingsConfDaysIntervalsToHrSB", "TimekprUserConfDaySettingsConfDaysIntervalsToMinSB"]:
                    self._timekprAdminFormBuilder.get_object(rCtrl).set_text("0")

                # sort intervals
                self.sortHourIntervals()
                # status change
                self.setTimekprStatus(False, "Interval added")
                # adjust internal representation
                self.rebuildHoursFromIntervals()
                # recalc control availability
                self.calculateUserConfigControlAvailability()

    def removeHourIntervalClicked(self, evt):
        """Handle remove hour interval"""
        hourIdx = self.getSelectedHourInterval()[0]
        rIdx = 0

        # if it's not selected
        if hourIdx is None:
            # status
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_NOHOUR_SELECTED"))
        else:
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
            self.setTimekprStatus(False, msg.getTranslation("TK_MSG_STATUS_INTERVAL_REMOVED"))
            # adjust internal representation
            self.rebuildHoursFromIntervals()
            # recalc control availability
            self.calculateUserConfigControlAvailability()

    def rebuildHoursFromIntervals(self):
        """Rebuild hours from intervals in GUI, representation to user is different than actual config"""
        # get day
        calcDay = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")[0][3] if len(self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS")) > 0 else None
        # day is here
        if calcDay is not None:
            # clear internal hour representation
            self._timeLimitDaysHoursActual[calcDay] = {}

            # remove selected item
            for rIt in self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS"):
                # start time
                calcTime = cons.TK_DATETIME_START + timedelta(seconds=rIt[4])
                # total seconds
                totalSeconds = rIt[5] - rIt[4]
                # failover
                maxIt = 30

                # now loop through time in interval
                while totalSeconds > 0 and maxIt > 0:
                    # failover
                    maxIt -= 1
                    # hour
                    calcHour = str(calcTime.hour)
                    # build up hour
                    self._timeLimitDaysHoursActual[calcDay][calcHour] = {cons.TK_CTRL_SMIN: calcTime.minute, cons.TK_CTRL_EMIN: None}
                    # calc end of the hour
                    timeToSubtract = min(cons.TK_LIMIT_PER_HOUR - calcTime.minute * cons.TK_LIMIT_PER_MINUTE, totalSeconds)
                    # adjust time
                    calcTime += timedelta(seconds=timeToSubtract)
                    # subtract hour
                    totalSeconds -= timeToSubtract

                    # add end hour
                    self._timeLimitDaysHoursActual[calcDay][calcHour][cons.TK_CTRL_EMIN] = 60 if calcTime.minute == 0 else calcTime.minute
                    # print(calcTime, calcHour, timeToSubtract, totalSeconds, self._timeLimitDaysHoursActual[calcDay][calcHour])

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

    def weeklyLimitDayHrMinChanged(self, evt):
        """Process when weekly limit changes"""
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
        self.calculateUserConfigControlAvailability()

    def monthlyLimitDayHrMinChanged(self, evt, pCheckEnabled=True):
        """Process when monthly limit changes"""
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
        self.calculateUserConfigControlAvailability()

    def dailyLimitDayHrMinChanged(self, evt, pCheckEnabled=True):
        """Process stuff when dday changes"""
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
        self.calculateUserConfigControlAvailability()

    def dailyLimitDayHrIntervalsChanged(self, evt, pCheckEnabled=True):
        """Calculate control availability on hour change"""
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
        self.calculateUserConfigControlAvailability()

    def trackInactiveChanged(self, evt):
        """Call control calculations when inactive flag has been added"""
        # recalc control availability
        self.calculateUserConfigControlAvailability()

    def todayAddTimeChanged(self, evt):
        """Call control calculations when time has been added"""
        # recalc control availability
        self.calculateUserConfigControlAvailability()

    def dailyLimitsDaySelectionChanged(self, evt):
        """Set up intervals on day change"""
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
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsSubtractBT").set_sensitive(ti is not None)

    def applyDaysHourIntervalsClicked(self, evt):
        """Call set methods for changes"""
        self.applyDayAndHourIntervalChanges()

    def trackedSessionTypesChanged(self, evt):
        """Tracked sessions types changed"""
        enabled = self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsEntryEF").get_text() != ""
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsAddBT").set_sensitive(enabled)
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def trackedSessionTypesSelectionChanged(self, evt):
        """When hour interval selection changed"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsTreeView").get_selection().get_selected()
        # only if there is smth selected
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsRemoveBT").set_sensitive(ti is not None)

    def trackedSessionsAddClicked(self, evt):
        """Add tracked session"""
        # remove selected item
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS").append([self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsEntryEF").get_text()])
        self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsEntryEF").set_text("")
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def trackedSessionsRemoveClicked(self, evt):
        """Remove tracked session"""
        # defaults
        elemIdx = self.getSelectedConfigElement("TimekprTrackingSessionsTreeView")
        rIdx = 0
        # remove selected item
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS"):
            # check what to remove
            if elemIdx == rIdx:
                # remove
                self._timekprAdminFormBuilder.get_object("TimekprTrackingSessionsLS").remove(rIt.iter)
                # this is it
                break
            # count further
            rIdx += 1
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedSessionTypesChanged(self, evt):
        """Excluded sessions types changed"""
        enabled = self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsEntryEF").get_text() != ""
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsAddBT").set_sensitive(enabled)
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedSessionTypesSelectionChanged(self, evt):
        """When hour interval selection changed"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsTreeView").get_selection().get_selected()
        # only if there is smth selected
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsRemoveBT").set_sensitive(ti is not None)

    def excludedSessionsAddClicked(self, evt):
        """Add excluded session"""
        # remove selected item
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS").append([self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsEntryEF").get_text()])
        self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsEntryEF").set_text("")
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedSessionsRemoveClicked(self, evt):
        """Remove excluded session"""
        # defaults
        elemIdx = self.getSelectedConfigElement("TimekprExcludedSessionsTreeView")
        rIdx = 0
        # remove selected item
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS"):
            # check what to remove
            if elemIdx == rIdx:
                # remove
                self._timekprAdminFormBuilder.get_object("TimekprExcludedSessionsLS").remove(rIt.iter)
                # this is it
                break
            # count further
            rIdx += 1
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedUsersChanged(self, evt):
        """Excluded user list changed"""
        enabled = self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersEntryEF").get_text() != ""
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersAddBT").set_sensitive(enabled)
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedUsersSelectionChanged(self, evt):
        """When hour interval selection changed"""
        # refresh the child
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersTreeView").get_selection().get_selected()
        # only if there is smth selected
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersRemoveBT").set_sensitive(ti is not None)

    def excludedUsersAddClicked(self, evt):
        """Add excluded session"""
        # remove selected item
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS").append([self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersEntryEF").get_text()])
        self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersEntryEF").set_text("")
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def excludedUsersRemoveClicked(self, evt):
        """Remove excluded user"""
        # defaults
        elemIdx = self.getSelectedConfigElement("TimekprExcludedUsersTreeView")
        rIdx = 0
        # remove selected item
        for rIt in self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS"):
            # check what to remove
            if elemIdx == rIdx:
                # remove
                self._timekprAdminFormBuilder.get_object("TimekprExcludedUsersLS").remove(rIt.iter)
                # this is it
                break
            # count further
            rIdx += 1
        # verify control avilaility
        self.calculateTimekprConfigControlAvailability()

    def configControlTimesChanged(self, evt):
        """Change any control time"""
        self.calculateTimekprConfigControlAvailability()

    def closePropertiesSignal(self, evt, smth):
        """Close the config form"""
        # close
        self._mainLoop.quit()
