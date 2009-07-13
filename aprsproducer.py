#aprsproducer.py
"""
APRS producer superclass and associated objects
"""
import Queue,datetime
import socket,select

import logging
from parameters import Parameters

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Producer:
    def __init__(self,parameters,name):
        """
        Producer super class
        """
        #self.iniFile=iniFile
        self.parameters=parameters
        self.name=name
        self.status=0 #0-init, 1-running, 3-error
        self.errorMessage=''
        self.queueOut=Queue.Queue()
        #self.parameters=Parameters(self.iniFile,self.name)
        self.pollInterval=float(self.parameters.poll_interval)
        self.handledPackets=0
        self.totalPackets=0

    def start(self):
        """
        Start producing packets.  This would most likely be a loop
        of some sort to respond to a data stream, query interval, etc.

        ** This should be overwritten
        """
        debug('Producer Starting: %s' % self.name)
        while 1:
            data='Error: Super Class instance'
            self.queueOut.put(data)
            time.sleep(self.pollInterval)
