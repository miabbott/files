#!/bin/bash
set -xeou pipefail

trap_cleanup() {
  ctr=$1; shift
  buildah umount "$ctr"
  buildah rm "$ctr"
}

if [ $# -eq 0 ]; then
  echo "Must supply value for releasever"
  exit 1
fi
releasever=$1; shift

registry="docker-registry-default.cloud.registry.upshift.redhat.com"


# create base container
ctr=$(buildah from registry.fedoraproject.org/fedora:"$releasever")

trap 'trap_cleanup $ctr' ERR

# mount container filesystem
mp=$(buildah mount "$ctr")

dnf_cmd() {
  dnf -y --installroot "$mp" --releasever "$releasever" "$@"
}

# set the maintainer label
buildah config --label maintainer="Micah Abbott <miabbott@redhat.com>" "$ctr"

# setup yum repos
curl -L -o "$mp"/etc/yum.repos.d/beaker-client.repo http://download-node-02.eng.bos.redhat.com/beakerrepos/beaker-client-Fedora.repo
curl -L -o "$mp"/etc/yum.repos.d/qa-tools.repo http://liver.brq.redhat.com/repo/qa-tools.repo

# coreutils-single conflicts with coreutils so have to swap?
if [ $releasever == "29" ]; then
  dnf_cmd swap coreutils-single coreutils-full
fi

# reinstall all pkgs with docs
sed -i '/tsflags=nodocs/d' "$mp"/etc/dnf/dnf.conf
dnf -y --installroot "$mp" --releasever "$releasever" --disablerepo=beaker-client --disablerepo=qa-tools reinstall '*'

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
                   origin-clients \
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
                   tmux \
                   vim


# clone c-a repo and install deps
cp /etc/resolv.conf "$mp"/etc/resolv.conf
chroot "$mp" git clone https://github.com/coreos/coreos-assembler
chroot "$mp" bash -c "(cd coreos-assembler && ./build.sh configure_yum_repos && ./build.sh install_rpms)"
chroot "$mp" rm -rf coreos-assembler

# install bat
chroot "$mp" git clone https://github.com/sharkdp/bat
chroot "$mp" bash -c "(cd bat && cargo install --path /usr/local bat && cargo clean)"
chroot "$mp" (mv /usr/bin/cat /usr/bin/cat.old && ln -s /usr/local/bin/bat /usr/bin/cat)
chroot "$mp" rm -rf bat

# clean up
dnf_cmd clean all

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
trap_cleanup "$ctr"

# tag and push image
podman tag localhost/miabbott/myprecious:"$releasever" "$registry"/miabbott/myprecious:"$releasever"
podman push "$registry"/miabbott/myprecious:"$releasever"
