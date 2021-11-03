#!/usr/bin/bash

ofports=(1 2 3)      # ofport id array
ofports_mac=("26:6b:0b:9a:2c:f1" "26:4a:e2:c2:39:58" "d6:96:bc:42:04:ae") #对应于ofport 的mac地址数组
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
  `ovs-ofctl add-flow ${br_name} "table=0,priority=100,in_port=${ofports[$i]},actions=set_field:${ofports[$i]}->reg7,goto_table:4"`
  `ovs-ofctl add-flow ${br_name} "table=4,priority=100,reg7=${ofports[$i]},dl_src=${ofports_mac[$i]},actions=goto_table:8"`
  `ovs-ofctl add-flow ${br_name} "table=4,priority=200,arp,reg7=${ofports[$i]},dl_src=${ofports_mac[$i]},actions=goto_table:6"`
  `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=1,arp_tpa=${ofports_ip[$i]} actions=move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],set_field:${ofports_mac[$i]}->eth_src,set_field:${ofports_mac[$i]}->arp_sha,set_field:${ofports_ip[$i]}->arp_spa,set_field:2->arp_op,IN_PORT"`
  `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=2,arp_tpa=${ofports_ip[$i]},dl_src=${ofports_mac[$i]} actions=output:${ofports[$i]}"`
  `ovs-ofctl add-flow ${br_name} "table=8,priority=100,ip,nw_dst=${ofports_ip[$i]},actions=set_field:${ofports[$i]}->reg5,goto_table:12"`
  `ovs-ofctl add-flow ${br_name} "table=12,priority=100,actions=goto_table:16"`
  `ovs-ofctl add-flow ${br_name} "table=16,priority=100,reg5=${ofports[$i]}, actions=output:${ofports[$i]}"`

  `ovs-ofctl add-flow ${br_name} "table=50,priority=100,ip,nw_dst=${ofports_ip[$i]},actions=output:${ofports[$i]}"`
done

remote_tunnel_ip="192.168.119.128"
tunnel_ofports=(4)
for i in ${!tunnel_ofports[*]};
do
  `ovs-ofctl add-flow ${br_name} "table=0,priority=100,in_port=${tunnel_ofports[$i]},actions=set_field:${tunnel_ofports[$i]}->reg7,goto_table:40"`
  `ovs-ofctl add-flow ${br_name} "table=16,priority=100,reg5=${tunnel_ofports[$i]}, actions=set_field:fa:16:3e:ee:ff:ff->dl_src,set_field:${remote_tunnel_ip}->tun_dst,output:${tunnel_ofports[$i]}"`
done


tunnel_tables=(40 45 50)

for i in ${!tunnel_tables[*]};
do
  `ovs-ofctl add-flow ${br_name} "table=${tunnel_tables[${i}]},priority=10,actions=drop"`
done

for i in ${!tunnel_ofports[*]};
do
  `ovs-ofctl add-flow ${br_name} "table=40,priority=100, reg7=${tunnel_ofports[$i]}, actions=goto_table:45"`
  `ovs-ofctl add-flow ${br_name} "table=45,priority=100, actions=goto_table:50"`
  #`ovs-ofctl add-flow ${br_name} "table=50,priority=100, actions=resubmit:8"`
done

remote_ofports_ip=("192.168.10.22" "192.168.10.21" "192.168.10.23")
remote_ofports_mac=("6a:c3:9a:ca:6c:32" "8a:d0:4c:03:95:60" "42:0f:16:6b:ef:d5")

for i in ${!ofports[*]};
do
  for i in ${!remote_ofports_ip[*]};
  do
    `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=1,arp_tpa=${remote_ofports_ip[$i]} actions=move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],set_field:${remote_ofports_mac[$i]}->eth_src,set_field:${remote_ofports_mac[$i]}->arp_sha,set_field:${remote_ofports_ip[$i]}->arp_spa,set_field:2->arp_op,IN_PORT"`
    `ovs-ofctl add-flow ${br_name} "table=6,priority=100,arp,arp_op=2,arp_tpa=${remote_ofports_ip[$i]},dl_src=${remote_ofports_mac[$i]} actions=output:${ofports[$i]}"`
  done
done

for i in ${!remote_ofports_ip[*]};
do
    `ovs-ofctl add-flow ${br_name} "table=8,priority=100,ip,nw_dst=${remote_ofports_ip[$i]},actions=set_field:${tunnel_ofports[0]}->reg5,goto_table:12"`
done

