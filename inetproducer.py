#inetproducer.py

import Queue,datetime,time
import socket,select
import logging

from aprsproducer import Producer
from aprspacket import AprsFrame

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info
exception=my_logger.exception

PLUGINTYPE='PRODUCER'
PLUGINNAME='APRSIS_INET'

class Main(Producer):
    def __init__(self,parameters,name,timeout=10,throttle=0.1):
        """
        Opens a connection to an APRSIS server and streams packet strings to
        a handler

        Args:
        parameters - Parameter objection storing the following:

        packetHandler - Any object that accepts APRS formatted packet strings
        host - Address to APRSIS server
        port - host port to connect to
        username - APRSIS login username if required by the host
        password - APRSIS password if required by the host
        adjunct - Additional string to pass to the host, filters, etc
        timeout - Maximum seconds to wait for a connection response from host
        pollInterval - Seconds between reads requests to host
        """
        Producer.__init__(self,parameters,name)
        self.timeout=timeout #seconds to wait for a response from the socket
        self.throttle=throttle #seconds to pause between socket reads
        self.socket=None
        self.socketBuffer=''
        self.bytesTally=0
        self.packetTally=0
        self.startTime=0
        self.bpsInterval=30
        self.bpsBytes={}
        self.bps=0
        #self.parameters.__getattribute__(name)  #parameters are in a section titled [self.name]

    def start(self):
        """
        Start the mainloop
        Maintains the connection automatically
        """
        self.__openSocket()
        self.startTime=time.clock()
        q=time.clock()
        while 1:
            try:
                #select returns 3 lists of sockets
                ##TODO: timeout is unnecessary if running in a private thread
                readReady,writeReady,inError=select.select([self.socket,],[],[],self.timeout)
                if self.socket in readReady:
                    self.__handleData()
                    #log something interesting
                    if time.clock()-q>10:
                        info('Packet Tally: %d, K. Bytes Tally: %d, BPS: %.2f' % (self.packetTally,self.bytesTally/1000.0,self.bps/1000.0))
                        q=time.clock()
            except:
                ##TODO: seperate select exceptions from other errors
                ##          ie. network failures, disapearing host, etc
                exception('Select failed, attempt to reopen socket')
                exception('readReady - %s' % readReady)
                exception('writeReady - %s' % writeReady)
                exception('inReady - %s' % inError)
                time.sleep(.5)
                self.__openSocket()

            time.sleep(self.pollInterval)

    def __openSocket(self):
        """
        Open the internet socket to the APRSIS host
        """
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
        """
        Listen on an open socket and log as necessary to an APRSIS server
        """
        ##TODO: robustify
        ##TODO: do recv non-blocking
        self.socketBuffer=''
        username=self.parameters.username
        password=self.parameters.password
        adjunct=self.parameters.adjunct
        connStr='user %s pass %s vers pyaprs 0.0 %s\r\n' % \
                (username,password,adjunct)
        debug('APRSIS Login: %s' % self.socket.recv(200))
        debug('Sending: %s' % connStr.strip())
        self.socket.send(connStr)
        d=self.socket.recv(200)
        debug('Response: %s' % d.strip())

        if d.startswith('# logresp %s verified' % username):
            debug('Login Successful')
        else:
            debug('***********Login Failed***********')

    def __handleData(self):
        """
        Grab a chunk of data from the server and split it into packets
        """
        #read from the socket and append the data to the local buffer
        #  the availability of data should have been checked before getting this far
        data=self.socket.recv(200)
        self.socketBuffer += data

        #set the time the data was received
        utcTime=datetime.datetime.utcnow()

        #split the buffer into complete lines, putting incomplete lines back in the buffer
        if self.socketBuffer.endswith('\r\n'):
            #buffer ends on a aprsis new line
            lines=self.socketBuffer.strip().split('\r\n')
            self.socketBuffer=''
        else:
            #buffer is not terminated by newline
            #lines=self.socketBuffer.strip().split('\r\n')
            lines=self.socketBuffer.split('\r\n')
            debug('Buffering: %s' % lines[-1])
            self.socketBuffer='%s' % lines.pop(-1)

        for line in lines:

            #track traffic volume
            x=time.clock()
            bytes=len(line)

            self.bytesTally+=bytes
            self.packetTally+=1

            #calculate the bits per second, processed packets
            self.bpsBytes[x]=bytes
            keys=self.bpsBytes.keys()
            for k in keys:
                if x-k>self.bpsInterval:
                    self.bpsBytes.pop(k)
            t=x-min(self.bpsBytes.keys())
            b=sum(self.bpsBytes.values())
            if t==0: self.bps=0
            else: self.bps=b/t

            #debug('Packet: %s' % (line.strip(),))
            if len(line.strip())==0:
                debug('Data: %s' % data)
                debug('Split: %s' % lines)
                #raise
            packet=AprsFrame()
            ok = packet.parseAprs(line.strip(),utcTime)
            if ok!=True:
                #print ok,'***  Null Packet ***'
                continue
            #if all looks good, post the packet to the output queue
            #debug('Post packet to queueOut')
            self.queueOut.put(('ok',packet))
