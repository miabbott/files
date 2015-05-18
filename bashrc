# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# https://www.digitalocean.com/community/tutorials/how-to-use-bash-history-commands-and-expansions-on-a-linux-vps
HISTTIMEFORMAT="%Y-%b-%d %T "

# https://www.happyassassin.net/2015/01/16/bash-history-with-multiple-sessions/
HISTSIZE=1048576
HISTFILESIZE=1048576

LAST_HISTORY_WRITE=$SECONDS
function prompt_command {
    if [ $(($SECONDS - $LAST_HISTORY_WRITE)) -gt 60 ]; then
        history -a && history -c && history -r
        LAST_HISTORY_WRITE=$SECONDS
    fi
}

PROMPT_COMMAND="$PROMPT_COMMAND; prompt_command"

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
alias sshq='ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
alias scpq='scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'

# unset USER/USERNAME to work with keystoneclient (but why?!?!?!)
unset USER
unset USERNAME

# Default to QEOS instance
source ~/qeos.sh

# Choose Openstack instance
alias qeos="source ~/qeos.sh"
alias os1="source ~/os1.sh"

# Clean up QEOS floating IP
function NovaCleanIPs()
{
    nova floating-ip-list | awk '{print $2,$6}' | grep '-' | awk '{print $1}' | xargs -i nova floating-ip-delete {}
}
alias nova-clean-ips=NovaCleanIPs

# Clean up QEOS images
function NovaCleanImages()
{
    nova list | grep $1 | awk '{print $2}' | xargs -i nova delete {}
}
alias nova-clean-images=NovaCleanImages

# Flush ARP cache
alias flush-arp="ip -s -s neigh flush all"

# Use 'sudo' with aliases
# http://askubuntu.com/a/22043
alias sudo="sudo "

# Retrieve the IP address for a VM
function GetVmIp()
{
    MAC=`sudo virsh dumpxml $1 | grep 'mac address' | awk -F\' '{print $2}'`
    ip neigh | grep $MAC | awk '{print $1}'
}
alias get-vm-ip=GetVmIp

# Free up cached memory
# http://www.yourownlinux.com/2013/10/how-to-free-up-release-unused-cached-memory-in-linux.html
# https://web.archive.org/web/*/http://www.yourownlinux.com/2013/10/how-to-free-up-release-unused-cached-memory-in-linux.html
function FreeCachedMem()
{
    echo 1 > /proc/sys/vm/drop_caches
    echo 2 > /proc/sys/vm/drop_caches
    echo 3 > /proc/sys/vm/drop_caches
    sync
}
alias free-mem=FreeCachedMem
