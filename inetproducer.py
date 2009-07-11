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

class InetProducer(Producer):
    def __init__(self,iniFile,name,timeout=10,throttle=0.1):
        Producer.__init__(self,iniFile,name)
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
                self.__openSocket()

            time.sleep(self.throttle)

    def __openSocket(self):
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socketBuffer=''
        host=self.parameters.get('host')
        port=int(self.parameters.get('port'))
        debug('Open Socket (%s:%d)' % (host,port))
##        try:
        self.socket.connect((host,port))
        if bool(int(self.parameters.get('aprsis_login'))):
            self.__aprsisLogin()
        return True
##        except:
##            debug('Error opening socket: (%s,%d)' %
##                    (host,port))
##            return False

    def __aprsisLogin(self):
        ##TODO: robustify
        ##TODO: do recv non-blocking
        username=self.parameters.get('username')
        password=self.parameters.get('password')
        filter=self.parameters.get('filter')
        connStr='user %s pass %s vers aprs2kml %s\r\n' % \
                (username,password,filter)
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
            #debug('Packet: %s' % (line.strip(),))
            packet=BasicPacket()
            ok = packet.fromAPRSIS(line,utcTime)
            if ok!=True:
                #print ok,'***  Null Packet ***'
                continue
            #if all looks good, post the packet to the output queue
            #debug('Post packet to queueOut')
            self.queueOut.put(('ok',packet))
