#parameters.py

"""
Handle application parameters stored in a ini style configuration file.
"""

import os,ConfigParser
import logging

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Section(object):
    def __init__(self,name,):
        self.name=name

class Parameters(object):
    def __init__(self,):
##        # parameter:(default,cast function)
##        self.paramMap={
##                'host':('127.0.0.1',str)
##                ,'port':(1448,int)
##                ,'init_interval':(60,int)  #seconds between reads of the ini file
##                ,'poll_interval':(2000,int)  #milliseconds between socket scans
##                ,'username':('KE7FXL',str)
##                ,'password':('22445',str)
##                ,'filter':('a/47/-127/41/-116',str)
##                ,'aprsis_login':(False,lambda x:x!='0')
##                ,'log_packets':(False,lambda x:x!='0')
##                }
##        for k in self.paramMap.keys():
##            self.__dict__[k]=self.paramMap[k][0]
        pass

    def readInifile(self,iniFile):
        cfg=ConfigParser.ConfigParser()
        oldParams=self.__dict__.copy()
        debug('Reading inifile: %s' % iniFile)
        print iniFile
        try:
            if not os.path.exists(iniFile):
                debug('Config file does not exist: %s' % iniFile)
                return False
            cfg.read(iniFile)
            for section in sections:
                self.__dict__[section]=Section(section)
                items=cfg.items('main')
                for item in items:
                    self.__dict__[section].__dict__[item[0]]=item[1]

            return True
        except:
            self.__dict__=oldParams.copy()
            debug('Error reading config file: %s' % iniFile)
            return False
