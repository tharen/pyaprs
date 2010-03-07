import BaseHTTPServer
import time,datetime,math
from sqlite3 import dbapi2 as dba

from aprspacket import BasicPacket
from kmlconsumer import KmlPacket

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

dba.register_adapter(datetime.datetime, adapt_datetime)

HOST_NAME = ''
PORT_NUMBER = 8080

HEAD="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
  <Folder>
    <name>APRS To Kml</name>
"""
TAIL="""  </Folder>
</Document>
</kml>
"""
BODY="""    <Placemark>
      <name>%(fromCall)s</name>
      <styleUrl>output/aprssymbols/aprssymbols.kml#msn_%(style)s</styleUrl>
      <description><![CDATA[
          <img src="output/aprssymbols/%(style)s.png" alt="%(style)s" width="40" height="40"/>
          <br> Station: <b>%(fromCall)s</b>
          <br> Symbol: %(symbolTable)s,%(symbolCharacter)s, %(style)s
          <br>Time: %(localTime)s
          <br>Path: %(path)s
          <br>Data: %(data)s
          <p style="margin-left:.5in;text-indent:-.5in">Packet: %(aprsisString)s
          <br>
          ]]>
      </description>
      <MultiGeometry>
        <Point>
          <coordinates>
            %(longitude).4f,%(latitude).4f,%(elevation)d
          </coordinates>
        </Point>
        <LineString>
          <coordinates>
            %(track)s
          </coordinates>
        </LineString>
       </MultiGeometry>
    </Placemark>
"""

class KmlRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        #print s.headers
        #print s.path

        """Respond to a GET request."""

        ##TODO: handle file requests using builtin features
        if s.path.lower().startswith('/output/aprssymbols/'):
            s.send_response(200)
            if s.path.endswith('.kml'):
                s.send_header("Content-type","text/plain") #"application/vnd.google-earth.kml+xml")
                s.end_headers()
                f=open(s.path[1:],'rb')
                s.wfile.write(f.read())
                f.close()
                print 'Served File: %s' % s.path[1:]
            if s.path.endswith('.png'):
                s.send_header("Content-type","image/png")
                s.end_headers()
                f=open(s.path[1:],'rb')
                s.wfile.write(f.read())
                f.close()
                print 'Served File: %s' % s.path[1:]
            return

        if not s.path.lower().startswith('/kml_query?'):
            print 'Unrecognized path %s' % s.path
            s.send_response(404)
            return

        params=s.path.split('?')
        bbox=False
        for p in params:
            if p.lower().startswith('bbox='):
                bbox=map(float,p.split('=')[1].split(','))

        if not bbox:
            print 'Bad BBOX %s' % p.split('=')
            s.send_response(404)
            return

        s.send_response(200)
        if 'Earth' in s.headers.get('User-Agent'):
            s.send_header("Content-type", "application/vnd.google-earth.kml+xml")
            s.end_headers()
            kml=getKml(bbox)
            s.wfile.write(kml)
            kml=None
        else:
            s.send_header("Content-type", "text/plain")
            s.end_headers()
            kml=getKml(bbox)
            s.wfile.write(kml)
            #s.wfile.write("<html><head><title>BBOX Query</title></head>")
            #s.wfile.write("<body><p>bbox=(%.4f,%.4f,%.4f,%.4f)</p>" % (bbox[0],bbox[1],bbox[2],bbox[3]))
            #s.wfile.write("</body></html>")

def greatCircleDistance(pnt1,pnt2):
    """
    returns distance in miles between two points in d.dd
    http://code.activestate.com/recipes/393241/
    """
    lon1,lat1=map(math.radians,pnt1)
    lon2,lat2=map(math.radians,pnt2)

    dlong = lon2-lon1
    dlat = lat2 - lat1
    a = (math.sin(dlat / 2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlong / 2))**2
    c = 2 * math.asin(min(1, math.sqrt(a)))
    dist = 3956 * c
    return dist

def getKml(bbox,maxAge=60*60):
    td=datetime.timedelta(seconds=maxAge)
    minTime=datetime.datetime.utcnow()-td
    conn=dba.connect('aprs.db')
    cur=conn.cursor()
    w,s,e,n=bbox
    cur.execute(""" select
                        receivedTime
                        ,aprsisString
                        ,sourcePort
                        ,heardLocal
                        ,fromCall
                        ,path
                        ,reportType
                        ,payload
                        ,symbolTable
                        ,symbolCharacter
                        ,symbolOverlay
                        ,latitude
                        ,longitude
                        ,elevation
                    from Reports
                    where receivedTime>=?
                    and longitude>=? and longitude<=?
                    and latitude>=? and latitude<=?
                    order by receivedTime
            """,
            (minTime,w,e,s,n))
    kml=HEAD
    i=0
    stationReports={}
    i=0
    for row in cur:
##        p={}
##        p['fromCall']=row[1]
##        p['fromSSID']=row[2]
##        p['symbolTable']=row[3]
##        p['symbolCharacter']=row[4]
##        p['latitude']=row[5]
##        p['longitude']=row[6]
##        p['elevation']=row[7]
##        p['localTime']=''
##        p['path']=
##        p['data']=
##        p['coordinates']=''
##        #p['style']='t1s15'
        p=BasicPacket()
        p.fromDbRow(row)
        call=p.fromCall
        if not stationReports.has_key(i):
            stationReports[call]=[]

        stationReports[call].append(p)
        i+=1

    stations={}
    for call,reports in stationReports.items():
        current=reports[0]
        tracks={}
        for report in reports:
            if report.utcTime>current.utcTime:
                current=report
            tracks[report.utcTime]='%.6f,%.6f,%.6f' % \
                    (report.payload.longitude
                    ,report.payload.latitude
                    ,report.payload.elevation)

        #sort the previous locations and string them together
        keys=tracks.keys()
        keys.sort()
        trackString=' '.join([tracks[k] for k in keys])

        stations[call]=(current,trackString)

    i=0
    for call,values in stations.items():
        try:
            p=values[0]
            k=KmlPacket(p)
            k.track=values[1]
            kml+=k.asPlacemark(BODY)
            i+=1
        except:
            print 'Error building placemark - %s' % values[0].aprsisString
            continue

    kml+=TAIL
    print '%d Reports returned' % i

    cur.close()
    cur=None
    conn.close()
    conn=None
    return kml

class KmlServer(BaseHTTPServer.HTTPServer):
    def __init__(self,hostName,hostPort,requestHandler):
        self.hostName=hostName
        self.hostPort=hostPort
        self.requestHandler=requestHandler
        BaseHTTPServer.HTTPServer.__init__(self,(self.hostName,self.hostPort), self.requestHandler)

    def start(self):
        print time.asctime(), "Server Starts - %s:%s" % (self.hostName,self.hostPort)
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass

    def stop(self):
        self.server_close()
        print time.asctime(), "Server Stops - %s:%s" % (self.hostName,self.hostPort)

if __name__ == '__main__':
    server=KmlServer(HOST_NAME,PORT_NUMBER,KmlRequestHandler)
    server.start()
##    server_class = BaseHTTPServer.HTTPServer
##    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
##    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
##    try:
##        httpd.serve_forever()
##    except KeyboardInterrupt:
##        pass
##    httpd.server_close()
##    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)