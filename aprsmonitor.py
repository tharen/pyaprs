#!c:/python25/python.exe

"""
APRS Monitor

Producers connect to various packet source streams.
    - Producers are expected to provide properly formatted APRS strings.
        "FROM>PATH,IDENTS:APRS Data Payload"

Consumers accept basic packet objects and further process them
    - Consumers are expected to receive a AprsFrame instance.

Each producer and consumer must provide a target method that will
    run in it's own thread.  Packets are exchanged via Queues.
"""

##TODO: Look into using asyncore instead of threads.
##TODO: Optional Parallel Python producers & consumers

import os,time,datetime
import threading,Queue
import logging

from copy import copy

from aprsconsumer import Consumer
from parameters import Parameters
#from aprspacket import AprsFrame

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Main:
    def __init__(self,parameters,name):
        #self.iniFile=iniFile
        #self.parameters=Parameters(self.iniFile,'main')
        self.parameters=parameters
        self.name=name
        self.packetBuffer=[]
        self.consumers={} # {name:consumerInstance,}
        self.producers={} # {name:producerInstance,}

    def addConsumer(self,consumer):
        """
        Add a consumer to accept AprsFrames
        """
        if self.consumers.has_key(consumer.name):
            raise "Consumer names must be unique"
        self.consumers[consumer.name]=consumer

    def addProducer(self,producer):
        """
        Add a producer to accept AprsFrames
        """
##        thread=threading.Thread(target=producer.start)
##        thread.start()
        if self.producers.has_key(producer.name):
            raise "Producer names must be unique"
        self.producers[producer.name]=producer

    def mainLoop(self):
        self.parameters.poll_interval
        for name,consumer in self.consumers.items():
            thread=threading.Thread(target=consumer.start)
            thread.start()
        for name,producer in self.producers.items():
            thread=threading.Thread(target=producer.start)
            thread.start()

        et=time.time()
        while 1:
            # all producers with data ready put packets in the packet buffer
            self.__pollProducers()

            # if there are packets to consume, consume them all
            if self.packetBuffer: debug('%d Packets to Parse' % len(self.packetBuffer))
            while self.packetBuffer:
                ##TODO: error trap
                #self.__notifyConsumers(self.packetBuffer.pop(0))
                pass

            self.packetBuffer=[]

            init_interval=float(self.parameters.init_interval)
            poll_interval=float(self.parameters.poll_interval)

            # reload the parameter file occasionally
            ##TODO: add this back in since it was moved to main
##            if (time.time()-et)>(init_interval):
##                self.parameters=Parameters(self.iniFile,'main')
##                et=time.time()

            # Wait x number of milliseconds
            time.sleep(1) #poll_interval/1000.0)

        #clean up on exit
        try:
            self.packetLog.close()
        except:
            exception('**Error exiting mainLoop')

    def __pollProducers(self):
        pc=0
        for name,producer in self.producers.items():
            try:
                #get the next packet from each producer
                #get_nowait raises an error if not data ready
                ok,packet=producer.queueOut.get_nowait()
            except:
                #no data to process
                continue

            if ok=='error':
                producer.status=3
                producer.error=packet
            else:
                #producers only produce complete packets
                #  but, there is not real verification
                producer.status=1
                producer.totalPackets+=1
                utcTime=datetime.datetime.utcnow()
                #add the packet to the buffer
                self.packetBuffer.append(packet)
                pc+=1

                producer.handledPackets+=1
        print 'polled packets: %d' % pc
            #producer.queueOut.clear()

    def __notifyConsumers(self,packet):
        for name,consumer in self.consumers.items():
            ##TODO: is copy necessary
            #pass the AprsFrame to each consumer
            #(status,packet)
            consumer.queueIn.put(('ok',copy(packet)))

    def __logPacket(self,packet):
        self.packetLog.write(packet.strip()+'\n')
        self.packetLog.flush()

if __name__=='__main__':
    pass