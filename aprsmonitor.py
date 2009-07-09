import os,time,datetime
import socket,select
import threading,Queue
import ConfigParser
import traceback
import logging,logging.handlers

from consumer import BasicPacket
from parameters import Parameters

from kmlconsumer import KmlConsumer

##TODO: put logging in its own module files
#setup global logging
LOG_FILENAME='aprs2kml.log'
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=500*1024, backupCount=5)
my_logger.addHandler(handler)
debug=my_logger.debug
info=my_logger.info

class APRSWatch:
    def __init__(self,iniFile):
        self.iniFile=iniFile
        self.parameters=Parameters()
        self.socketBuffer=''
        self.consumers=[]

    def addConsumer(self,consumer):
        thread=threading.Thread(target=consumer.start)
        thread.start()
        self.consumers.append(consumer)

    def mainLoop(self):
        self.parameters.readInifile(self.iniFile)
        if self.parameters.log_packets:
            self.packetLog=open('packets.log','a')
        self.__openSocket()
        et=time.time()
        while 1:
            self.__pollData()
            if (time.time()-et)>(self.parameters.init_interval):
                self.parameters.readInifile(self.iniFile)
                et=time.time()
            debug('Wait %d seconds' % (self.parameters.poll_interval/1000.0,))
            #time.sleep(self.parameters.poll_interval/1000.0)

        #clean up on exit
        try:
            self.packetLog.close()
        except:
            print 'Error exiting mainLoop'

    def __pollData(self):
        try:
            debug('Polling socket')
            readReady,writeReady,inError=select.select([self.socket,],[],[],10)
            if self.socket in readReady:
                debug('Socket has data')
                self.__handleData()
                return True
            return False
        except:
            ##TODO: seperate select exceptions from other errors
            ##          ie. network failures, disapearing host, etc
            debug('Select failed, attempt to reopen socket')
            print traceback.print_exc()
            self.__openSocket()
            return None

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
            if self.parameters.log_packets:
                self.__logPacket(line)
            for consumer in self.consumers:
                consumer.queueIn.put(('ok',packet))

    def __logPacket(self,packet):
        self.packetLog.write(packet.strip()+'\n')
        self.packetLog.flush()

if __name__=='__main__':
    ini='aprs2kml.ini'

    kmlConsumer=KmlConsumer('aprs.kml')

    aprs=APRSWatch(ini)
    aprs.addConsumer(kmlConsumer)
    aprs.mainLoop()