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

        """
        # sets up limit variables
        timeSpent = None
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
        """

        # ## forms builders ##
        # init config builder
        self._timekprAdminFormBuilder = Gtk.Builder()
        # get our dialog
        self._timekprAdminFormBuilder.add_from_file(os.path.join(self._resourcePath, "admin_alt.glade"))
        # connect signals, so they get executed
        self._timekprAdminFormBuilder.connect_signals(self)
        # get window
        self._timekprAdminForm = self._timekprAdminFormBuilder.get_object("TimekprApplicationWindow")

        """
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
        """

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

        # start main loop
        self._mainLoop.run()

    # --------------- initialization / control methods --------------- #

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

    def initInternalConfiguration(self):
        """This initializes the internal configuration for admin form"""
        self._controlButtons = [
            # combo
            "TimekprUserSelectionCB"
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
        ]

    def toggleControls(self, pEnable=True):
        """Enable or disable all controls for the form"""
        # apply settings to all buttons`
        for rButton in self._controlButtons:
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
        else:
            # status
            self.setStatus(False, message)

    def retrieveUserConfig(self, pUserName):
        """Get user configuration from server"""
        # clear before user
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
                        print(rKey, rValue)
                        # limits
                        timeSpent = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentStr = str((timeSpent - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpent.hour).rjust(2, "0") + ":" + str(timeSpent.minute).rjust(2, "0") + ":" + str(timeSpent.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentTodayLB").set_text(timeSpentStr)
                    elif rKey == "TIME_SPENT_WEEK":
                        # limits
                        timeSpentWeek = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentWeekStr = str((timeSpentWeek - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpentWeek.hour).rjust(2, "0") + ":" + str(timeSpentWeek.minute).rjust(2, "0") + ":" + str(timeSpentWeek.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentWeekLB").set_text(timeSpentWeekStr)
                    elif rKey == "TIME_SPENT_MONTH":
                        # limits
                        timeSpentMonth = cons.TK_DATETIME_START + timedelta(seconds=rValue)
                        timeSpentMonthStr = str((timeSpentMonth - cons.TK_DATETIME_START).days).rjust(2, "0") + ":" + str(timeSpentMonth.hour).rjust(2, "0") + ":" + str(timeSpentMonth.minute).rjust(2, "0") + ":" + str(timeSpentMonth.second).rjust(2, "0")
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodayInfoSpentMonthLB").set_text(timeSpentMonthStr)
                    elif rKey == "TRACK_INACTIVE":
                        # track inactive
                        timeTrackInactive = bool(rValue)
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_active(timeTrackInactive)
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveCB").set_sensitive(True)
                        self._timekprAdminFormBuilder.get_object("TimekprUserConfTodaySettingsTrackInactiveSetBT").set_sensitive(True)


                    # timeTrackInactive = True if pTimeLeft[cons.TK_CTRL_TRACK] else False



                """
                ALLOWED_HOURS_5: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                ALLOWED_HOURS_4: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                LIMITS_PER_WEEKDAYS: 2100;2100;2100;2100;2100;2100;2100
                ALLOWED_HOURS_2: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                ALLOWED_HOURS_7: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                ALLOWED_WEEKDAYS: 1;2;3;4;5;6;7
                ALLOWED_HOURS_3: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                ALLOWED_HOURS_6: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                ALLOWED_HOURS_1: 0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23
                """

                # status
                self.setStatus(False, "User config retrieved")
                # enable
                #self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB").set_sensitive(True)
            else:
                # status
                self.setStatus(False, message)

    # --------------- GTK signal methods --------------- #

    def userSelectionChanged(self, evt):
        """User selected"""
        # only if connected
        if self._isConnected:
            userCombobox = self._timekprAdminFormBuilder.get_object("TimekprUserSelectionCB")
            # get chosen index, model and actual id of the item
            userIdx = userCombobox.get_active()
            userModel = userCombobox.get_model()
            userName = userModel[userIdx][0]

            # get user config
            self.retrieveUserConfig(userName)

        # return
        return True

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
