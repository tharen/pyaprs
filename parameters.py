#parameters.py

"""
Handle application parameters stored in a ini style configuration file.
"""

import os,ConfigParser
import logging

# Reference the global logger
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info

class Section(object):
    def __init__(self,name,):
        self.name=name

class Parameters(object):
    def __init__(self,iniFile,sectionName='main'):
        self.iniFile=iniFile
        self.sectionName=sectionName
        self._readIniFile(self.iniFile)
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

    def get(self,attr):
        #print self.__dict__[self.sectionName].__dict__[attr]
        return self.__dict__[self.sectionName].__getattribute__(attr)

    def _readIniFile(self,iniFile=None):
        if iniFile:
            oldIniFile=self.iniFile
            self.iniFile=iniFile
        else:
            oldIniFile=self.iniFile

        cfg=ConfigParser.ConfigParser()
        oldParams=self.__dict__.copy()
        debug('Reading inifile: %s' % self.iniFile)
##        try:
        if not os.path.exists(iniFile):
            debug('Config file does not exist: %s' % iniFile)
            return False
        cfg.read(iniFile)

        for section in cfg.sections():
            self.__dict__[section]=Section(section)
            items=cfg.items(section)
            for item in items:
                self.__dict__[section].__setattr__(item[0],item[1])

        debug('Init parmeters: %s' % self.__dict__[self.sectionName].__dict__)
        return True
##        except:
##            debug('Error reading config file: %s' % self.iniFile)
##            self.__dict__=oldParams.copy()
##            self.iniFile=oldIniFile
##            return False

if __name__=='__main__':
    p=Parameters('aprsmonitor.ini')