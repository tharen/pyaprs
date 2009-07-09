#inetproducer.py

import Queue,datetime
import socket,select
import logging

from parameters import Parameters
from aprsproducer import Producer

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class InetProducer(Producer):
    def __init__(self,name,timeout=10,throttle=0.1):
        Producer.__init__(self,name)
        self.timeout=timeout #seconds to wait for a response from the socket
        self.throttle=throttle #seconds to pause between socket reads
        self.socket=None
        self.socketBuffer=''
        print Parameters()
        p=self.parameters=Parameters().__getattribute__(name)  #parameters are in a section titled [self.name]

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
                debug('Select failed, attempt to reopen socket')
                print traceback.print_exc()
                self.__openSocket()

            time.sleep(self.throttle)

    def __openSocket(self):
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socketBuffer=''
        try:
            self.socket.connect((self.parameters.host,self.parameters.port))
            if self.parameters.aprsis_login:
                self.__aprsisLogin()
            return True
        except:
            debug('Error opening socket: (%s,%d)' %
                    (self.parameters.host,self.parameters.port))
            return False

    def __aprsisLogin(self):
        ##TODO: robustify
        ##TODO: do recv non-blocking
        p=self.parameters
        connStr='user %s pass %s vers aprs2kml %s\r\n' % \
                (p.username,p.password,p.filter)
        data=self.socket.recv(100)
        self.socket.send(connStr)
        self.socketBuffer=self.socket.recv(100)
        debug('Login successful')

    def __handleData(self):
        self.socketBuffer += self.socket.recv(100)
        utcTime=datetime.datetime.utcnow()
        if self.socketBuffer.endswith('\n'):
            lines=self.socketBuffer.split('\n')
            self.socketBuffer=''
        else:
            lines=self.socketBuffer.split('\n')
            debug('Buffering: %s' % lines[-1])
            self.socketBuffer=lines.pop(-1)

        for line in lines:
            debug('Packet: %s' % (line.strip(),))
            packet=BasicPacket()
            ok = packet.fromAPRSIS(line,utcTime)
            if not ok:
                #print '***  Null Packet ***'
                continue

            #if all looks good, post the packet to the output queue
            consumer.queueOut.put(('ok',packet))
