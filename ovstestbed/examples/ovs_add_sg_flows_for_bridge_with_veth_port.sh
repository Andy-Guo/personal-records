#!/usr/bin/bash

ingress_table=12
ct_table=13
after_sg_table=16

ofports=(1 2)
conj_ids=(11 12)
ofports_ips=("192.168.10.12" "192.168.10.11")

tables=(12 13)
vni=1

## ct_state 
track="+trk"
no_track="-trk"
new="+new-est"
all_establish="+est-rel-rpl"
invalid="+inv+trk"
related="-new-est+rel-inv"
reply="+est-rel+rpl-inv"
establish="+est"
no_establish="-est"

## clear sg tables
for i in ${!tables[@]};
do 
    `ovs-ofctl -O openflow15 del-flows br-int "table=${tables[${i}]}"`
done

## create sg tables
for i in ${!tables[@]};
do 
    `ovs-ofctl -O Openflow15  add-flow br-int  "table=${tables[${i}]},priority=10,actions=drop"`
done

# table=12
for i in ${!ofports[@]};
do 
    `ovs-ofctl -O Openflow15  add-flow br-int "table=${ingress_table}, priority=100,ip,ct_state=-trk,metadata=${vni},in_port=${ofports[$i]} actions=ct(table=${ct_table},zone=${vni})"`
#    `ovs-ofctl -O Openflow15  add-flow br-int "table=${ingress_table}, priority=100,ip,ct_state=+trk,metadata=${vni} actions=goto_table:${ct_table}"`
done

# table = 13, ct_table

## tcp sync
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,ip,ct_state=${new},metadata=${vni},nw_src="192.168.10.11" actions=conjunction(11,1/2)"`

`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,tcp,ct_state=${new},metadata=${vni},tp_dst=8890 actions=conjunction(11,2/2)"`
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,udp,ct_state=${new},metadata=${vni},tp_dst=8890 actions=conjunction(11,2/2)"`
## icmp 
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=110,icmp,ct_state=${new},metadata=${vni} actions=conjunction(11,2/2)"`
#`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=110,icmp,ct_state=${all_establish},metadata=${vni} actions=conjunction(11,2/2)"`

`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,ip,ct_state=${new},conj_id=11,metadata=${vni} actions=ct(commit,zone=${vni}),goto_table:${after_sg_table}"`


## tcp sync + ack
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=50,ip,ct_state=${reply},ct_zone=${vni},metadata=${vni} actions=goto_table:${after_sg_table}"`

## tcp fin 
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=40,ct_state=${establish},ip,ct_zone=${vni},metadata=${vni}, actions=goto_table:${after_sg_table}"`


## ---- 对于trk 数据包 ---
for i in ${!ofports[@]};
do 
    `ovs-ofctl -O Openflow15  add-flow br-int "table=${ingress_table}, priority=100,ip,ct_state=+trk,metadata=${vni} actions=goto_table:${ct_table}"`
done

`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,ip,ct_state=${all_establish},metadata=${vni},nw_src="192.168.10.11" actions=conjunction(15,1/2)"`

`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,tcp,ct_state=${all_establish},metadata=${vni},tp_dst=8890 actions=conjunction(13,2/2)"`
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,udp,ct_state=${all_establish},metadata=${vni},tp_dst=8890 actions=conjunction(13,2/2)"`

`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=100,ip,ct_state=${all_establish},conj_id=15,metadata=${vni} actions=goto_table:${after_sg_table}"`
`ovs-ofctl -O Openflow15  add-flow br-int "table=${ct_table}, priority=50,ip,ct_state=${invalid} actions=drop"`
