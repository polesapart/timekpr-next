#!/bin/bash
# convert debian install file to RPM install file list
grep -v -e '^#' -e '^$' ../debian/install | sort | sed \
-e 's|/\+$||' \
-e 's|^\(.\+/\)\(.\+\) \(.\+\)$|/\3|g' \
-e 's|\(.\+\)\(/timekpr\)/.\+$|\1\2|g' \
-e '/\/timekpr$/! s|$|/*|' \
-e 's|/usr/share/|%{_datadir}/|' \
-e 's|/usr/bin/|%{_bindir}/|' \
-e 's|/usr/|%{_prefix}/|' \
-e 's|/etc/|%{_sysconfdir}/|' \
-e 's|/var/lib/|%{_sharedstatedir}/|' \
-e 's|/lib/systemd/|%{_prefix}/lib/systemd/|' \
| sort -u
