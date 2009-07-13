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

        d['data']=self.encode(d['data'])
        d['aprsisString']=self.encode(d['aprsisString'])
        d['localTime']=self.localTime()

        return template % d


    def encode(self,str):
        new=[]
        for ch in str:
            #print ch,ord(ch)
            ##TODO: fix me
            if ((ch == 0x9) | (ch == 0xA) | (ch == 0xD) | ((ch >= 0x20) & (ch <= 0xD7FF)) | ((ch >= 0xE000) & (ch <= 0xFFFD)) | ((ch >= 0x10000) & (ch <= 0x10FFFF))):
                new.append(ch)
            else:
                new.append(' ')
        return ''.join(new)

    def xencode(self,str):
        new=[]
        for c in unicode(str,"utf-8"):
            try:
                new.append(c.encode("cp1252"))
            except:
                raise
                new.append(c.encode("iso-8859-15"))
        return ''.join(new)

##    #---encode for xml
##    ## http://code.activestate.com/recipes/303668/
##    def encode_for_xml(self,unicode_data, encoding='utf-8'):
##        """
##        Encode unicode_data for use as XML or HTML, with characters outside
##        of the encoding converted to XML numeric character references.
##        """
##        try:
##            return unicode_data.encode(encoding, 'xmlcharrefreplace')
##        except ValueError:
##            raise
##            # ValueError is raised if there are unencodable chars in the
##            # data and the 'xmlcharrefreplace' error handler is not found.
##            # Pre-2.3 Python doesn't support the 'xmlcharrefreplace' error
##            # handler, so we'll emulate it.
##            return self._xmlcharref_encode(unicode_data, encoding)
##
##    def _xmlcharref_encode(self,unicode_data, encoding):
##        """Emulate Python 2.3's 'xmlcharrefreplace' encoding error handler."""
##        chars = []
##        # Step through the unicode_data string one character at a time in
##        # order to catch unencodable characters:
##        for char in unicode_data:
##            try:
##                chars.append(char.encode(encoding, 'strict'))
##            except UnicodeError:
##                chars.append('&#%i;' % ord(char))
##        return ''.join(chars)

##    def __str__(self):
##        return self.asPlacemark()

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
        self.header=open(self.headerFile).read()
        self.tail=open(self.tailFile).read()
        self.kmlFile=open(self.kmlPath,'wb+')
        self.kmlFile.write(self.header)
        self.kmlFile.write(self.tail)

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
        debug('KML refresh')
        try:self.kmlFile.close()
        except:
            debug('Unable to close kml file')
            pass
        self.__initKML()
        #copy and reset the current set of packets
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

        info('%d Position Reports' % c)

if __name__=='__main__':
    d=open(r'C:\proj\pyAPRS\output\bum_packets.txt').read()
    dd=d.split('\n')
    p=BasicPacket()
    p.fromAPRSIS(dd[0])
    k=KmlPacket(p)
    t=open(r'C:\proj\pyAPRS\resources\kml_placemark.txt').read()
    open(r'C:\proj\pyAPRS\output\bum_packets.kml','wb').write(k.asPlacemark(t))