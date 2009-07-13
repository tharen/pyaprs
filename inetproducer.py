#inetproducer.py

import Queue,datetime,time
import socket,select
import logging

from aprsproducer import Producer
from aprspacket import BasicPacket

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info
exception=my_logger.exception

class Main(Producer):
    def __init__(self,parameters,name,timeout=10,throttle=0.1):
        Producer.__init__(self,parameters,name)
        self.timeout=timeout #seconds to wait for a response from the socket
        self.throttle=throttle #seconds to pause between socket reads
        self.socket=None
        self.socketBuffer=''
        #self.parameters.__getattribute__(name)  #parameters are in a section titled [self.name]

    def start(self):
        self.__openSocket()
        while 1:
            try:
                #select returns 3 lists of sockets
                ##TODO: timeout is unnecessary if running in a private thread
                readReady,writeReady,inError=select.select([self.socket,],[],[],self.timeout)
                if self.socket in readReady:
                    self.__handleData()
            except:
                ##TODO: seperate select exceptions from other errors
                ##          ie. network failures, disapearing host, etc
                exception('Select failed, attempt to reopen socket')
                time.sleep(0.2)
                self.__openSocket()

            time.sleep(self.pollInterval)

    def __openSocket(self):
        self.socket=socket.socket(
                family=socket.AF_INET
                ,type=socket.SOCK_STREAM
                #,proto=0
                )
        #self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socketBuffer=''
        host=self.parameters.host
        port=int(self.parameters.port)
        debug('Open Socket (%s:%d)' % (host,port))
##        try:
        self.socket.connect((host,port))
        if bool(int(self.parameters.aprsis_login)):
            self.__aprsisLogin()
        return True
##        except:
##            debug('Error opening socket: (%s,%d)' %
##                    (host,port))
##            return False

    def __aprsisLogin(self):
        ##TODO: robustify
        ##TODO: do recv non-blocking
        self.socketBuffer=''
        username=self.parameters.username
        password=self.parameters.password
        adjunct=self.parameters.adjunct
        connStr='user %s pass %s vers pyaprs 0.0 %s\r\n' % \
                (username,password,adjunct)
        debug('APRSIS Login: %s' % self.socket.recv(200))
        debug('Sending: %s' % connStr)
        self.socket.send(connStr)
        d=self.socket.recv(200)
        debug('Response: %s' % d)

        if d.startswith('# logresp %s verified' % username):
            debug('Login Successful')
        else:
            debug('***********Login Failed***********')

    def __handleData(self):
        data=self.socket.recv(200)
        self.socketBuffer += data
        utcTime=datetime.datetime.utcnow()
        #lines=self.socketBuffer.split('\r\n')
        if self.socketBuffer.endswith('\r\n'):
            #buffer ends on a aprsis new line
            lines=self.socketBuffer.strip().split('\r\n')
            self.socketBuffer=''
        else:
            #buffer is not terminated by newline
            lines=self.socketBuffer.strip().split('\r\n')
            debug('Buffering: %s' % lines[-1])
            self.socketBuffer='%s' % lines.pop(-1)

        for line in lines:
            #debug('Packet: %s' % (line.strip(),))
            if len(line.strip())==0:
                debug('Data: %s' % data)
                debug('Split: %s' % lines)
                #raise
            packet=BasicPacket()
            ok = packet.fromAPRSIS(line.strip(),utcTime)
            if ok!=True:
                #print ok,'***  Null Packet ***'
                continue
            #if all looks good, post the packet to the output queue
            #debug('Post packet to queueOut')
            self.queueOut.put(('ok',packet))
