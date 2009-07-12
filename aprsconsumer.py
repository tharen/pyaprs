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
    def __init__(self,iniFile,name,*args,**kwargs):
        self.iniFile=iniFile
        self.name=name
        self.status=0 #0=init, 1=ready, -1=error
        self.queueIn=Queue.Queue()
        self.parameters=Parameters(self.iniFile,self.name)
        self.pollInterval=float(self.parameters.get('poll_interval'))
        self.refreshInterval=float(self.parameters.get('refresh_interval'))
        self.handledPackets=0
        self.totalPackets=0

    def start(self):
        """
        Main loop to handle BasicPackets placed in the queue
        """
        time.clock()
        debug('Consumer Starting: %s' % self.name)
        rt=time.clock()-self.refreshInterval
        while 1:
            # is it time to refresh
            if time.clock()-rt>self.refreshInterval:
                debug('%s - Refresh Time' % self.name)
                self.refresh()
                rt=time.clock()

            # check the queue for incoming packets
            try:
                flag,basicPacket=self.queueIn.get_nowait()
            except Queue.Empty:
                time.sleep(self.pollInterval)
                continue
            except:
                exception('Consumer queue Error')


            if flag=='stop':
                break
            self.consume(basicPacket)

    def consume(self,basicPacket):
        """
        Do something with packet data
        """
        pass

    def refresh(self):
        """
        Do something on a time schedule
        """
        pass

##class Producer:
##    def __init__(self,iniFile,name):
##        """
##        Producer super class
##        """
##        self.iniFile=iniFile
##        self.name=name
##        self.status=0 #0-init, 1-running, 3-error
##        self.errorMessage=''
##        self.queueOut=Queue.Queue()
##        self.parameters=Parameters(self.iniFile)
##
##    def start(self):
##        """
##        Start producing packets.  This would most likely be a loop
##        of some sort to respond to a data stream, query interval, etc.
##
##        ** This should be overwritten
##        """
##        while 1:
##            data='Error: Super Class instance'
##            self.queueOut.put(data)
##            time.sleep(0.5)

