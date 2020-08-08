FROM registry.access.redhat.com/ubi8/ubi:latest
## Repo file needs to have access to baseos, appstream, codeready
COPY rhel8.repo /etc/yum.repos.d/rhel8.repo
RUN dnf -y builddep ostree && \
    dnf -y install /usr/bin/python3 \
                   chrpath \
                   cmake \
                   gcc-c++ \
                   gnome-common \
                   gperf \
                   make \
                   rpm-build \
                   "pkgconfig(check)" \
                   "pkgconfig(cppunit)" \
                   "pkgconfig(expat)" \
                   "pkgconfig(json-c)" \
                   "pkgconfig(json-glib-1.0)" \
                   "pkgconfig(modulemd-2.0)" \
                   "pkgconfig(ostree-1)" \
                   "pkgconfig(polkit-gobject-1)" \
                   "pkgconfig(rpm)" \
                   "pkgconfig(smartcols)" \
                   rust-toolset \
                   sqlite-devel \
                   swig && \
    dnf -y clean all
