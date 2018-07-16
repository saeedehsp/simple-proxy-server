from socket import AF_INET, SOCK_DGRAM  # For setting up the UDP socket.
import sys
import socket
import struct  # For constructing and destructing the DNS packet.

# Construct the DNS packet of header + QNAME + QTYPE + QCLASS.

# Get the host name from the command line.

host_name_to_look_up = "";
T_A = 1  # Ipv4 address
T_CNAME = 5  # canonical name

address = sys.argv[2]
port = sys.argv[3]
query_type = int(sys.argv[4])

try:

    host_name_to_look_up = sys.argv[1];

except IndexError:

    print "No host name specified.";

    sys.exit(0);


# build the DNS packets to be sent with asingle questiom
def DNSquery(host, type, Class):
    packet = struct.pack("!H", 12049)  # Query Ids (Just 1 for now)
    packet += struct.pack("!H", 0)  # Flags
    packet += struct.pack("!H", 1)  # Questions
    packet += struct.pack("!HHH", 0, 0, 0)  # Answers , Additional RR , info
    for name in host:  # add url to pack
        packet += struct.pack("!B", len(name))
        for byte in name:
            packet += struct.pack("!c", byte.encode('utf-8'))
    packet = packet + struct.pack("!bHH", 0, type, Class)
    return packet


# check and merge 2 bytes to a  single byte
def chk(chunk):
    if len(chunk) == 2:
        temp = ord(chunk[0])
        temp1 = ord(chunk[1])
        return temp * 256 + temp1
    else:
        return ord(chunk[0]) * 16777216 + ord(chunk[1]) * 65536 + ord(chunk[2]) * 256 + ord(chunk[3])


print_name = ""
print_right = ""
l = [None] * 6


def decode_A(data):
    print "Non-authoritative answer:"
    # decode header
    for i in xrange(0, 12, 2):
        # print ord(data[i]) , ord(data[i+1])
        l[i / 2] = chk(data[i] + data[i + 1])
    # print l[i/2]
    ans_count = l[3]
    question_count = l[2]
    i = 0
    name = []
    # print l[3]
    i += 12
    # usign rfc1035
    # get name of question
    while (ord(data[i]) > 0):
        length = ord(data[i])
        i += 1
        x = []
        for k in xrange(length):
            # print ord(data[i+k])
            x.append(chr(ord(data[i + k])))
        name.append(''.join(x))
        i += length
    print_name = ".".join(name)
    i += 1
    # get query type of question
    q_type = chk(data[i:i + 2])
    i += 2
    # get query class
    q_class = chk(data[i:i + 2])
    i += 2
    prev = print_name
    # for number of answers
    for _ in xrange(ans_count):
        while (ord(data[i]) > 0):
            # print ord(data[i])
            i += 1
        a_type = chk(data[i:i + 2])
        i += 2
        # print a_type
        # for type A
        if a_type == 1:
            # get each of class ttl datalen out
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            ip = []
            # print a_datalen
            for __ in xrange(a_datalen):
                ip.append(str(ord(data[i + __])))
            i += a_datalen
            # get the ip address and print in the format
            print "Name: ", prev
            print "Address: ", ".".join(ip)
        # for query type CNAME, SOA
        elif a_type == 5 or a_type == 6:
            # get class, ttl ,datalen
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            y = []
            tt = i
            length = ord(data[i])
            # get the following address path of canonical name
            while length > 0 and length <= 15:
                i += 1
                x = []
                for _l in xrange(length):
                    x.append(chr(ord(data[i + _l])))
                y.append("".join(x))
                i += length
                length = ord(data[i])
            print  prev, "\t canonical name = ", ".".join(y)
            prev = ".".join(y)
            # i+=a_datalen
            i += 2
        else:
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            i += a_datalen
    # stop if the question query type = 1 or A
    if q_type == 1:
        return
    # authoritative answers
    print "\nAuthoritative answers can be found from:"
    print prev
    ky = 0
    part = []
    # authoritaive answers same as non authoritative just addition of query type NS
    for _ in xrange(l[4] + l[5]):

        while (ord(data[i]) > 0):
            # print ord(data[i])
            i += 1
        a_type = chk(data[i:i + 2])
        i += 2
        # print a_type
        if a_type == 2:
            # query type ns
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            y = []
            tt = i
            # print name servers
            length = ord(data[i])
            while length > 0 and length < 15:
                i += 1
                x = []
                for _l in xrange(length):
                    x.append(chr(ord(data[i + _l])))
                y.append("".join(x))
                i += length
                length = ord(data[i])
            # print nameservers
            print  print_name, "nameserver = ", ".".join(y)
            prev = ".".join(y)
            part.append(prev)
            # i+=a_datalen
            i += 2
        elif a_type == 5 or a_type == 6:
            # type 5, 6 CNAME , SOA , done from above
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            y = []
            tt = i
            length = ord(data[i])
            while length > 0 and length < 15:
                i += 1
                x = []
                for _l in xrange(length):
                    x.append(chr(ord(data[i + _l])))
                y.append("".join(x))
                i += length
                length = ord(data[i])
            print  prev, "\t address = ", ".".join(y)
            prev = ".".join(y)
            # i+=a_datalen
            i += 2
        elif a_type == 1:
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            ip = []
            # print a_datalen
            for __ in xrange(a_datalen):
                ip.append(str(ord(data[i + __])))
            i += a_datalen
            print "Name: ", part[ky]
            ky += 1
            print "Address: ", ".".join(ip)
        else:
            a_class = chk(data[i:i + 2])
            i += 2
            a_ttl = chk(data[i:i + 4])
            i += 4
            a_datalen = chk(data[i:i + 2])
            i += 2
            i += a_datalen


# send packets to server , port taken in arguments
packet = DNSquery(host_name_to_look_up.split("."), query_type, 1)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 8888))
sock.settimeout(5)
sock.sendto(bytes(packet), (address, int(port)))
try:
    data, addr = sock.recvfrom(1024)
except Exception, e:
    print  "Timeout Occured"
# print(len(data))
sock.close()
# print the server and address used
print "Server:\t\t", address
print "Address:\t", address + "#" + port
print "\n"
try:
    # for i in data:
    # 	print (ord(i))
    decode_A(data)
except Exception, e:
    print "Please check the url and dns address again"
    sock.close()
    sys.exit(0)
