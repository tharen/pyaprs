import logging
import ConfigParser

#from inetproducer import InetProducer
#from kmlconsumer import KmlConsumer
#from aprsmonitor import APRSMonitor

import logger
#,parameters

my_logger = logging.getLogger('MyLogger')
#my_logger.setLevel(logging.INFO)

##TODO: read up on factory functions
class ConfigSection(object):
    def __init__(self,items):
        for k,v in items:
            self.__dict__[k]=v

class Main:
    def __init__(self,iniFile,autoStart=True):
        my_logger.debug('****Creating an instance of Main****')
        self.iniFile=iniFile
        self.cfg=ConfigParser.ConfigParser()
        self.cfg.read(self.iniFile)

        configMonitors={}
        configProducers={}
        configConsumers={}

        for section in self.cfg.sections():
            type,name=section.split('|')
            if type=='monitor':
                configMonitors[name]=ConfigSection(self.cfg.items(section))
            elif type=='producer':
                configProducers[name]=ConfigSection(self.cfg.items(section))
            elif type=='consumer':
                configConsumers[name]=ConfigSection(self.cfg.items(section))

        self.monitors=[]

        ##add monitors
        for name,config in configMonitors.items():
            my_logger.debug('Add monitor - %s' % name)
            try:
                m=__import__(config.plugin)
                self.monitors.append(m.Main(config,name))
            except:
                my_logger.exception('Monitor plugin load error - %s' % name)

        for monitor in self.monitors:
            ## for each monitor add producers
            for name,config in configProducers.items():
                my_logger.debug('Add producer %s to monitor - %s' % (name,monitor.name))
                try:
                    p=__import__(config.plugin)
                    monitor.addProducer(p.Main(config,name))
                except:
                    my_logger.exception('Producer plugin load error - %s' % name)

            ##for each monitor add consumers
            for name,config in configConsumers.items():
                try:
                    c=__import__(config.plugin)
                    monitor.addConsumer(c.Main(config,name))
                except:
                    my_logger.exception('Consumer plugin load error - %s' % name)
                    configConsumers.pop(name)
                    #raise

        if autoStart:
            self.start()

    def start(self):
        ##TODO: add support for multiple monitors
        self.monitors[0].mainLoop()

if __name__=='__main__':
    ini='aprsmonitor.ini'

    main=Main(ini)
    #main.start()