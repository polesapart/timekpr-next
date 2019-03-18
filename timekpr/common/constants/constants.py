"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import dbus
from datetime import datetime

# ## constants ##
# version (in case config is corrupt or smth like that)
TK_VERSION = "0.1.13"
TK_DEV_ACTIVE = False  # change this accordingly when running in DEV or PROD
TK_DEV_BUS = "ses"  # this sets up which bus to use for development (sys or ses)

# formats
TK_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TK_LOG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
TK_DATETIME_START = datetime(2018, 1, 1)

# logging
TK_LOG_LEVEL_INFO = 1
TK_LOG_LEVEL_DEBUG = 2
TK_LOG_LEVEL_EXTRA_DEBUG = 3
TK_LOG_L = "lvl"
TK_LOG_D = "dir"
TK_LOG_TEMP_DIR = "/tmp"
TK_LOG_PID_EXT = ".pid"

# ## dbus ##
# common
TK_DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

# login1
TK_DBUS_L1_OBJECT = "org.freedesktop.login1"
TK_DBUS_L1_PATH = "/org/freedesktop/login1"
TK_DBUS_L1_MANAGER_INTERFACE = "org.freedesktop.login1.Manager"

# ck
TK_DBUS_CK_OBJECT = "org.freedesktop.ConsoleKit"
TK_DBUS_CK_PATH = "/org/freedesktop/ConsoleKit"
TK_DBUS_CK_MANAGER_INTERFACE = "org.freedesktop.ConsoleKit.Manager"

# user / session
TK_DBUS_USER_OBJECT = "org.freedesktop.login1.User"
TK_DBUS_SESSION_OBJECT = "org.freedesktop.login1.Session"

# path / objects / interfaces
TK_DBUS_BUS_NAME = "com.timekpr.server"
TK_DBUS_SERVER_PATH = "/com/timekpr/server"
TK_DBUS_ADMIN_INTERFACE = "com.timekpr.server.admin"
TK_DBUS_USER_NOTIF_PATH_PREFIX = "/com/timekpr/server/user/"
TK_DBUS_USER_NOTIF_INTERFACE = "com.timekpr.server.user.notifications"
TK_DBUS_USER_LIMITS_INTERFACE = "com.timekpr.server.user.limits"
TK_DBUS_USER_ADMIN_INTERFACE = "com.timekpr.server.user.admin"

# DBUS performance measurement
TK_DBUS_ANSWER_TIME = 3

# user properties
TK_CTRL_UID = "USERID"
TK_CTRL_UNAME = "USERNAME"
TK_CTRL_UPATH = "USERPATH"

# limit configuration
TK_CTRL_NDAY = "NEXTDAY"   # next day idx
TK_CTRL_PDAY = "PREVDAY"   # previous day idx
TK_CTRL_LIMITD = "LIMITD"  # limit idx
TK_CTRL_LEFTD = "LEFTD"    # time left today idx
TK_CTRL_LEFT = "LEFT"      # time left idx (continously)
TK_CTRL_LEFTW = "LEFTW"    # time left for week
TK_CTRL_LEFTM = "LEFTM"    # time left for month
TK_CTRL_LCHECK = "LCHK"    # last checked idx
TK_CTRL_LSAVE = "LSAVE"    # last saved idx
TK_CTRL_LMOD = "LMOD"      # file modification idx (control)
TK_CTRL_LCMOD = "LMCOD"    # file modification idx (config)
TK_CTRL_LIMITW = "LIMITW"  # left per week idx
TK_CTRL_LIMITM = "LIMITM"  # left per month idx
TK_CTRL_ACT = "ACTIVE"     # is hour enabled
TK_CTRL_SLEEP = "SLEEP"    # time spent in "inactive"
TK_CTRL_SPENT = "SPENT"    # time spent in this session
TK_CTRL_SPENTH = "SPENTH"  # time spent in this hour
TK_CTRL_SPENTD = "SPENTD"  # time spent in this day
TK_CTRL_SPENTW = "SPENTW"  # time spent for week
TK_CTRL_SPENTM = "SPENTM"  # time spent for month
TK_CTRL_SMIN = "STARTMIN"  # start minute in this hour
TK_CTRL_EMIN = "ENDMIN"    # end minute in this hour
TK_CTRL_INT = "INTERVALS"  # intervals of time available to user
TK_CTRL_TRACK = "TRACKI"   # whether to track inactive sessions

# notificaton limits
TK_NOTIF_LEFT = "LEFT"
TK_NOTIF_INTERVAL = "INTERVAL"
TK_NOTIF_URGENCY = "URGENCY"

# notification idx config
TK_ICON_NOTIF = "NOTIF-ICON"
TK_ICON_STAT = "STATUS-ICON"
TK_DBUS_PRIO = "DBUS-PRIO"

# session types (and whether they are subject to termination)
# "unspecified" (for cron PAM sessions and suchalike), "tty" (for text logins) or "x11"/"mir"/"wayland" (for graphical logins).
# real
TK_SESSION_TYPES_CTRL = "x11;wayland;mir"
TK_SESSION_TYPES_EXCL = "tty;unspecified"
# exclude users
TK_USERS_EXCL = "testtimekpr;gdm;kdm;lightdm;mdm;lxdm;xdm;sddm;cdm"

# ## user defaults ##
# default value for allowed hours
TK_ALLOWED_HOURS = "0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23"
# default value for allowed week days
TK_ALLOWED_WEEKDAYS = "1;2;3;4;5;6;7"
# default value for limit per hour
TK_LIMIT_PER_MINUTE = 60
# default value for limit per hour
TK_LIMIT_PER_HOUR = 3600
# default value for limit per day
TK_LIMIT_PER_DAY = 86400
# default value for limit per week
TK_LIMIT_PER_WEEK = TK_LIMIT_PER_DAY*7
# default value for limit per month
TK_LIMIT_PER_MONTH = TK_LIMIT_PER_DAY*31
# default value for limit per day
TK_LIMITS_PER_WEEKDAYS = "%s;%s;%s;%s;%s;%s;%s" % (TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY)

# ## default values for control ##
# time control
# in-memory poll time
TK_POLLTIME = 3
# flush interval
TK_SAVE_INTERVAL = 30
# time left for putting user on kill list
TK_TERMINATION_TIME = 15
# time left for final warning time
TK_FINAL_COUNTDOWN_TIME = 5
# default value for tracking inactive sessions
TK_TRACK_INACTIVE = False

# ## files ##
# config
TK_MAIN_CONFIG_FILE = "timekpr.conf"
TK_USER_CONFIG_FILE = "timekpr.%s.conf"

# ## timekpr notification config ##
# priorites
TK_PRIO_LOW = "low"
TK_PRIO_NORMAL = "normal"
TK_PRIO_WARNING = "warning"
TK_PRIO_IMPORTANT = "important"
TK_PRIO_CRITICAL = "critical"
TK_PRIO_IMPORTANT_INFO = "important_info"

# config
TK_PRIO_CONF = {}
TK_PRIO_CONF["logo"] = {TK_ICON_STAT: "timekpr.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF["client-logo"] = {TK_ICON_STAT: "timekpr-client.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF["unlimited"] = {TK_ICON_STAT: "timekpr-padlock-unlimited-green.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_LOW] = {TK_ICON_STAT: "timekpr-padlock-limited-green.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_NORMAL] = {TK_ICON_STAT: "timekpr-padlock-limited-green.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_WARNING] = {TK_ICON_STAT: "timekpr-padlock-limited-yellow.svg", TK_ICON_NOTIF: "gtk-dialog-warning", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_IMPORTANT] = {TK_ICON_STAT: "timekpr-padlock-limited-red.svg", TK_ICON_NOTIF: "dialog-warning", TK_DBUS_PRIO: dbus.Byte(2, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_CRITICAL] = {TK_ICON_STAT: "timekpr-padlock-limited-red.svg", TK_ICON_NOTIF: "gtk-dialog-error", TK_DBUS_PRIO: dbus.Byte(2, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_IMPORTANT_INFO] = {TK_ICON_STAT: "timekpr-padlock-limited-yellow.svg", TK_ICON_NOTIF: "gtk-dialog-info", TK_DBUS_PRIO: dbus.Byte(2, variant_level=1)}

# ## timekpr notification config ##
# define admin commands
TK_ADMIN_COMMANDS = {
    # "--setloglevel"             : ""
    # ,"--setpolltime"             : ""
    # ,"--setsavetime"             : ""
    # ,"--settrackinactive"        : ""
    # ,"--setterminationtime"      : ""
    # ,"--setfinalwarningtime"     : ""
    # ,"--setsessiontypes"         : ""
    # ,"--setexcludedsessiontypes" : ""
    # ,"--setexcludedusers"        : ""
}
# define user admin commands
TK_USER_ADMIN_COMMANDS = {
     "--help"              : "print help, example:\n    timekpra --help"
    ,"--userlist"          : "this gets saved user list from the server, example:\n    timekpra --userlist"
    ,"--userconfig"        : "this gets user configuration from the server, example:\n    timekpra --userconfig \"testuser\""
    ,"--setalloweddays"    : "this sets allowed days for the user, example:\n    timekpra --setalloweddays \"testuser\" \"1,2,3,4,5\""
    ,"--setallowedhours"   : "this sets allowed hours per specified day or ALL for every day, example:\n    timekpra --setallowedhours \"testuser\" \"ALL\" \"7,8,9,10,11[00-30],17,18,19,20[00-45]\""
    ,"--settimelimits"     : "this sets time limits per all allowed days, example:\n    timekpra --settimelimits \"testuser\" \"7200,7200,7200,7200,10800\""
    ,"--settimelimitweek"  : "this sets time limits per week, example:\n    timekpra --settimelimitweek \"testuser\" \"50000\""
    ,"--settimelimitmonth" : "this sets time limits per month, example:\n    timekpra --settimelimitmonth \"testuser\" \"200000\""
    ,"--settrackinactive"  : "this sets whether to track inactive user sessions, example:\n    timekpra --settrackinactive \"testuser\" \"false\""
    ,"--settimeleft"       : "this sets time left for the user at current moment, example (add one hour):\n    timekpra --settimeleft \"testuser\" \"+\" 3600"
}


def getNotificationPrioriy(pPriority):
    """Get the proper notification level"""
    # if we have it, just return it, else fallback to logo
    if pPriority in TK_PRIO_CONF:
        result = pPriority
    else:
        result = "logo"

    # return
    return result


# this defines messages for use in notifications
TK_MSG_TIMEUNLIMITED = "TIME_UNLIMITED"
TK_MSG_TIMELEFT = "TIME_LEFT"
TK_MSG_TIMECRITICAL = "TIME_CRITICAL"
TK_MSG_TIMELEFTCHANGED = "TIME_LIMIT_CHANGED"
TK_MSG_TIMECONFIGCHANGED = "TIME_CONFIG_CHANGED"
TK_MSG_REMOTE_COMMUNICATION_ERROR = "TIMEKPR_REMOTE_COMMUNICATION_ERROR"
TK_MSG_REMOTE_INVOCATION_ERROR = "TIMEKPR_REMOTE_INVOCATION_ERROR"

# ## actual system ##
TK_LOG_FILE = "timekpr.log"
# main config file
TK_MAIN_CONFIG_DIR = "/etc/timekpr"
# runtime directory for timekpr user configuration files
TK_CONFIG_DIR = "/var/lib/timekpr/config"
# runtime directory for timekpr time control files
TK_WORK_DIR = "/var/lib/timekpr/work"
# directory for shared files (images, gui definitions, etc.)
TK_SHARED_DIR = "/usr/share/timekpr"
# directory for log files
TK_LOGFILE_DIR = "/var/log"

# ## development ##
# main config file
TK_MAIN_CONFIG_DIR_DEV = "../resource/server"
# runtime directory for timekpr user configuration files
TK_CONFIG_DIR_DEV = "../../runtime.tmp"
# runtime directory for timekpr time control files
TK_WORK_DIR_DEV = "../../runtime.tmp"
# directory for shared files (images, gui definitions, etc.)
TK_SHARED_DIR_DEV = "../resource"
# directory for log files
TK_LOGFILE_DIR_DEV = "../../runtime.tmp"
