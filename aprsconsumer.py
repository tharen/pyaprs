#aprsconsumer.py
"""
APRS consumer superclass and associated objects
"""
import Queue,datetime,re

import logging

from parameters import Parameters

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Consumer:
    def __init__(self,iniFile,name,*args,**kwargs):
        self.iniFile=iniFile
        self.name=name
        self.status=0 #0=init, 1=ready, -1=error
        self.queueIn=Queue.Queue()
        self.parameters=Parameters(self.iniFile,self.name)
        self.handledPackets=0
        self.totalPackets=0

    def start(self):
        """
        Main loop to handle BasicPackets placed in the queue
        """
        debug('Consumer Starting: %s' % self.name)
        while 1:
            #block while waiting for data to handle
            flag,basicPacket=self.queueIn.get()
            if flag=='stop':
                break
            self.consume(basicPacket)

    def consume(self,basicPacket):
        """
        Do something with packet data
        """
        x=basicPacket

class Producer:
    def __init__(self,iniFile,name):
        """
        Producer super class
        """
        self.iniFile=iniFile
        self.name=name
        self.status=0 #0-init, 1-running, 3-error
        self.errorMessage=''
        self.queueOut=Queue.Queue()
        self.parameters=Parameters(self.iniFile)

    def start(self):
        """
        Start producing packets.  This would most likely be a loop
        of some sort to respond to a data stream, query interval, etc.

        ** This should be overwritten
        """
        while 1:
            data='Error: Super Class instance'
            self.queueOut.put(data)
            time.sleep(0.5)

if __name__=='__main__':
    p='!3858.21N/09007.02W#PHG3430/W3,Godfrey IL kb9bpf@arrl.net TNX K9SD\r\n'
    payload=Payload(p)
