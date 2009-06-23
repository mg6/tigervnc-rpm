Name:		tigervnc
Version:	0.0.91
Release:	0.13%{?dist}
Summary:	A TigerVNC remote display system

Group:		User Interface/Desktops
License:	GPLv2+
URL:		http://www.tigervnc.com

Source0:	%{name}-%{version}.tar.gz
Source1:	vncserver.init
Source2:	vncserver.sysconfig
Source6:	vncviewer.desktop
Source7:	xorg-x11-server-source-1.6.1.901-5.fc11.x86_64.rpm
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	libX11-devel, automake, autoconf, libtool, gettext, cvs
BuildRequires:	libXext-devel, xorg-x11-server-source, libXi-devel
BuildRequires:	xorg-x11-xtrans-devel, xorg-x11-util-macros, libXtst-devel
BuildRequires:	libdrm-devel, libXt-devel, pixman-devel libXfont-devel
BuildRequires:	libxkbfile-devel, openssl-devel, libpciaccess-devel
BuildRequires:	mesa-libGL-devel, libXinerama-devel, ImageMagick
BuildRequires:  freetype-devel
BuildRequires:	desktop-file-utils

%ifarch %ix86
BuildRequires: nasm
%endif


Requires(post):	coreutils	
Requires(postun):coreutils	

Provides:	vnc = 4.1.3-2, vnc-libs = 4.1.3-2
Obsoletes:	vnc < 4.1.3-2, vnc-libs < 4.1.3-2
Provides:	tightvnc = 1.5.0-0.15.20090204svn3586
Obsoletes:	tightvnc < 1.5.0-0.15.20090204svn3586

Patch0:		tigervnc-102434.patch
Patch4:		tigervnc-cookie.patch
Patch8:		tigervnc-viewer-reparent.patch
Patch9:		tigervnc10-rh495457.patch

%description
Virtual Network Computing (VNC) is a remote display system which
allows you to view a computing 'desktop' environment not only on the
machine where it is running, but from anywhere on the Internet and
from a wide variety of machine architectures.  This package contains a
client which will allow you to connect to other desktops running a VNC
server.

%package server
Summary:	A TigerVNC server
Group:		User Interface/X
Provides:	vnc-server = 4.1.3-2, vnc-libs = 4.1.3-2
Obsoletes:	vnc-server < 4.1.3-2, vnc-libs < 4.1.3-2
Provides:	tightvnc-server = 1.5.0-0.15.20090204svn3586
Obsoletes:	tightvnc-server < 1.5.0-0.15.20090204svn3586
Requires(post):	chkconfig
Requires(preun):chkconfig
Requires(preun):initscripts
Requires(postun):initscripts

# Check you don't reintroduce #498184 again
Requires:	xorg-x11-fonts-misc

%description server
The VNC system allows you to access the same desktop from a wide
variety of platforms.  This package is a TigerVNC server, allowing
others to access the desktop on your machine.

%ifnarch s390 s390x
%package server-module
Summary:	TigerVNC module to Xorg
Group:		User Interface/X
Provides:	vnc-server = 4.1.3-2, vnc-libs = 4.1.3-2
Obsoletes:	vnc-server < 4.1.3-2, vnc-libs < 4.1.3-2
Provides:	tightvnc-server-module = 1.5.0-0.15.20090204svn3586
Obsoletes:	tightvnc-server-module < 1.5.0-0.15.20090204svn3586
Requires:	xorg-x11-server-Xorg
%endif

%description server-module
This package contains libvnc.so module to X server, allowing others
to access the desktop on your machine.

%prep
%setup -q -n %{name}-%{version}

rpm2cpio %{SOURCE7} > cpio
cpio -id < cpio

cp -r usr/share/xorg-x11-server-source/* unix/xserver
pushd unix/xserver
for all in `find . -type f -perm -001`; do
	chmod -x "$all"
done
patch -p1 -b --suffix .vnc < ../xserver16.patch
popd


%patch0 -p1 -b .102434
%patch4 -p1 -b .cookie
%patch8 -p1 -b .viewer-reparent
%patch9 -p0 -b .rh495457

# Use newer gettext
sed -i 's/AM_GNU_GETTEXT_VERSION.*/AM_GNU_GETTEXT_VERSION([0.17])/' \
	unix/configure.ac

%build
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$CFLAGS"

pushd unix
autoreconf -fiv
%configure \
	--disable-static

make %{?_smp_mflags}
popd

pushd unix/xserver
autoreconf -fiv
%configure \
	--disable-xorg --disable-xnest --disable-xvfb --disable-dmx \
	--disable-xwin --disable-xephyr --disable-kdrive --with-pic \
	--disable-static \
	--disable-composite \
	--with-default-font-path="catalogue:%{_sysconfdir}/X11/fontpath.d,built-ins" \
	--with-fontdir=%{_datadir}/X11/fonts \
	--with-xkb-output=%{_localstatedir}/lib/xkb \
	--enable-install-libxf86config \
	--disable-dri2 \
	--enable-glx \
	--disable-config-dbus \
	--disable-config-hal \
	--with-dri-driver-path=%{_libdir}/dri

make %{?_smp_mflags}
popd

# Build icons
pushd media
make
popd

%install
rm -rf $RPM_BUILD_ROOT
pushd unix
make install DESTDIR=$RPM_BUILD_ROOT
popd

pushd unix/xserver/hw/vnc
make install DESTDIR=$RPM_BUILD_ROOT
popd

# Install Xvnc as service
mkdir -p $RPM_BUILD_ROOT%{_initddir}
install -m755 %{SOURCE1} $RPM_BUILD_ROOT%{_initddir}/vncserver

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig
install -m644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/vncservers

# Install desktop stuff
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/{16x16,24x24,48x48}/apps

pushd media/icons
for s in 16 24 48; do
install -m644 tigervnc_$s.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x$s/apps/tigervnc.png
done
popd

mkdir $RPM_BUILD_ROOT%{_datadir}/applications
desktop-file-install \
	--dir $RPM_BUILD_ROOT%{_datadir}/applications \
	%{SOURCE6}

%find_lang %{name} %{name}.lang

# remove unwanted files
rm -f  $RPM_BUILD_ROOT%{_libdir}/xorg/modules/extensions/libvnc.la

%ifarch s390 s390x
rm -f $RPM_BUILD_ROOT%{_libdir}/xorg/modules/extensions/libvnc.so
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
touch -c %{_datadir}/icons/hicolor
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
	%{_bindir}/gtk-update-icon-cache -q %{_datadir}/icons/hicolor || :
fi

%postun
touch -c %{_datadir}/icons/hicolor
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
	%{_bindir}/gtk-update-icon-cache -q %{_datadir}/icons/hicolor || :
fi

%post server
/sbin/chkconfig --add vncserver

%preun server
if [ "$1" -eq 0 ]; then
	/sbin/service vncserver stop > /dev/null 2>&1
	/sbin/chkconfig --del vncserver
fi

%postun server
if [ "$1" -ge "1" ]; then
	/sbin/service vncserver condrestart > /dev/null 2>&1 || :
fi

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc LICENCE.TXT unix/README
%{_bindir}/vncviewer
%{_datadir}/icons/*
%{_datadir}/applications/*
%{_mandir}/man1/vncviewer.1*

%files server
%defattr(-,root,root,-)
%{_initddir}/vncserver
%config(noreplace) %{_sysconfdir}/sysconfig/vncservers
%{_bindir}/vncconfig
%{_bindir}/vncpasswd
%{_bindir}/x0vncserver
%{_bindir}/Xvnc
%{_bindir}/vncserver
%{_mandir}/man1/Xvnc.1*
%{_mandir}/man1/vncpasswd.1*
%{_mandir}/man1/vncconfig.1*
%{_mandir}/man1/vncserver.1*
%{_mandir}/man1/x0vncserver.1*

%ifnarch s390 s390x
%files server-module
%defattr(-,root,root,-)
%{_libdir}/xorg/modules/extensions/libvnc.so
%endif

%changelog
* Tue Jun 23 2009 Adam Tkac <atkac redhat com> 0.0.91-0.13
- temporary use F11 Xserver base to make Xvnc compilable
- BuildRequires: libXi-devel
- don't ship tigervnc-server-module on s390/s390x

* Mon Jun 22 2009 Adam Tkac <atkac redhat com> 0.0.91-0.12
- fix local rendering of cursor (#495457)

* Thu Jun 18 2009 Adam Tkac <atkac redhat com> 0.0.91-0.11
- update to 0.0.91 (1.0.0 RC1)
- patches merged
  - tigervnc10-rh499401.patch
  - tigervnc10-rh497592.patch
  - tigervnc10-rh501832.patch
- after discusion in upstream drop tigervnc-bounds.patch
- configure flags cleanup

* Thu May 21 2009 Adam Tkac <atkac redhat com> 0.0.90-0.10
- rebuild against 1.6.1.901 X server (#497835)
- disable i18n, vncviewer is not UTF-8 compatible (#501832)

* Mon May 18 2009 Adam Tkac <atkac redhat com> 0.0.90-0.9
- fix vncpasswd crash on long passwords (#499401)
- start session dbus daemon correctly (#497592)

* Mon May 11 2009 Adam Tkac <atkac redhat com> 0.0.90-0.8.1
- remove merged tigervnc-manminor.patch

* Tue May 05 2009 Adam Tkac <atkac redhat com> 0.0.90-0.8
- update to 0.0.90

* Thu Apr 30 2009 Adam Tkac <atkac redhat com> 0.0.90-0.7.20090427svn3789
- server package now requires xorg-x11-fonts-misc (#498184)

* Mon Apr 27 2009 Adam Tkac <atkac redhat com> 0.0.90-0.6.20090427svn3789
- update to r3789
  - tigervnc-rh494801.patch merged
- tigervnc-newfbsize.patch is no longer needed
- fix problems when vncviewer and Xvnc run on different endianess (#496653)
- UltraVNC and TightVNC clients work fine again (#496786)

* Wed Apr 08 2009 Adam Tkac <atkac redhat com> 0.0.90-0.5.20090403svn3751
- workaround broken fontpath handling in vncserver script (#494801)

* Fri Apr 03 2009 Adam Tkac <atkac redhat com> 0.0.90-0.4.20090403svn3751
- update to r3751
- patches merged
  - tigervnc-xclients.patch
  - tigervnc-clipboard.patch
  - tigervnc-rh212985.patch
- basic RandR support in Xvnc (resize of the desktop)
- use built-in libjpeg (SSE2/MMX accelerated encoding on x86 platform)
- use Tight encoding by default
- use TigerVNC icons

* Tue Mar 03 2009 Adam Tkac <atkac redhat com> 0.0.90-0.3.20090303svn3631
- update to r3631

* Tue Mar 03 2009 Adam Tkac <atkac redhat com> 0.0.90-0.2.20090302svn3621
- package review related fixes

* Mon Mar 02 2009 Adam Tkac <atkac redhat com> 0.0.90-0.1.20090302svn3621
- initial package, r3621
