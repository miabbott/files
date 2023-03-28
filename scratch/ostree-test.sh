#!/usr/bin/bash

# This is a cheap bash script that will pull the HEAD commit for the
# Silverblue and Kinoite refs for the purpose of demonstrating how
# ostree avoids pulling content it already knows about on disk.
#
# This script should be run with elevated privileges:
#
# $ sudo ./ostree-test.sh

set -eou pipefail

if [ "${EUID}" -ne 0 ]; then
    echo "Must run this script as root or with sudo"
    exit 1
fi

tmprepo=$(mktemp -d)
mkdir -p "${tmprepo}"/{silverblue,kinoite,unified}

trap 'rm -rf "${tmprepo}"' EXIT

printf "We'll first pull the HEAD commit on the Silverblue + Kinoite refs separately and display the data\n\n"

# silverblue/kinoite measurement
for ref in silverblue kinoite; do
    repo="${tmprepo}/${ref}"
    fullref="fedora:fedora/37/x86_64/${ref}"
    ostree --repo="${repo}" init
    cat << EOF >> "${repo}/config"
[remote "fedora"]
url=https://ostree.fedoraproject.org
gpg-verify=true
gpgkeypath=/etc/pki/rpm-gpg/
contenturl=mirrorlist=https://ostree.fedoraproject.org/mirrorlist
EOF

    echo "Pulling ${fullref}..."
    ostree --repo="${repo}" pull --depth=1 "${fullref}" > "${tmprepo}/${ref}.log"
    cat "${tmprepo}/${ref}.log"
    ondisksize=$(du -hs "${repo}" | awk '{print $1}' | tee "${tmprepo}/${ref}_ondisksize.txt")
    printf "Size of %s on disk: %s\n\n" "${fullref}" "${ondisksize}"
    rm -rf "${repo}"
done

silverblue=$(sed "s|G||" < "${tmprepo}/silverblue_ondisksize.txt")
kinoite=$(sed "s|G||" < "${tmprepo}/kinoite_ondisksize.txt")
fullsize=$(echo "${silverblue} + ${kinoite}" | bc -l)

printf "The combined ondisk size of both refs is: %.1fG\n\n" "${fullsize}"
printf "Now we'll pull both again into a shared repo to show that we are saving disk space and network bandwidth\n\n"

# measure unified repo
repo="${tmprepo}/unified"
ostree --repo="${repo}" init
cat << EOF >> "${repo}/config"
[remote "fedora"]
url=https://ostree.fedoraproject.org
gpg-verify=true
gpgkeypath=/etc/pki/rpm-gpg/
contenturl=mirrorlist=https://ostree.fedoraproject.org/mirrorlist
EOF

for ref in silverblue kinoite; do
    fullref="fedora:fedora/37/x86_64/${ref}"
    echo "Pulling ${fullref} into a unified ostree repo..."
    ostree --repo="${repo}" pull --depth=1 "${fullref}" > "${tmprepo}/${ref}_unified.log"
    cat "${tmprepo}/${ref}_unified.log"
    ondisksize=$(du -hs "${repo}" | awk '{print $1}' | tee "${tmprepo}/${ref}_unified_ondisksize.txt")
    printf "On disk size of the unified ostree repo after pulling %s: %s\n\n" "${fullref}" "${ondisksize}"
done

kinoite=$(sed "s|G||" < "${tmprepo}/kinoite_unified_ondisksize.txt")
difference=$(echo "${fullsize} - ${kinoite}" | bc -l)

echo "The combined ondisk size of both refs in the unified ostree repo is: ${kinoite}G"
echo "The unified ostree repo is ${difference}G smaller than separate repos"
