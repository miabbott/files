#!/bin/bash
set -xeou pipefail

# create base container
ctr=$(buildah from registry.fedoraproject.org/fedora:27)

# mount container filesystem
mp=$(buildah mount $ctr)

# set the maintainer label
buildah config --label maintainer="Micah Abbott <miabbott@redhat.com>" $ctr

# setup yum repos
curl -L -o $mp/etc/yum.repos.d/beaker-client.repo http://download-node-02.eng.bos.redhat.com/beakerrepos/beaker-client-Fedora.repo
curl -L -o $mp/etc/yum.repos.d/qa-tools.repo http://liver.brq.redhat.com/repo/qa-tools.repo

# reinstall all pkgs with docs
sed -i '/tsflags=nodocs/d' $mp/etc/dnf/dnf.conf
dnf -y reinstall --disablerepo=beaker-client --disablerepo=qa-tools --installroot $mp --releasever 27 '*'

# install the rest
dnf -y install --installroot $mp --releasever 27 \
                   beaker-client \
                   beaker-redhat \
                   conserver-client \
                   fuse \
                   gcc \
                   git \
                   git-review \
                   golang \
                   iputils \
                   man \
                   python2-virtualenv \
                   python3-virtualenv \
                   qa-tools-workstation \
                   redhat-rpm-config \
                   rsync \
                   sshpass \
                   sudo \
                   vim

# clean up
dnf clean all --installroot $mp

# setup sudoers
echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> $mp/etc/sudoers
echo "Defaults secure_path = /usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> $mp/etc/sudoers

# add my username/uid
chroot $mp bash -c "/usr/sbin/useradd --groups wheel --uid 1000 miabbott"

# config the user
buildah config --user miabbott $ctr

# commit the image
buildah commit $ctr miabbott/myprecious:buildah27

# unmount and remove the container
buildah unmount $ctr
buildah rm $ctr
