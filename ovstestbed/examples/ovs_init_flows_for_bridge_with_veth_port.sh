#!/usr/bin/bash

ofports=(1 2 3)      # ofport id array
ofports_mac=("b6:78:c4:25:ab:2f" "86:78:36:bc:c1:53" "2e:04:f4:69:d3:cd") #对应于ofport 的mac地址数组
ofports_ip=("192.168.10.12" "192.168.10.11" "192.168.10.13")  #对应于ofport的ip地址数组

br_name="br-int"

## table 4: port security;  table 6: arp; table 8: ip; table 12: ingress sg ;table 16: input
tables=(0 4 6 8 12 16)
for i in ${!tables[*]};
do
  `ovs-ofctl add-flow ${br_name} "table=${tables[${i}]},priority=10,actions=drop"`
done


for i in ${!ofports[*]};
do
ovs-ofctl add-flow br-int "table=0,priority=100,in_port=1,actions=goto_table:4"
  `ovs-ofctl add-flow ${br_name} "table=0,priority=100,in_port=${i},actions=goto_table:4"`
  `ovs-ofctl add-flow ${br_name} "table=4,priority=100,in_port=${i},dl_src=${ofports_mac[$i]},actions=goto_table:8"`
  `ovs-ofctl add-flow ${br_name} "table=4,priority=200,arp,in_port=${i},dl_src=${ofports_mac[$i]},actions=goto_table:6"`
  `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=1,arp_tpa=${ofports_ip[$i]} actions=move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],set_field:${ofports_mac[$i]}->eth_src,set_field:${ofports_mac[$i]}->arp_sha,set_field:${ofports_ip[$i]}->arp_spa,set_field:2->arp_op,IN_PORT"`
  `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=2,arp_tpa=${ofports_ip[$i]},dl_src=${ofports_mac[$i]} actions=output:${i}"`
  `ovs-ofctl add-flow ${br_name} "table=8,priority=100,ip,nw_dst=${ofports_ip[$i]},actions=set_field:${ofports[$i]}->reg5,goto_table:12"`
  `ovs-ofctl add-flow ${br_name} "table=12,priority=100,actions=goto_table:16"`
  `ovs-ofctl add-flow ${br_name} "table=16,priority=100,reg5=${i}, actions=output:${i}"`
done
