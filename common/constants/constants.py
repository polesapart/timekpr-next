"""
Created on Aug 28, 2018

@author: mjasnik
"""

# timekpr imports
from timekpr.common.constants import messages as msg

# imports
import dbus
import locale
import gettext
from datetime import datetime

# ## constants ##
# version (in case config is corrupt or smth like that)
TK_VERSION = "0.5.8"
TK_DEV_ACTIVE = False  # change this accordingly when running in DEV or PROD
TK_DEV_BUS = "ses"  # this sets up which bus to use for development (sys or ses)
TK_DEV_SUPPORT_PAGE = "https://tinyurl.com/yc9x85v2"

# formats
TK_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TK_LOG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
TK_DATETIME_START = datetime(2018, 1, 1)

# logging levels
TK_LOG_LEVEL_NONE = 0
TK_LOG_LEVEL_INFO = 1
TK_LOG_LEVEL_DEBUG = 2
TK_LOG_LEVEL_EXTRA_DEBUG = 3
# logging properties
TK_LOG_L = "lvl"
TK_LOG_D = "dir"
TK_LOG_W = "who"
TK_LOG_U = "user"
TK_LOG_TEMP_DIR = "/tmp"
TK_LOG_PID_EXT = "pid"
# logging clients
TK_LOG_OWNER_SRV = 0
TK_LOG_OWNER_CLIENT = 1
TK_LOG_OWNER_ADMIN = 2
TK_LOG_OWNER_ADMIN_SU = 3
# default event count for log file flush
TK_LOG_AUTO_FLUSH_EVT_CNT = 42

# client config and default values
TK_CL_NOTIF_MAX = 60
TK_CL_NOTIF_TMO = 3
TK_CL_NOTIF_CRIT_TMO = 10
TK_CL_NOTIF_SND_TYPE="sound-name"  # can be sound-name or sound-file
TK_CL_NOTIF_SND_FILE_WARN = "/usr/share/sounds/freedesktop/stereo/dialog-information.oga"
TK_CL_NOTIF_SND_FILE_CRITICAL = "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
TK_CL_NOTIF_SND_NAME_WARNING = "bell-window-system"
TK_CL_NOTIF_SND_NAME_IMPORTANT = "dialog-warning"
TK_CL_INF_FULL = "F"
TK_CL_INF_SAVED = "S"
TK_CL_INF_RT = "R"

# ## files and locations ##
# users and login configuration
TK_USERS_FILE = "/etc/passwd"
TK_USER_LIMITS_FILE = [ "/etc/login.defs", "/usr/etc/login.defs" ]
# backup extension
TK_BACK_EXT = ".prev"
# log files
TK_LOG_USER = "<USER>"
TK_LOG_FILE = "timekpr.log"
TK_LOG_FILE_CLIENT = "timekprc.<USER>.log"
TK_LOG_FILE_ADMIN = "timekpra.<USER>.log"
TK_LOG_FILE_ADMIN_SU = "timekpra.su.log"
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
# localization
TK_LOCALIZATION_DIR = "/usr/share/locale"

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
# localization
TK_LOCALIZATION_DIR_DEV = "../resource/locale"

# retry cnt for various actions
TK_MAX_RETRIES = 5
# max symbols to search for pattern in cmdline for PlayTime
TK_MAX_CMD_SRCH = 512

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

# seat / user / session / screensaver
TK_DBUS_SEAT_OBJECT = "org.freedesktop.login1.Seat"
TK_DBUS_USER_OBJECT = "org.freedesktop.login1.User"
TK_DBUS_SESSION_OBJECT = "org.freedesktop.login1.Session"

# path / objects / interfaces
TK_DBUS_BUS_NAME = "com.timekpr.server"
TK_DBUS_SERVER_PATH = "/com/timekpr/server"
TK_DBUS_ADMIN_INTERFACE = "com.timekpr.server.admin"
TK_DBUS_USER_NOTIF_PATH_PREFIX = "/com/timekpr/server/user/"
TK_DBUS_USER_NOTIF_INTERFACE = "com.timekpr.server.user.notifications"
TK_DBUS_USER_LIMITS_INTERFACE = "com.timekpr.server.user.limits"
TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE = "com.timekpr.server.user.sessionattributes"
TK_DBUS_USER_ADMIN_INTERFACE = "com.timekpr.server.user.admin"

# actual user session validation and control
TK_CTRL_SCR_N = "scrs"
TK_CTRL_SCR_K = "scrs:key"
TK_CTRL_SCR_R = "scrs:retr"

# WORKAROUNDS section for use in Gnome and similar (almost everyone makes their own screensaver dbus interface these days, KDE (of the biggest players) is not)
TK_SCR_XDGCD_OVERRIDE = [
    ["unity", "gnome"],
    ["kde", "freedesktop"]]

# DBUS performance measurement
TK_DBUS_ANSWER_TIME = 3

# user and their restriction constants
TK_CTRL_UID = "UID"      # user id
TK_CTRL_UNAME = "UNAME"  # user name
TK_CTRL_UPATH = "UPATH"  # user path on dbus
TK_CTRL_FCNTD = "FCNTD"  # final countdown
TK_CTRL_RESTY = "RESTY"  # restricton type: lock, suspend, suspendwake, terminate, kill, shutdown
TK_CTRL_RTDEL = "RTDEL"  # retry delay before next attempt to enforce restrictions
TK_CTRL_RTDEA = "RTDEA"  # retry delay (additional delay for lock in case of suspend)
TK_CTRL_USACT = "USACT"  # whether user is active
TK_CTRL_USLCK = "USLCK"  # whether user screen is locked
TK_CTRL_USWKU = "USWKU"  # wake up time for computer if one is specified
TK_CTRL_LCDEL = 1        # lock cycle delay (how many ticks happen before repetitive lock)
TK_CTRL_SCDEL = 20       # suspend cycle delay (how many ticks happen before repetitive suspend)
# restriction / lockout types
TK_CTRL_RES_L = "lock"
TK_CTRL_RES_S = "suspend"
TK_CTRL_RES_W = "suspendwake"
TK_CTRL_RES_T = "terminate"
TK_CTRL_RES_K = "kill"
TK_CTRL_RES_D = "shutdown"
# wake up RTC file
TK_CTRL_WKUPF = "/sys/class/rtc/rtc0/wakealarm"

# session properties
TK_CTRL_DBUS_SESS_OBJ = "SESSION_OBJECT"
TK_CTRL_DBUS_SESS_IF = "SESSION_INTERFACE"
TK_CTRL_DBUS_SESS_PROP_IF = "SESSION_PROPERTIES_INTERFACE"
TK_CTRL_DBUS_SESS_PROP = "SESSION_STATIC_PROPERTIES"

# limit configuration
TK_CTRL_NDAY = "NEXTDAY"     # next day idx
TK_CTRL_PDAY = "PREVDAY"     # previous day idx
TK_CTRL_LIMITD = "LIMITD"    # limit idx / today
TK_CTRL_LEFTD = "LEFTD"      # time left today idx
TK_CTRL_LEFT = "LEFT"        # time left idx (continously)
TK_CTRL_LEFTW = "LEFTW"      # time left for week
TK_CTRL_LEFTM = "LEFTM"      # time left for month
TK_CTRL_LCHECK = "LCHK"      # last checked idx
TK_CTRL_LSAVE = "LSAVE"      # last saved idx
TK_CTRL_LMOD = "LMOD"        # file modification idx (control)
TK_CTRL_LCMOD = "LMCOD"      # file modification idx (config)
TK_CTRL_LIMITW = "LIMITW"    # left per week idx
TK_CTRL_LIMITM = "LIMITM"    # left per month idx
TK_CTRL_ACT = "ACTIVE"       # is hour enabled
TK_CTRL_UACC = "UACC"        # is hour unaccounted
TK_CTRL_SLEEP = "SLEEP"      # time spent in "inactive"
TK_CTRL_SPENT = "SPENT"      # time spent in this session
TK_CTRL_SPENTBD = "SPENTBD"  # time balance spent in this day
TK_CTRL_SPENTH = "SPENTH"    # time spent in this hour
TK_CTRL_SPENTD = "SPENTD"    # time spent in this day
TK_CTRL_SPENTW = "SPENTW"    # time spent for week
TK_CTRL_SPENTM = "SPENTM"    # time spent for month
TK_CTRL_SMIN = "STARTMIN"    # start minute in this hour
TK_CTRL_EMIN = "ENDMIN"      # end minute in this hour
TK_CTRL_INT = "INTERVALS"    # intervals of time available to user
TK_CTRL_TRACK = "TRACKI"     # whether to track inactive sessions
TK_CTRL_HIDEI = "HIDEI"      # whether to hide timekpr icon
TK_CTRL_TNL = "TNL"          # time not limited
TK_CTRL_PTTLE = "PTTLE"      # PlayTime enabled
TK_CTRL_PTCNT = "PTCNT"      # PlayTime counters
TK_CTRL_PTSPD = "PTSPD"      # time spent for PlayTime
TK_CTRL_PTLPD = "PTLPD"      # time left for PlayTime
TK_CTRL_PTTLO = "PTTLO"      # PlayTime limit override
TK_CTRL_PTAUH = "PTAUH"      # PlayTime allowed during unaccounted intervals
TK_CTRL_PTLMT = "PTLMT"      # time limits for each day for PlayTime
TK_CTRL_PTLST = "PTLST"      # process list for PlayTime
TK_CTRL_PTLSTC = "PTLSTC"    # process list count for PlayTime

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
# exclude users (test user for timekpr and all known login managers)
TK_USERS_TEST = "testtimekpr"
TK_USERS_LOGIN_MANAGERS = "gdm;gdm3;kdm;lightdm;mdm;lxdm;xdm;sddm;cdm"
TK_USERS_EXCL = "%s;%s" % (TK_USERS_TEST, TK_USERS_LOGIN_MANAGERS)

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
# default value for limit per every weekday
TK_LIMITS_PER_WEEKDAYS = "%s;%s;%s;%s;%s;%s;%s" % (TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY, TK_LIMIT_PER_DAY)
# default value for nitification levels
TK_NOTIFICATION_LEVELS = "3600[3];1800[2];600[1];300[0]"
TK_PT_NOTIFICATION_LEVELS = "180[1]"

# ## user PlayTime defaults ##
# enabled
TK_PLAYTIME_ENABLED = False
# default value for allowed week days
TK_PLAYTIME_ALLOWED_WEEKDAYS = "1;2;3;4;5;6;7"
# how much PlayTime is allowed per allowed days
TK_PLAYTIME_LIMITS_PER_WEEKDAYS = "0;0;0;0;0;0;0"

# ## default values for control ##
# time control
# in-memory poll time
TK_POLLTIME = 3
# flush interval
TK_SAVE_INTERVAL = 30
# time left for putting user on kill list
TK_TERMINATION_TIME = 15
# time left for final warning time
TK_FINAL_COUNTDOWN_TIME = 10
# time left for final warning time
TK_FINAL_NOTIFICATION_TIME = 60
# default value for tracking inactive sessions
TK_TRACK_INACTIVE = False
# default value for tracking inactive sessions
TK_HIDE_TRAY_ICON = False

# ## files ##
# config
TK_MAIN_CONFIG_FILE = "timekpr.conf"
TK_USER_CONFIG_FILE = "timekpr.%s.conf"
TK_UNAME_SRCH_LN_LMT = 10  # this defines line count for verifying username in first n lines

# ## timekpr notification config ##
# priorites
TK_PRIO_LOW = "low"
TK_PRIO_NORMAL = "normal"
TK_PRIO_WARNING = "warning"
TK_PRIO_IMPORTANT = "important"
TK_PRIO_CRITICAL = "critical"
TK_PRIO_IMPORTANT_INFO = "important_info"
TK_PRIO_UACC = "unaccounted"
# notification levels mapping from / to codes
TK_PRIO_LVL_MAP = {"4": TK_PRIO_UACC, "3": TK_PRIO_LOW, "2": TK_PRIO_WARNING, "1": TK_PRIO_IMPORTANT, "0": TK_PRIO_CRITICAL,
    TK_PRIO_UACC: "4", TK_PRIO_LOW: "3", TK_PRIO_WARNING: "2", TK_PRIO_IMPORTANT: "1", TK_PRIO_CRITICAL: "0"}

# config
TK_PRIO_CONF = {}
TK_PRIO_CONF["logo"] = {TK_ICON_STAT: "timekpr-logo.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF["client-logo"] = {TK_ICON_STAT: "timekpr-client-logo.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF["unlimited"] = {TK_ICON_STAT: "timekpr-padlock-unlimited-green.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_LOW] = {TK_ICON_STAT: "timekpr-padlock-limited-green.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(0, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_NORMAL] = {TK_ICON_STAT: "timekpr-padlock-limited-green.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_WARNING] = {TK_ICON_STAT: "timekpr-padlock-limited-yellow.svg", TK_ICON_NOTIF: "dialog-warning", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_IMPORTANT] = {TK_ICON_STAT: "timekpr-padlock-limited-red.svg", TK_ICON_NOTIF: "dialog-warning", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_CRITICAL] = {TK_ICON_STAT: "timekpr-padlock-limited-red.svg", TK_ICON_NOTIF: "dialog-error", TK_DBUS_PRIO: dbus.Byte(2, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_IMPORTANT_INFO] = {TK_ICON_STAT: "timekpr-padlock-limited-yellow.svg", TK_ICON_NOTIF: "dialog-information", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}
TK_PRIO_CONF[TK_PRIO_UACC] = {TK_ICON_STAT: "timekpr-padlock-limited-uacc.svg", TK_ICON_NOTIF: "dialog-warning", TK_DBUS_PRIO: dbus.Byte(1, variant_level=1)}

# ## timekpr notification config ##
# init python gettext
gettext.bindtextdomain("timekpr", TK_LOCALIZATION_DIR if not TK_DEV_ACTIVE else TK_LOCALIZATION_DIR_DEV)
gettext.textdomain("timekpr")
# init actual libc gettext
locale.bindtextdomain("timekpr", TK_LOCALIZATION_DIR if not TK_DEV_ACTIVE else TK_LOCALIZATION_DIR_DEV)
locale.textdomain("timekpr")

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
    "--help"                                : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_HELP"), "timekpra --help"),
    "--userlist"                            : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_USERLIST"), "timekpra --userlist"),
    "--userinfo"                            : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_USERCONFIG"), "timekpra --userinfo 'testuser'"),
    "--userinfort"                          : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_USERCONFIGRT"), "timekpra --userinfort 'testuser'"),
    "--setalloweddays"                      : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETALLOWEDDAYS"), "timekpra --setalloweddays 'testuser' '1;2;3;4;5'"),
    "--setallowedhours"                     : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETALLOWEDHOURS"), "timekpra --setallowedhours 'testuser' 'ALL' '7;8;9;10;11[00-30];!14;!15;17;18;19;20[00-45]'"),
    "--settimelimits"                       : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETTIMELIMITS"), "timekpra --settimelimits 'testuser' '7200;7200;7200;7200;10800'"),
    "--settimelimitweek"                    : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETTIMELIMITWK"), "timekpra --settimelimitweek 'testuser' '50000'"),
    "--settimelimitmonth"                   : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETTIMELIMITMON"), "timekpra --settimelimitmonth 'testuser' '200000'"),
    "--settrackinactive"                    : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETTRACKINACTIVE"), "timekpra --settrackinactive 'testuser' 'false'"),
    "--sethidetrayicon"                     : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETHIDETRAYICON"), "timekpra --sethidetrayicon 'testuser' 'false'"),
    "--setlockouttype"                      : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETLOCKOUTTYPE"), "timekpra --setlockouttype 'testuser' 'terminate'\n    timekpra --setlockouttype 'testuser' 'suspendwake;7;18'"),
    "--settimeleft"                         : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETTIMELEFT"), "timekpra --settimeleft 'testuser' '+' 3600"),
    "--setplaytimeenabled"                  : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMEENABLED"), "timekpra --setplaytimeenabled 'testuser' 'false'"),
    "--setplaytimelimitoverride"            : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMELIMITOVERRIDE"), "timekpra --setplaytimelimitoverride 'testuser' 'false'"),
    "--setplaytimeunaccountedintervalsflag" : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMEUNACCOUNTEDINTARVALSFLAG"), "timekpra --setplaytimeunaccountedintervalsflag 'testuser' 'false'"),
    "--setplaytimealloweddays"              : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMEALLOWEDDAYS"), "timekpra --setplaytimealloweddays 'testuser' '1;2;3;4;5'"),
    "--setplaytimelimits"                   : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMELIMITS"), "timekpra --setplaytimelimits 'testuser' '1800;1800;1800;1800;3600'"),
    "--setplaytimeactivities"               : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMEACTIVITIES"), "timekpra --setplaytimeactivities 'testuser' 'DOOMEternalx64vk.exe[Doom Eternal];csgo_linux[CS: GO];firefox[Firefox browser]'"),
    "--setplaytimeleft"                     : "%s:\n    %s" % (msg.getTranslation("TK_MSG_USER_ADMIN_CMD_SETPLAYTIMELEFT"), "timekpra --setplaytimeleft 'testuser' '+' 3600")
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
TK_MSG_CODE_TIMEUNLIMITED = "TIME_UNLIMITED"
TK_MSG_CODE_TIMELEFT = "TIME_LEFT"
TK_MSG_CODE_TIMECRITICAL = "TIME_CRITICAL"
TK_MSG_CODE_TIMELEFTCHANGED = "TIME_LIMIT_CHANGED"
TK_MSG_CODE_TIMECONFIGCHANGED = "TIME_CONFIG_CHANGED"
TK_MSG_CODE_REMOTE_COMMUNICATION_ERROR = "TIMEKPR_REMOTE_COMMUNICATION_ERROR"
TK_MSG_CODE_REMOTE_INVOCATION_ERROR = "TIMEKPR_REMOTE_INVOCATION_ERROR"
TK_MSG_CODE_ICON_INIT_ERROR = "TIMEKPR_ICON_INIT_ERROR"
TK_MSG_CODE_FEATURE_SCR_NOT_AVAILABLE_ERROR = "TIMEKPR_SCR_FEATURE_NOT_AVAILABLE_ERROR"
