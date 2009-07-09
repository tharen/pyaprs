#kmlconsumer.py

"""
KML APRS consumer.  Converts a basic packet object for KML presentation.
"""

from consumer import *
from cgi import escape

class KmlPacket(BasicPacket):
    def __init__(self,srcPacket):
        """
        Extends BasicPacket to output kml placemarks
        """
        ##TODO: There's got to be a better way to with an existing instance
        BasicPacket.__init__(self)
        self.__dict__.update(srcPacket.__dict__.copy())

    def asPlacemark(self):
        template=r"""    <Placemark>
      <name>%(station)s</name>
      <description><![CDATA[Station: <b>%(station)s</b>
          <br>Time: %(localTime)s
          <br>Path: %(path)s
          <br>Data: %(data)s
          <br>Packet: <br>%(aprsisString)s
          ]]>
      </description>
      <Point>
        <coordinates>%(lon).4f,%(lat).4f,%(elev)d</coordinates>
      </Point>
    </Placemark>
"""
        d=self.__dict__.copy()
        #p=self.payload.__dict__.copy()
        d.update(self.payload.__dict__)
        d['data']=escape(d['data'])
        d['aprsisString']=escape(d['aprsisString'])
        d['localTime']=self.localTime()
        return template % d

    def __str__(self):
        return self.asPlacemark()

class KmlConsumer(Consumer):
    def __init__(self,kmlPath,kmz=False):
        Consumer.__init__(self)
        self.kmlPath=kmlPath
        self.kmz=kmz
        self.header="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
  <Folder>
    <name>APRS To Kml</name>
"""
        self.tail="""  </Folder>
</Document>
</kml>"""

        try:
            self.kmlFile=open(kmlPath,'rb+')
        except:
            self.kmlFile=open(kmlPath,'wb+')
            self.kmlFile.write(self.header)
            self.kmlFile.write(self.tail)

    def consume(self,srcPacket):
        kmlPacket=KmlPacket(srcPacket)

        placemark=kmlPacket.asPlacemark()
        self.kmlFile.seek(-1*len(self.tail),2)
        self.kmlFile.write(placemark)
        self.kmlFile.write(self.tail)
        self.kmlFile.flush()

        return True
