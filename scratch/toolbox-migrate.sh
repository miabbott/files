#!/usr/bin/bash
set -xeou pipefail

if [ $# -eq 0 ]; then
    echo "Must supply action: backup, cleanup, or restore"
    exit 1
fi

action=$1; shift

case $action in
    backup)
        mkdir -p "$HOME/toolbox-repos-backup/"
        repos=$(ls /etc/yum.repos.d)
        for r in $repos; do
            if [[ $r != "fedora"* ]]; then
                cp "/etc/yum.repos.d/$r" "$HOME/toolbox-repos-backup/"
            fi
        done
        rpm -qa --queryformat="%{NAME} " > ~/toolbox-rpms.backup
        ;;
    restore)
        if [ "$(id -u)" -ne 0 ]; then
            echo "Must run restore as superuser"
            exit 1
        fi
        if [ ! -d "/var/home/$SUDO_USER/toolbox-repos-backup/" ] || [ ! -f "/var/home/$SUDO_USER/toolbox-rpms.backup" ]; then
            echo "Cannot find backup repos or backup RPM file; run backup first"
            exit 1
        fi
        shopt -s globstar nullglob
        for r in "/var/home/$SUDO_USER"/toolbox-repos-backup/*.repo; do
            cp "${r}" /etc/yum.repos.d/
        done
        rpms=$(cat "/var/home/$SUDO_USER/toolbox-rpms.backup")
        # shellcheck disable=SC2086
        dnf -y --skip-broken install $rpms
        ;;
    cleanup)
        if [ "$(id -u)" -eq 0 ]; then
            echo "You are running cleanup as superuser; you probably want to run this as a normal user"
        fi
        rm -rf "$HOME/toolbox-repos-backup/" "$HOME/toolbox-rpms.backup"
        ;;
    *)
        echo "Unsupported action; use backup, cleanup, or restore"
        exit 1
esac
