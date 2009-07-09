#!c:/python25/python.exe

"""
APRS Monitor

Producers connect to various packet source streams.
    - Producers are expected to provide properly formatted APRS strings.
        "FROM>PATH,IDENTS:APRS Data Payload"

Consumers accept basic packet objects and further process them
    - Consumers are expected to receive a BasicPacket instance.

Each producer and consumer must provide a target method that will
    run in it's own thread.  Packets are exchanged via Queues.
"""

##TODO: Look into using asyncore instead of threads.
##TODO: Optional Parallel Python producers & consumers

import os,time,datetime
import threading,Queue
import ConfigParser
import traceback
import logging,logging.handlers

from aprsconsumer import BasicPacket
from parameters import Parameters

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

class APRSMonitor:
    def __init__(self,iniFile):
        self.iniFile=iniFile
        self.parameters=Parameters()
        self.socketBuffer=''
        self.consumers={} # {name:consumerInstance,}
        self.producers={} # {name:producerInstance,}

    def addConsumer(self,consumer):
        """
        Add a consumer to accept BasicPackets
        """
        thread=threading.Thread(target=consumer.start)
        thread.start()
        if self.consumers.has_key(consumer.namer):
            raise "Consumer names must be unique"
        self.consumers[consumer.name]=consumer

    def addProducer(self,producer):
        """
        Add a producer to accept BasicPackets
        """
        thread=threading.Thread(target=producer.start)
        thread.start()
        if self.producers.has_key(producer.name):
            raise "Producer names must be unique"
        self.producers[producer.name]=producer

    def mainLoop(self):
        self.parameters.readInifile(self.iniFile)
        et=time.time()
        while 1:
            #self.__pollData()
            self.__pollProducers()
            if (time.time()-et)>(self.parameters.init_interval):
                self.parameters.readInifile(self.iniFile)
                et=time.time()
            debug('Wait %d seconds' % (self.parameters.main.poll_interval/1000.0,))
            # Wait x number of milliseconds
            time.sleep(self.parameters.main.poll_interval/1000.0)

        #clean up on exit
        try:
            self.packetLog.close()
        except:
            print 'Error exiting mainLoop'

    def __pollProducers(self):
        for name,producer in self.producers.items():
            try:
                packet=producer.outQueue.get_nowait()
                if packet.startswith('error'):
                    producer.status=3
                    producer.error=packet
                else:
                    producer.status=1
                    producer.totalPackets+=1
                    utcTime=datetime.datetime.utcnow()
                    basicPacket=BasicPacket()
                    x=basicPacket.fromAPRSIS(packet,utcTime)
                    if x:
                        self.__notifyConsumers(basicPacket)
                        producer.handledPackets+=1
                    else:
                        debug('Parse Error: %s' % packet)
            except:
                pass

    def __notifyConsumers(self,packet):
        for name,consumer in self.consumers.items():
            ##TODO: is copy necessary
            #pass the BasicPacket to each consumer
            #(status,packet)
            consumer.queueId.put(('ok',copy(packet)))


    def __logPacket(self,packet):
        self.packetLog.write(packet.strip()+'\n')
        self.packetLog.flush()

if __name__=='__main__':
    from inetproducer import InetProducer
    from kmlconsumer import KmlConsumer

    ini='aprsmonitor.ini'

    kmlConsumer=KmlConsumer('output/aprs.kml')
    inetProducer=InetProducer('aprsis_1')

    aprs=APRSMonitor(ini)
    aprs.addConsumer(kmlConsumer)
    aprs.addProducer(inetProducer)

    aprs.mainLoop()