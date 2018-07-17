# coding=utf-8
import datetime
import threading
import traceback
import SocketServer
import sys
from socket import *
from dnslib import *


class DomainName(str):
    def __getattr__(self, item):
        return DomainName(item + '.' + self)


IP = '127.0.0.1'
TTL = 60 * 5
PORT = 5053
CACHE_DURATION = 10  # Seconds

dns_cache = []


def request_dns_by_udp(data):
    for req in dns_cache:
        req_data, req_time, req_res = req
        if (datetime.datetime.now()-req_time).total_seconds() > CACHE_DURATION:
            dns_cache.remove(req)
            continue
        if req_data == data:
            print "from cache"
            return req_res

    # Creates a new udp socket to a real DNS Server, sends data to it and returns it's result
    udp_socket = socket.socket(AF_INET, SOCK_DGRAM)
    udp_socket.sendto(data, ("8.8.8.8", 53))
    message, addr = udp_socket.recvfrom(10000)
    udp_socket.close()
    dns_cache.append((data, datetime.datetime.now(), message))
    return message


def request_http_by_tcp(data):
    # TODO: Create a new tcp socket to a real HTTP Server, send data to it and return it's result
    pass


class BaseRequestHandler(SocketServer.BaseRequestHandler):

    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        print "\n\n%s request %s (%s %s):" % (
            self.__class__.__name__[:3],
            now,
            self.client_address[0],
            self.client_address[1]
        )
        try:
            is_udp = isinstance(self, UDPRequestHandler)
            data = self.get_data()
            if is_udp:
                data = request_http_by_tcp(data)
            else:
                data = request_dns_by_udp(data)
            print len(data), data.encode('hex')  # repr(data).replace('\\x', '')[1:-1]
            self.send_data(data)
        except Exception:
            traceback.print_exc(file=sys.stderr)


class TCPRequestHandler(BaseRequestHandler):

    def get_data(self):
        data = self.request.recv(8192)
        sz = int(data[:2].encode('hex'), 16)
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send_data(self, data):
        sz = hex(len(data))[2:].zfill(4).decode('hex')
        return self.request.sendall(sz + data)


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0]

    def send_data(self, data):
        return self.request[1].sendto(data, self.client_address)


if __name__ == '__main__':
    print "Starting nameserver..."

    servers = [
        SocketServer.ThreadingUDPServer(('', PORT), UDPRequestHandler),
        SocketServer.ThreadingTCPServer(('', PORT), TCPRequestHandler),
    ]

    for s in servers:
        thread = threading.Thread(target=s.serve_forever)  # that thread will start one more thread for each request
        thread.daemon = True  # exit the server thread when the main thread terminates
        thread.start()
        print "%s server loop running in thread: %s" % (s.RequestHandlerClass.__name__[:3], thread.name)

    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.shutdown()
