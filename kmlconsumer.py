#kmlconsumer.py

"""
KML APRS consumer.  Converts a basic packet object for KML presentation.
"""

import datetime

from aprsconsumer import Consumer
from aprspacket import BasicPacket

#from cgi import escape
#from xml.sax.saxutils import escape
#from xmlrpclib import Binary as encode

import logging,sys
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info
exception=logger.exception

##class Yada:
##    def __init__(self):
##        pass
##    def write(self,msg):
##        exception(msg)
##yada=Yada()
##sys.stderr=yada

class KmlPacket(BasicPacket):
    def __init__(self,srcPacket):
        """
        Extends BasicPacket to output kml placemarks
        """
        ##TODO: There's got to be a better way to with an existing instance
        BasicPacket.__init__(self)
        self.__dict__.update(srcPacket.__dict__.copy())
        self.trackCoords=[]

    def asPlacemark(self,template):
        d=self.__dict__.copy()
        d.update(self.payload.__dict__.copy())

        d['data']=self.encode(d['data'])
        d['aprsisString']=self.encode(d['aprsisString'])
        d['localTime']=self.localTime()

        trackCoords=''
        for coords in self.trackCoords:
            trackCoords+='%s ' % ','.join(coords)

        d['trackCoords']=trackCoords


        d['style']='t%ds2' % d['symbolTable']
        try:
            d['style']='t%ds%d' % (d['symbolTable'],d['symbolCharacter'])
        except:
            pass

        return template % d

    def encode(self,str):
        new=[]
        for c in str:
            ch=ord(c)
            #If the character is not in the approved XML character set
            #    convert it to a hex reference
            if ((ch == 0x9) | (ch == 0xA) | (ch == 0xD) | ((ch >= 0x20) & (ch <= 0xD7FF)) | ((ch >= 0xE000) & (ch <= 0xFFFD)) | ((ch >= 0x10000) & (ch <= 0x10FFFF))):
                new.append(c)
            else:
                ##TODO: Proper hex strings in XML?
                new.append('0x%d' % ch)
        return ''.join(new)

class Main(Consumer):
    def __init__(self,parameters,name):
        Consumer.__init__(self,parameters,name)
        self.kmlPath=self.parameters.outpath
        self.kmz=bool(int(self.parameters.kmz))
        self.kmlFile=None
        ##TODO: move header and tail to a file or two
        self.headerFile=self.parameters.kmlheader
        self.tailFile=self.parameters.kmltail
        self.placemarkFile=self.parameters.kmlplacemark
        self.packets=[]

    def __initKML(self):
        """
        Initiate the kml file by writing out the kml header and tail strings
        """
        debug('Rebuild kml')
        self.header=open(self.headerFile).read()
        self.tail=open(self.tailFile).read()
        self.kmlFile=open(self.kmlPath,'wb+')
        self.kmlFile.write(self.header)
        self.kmlFile.write(self.tail)
        self.kmlFile.close()

    def consume(self,srcPacket):
        #debug('KML Consuming: %s' % srcPacket)
        kmlPacket=KmlPacket(srcPacket)
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
            #self.header=open(self.headerFile).read()
            self.kmlFile.seek(-1*len(self.tail),2)
            self.kmlFile.write(placemark)
            self.kmlFile.write(self.tail)
            self.kmlFile.flush()

        self.packets.append(kmlPacket)

        return True

    def refresh(self):
        """
        Refresh the KML file from the datastore
        """
        info('KML refresh')
        try:self.kmlFile.close()
        except:
            exception('Unable to close kml file')
            pass
        self.__initKML()
        #copy and reset the current set of packets
        ##TODO: convert self.packets to a database
        packets=self.packets[:]
        self.packets=[]
        keepAge=float(self.parameters.keep_age)
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

        info('Refreshed %d Position Reports' % c)

if __name__=='__main__':
    d=open(r'C:\proj\pyAPRS\output\bum_packets.txt').read()
    dd=d.split('\n')
    p=BasicPacket()
    p.fromAPRSIS(dd[0])
    k=KmlPacket(p)
    t=open(r'C:\proj\pyAPRS\resources\kml_placemark.txt').read()
    open(r'C:\proj\pyAPRS\output\bum_packets.kml','wb').write(k.asPlacemark(t))