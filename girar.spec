Name: girar
Version: 0.5
Release: alt1

Summary: git.alt server engine
License: GPLv2+
Group: System/Servers
Packager: Dmitry V. Levin <ldv@altlinux.org>

Source: %name-%version.tar

Requires(pre): shadow-utils
# due to "enable -f /usr/lib/bash/lockf lockf"
Requires: bash-builtin-lockf >= 0:0.2
# due to post-receive hook
Requires: git-core >= 0:1.5.1
# due to girar-task-add
Requires: gear
# due to gb-sh-rpmhdrcache
Requires: memcached rpmhdrmemcache
# due to cron jobs
Requires: stmpclean
# due to "locale -m"
Requires: glibc-i18ndata

Obsoletes: girar-builder

BuildRequires: perl(RPM.pm) perl(Date/Format.pm)

%description
This package contains server engine initially developed for git.alt,
including administration and user utilities, git hooks, email
subscription support and config files.

%prep
%setup

%build
%make_build

%install
%makeinstall_std
echo 0 >%buildroot/var/lib/girar/tasks/.max-task-id
mksock %buildroot/var/run/girar/{acl,depot,repo}/socket
mkdir -p %buildroot/var/spool/cron
touch %buildroot/var/spool/cron/{bull,cow}

mkdir -p %buildroot/usr/libexec/girar-builder
cp -a gb/gb-* gb/remote gb/template %buildroot/usr/libexec/girar-builder/
%add_findreq_skiplist /usr/libexec/girar-builder/remote/*

%check
cd gb/tests
./run

%pre
%_sbindir/groupadd -r -f girar
%_sbindir/groupadd -r -f girar-users
%_sbindir/groupadd -r -f girar-admin
%_sbindir/groupadd -r -f tasks
for u in acl depot repo; do
	%_sbindir/groupadd -r -f $u
	%_sbindir/useradd -r -g $u -G girar -d /var/empty -s /dev/null -c 'Girar $u robot' -n $u ||:
done
for u in bull cow; do
	%_sbindir/groupadd -r -f $u
	%_sbindir/useradd -r -g $u -G girar,tasks -d /var/lib/girar/$u -c "Girar $u robot" -n $u ||:
done

%post
%post_service girar-proxyd-acl
%post_service girar-proxyd-depot
%post_service girar-proxyd-repo
%_sbindir/girar-make-template-repos
if [ $1 -eq 1 ]; then
	if grep -Fxqs 'EXTRAOPTIONS=' /etc/sysconfig/memcached; then
		sed -i 's/^EXTRAOPTIONS=$/&"-m 2048"/' /etc/sysconfig/memcached
	fi
	if grep -Fxqs 'AllowGroups wheel users' /etc/openssh/sshd_config; then
		sed -i 's/^AllowGroups wheel users/& girar-users/' /etc/openssh/sshd_config
	fi
	crontab -u bull - <<-'EOF'
	#1	*	*	*	*	/usr/libexec/girar-builder/gb-toplevel-commit sisyphus
	EOF
	crontab -u cow - <<-'EOF'
	#1	*	*	*	*	/usr/libexec/girar-builder/gb-toplevel-build sisyphus
	40	7	*	*	*	/usr/sbin/stmpclean -t 14d $HOME/.cache
	EOF
fi

%preun
%preun_service girar-proxyd-acl
%preun_service girar-proxyd-depot
%preun_service girar-proxyd-repo

%files
%config(noreplace) %attr(400,root,root) /etc/sudoers.d/girar
%config(noreplace) /etc/sisyphus_check/check.d/*
/etc/girar/
/usr/libexec/girar/
/usr/libexec/girar-builder/
%_datadir/girar/
%_initdir/girar-proxyd-*
%attr(700,root,root) %_sbindir/*

%doc LICENSE TASK gb/conf/

# all the rest should be listed explicitly
%defattr(0,0,0,0)

%dir %attr(755,root,root) /var/lib/girar/
%dir %attr(2775,root,acl) /var/lib/girar/acl/
%dir %attr(770,root,bull) /var/lib/girar/bull/
%dir %attr(770,root,cow) /var/lib/girar/cow/
%dir %attr(770,root,cow) /var/lib/girar/cow/.cache/
%dir %attr(755,root,root) /var/lib/girar/depot/
%dir %attr(770,root,depot) /var/lib/girar/depot/.tmp/
%dir %attr(775,root,depot) /var/lib/girar/depot/??/
%dir %attr(755,root,root) /var/lib/girar/repo/
%dir %attr(755,root,root) /var/lib/girar/people/
%dir %attr(775,root,bull) /var/lib/girar/gears/
%dir %attr(775,root,bull) /var/lib/girar/srpms/

%dir %attr(3775,bull,tasks) /var/lib/girar/tasks/
%dir %attr(3775,root,bull) /var/lib/girar/tasks/archive/
%dir %attr(775,root,bull) /var/lib/girar/tasks/archive/*
%dir %attr(755,root,root) /var/lib/girar/tasks/index/
%config(noreplace) %attr(664,bull,tasks) /var/lib/girar/tasks/.max-task-id

%dir %attr(750,root,girar) /var/lib/girar/email/
%dir %attr(755,root,root) /var/lib/girar/email/*

%dir %attr(750,root,girar) /var/lock/girar/
%dir %attr(770,root,bull) /var/lock/girar/bull/
%dir %attr(770,root,cow) /var/lock/girar/cow/

%dir %attr(750,root,girar) /var/run/girar/
%dir %attr(710,root,girar) /var/run/girar/acl/
%dir %attr(710,root,bull) /var/run/girar/depot/
%dir %attr(710,root,bull) /var/run/girar/repo/
%ghost %attr(666,root,root) /var/run/girar/*/socket

%config(noreplace) %ghost %attr(600,bull,crontab) /var/spool/cron/bull
%config(noreplace) %ghost %attr(600,cow,crontab) /var/spool/cron/cow

%changelog
* Wed Nov 21 2012 Dmitry V. Levin <ldv@altlinux.org> 0.5-alt1
- Imported girar-builder.

* Fri Nov 16 2012 Dmitry V. Levin <ldv@altlinux.org> 0.4-alt1
- Imported gb-depot.

* Thu Dec 11 2008 Dmitry V. Levin <ldv@altlinux.org> 0.3-alt1
- Added task subcommands.

* Mon Jun 16 2008 Dmitry V. Levin <ldv@altlinux.org> 0.2-alt1
- Rewrote hooks using post-receive.

* Tue Nov 21 2006 Dmitry V. Levin <ldv@altlinux.org> 0.1-alt1
- Specfile cleanup.

* Fri Nov 17 2006 Alexey Gladkov <legion@altlinux.ru> 0.0.1-alt1
- Initial revision.
