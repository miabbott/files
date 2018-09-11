#!/bin/bash
set -xeou pipefail

if [ $# -eq 0 ]; then
  echo "Must supply value for releasever"
  exit 1
fi
releasever=$1; shift

# create base container
ctr=$(buildah from registry.fedoraproject.org/fedora:$releasever)

# mount container filesystem
mp=$(buildah mount $ctr)

dnf_cmd() {
  dnf -y --installroot $mp --releasever $releasever $@
}

# set the maintainer label
buildah config --label maintainer="Micah Abbott <miabbott@redhat.com>" $ctr

# setup yum repos
curl -L -o $mp/etc/yum.repos.d/beaker-client.repo http://download-node-02.eng.bos.redhat.com/beakerrepos/beaker-client-Fedora.repo
curl -L -o $mp/etc/yum.repos.d/qa-tools.repo http://liver.brq.redhat.com/repo/qa-tools.repo

# reinstall all pkgs with docs
sed -i '/tsflags=nodocs/d' $mp/etc/dnf/dnf.conf
dnf -y --installroot $mp --releasever $releasever --disablerepo=beaker-client --disablerepo=qa-tools reinstall '*'

# install tools needed for building ostree/rpm-ostree stack
dnf_cmd install @buildsys-build dnf-plugins-core
dnf_cmd builddep ostree rpm-ostree

# install the rest
dnf_cmd install \
                   awscli \
                   beaker-client \
                   beaker-redhat \
                   btrfs-progs-devel\
                   conmon \
                   conserver-client \
                   createrepo_c \
                   cyrus-sasl-gssapi \
                   device-mapper-devel \
                   fuse \
                   gcc \
                   git \
                   git-review \
                   glib2-devel \
                   glibc-static \
                   golang \
                   golang-github-cpuguy83-go-md2man \
                   gpgme-devel \
                   iputils \
                   libassuan-devel \
                   libgpg-error-devel \
                   libseccomp-devel \
                   libselinux-devel \
                   jq \
                   man \
                   python-qpid-messaging \
                   python-saslwrapper \
                   python2-virtualenv \
                   python3-virtualenv \
                   qa-tools-workstation \
                   redhat-rpm-config \
                   rpm-ostree \
                   rsync \
                   sshpass \
                   sudo \
                   tmux \
                   vim


# clean up
dnf_cmd clean all

# setup sudoers
echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> $mp/etc/sudoers
echo "Defaults secure_path = /usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> $mp/etc/sudoers

# add my username/uid
chroot $mp bash -c "/usr/sbin/useradd --groups wheel --uid 1000 miabbott"

# config the user
buildah config --user miabbott $ctr

# commit the image
buildah commit $ctr miabbott/myprecious:$releasever

# unmount and remove the container
buildah unmount $ctr
buildah rm $ctr
