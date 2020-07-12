#!/bin/bash
# convert debian install file to RPM install file list
grep -v -e '^#' -e '^$' ../debian/install | sed \
-e 's|/$||' -e 's|^\(.\+/\)\(.\+\) \(.\+\)$|\3|g' \
-e 's|\(.\+\)/timekpr/.*$|\1|g' \
-e 's|^\(.*\)$|/\1/*|' \
-e 's|/usr/share/|%{_datadir}/|' \
-e 's|/usr/bin/|%{_bindir}/|' \
-e 's|/etc/|%{_sysconfdir}/|' \
-e 's|/var/lib/|%{_sharedstatedir}/|' \
| sort -u
