import os
import Image

def splitIcons():
    p=r'C:\proj\pyAPRS\resources\aprssymbols\mysymb2.png'
    o=r'C:\proj\pyAPRS\resources\aprssymbols'

    base=Image.open(p).convert('RGBA')
    w,h=base.size
    print w,h
    s=w/16

    for y in range(0,h/s):
        for x in range(0,w/s):
            #print x+y*16,x,y
            new=base.crop((x*s,y*s,x*s+s,y*s+s))
            new.save(os.path.join(o,'t2s%d.png' % (x+(y*16)+1,)))

def buildStyleXml():
    r=r'C:\proj\pyAPRS\resources\aprssymbols'
    f=r'C:\proj\pyAPRS\resources\aprssymbols\aprssymbols.kml'
    head="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
"""
    style="""  <StyleMap id="msn_%(symbol)s">
    <Pair>
      <key>normal</key>
      <styleUrl>#sn_%(symbol)s</styleUrl>
    </Pair>
    <Pair>
      <key>highlight</key>
      <styleUrl>#sh_%(symbol)s</styleUrl>
    </Pair>
  </StyleMap>
  <Style id="sn_%(symbol)s">
    <IconStyle>
      <scale>0.8</scale>
      <Icon>
        <href>%(symbol)s.png</href>
      </Icon>
    </IconStyle>
    <LabelStyle>
      <color>7ff000000</color>
      <scale>1</scale>
    </LabelStyle>
    <LineStyle>
      <color>ff0000ff</color>
      <width>3</width>
    </LineStyle>
    <PolyStyle>
      <color>7f7faaaa</color>
      <colorMode>random</colorMode>
    </PolyStyle>
    <ListStyle>
    </ListStyle>
  </Style>
  <Style id="sh_%(symbol)s">
    <IconStyle>
      <scale>1.2</scale>
      <Icon>
        <href>%(symbol)s.png</href>
      </Icon>
    </IconStyle>
    <LabelStyle>
      <color>7ff000000</color>
      <scale>1</scale>
    </LabelStyle>
    <LineStyle>
      <color>ff0000ff</color>
      <width>3</width>
    </LineStyle>
    <PolyStyle>
      <color>7f7faaaa</color>
      <colorMode>random</colorMode>
    </PolyStyle>
    <ListStyle>
    </ListStyle>
  </Style>
"""
    tail="""</Document>
</kml>"""

    out=open(f,'w')
    out.write(head)
    for table in (1,2):
        for symbol in range(1,97):
            s='t%ds%d' % (table,symbol)
            out.write(style % {'symbol':s,})

    out.write(tail)
    out.close()

if __name__=='__main__':
    splitIcons()
    buildStyleXml()
