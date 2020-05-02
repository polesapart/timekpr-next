"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import dbus.service
from datetime import datetime

# timekpr imports
from timekpr.common.log import log
from timekpr.common.constants import constants as cons


class timekprNotificationManager(dbus.service.Object):
    """Notification manager"""

    # --------------- initialization / control methods --------------- #

    def __init__(self, pLog, pBusName, pUserName):
        """Initialize notification manager"""
        # init logging firstly
        log.setLogging(pLog)

        log.log(cons.TK_LOG_LEVEL_INFO, "start init notifications")

        # last notification
        self._userName = pUserName
        self._userNameDBUS = self._userName.replace(".", "").replace("-", "")
        self._lastNotified = datetime.now().replace(microsecond=0)
        self._notificationLvl = -1
        self._prevNotificationLvl = -1

        # define notifications levels
        self._notificationLimits = (
            {cons.TK_NOTIF_LEFT: 3600, cons.TK_NOTIF_INTERVAL: 3600, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_LOW}
            ,{cons.TK_NOTIF_LEFT: 1800, cons.TK_NOTIF_INTERVAL: 900, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_NORMAL}
            ,{cons.TK_NOTIF_LEFT: 900, cons.TK_NOTIF_INTERVAL: 300, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_WARNING}
            ,{cons.TK_NOTIF_LEFT: 300, cons.TK_NOTIF_INTERVAL: 180, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_WARNING}
            ,{cons.TK_NOTIF_LEFT: 120, cons.TK_NOTIF_INTERVAL: 120, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_IMPORTANT}
            ,{cons.TK_NOTIF_LEFT: 0, cons.TK_NOTIF_INTERVAL:60, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL}
            ,{cons.TK_NOTIF_LEFT: -cons.TK_LIMIT_PER_DAY, cons.TK_NOTIF_INTERVAL: 10, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL}
        )

        # init DBUS
        super().__init__(pBusName, cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init notifications")

    # --------------- worker methods --------------- #

    def deInitUser(self):
        """Leave the connection"""
        # un-init DBUS
        super().remove_from_connection()

    def processTimeLeft(self, pForce, pTimeSpent, pTimeSpentWeek, pTimeSpentMonth, pTimeInactive, pTimeLeftToday, pTimeLeftTotal, pTimeLimitToday, pTrackInactive):
        """Process notifications and send signals if needed"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "start processTimeLeft")

        # save old level
        self._prevNotificationLvl = self._notificationLvl

        # defaults
        newNotificatonLvl = -1
        effectiveDatetime = datetime.now().replace(microsecond=0)
        secondsFromDayStart = (effectiveDatetime - effectiveDatetime.replace(hour=0, minute=0, second=0)).total_seconds()

        # find current limit
        for i in self._notificationLimits:
            # set up new level
            newNotificatonLvl += 1

            # check
            if pTimeLeftTotal >= i[cons.TK_NOTIF_LEFT]:
                # set up new level
                self._notificationLvl = newNotificatonLvl

                # we found what we needed
                break

        # timeleft
        timeLeft = dbus.Dictionary({}, signature="si")
        timeLeft[cons.TK_CTRL_LEFTD] = int(pTimeLeftToday)
        timeLeft[cons.TK_CTRL_LEFT] = int(pTimeLeftTotal)
        timeLeft[cons.TK_CTRL_SPENT] = int(pTimeSpent)
        timeLeft[cons.TK_CTRL_SPENTW] = int(pTimeSpentWeek)
        timeLeft[cons.TK_CTRL_SPENTM] = int(pTimeSpentMonth)
        timeLeft[cons.TK_CTRL_SLEEP] = int(pTimeInactive)
        timeLeft[cons.TK_CTRL_TRACK] = (1 if pTrackInactive else 0)

        # inform clients about time left in any case
        self.timeLeft(self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_URGENCY], timeLeft)

        # if notification levels changed (and it was not the first iteration)
        if (pForce) or (self._notificationLvl != self._prevNotificationLvl) or ((effectiveDatetime - self._lastNotified).total_seconds() >= self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_INTERVAL]):
            # set up last notified
            self._lastNotified = effectiveDatetime

            # if time left is whole day, we have no limit (as an additonal limit is the hours, so check if accounting is actually correct)
            if pTimeLimitToday >= cons.TK_LIMIT_PER_DAY and int(pTimeLeftToday) + secondsFromDayStart + 10 >= cons.TK_LIMIT_PER_DAY and int(pTimeLeftTotal) + secondsFromDayStart + 10 >= cons.TK_LIMIT_PER_DAY:
                # we send no limit just once
                if self._prevNotificationLvl < 0 or pForce:
                    # no limit
                    self.timeNoLimitNotification(self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_URGENCY])
            else:
                # limit
                self.timeLeftNotification(self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_URGENCY], max(pTimeLeftTotal, 0), max(pTimeLeftToday, 0), pTimeLimitToday)

        log.log(cons.TK_LOG_LEVEL_DEBUG, "time left: %i; %i; %i, notification lvl: %s, priority: %s, force: %s" % (pTimeLeftTotal, pTimeLeftToday, pTimeLimitToday, self._notificationLvl, self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_URGENCY], str(pForce)))
        log.log(cons.TK_LOG_LEVEL_DEBUG, "finish processTimeLeft")

    def processTimeLimits(self, pTimeLimits):
        """Enable sending out the limits config"""
        # dbus dict for holding days
        timeLimits = dbus.Dictionary(signature="sv")

        # convert this all to dbus
        for rKey, rValue in pTimeLimits.items():
            # weekly & monthly limits are set differently
            if rKey in [cons.TK_CTRL_LIMITW, cons.TK_CTRL_LIMITM]:
                # this is to comply with standard limits structure
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][rKey] = dbus.Int32(rValue)
            else:
                # dbus dict for holding limits and intervals
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][cons.TK_CTRL_LIMITD] = rValue[cons.TK_CTRL_LIMITD]
                # dbus list for holding intervals
                timeLimits[rKey][cons.TK_CTRL_INT] = dbus.Array(signature="av")
                # set up dbus dict
                for rLimit in rValue[cons.TK_CTRL_INT]:
                    # add intervals
                    timeLimits[rKey][cons.TK_CTRL_INT].append(dbus.Array([rLimit[0], rLimit[1]], signature="i"))

        if log.isDebug():
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "TLDB: %s" % (str(timeLimits)))

        # process
        self.timeLimits(cons.TK_PRIO_LOW, timeLimits)

    def processEmergencyNotification(self, pCountdown):
        """Emergency notifcation call wrapper"""
        # forward to dbus
        self.timeCriticalNotification(cons.TK_PRIO_CRITICAL, pCountdown)

    def procesSessionAttributes(self, pWhat, pKey):
        """Session attribute verification wrapper"""
        # forward to dbus
        self.sessionAttributeVerification(pWhat, pKey)

    # --------------- DBUS / communication methods (verification, user session states) --------------- #

    @dbus.service.signal(cons.TK_DBUS_USER_SESSION_ATTRIBUTE_INTERFACE, signature="ss")
    def sessionAttributeVerification(self, pWhat, pKey):
        """Send out signal"""
        # this just passes time back
        pass

    # --------------- DBUS / communication methods (limits, config) --------------- #

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="sa{si}")
    def timeLeft(self, pPriority, pTimeLeft):
        """Send out signal"""
        # this just passes time back
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="sa{sa{sv}}")
    def timeLimits(self, pPriority, pTimeLimits):
        """Send out signal"""
        # this just passes time back
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="siii")
    def timeLeftNotification(self, pPriority, pTimeLeftTotal, pTimeLeftToday, pTimeLimitToday):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tln: %i" % (pTimeLeftTotal))
        # You have %s to use continously, including %s ouf of %s today
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="si")
    def timeCriticalNotification(self, pPriority, pSecondsLeft):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tcn: %i" % (pSecondsLeft))
        # Your time is up, You will be forcibly logged out in %i seconds!
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="s")
    def timeNoLimitNotification(self, pPriority):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending ntln")
        # Congratulations, Your time is not limited today
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="s")
    def timeLeftChangedNotification(self, pPriority):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tlcn")
        # Limits have changed and applied
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="s")
    def timeConfigurationChangedNotification(self, pPriority):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tccn")
        # Configuration has changed, new limits may have been applied
        pass
