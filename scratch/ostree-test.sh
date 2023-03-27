#!/usr/bin/bash

set -xeou pipefail

tmprepo=$(mktemp -d)
mkdir -p ${tmprepo}/{silverblue,kinoite,unified}

# silverblue/kinoite measurement
for ref in silverblue kinoite; do
    repo=${tmprepo}/${ref}
    ostree --repo=${repo} init
    cat << EOF >> ${repo}/config
[remote "fedora"]
url=https://ostree.fedoraproject.org
gpg-verify=true
gpgkeypath=/etc/pki/rpm-gpg/
contenturl=mirrorlist=https://ostree.fedoraproject.org/mirrorlist
EOF

    ostree --repo=${repo} pull --depth=1 fedora:fedora/37/x86_64/${ref}
    du -hs ${repo}
    rm -rf ${repo}
done

# measure unified repo
repo=${tmprepo}/unified
ostree --repo=${repo} init
cat << EOF >> ${repo}/config
[remote "fedora"]
url=https://ostree.fedoraproject.org
gpg-verify=true
gpgkeypath=/etc/pki/rpm-gpg/
contenturl=mirrorlist=https://ostree.fedoraproject.org/mirrorlist
EOF

for ref in silverblue kinoite; do
    ostree --repo=${repo} pull --depth=1 fedora:fedora/37/x86_64/${ref}
    du -hs ${repo}
done

rm -rf ${tmprepo}
