#kmlconsumer.py

"""
KML APRS consumer.  Converts a basic packet object for KML presentation.
"""

import datetime

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
##        cd=''
##        for c in d['data']:
##            if ord(c) in (27,):
##                cd+=' '
##            else: cd+=c
##        d['data']=cd
##
##        cd=''
##        for c in d['aprsisString']:
##            if ord(c) in (27,):
##                cd+=' '
##            else: cd+=c
##        d['aprsisString']=cd

        d['data']=''
        d['aprsisString']=''
        d['localTime']=self.localTime()
        return template % d

##    def __str__(self):
##        return self.asPlacemark()

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
        self.packets=[]

    def __initKML(self):
        self.header=open(self.headerFile).read()
        self.tail=open(self.tailFile).read()
        self.kmlFile=open(self.kmlPath,'wb+')
        self.kmlFile.write(self.header)
        self.kmlFile.write(self.tail)

    def consume(self,srcPacket):
        #debug('KML Consuming: %s' % srcPacket)
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

        self.packets.append(kmlPacket)

        return True

    def refresh(self):
        debug('KML refresh')
        try:self.kmlFile.close()
        except:
            debug('Unable to close kml file')
            pass
        self.__initKML()
        #copy and reset the current set of packets
        packets=self.packets[:]
        self.packets=[]
        keepAge=float(self.parameters.get('keep_age'))
        now=datetime.datetime.utcnow()
        c=0
        for i in range(len(packets)-1):
            packet=packets[i]
            td=now-packet.utcTime
            age=td.days*24*60*60 + td.seconds
            if age<=keepAge:
                #re-consume the packet
                self.consume(packet)
                c+=1

        info('%d Position Reports' % c)
