#kmlconsumer.py

"""
KML APRS consumer.  Converts a basic packet object for KML presentation.
"""

from aprsconsumer import Consumer
from aprspacket import BasicPacket

#from cgi import escape

import logging
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info

class KmlPacket(BasicPacket):
    def __init__(self,srcPacket):
        """
        Extends BasicPacket to output kml placemarks
        """
        ##TODO: There's got to be a better way to with an existing instance
        BasicPacket.__init__(self)
        self.__dict__.update(srcPacket.__dict__.copy())

    def asPlacemark(self,template):
        d=self.__dict__.copy()
        #p=self.payload.__dict__.copy()
        d.update(self.payload.__dict__)
        #d['data']=escape(d['data'])
        ##TODO: esc characters are breaking kml cdata???
        d['data']=d['data'].replace(chr(27),' ')
        d['aprsisString']=d['aprsisString'].replace(chr(27),' ')
        d['localTime']=self.localTime()
        return template % d

    def __str__(self):
        return self.asPlacemark()

class KmlConsumer(Consumer):
    def __init__(self,iniFile,name):
        Consumer.__init__(self,iniFile,name)
        self.kmlPath=self.parameters.get('outpath')
        self.kmz=bool(int(self.parameters.get('kmz')))
        self.kmlFile=None
        ##TODO: move header and tail to a file or two
        self.headerFile=self.parameters.get('kmlheader')
        self.tailFile=self.parameters.get('kmltail')
        self.placemarkFile=self.parameters.get('kmlplacemark')

    def __initKML(self):
        self.header=open(self.headerFile).read()
        self.header=open(self.tailFile).read()
        self.kmlFile=open(self.kmlPath,'wb+')
        self.kmlFile.write(self.header)
        self.kmlFile.write(self.tail)

    def consume(self,srcPacket):
        debug('KML Consuming: %s' % srcPacket)
        kmlPacket=KmlPacket(srcPacket)
        self.header=open(self.headerFile).read()
        self.tail=open(self.tailFile).read()
        self.placemark=open(self.placemarkFile).read()
        placemark=kmlPacket.asPlacemark(self.placemark)
        try:
            self.kmlFile=open(self.kmlPath,'rb+')
            self.kmlFile.seek(-1*len(self.tail),2)
            self.kmlFile.write(placemark)
            self.kmlFile.write(self.tail)
            self.kmlFile.flush()
        except:
            self.__initKML()
            self.kmlFile.seek(-1*len(self.tail),2)
            self.kmlFile.write(placemark)
            self.kmlFile.write(self.tail)
            self.kmlFile.flush()

        return True
