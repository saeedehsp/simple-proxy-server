from socket import *
import time, sys, signal


def handler(signum, frame):
    raise Exception("")


signal.signal(signal.SIGALRM, handler)
# makke cache of packets recieved and sent
cache = {}
Port = 12001
i = 0
now = time.time()
# 20 request to prevent port usage cannot use error
while i < 1000:
    if time.time() - now >= 300:
        cache.clear()
        now = time.time()
    print "Listening on port 12001"
    # recieve dns query
    socket1 = socket(AF_INET, SOCK_DGRAM)
    socket1.bind(('', Port))
    # forward to 127.0.1.1 - local dns server
    message, addr1 = socket1.recvfrom(1024)
    if message[2:] in cache.keys():
        socket1.sendto(message[0:2] + cache[message[2:]], addr1)
        print "Used Cache"
        continue
    else:
        socket1.sendto(message, ("127.0.1.1", 53))
        print "Query sent"
        message1, addr = socket1.recvfrom(10000)
        socket1.sendto(message1, addr1)
        if len(message1) > len(message):
            cache[message[2:]] = message1[2:]
    print  "DNS query replied"
    i += 1

socket1.close()
