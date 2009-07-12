import logging

from inetproducer import InetProducer
from kmlconsumer import KmlConsumer
from aprsmonitor import APRSMonitor

import logger,parameters

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)

ini='aprsmonitor.ini'

class Main:
    def __init__(self):
        self.aprs=APRSMonitor(ini)

        kmlConsumer=KmlConsumer(ini,'kml_1')
        inetProducer=InetProducer(ini,'aprsis_1')

        self.aprs.addConsumer(kmlConsumer)
        self.aprs.addProducer(inetProducer)

    def start(self):
        self.aprs.mainLoop()

if __name__=='__main__':
    main=Main()
    main.start()