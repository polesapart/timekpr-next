%global debug_package %{nil}

Name:             timekpr-next
Version:          0.5.1
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

Requires:         ( gtk3 >= 3.4 )
Requires:         ( polkit )
Requires:         ( python3 )
Requires:         ( python3-dbus or python3-dbus-python )
Requires:         ( python3-gobject )
Requires:         ( python3-psutil )
Requires:         ( ( libindicator-gtk3 and libappindicator-gtk3 ) or ( typelib-1_0-Gtk-3_0 and ( ( libayatana-indicator3-7 and typelib-1_0-AyatanaAppIndicator3-0_1 ) or ( libindicator3-7 and typelib-1_0-AppIndicator3-0_1 ) ) ) )
Requires:         ( gettext )

Requires(post):   ( systemd )
Requires(preun):  ( systemd )
Requires(postun): ( systemd )

%description
Timekpr-nExT is a program that tracks and controls the computer usage
of your user accounts. You can limit their daily usage based on a
timed access duration and configure periods of day when they can or
cannot log in.
.
This may be used for parental control to limit the amount of screen time
a child spends in front of the computer.
.
Please report any bugs to Timekpr-nExT’s bug tracker on Launchpad at:
https://bugs.launchpad.net/timekpr-next

%prep
%setup -q -n %{name}

%build

%install
# remove all root before build
rm -rf $RPM_BUILD_ROOT

# install files
grep -v -e '^#' -e '^$' debian/install | sed -e 's|/$||' -e 's| lib/systemd/| usr/lib/systemd/|g' -e 's|^\(.\+/\)\(.*\) \(.*\)/\?$|mkdir -p %{buildroot}/\3 ; cp \1\2 %{buildroot}/\3|g' | sh -

# install pre/post files
mkdir mkdir -p %{buildroot}/%{_sharedstatedir}/timekpr
%__cp debian/postinst  %{buildroot}/%{_sharedstatedir}/timekpr/%{name}.postinst
%__cp debian/postrm  %{buildroot}/%{_sharedstatedir}/timekpr/%{name}.postrm

# appdata file
install -Dpm 644 resource/appstream/org.timekpr.%{name}.metainfo.xml %{buildroot}%{_datadir}/metainfo/org.timekpr.%{name}.metainfo.xml
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/org.timekpr.%{name}.metainfo.xml

%post
# reload units
systemctl daemon-reload

# post installation
%{_sharedstatedir}/timekpr/%{name}.postinst

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

# package files
%{_bindir}/*
%{_datadir}/applications/*
%{_datadir}/icons/hicolor/128x128/apps/*
%{_datadir}/icons/hicolor/48x48/apps/*
%{_datadir}/icons/hicolor/64x64/apps/*
%{_datadir}/icons/hicolor/scalable/apps/*
#%{_datadir}/locale/cs/LC_MESSAGES/*
#%{_datadir}/locale/de/LC_MESSAGES/*
#%{_datadir}/locale/fr/LC_MESSAGES/*
#%{_datadir}/locale/hu/LC_MESSAGES/*
%{_datadir}/locale/it/LC_MESSAGES/*
%{_datadir}/locale/lv/LC_MESSAGES/*
%{_datadir}/metainfo/*
%{_datadir}/polkit-1/actions/*
%{_datadir}/timekpr
%{_prefix}/lib/python3/dist-packages/timekpr
%{_prefix}/lib/systemd/system/*
%{_sharedstatedir}/timekpr
%{_sysconfdir}/dbus-1/system.d/*
%{_sysconfdir}/logrotate.d/*
%{_sysconfdir}/timekpr
%{_sysconfdir}/xdg/autostart/*

%changelog
* Fri Jan 22 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.1-1.0
- Updated spec file for version 0.5.1, release 8 (BETA)
* Thu Jan 7 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-8.0
- Updated spec file for version 0.5.0, release 8 (STABLE)
* Tue Dec 29 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-7.0
- Updated spec file for version 0.5.0, release 7 (STABLE)
* Thu Dec 17 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-4.0
- Updated spec file for version 0.5.0, release 4 (BETA)
* Tue Dec 1 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-3.0
- Updated spec file for version 0.5.0, release 3 (BETA)
* Wed Nov 18 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-2.0
- Updated spec file for version 0.5.0, release 2 (BETA)
* Sun Nov 1 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.5.0-1.0
- Updated spec file for version 0.5.0 (BETA)
* Sat Oct 31 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.4-1.0
- Updated spec file for version 0.4.4 (STABLE)
* Tue Sep 8 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.3-1.0
- Updated spec file for version 0.4.3 (STABLE)
* Tue Aug 18 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.2-1.0
- Updated spec file for version 0.4.2 (STABLE)
* Wed Jul 15 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.1-1.0
- Updated spec file for version 0.4.1 (STABLE)
* Fri Jul 10 2020 Eduards Bezverhijs <edzis@inbox.lv> - 0.4.0-1.0
- Initial version of the spec file (STABLE)
