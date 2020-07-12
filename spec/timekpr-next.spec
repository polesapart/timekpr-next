%global debug_package %{nil}

Name:             timekpr-next
Version:          0.4.0
Release:          1.0%{?dist}
Summary:          Keep control of computer usage
Group:            System Environment/Daemons
License:          GPLv3
URL:              https://launchpad.net/timekpr-next

Source0:          https://launchpad.net/%{name}/stable/%{version}/+download/%{name}-%{version}.tar.gz

BuildRoot:        %{_tmppath}/%{name}-%{version}-build

BuildRequires:    ( python3 )
BuildRequires:    ( desktop-file-utils )
BuildRequires:    ( libappstream-glib or appstream-glib )
BuildRequires:    ( systemd )
BuildRequires:    ( sed )
BuildRequires:    ( grep )

Requires:         ( gtk3 >= 3.12 )
Requires:         ( python3 )
Requires:         ( python3-dbus or python3-dbus-python )
Requires:         ( python3-gobject )
Requires:         ( ( libindicator-gtk3 and libappindicator-gtk3 ) or ( libindicator3-7 and typelib-1_0-Gtk-3_0 and typelib-1_0-AppIndicator3-0_1 ) )
Requires:         ( gettext )

Requires(post):   ( systemd )
Requires(preun):  ( systemd )
Requires(postun): ( systemd )

%description
This program will track and control the computer usage of
your user accounts. You can limit their daily usage based
on a timed access duration and configure periods of day
when they can or cannot log in.
.
Any bugs should be reported to our bug tracker:
https://bugs.launchpad.net/timekpr-next/+bugs

%prep
%setup -q -n %{name}

%build

%install
# remove all root before build
rm -rf $RPM_BUILD_ROOT

# install files
grep -v -e '^#' -e '^$' debian/install | sed -e 's|/$||' -e 's|^\(.\+/\)\(.*\) \(.*\)/\?$|mkdir -p %{buildroot}/\3 ; cp \1\2 %{buildroot}/\3|g' | sh -

# install pre/post files
mkdir mkdir -p %{buildroot}/%{_sharedstatedir}/timekpr
%__cp debian/postinst  %{buildroot}/%{_sharedstatedir}/timekpr/%{name}.postinst
%__cp debian/postrm  %{buildroot}/%{_sharedstatedir}/timekpr/%{name}.postrm

# appdata file
install -Dpm 0644 spec/%{name}.appdata.xml %{buildroot}%{_datadir}/appdata/%{name}.appdata.xml
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/appdata/%{name}.appdata.xml

%post
# post installation
if [ $1 == 1 ]
then
    %{_sharedstatedir}/timekpr/%{name}.postinst
fi

# update mime / desktop
update-mime-database %{_datadir}/mime &> /dev/null || :
update-desktop-database &> /dev/null || :

%preun
# before removal
if [ $1 == 0  ];
then
    %{_sharedstatedir}/timekpr/%{name}.postrm
fi

%postun
# update mime / desktop
update-mime-database %{_datadir}/mime &> /dev/null || :
update-desktop-database &> /dev/null || :

%files
# specific purpose files
%defattr(-,root,root,-)
%doc debian/changelog debian/copyright
%config /etc/timekpr/timekpr.conf
%{_datadir}/appdata/%{name}.appdata.xml

# package files
%{_bindir}/*
%{_datadir}/*
%{_datadir}/applications/*
%{_datadir}/icons/hicolor/64x64/apps/*
%{_datadir}/icons/hicolor/scalable/apps/*
%{_datadir}/locale/cs/LC_MESSAGES/*
%{_datadir}/locale/de/LC_MESSAGES/*
%{_datadir}/locale/fr/LC_MESSAGES/*
%{_datadir}/locale/hu/LC_MESSAGES/*
%{_datadir}/locale/it/LC_MESSAGES/*
%{_datadir}/locale/lv/LC_MESSAGES/*
%{_datadir}/polkit-1/actions/*
%{_datadir}/pyshared/*
%{_sharedstatedir}/*
%{_sysconfdir}/dbus-1/system.d/*
%{_sysconfdir}/logrotate.d/*
%{_sysconfdir}/systemd/system/*
%{_sysconfdir}/timekpr/*
%{_sysconfdir}/xdg/autostart/*

%changelog
* Fri Jul 10 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.0-1.0
- Initial version of the spec file
