# Timekpr-nExT

## Keep control of computer usage

Timekpr-nExT, a fresh, simple and easy to use screen time managing application that helps optimizing time spent at computer for your subordinates, children or 
even for yourself.

The application is targeted at parents or supervisors to optimize / limit time spent at computer as they see fits their situation.

</br>

## Overview

Timekpr-nExT is designed to keep control of computer usage, which implies forcibly terminating user sessions and / or other types of 
restrictions and limitations.

Please be responsible and inform your users that their time is accounted and their work might be terminated abruptly, although 
notifications can be configured to warn them. In fact, notifications are mostly in their own hands :)

</br>

Supervisor, when setting up limitations, please read the description of options and explore application before you enforce some option on user. Combination of 
options will give very tailored experience, but remember - Timekpr-nExT is a restrictive application.

</br>

_**Note**: information in this README is updated along with ```beta``` releases, if you do not find a particular option in ```stable``` series, please wait 
until it's released or use ```beta```._

</br>

## Navigation guide

**This README** is useful, but quite large, so I have prepared a guide for You.

* About functionality:

  - a short description of [applications](#applications) with [typical use case](#typicalusecase)

  - to better understand functionality click on [description of functionality](#detaileddescription) and particularly [client application](#clientapplication) and [administration application](#administrationapplication)

  - latest prominent features introduced are [suspend/lock/shutdown](#restrictionlockouttypes), [PlayTime functionality](#playtimeconfiguration), 
  [user configurable notifications](#userconfigurablenotifications), ["freeride" time periods](#freerideintervals)

  - to get information about CLI (console) use / file configuration possibilities [additional configuration possibilities](#additionalconfigpossibilities)

* Support the project:

  - support by **[donating](#support)** or translating it to your [language](#translate)

* Installation guide:

  - installation / removal [instructions](#installation) for most popular Linux systems

* Disclaimer, questions, suggestions and bugs:

  - disclaimer is [here](#disclaimer) and information about questions, suggestions and bugs is [here](#bugs)

</br>

<a name="applications"></a>
## Applications overview

Timekpr-nExT has two user facing applications which governs its behaviour.

</br>

#### Timekpr-nExT Client indicator icon

An application and indicator icon which takes care of showing the time, limits and notifications to the user.

![Timekpr-nExT icon](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-icon-system-notification-area.png)

_Informational "padlock" icon in they system notification area which is what user is automatically seeing when logged in._

</br>

#### Timekpr-nExT Client application

Client application itself is activated by clicking on the icon and choosing menu "Limits & configuration", it contains more detailed information and 
some useful configuration options.

![Timekpr-nExT Client application](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-client.png)

_Application shows detailed information about limits as well as allows to configure certain aspects of functionality._

</br>

#### Timekpr-nExT Administration application

An administration application for supervisors or parents to configure time limits for any user in the system as well as configure technical aspects of 
Timekpr-nExT.

![Timekpr-nExT Administration application](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-admin.png)

_Application has multiple configuration options organized in tabs to tailor experience as desired._

</br>

#### Core of the Timekpr-nExT

The invisible part of the Timekpr-nExT is the background service, sometimes referred as daemon, not demon :), which takes care of monitoring the system 
and enforcing 
restrictions and limits.

There is no nice picture for it, but mark my word, it's there working for you ;)

</br>

<a name="detaileddescription"></a>
## Description of functionality

This section describes what and how Timekpr-nExT does its thing rather than descriptive information about every configuration option.

**Please note** that to describe configuration options, Timekpr-nExT heavily relies on tool-tip / hint functionality, please navigate mouse 
over to any configuration option and read its description, it usually helps to understand it better.

</br>

### Overall features

Timekpr-nExT tries to be as precise as possible and as much nice to user as restrictive software can be.

One of the things that has to be in place to accomplish that, is predictable and precise time accounting. Timekpr-nExT accounts time every 3 seconds by default 
and gives clear time / limits information to user.

Another thing is that time must not be accounted when it doesn't have to, so it tries to avoid accounting inactive session time. By inactive I mean user that 
is not using computer either because another user is using the computer via user switching functionality or user's session is locked.

Time is not accounted, obviously, when computer is put to sleep too.

The rest is up to supervisor to decide. Read on to have complete understanding of all functionality Timekpr-nExT offers.

</br>

<a name="administrationapplication"></a>
### Administration application

Administration application is used to configure time limits and restrictions for users as well as technical options for Timekpr-nExT itself.

To run administration application you either need to run it as superuser or you need to add yourself to ```timekpr``` system group to have password-less 
access to configuration.

Running as superuser is straightforward, open your favourite dock / launcher / application list and choose "(SU) Timekpr-nExT Control Panel 
(superuser mode)". 

_Note: "(SU)" was added in front of application names because some earlier Gnome3 versions simply truncated longer application names and it 
was indistinguishable between the modes._

Running as part of the group requires more involvement. Add yourself to timekpr group either by your favourite user administration 
application which should be provided by your favourite desktop environment or simply run ```sudo gpasswd -a $USER timekpr``` (change $USER to proper
username for administration, if it differs from currently logged in one and do NOT put your subordinate's username there ;)). The user who was added to 
```timekpr``` group will need to log out and in for this to work.

</br>

_**Please note**: certain configuration options are not accessible when running in password-less mode, they're not related to user 
configuration and should be used very seldom in very special cases, however running in superuser mode grants all access to all options._

</br>

### User configuration

To configure limits and restrictions for user, it has to be selected from the user list. User list is retrieved from your system and initial 
configuration is applied.

_**Please note**: when opening administration application no user is pre-selected, this is by design to force a supervisor to choose a correct 
user to configure and avoid unintentional misconfiguration._

</br>

#### Tab "Info & today"

As the title implies, this section shows information about how much time user has spent and how much time he has left.

Some of the information is shown only when user is logged in, but some of the information is from saved state only. Live information is more accurate and 
allows to monitor user in realtime, however saved state will be shown always.

Time adjustment controls are used, for example, if a supervisor decides to reward user with greater time allowance just for this day. Of course reward is 
not always a choice to make, so it's possible to penalise user too.

Keep in mind that adding more time will not override allowed time periods and general time allowance, you'll read about them later in this README.

Pro tip: use tool-tips to find more information.

</br>

There's a special time value called "Continuous time available" which means exactly that - a time which is available to use continuously depending on time 
allowance and allowed time period setup, however it's not counted for more than this and the next days together.

Continuous time may span this and next days, which means that user will be able to use computer across midnight, it's only possible when this days time period 
ends at 24:00 and next days time period starts at 00:00.

</br>

#### Tab "Limit configuration"

This tab allows you to configure time limitations for users. Combine options to have the setup tailored to your view of user's order of the day.

Before explaining how to configure them, I'll give two most common setup variants for the limits:

* set time allowance to whole day and limit access to specific time periods, example: 24hrs of allowance and 9:00-12:00, 13:00-16:00 and 19:00-21:00

* set time allowance to allowed hours a day and set time periods when user can use computer, example: 8hrs of allowance and 9:00-21:00 period when to spend 
those 8hrs

_**Please note** that time values follow ISO 8601 standard, in other words it means that first week day is Monday and hours are displayed in 24h format._

---------------------------------------

##### Week day limits

This section presents configuration for every week day. Namely one can select on which days user can use computer as well as adjust a time limit for every day.

Days have to be enabled / disabled for every day separately, but limits can be adjusted for multiple days at once. Just select multiple days, select what you 
would like to adjust - hours or minutes and press "+" or "-" button. Simple as that :)

By default every day is enabled and user have all the time available.

---------------------------------------

##### Hour intervals

Hour intervals define time periods when user can use the computer. These can be configured on per day basis, however it's possible to configure them for 
multiple days at once, just select multiple days and configure time periods.

The configuration itself is simple too. To create an interval, press create button and specify start and end of the time period by clicking on created interval 
inside the table.

<a name="freerideintervals"></a>
There's a special setting for time interval indicated as "∞". Basically this setting means that time spent in this time period will not be accounted 
towards user's daily allowance, i.e. it's free time for him. In addition to that, this allows the user to use computer even if he has no time left all. This 
setting can be useful in case user has a special arrangement, such as online courses at specific times, so he does not spend his personal limit on them.

Please keep in mind that intervals themselves **cannot** overlap in any way, however it's possible to have intervals ending and starting continuously, for 
example, intervals 7:00-13:00 and 13:00-14:30 can coexist, but don't be surprised when adjacent intervals are merged into one.

Be aware, that if there's a break in time periods, even just for one minute, user will face whatever restriction is set for him.

Be aware that there's is a specific design choice in place which governs that one hour can not contain more than one time period. Time period, however, can 
fully fit within an hour, start in it or end there, i.e. time periods 7:15-9:15 and 9:45-14:30 cannot be entered, but time periods 7:15-9:00 and 9:45-14:30 
are allowed.

After entering intervals, one have to press "verify" button for application to know that one, you know, did not made a typo :) If intervals are ok, one can 
apply the configuration. When time periods are misconfigured, both conflicting intervals will be highlighted.

When defining the intervals one can use shortcuts, namely - entering 7 will result in 07:00, entering 7:15 will result in 07:15.

By default whole day is available.

---------------------------------------

##### Weekly and monthly limits

This section allows to adjust weekly and monthly time allowances. Just select a period and a time unit day, hour or minute and press "+" or "-" buttons to 
adjust the limits.

These limits work together with daily limits and hour intervals, user's time is the least of the limits.

By default whole week and month is allowed, which is the common use case, one does not have to modify these values when daily limits are in use.

</br>

<a name="playtimeconfiguration"></a>
#### PlayTime configuration

PlayTime is screen time limiting mode for applications / processes in the system, which in context of PlayTime, are called "activities".

PlayTime extends time limit configuration and accounting by greater control over how long certain applications can run. In other words, this functionality 
works as a process monitor of sorts.

PlayTime allows users to use certain applications for the configured period of time. If time allowance is all used, applications are terminated. 
Running them again will result in termination.

Please keep in mind that generally PlayTime is a special limit within a standard time limit, therefore all rules of standard time limits and allowances fully 
apply, except "override" mode, which will be explained in the options section.

This mode was designed for games, hence the name, but a supervisor can define any application to be monitored, for example Web browsers.

_**Please note** that PlayTime will still account user's PlayTime even in time periods which are marked as free ("∞") in standard time configuration! Except 
"override" mode, that is :)_

---------------------------------------

##### PlayTime options

This section provides controls for PlayTime enablement and so called PlayTime override mode.

PlayTime has to be enabled for every user separately and if it's not enabled, obviously, PlayTime will not work for this user. Be sure to enable 
[PlayTime master switch](#playtimemasterswitch) to enable PlayTime accounting in the system, otherwise it will not work even if it's enabled for the user.

By default, PlayTime is not enabled.

</br>

There's a special "override" mode for PlayTime already mentioned above.

There is a big difference from standard restrictive mode. In this mode PlayTime allowance and limits are disabled and user's time spent at computer is only 
accounted when applications configured as activities are used. That means that unless user uses computer for configured activities, it's free time for him.

</br>

Option "Allowed during "∞" intervals" controls whether PlayTime activities are allowed to run during unaccounted time intervals which are marked as "∞". 
If this option is disabled, user will not be able to run any of the configured activities.

However, if this option is enabled, user can use any of the activities configured for him even in unaccounted, i.e. "free", time intervals.

As an example, this option can come handy, if time intervals marked as "∞" are used to attend mandatory education classes and supervisor 
does not want to allow a subordinate to run any of the configured activities during unaccounted time intervals. Just do not enable the option and you are set.

</br>

_**Please note** that if "override" mode is enabled and user uses PlayTime in time periods which are marked as free ("∞") in standard time configuration, 
the time is not accounted towards PlayTime limit, i.e. it's free time for him. The exception is the option "Allowed during "∞" intervals", if it's disabled, 
activities is not allowed even in "override" mode!_

---------------------------------------

##### PlayTime limits

PlayTime limits are similar to standard time limits and allowances, configuration is the same, but these only apply to PlayTime.

If certain day is disabled for PlayTime, user can not use any of configured activities - they will be terminated immediately.

_**Please note** that PlayTime limits are not effective when "override" mode is used._

---------------------------------------

##### PlayTime activities

This is the most important section for PlayTime. Here one configures what are the activities to be monitored, but please keep in mind that this list is not a 
allowlist or denylist of applications.

PlayTime functionality requires the supervisor to set up process masks for each activity he wants to limit. This may involve running process monitor from your 
favourite desktop environment, console / terminal or even remotely via SSH.

The reason for this is that Linux is completely open. This in itself is great, but that means that any software can be installed anywhere even in multiple 
copies and even user itself can do it! Yes, games in Lutris or Steam and so on. Installed software does not scream out load "hey, I'm a game!", so a supervisor 
has to determine that.

</br>

So here's a generic guide how to determine processes or their masks which can be used in activity configuration.

At first, especially if you have not seen terminal, this may look scary, but you always can use graphical tools to achieve this. KDEs and Gnomes "System 
monitor" does this pretty well, look for process name or command or commandline columns, they are your best friends in this.
You can always ask your favourite web search engine or community how to determine process executable name.

Since process mask for PlayTime activity is basically a name of executable or full command line in case ["Enhanced activity monitor"](#playtimeenhancedactivitymonitor) 
is enabled (case sensitive!), a simple ```top -c -d 1``` in terminal usually will do the trick to find one. 
Games, when running, usually use most resources compared to anything else, so they will be on top.

Watch for COMMAND column. If the process looks very much like activity you want to limit, take actual executable name, without path, and fill it in the process 
mask field. Here's the example for Discord Canary, in the process list I see ```/opt/discord-canary/DiscordCanary --type=renderer ...```, only 
```DiscordCanary``` is the part you need. It's located after last slash and before arguments.

Some games on Linux behaves badly when Alt-Tabbing them, so connect to computer via SSH and determine a process name from there.

You can enter the description of activity too, it will be shown to user instead of actual process mask. If description is not entered, the actual mask is shown 
to the user.

</br>

**Please note** that process masks can accept RegExp (not glob!) expressions, except symbols [], but keep in mind that this is an expert option!

Please do verify that your RegExp is correct and it actually works, misusing them may end up killing unwanted user processes or may not match anything at all!

If RegExp is not correct, it will be used as literal strings. For example, ```*wine*``` is **not** a correct RegExp, ```.*wine.*``` is. Failing to specify this 
correctly will end up searching processes which are literary ```*wine*```, which obviously does not exist usually.

It's worth mentioning that PlayTime employs a smart caching algorithms and tries to get the process list in a very efficient way. Only processes that are run 
as particular user are monitored, accounted and terminated.

In addition to that PlayTime logic works only when there are users that have PlayTime enabled and there are at least some activities configured.

</br>

#### Tab "Additional options"

As the name suggests this section has additional per user configuration options.

By enabling track inactive sessions every user session will be accounted, even if they are locked or other user is currently using the computer. Enable with 
care.

Hide icon and notifications does exactly that, it hides Timekpr-nExT client icon and hides most notifications too. Only critical notifications are shown. If 
you 
enable this to unrestricted user, he will not even notice Timekpr-nExT is there :)

</br>

Restriction & lockout type governs what type of action will be executed when time for the user will run out.

_**Note**: please be careful if choosing non-default option, think ahead and figure out whether other options are suited for your use case!_

---------------------------------------

<a name="restrictionlockouttypes"></a>
##### terminate sessions

This is the default option and a restrictive one. It terminates user sessions, that is, user is forcibly logged out without asking much questions.

---------------------------------------

##### shutdown computer

This is another restrictive option, when time runs out, the computer will be shut down. Please use with caution, especially in multi-user environments!

---------------------------------------

##### suspend computer

This is lockout option. That is when time runs out computer is suspended.

Option is more suited for self control rather than restrict computer usage, due to the fact that sessions aren't terminated.

When computer is woken up at the moment when there is no time left, but user does not unlock the computer, it stays that way. If computer is unlocked, then 
instead of suspend, the screen is locked. This behaviour was put in place to avoid excessive turn on / off of computer for regular user, however if user 
unlocked 
computer a lot of times ~ 20, then it will be suspended.

---------------------------------------

##### suspend / wakeup computer

This is lockout option, very similar to plain suspend, but with a catch - computer will be woken up at next available time period for that day. It will be 
woken 
up only if Timekpr-nExT was the one who put it to sleep.

Additionally you need to specify hour interval when computer may be woken up automatically. If next available time period is outside of configured interval, 
computer will NOT be woken up!

**Please note** that wakeup time is dependent on BIOS / UEFI support for RTC wakeup. If there is no support for it or it is disabled, computer will NOT be 
woken 
up!

---------------------------------------

##### lock screen

This is lockout option. When time runs out, computer screen is locked. If computer is unlocked when there is still no time left, it will be locked again 
shortly. Simple as that :)

Option is more suited for self control rather than restrict computer usage.

</br>

### Timekpr-nExT configuration

This tab allows a supervisor to configure certain technical aspects how Timekpr-nExT behaves. These options usually doesn't have to be changed as they are 
tuned to their optimal values.

</br>

#### Timekpr-nExT control options

This section contains various knobs to finetune time accounting and enforce limits.

---------------------------------------

##### Final notification

Notification configuration is now a users responsibility, so he may decide to remove all notifications altogether, which may not be the best way to be 
informed about imminent log out.

This option comes to rescue, it will force a one final notification on user (which can still be disabled by user) to inform about the imminent restriction 
enforcement.

---------------------------------------

##### Termination time

This option specifies number of seconds left for user before enforcing the selected lockout / restriction on him. When this many seconds are left, user is 
added to the restriction list and will start to face them.

This can be prevented by adding more time allowance or when user becomes inactive, so the scenario when user locks computer to go to supervisor to ask for more 
time allowance is plausible.

---------------------------------------

##### Countdown time

This option specifies number of seconds left for user before a countdown for the selected lockout / restriction starts. Countdown is continuous notification 
stream about very last seconds left.

---------------------------------------

##### Poll interval

This option specifies the rate in seconds at which Timekpr-nExT processes users, their sessions and calculates time values for them. This option can 
somewhat be considered as resolution of time accounting too.

---------------------------------------

##### Save time

This option specifies the rate in seconds at which Timekpr-nExT saves calculated time values to disk. Theoretically this means that if computer crashes this 
should be the max time that can be lost / unaccounted.

---------------------------------------

##### Log level

This is the log level, high the level more information is written to log files. Level 1 is the minimal level which will save space but will not give me enough 
information in case you file a bug, level 2 is the standard level, it usually writes sufficient level of information for problem solving. Level 3 is the 
"crazy" value which prints way too much cryptic in memory structures which may be interesting to me, but not to non-developer.

If everything is working fine for you, set the level to 1, otherwise leave it at default value. Be assured that log files doesn't contain anything sensitive 
except usernames.

Please note that log files are handled by ```logrotate``` and are compressed, so I wouldn't worry about space usage at all.

</br>

#### Tracked sessions

There are multiple session types on Linux systems. By default Timekpr-nExT tracks graphical sessions that are running on "x11" (xorg), "wayland" and "mir".

The two most common types used 99.99% of all desktop Linux installations are "x11" and "wayland", however "mir" is not, but support to detect these is still in 
place, so it's left there just in case.

Please keep in mind that there are no more session types than these and the ones mentioned in excluded sessions option, please do not modify this unless you 
know what you are doing.

</br>

#### Excluded sessions

By default Timekpr-nExT does not track sessions from "tty" (console logins that are accessible by pressing Ctrl+Alt+F[1-7]) and "unspecified" which are the 
rest. Please do not modify this unless you know what you are doing.

In case you really need to track console sessions too, please remove "tty" from this list and add it to the tracked sessions list.

</br>

#### Excluded users

This section allows supervisor to exclude certain **system** users from accounting. This section is meant to exclude users that do create sessions, but are not 
used to log in directly, e.g. login managers.

Please do not enter normal users here as that will not work and cause errors when client will try to obtain information from daemon!

</br>

<a name="playtimemasterswitch"></a>
#### Additional options

Currently there are couple of options, all related to PlayTime.

</br>

##### PlayTime enabled
"PlayTime enabled" controls **master switch for PlayTime** functionality. 
I has to be turned on to enable PlayTime globally, if it's switched off, none of the users will have their activities accounted regardless of individual 
PlayTime setting!

</br>

<a name="playtimeenhancedactivitymonitor"></a>
##### Enhanced activity monitor
"Enhanced activity monitor" option controls whether PlayTime functionality will use first 512 characters of full process commandline, including process arguments, 
to match proccesses against registered activity / process masks for users. 

This allows a supervisor to use advanced RegExp patterns to find not just a process name, but a great deal of arguments too. This option may be useful for 
situatuations when there are processes running interpreted language, such as python or java. The most common gaming example is Minecraft, which is a java 
application started from jar file, a process mask for it would be ```.*java.*minecraft.*```.

</br>

<a name="clientapplication"></a>
### Client application

Timekpr-nExT client application provides time metrics and configuration possibilities to user. Since the user is the one who actually face the restrictions, 
the configuration possibilities are limited.

User can use tool-tips / hints to get more information on every value of the application by navigating mouse over the displayed information.

Please look at the [information representation differences](#desktopenvironmentdifferences) which may affect the way application looks to user.

</br>

#### Daily limits

Daily limits shows daily time allowance, time period restrictions and time spent / left set by supervisor. Most important metrics are continuous time left and 
time periods when user can use the computer.

If time period has "∞" sign besides it, the time for this period will not be counted towards the user's limit, i.e. free time for the user.

</br>

#### Additional limits

Additional limits show weekly and monthly limits set by supervisor as well as time spent so far during this week and month.

</br>

#### PlayTime limits

This tab shows time allowance and activity list for PlayTime. Description of PlayTime can be found in [PlayTime administration part](#playtimeconfiguration) of 
this guide. User is able to see what type of PlayTime mode is enabled and what are the limits for this day.

Tab shows active PlayTime activity count too as well as description of activities that are being monitored / restricted.

Please note that this tab is not available to user if supervisor has not enabled PlayTime for the user.

</br>

<a name="userconfigurablenotifications"></a>
#### Notifications

This is the first tab where user can make adjustments to tailor Timekpr-nExT behaviour to his needs. User can define a time left threshold when he'll be 
notified about how much time is left. He can assign a priority of notification as well.

There is a separate section for standard time left and PlayTime left notification configuration. Please note that PlayTime notification configuration is not 
shown to user if supervisor has not enabled PlayTime for the user.

More information can be found by viewing tool-tips of the configuration table.

</br>

#### Configuration

This tab allows user to configure additional options to tailor Timekpr-nExT to his needs.

User is able to control whether seconds are shown besides the icon, whether all and limit change notifications are shown. It's possible to set up sound 
notification too, by installing ```python3-espeak``` package.

There are configuration options for normal and critical notifications, sound "bell" when notifications are shown and technical log level too.

More information on every option can be found in tool-tips.

_**Please note** that there seems to be a [bug](#quirkssound) in sound notifications._

<a name="typicalusecase"></a>
</br>

## Typical use case

Let's imagine a situation that Liane had to limit computer time for Cartman because he uses computer way too much to talk to Kyle and Stan _(but not Kenny, 
because he doesn't have a computer ;-))_ about messing up a day for Mr. Garrison or something along these lines. Due to his behaviour he has to attend online 
anger management classes to improve his behaviour in general.

So, Liane is thinking to introduce rather flexible time limit within strict time window for working days and holidays, in addition to that she reserves 2 hours 
from 15:00 - 17:00 on Monday for mandatory anger management classes.

Timekpr-nExT comes handy, Liane opens Timekpr-nExT Administration application makes configuration as follows:

* choose username "cartman" and switch to "Limit configuration" tab

* select Monday:

  - add interval from 7:30 - 15:00

  - add interval from 15:00 - 17:00, check the "∞" checkbox

  - add interval from 17:00 - 21:00

* select days from Tuesday through Friday:

  - set time limit to 6 hours

  - add interval from 7:30 - 21:00

* select last two days - holidays:

  - add interval from 9:00 - 22:30

  - set time limit to 8 hours

* press "Apply daily limits" and restrictions are set

</br>

By this she achieves flexibility of:

* allowing 6 hours of computer time to be used from 7:30 to 21:00 from Monday to Friday

  - allowing the use of computer from 15:00 - 17:00 without the need of spending his limit on mandatory anger management classes

* allowing 8 hours of computer time from 9:00 - 22:30 during holidays

* Cartman can not use his computer before outside of defined time periods and over the specified time allowance

</br>

Typical setup is rather simple and easy, there are (of course) more to it, please read on [Detailed information](#detaileddescription), if You're interested.

</br>

<a name="installation"></a>
## Installation / removal

First step to start using Timekpr-nExT is to install it, right? :-)

Basically there are two versions - beta and stable, usually they are not that different, but beta comes out earlier, especially when changes in upcoming 
version 
are larger.

The installation instructions are easy as well (I know that one can do that in GUI, but terminal is just simply faster :-)), just paste these lines in terminal 
and You're set.

_Note: it's highly advised to log in and out after installation of new version._

</br>

Timekpr-nExT is available in:

* my PPA (Personal Package Archive) for Ubuntu and compatible distributions

* Timekpr-nExT is available in AUR (ArchLinux User Repository) for ArchLinux and Manjaro

* packages for Fedora 32+ and openSUSE Leap 15.2+ are provided as is, link below

</br>

#### Stable

| Distribution | Stable install | Stable remove |
| :--- | :--- | :--- |
| Ubuntu & co (via PPA) | ```sudo add-apt-repository ppa:mjasnik/ppa```</br>```sudo apt-get update```</br>```sudo apt-get install timekpr-next``` | ```sudo apt-get remove --purge timekpr-next``` |
| ArchLinux & Manjaro (via AUR) | ```yay -S timekpr-next``` | ```sudo pacman -Rdd timekpr-next``` |
| Fedora and openSUSE | [manual installation](https://launchpad.net/timekpr-next/+announcement/27532) | [manual uninstallation](https://launchpad.net/timekpr-next/+announcement/27532) |

#### Beta

| Distribution | Beta install | Beta remove |
| :-- | :--: | --: |
| Ubuntu & co (via PPA) | ```sudo add-apt-repository ppa:mjasnik/ppa```</br>```sudo apt-get update```</br>```sudo apt-get install timekpr-next-beta``` | ```sudo apt-get remove --purge timekpr-next-beta``` |
| ArchLinux & Manjaro (via AUR) | ```yay -S timekpr-next-git``` | ```sudo pacman -Rdd timekpr-next-git``` |

_**Note**: for ArchLinux and Manjaro, please choose Your favourite AUR helper, if that differs from mine._

_**Note**: special thanks goes to SanskritFritz from ArchLinux community who was not only one of the first beta testers and active users, but he maintains said 
packages too._

</br>

#### Debian
Until recently there was no easy way of using Timekpr-nExT in Debian, but thanks to Sim (smntov) and Anthony Fok (foka), Timekpr-nExT is available in Debian as native 
installation.

The preferred method of installing Timekpr-nExT in Debian is the same as in Ubuntu:

| Stable install | Stable remove | Beta |
| :--- | :--- | :--- |
| ```sudo apt-get update```</br>```sudo apt-get install timekpr-next``` | ```sudo apt-get remove --purge timekpr-next``` | Not available |

**Note**: it might be possible to use a package made for ["sid"](https://packages.debian.org/sid/timekpr-next) in other versions of Debian, if dependencies are 
satisfied. For example, a package for "sid" (unstable) works in "buster" (10.7) just fine.

</br>
Of course, you can use any graphical software installer that comes with Debian too, like "KDE Discover" or "GNOME Software".

**Note**: for Debian please use a package created for Debian.

</br>

## Compatibility
I'm developing Timekpr-nExT to be compatible with most Desktop Environments, I have somewhere around 20 VMs where I test bigger changes, but I can not and will 
not test everything in the open.

I have tested that KDE, Gnome, Cinnamon, MATE, XFCE works in Ubuntu compatible OS, Manjaro / ArchLinux (which are my distributions of choice) and Debian. 
Recently I started testing in Fedora and openSUSE too.

Please read [nuances](#quirks) section for more information.

If You have an issue with Timekpr-nExT, please read [this](#bugs) and file a bug.

</br>

<a name="desktopenvironmentdifferences"></a>
## Information representation differences

Not every desktop environment is made the same, there are differences how information is shown to user.

---------------------------------------

##### icon differences

The icon in system notification area is the one that differs. Gnome3 / Unity / XFCE / etc. show icon as well as detailed label besides it, however KDE / Deepin 
show only the icon without label. However, hovering mouse over the icon, actual time left is revealed.

---------------------------------------

##### extension might be needed

On some distributions which use Gnome3 or other desktop environment based on Gnome3, a specific extension has to be enabled for icon to be shown. Usually the 
extension is provided by distribution itself, but in case it's not, please install [Appinicator 
Support](https://extensions.gnome.org/extension/615/appindicator-support/) extension manually.

---------------------------------------

##### notification timeouts / severity

Some desktop environments can and will override timeout settings specified in Timekpr-nExT configuration. Sometimes they are configurable, but sometimes they 
are not. KDE Plasma has the best respect regarding notifications I have found so far.

So unfortunately, unless you use desktop environment that respect custom values for notification timeouts, you will face the preconfigured ones.

---------------------------------------

##### the icon & future

There's a possible future issue that can surface when Gnome3 will remove [status icon](https://wiki.gnome.org/Initiatives/StatusIconMigration/Guidelines) 
functionality. When the time comes if at all, I'll try to figure out what to do about it.

</br>

## Short and very technical overview

**Warning**: this section is **very technical** and has no information that regular users of Timekpr-nExT would (possibly) want to know.

</br>

Timekpr-nExT is built with technologies which heavily use DBUS for it's interaction with the system. Not only it uses interfaces provided by various solutions, 
it exposes own interfaces to DBUS too.
It allows Timekpr-nExT to be integrated into any client application or control panel which supports DBUS interactions.

</br>

### Interfaces used
The main interface used is systemd's [login1](https://www.freedesktop.org/wiki/Software/systemd/logind/) session management interface, without it Timekpr-nExT 
will not work.

It tries to use FreeDesktops screensaver [interfaces _(better source needed)_](https://people.freedesktop.org/~hadess/idle-inhibition-spec/ch05.html) as well 
as notification [interfaces](https://specifications.freedesktop.org/notification-spec/latest/ar01s09.html) too.

In case FreeDesktop screensaver interfaces are not available, it tries to use 
[Gnome's](https://people.gnome.org/~mccann/gnome-screensaver/docs/gnome-screensaver.html).

Timekpr-nExT makes connections to DBUS objects, they are cached and during execution, it mostly just calls.

</br>

<a name="additionalconfigpossibilities"></a>
### Additional configuration possibilities

In addition to graphical applications, Timekpr-nExT can be configured using tools available in CLI (Command Line Interface) and config files (by hand).

</br>

#### CLI mode

Timekpr-nExT Administration application can be run in terminal to obtain information on users and configure limits at the same functional level as in 
graphical mode. Please note that at this time CLI interface is available for user configuration only.

For CLI usage, please open your terminal emulator of choice (i.e. Gnome Terminal / Konsole / XTerm) and type ```timekpra --help```, it will introduce you to 
Timekpr-nExT CLI by printing usage notes and examples. Timekpr-nExT Administration application in both modes apply configuration in real-time, i.e. 
configuration is effective immediately.

</br>

#### Configuration by files

It's possible to edit configuration files directly to achieve the same as with tools provided by Timekpr-nExT. In this case configuration will be read and 
applied at save intervals (by default, every 30 sec).

**Note**: please be aware that configuration files are structured in particular way, have internal representation of values and one can break the configuration 
if not being careful. You have been warned :)

**Note**: if configuration files are borked, e.g. Timekpr-nExT can not interpret them properly, it will try to salvage options it can and it will recreate the 
config file with defaults for damaged options.

</br>

**Configuration files (be careful editing them)**

| The purpose of the file | File location |
| --: | :-- |
| Timekpr-nExT main configuration file | ```/etc/timekpr/timekpr.conf``` |
| User configuration files (one per user) | ```/var/lib/timekpr/config/timekpr.*.conf``` |
| User control files (one per user) | ```/var/lib/timekpr/work/timekpr.*.conf``` |
| Client configuration file | ```$HOME/.config/timekpr/timekpr.conf``` |

</br>

### Log files

Log files are the files where Timekpr-nExT writes it's messages about execution, including a performance counters. Files are not meant to be inspected by users 
on regular basis, **there's nothing interesting nor understandable for non technical users**.

However it's possible to look at them to find technical details about state of Timekpr-nExT or investigate the problematic behaviour and errors. These are the 
files I'll be asking in case something does not work as expected.

By default Timekpr-nExT writes a sufficiently detailed log file for me to understand the problem area quite well, but that means that there are a lot of 
messages in log files. There's nothing sensitive except usernames, if this is a concern, please obfuscate them before sending the files to me or attaching them 
to bug reports.

_**Note**: if the log file size is the concern, it's possible to decrease log level in Timekpr-nExT administration application to save some space, however when 
the issue arises, most likely I'll need it to be set to level 2 (the default). Please restart Timekpr-nExT daemon ```sudo systemctl restart timekpr``` or reboot 
the computer for logging level changes to take effect._

</br>

**Log files**

| Logging area | File location |
| --: | :-- |
| Daemon log file | ```/var/log/timekpr.log``` |
| Client application log files | ```/tmp/timekprc.*.log``` |
| Administration application log files | ```/tmp/timekpra.*.log``` |

</br>


<a name="quirks"></a>
### Quirks

Linux distributions (i.e. Ubuntu, Fedora, Mint, ...) ecosystem is large, nice, diverse and all those good things, but not everything there adheres to the same 
standards, so naturally there are some differences here and there, which affects Timekpr-nExT looks and/or functionality.

When I started designing / developing Timekpr-nExT I was pretty much sure how to implement desired functionality as I have _looked into_ standards and _tested 
particular implementation_ in Ubuntu 16.04 (Unity) and it's clear what to expect, i.e. standards are standards and every implementation which uses them, should 
be roughly the same.

Roughly it was ;-) Most of the time, everything worked perfectly, but for certain functionality every Desktop Environment has it's own quirks, maybe not using 
all bits or maybe it's just buggy implementation.

This section will contain these oddities / differences in implementations as far as Timekpr-nExT development is concerned. If You find odd why things happen or 
not happen the way You expect, maybe here's an answer ;-)

---------------------------------------

_**NOTE**: the situation with quirks may change in the future, I have observed that with every new release of distributions / desktop environment 
software stack or frameworks, situation gets better, so this information may become stale at some point! I'll try to address it, but since Timekpr-nExT tries 
to support as much versions and distributions as possible, it may still apply to older version of the distributions or desktop environments..._

---------------------------------------

<a name="quirkssound"></a>
##### sound "bell" notifications

Currently it's known that if user has enabled ```Use sound "bell" for notifications```, then critical notifications might not show on Desktop, they 
are registered and can be seen in notification register, though.

---------------------------------------

##### blinking cursor of the left side of screen

Timekpr-nExT is heavily using ```login1``` DBUS interfaces to accomplish what it does. One of the things is user session termination. Timekpr-nExT asks 
```login1``` to terminate user session(s), but sometimes that ends up in black screen and a blinking cursor. This is a case when screen is not switched to 
login manager screen.
So I have implemented a workaround that after user sessions are terminated, it tries to switch to login manager.

For this to work I have developed a logic that tries to detect where's the login manager and usually it's possible when computer boots up, so restarting or 
upgrading Timekpr-nExT without rebooting while you have this issue, might end up in blinking cursor. Please restart to fix this.

---------------------------------------

##### locking the screen

Due to differences in using the standards not every Desktop Environment works equally well with time accounting for locked screen.

Some Linux distributions which are using Gnome3 and desktop environments based on it, require screen to be locked and switched off before session is considered 
locked.

KDE, XFCE and multiple other desktop environments require screen to be just locked for session to be considered inactive.

Deepin (for example) does not get along Timekpr-nExT with screen locking at all, because their implementation differs from major players and is not exactly 
compatible with the FreeDesktop / Gnome standards.

---------------------------------------

##### technical nuances

* when user closes / opens laptops lid multiple times, ```org.freedesktop.login1``` sometimes reports session as inactive despite a user is happily using the 
computer

  * _by default Timekpr-nExT does not account time for inactive sessions, so it's free time for them unless "inactive session tracking" is turned on_

* some Desktop Environments have ```org.freedesktop.ScreenSaver``` exported to DBUS, but it's not fully functional, i.e. ```GetActive``` always reports _"not 
active"_ or there's an error about method not implemeted

  * _this is used for idle time accounting_

* when asking systemd ```org.freedesktop.login1.Manager``` to terminate a single active user session, certain Desktop Environments does not automatically 
switch to login screen

  * _a surprise for unaware user (he is left with black screen and blinking cursor in the corner)_

* after ```org.freedesktop.login1.Manager``` ```TerminateSession``` is called for inactive session and that session is terminated, some Desktop Environments 
switch to login screen even different session for different user is in foreground / active, but the rest of Desktop Environments _"don't blink an eye about 
background session termination"_

  * _a surprise for unaware user_

* some Desktop Environments consider user session to be inactive by setting property ```IdleHint``` in ```org.freedesktop.login1``` session when screen is 
locked, some do the same but only when screen turns off and some do not that all

  * _this is used for idle time accounting_

* systemd ```LockedHint``` is set and used by some Desktop Environments, for some Desktop Environments it's set only when screen is off and some do not use it 
at all

  * _this is used for idle time accounting_

</br>

So, there are inconsistencies and at times it was quite tricky / required workarounds to get the solution to be compatible with most popular Desktop 
Environments at the same functionality level.

</br>

<a name="support"></a>
## How You can help

Quite a lot of time and effort went into making this a reality, so if You appreciate my work, would like to say thanks for making Timekpr-nExT or just want to 
contribute, please do so via PayPal.

The PayPal donations URL (shortened): https://tinyurl.com/yc9x85v2 .

As a matter of fact, I'm starting to look for a replacement of my year 2001 Chicony keyboard with more programming / ergo oriented one which can be used in 
gaming too, like Dygma Raise. I will be happy for any help getting it ;)

</br>

<a name="translate"></a>
Alternatively, You can help to translate Timekpr-nExT in Your language [here](https://translations.launchpad.net/timekpr-next) too.

</br>

<a name="disclaimer"></a>
## Disclaimer

Timekpr-nExT development started because I was not happy with the old Timekpr I brought back to useful state. 
I had complaints from my kid about precision of accounting, session termination behaviour and some others I don't remember anymore :)

So, development was mainly driven by a technical challenge to use better available technologies and giving the best functionality to my kid. 
However, it's not the case anymore for quite a long time (more than a year already). 
My kid has grown up and is rather responsible in his actions, so there is no need to use time restrictions.

That was a long way of saying that I'm not using Timekpr-nExT myself anymore :)

What does that mean, you may ask? Honestly, it changes some things. One thing that changed for sure is that I'm not intentionally proactive in feature 
development. Latest features I introduced were suggested, some even backed, by users! Another thing is that I'm not giving it a long term testing as before 
when my kid used it.

So, if this application is sufficient for your needs, good, consider saying [thanks](#support), if not, suggest features or improvements and if they end up in 
Timekpr-nExT consider saying [thanks](#support) afterwards.

</br>

<a name="bugs"></a>
## Suggestions and bugs

Please register suggestions and bugs [here](https://bugs.launchpad.net/timekpr-next). As for questions, please ask them 
[here](https://answers.launchpad.net/timekpr-next).

_**Please prefix** a title of the bug with ```BETA``` if the bug was found in beta version._

Alternatively suggestions can be sent to me via e-mail ```edzis"replace this with at symbol"inbox"place a dot here"lv```, I'll evaluate their usefulness and 
who knows, they may see a light of the day.

As for bugs: please describe Your issues as precisely as possible including a steps to fully reproduce the issue, if applicable, describe Your setup too, i.e. 
which distribution, version of OS, Desktop Environment are You using, be prepared to send me config and log files (they do not contain anything sensitive, 
except usernames).

If you don't want to register a user in LP, you can send bug reports via e-mail too, but it's NOT the best way to handle them!

I'll do my best to address them as my free time allows.

</br>

Thanks for choosing Timekpr-nExT!
