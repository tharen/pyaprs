#aprsconsumer.py
"""
APRS consumer superclass and associated objects
"""
import Queue,datetime,time,re

import logging

from parameters import Parameters

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info
exception=my_logger.exception

class Consumer:
    def __init__(self,parameters,name,*args,**kwargs):
        """
        Consumer subclasses receive raw APRS data and turn it into 
        functional objects.
        
        Args
        ----
        parameters - reference to the global parameters object
        name - name given to the consumer
        """
        #self.iniFile=iniFile
        self.parameters=parameters
        self.name=name
        self.status=0 #0=init, 1=ready, -1=error
        self.queueIn=Queue.Queue()
        #self.parameters=Parameters(self.iniFile,self.name)
        self.pollInterval=float(self.parameters.poll_interval)
        self.refreshInterval=float(self.parameters.refresh_interval)
        self.handledPackets=0
        self.totalPackets=0

    def _runFirst(self):
        pass

    def start(self):
        """
        Main loop to handle BasicPackets placed in the queue
        """
        time.clock()
        debug('Consumer Starting: %s' % self.name)
        self._runFirst()
        rt=time.clock()-self.refreshInterval
        while 1:
            # is it time to refresh
            if (time.clock()-rt>self.refreshInterval) and \
                    (self.refreshInterval>-1):
                info('*** %s - Refresh Time' % self.name)
                self.refresh()
                rt=time.clock()

            # check the queue for incoming packets
            try:
                flag,data=self.queueIn.get_nowait()
            except Queue.Empty:
                #wait a while to avoid runaway
                time.sleep(self.pollInterval)
                continue
            except:
                #log the exeception
                exception('Consumer queue Error')


            if flag=='stop':
                break
            if flag=='restart':
                pass

            try:
                self.consume(data)
            except:
                exception('(%s) Error consuming packet: %s' % (self.name,data))

    def consume(self,basicPacket):
        """
        (Subclass this)
        Do something with packet data
        
        """
        pass

    def refresh(self):
        """
        Do something on a time schedule
        """
        pass

