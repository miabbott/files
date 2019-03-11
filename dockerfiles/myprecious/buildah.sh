#!/bin/bash
set -xeou pipefail

cleanup() {
  ctr=$1; shift
  buildah umount "$ctr"
  buildah rm "$ctr"
}

dnf_cmd() {
  dnf -y --installroot "$mp" --releasever "$releasever" "$@"
}

if [ $# -eq 0 ]; then
  echo "Must supply value for releasever"
  exit 1
fi
releasever=$1; shift

registry="docker-registry-default.cloud.registry.upshift.redhat.com"

token="$(cat /home/miabbott/.secrets/upshift-registry-sa.secret)"

# create base container
ctr=$(buildah from registry.fedoraproject.org/fedora:"$releasever")

trap 'cleanup $ctr' ERR

# mount container filesystem
mp=$(buildah mount "$ctr")

# set the maintainer label
buildah config --label maintainer="Micah Abbott <miabbott@redhat.com>" "$ctr"

# setup yum repos
curl -L -o "$mp"/etc/yum.repos.d/beaker-client.repo http://download-node-02.eng.bos.redhat.com/beakerrepos/beaker-client-Fedora.repo
curl -L -o "$mp"/etc/yum.repos.d/qa-tools.repo http://liver.brq.redhat.com/repo/qa-tools.repo

# coreutils-single conflicts with coreutils so have to swap?
if [ "$releasever" == "29" ]; then
  dnf_cmd swap coreutils-single coreutils-full
fi

# reinstall all pkgs with docs
sed -i '/tsflags=nodocs/d' "$mp"/etc/dnf/dnf.conf
dnf -y --installroot "$mp" --releasever "$releasever" --disablerepo=beaker-client --disablerepo=qa-tools reinstall '*'

# install v3.9 origin for UpShift compat
mkdir -p "$mp/tmp"
curl -L -o "$mp/tmp/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz" https://github.com/openshift/origin/releases/download/v3.9.0/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz
tar -zxvf "$mp/tmp/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz" -C "$mp/tmp/"
cp "$mp/tmp/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit/oc" "$mp/usr/local/bin/oc"
chmod +x "$mp/usr/local/bin/oc"
rm -rf "$mp/tmp"

# install tools needed for building ostree/rpm-ostree stack
dnf_cmd install @buildsys-build dnf-plugins-core
dnf_cmd builddep ostree rpm-ostree

# install the rest
dnf_cmd install \
                   awscli \
                   beaker-client \
                   beaker-redhat \
                   bind-utils \
                   btrfs-progs-devel\
                   conmon \
                   conserver-client \
                   createrepo_c \
                   cyrus-sasl-gssapi \
                   device-mapper-devel \
                   fuse \
                   gcc \
                   gdb \
                   git \
                   git-evtag \
                   git-review \
                   glib2-devel \
                   glibc-static \
                   golang \
                   golang-github-cpuguy83-go-md2man \
                   gpg \
                   gpgme-devel \
                   hostname \
                   iputils \
                   libassuan-devel \
                   libgpg-error-devel \
                   libseccomp-devel \
                   libselinux-devel \
                   libvirt-devel \
                   lz4 \
                   jq \
                   man \
                   podman \
                   python-qpid-messaging \
                   python-saslwrapper \
                   python2-virtualenv \
                   python3-virtualenv \
                   qa-tools-workstation \
                   redhat-rpm-config \
                   rpm-ostree \
                   rsync \
                   ShellCheck \
                   skopeo \
                   sshpass \
                   sudo \
                   tig \
                   tmux \
                   vim

# install bat
cp /etc/resolv.conf "$mp"/etc/resolv.conf
mount -t proc /proc "$mp"/proc
mount -t sysfs /sys "$mp"/sys
chroot "$mp" git clone https://github.com/sharkdp/bat
chroot "$mp" bash -c "(cd bat && /usr/bin/cargo install --root /usr/local bat && /usr/bin/cargo clean)"
chroot "$mp" bash -c "(mv /usr/bin/cat /usr/bin/cat.old && ln -s /usr/local/bin/bat /usr/bin/cat)"
chroot "$mp" bash -c "rm -rf bat"
umount "$mp/proc"
umount "$mp/sys"

# clean up
dnf_cmd clean all

# get Red Hat certs
curl -kL -o $mp/etc/pki/ca-trust/source/anchors/Red_Hat_IT_Root_CA.crt https://password.corp.redhat.com/RH-IT-Root-CA.crt
curl -kL -o $mp/etc/pki/ca-trust/source/anchors/legacy.crt https://password.corp.redhat.com/legacy.crt
curl -kL -o $mp/etc/pki/ca-trust/source/anchors/Eng-CA.crt https://engineering.redhat.com/Eng-CA.crt
chroot "$mp" bash -c "update-ca-trust"

# setup sudoers
echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> "$mp"/etc/sudoers
echo "Defaults secure_path = /usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> "$mp"/etc/sudoers

# add my username/uid
chroot "$mp" bash -c "/usr/sbin/useradd --groups wheel --uid 1000 miabbott"

# config the user
buildah config --user miabbott "$ctr"

# commit the image
buildah commit "$ctr" miabbott/myprecious:"$releasever"

# unmount and remove the container
cleanup "$ctr"

# tag and push image
podman login -u unused -p "$token" "$registry"
podman tag localhost/miabbott/myprecious:"$releasever" "$registry"/miabbott/myprecious:"$releasever"
podman push "$registry"/miabbott/myprecious:"$releasever"
