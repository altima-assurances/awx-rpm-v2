%define  debug_package %{nil}
%define _prefix /opt/awx-rpm
%define _mandir %{_prefix}/share/man
%global __os_install_post %{nil}

%define service_user awx
%define service_group awx
%define service_homedir /var/lib/tower
%define service_logdir /var/log/tower
%define service_configdir /etc/tower

Summary: Ansible AWX
Name: awx-rpm
Version: ¤VERSION¤
Release: 3%{dist}
Source0: awx-¤VERSION¤.tar.gz
Source1: settings.py-%{version}
Source2: awx-receiver.service-%{version}
Source3: awx-dispatcher.service-%{version}
Source4: awx-wsbroadcast.service-%{version}
Source6: awx-daphne.service-%{version}
Source7: awx-web.service-%{version}
Source20: awx-receptor.service-%{version}
Source21: awx-receptor-hop.service-%{version}
Source22: awx-receptor-worker.service-%{version}
Source30: receptor.conf-%{version}
Source31: receptor-hop.conf-%{version}
Source32: receptor-worker.conf-%{version}
#Source8: nginx.conf.example
#Source9: awx-create-venv
#Source10: awx-rpm-logo.svg
#Source11: awx.service
Patch0: patch-%{version}.patch
License: GPLv3
Group: AWX
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}.buildroot
Vendor: AWX
Prefix: %{_prefix}
AutoReqProv: false

BuildRequires: make python3 python3-devel nodejs npm gettext git python3-build rsync
¤BUILDREQUIRES¤

Requires: python3 nodejs npm gettext git nginx redis xmlsec1-openssl xmlsec1 podman
¤REQUIRES¤

%{?systemd_requires}

%description
%{summary}

%prep
%setup -q -n awx
%patch0 -p0

%build
git checkout devel
git checkout %{version}

%install
echo 'node-options="--openssl-legacy-provider"' >> awx/ui/.npmrc
GIT_BRANCH=%{version} VERSION=%{version} python3 -m build -s
make ui-release
mkdir -p /var/log/tower
python3 manage.py collectstatic --clear --noinput
mkdir -p %{buildroot}%{_prefix}
for i in `find -type f |grep mappings.wasm`; do
	echo "Removing $i"
	rm -f $i
done
cp dist/awx-*.tar.gz %{buildroot}%{_prefix}/
pushd %{buildroot}%{_prefix}
tar zxvf awx-*.tar.gz
rm awx-*.tar.gz
mv awx-*/* .
rm -rf awx-*
pip3 install --root=%{buildroot}/ .
popd
sed -i "s|/builddir.*.x86_64||g" $RPM_BUILD_ROOT/usr/bin/awx-manage
pushd %{buildroot}/usr/lib/python3.9/site-packages/
for i in `find -type f`; do
	sed -i "s|/builddir.*.x86_64||g" $i
done
popd

rsync -avr awx/ $RPM_BUILD_ROOT/opt/awx-rpm/awx/
cp -a /var/lib/awx/public/static /opt/awx-rpm/

# Collect django static
mkdir -p /var/log/tower/
mkdir -p %{buildroot}%{service_homedir}
mkdir -p %{buildroot}%{service_logdir}
mkdir -p %{buildroot}%{_prefix}/bin
mkdir -p %{buildroot}%{service_configdir}
echo %{version} > %{buildroot}%{service_homedir}/.tower_version

cp %{_sourcedir}/settings.py-%{version} %{buildroot}%{service_configdir}/settings.py
rsync -avr /var/lib/awx/public %{buildroot}%{_prefix}/public

mkdir -p %{buildroot}/usr/lib/systemd/system
# awx-channels-worker awx
for service in awx-web awx-wsbroadcast awx-daphne awx-dispatcher awx-receiver awx-receptor awx-receptor-hop awx-receptor-worker; do
    cp %{_sourcedir}/${service}.service-%{version} %{buildroot}/usr/lib/systemd/system/${service}.service
done

mkdir -p %{buildroot}/etc/receptor

for receptor in receptor receptor-hop receptor-worker; do
	cp %{_sourcedir}/$receptor.conf-%{version} %{buildroot}/etc/receptor/$receptor.conf
done

# Create Virtualenv folder
mkdir -p %{buildroot}%{service_homedir}/venv

# Install docs
#cp %{_sourcedir}/nginx.conf.example ./

# Install VENV Script
#cp %{_sourcedir}/awx-create-venv $RPM_BUILD_ROOT/opt/rh/rh-python36/root/usr/bin/
#mkdir -p $RPM_BUILD_ROOT/usr/bin/

#cp %{_sourcedir}/awx-rpm-logo.svg $RPM_BUILD_ROOT/opt/awx/static/assets/awx-rpm-logo.svg
#mv $RPM_BUILD_ROOT/opt/awx/static/assets/logo-header.svg $RPM_BUILD_ROOT/opt/awx/static/assets/logo-header.svg.orig
#mv $RPM_BUILD_ROOT/opt/awx/static/assets/logo-login.svg $RPM_BUILD_ROOT/opt/awx/static/assets/logo-login.svg.orig
#ln -s /opt/awx/static/assets/awx-rpm-logo.svg $RPM_BUILD_ROOT/opt/awx/static/assets/logo-header.svg
#ln -s /opt/awx/static/assets/awx-rpm-logo.svg $RPM_BUILD_ROOT/opt/awx/static/assets/logo-login.svg
mkdir -p $RPM_BUILD_ROOT/etc/nginx/conf.d/
cp tools/docker-compose/nginx.vh.default.conf $RPM_BUILD_ROOT/etc/nginx/conf.d/awx-rpm.conf
echo "map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}" >> $RPM_BUILD_ROOT/etc/nginx/conf.d/awx-rpm.conf

sed -i "s|/var/lib/awx/|/opt/awx-rpm/|g" $RPM_BUILD_ROOT/etc/nginx/conf.d/awx-rpm.conf

%pre
/usr/bin/getent group %{service_group} >/dev/null || /usr/sbin/groupadd --system %{service_group}
/usr/bin/getent passwd %{service_user} >/dev/null || /usr/sbin/useradd --no-create-home --system -g %{service_group} --home-dir %{service_homedir} -s /bin/bash %{service_user}
/usr/sbin/usermod -s /bin/bash %{service_user}

%post
#%if 0%{?el7}
#%systemd_post awx-cbreceiver
#%systemd_post awx-dispatcher
#%systemd_post awx-channels-worker
#%systemd_post awx-daphne
#%systemd_post awx-web
#%endif
#ln -sfn /opt/rh/rh-python36/root /var/lib/awx/venv/awx

%preun
#%if 0%{?el7}
#%systemd_preun awx-cbreceiver
#%systemd_preun awx-dispatcher
#%systemd_preun awx-channels-worker
#%systemd_preun awx-daphne
#%systemd_preun awx-web
#%endif

%postun
#%if 0%{?el7}
#%systemd_postun awx-cbreceiver
#%systemd_postun awx-dispatcher
#%systemd_postun awx-channels-worker
#%systemd_postun awx-daphne
#%systemd_postun awx-web
#%endif

%clean

%files
%defattr(0644, awx, awx, 0755)
#%doc nginx.conf.example
%attr(0755, root, root) /usr/bin/awx-manage
#%attr(0755, root, root) /opt/rh/rh-python36/root/usr/bin/awx-create-venv
#/usr/bin/awx-create-venv
%attr(0755, root, root) /usr/lib/systemd/system/*.service
%attr(0755, root, root) /usr/lib/python3.9/site-packages/awx*
%attr(0755, awx, awx) %{_prefix}
%dir %attr(0750, %{service_user}, %{service_group}) %{service_homedir}
%dir %attr(0750, %{service_user}, %{service_group}) %{service_homedir}/venv
%{service_homedir}/.tower_version
%dir %attr(0770, %{service_user}, %{service_group}) %{service_logdir}
%config %{service_configdir}/settings.py
/etc/nginx/conf.d/awx-rpm.conf
#/usr/bin/ansible-tower-service
#/usr/bin/ansible-tower-setup
#/usr/bin/awx-python
#/usr/bin/failure-event-handler
#/usr/share/awx
#/usr/share/sosreport/sos/plugins/tower.py
#/var/lib/awx/favicon.ico
#/var/lib/awx/wsgi.py


%if 0%{?el7}
%attr(0644, root, root) %{_unitdir}/awx-cbreceiver.service
%attr(0644, root, root) %{_unitdir}/awx-dispatcher.service
%attr(0644, root, root) %{_unitdir}/awx-channels-worker.service
%attr(0644, root, root) %{_unitdir}/awx-daphne.service
%attr(0644, root, root) %{_unitdir}/awx-web.service
%attr(0644, root, root) %{_unitdir}/awx.service
%endif

%changelog
* Mon Feb 13 2023 22:55:34 +0000 Martin Juhl <m@rtinjuhl.dk> 21.11.0
- New version build: 21.11.0

