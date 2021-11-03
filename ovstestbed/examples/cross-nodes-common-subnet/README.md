## 跨节点同子网 tap互通
   在node1 和node2 分别创建网桥及相关tap口，下发流表

### 初始化br-int网桥
```txt
  #!/usr/bin/bash

## add tunnel
bridge=br-int
ovs-vsctl -- --may-exist add-br $bridge 
ovs-vsctl set-fail-mode $bridge secure
ovs-vsctl set bridge $bridge other-config:disable-in-band=true
#ovs-vsctl set Bridge $bridge protocols=OpenFlow15
#ovs-vsctl set-controller br-int tcp:127.0.0.1:6653 
ovs-vsctl add-port $bridge vxlan1  -- set interface vxlan1 type=vxlan option:key=flow option:remote_ip=flow
```

### 流量镜像
```txt
ip link add tap1 type dummy
ip link set tap1 up

ovs-vsctl add-port br-int tap1 -- --id=@p get port tap1  -- --id=@m create mirror name=m0 select-all=true output-port=@p -- set bridge br-int mirrors=@m

ovs-vsctl clear bridge br-int mirrors	
```

### hping打流
```txt
server:
ip netns exec nsdev-2 python -m SimpleHTTPServer 80

client:
ip netns exec nsdev-3 hping3 -I nsdev3-tap1 -S  192.168.10.12 -p 80
```
