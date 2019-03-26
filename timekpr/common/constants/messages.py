"""
Created on Mar 19, 2019

@author: mjasnik
"""
# imports
import gettext
from gettext import ngettext as _translatePlural
from gettext import gettext as _translateSingle


def _(pMsg):
    """Make automated tools like poedit to pick up translations, which will actually be translated later"""
    return pMsg


# ## This module is responsible for all message translations for timekpr ##

"""Initialize all stuff for messages"""
# init python gettext
gettext.bindtextdomain("timekpr", "/usr/share/locale")
gettext.textdomain("timekpr")
# messages
_messages = {}


def initMessages():
    """Initialize all messages"""
    # ## define user admin command texts ##
    _messages["TK_MSG_USER_ADMIN_CMD_HELP"] = {"s": _("print help, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_USERLIST"] = {"s": _("this gets saved user list from the server, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_USERCONFIG"] = {"s": _("this gets user configuration from the server, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETALLOWEDDAYS"] = {"s": _("this sets allowed days for the user, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETALLOWEDHOURS"] = {"s": _("this sets allowed hours per specified day or ALL for every day, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETTIMELIMITS"] = {"s": _("this sets time limits per all allowed days, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETTIMELIMITWK"] = {"s": _("this sets time limits per week, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETTIMELIMITMON"] = {"s": _("this sets time limits per month, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETTRACKINACTIVE"] = {"s": _("this sets whether to track inactive user sessions, example")}
    _messages["TK_MSG_USER_ADMIN_CMD_SETTIMELEFT"] = {"s": _("this sets time left for the user at current moment, example (add one hour")}

    # ## this defines messages for use in configuration validation ##
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_NONE"] = {"s": _("Control sessions types are not passed")}
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID"] = {"s": _("Control sessions types list is not correct")}
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID_SET"] = {"s": _("Control sessions types list is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_EXCLSESSIONW_NONE"] = {"s": _("Excluded session types are not passed")}
    _messages["TK_MSG_ADMIN_CHK_EXCLSESSIONS_INVALID"] = {"s": _("Excluded session types list is not correct")}
    _messages["TK_MSG_ADMIN_CHK_EXCLSESSIONS_INVALID_SET"] = {"s": _("Excluded session types list is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_EXCLUSERS_NONE"] = {"s": _("Excluded user list is not passed")}
    _messages["TK_MSG_ADMIN_CHK_EXCLUSERS_INVALID"] = {"s": _("Excluded user list is not correct")}
    _messages["TK_MSG_ADMIN_CHK_EXCLUSERS_INVALID_SET"] = {"s": _("Excluded user list is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_FINALWARNTIME_NONE"] = {"s": _("Final warning time is not passed")}
    _messages["TK_MSG_ADMIN_CHK_FINALWARNTIME_INVALID"] = {"s": _("Final warning time \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_FINALWARNTIME_INVALID_SET"] = {"s": _("Final warning time \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_TERMTIME_NONE"] = {"s": _("Termination time is not passed")}
    _messages["TK_MSG_ADMIN_CHK_TERMTIME_INVALID"] = {"s": _("Termination time \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_TERMTIME_INVALID_SET"] = {"s": _("Termination time \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_TRACKINACTIVE_NONE"] = {"s": _("Track inactive is not passed")}
    _messages["TK_MSG_ADMIN_CHK_TRACKINACTIVE_INVALID"] = {"s": _("Track inactive \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_TRACKINACTIVE_INVALID_SET"] = {"s": _("Track inactive \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_LOGLEVEL_NONE"] = {"s": _("Log level is not passed")}
    _messages["TK_MSG_ADMIN_CHK_LOGLEVEL_INVALID"] = {"s": _("Log level \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_LOGLEVEL_INVALID_SET"] = {"s": _("Log level \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_POLLTIME_NONE"] = {"s": _("Poll time is not passed")}
    _messages["TK_MSG_ADMIN_CHK_POLLTIME_INVALID"] = {"s": _("Poll time \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_POLLTIME_INVALID_SET"] = {"s": _("Poll time \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_SAVETIME_NONE"] = {"s": _("Save time is not passed")}
    _messages["TK_MSG_ADMIN_CHK_SAVETIME_INVALID"] = {"s": _("Save time \"%%s\"is not correct")}
    _messages["TK_MSG_ADMIN_CHK_SAVETIME_INVALID_SET"] = {"s": _("Save time \"%%s\" is not correct and can not be set")}
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_NONE"] = {"s": _("Control sessions types are not passed")}
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID"] = {"s": _("Control sessions types list is not correct")}
    _messages["TK_MSG_ADMIN_CHK_CTRLSESSIONS_INVALID_SET"] = {"s": _("Control sessions types list is not correct and can not be set")}

    # ## this defines messages for use in user configuration validation ##
    _messages["TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_DAY_NONE"] = {"s": _("User's \"%%s\" day number must be present")}
    _messages["TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_DAY_INVALID"] = {"s": _("User's \"%%s\" day number must be between 1 and 7")}
    _messages["TK_MSG_USER_ADMIN_CHK_ALLOWEDHOURS_INVALID_SET"] = {"s": _("User's \"%%s\" allowed hours are not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_NONE"] = {"s": _("User's \"%%s\" day limits list is not passed")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_INVALID"] = {"s": _("User's \"%%s\" day limits list is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAILYLIMITS_INVALID_SET"] = {"s": _("User's \"%%s\" day limits list is not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAYLIST_NONE"] = {"s": _("User's \"%%s\" day list is not passed")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAYLIST_INVALID"] = {"s": _("User's \"%%s\" day list is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_DAYLIST_INVALID_SET"] = {"s": _("User's \"%%s\" day list is not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_NONE"] = {"s": _("User's \"%%s\" monthly allowance is not passed")}
    _messages["TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_INVALID"] = {"s": _("User's \"%%s\" monthly allowance is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_MONTHLYALLOWANCE_INVALID_SET"] = {"s": _("User's \"%%s\" monthly allowance is not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_TIMELIMIT_OPERATION_INVALID"] = {"s": _("User's \"%%s\" set time operation can be one of these: -+=")}
    _messages["TK_MSG_USER_ADMIN_CHK_TIMELIMIT_INVALID"] = {"s": _("User's \"%%s\" set time limit is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_TIMELIMIT_INVALID_SET"] = {"s": _("User's \"%%s\" set time limit is not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_NONE"] = {"s": _("User's \"%%s\" track inactive flag is not passed")}
    _messages["TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_INVALID"] = {"s": _("User's \"%%s\" track inactive flag is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_TRACKINACTIVE_INVALID_SET"] = {"s": _("User's \"%%s\" track inactive flag is not correct and can not be set")}
    _messages["TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_NONE"] = {"s": _("User's \"%%s\" weekly allowance is not passed")}
    _messages["TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_INVALID"] = {"s": _("User's \"%%s\" weekly allowance is not correct")}
    _messages["TK_MSG_USER_ADMIN_CHK_WEEKLYALLOWANCE_INVALID_SET"] = {"s": _("User's \"%%s\" weekly allowance is not correct and can not be set")}

    # ## this defines messages for use in configuration loader ##
    _messages["TK_MSG_CONFIG_LOADER_ERROR_GENERIC"] = {"s": _("Something went wrong while loading configuration. Please inspect Timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_UNEXPECTED_ERROR"] = {"s": _("Unexpected ERROR getting confguration. Please inspect timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_USER_UNEXPECTED_ERROR"] = {"s": _("Unexpected ERROR getting user confguration. Please inspect timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_USERLIST_UNEXPECTED_ERROR"] = {"s": _("Unexpected ERROR getting user list. Please inspect timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_SAVECONFIG_UNEXPECTED_ERROR"] = {"s": _("Unexpected ERROR updating confguration. Please inspect timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_SAVECONTROL_UNEXPECTED_ERROR"] = {"s": _("Unexpected ERROR updating control. Please inspect timekpr log files")}
    _messages["TK_MSG_CONFIG_LOADER_USERCONFIG_NOTFOUND"] = {"s": _("User \"%%s\" configuration is not found")}
    _messages["TK_MSG_CONFIG_LOADER_USERCONTROL_NOTFOUND"] = {"s": _("User \"%%s\" control file is not found")}
    _messages["TK_MSG_CONFIG_LOADER_USER_NOTFOUND"] = {"s": _("User \"%%s\" is not found")}

    # ## misc errors ##
    _messages["TK_MSG_UNEXPECTED_ERROR"] = {"s": _("UNEXPECTED ERROR: %%s")}
    _messages["TK_MSG_DBUS_COMMUNICATION_COMMAND_FAILED"] = {"s": _("Command FAILED: access denied")}
    _messages["TK_MSG_DBUS_COMMUNICATION_COMMAND_NOT_ACCEPTED"] = {"s": _("Command FAILED: message was not accepted")}

    # ## this defines messages for use in notifications ##
    _messages["TK_MSG_STATUS_CONNECTED"] = {"s": _("Connected")}
    _messages["TK_MSG_STATUS_CONNECTING"] = {"s": _("Connecting...")}
    _messages["TK_MSG_STATUS_CONNECTION_FAILED"] = {"s": _("Failed to connect")}
    _messages["TK_MSG_STATUS_CONNECTION_ACCESS_DENIED"] = {"s": _("Please reopen the application if You have permissions and timekpr is running")}
    _messages["TK_MSG_STATUS_STARTED"] = {"s": _("Started")}
    _messages["TK_MSG_STATUS_USER_CONFIG_RETRIEVED"] = {"s": _("User configuration retrieved")}
    _messages["TK_MSG_STATUS_CONFIG_RETRIEVED"] = {"s": _("Configuration retrieved")}
    _messages["TK_MSG_STATUS_TRACKINACTIVE_PROCESSED"] = {"s": _("Track inactive for user has been processed")}
    _messages["TK_MSG_STATUS_ADJUSTTIME_PROCESSED"] = {"s": _("Additional time for user has been processed")}
    _messages["TK_MSG_STATUS_WKMONADJUSTTIME_PROCESSED"] = {"s": _("Weekly and monthly limits for user have been processed")}
    _messages["TK_MSG_STATUS_ALLOWEDDAYS_PROCESSED"] = {"s": _("Allowed days for user have been processed")}
    _messages["TK_MSG_STATUS_TIMELIMITS_PROCESSED"] = {"s": _("Time limits for days for user have been processed")}
    _messages["TK_MSG_STATUS_ALLOWEDHOURS_PROCESSED"] = {"s": _("Allowed hours for user have been processed")}
    _messages["TK_MSG_STATUS_ALLTIMELIMITS_PROCESSED"] = {"s": _("Time limits for days for user have been processed")}
    _messages["TK_MSG_STATUS_CONFIGURATION_SAVED"] = {"s": _("Timekpr configuration has been saved")}
    _messages["TK_MSG_STATUS_NODAY_SELECTED"] = {"s": _("Please select a day to set the limits")}
    _messages["TK_MSG_STATUS_INTERVAL_OVERLAP_DETECTED"] = {"s": _("Interval overlaps with existing one")}
    _messages["TK_MSG_STATUS_INTERVALSTART_CONFLICT_DETECTED"] = {"s": _("Interval start conflicts with existing one")}
    _messages["TK_MSG_STATUS_INTERVALEND_CONFLICT_DETECTED"] = {"s": _("Interval end conflicts with existing one")}
    _messages["TK_MSG_STATUS_INTERVAL_DUPLICATE_DETECTED"] = {"s": _("Interval start or end duplicates existing interval")}
    _messages["TK_MSG_STATUS_INTERVAL_STARTENDEQUAL_DETECTED"] = {"s": _("Interval start can not be the same as end")}
    _messages["TK_MSG_STATUS_NOHOUR_SELECTED"] = {"s": _("Please select a hour interval to remove")}
    _messages["TK_MSG_STATUS_INTERVAL_REMOVED"] = {"s": _("Interval removed")}
    _messages["TK_MSG_STATUS_INTERFACE_NOTREADY"] = {"s": _("Timekpr interface is not yet ready")}

    # ## this defines messages for use in CLI ##
    _messages["TK_MSG_CONSOLE_GUI_NOT_AVAILABLE"] = {"s": _("WARNING: Timekpr administration utility was asked to run in GUI mode, but no displays are available, thus running in CLI...")}
    _messages["TK_MSG_CONSOLE_COMMAND_INCORRECT"] = {"s": _("The command is incorrect:")}
    _messages["TK_MSG_CONSOLE_USAGE_NOTES"] = {"s": _("The usage of timekpr admin client is as follows:")}
    _messages["TK_MSG_CONSOLE_USERS_TOTAL"] = {"s": _("%(n)s user in total:"), "p": _("%(n)s users in total:")}
    _messages["TK_MSG_CONSOLE_CONFIG_FOR"] = {"s": _("Config for %s:")}

    # ## this defines messages for use in menus ##
    _messages["TK_MSG_MENU_TIME_LEFT"] = {"s": _("Time left...")}
    _messages["TK_MSG_MENU_CONFIGURATION"] = {"s": _("Limits & configuration")}
    _messages["TK_MSG_MENU_ABOUT"] = {"s": _("About")}

    # ## GUI labels ##
    _messages["TK_MSG_ENTER_TRANSLATION_CREDITS"] = {"s": _("Instead of this text, please enter translator credits!")}
    _messages["TK_MSG_LOGO_LABEL"] = {"s": _("Keep control of computer usage")}

    # ## this defines messages for use in notifications ##
    _messages["TK_MSG_NOTIFICATION_TITLE"] = {"s": _("Timekpr notification")}
    _messages["TK_MSG_NOTIFICATION_NOT_LIMITED"] = {"s": _("Your time is not limited today")}
    _messages["TK_MSG_NOTIFICATION_ALLOWANCE_CHANGED"] = {"s": _("Time allowance has changed, please note new time left!")}
    _messages["TK_MSG_NOTIFICATION_CONFIGURATION_CHANGED"] = {"s": _("Time limit configuration has changed, please note new configuration!")}
    _messages["TK_MSG_NOTIFICATION_CANNOT_CONNECT"] = {"s": _("There is a problem connecting to timekpr daemon (%%s)!")}
    _messages["TK_MSG_NOTIFICATION_CANNOT_COMMUNICATE"] = {"s": _("There is a problem communicating to timekpr (%%s)!")}
    _messages["TK_MSG_NOTIFICATION_CANNOT_INIT_ICON"] = {"s": _("Icon inititalization error (%%s)!")}
    # TRANSLATORS: this is a part of message "Your time is up, You will be forcibly logged out in %s seconds", please translate accordingly
    _messages["TK_MSG_NOTIFICATION_TIME_IS_UP_1"] = {"s": _("Your time is up, You will be forcibly logged out in")}
    # TRANSLATORS: this is a part of message "Your time is up, You will be forcibly logged out in %s seconds", please translate accordingly
    _messages["TK_MSG_NOTIFICATION_TIME_IS_UP_2"] = {"s": _("%(n)s second"), "p": _("%(n)s seconds")}
    _messages["TK_MSG_NOTIFICATION_CONNECTION_ERROR"] = {"s": _("Internal connection error, please check log files")}
    # TRANSLATORS: this is a part of message "You have %i hour(s), %i minute(s) and %i second(s) left" please translate accordingly
    _messages["TK_MSG_NOTIFICATION_TIME_LEFT_1"] = {"s": _("You have %(n)s hour"), "p": _("You have %(n)s hours")}
    # TRANSLATORS: this is a part of message "You have %i hour(s), %i minute(s) and %i second(s) left" please translate accordingly
    _messages["TK_MSG_NOTIFICATION_TIME_LEFT_2"] = {"s": _("%(n)s minute"), "p": _("%(n)s minutes")}
    # TRANSLATORS: this is a part of message "You have %i hour(s), %i minute(s) and %i second(s) left" please translate accordingly
    _messages["TK_MSG_NOTIFICATION_TIME_LEFT_3"] = {"s": _("%(n)s second left"), "p": _("%(n)s seconds left")}


# init
initMessages()


def getTranslation(pMsgCode, n=None):
    """Get message translation"""
    # initial
    result = None
    # we need to translate plurals
    if "p" in _messages[pMsgCode] and n is not None:
        # numbers
        try:
            result = _translatePlural(_messages[pMsgCode]["s"], _messages[pMsgCode]["p"], n) % {"n": n}
        except Exception:
            pass
    # if translation was not plural or plural failed
    if result is None:
        # single
        result = _translateSingle(_messages[pMsgCode]["s"]).replace("%%", "%")
    # result
    return result


# main start
if __name__ == "__main__":
    print(getTranslation("TK_MSG_USER_ADMIN_CMD_USERLIST"))
    print(getTranslation("TK_MSG_USER_ADMIN_CMD_HELP", 1))
    print(getTranslation("TK_MSG_USER_ADMIN_CMD_SETTIMELIMITWK", 3))
