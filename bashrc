# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# https://www.digitalocean.com/community/tutorials/how-to-use-bash-history-commands-and-expansions-on-a-linux-vps
HISTTIMEFORMAT="%Y-%b-%d %T "
HISTSIZE=5000
HISTFILESIZE=10000

shopt -s histappend

export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
alias sshq='ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
alias scpq='scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'

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