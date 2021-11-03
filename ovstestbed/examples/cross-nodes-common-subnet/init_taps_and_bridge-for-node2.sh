#!/usr/bin/bash

## br-int 网桥挂3个veth port， veth port的对端分别对应于3个namespace中的port，并设置port的ip，mac

ns_name="nsdev-2"
ns_tap="nsdev2-tap1"
ns_tap_veth="${ns_tap}veth"
ns_tap_ipaddr="192.168.10.22"
ns_tap_netmask="24"
bridge_name="br-int"

ovs-vsctl del-br ${bridge_name}
ovs-vsctl add-br ${bridge_name}

ovs-vsctl del-port ${bridge_name} ${ns_tap_veth}
ip link del ${ns_tap} type veth peer name ${ns_tap_veth}
ip netns add ${ns_name}
ip link add ${ns_tap} type veth peer name ${ns_tap_veth}
ip link set ${ns_tap_veth} up
ip link set ${ns_tap} netns ${ns_name}
ip netns exec ${ns_name} ip link set ${ns_tap} up
ip netns exec ${ns_name} ip addr add ${ns_tap_ipaddr}/${ns_tap_netmask} dev ${ns_tap}
ovs-vsctl add-port ${bridge_name} ${ns_tap_veth}

ns1_name="nsdev-1"
ns1_tap="nsdev1-tap1"
ns1_tap_veth="${ns1_tap}veth"
ns1_tap_ipaddr="192.168.10.21"
ns1_tap_netmask="24"

ovs-vsctl del-port ${bridge_name} ${ns1_tap_veth}
ip link del ${ns1_tap} type veth peer name ${ns1_tap_veth}

ip netns add ${ns1_name}
ip link add ${ns1_tap} type veth peer name ${ns1_tap_veth}
ip link set ${ns1_tap_veth} up
ip link set ${ns1_tap} netns ${ns1_name}
ip netns exec ${ns1_name} ip link set ${ns1_tap} up
ip netns exec ${ns1_name} ip addr add ${ns1_tap_ipaddr}/${ns1_tap_netmask} dev ${ns1_tap}
ovs-vsctl add-port ${bridge_name} ${ns1_tap_veth}

ns2_name="nsdev-3"
ns2_tap="nsdev3-tap1"
ns2_tap_veth="${ns2_tap}veth"
ns2_tap_ipaddr="192.168.10.23"
ns2_tap_netmask="24"

ovs-vsctl del-port ${bridge_name} ${ns2_tap_veth}
ip link del ${ns2_tap} type veth peer name ${ns2_tap_veth}

ip netns add ${ns2_name}
ip link add ${ns2_tap} type veth peer name ${ns2_tap_veth}
ip link set ${ns2_tap_veth} up
ip link set ${ns2_tap} netns ${ns2_name}
ip netns exec ${ns2_name} ip link set ${ns2_tap} up
ip netns exec ${ns2_name} ip addr add ${ns2_tap_ipaddr}/${ns2_tap_netmask} dev ${ns2_tap}
ovs-vsctl add-port ${bridge_name} ${ns2_tap_veth}
