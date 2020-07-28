 [//]: # (https://matteobrusa.github.io/md-styler/?url=https://git.launchpad.net/timekpr-next/plain/README.md)
# Timekpr-nExT
## Keep control of computer usage

Timekpr-nExT, a fresh, simple and easy to use time managing software that helps optimizing time spent at computer for Your subordinates, children or even for Yourself.

The software is targeted at parents or supervisors to optimize / limit time spent at computer as they see fit.
</br></br>

_**This README** is quite large, so I have prepared a guide for You:_

* _a short description of [applications](#applications) with [typical use case](#typicalusecase)_
* _installation / removal [instructions](#installation) for most widely used systems_
* _a short description about [how You can help](#support)_
* _to better understand functionality click on [description of functionality](#details)_
* _to get information on console / file usage click on [additional configuration possibilities](#manualconfig)_
* _information about questions, suggestions and bugs is [here](#bugs)_
</br>

<a name="applications"></a>
</br>
### Applications

Timekpr-nExT has two user facing applications:

* Timekpr-nExT Client application showing the time and notifications to the user, which consists of

 * informational "padlock" icon in they system notification area which is helping with notifications too

 ![Timekpr-nExT icon](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-icon-system-notification-area.png)

 * client application itself which is activated by clicking on the icon and choosing menu "Limits & configuration", it contains more detailed information and some useful configuration options

 ![Timekpr-nExT Client application](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-client.png)

* Timekpr-nExT Administration application - administration application to set time limits for any user in the system as well as configure technical aspects of Timekpr-nExT

![Timekpr-nExT Administration application](https://git.launchpad.net/timekpr-next/plain/resource/screenshots/timekpr-next-screenshot-admin.png)
</br>

<a name="typicalusecase"></a>
</br>
### Typical use case

Let's imagine a situation that Liane had to limit computer time for Cartman because he uses computer way too much to talk to Kyle and Stan _(but not Kenny, because he doesn't have a computer ;-))_ about messing up a day for Mr. Garrison or something along these lines.

So, Liane is thinking to introduce rather flexible time limit within strict time window for working days and holidays.

Timekpr-nExT comes handy, Liane opens Timekpr-nExT Administration application makes configuration as follows:

* choose username "cartman" and switch to "Daily limits" tab

* select first five working days:

 * set intervals from 7:30 - 21:00

 * set time limit to 10 hours

* select last two holidays:

 * set intervals from 7:30 - 22:30

 * set time limit to 13 hours

* press "Apply daily limits" and restrictions are set
</br></br>

By this she achieves flexibility of:

* allowing 10 hours of computer time out of 13 hours 30 minutes of total allowed time frame for working days

* allowing 13 hours of computer time out of 15 hours of total allowed time frame for holidays

* Cartman can not use his computer before 7:30 in the morning and after 21:00 on working days / 22:30 on holidays in the evening
</br></br>

Typical setup is rather simple and easy, there are (of course) more to it, please read on [Detailed information](#details), if You're interested.
</br>

<a name="installation"></a>
</br>
## Installation / removal

First step to start using Timekpr-nExT is to install it, right? :-)

Basically there are two versions - beta and stable, usually they are not that different, but beta comes out earlier, especially when changes in upcoming version are larger.

The installation instructions are easy as well (I know that one can do that in GUI, but terminal is just simply faster :-)), just paste these lines in terminal and You're set.
</br></br>

### Ubuntu & co (via PPA)
Timekpr-nExT is available in my PPA (Personal Package Archive) for Ubuntu and compatible distributions.

#### Stable
##### Install
```
sudo add-apt-repository ppa:mjasnik/ppa
sudo apt-get update
sudo apt-get install timekpr-next
```
##### Remove
```
sudo apt-get remove --purge timekpr-next
```

#### Beta
##### Install
```
sudo add-apt-repository ppa:mjasnik/ppa
sudo apt-get update
sudo apt-get install timekpr-next-beta
```
##### Remove
```
sudo apt-get remove --purge timekpr-next-beta
```
</br></br>

### ArchLinux & Manjaro (via AUR)
Timekpr-nExT is available in AUR (ArchLinux User Reository) for ArchLinux and Manjaro.

_Note: please choose Your favorite AUR helper, if that differs from mine._

#### Stable
##### Install
```
yay -S timekpr-next
```
##### Remove
```
sudo pacman -Rdd timekpr-next
```

#### Beta
##### Install
```
sudo pacman -Rdd timekpr-next-git
```
##### Remove
```
sudo pacman -Rdd timekpr-next-git
```

_**Note**: special thanks goes to SanskritFritz from ArchLinux community who was not only one of the first beta testers and active users, but he maintains said packages too._
</br></br>

### Fedora and openSUSE
Recently I created packages for Fedora 32+ and openSUSE Leap 15.2+ and pre-build packages are available.

Please read more about installation and removal [here](https://launchpad.net/timekpr-next/+announcement/27532).
</br></br>

### Debian
Until recently there was no easy way of using Timekpr-nExT in Debian, but thanks to Sim (smntov) and Anthony Fok (foka), Timekpr-nExT is / will be available in Debian as native installation via Software Center.

To install or un-install Timekpr-nExT, please search for it in Software Center.
</br></br>

### Compatibility
I'm developing Timekpr-nExT to be compatible with most Desktop Environments, I have somewhere around 20 VMs where I test bigger changes, but I can / will not test everything in the open.

I have tested that KDE, Gnome, Cinnamon, MATE, XFCE works in Ubuntu compatible OS, Manjaro / ArchLinux (which are my distributions of choice) and Debian. Recently I started testing in Fedora and openSUSE too.

Please read [nuances](#quirks) section for more information.

If You have an issue with Timekpr-nExT, please read [this](#bugs) and file a bug.
</br></br>

<a name="support"></a>
</br>
## How You can help

Quite a lot of time and effort went into making this a reality, so if You would like to say thanks for making Timekpr-nExT or just want to contribute, please do so via PayPal: https://tinyurl.com/yc9x85v2 .

Alternatively, You can help to translate Timekpr-nExT in Your language [here](https://translations.launchpad.net/timekpr-next) too.
</br></br>

<a name="details"></a>
</br>
## Detailed information

This section contains information about major / most important features of Timekpr-nExT. Section is meant to deep dive into functionality without tehnical details.

<a name="quirks"></a>
</br>
### Quirks
Linux distributions (i.e. Ubuntu, Fedora, Mint, ...) ecosystem is large, nice, diverse and all those good things, but not everything there adheres to the same standards, so naturally there are some differences here and there, which affects Timekpr-nExT looks and/or functionality.

I'll add notes (i.e. _Note: ..._) to highlight differences in functionality for the descriptions below, so users are fully aware of what to expect.
</br></br>

### Description of functionality

This section describes what Timekpr-nExT does rather than details every configuration option.

**Please note** that to describe configuration options, Timekpr-nExT heavily relies on "tooltip / hint" functionality, please navigate mouse over to any configuration option and read a description, it usually helps to understand it better.
</br></br>

#### Information representation to user

* there is an icon in system notification area, which takes care of presenting information about time to the user

 _**Note**: due to differences in standards not every Desktop Environment shows the same information_

 _Gnome3 / Unity / XFCE / etc. shows icon as well as detailed label (i.e. actual time left)_

 * _on some distributions which ship Gnome3, specific extension has to be anabled for icon to be shown in the first place, usually extension is provided by distribution, in case it's not, please install [this](https://extensions.gnome.org/extension/615/appindicator-support/) manually_

 * _in the future Gnome3 will possibly remove [status icon](https://wiki.gnome.org/Initiatives/StatusIconMigration/Guidelines) functionality, when the time comes, I'll try to figure out what to do about it _

 _KDE / Deepin / etc. shows only the icon, however, hovering mouse over the icon, actual time left is revealed_

* information about time left and time limit changes, is communicated to user as notifications (see the very first screenshot up there ;-))

 * _Note: there are very rare cases when Linux distribution does not support notifications the way Timekpr-nExT expects it, in that case, one is out of luck_
</br></br>

#### Robust time accounting
* time accounting is done every 3 secs (default) in memory and accounted time is saved permanently every 30 secs (default)

* in multi-user setups when user is not active, i.e. other user is at the computer (which is achieved by user switching functionality), time is not accounted

 * there is a configuration option to account time for inactive sessions


* when computer is put to sleep, time spent is not accounted

 * time spent sleeping is not accounted as activity, but it's effective only if computer was put to sleep for more than 60 seconds


* when screen is locked, time is not accounted

 _**Note**: due to differences in standards not every Desktop Environment works equally well with time accounting for locked screen_

 _* Gnome3 and solutions based on it, requires not only that screen is locked, but has to turn off before screen is considered locked_

 _* KDE, XFCE and multiple other Desktop Environments require only screen to be locked_

 _* Deepin (for example) does not get along Timekpr-nExT with screen locking easily, because their implementation vastly differs from major players_


* time accounting can be done for certain types of sessions:

 * by default time is accounted all graphical sessions

 * by default console sessions (i.e. Ctrl + Alt + Fn logins) are not accounted

 * _Note: there is a configuration option to change accountable session types_
</br></br>

#### Robust time limit configuration

* allowed time frame can be configured in intervals (including minutes):

 * it's possible to have more than one time interval per day, example: 7:30 - 13:30 and 17:45 - 22:15 _(user will be be able to use computer before 7:30, between 13:30 and 17:45 and after 22:15)_

 * please note that it's not possible to have more than one interval per hour, for example, it's not possible to have setup like this, 15:00 - 16:15 and 16:45 - 18:00 at the same time

   * _this is a design feature and not a bug, the the rationale is that Timekpr-nExT itself is a distraction to the user and micromanaging users was not a design goal_


* user will be able to use computer across midnight without being kicked out:

 * to enable this this, next day's allowed hours had to include at least first hour (example: previous day .. - 24:00 and next day 00:00 - 01:00)

 * this example allows computer to be used continuously across midnight until 1:00 in the morning


* it's possible to exclude certain sessions from being accounted

 * for example TTY sessions are not accounted by default, please be careful with this configuration


* it's possible to exclude certain users from being accounted

 * - for example, lightdm, gdm, ... users are not accounted by default, please be aware that this means they are not even considered as users, they are completely ignored, please do not put actual usernames here, just some system users, if needed


* it's possible to limit time allowance per week and month separately

 * in addition to daily allowances, global week and month allowances can be set
</br></br>

_**Note**: please be aware that all configured limits are taken into account simultaneously, so the time available to the user is the least of limits_
</br></br></br></br>

## Short and very technical overview

**Warning**: this section is **very technical** and has no information that regular users of Timekpr-nExT would (possibly) want to know.
</br></br>

Timekpr-nExT is built with technologies which heavily use D-BUS for it's interaction with the system. Not only it uses interfaces provided by various solutions, it exposes own interfaces to D-BUS too.
It allows Timekpr-nExT to be integrated into any client application or control panel which supports D-BUS interactions.
</br></br>

### Interfaces used
The main interface used is systemd's [login1](https://www.freedesktop.org/wiki/Software/systemd/logind/) session management interface, without it Timekpr-nExT will not work.

It tries to use FreeDesktops screensaver [interfaces _(better source needed)_](https://people.freedesktop.org/~hadess/idle-inhibition-spec/ch05.html) as well as notification [interfaces](https://specifications.freedesktop.org/notification-spec/latest/ar01s09.html) too. In case FreeDesktop screensaver interfaces are not available, it tries to use [Gnome's](https://people.gnome.org/~mccann/gnome-screensaver/docs/gnome-screensaver.html).

Timekpr-nExT makes connections to D-BUS objects, they are cached and during execution, it mostly just calls.
</br>

<a name="manualconfig"></a>
</br>
### Additional configuration possibilities

In addition to graphical applications, Timekpr-nExT still can be configured via CLI (Command Line Interfaces) and actual config files by hand.

For CLI usage, please open Your terminal emulator of choice (i.e. Gnome Terminal / Konsole / XTerm) and type ```timekpra --help```, it will print all You need to know ;-)

Graphical applications and CLI apply configuration right away, but if config files are edited manually, configuration is read and applied at save intervals (every 30 sec).
</br></br>

_**Note**: please be aware that configuration files are structured in particular way, have internal representation of values and one can break the configuration if not being careful. You have been warned :)_

_**Note**: if configuration files are borked, e.g. Timekpr-nExT can not interpret them properly, it will try to salvage options it can and it will recreate the config file with defaults for damaged options._
</br></br>

#### Configuration files
* Timekpr-nExT main configuration file: ```/etc/timekpr/timekpr.conf```
* User configuration files (one per user): ```/var/lib/timekpr/config/timekpr.*.conf```
* User control files (one per user): ```/var/lib/timekpr/work/timekpr.*.conf```
* Client configuration files: ```$HOME/.config/timekpr/timekpr.conf```
</br></br>

### Oddities
When I started designing / developing Timekpr-nExT I was pretty much sure how to implement desired functionality as I have _looked into_ standards and _tested particular implementation_ in Ubuntu 16.04 (Unity) and it's clear what to expect, i.e. standards are standards and every implementation which uses them, should be roughly the same.

Roughly it was ;-) Most of the time, everything worked perfectly, but for certain functionality every Desktop Environment has it's own quirks, maybe not using all bits or maybe it's just buggy implementation.

This section will contain these oddities / differences in implementations as far as Timekpr-nExT development is concerned. If You find odd why things happen or not happen the way You expect, maybe here's an answer ;-)
</br></br>

Here are some examples:

* when user closes / opens laptops lid multiple times, ```org.freedesktop.login1``` sometimes reports session as inactive despite a user is happily using the computer

  * _by default Tmekpr-nExT does not account time for inactive sessions, so it's free time for them unless "inactive session tracking" is turned on_


* some Desktop Environments have ```org.freedesktop.ScreenSaver``` exported to D-BUS, but it's not fully functional, i.e. ```GetActive``` always reports _"not active"_ or there's an error about method not implemeted

  * _this is used for idle time accounting_


* when asking systemd ```org.freedesktop.login1.Manager``` to terminate a single active user session, certain Desktop Environments does not automatically switch to login screen

  * _a surprise for unaware user (he is left with black screen and blinking cursor in the corner)_


* after ```org.freedesktop.login1.Manager``` ```TerminateSession``` is called for inactive session and that session is terminated, some Desktop Environments switch to login screen even different session for different user is in foreground / active, but the rest of Desktop Environments _"don't blink an eye about background session termination"_

  * _a surprise for unaware user_


* some Desktop Environments consider user session to be inactive by setting property ```IdleHint``` in ```org.freedesktop.login1``` session when screen is locked, some do the same but only when screen turns off and some do not that all

  * _this is used for idle time accounting_


* systemd ```LockedHint``` is set and used by some Desktop Environments, for some Desktop Environments it's set only when screen is off and some do not use it at all

  * _this is used for idle time accounting_

</br>
So, there are inconsistencies and at times it was quite tricky / required workarounds to get the solution to be compatible with most popular Desktop Environments at the same functionality level.
</br>

<a name="bugs"></a>
</br>
## Suggestions and bugs

Please register suggestions and bugs [here](https://bugs.launchpad.net/timekpr-next), alternatively suggestions can be sent to me via e-mail. As for questions, please ask them [here](https://answers.launchpad.net/timekpr-next).

For bugs, please describe Your setup, i.e. which distribution, version of OS, Desktop Environment are You using, be prepared to send me config and log files (they do not contain anything sensitive, except usernames).

I'll do my best to address them as my free time allows.

</br></br>
Thanks for choosing Timekpr-nExT!
