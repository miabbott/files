#!/usr/bin/env bash

# inspired by https://github.com/coreos/fedora-coreos-config/blob/testing-devel/tests/manual/coreos-docs-net-testing.sh
# very specific to my config

set -xeou pipefail

if [ "$#" -ne 1 ]; then
        echo "Need to specify an Ignition config in /var/srv/www-data/"
        exit 1
fi

VM_NAME="coreos"
VCPUS="2"
RAM_MB="4096"
DISK_GB="20"
IMAGE="/var/lib/libvirt/images/rhcos-46.82.202104301741-0-qemu.x86_64.qcow2"
KERNEL="/var/lib/libvirt/images/rhcos-46.82.202104301741-0-kernel"
INITRAMFS="/var/lib/libvirt/images/rhcos-46.82.202104301741-0-initramfs.img"
## common set of kargs when network config is on kernel cmdline
COMMON_ARGS="rhcos.root=crypt_rootfs random.trust_cpu=on console=tty0 console=ttyS0,115200n8 ignition.platform.id=qemu ignition.firstboot rd.luks.options=discard ostree=/ostree/boot.1/rhcos/f258eb9501c090176d3ee9a4d212f7eef7de0e13fdfea9d972a9ebceffc0e8dc/0"
## single dhcp
#KERNEL_ARGS=" ip=enp1s0:dhcp ip=enp2s0:off"
## multiple dhcp
#KERNEL_ARGS=" ip=enp1s0:dhcp ip=enp2s0:dhcp"
## single static ip
#KERNEL_ARGS=" ip=192.168.122.210::192.168.122.1:255.255.255.0:coreos:enp1s0:none:192.168.122.1 ip=enp2s0:off"
## multiple static ip
#KERNEL_ARGS=" ip=192.168.122.210::192.168.122.1:255.255.255.0:coreos:enp1s0:none:192.168.122.1 ip=192.168.122.211::192.168.122.1:255.255.255.0:coreos:enp1s0:none:192.168.122.1"
## static ip bond
#KERNEL_ARGS=" ip=192.168.122.210::192.168.122.1:255.255.255.0:coreos:bond0:none:192.168.122.1 bond=bond0:enp1s0,enp2s0:mode=active-backup,miimon=100"
## static ip team
#KERNEL_ARGS=" ip=192.168.122.210::192.168.122.1:255.255.255.0:coreos:team0:none:192.168.122.1 team=team0:enp1s0,enp2s0"
## static ip vlan
## needs another host connected to virbr1 with a tagged interface; see: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/tests/manual/coreos-docs-net-testing.sh#L18-L32
## needs `--network bridge=virbr1 --network bridge=virbr1` passed to `virt-install`
#KERNEL_ARGS=" ip=192.168.200.210::192.168.200.1:255.255.255.0:coreos:enp1s0.100:none:192.168.200.1 vlan=enp1s0.100:enp1s0 ip=enp2s0:off ip=enp1s0:off"
## static ip bond vlan
## needs another host connected to virbr1 with a tagged interface; see: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/tests/manual/coreos-docs-net-testing.sh#L18-L32
## needs `--network bridge=virbr1 --network bridge=virbr1` passed to `virt-install`
#KERNEL_ARGS=" ip=192.168.200.210::192.168.200.1:255.255.255.0:coreos:bond0.100:none:192.168.200.1 bond=bond0:enp1s0,enp2s0:mode=active-backup,miimon=100 vlan=bond0.100:bond0"
## dhcp bond vlan
## needs another host connected to virbr1 with a tagged interface; see: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/tests/manual/coreos-docs-net-testing.sh#L18-L32
## needs `--network bridge=virbr1 --network bridge=virbr1` passed to `virt-install`
KERNEL_ARGS=" ip=bond0.100:dhcp bond=bond0:enp1s0,enp2s0:mode=active-backup,miimon=100 vlan=bond0.100:bond0"

IGNITION_CONFIG=$1; shift

## use this for installing from qcow2 + network config in ignition config
# virt-install --connect="qemu:///system" --name="${VM_NAME}" --vcpus="${VCPUS}" --memory="${RAM_MB}" \
#         --os-variant="rhel8.2" --import --graphics=none \
#         --network bridge=virbr1 --network bridge=virbr1 \
#         --disk="size=${DISK_GB},backing_store=${IMAGE}" \
#         --qemu-commandline="-fw_cfg name=opt/com.coreos/config,file=/var/srv/www-data/${IGNITION_CONFIG}"

## use this for isntalling from qcow2 + network config on kernel cmdline
## use base.bu/base.json for ignition config
## see: https://github.com/miabbott/butane-configs/blob/main/base.bu
virt-install --connect="qemu:///system" --name="${VM_NAME}" --vcpus="${VCPUS}" --memory="${RAM_MB}" \
        --os-variant="rhel8.2" --graphics=none \
        --network bridge=virbr1 --network bridge=virbr1 \
        --disk "size=${DISK_GB},backing_store=${IMAGE}" \
        --install "kernel=${KERNEL},initrd=${INITRAMFS},kernel_args=${COMMON_ARGS}${KERNEL_ARGS}" \
        --qemu-commandline="-fw_cfg name=opt/com.coreos/config,file=/var/srv/www-data/${IGNITION_CONFIG}"

if virsh list --state-running | grep "${VM_NAME}"; then
        virsh destroy "${VM_NAME}"
fi
virsh undefine "${VM_NAME}" --nvram --wipe-storage --storage vda