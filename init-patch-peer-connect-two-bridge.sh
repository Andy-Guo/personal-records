ovs-vsctl add-br br-int
ovs-vsctl add-br br-mirror
//in mirrors
ovs-vsctl add-port br-int patch-to-mr-in
ovs-vsctl set interface patch-to-mr-in type=patch options:peer=patch-to-int-in
ovs-vsctl add-port br-mirror patch-to-int-in
ovs-vsctl set interface patch-to-int-in type=patch options:peer=patch-to-mr-in

//out mirrors
ovs-vsctl add-port br-mirror patch-to-int-out
ovs-vsctl set interface patch-to-int-out type=patch options:peer=patch-to-mr-out
ovs-vsctl add-port br-int patch-to-mr-out
ovs-vsctl set interface patch-to-mr-out type=patch options:peer=patch-to-int-out
