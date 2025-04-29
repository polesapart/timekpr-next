"""
Created on Aug 01, 2020

@author: mjasnik
"""

# imports
import os
import psutil
from gi.repository import GLib
from datetime import datetime
import re

# timekpr imports
from timekpr.common.log import log
from timekpr.common.constants import constants as cons
from timekpr.server.config import userhelper


class timekprPlayTimeConfig(object):
    """Contains all the data for PlayTime user"""

    # key constants
    _PIDS = "P"   # used to identify pids
    _USRS = "U"   # used to identify users (in master structure)
    _MPIDS = "M"  # used to identify processes that match patterns
    _FLTS = "F"   # used to identify filters for processes for particular user
    _UID = "u"    # used to identify user id (child struct)
    _EXE = "e"    # used to identify executable for process
    _CMD = "c"    # used to identify command line for process
    _TERM = "k"   # used to identify terminate attempts before killing
    _QCP = "Q"    # used to identify how many times we need to verify process has changed euid / cmdline (def: 2)
    _QCT = "q"    # used to identify time between the QC passes  (def: 5 iterations)
    _TIM = "t"    # used to identify last update date
    # value constants
    _QCP_V = 2
    _QCT_V = 5
    # file locations for inspecting process and its cmdline
    # status
    _STATUS = "/proc/%s/status"
    # exe
    _EXECUTABLE ="/proc/%s/exe"
    # cmdline
    _CMDLINE = "/proc/%s/cmdline"

    def __init__(self, pTimekprConfig):
        """Initialize all stuff for PlayTime"""

        log.log(cons.TK_LOG_LEVEL_INFO, "start init timekprUserPlayTime")

        # structure:
        #   P - process pids for all processes, every process has: u - user id, c - cmdline, t - adjustment time
        #   U - contains users, which in turn contains reference to P
        #   TIM - last update date for processes
        self._cachedPids = {self._PIDS: {}, self._USRS: {}, self._TIM: None}
        # global server config
        self._timekprConfig = pTimekprConfig

        log.log(cons.TK_LOG_LEVEL_INFO, "finish init timekprUserPlayTime")

    def _getMatchedProcessesByFilter(self, pUid, pFlts, pPids):
        """Method to validate whether cmdline matches the filter"""
        # def
        matchedPids = []
        # loop through user processes
        for rPid in pPids:
            # executable
            exe = self._cachedPids[self._PIDS][rPid][self._EXE]
            # command line
            cmdLine = self._cachedPids[self._PIDS][rPid][self._CMD]
            # try searching only if exe is specified
            if exe is not None:
                # match
                for rFlt in pFlts:
                    # pid matched
                    isMatched = rFlt.search(exe) is not None
                    isMatched = isMatched or (self._timekprConfig.getTimekprPlayTimeEnhancedActivityMonitorEnabled() and cmdLine is not None and rFlt.search(cmdLine) is not None)
                    # try to check if matches
                    if isMatched:
                        # match
                        matchedPids.append(rPid)
                        # log
                        log.log(cons.TK_LOG_LEVEL_DEBUG, "PT match, uid: %s, exe: %s, cmdl: %s" % (pUid, exe, "n/a" if cmdLine is None else cmdLine[:128]))
                        # first filter is enough
                        break
        # result
        return matchedPids

    def _initUserData(self, pUid):
        """Initialize user in cached structure"""
        # result
        self._cachedPids[self._USRS][pUid] = {self._PIDS: set(), self._MPIDS: set(), self._FLTS: {}}

    def _cachePlayTimeProcesses(self):
        """Refresh all processes for inspection"""
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "start cachePlayTimeProcesses")

        # ## the idea is that processes have to be refreshed regularly, that is:
        #      if users exist with active filters, then it's regular
        #      if they do not exist, we still need to refresh processes, just more seldom

        # def
        dt = datetime.now()
        # regular refreshes need to happen even noone is logged in (process pid reuse)
        if not ((abs((dt - self._cachedPids[self._TIM]).total_seconds()) if self._cachedPids[self._TIM] is not None else cons.TK_SAVE_INTERVAL) >= cons.TK_SAVE_INTERVAL):
            # def
            areFltsEnabled = False
            # if no users have set up their filters, we do NOT execute process list
            for rUser in self._cachedPids[self._USRS]:
                # check if there are filters
                if self._cachedPids[self._USRS][rUser][self._FLTS]:
                    # filters found
                    areFltsEnabled = True
                    # no need to search further
                    break
            # do not do anything if there are users and filters are not enabled
            if not areFltsEnabled:
                # do not do anything
                return

        # ## this is the fastest way I found how to list all processes ##
        # I tried with:
        #   subprocess + ps -ef (~ 2.2x slower)
        #                psutil (~ 10x  slower)
        #   even scandir is a tad slower than listdir (for our use case)

        # this method was built for support of filtering any processes
        # even by regexp, but as configuration by regexp is considered
        # not easy for regular user, so user must specify actual executable
        # for it to be filterable (at least currently)

        # as for linux reusing the pids, timekpr refreshes processes very 3 secs
        # or so, depending on config, but reuse seems to be full circle, i.e.
        # pid is reused only when limit is reached, then it reuses pids from
        # the start of interval and only those which are not in use
        # so I don't think this actually affects timekpr at all

        # unique last update date + stats variables (these ar for actual counts, not just assesing the result)
        self._cachedPids[self._TIM] = dt
        cpids = 0
        rpids = 0
        apids = 0
        lpids = 0
        lcmpids = 0
        ccmpids = 0
        qcpids = 0
        ampids = 0

        # ## alternative solutions for determining owner / process ##
        useAltNr = 3
        # list all in /proc
        procIds = [rPid for rPid in os.listdir("/proc") if rPid.isdecimal()]
        # loop through processes
        for procId in procIds:
            # def
            exe = None
            cmdLine = None
            userId = None
            prevUserId = None
            qcChk = False
            processChanged = False

            # matched
            if procId in self._cachedPids[self._PIDS]:
                # determine whether this process passed QC validation
                if self._cachedPids[self._PIDS][procId][self._QCP] > 0 and self._cachedPids[self._PIDS][procId][self._EXE] is not None:
                    # stat
                    qcpids += 1
                    # decrease check times
                    self._cachedPids[self._PIDS][procId][self._QCT] -= 1
                    # check whether it's time to recheck the process
                    if not self._cachedPids[self._PIDS][procId][self._QCT] > 0:
                        # decrease pass times
                        self._cachedPids[self._PIDS][procId][self._QCP] -= 1
                        # set up next countdown
                        self._cachedPids[self._PIDS][procId][self._QCT] = self._QCT_V
                        # we need to check process
                        qcChk = True

                # cached
                self._cachedPids[self._PIDS][procId][self._TIM] = self._cachedPids[self._TIM]
                # stats
                cpids += 1
                # if not QC
                if not qcChk:
                    # pass
                    continue

            # since processes come and go
            try:
                # ## depending on version (they all work, but speed / feature may differ)
                # using status (correct euid)
                if useAltNr == 1:
                    # obj
                    obj = self._STATUS % (procId)
                    # found the process, now try to determine whether this belongs to our user
                    with open(obj, mode="r") as usrFD:
                        # read status lines
                        content = usrFD.read().splitlines()
                        # loop through status lines
                        for rStat in content:
                            # we are interested in Uid
                            if rStat.startswith("Uid:"):
                                # check for our user
                                userId = rStat.split("\t")[1]
                                # found Uids, no need to check more
                                break
                # using commandline (filter through params too)
                elif useAltNr == 2:
                    # obj
                    obj = self._CMDLINE % (procId)
                    # check the owner (since we are interested in processes, that usually do not change euid, this is not only enough, it's even faster than checing euid)
                    userId = str(os.stat(obj).st_uid)
                # using symlinks (faster)
                else:
                    # obj
                    obj = self._EXECUTABLE % (procId)
                    # check the owner (since we are interested in processes, that usually do not change euid, this is not only enough, it's even faster than checing euid)
                    userId = str(os.lstat(obj).st_uid)

                # check if we have it
                if userId not in self._cachedPids[self._USRS]:
                    # verify
                    if userhelper.isUserValid(int(userId)):
                        # initialize set
                        self._initUserData(userId)
                    else:
                        # this is not of our interest
                        userId = None
                # we need commandlines for every process, in case it changes (snapd?)
                try:
                    # ## alternative
                    if useAltNr == 3:
                        # read link destination (this is the final destination)
                        exe = os.readlink(obj)
                    # ## alternative
                    else:
                        # try reading executable for process
                        with open(obj, mode="r") as cmdFd:
                            # split this
                            exe = cmdFd.read().split("\x00")[0]
                    # we have to inspect full cmdline (the first TK_MAX_CMD_SRCH (def: 512) symbols to be precise)
                    if self._timekprConfig.getTimekprPlayTimeEnhancedActivityMonitorEnabled():
                        # obj
                        obj = self._CMDLINE % (procId)
                        # try reading cmdline for process
                        with open(obj, mode="r") as cmdFd:
                            # split this
                            cmdLine = cmdFd.read().replace("\x00", " ")[:cons.TK_MAX_CMD_SRCH]
                except Exception:
                    # it's not possible to get executable, but we still cache the process
                    exe = None
                    # stat
                    lcmpids += 1
            # try next on any exception
            except Exception:
                # stats
                lpids += 1
                # process not here anymore, move on
                continue

            # if we ar not running QC check, we cache it, else we make verifications
            if not qcChk:
                # cache it
                self._cachedPids[self._PIDS][procId] = {self._UID: userId, self._EXE: exe, self._CMD: cmdLine, self._QCP: (self._QCP_V if exe is not None else 0), self._QCT: (self._QCT_V if exe is not None else 0), self._TERM: 0, self._TIM: self._cachedPids[self._TIM]}
                # stats
                apids += 1
            else:
                # check if process changed uid / cmdline
                if self._cachedPids[self._PIDS][procId][self._UID] != userId or self._cachedPids[self._PIDS][procId][self._EXE] != exe:
                    # log
                    log.log(cons.TK_LOG_LEVEL_DEBUG, "WARNING: uid/executable changes, uid: %s -> %s, executable: \"%s\" -> \"%s\"" % (self._cachedPids[self._PIDS][procId][self._UID], userId, self._cachedPids[self._PIDS][procId][self._EXE], exe))
                    # save previous user id
                    prevUserId = self._cachedPids[self._PIDS][procId][self._UID]
                    # adjust new values
                    self._cachedPids[self._PIDS][procId][self._UID] = userId
                    self._cachedPids[self._PIDS][procId][self._EXE] = exe
                    self._cachedPids[self._PIDS][procId][self._CMD] = cmdLine
                    # if process has changed, we do not verify it anymore
                    self._cachedPids[self._PIDS][procId][self._QCP] = 0
                    self._cachedPids[self._PIDS][procId][self._QCT] = 0
                    # flag that this is changed
                    processChanged = True
                    # stats
                    ccmpids += 1
                else:
                    # nothing here
                    continue

            # we have user (or process changed and we have to update processes / matches)
            if (userId is not None and not qcChk) or processChanged:
                # handle case when uid becomes None from existing
                if userId != prevUserId and prevUserId is not None:
                    # remove from user pids
                    if procId in self._cachedPids[self._USRS][prevUserId][self._PIDS]:
                        # remove
                        self._cachedPids[self._USRS][prevUserId][self._PIDS].remove(procId)
                    # remove from matched pids
                    if procId in self._cachedPids[self._USRS][prevUserId][self._MPIDS]:
                        # remove
                        self._cachedPids[self._USRS][prevUserId][self._MPIDS].remove(procId)
                # only if user is specified
                if userId is not None:
                    # manage pids for users
                    self._cachedPids[self._USRS][userId][self._PIDS].add(procId)
                    # verify whether this cmdline matches any of the filters user set up
                    for rFlt in self._cachedPids[self._USRS][userId][self._FLTS]:
                        # matched pids
                        matchedPids = self._getMatchedProcessesByFilter(userId, self._cachedPids[self._USRS][userId][self._FLTS][rFlt], set([procId]))
                        # match and add to user matched pids
                        for rPid in matchedPids:
                            # add to user pids
                            self._cachedPids[self._USRS][userId][self._MPIDS].add(rPid)
                            # stats
                            ampids += 1

        # take care of removing the disapeared pids
        pids = [rPid for rPid in self._cachedPids[self._PIDS] if self._cachedPids[self._TIM] != self._cachedPids[self._PIDS][rPid][self._TIM]]

        # remove items
        for rPid in pids:
            # pid
            uid = self._cachedPids[self._PIDS][rPid][self._UID]
            # uid found
            if uid is not None:
                # remove it from user pids
                self._cachedPids[self._USRS][uid][self._PIDS].remove(rPid)
                # remove it from user pids that matched filters
                if rPid in self._cachedPids[self._USRS][uid][self._MPIDS]:
                    # remove
                    self._cachedPids[self._USRS][uid][self._MPIDS].remove(rPid)
            # remove
            self._cachedPids[self._PIDS].pop(rPid)
        # stats
        rpids += len(pids)

        # extra log
        if log.getLogLevel() == cons.TK_LOG_LEVEL_EXTRA_DEBUG:
            # users
            for rUser in self._cachedPids[self._USRS]:
                # print processes
                log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "PT, user: %s, processes: %i, match: %i" % (rUser, len(self._cachedPids[self._USRS][rUser][self._PIDS]), len(self._cachedPids[self._USRS][rUser][self._MPIDS])))

        log.log(cons.TK_LOG_LEVEL_DEBUG, "PT stats, users: %i, cache: %i, add: %i, rm: %i, lost: %i, nocmd: %i, qc: %i, changed: %i, admatch: %i" % (len(self._cachedPids[self._USRS]), cpids, apids, rpids, lpids, lcmpids, qcpids, ccmpids, ampids))
        log.log(cons.TK_LOG_LEVEL_EXTRA_DEBUG, "finish cachePlayTimeProcesses")

    def _scheduleKill(self, pPid, pKill):
        # kill process
        try:
            # if trying to terminate
            if not pKill:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "sending terminate signal to process %s" % (pPid))
                # terminate
                psutil.Process(pid=int(pPid)).terminate()
            # now just kill
            else:
                # logging
                log.log(cons.TK_LOG_LEVEL_INFO, "sending kill signal to process %s" % (pPid))
                # kill
                psutil.Process(pid=int(pPid)).kill()
        except:
            # error in killing does not matter
            pass

    def processPlayTimeActivities(self):
        """This is the main process to take care of PT processes"""
        # cache processes
        self._cachePlayTimeProcesses()

    def verifyPlayTimeActive(self, pUid, pUname, pSilent=False):
        """Return whether PlayTime is active, i.e. offending process is running"""
        # if we have user
        if pUid in self._cachedPids[self._USRS]:
            # extra log
            if not pSilent and log.getLogLevel() == cons.TK_LOG_LEVEL_DEBUG:
                # logging
                log.log(cons.TK_LOG_LEVEL_DEBUG, "PT: user \"%s\" (%s) has %i matching processes out of %i, using %i filters" % (pUname, pUid, len(self._cachedPids[self._USRS][pUid][self._MPIDS]), len(self._cachedPids[self._USRS][pUid][self._PIDS]), len(self._cachedPids[self._USRS][pUid][self._FLTS])))
            # result
            return True if self._cachedPids[self._USRS][pUid][self._MPIDS] else False
        else:
            # result
            return False

    def processPlayTimeFilters(self, pUid, pFlts):
        """Add, modify, delete user process filters"""
        # if we do not have a user yet
        if pUid not in self._cachedPids[self._USRS]:
            # initialize set
            self._initUserData(str(pUid))

        # the logic here is that we need to remove obsolete first and add the rest later
        # this is due to user may enter filters in a way that process matches more than one filter
        # therefore not to loose processes, this order is important
        newFlts = set([rFlt[0] for rFlt in pFlts])
        existFlts = set([rFlt for rFlt in self._cachedPids[self._USRS][pUid][self._FLTS]])
        # remove obsolete filters
        for rFlt in existFlts:
            # if this is obsolete
            if rFlt not in newFlts:
                # now remove processes associated with filter
                for rPid in self._getMatchedProcessesByFilter(pUid, self._cachedPids[self._USRS][pUid][self._FLTS][rFlt], self._cachedPids[self._USRS][pUid][self._MPIDS]):
                    # remove pids
                    self._cachedPids[self._USRS][pUid][self._MPIDS].remove(rPid)
                # remove filter
                self._cachedPids[self._USRS][pUid][self._FLTS].pop(rFlt)
        # process filters
        for rFlt in newFlts:
            # if filter does not exist, we need to add it
            if rFlt not in existFlts:
                # filter does not exist, we need to add it
                self._cachedPids[self._USRS][pUid][self._FLTS][rFlt] = []
                # firstly check if regexp is valid, in case someone will not enter it correclty (probably by mistake)
                try:
                    # if this succeeds then match is valid
                    re.compile("^%s$" % (rFlt))
                    # filter as is
                    flt = rFlt
                except re.error:
                    # it failed, so we do escape and that's our pattern
                    flt = re.escape(rFlt)
                # remove brackets "[]" because we use them as description
                flt = flt.replace("[", "").replace("]", "")
                # add precompiled filters
                self._cachedPids[self._USRS][pUid][self._FLTS][rFlt].append(re.compile("^%s$" % (flt)))
                self._cachedPids[self._USRS][pUid][self._FLTS][rFlt].append(re.compile("[/\\\\]%s$" % (flt)))
                self._cachedPids[self._USRS][pUid][self._FLTS][rFlt].append(re.compile("[/\\\\]%s " % (flt)))
                # add matched pids to to matched pid list
                self._cachedPids[self._USRS][pUid][self._MPIDS].update(self._getMatchedProcessesByFilter(pUid, self._cachedPids[self._USRS][pUid][self._FLTS][rFlt], self._cachedPids[self._USRS][pUid][self._PIDS]))

    def killPlayTimeProcesses(self, pUid):
        """Kill all PT processes"""
        # if we have user
        if pUid in self._cachedPids[self._USRS]:
            # logging
            log.log(cons.TK_LOG_LEVEL_INFO, "killing %i PT processes for uid \"%s\" " % (len(self._cachedPids[self._USRS][pUid][self._MPIDS]), pUid))
            # terminate / kill all user PT processes
            for rPid in self._cachedPids[self._USRS][pUid][self._MPIDS]:
                # increase terminate attempts
                self._cachedPids[self._PIDS][rPid][self._TERM] += 1
                # schedule a terminate / kill (first we try to terminate and later we just kill)
                GLib.timeout_add_seconds(0.1, self._scheduleKill, rPid, True if self._cachedPids[self._PIDS][rPid][self._TERM] > cons.TK_POLLTIME else False)

    # --------------- helper methods --------------- #

    def getCachedProcesses(self):
        """Get all cached processes"""
        proc = [[rPid, self._cachedPids[self._PIDS][rPid][self._EXE], self._cachedPids[self._PIDS][rPid][self._CMD]] for rPid in self._cachedPids[self._PIDS]]
        return proc

    def getCachedUserProcesses(self, pUserId):
        """Get processes, that are cached for user"""
        if pUserId in self._cachedPids[self._USRS]:
            proc = [[rPid, self._cachedPids[self._PIDS][rPid][self._EXE], self._cachedPids[self._PIDS][rPid][self._CMD]] for rPid in self._cachedPids[self._USRS][pUserId][self._PIDS]]
        else:
            proc = []
        return proc

    def getMatchedUserProcesses(self, pUserId):
        """Get processes, that are cached for user and matches at least one filter"""
        if pUserId in self._cachedPids[self._USRS]:
            proc = [[rPid, self._cachedPids[self._PIDS][rPid][self._EXE], self._cachedPids[self._PIDS][rPid][self._CMD]] for rPid in self._cachedPids[self._USRS][pUserId][self._MPIDS]]
        else:
            proc = []
        return proc

    def getMatchedUserProcessCnt(self, pUserId):
        """Get process count, that are cached for user and matches at least one filter"""
        if pUserId in self._cachedPids[self._USRS]:
            procCnt = len(self._cachedPids[self._USRS][pUserId][self._MPIDS])
        else:
            procCnt = 0
        return procCnt
