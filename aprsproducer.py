#aprsproducer.py
"""
APRS producer superclass and associated objects
"""
import Queue,datetime
import socket,select
import logging

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Producer:
    def __init__(self,name):
        """
        Producer super class
        """
        self.name=name
        self.status=0 #0-init, 1-running, 3-error
        self.errorMessage=''
        self.queueOut=Queue.Queue()

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
