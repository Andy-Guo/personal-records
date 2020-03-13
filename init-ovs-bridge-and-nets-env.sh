#!/usr/bin/bash
bridge="br-int"
netns1="test-ns1"
netns2="test-ns2"
netgw="netgw"
netns1tap1="tap-1100"
netns2tap1="tap-2200"
netns1net1tap1ip="192.168.10.120/24"
netns2net2tap1ip="192.168.20.120/24"
netnsnet1gwtap="tapgw-100"
netnsnet2gwtap="tapgw-200"
netnsnet1gwip="192.168.10.1"
netnsnet2gwip="192.168.20.1"

# clear env
ip netns del $netns1
ip netns del $netns2
ip netns del $netgw
ovs-vsctl del-port $bridge $netns1tap1-reply
ovs-vsctl del-port $bridge $netns2tap1-reply
ovs-vsctl del-port $bridge $netnsnet1gwtap-reply
ovs-vsctl del-port $bridge $netnsnet2gwtap-reply
ovs-ofctl del-flows $bridge
ovs-vsctl del-br $bridge

#exit 1

# create bridge
ovs-vsctl -- --may-exist add-br $bridge 
ovs-vsctl set-fail-mode $bridge secure
ovs-vsctl set Bridge $bridge protocols=OpenFlow10,OpenFlow13,OpenFlow15

# add normal flows
ovs-ofctl add-flow br-int "table=0,priority=0 actions=NORMAL"

#create netns
ip netns add $netns1
ip netns add $netns2
ip netns add $netgw

#create veth peer
ip link add $netns1tap1 type veth peer name $netns1tap1-reply
ip link set $netns1tap1 netns $netns1
ip netns exec $netns1 ifconfig lo up
ip netns exec $netns1 ifconfig $netns1tap1 up
ip netns exec $netns1 ifconfig $netns1tap1 $netns1net1tap1ip
ip link set $netns1tap1-reply up
ovs-vsctl --may-exist add-port $bridge $netns1tap1-reply 
#ovs-vsctl set Interface $netns1tap1-reply type=internal

ip link add $netns2tap1 type veth peer name $netns2tap1-reply
ip link set $netns2tap1 netns $netns2
ip netns exec $netns2 ifconfig lo up
ip netns exec $netns2 ifconfig $netns2tap1 up
ip netns exec $netns2 ifconfig $netns2tap1 $netns2net2tap1ip
ip link set $netns2tap1-reply up
ovs-vsctl --may-exist add-port $bridge $netns2tap1-reply 
#ovs-vsctl set Interface $netns2tap1-reply type=internal

# set gw
 # net1 gw
ip link add $netnsnet1gwtap type veth peer name $netnsnet1gwtap-reply
ip link set $netnsnet1gwtap netns $netgw
ip netns exec $netgw ifconfig $netnsnet1gwtap up
ip netns exec $netgw ifconfig $netnsnet1gwtap $netnsnet1gwip
#ip link set $netnsnet1gwtap-reply up
ovs-vsctl --may-exist add-port $bridge $netnsnet1gwtap-reply 
#ovs-vsctl set Interface $netnsnet1gwtap-reply type=internal

 # net2 gw
ip link add $netnsnet2gwtap type veth peer name $netnsnet2gwtap-reply
ip link set $netnsnet2gwtap netns $netgw
ip netns exec $netgw ifconfig $netnsnet2gwtap up
ip netns exec $netgw ifconfig $netnsnet2gwtap $netnsnet2gwip
#ip link set $netnsnet1gwtap-reply up
ovs-vsctl --may-exist add-port $bridge $netnsnet2gwtap-reply 
#ovs-vsctl set Interface $netnsnet1gwtap-reply type=internal
