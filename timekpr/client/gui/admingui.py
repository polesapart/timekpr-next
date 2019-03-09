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
        self._timekprAdminFormBuilder.get_object("TimekprMainTabBar").set_current_page(1)
        self._timekprAdminFormBuilder.get_object("TimekprMainTabBar").set_current_page(0)
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationTabBar").set_current_page(1)
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationTabBar").set_current_page(2)
        self._timekprAdminFormBuilder.get_object("TimekprConfigurationTabBar").set_current_page(0)

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
        col.set_min_width(25)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # hour limits
        rend = Gtk.CellRendererSpin()
        rend.set_property("editable", True)
        rend.set_property("max_width_chars", 2)
        rend.set_property("width_chars", 2)
        rend.set_property("max-width-chars", 2)
        rend.set_property("width-chars", 2)
        adjustment = Gtk.Adjustment(0, 0, 24, 1, 5, 0)
        rend.set_property("adjustment", adjustment)
        rend.connect("edited", self.dayHoursChanged)
        col = Gtk.TreeViewColumn("Hrs", rend, text=3)
        col.set_min_width(30)
        col.add_attribute(rend, "editable", 2)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # minute limits
        rend = Gtk.CellRendererSpin()
        rend.set_property("editable", True)
        rend.set_property("max_width_chars", 2)
        rend.set_property("width_chars", 2)
        rend.set_property("max-width-chars", 2)
        rend.set_property("width-chars", 2)
        adjustment = Gtk.Adjustment(0, 0, 60, 1, 5, 0)
        rend.set_property("adjustment", adjustment)
        rend.connect("edited", self.dayMinutesChanged)
        col = Gtk.TreeViewColumn("Mins", rend, text=4)
        col.set_min_width(30)
        col.add_attribute(rend, "editable", 2)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").append_column(col)

        # second limits
        rend = Gtk.CellRendererSpin()
        rend.set_property("editable", True)
        rend.set_property("max_width_chars", 2)
        rend.set_property("width_chars", 2)
        rend.set_property("max-width-chars", 2)
        rend.set_property("width-chars", 2)
        adjustment = Gtk.Adjustment(0, 0, 60, 1, 5, 0)
        rend.set_property("adjustment", adjustment)
        rend.connect("edited", self.daySecondsChanged)
        col = Gtk.TreeViewColumn("Secs", rend, text=5)
        col.set_min_width(30)
        col.add_attribute(rend, "editable", 2)
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
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS").append([str(rDay), (cons.TK_DATETIME_START + timedelta(days=rDay-1)).strftime("%A"), False, 0, 0, 0, 0])

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
            # spin buttons for adjustments
            ,"TimekprUserConfTodaySettingsSetMinSB"
            ,"TimekprUserConfTodaySettingsSetHrSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsHrSB"
            ,"TimekprUserConfDaySettingsConfDaysIntervalsMinSB"
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
        self._timeLimitDaysHours = {}
        for rDay in range(1, 7+1):
            self._timeLimitDaysHours[str(rDay)] = {}
            for rHour in range(1, 23+1):
                self._timeLimitDaysHours[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

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
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentTodayLB").set_text(_NO_TIME_LIMIT_LABEL)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentWeekLB").set_text(_NO_TIME_LIMIT_LABEL)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentMonthLB").set_text(_NO_TIME_LIMIT_LABEL)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_active(False)
        for rDay in range(1, 7+1):
            # clear list store
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][2] = False
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][3] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][4] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][5] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay-1][6] = 0

            # clear day config
            for rHour in range(1, 23+1):
                self._timeLimitDaysHours[str(rDay)][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}

            # clear up the intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()

            # TODO: eventually we'll need to add a lot of stuff here

    def getIntervalList(self, pDay):
        """Get intervals for use in GUI"""
        # init hours for intervals
        timeLimits = []
        startHour = None
        endHour = None

        # loop through all days
        for rHour in range(0, 23+1):
            # define intervals
            if startHour is not None and endHour is not None:
                if str(rHour) not in self._timeLimitDaysHours[pDay] or self._timeLimitDaysHours[pDay][str(rHour)][cons.TK_CTRL_SMIN] != 0:
                    timeLimits.append([startHour, endHour])
                    startHour = None
                    endHour = None

            # we process only hours that are available
            if str(rHour) in self._timeLimitDaysHours[pDay]:
                # if start hour is not yet defined
                if startHour is None:
                    # first avaiable hour
                    startHour = str(rHour).rjust(2, "0") + ":" + str(self._timeLimitDaysHours[pDay][str(rHour)][cons.TK_CTRL_SMIN]).rjust(2, "0")

                # define end hour
                endDate = cons.TK_DATETIME_START + timedelta(hours=rHour, minutes=self._timeLimitDaysHours[str(pDay)][str(rHour)][cons.TK_CTRL_EMIN])
                endHour = str(endDate.hour).rjust(2, "0") + ":" + str(endDate.minute).rjust(2, "0")

                # define intervals
                if self._timeLimitDaysHours[pDay][str(rHour)][cons.TK_CTRL_EMIN] != 60 or rHour == 23:
                    timeLimits.append([startHour, endHour])
                    startHour = None
                    endHour = None

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

    # --------------- info population methods --------------- #

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
            # reset config
            # self._timeLimitDaysHours = {}

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
                                self._timeLimitDays.append(str(rDay))
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
                            self._timeLimitDaysHours[day] = {}

                            # loop through available hours
                            for rHour, rHourMinutes in rValue.items():
                                # add config
                                self._timeLimitDaysHours[day][str(rHour)] = {cons.TK_CTRL_SMIN: int(rHourMinutes[cons.TK_CTRL_SMIN]), cons.TK_CTRL_EMIN: int(rHourMinutes[cons.TK_CTRL_EMIN])}

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
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").set_text("0")
                self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetMinSB").set_text("0")
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
                self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").emit("value-changed")
                self._timekprAdminFormBuilder.get_object("TimekprUserConfMONDaySB").emit("value-changed")
            else:
                # disable all but choser
                self.toggleControls(False, True)
                # status
                self.setStatus(False, message)

    def applyUserConfig(self):
        # ## track inactive ##
        # set value
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_active(self._timeTrackInactive)
        # enable field & set button
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_sensitive(True)

        # enable refresh
        self._timekprAdminFormBuilder.get_object("TimekprUserSelectionRefreshBT").set_sensitive(True)

        # set selection to first row
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").set_cursor(0)
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

        # ## allowed days ###
        for rDay in range(1, 7+1):
            # if we have a day
            if str(rDay) in self._timeLimitDays:
                # enable certain days
                self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)-1][2] = True
            else:
                # disable certain days
                self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)-1][2] = False
        # enable editing
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").set_sensitive(True)
        # enable editing
        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").set_sensitive(True)

        # ## limits per allowed days ###
        for rDay in range(0, len(self._timeLimitDaysLimits)):
            # calculate time
            limitTime = cons.TK_DATETIME_START + timedelta(seconds=self._timeLimitDaysLimits[int(rDay)])
            # enable certain days
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][3] = limitTime.hour
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][4] = limitTime.minute
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][5] = limitTime.second
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[rDay][6] = self._timeLimitDaysLimits[int(rDay)]

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

    def calculateControlAvailability(self):
        # ## add time today ##
        enabled = (int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").get_text()) != 0 or int(self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetMinSB").get_text()))
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetAddBT").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetSubractBT").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetSetBT").set_sensitive(enabled)

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
        # enable apply
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsApplyBT").set_sensitive(enabled)

        enabled_alt = False
        # ## limits per allowed days ###
        for rDay in range(0, len(self._timeLimitDaysLimits)):
            # check if different
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[int(rDay)][6] != self._timeLimitDaysLimits[int(rDay)]:
                # enable apply
                enabled = True
                # this is it
                break
        # enable apply
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsApplyBT").set_sensitive(enabled or enabled_alt)

        # ## limit per week ##
        timeLimitWeek = self.getWeekLimitSecs()
        timeLimitMonth = self.getMonthLimitSecs()
        # enable apply
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMONApplyBT").set_sensitive(timeLimitWeek != self._timeLimitWeek or timeLimitMonth != self._timeLimitMonth)
        # whether we can change the limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_sensitive(timeLimitWeek == cons.TK_LIMIT_PER_WEEK)
        self.weekAvailabilityChanged(None)
        # whether we can change the limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_sensitive(timeLimitMonth == cons.TK_LIMIT_PER_MONTH)
        self.monthAvailabilityChanged(None)

        # ## add new intervals ##
        enabled = self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").get_sensitive()
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsHrSB").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsMinSB").set_sensitive(enabled)
        # check whether to enable add/remove intervals
        if int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsHrSB").get_text()) > 0 or int(self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsMinSB").get_text()) > 0:
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsAddBT").set_sensitive(True)
        else:
            self._timekprAdminFormBuilder.get_object("TimekprUserConfDaySettingsConfDaysIntervalsAddBT").set_sensitive(False)








    def enableTimeControlToday(self, pEnable=True):
        """Enable buttons to add time today"""
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetHrSB").set_sensitive(pEnable)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsSetMinSB").set_sensitive(pEnable)

    # --------------- GTK signal methods --------------- #

    def userSelectionChanged(self, evt):
        """User selected"""
        # get username
        userName = self.getSelectedUserName()
        # only if connected
        if userName is not None:
            # get user config
            self.retrieveUserConfig(userName, True if evt is not None else False)

        # return
        return True

    def userConfigurationRefreshActivated(self, evt):
        """User requested config restore from server"""
        self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").emit("changed")

    def dayAvailabilityChanged(self, widget, path):
        """Changed minutes depending on day availability"""
        # flip the checkbox
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2] = not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]
        # if day was disabled, reset hours and minutes
        if not self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][2]:
            # reset hours & minutes
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][5] = 0
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][6] = 0

            # change interval selection as well
            if self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][0] in self._timeLimitDays:
                # clear day config
                for rHour in range(1, 23+1):
                    self._timeLimitDaysHours[self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][0]][str(rHour)] = {cons.TK_CTRL_SMIN: 0, cons.TK_CTRL_EMIN: 60}
                # clear stuff and disable intervals
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").set_sensitive(False)
        else:
            # enable intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").set_sensitive(True)
            # enable interval refresh
            self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().emit("changed")

        # recalc control availability
        self.calculateControlAvailability()

    def recalcDayTotalLimit(self, path):
        """Recalc total seconds"""
        # calculate todays limit
        totalSecs = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3] * cons.TK_LIMIT_PER_HOUR
        totalSecs += self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] * cons.TK_LIMIT_PER_MINUTE
        totalSecs += self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][5]
        # set the limit
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][6] = totalSecs

    def dayHoursChanged(self, widget, path, value):
        "Set hours to liststore"
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][3] = int(value)
        # recalc totals
        self.recalcDayTotalLimit(path)
        # recalc control availability
        self.calculateControlAvailability()

    def dayMinutesChanged(self, widget, path, value):
        """Set minutes to liststore"""
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][4] = int(value)
        # recalc totals
        self.recalcDayTotalLimit(path)
        # recalc control availability
        self.calculateControlAvailability()

    def daySecondsChanged(self, widget, path, value):
        """Set seconds to liststore"""
        self._timekprAdminFormBuilder.get_object("TimekprWeekDaysLS")[path][5] = int(value)
        # recalc totals
        self.recalcDayTotalLimit(path)
        # recalc control availability
        self.calculateControlAvailability()

    def weekAvailabilityChanged(self, evt):
        """Change in minutes depending on week availability"""
        # whether there should be a week limit
        enabled = self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").get_active()
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKDaySB").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKHrSB").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKMinSB").set_sensitive(enabled)
        # check values
        # self.weeklyLimitDayHrMinChanged(evt, enabled)

    def monthAvailabilityChanged(self, evt):
        """Change in minutes depending on week availability"""
        # whether there should be a month limit
        enabled = self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").get_active()
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONDaySB").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONHrSB").set_sensitive(enabled)
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONMinSB").set_sensitive(enabled)
        # check values
        #self.monthlyLimitDayHrMinChanged(evt, enabled)

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
        # whether we can change the limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfWKCB").set_sensitive(totalSecs == cons.TK_LIMIT_PER_WEEK)

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
        # whether we can change the limit
        self._timekprAdminFormBuilder.get_object("TimekprUserConfMONCB").set_sensitive(totalSecs == cons.TK_LIMIT_PER_MONTH)

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
        (tm, ti) = self._timekprAdminFormBuilder.get_object("TimekprWeekDaysTreeView").get_selection().get_selected()

        # only if there is smth selected
        if ti is not None:
            # clear out existing intervals
            self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").clear()
            # idx
            dayIdx = str(tm.get_value(ti, 0))

            # check if day is in the list
            if not dayIdx in self._timeLimitDays:
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").set_sensitive(False)
            else:
                self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsTreeView").set_sensitive(True)

                # fill intervals only if that day exists
                if dayIdx in self._timeLimitDaysHours:
                    # idx
                    idx = 0
                    # fill the intervals
                    for rInterval in self.getIntervalList(dayIdx):
                        # fill in the intervals
                        self._timekprAdminFormBuilder.get_object("TimekprHourIntervalsLS").append([idx, rInterval[0], rInterval[1]])
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

    def closePropertiesSignal(self, evt):
        """Close the config form"""
        # close
        self._timekprConfigDialog.hide()
