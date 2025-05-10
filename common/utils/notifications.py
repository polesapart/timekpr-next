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

    def __init__(self, pBusName, pUserName, pTimekprConfig):
        """Initialize notification manager"""

        log.log(cons.TK_LOG_LEVEL_INFO, "start init notifications")

        # config
        self._timekprConfig = pTimekprConfig

        # last notification
        self._userName = pUserName
        self._userNameDBUS = self._userName.replace(".", "").replace("-", "")
        self._lastNotified = datetime.now().replace(microsecond=0)
        self._notificationLvl = -1
        self._prevNotificationLvl = -1

        # ## define notifications levels
        # notifications are calculated as more than specified limit in ascending order, e.g. if there is 2400 seconds
        # left, it means that (3600 > 2400 > 1800) second level is chosen
        self._notificationLimits = (
            #  ## historical config, just for reference ##
            #  {cons.TK_NOTIF_LEFT: 3600*2, cons.TK_NOTIF_INTERVAL: 3600*2, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_LOW}
            # ,{cons.TK_NOTIF_LEFT: 3600, cons.TK_NOTIF_INTERVAL: 3600, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_LOW}
            # ,{cons.TK_NOTIF_LEFT: 1800, cons.TK_NOTIF_INTERVAL: 1800, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_NORMAL}
            # ,{cons.TK_NOTIF_LEFT: 300, cons.TK_NOTIF_INTERVAL: 600, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_WARNING}
            # ,{cons.TK_NOTIF_LEFT: 60, cons.TK_NOTIF_INTERVAL: 120, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_IMPORTANT}
            # ,{cons.TK_NOTIF_LEFT: 0, cons.TK_NOTIF_INTERVAL:60, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL}
            # ,{cons.TK_NOTIF_LEFT: -cons.TK_LIMIT_PER_DAY*31, cons.TK_NOTIF_INTERVAL: 10, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL}

            # ## since notifications are client responsibility, but we still need to send them at some point, so this is a placeholder config ##
            # ## notification levels should not matter anymore, when message arrives to client, it will calc prio depending on it's config ##
            {cons.TK_NOTIF_LEFT: self._timekprConfig.getTimekprFinalNotificationTime, cons.TK_NOTIF_INTERVAL: self._getTwoDaysTime, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_LOW},
            {cons.TK_NOTIF_LEFT: self._getZeroDaysTime, cons.TK_NOTIF_INTERVAL: self._timekprConfig.getTimekprFinalNotificationTime, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL},
            {cons.TK_NOTIF_LEFT: self._getLongestTimeNeg, cons.TK_NOTIF_INTERVAL: self._getLongestTime, cons.TK_NOTIF_URGENCY: cons.TK_PRIO_CRITICAL}
        )

        # init DBUS
        super().__init__(pBusName, cons.TK_DBUS_USER_NOTIF_PATH_PREFIX + self._userNameDBUS)

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init notifications")

    # --------------- helper methods --------------- #

    # a time ceiling of time for comparison
    def _getLongestTime(self): return cons.TK_LIMIT_PER_DAY * 31
    # a time floor of time for comparison
    def _getLongestTimeNeg(self): return -self._getLongestTime
    # max time user could have
    def _getTwoDaysTime(self): return cons.TK_LIMIT_PER_DAY * 2
    # 0 time
    def _getZeroDaysTime(self): return 0

    # --------------- worker methods --------------- #

    def deInitUser(self):
        """Leave the connection"""
        # un-init DBUS
        super().remove_from_connection()

    def processTimeLeft(self, pForce, pTimeValues):
        """Process notifications and send signals if needed"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start processTimeLeft")

        # save old level
        self._prevNotificationLvl = self._notificationLvl

        # defaults
        newNotificatonLvl = -1
        effectiveDatetime = datetime.now().replace(microsecond=0)

        # find current limit
        for i in self._notificationLimits:
            # set up new level
            newNotificatonLvl += 1
            # check
            if pTimeValues[cons.TK_CTRL_LEFT] >= i[cons.TK_NOTIF_LEFT]():
                # set up new level
                self._notificationLvl = newNotificatonLvl
                # we found what we needed
                break

        # timeleft
        timeLeft = dbus.Dictionary({}, signature="si")
        timeLeft[cons.TK_CTRL_LEFTD] = int(pTimeValues[cons.TK_CTRL_LEFTD])
        timeLeft[cons.TK_CTRL_LEFT] = int(pTimeValues[cons.TK_CTRL_LEFT])
        timeLeft[cons.TK_CTRL_SPENT] = int(pTimeValues[cons.TK_CTRL_SPENT])
        timeLeft[cons.TK_CTRL_SPENTW] = int(pTimeValues[cons.TK_CTRL_SPENTW])
        timeLeft[cons.TK_CTRL_SPENTM] = int(pTimeValues[cons.TK_CTRL_SPENTM])
        timeLeft[cons.TK_CTRL_SLEEP] = int(pTimeValues[cons.TK_CTRL_SLEEP])
        timeLeft[cons.TK_CTRL_TRACK] = (1 if pTimeValues[cons.TK_CTRL_TRACK] else 0)
        timeLeft[cons.TK_CTRL_HIDEI] = (1 if pTimeValues[cons.TK_CTRL_HIDEI] else 0)
        timeLeft[cons.TK_CTRL_TNL] = pTimeValues[cons.TK_CTRL_TNL]
        # include PlayTime (if enabled, check is done for couple of mandatory values)
        if cons.TK_CTRL_PTTLO in pTimeValues and cons.TK_CTRL_PTSPD in pTimeValues:
            timeLeft[cons.TK_CTRL_PTTLO] = (1 if pTimeValues[cons.TK_CTRL_PTTLO] else 0)
            timeLeft[cons.TK_CTRL_PTAUH] = (1 if pTimeValues[cons.TK_CTRL_PTAUH] else 0)
            timeLeft[cons.TK_CTRL_PTSPD] = int(pTimeValues[cons.TK_CTRL_PTSPD])
            timeLeft[cons.TK_CTRL_PTLPD] = int(pTimeValues[cons.TK_CTRL_PTLPD])
            timeLeft[cons.TK_CTRL_PTLSTC] = int(pTimeValues[cons.TK_CTRL_PTLSTC])

        # save calculated urgency (calculated may get overridden by uacc)
        notifUrgency = cons.TK_PRIO_UACC if pTimeValues[cons.TK_CTRL_UACC] else self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_URGENCY]

        # inform clients about time left in any case
        self.timeLeft(notifUrgency, timeLeft)

        # if notification levels changed (and it was not the first iteration)
        if (pForce) or (self._notificationLvl != self._prevNotificationLvl) or (abs((effectiveDatetime - self._lastNotified).total_seconds()) >= self._notificationLimits[self._notificationLvl][cons.TK_NOTIF_INTERVAL]() and not pTimeValues[cons.TK_CTRL_UACC]):
            # set up last notified
            self._lastNotified = effectiveDatetime

            # if time left is whole day, we have no limit (as an additonal limit is the hours, so check if accounting is actually correct)
            if timeLeft[cons.TK_CTRL_TNL] > 0:
                # we send no limit just once
                if self._prevNotificationLvl < 0 or pForce:
                    # no limit
                    self.timeNoLimitNotification(cons.TK_PRIO_LOW)
            else:
                # limit
                self.timeLeftNotification(notifUrgency, max(pTimeValues[cons.TK_CTRL_LEFT], 0), max(pTimeValues[cons.TK_CTRL_LEFTD], 0), pTimeValues[cons.TK_CTRL_LIMITD])

        log.log(cons.TK_LOG_LEVEL_DEBUG, "time left, tlrow: %i, tleftd: %i, tlimd: %i, notification lvl: %s, priority: %s, force: %s" % (pTimeValues[cons.TK_CTRL_LEFT], pTimeValues[cons.TK_CTRL_LEFTD], pTimeValues[cons.TK_CTRL_LIMITD], self._notificationLvl, notifUrgency, str(pForce)))
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish processTimeLeft")

    def processTimeLimits(self, pTimeLimits):
        """Enable sending out the limits config"""
        # dbus dict for holding days
        timeLimits = dbus.Dictionary(signature="sv")

        # convert this all to dbus
        for rKey, rValue in pTimeLimits.items():
            # weekly & monthly limits are set differently
            if rKey in (cons.TK_CTRL_LIMITW, cons.TK_CTRL_LIMITM):
                # this is to comply with standard limits structure
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][rKey] = dbus.Int32(rValue)
            # PlayTime flags
            elif rKey in (cons.TK_CTRL_PTTLO, cons.TK_CTRL_PTAUH, cons.TK_CTRL_PTTLE):
                # this is to comply with standard limits structure
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][rKey] = dbus.Int32(rValue)
            # PlayTime lists
            elif rKey in (cons.TK_CTRL_PTLMT, cons.TK_CTRL_PTLST):
                # dbus dict for holding days, limits and activities
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][rKey] = dbus.Array(signature="av")
                # fill in limits or activities (both have 2 node arrays)
                for rSubValue in rValue:
                    timeLimits[rKey][rKey].append(dbus.Array([rSubValue[0], rSubValue[1]], signature=("i" if rKey == cons.TK_CTRL_PTLMT else "s")))
            else:
                # dbus dict for holding limits and intervals
                timeLimits[rKey] = dbus.Dictionary(signature="sv")
                timeLimits[rKey][cons.TK_CTRL_LIMITD] = rValue[cons.TK_CTRL_LIMITD]
                # dbus list for holding intervals
                timeLimits[rKey][cons.TK_CTRL_INT] = dbus.Array(signature="av")
                # set up dbus dict
                for rLimit in rValue[cons.TK_CTRL_INT]:
                    # add intervals
                    timeLimits[rKey][cons.TK_CTRL_INT].append(dbus.Array([rLimit[0], rLimit[1], rLimit[2]], signature="i"))

        if log.isDebugEnabled(cons.TK_LOG_LEVEL_EXTRA_DEBUG):
            log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "TLDB: %s" % (str(timeLimits)))

        # process
        self.timeLimits(cons.TK_PRIO_LOW, timeLimits)

    def processEmergencyNotification(self, pFinalNotificationType, pCountdown):
        """Emergency notifcation call wrapper"""
        # forward to dbus
        self.timeCriticalNotification(pFinalNotificationType, cons.TK_PRIO_CRITICAL, pCountdown)

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

    @dbus.service.signal(cons.TK_DBUS_USER_LIMITS_INTERFACE, signature="sa{si}")
    def timeLeft(self, pPriority, pTimeLeft):
        """Send out signal"""
        # this just passes time back
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_LIMITS_INTERFACE, signature="sa{sa{sv}}")
    def timeLimits(self, pPriority, pTimeLimits):
        """Send out signal"""
        # this just passes time back
        pass

    # --------------- DBUS / communication methods (notifications) --------------- #

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="siii")
    def timeLeftNotification(self, pPriority, pTimeLeftTotal, pTimeLeftToday, pTimeLimitToday):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tln: %i" % (pTimeLeftTotal))
        # You have %s to use continously, including %s ouf of %s today
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="ssi")
    def timeCriticalNotification(self, pFinalNotificationType, pPriority, pSecondsLeft):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending tcn: %s, %i" % (pFinalNotificationType, pSecondsLeft))
        # Your time is up, you will be forcibly logged / locked / suspended / shutdown out in %i seconds!
        pass

    @dbus.service.signal(cons.TK_DBUS_USER_NOTIF_INTERFACE, signature="s")
    def timeNoLimitNotification(self, pPriority):
        """Send out signal"""
        log.log(cons.TK_LOG_LEVEL_DEBUG, "sending ntln")
        # Congratulations, your time is not limited today
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
