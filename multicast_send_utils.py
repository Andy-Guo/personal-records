#
# Copyright (c) 2015 Intel, Inc., Cisco Systems, Inc. and others.  All rights
# reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html
import socket, sys, os
import argparse
from struct import *
from ctypes import Structure, c_ubyte, c_ushort, c_uint

NSH_TYPE1_LEN = 0x6
NSH_MD_TYPE1 = 0x1
NSH_VERSION1 = int('00', 2)
NSH_NEXT_PROTO_IPV4 = int('00000001', 2)
NSH_NEXT_PROTO_OAM = int('00000100', 2)
NSH_NEXT_PROTO_ETH = int('00000011', 2)
NSH_FLAG_ZERO = int('00000000', 2)

IP_HEADER_LEN = 5
IPV4_HEADER_LEN_BYTES = 20
IPV4_VERSION = 4
IPV4_PACKET_ID = 54321
IPV4_FLAG_OFFSET = 0x4000
IPV4_TTL = 255
IPV4_TOS = 0
IPV4_IHL_VER = (IPV4_VERSION << 4) + IP_HEADER_LEN

UDP_HEADER_LEN_BYTES = 8

VXLAN_DPORT = 4789
VXLAN_GPE_DPORT = 4790
OLD_VXLAN_GPE_DPORT = 6633

IPV4_PROTO_IGMP = 0x2
IGMPv2_TYPE_MEMREPORT = 0x16
IGMPv2_MEMREPORT_LEN = 8
IGMP_MAX_RES_TIME = 100
IGMP_DEFAULT_GROUP_ADDR = "239.0.1.1"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class VXLAN(Structure):
    _fields_ = [('flags', c_ubyte),
                ('reserved', c_uint, 16),
                ('next_protocol', c_uint, 8),
                ('vni', c_uint, 24),
                ('reserved2', c_uint, 8)]

    def __init__(self, flags=int('00001000', 2), reserved=0, next_protocol=0,
                 vni=int('111111111111111111111111', 2), reserved2=0, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.flags = flags
        self.reserved = reserved
        self.next_protocol = next_protocol
        self.vni = vni
        self.reserved2 = reserved2

    header_size = 8

    def build(self):
        return pack('!B H B I',
                    self.flags,
                    self.reserved,
                    self.next_protocol,
                    (self.vni << 8) + self.reserved2)

class ETHHEADER(Structure):
    _fields_ = [('dmac0', c_ubyte),
                ('dmac1', c_ubyte),
                ('dmac2', c_ubyte),
                ('dmac3', c_ubyte),
                ('dmac4', c_ubyte),
                ('dmac5', c_ubyte),
                ('smac0', c_ubyte),
                ('smac1', c_ubyte),
                ('smac2', c_ubyte),
                ('smac3', c_ubyte),
                ('smac4', c_ubyte),
                ('smac5', c_ubyte),
                ('ethertype0', c_ubyte),
                ('ethertype1', c_ubyte)]

    header_size = 14

    def build(self):
        return pack('!B B B B B B B B B B B B B B',
                    self.dmac0,
                    self.dmac1,
                    self.dmac2,
                    self.dmac3,
                    self.dmac4,
                    self.dmac5,
                    self.smac0,
                    self.smac1,
                    self.smac2,
                    self.smac3,
                    self.smac4,
                    self.smac5,
                    self.ethertype0,
                    self.ethertype1)

class BASEHEADER(Structure):
    """
    Represent a NSH base header
    """
    _fields_ = [('version', c_ushort, 2),
                ('flags', c_ushort, 8),
                ('length', c_ushort, 6),
                ('md_type', c_ubyte),
                ('next_protocol', c_ubyte),
                ('service_path', c_uint, 24),
                ('service_index', c_uint, 8)]

    def __init__(self, service_path=1, service_index=255, version=NSH_VERSION1, flags=NSH_FLAG_ZERO,
                 length=NSH_TYPE1_LEN, md_type=NSH_MD_TYPE1, proto=NSH_NEXT_PROTO_ETH, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.version = version
        self.flags = flags
        self.length = length
        self.md_type = md_type
        self.next_protocol = proto
        self.service_path = service_path
        self.service_index = service_index

    header_size = 8

    def build(self):
        return pack('!H B B I',
                    (self.version << 14) + (self.flags << 6) + self.length,
                    self.md_type,
                    self.next_protocol,
                    (self.service_path << 8) + self.service_index)


class CONTEXTHEADER(Structure):
    _fields_ = [('network_platform', c_uint),
                ('network_shared', c_uint),
                ('service_platform', c_uint),
                ('service_shared', c_uint)]

    header_size = 16

    def __init__(self, network_platform=0x00, network_shared=0x00, service_platform=0x00, service_shared=0x00, *args,
                 **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.network_platform = network_platform
        self.network_shared = network_shared
        self.service_platform = service_platform
        self.service_shared = service_shared

    def build(self):
        return pack('!I I I I',
                    self.network_platform,
                    self.network_shared,
                    self.service_platform,
                    self.service_shared)

class IP4HEADER(Structure):
    _fields_ = [
        ('ip_ihl', c_ubyte),
        ('ip_ver', c_ubyte),
        ('ip_tos', c_ubyte),
        ('ip_tot_len', c_ushort),
        ('ip_id', c_ushort),
        ('ip_frag_offset', c_ushort),
        ('ip_ttl', c_ubyte),
        ('ip_proto', c_ubyte),
        ('ip_chksum', c_ushort),
        ('ip_saddr', c_uint),
        ('ip_daddr', c_uint)]

    header_size = 20

    def build(self):
        ip_header_pack = pack('!B B H H H B B H I I', IPV4_IHL_VER, self.ip_tos, self.ip_tot_len, self.ip_id,
                              self.ip_frag_offset, self.ip_ttl, self.ip_proto, self.ip_chksum, self.ip_saddr,
                              self.ip_daddr)
        return ip_header_pack

    def set_ip_checksum(self, checksum):
        self.ip_chksum = checksum

class IGMPv2MEMREPORTERHEADER(Structure):
    _fields_ = [
	('type', c_ubyte),
        ('max_resp_time', c_ubyte),
	('checksum', c_ushort),
        ('group_ipv4', c_uint)]
    header_size = 8

    def build(self):
	igmpv2_memrep_pack = pack('!B B H I',self.type, self.max_resp_time, self.checksum, self.group_ipv4)
	return igmpv2_memrep_pack
		
    def set_checksum(self, checksum):
	self.checksum = checksum

class UDPHEADER(Structure):
    """
    Represents a UDP header
    """
    _fields_ = [
        ('udp_sport', c_ushort),
        ('udp_dport', c_ushort),
        ('udp_len', c_ushort),
        ('udp_sum', c_ushort)]

    header_size = 8

    def build(self):
        udp_header_pack = pack('!H H H H', self.udp_sport, self.udp_dport, self.udp_len,
                               self.udp_sum)
        return udp_header_pack

class PSEUDO_UDPHEADER(Structure):
    """ Pseudoheader used in the UDP checksum."""

    def __init__(self):
        self.src_ip = 0
        self.dest_ip = 0
        self.zeroes = 0
        self.protocol = 17
        self.length = 0

    def build(self):
        """ Create a string from a pseudoheader """
        p_udp_header_pack = pack('!I I B B H', self.src_ip, self.dest_ip,
                                 self.zeroes, self.protocol, self.length)
        return p_udp_header_pack

class TCPHEADER(Structure):
    """
    Represents a TCP header
    """
    _fields_ = [
        ('tcp_sport', c_ushort),
        ('tcp_dport', c_ushort),
        ('tcp_len', c_ushort),
        ('tcp_sum', c_ushort)]

    header_size = 8


def decode_eth(payload, offset, eth_header_values):
    eth_header = payload[offset:(offset+14)]

    _header_values = unpack('!B B B B B B B B B B B B B B', eth_header)
    eth_header_values.dmac0 = _header_values[0]
    eth_header_values.dmac1 = _header_values[1]
    eth_header_values.dmac2 = _header_values[2]
    eth_header_values.dmac3 = _header_values[3]
    eth_header_values.dmac4 = _header_values[4]
    eth_header_values.dmac5 = _header_values[5]
    eth_header_values.smac0 = _header_values[6]
    eth_header_values.smac1 = _header_values[7]
    eth_header_values.smac2 = _header_values[8]
    eth_header_values.smac3 = _header_values[9]
    eth_header_values.smac4 = _header_values[10]
    eth_header_values.smac5 = _header_values[11]
    eth_header_values.ethertype0 = _header_values[12]
    eth_header_values.ethertype1 = _header_values[13]

def decode_ip(payload, ip_header_values):
    ip_header = payload[14:34]

    _header_values = unpack('!B B H H H B B H I I', ip_header)
    ip_header_values.ip_ihl = _header_values[0] & 0x0F
    ip_header_values.ip_ver = _header_values[0] >> 4
    ip_header_values.ip_tos = _header_values[1]
    ip_header_values.ip_tot_len = _header_values[2]
    ip_header_values.ip_id = _header_values[3]
    ip_header_values.ip_frag_offset = _header_values[4]
    ip_header_values.ip_ttl = _header_values[5]
    ip_header_values.ip_proto = _header_values[6]
    ip_header_values.ip_chksum = _header_values[7]
    ip_header_values.ip_saddr = _header_values[8]
    ip_header_values.ip_daddr = _header_values[9]

def decode_udp(payload, udp_header_values):
    udp_header = payload[34:42]

    _header_values = unpack('!H H H H', udp_header)
    udp_header_values.udp_sport = _header_values[0]
    udp_header_values.udp_dport = _header_values[1]
    udp_header_values.udp_len = _header_values[2]
    udp_header_values.udp_sum = _header_values[3]

def decode_tcp(payload, offset, tcp_header_values):
    tcp_header = payload[offset:(offset+8)]

    _header_values = unpack('!H H H H', tcp_header)
    tcp_header_values.tcp_sport = _header_values[0]
    tcp_header_values.tcp_dport = _header_values[1]
    tcp_header_values.tcp_len = _header_values[2]
    tcp_header_values.tcp_sum = _header_values[3]

def decode_vxlan(payload, vxlan_header_values):
    """Decode the VXLAN header for a received packets"""
    vxlan_header = payload[42:50]

    _header_values = unpack('!B H B I', vxlan_header)
    vxlan_header_values.flags = _header_values[0]
    vxlan_header_values.reserved = _header_values[1]
    vxlan_header_values.next_protocol = _header_values[2]

    vni_rsvd2 = _header_values[3]
    vxlan_header_values.vni = vni_rsvd2 >> 8
    vxlan_header_values.reserved2 = vni_rsvd2 & 0x000000FF

def decode_nsh_baseheader(payload, offset, nsh_base_header_values):
    """Decode the NSH base headers for a received packets"""
    base_header = payload[offset:(offset+8)]

    _header_values = unpack('!H B B I', base_header)
    start_idx = _header_values[0]
    nsh_base_header_values.md_type = _header_values[1]
    nsh_base_header_values.next_protocol = _header_values[2]
    path_idx = _header_values[3]

    nsh_base_header_values.version = start_idx >> 14
    nsh_base_header_values.flags = start_idx >> 6
    nsh_base_header_values.length = start_idx >> 0
    nsh_base_header_values.service_path = path_idx >> 8
    nsh_base_header_values.service_index = path_idx & 0x000000FF

def decode_nsh_contextheader(payload, offset, nsh_context_header_values):
    """Decode the NSH context headers for a received packet"""
    context_header = payload[offset:(offset+16)]

    _header_values = unpack('!I I I I', context_header)
    nsh_context_header_values.network_platform = _header_values[0]
    nsh_context_header_values.network_shared = _header_values[1]
    nsh_context_header_values.service_platform = _header_values[2]
    nsh_context_header_values.service_shared = _header_values[3]

def compute_internet_checksum(data):
    """
    Function for Internet checksum calculation. Works
    for both IP and UDP.
    """
    checksum = 0
    n = len(data) % 2
    # data padding
    pad = bytearray('', encoding='UTF-8')
    if n == 1:
        pad = bytearray(b'\x00')
    # for i in range(0, len(data + pad) - n, 2):
    for i in range(0, len(data)-1, 2):
        checksum += (ord(data[i]) << 8) + (ord(data[i + 1]))
    if n == 1:
        checksum += (ord(data[len(data)-1]) << 8) + (pad[0])
    while checksum >> 16:
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum = ~checksum & 0xffff
    return checksum

# Implements int.from_bytes(s, byteorder='big')
def int_from_bytes(s):
    return sum(ord(c) << (i * 8) for i, c in enumerate(s[::-1]))

def build_ethernet_header_swap(myethheader):
    """ Build Ethernet header """
    newethheader=ETHHEADER()
    newethheader.smac0 = myethheader.dmac0
    newethheader.smac1 = myethheader.dmac1
    newethheader.smac2 = myethheader.dmac2
    newethheader.smac3 = myethheader.dmac3
    newethheader.smac4 = myethheader.dmac4
    newethheader.smac5 = myethheader.dmac5

    newethheader.dmac0 = myethheader.smac0
    newethheader.dmac1 = myethheader.smac1
    newethheader.dmac2 = myethheader.smac2
    newethheader.dmac3 = myethheader.smac3
    newethheader.dmac4 = myethheader.smac4
    newethheader.dmac5 = myethheader.smac5

    newethheader.ethertype0 = myethheader.ethertype0
    newethheader.ethertype1 = myethheader.ethertype1
    return newethheader

def build_ipv4_header(ip_tot_len, proto, src_ip, dest_ip, swap_ip):
    """
    Builds a complete IP header including checksum
    """

    if src_ip:
        ip_saddr = socket.inet_aton(src_ip)
    else:
        ip_saddr = socket.inet_aton(socket.gethostbyname(socket.gethostname()))

    if (swap_ip == True):
        new_ip_daddr = int_from_bytes(ip_saddr)
        new_ip_saddr = socket.inet_aton(dest_ip)
        new_ip_saddr = int_from_bytes(new_ip_saddr)
    else:
        new_ip_saddr = int_from_bytes(ip_saddr)
        new_ip_daddr = int_from_bytes(socket.inet_aton(dest_ip))

    ip_header = IP4HEADER(IP_HEADER_LEN, IPV4_VERSION, IPV4_TOS, ip_tot_len, IPV4_PACKET_ID, IPV4_FLAG_OFFSET, IPV4_TTL, proto, 0, new_ip_saddr, new_ip_daddr)

    checksum = compute_internet_checksum(ip_header.build())
    ip_header.set_ip_checksum(checksum)
    ip_header_pack = ip_header.build()

    return ip_header, ip_header_pack

def buld_igmpv2_memreporter_header(type, group_ipv4):
    """
    build a igmpv2 header
    """
    if group_ipv4:
	g_ip = socket.inet_aton(group_ipv4)
    else:
        g_ip = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
    new_g_ip = int_from_bytes(g_ip)
    igmpv2_memrep_header = IGMPv2MEMREPORTERHEADER(type, IGMP_MAX_RES_TIME, 0, new_g_ip)
    checksum = compute_internet_checksum(igmpv2_memrep_header.build())
    igmpv2_memrep_header.set_checksum(checksum)
    igmpv2_memrep_pack = igmpv2_memrep_header.build()
    
    return igmpv2_memrep_header, igmpv2_memrep_pack

def build_udp_header(src_port, dest_port, ip_header, data):
    """
    Building an UDP header requires fields from
    IP header in order to perform checksum calculation
    """

    # build UDP header with sum = 0
    udp_header = UDPHEADER(src_port, dest_port, UDP_HEADER_LEN_BYTES + len(data), 0)
    udp_header_pack = udp_header.build()

    # build Pseudo Header
    p_header = PSEUDO_UDPHEADER()
    p_header.dest_ip = ip_header.ip_daddr
    p_header.src_ip = ip_header.ip_saddr
    p_header.length = udp_header.udp_len

    p_header_pack = p_header.build()

    udp_checksum = compute_internet_checksum(p_header_pack + udp_header_pack + data)
    udp_header.udp_sum = udp_checksum
    # pack UDP header again but this time with checksum
    udp_header_pack = udp_header.build()

    return udp_header, udp_header_pack
	
def build_igmpv2_memrep_packet(src_ip, dest_ip, type, group_ipv4):
    total_len = IPV4_HEADER_LEN_BYTES + IGMPv2_MEMREPORT_LEN
    ip_header, ip_header_pack = build_ipv4_header(total_len, IPV4_PROTO_IGMP, src_ip, dest_ip, False)
    igmpv2_memrpt_hdr, igmpv2_memrpt_pack = buld_igmpv2_memreporter_header(type, group_ipv4)

    igmpv2_memrpt_packet = ip_header_pack + igmpv2_memrpt_pack
    
    return igmpv2_memrpt_packet

def build_udp_packet(src_ip, dest_ip, src_port, dest_port, data, swap_ip):
    """
    Data needs to encoded as Python bytes. In the case of strings
    this means a bytearray of an UTF-8 encoding
    """

    total_len = len(data) + IPV4_HEADER_LEN_BYTES + UDP_HEADER_LEN_BYTES
    # First we build the IP header
    ip_header, ip_header_pack = build_ipv4_header(total_len, socket.IPPROTO_UDP, src_ip, dest_ip, swap_ip)

    # Build UDP header
    udp_header, udp_header_pack = build_udp_header(src_port, dest_port, ip_header, data)

    udp_packet = ip_header_pack + udp_header_pack + data

    return udp_packet

def getmac(interface):
  try:
    mac = open('/sys/class/net/'+interface+'/address').readline()
  except:
    mac = None
  return mac

def getmacbyip(ip):
    os.popen('ping -c 1 %s' % ip)
    fields = os.popen('grep "%s " /proc/net/arp' % ip).read().split()
    if len(fields) == 6 and fields[3] != "00:00:00:00:00:00":
        mac = fields[3]
    else:
        mac = None
    return mac

def print_ethheader(ethheader):
    print("Eth Dst MAC: %.2x:%.2x:%.2x:%.2x:%.2x:%.2x, Src MAC: %.2x:%.2x:%.2x:%.2x:%.2x:%.2x, Ethertype: 0x%.4x" % (ethheader.dmac0, ethheader.dmac1, ethheader.dmac2, ethheader.dmac3, ethheader.dmac4, ethheader.dmac5, ethheader.smac0, ethheader.smac1, ethheader.smac2, ethheader.smac3, ethheader.smac4, ethheader.smac5, (ethheader.ethertype0<<8) | ethheader.ethertype1))

def print_ipheader(ipheader):
    print("IP Version: %s IP Header Length: %s, TTL: %s, Protocol: %s, Src IP: %s, Dst IP: %s" % (ipheader.ip_ver, ipheader.ip_ihl, ipheader.ip_ttl, ipheader.ip_proto, str(socket.inet_ntoa(pack('!I', ipheader.ip_saddr))), str(socket.inet_ntoa(pack('!I', ipheader.ip_daddr)))))

def print_udpheader(udpheader):
    print ("UDP Src Port: %s, Dst Port: %s, Length: %s, Checksum: %s" % (udpheader.udp_sport, udpheader.udp_dport, udpheader.udp_len, udpheader.udp_sum))

def print_vxlanheader(vxlanheader):
    print("VxLAN/VxLAN-gpe VNI: %s, flags: %.2x, Next: %s" % (vxlanheader.vni, vxlanheader.flags, vxlanheader.next_protocol))

def print_nsh_baseheader(nshbaseheader):
    print("NSH base nsp: %s, nsi: %s" % (nshbaseheader.service_path, nshbaseheader.service_index))

def print_nsh_contextheader(nshcontextheader):
    print("NSH context c1: 0x%.8x, c2: 0x%.8x, c3: 0x%.8x, c4: 0x%.8x" % (nshcontextheader.network_platform, nshcontextheader.network_shared, nshcontextheader.service_platform, nshcontextheader.service_shared))

def main():
    parser = argparse.ArgumentParser(description='This is a UDP dump and forward tool, you can use it to dump and forward VxLAN/VxLAN-gpe + NSH packets, it can also act as an NSH-aware SF for SFC test when you use --forward option, in that case, it will automatically decrease nsi by one.', prog='vxlan_tool.py')
    parser.add_argument('-i', '--interface',
                        help='Specify the interface to listen')
    parser.add_argument('-o', '--output',
                        help='Specify the interface to send on')
    parser.add_argument('-d', '--do', choices=['dump', 'forward', 'nsh_proxy', 'send'],
                        help='dump/foward/send VxLAN/VxLAN-gpe + NSH or Eth + NSH packet')
    parser.add_argument('-t', '--type', choices=['eth_nsh', 'vxlan_gpe_nsh', 'udp'], default='vxlan_gpe_nsh',
                        help='Specify packet type for send: eth_nsh or vxlan_gpe_nsh')
    parser.add_argument('--outer-source-mac',
                        help='Specify outer source MAC for packet send')
    parser.add_argument('--outer-destination-mac',
                        help='Specify outer destination MAC for packet send')
    parser.add_argument('--outer-source-ip',
                        help='Specify outer source IP address for packet send')
    parser.add_argument('--outer-destination-ip',
                        help='Specify outer destination IP address for packet send')
    parser.add_argument('--outer-source-udp-port', type=int,
                        help='Specify outer source UDP port for packet send')
    parser.add_argument('--outer-destination-udp-port', type=int,
                        help='Specify outer destination UDP port for packet send')
    parser.add_argument('-n', '--number', type=int,
                        help='Specify number of packet to send')
    parser.add_argument('-igmpt', '--igmp-type', type=int,
                        help='Specify the type of igmp protocol')
    parser.add_argument('--mc-group-ip',
                        help='Specify the group ip address of igmp protocol')
    parser.add_argument('-igmp', '--igmp-enabled', type=int,
                        help='Specify if enable the igmp')						
    parser.add_argument('--no-swap-ip', dest='swap_ip', default=True, action='store_false',
                        help="won't swap ip if provided")
    parser.add_argument('-v', '--verbose', choices=['on', 'off'],
                        help='dump packets when in forward mode')
    parser.add_argument('--block', '-b', type=int, default=0,
                        help='Acts as a firewall dropping packets that match this TCP dst port')
    parser.add_argument('--source-block', type=int, default=0,
                        help='Acts as a firewall dropping packets that match this TCP src port')

    args = parser.parse_args()
    macaddr = None

    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
        if args.interface is not None:
            s.bind((args.interface, 0))
        output = args.output if args.output else args.interface
        if ((args.do == "forward") or (args.do == "nsh_proxy") or (args.do == "send")):
            if output is None:
                print("Error: you must specify the interface for forward and send")
                sys.exit(-1)
            send_s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            send_s.bind((output, 0))
        if args.interface is not None:
            macstring = getmac(args.interface)
            if (macstring is not None):
                macaddr = macstring.strip().split(':')
        if output is not None:
            output_macstring = getmac(output)
        if (args.do == "send"):
            if (args.outer_source_mac is None):
                args.outer_source_mac = args.inner_source_mac
            if (args.outer_destination_mac is None):
                args.outer_destination_mac = args.inner_destination_mac
            if (args.outer_source_ip is None):
                args.outer_source_ip = args.inner_source_ip
            if (args.outer_destination_ip is None):
                args.outer_destination_ip = args.inner_destination_ip
            if (args.outer_source_udp_port is None):
                args.outer_source_udp_port = 55651
            if (args.outer_destination_udp_port is None):
                args.outer_destination_udp_port = 25
	    if (args.igmp_type is None):
                args.igmp_type = IGMPv2_TYPE_MEMREPORT
            if (args.mc_group_ip is None):
                args.mc_group_ip = IGMP_DEFAULT_GROUP_ADDR
            if (args.igmp_enabled is None):
                args.igmp_enabled = 0			
            if (args.number is None):
                args.number = 10

    except OSError as e:
        print("{}".format(e) + " '%s'" % args.interface)
        sys.exit(-1)

    do_print = ((args.do != "forward") or (args.verbose == "on"))

    vxlan_gpe_udp_ports = [VXLAN_GPE_DPORT, OLD_VXLAN_GPE_DPORT]
    vxlan_udp_ports = [VXLAN_DPORT] + vxlan_gpe_udp_ports

    #header len
    eth_length = 14
    ip_length = 20
    udp_length = 8
    vxlan_length = 8
    nshbase_length = 8
    nshcontext_length = 16

    """ For NSH proxy """
    vni = 0;
    # NSP+NSI to VNI Mapper
    nsh_to_vni_mapper = {}
    # VNI to NSH Mapper
    vni_to_nsh_mapper = {}

    """ Send VxLAN/VxLAN-gpe + NSH packet """
    if (args.do == "send"):
        myethheader = ETHHEADER()
        myipheader = IP4HEADER()
        myudpheader = UDPHEADER()

        """ Set Ethernet header """
        dstmacaddr = args.outer_destination_mac.split(":")
        myethheader.dmac0 = int(dstmacaddr[0], 16)
        myethheader.dmac1 = int(dstmacaddr[1], 16)
        myethheader.dmac2 = int(dstmacaddr[2], 16)
        myethheader.dmac3 = int(dstmacaddr[3], 16)
        myethheader.dmac4 = int(dstmacaddr[4], 16)
        myethheader.dmac5 = int(dstmacaddr[5], 16)

        myethheader.smac0 = int(macaddr[0], 16)
        myethheader.smac1 = int(macaddr[1], 16)
        myethheader.smac2 = int(macaddr[2], 16)
        myethheader.smac3 = int(macaddr[3], 16)
        myethheader.smac4 = int(macaddr[4], 16)
        myethheader.smac5 = int(macaddr[5], 16)

        myethheader.ethertype0 = 0x08
        myethheader.ethertype1 = 0x00

        if (args.igmp_enabled == 0):
            outerippack = build_udp_packet(args.outer_source_ip, args.outer_destination_ip, args.outer_source_udp_port, args.outer_destination_udp_port, "Hellow, World!!!".encode('utf-8'), False)
        else:
	    outerippack = build_igmpv2_memrep_packet(args.outer_source_ip, args.outer_destination_ip, args.igmp_type, args.mc_group_ip)
			
        """ Build Ethernet packet """
        ethpkt = myethheader.build() + outerippack

        """ Decode ethernet header """
        decode_eth(ethpkt, 0, myethheader)

        pktnum = 0
        while (args.number > 0):
            """ Send it and make sure all the data is sent out """
            pkt = ethpkt
            while pkt:
                sent = send_s.send(pkt)
                args.number -= 1
                pkt = pkt[sent:]
            pktnum += 1
         #   if (do_print):
         #       print("\n\nSent Packet #%d" % pktnum)

            """ Print ethernet header """
         #   if (do_print):
         #       print_ethheader(myethheader)

        sys.exit(0)

### 发送UDP 报文
# python igmpv2-send-tools.py -i eth0 -d send --outer-source-mac fa:16:3e:e1:e9:b9 --outer-destination-mac fa:16:3e:66:9f:b9 --outer-source-ip  192.168.2.7 --outer-destination-ip 192.168.2.170 --outer-source-udp-port 11404 --outer-destination-udp-port 80 -n 1
### IGMPv2 
### 发送组播包
# python igmpv2-send-tools.py -i port-1z6lvgdiiy -d send --outer-source-mac fa:16:3e:b8:7c:06 --outer-destination-mac 01:00:5e:00:01:01 --outer-source-ip 10.1.10.5 --outer-destination-ip 239.0.1.1 --outer-source-udp-port 11404 --outer-destination-udp-port 12345 -n 1
### 发送IGMP member report 报文
# python igmpv2-send-tools.py -i port-1z6lvgdiiy -d send --outer-source-mac fa:16:3e:b8:7c:06 --outer-destination-mac 1:00:5e:00:01:01 --outer-source-ip 10.1.10.5 --outer-destination-ip 239.0.1.1 --igmp-type 22 --mc-group-ip 239.0.1.1 --igmp-enabled 1 -n 1
### 发送IGMP leave 报文
# python igmpv2-send-tools.py -i port-1z6lvgdiiy -d send --outer-source-mac fa:16:3e:b8:7c:06 --outer-destination-mac 1:00:5e:00:01:01 --outer-source-ip 10.1.10.5 --outer-destination-ip 239.0.1.1 --igmp-type 23 --mc-group-ip 239.0.1.1 --igmp-enabled 1 -n 1

if __name__ == "__main__":
    main()
