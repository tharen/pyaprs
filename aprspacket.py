##TODO: use Assert or debug messages???

import datetime,re

import logging
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info
exception=logger.exception

import miceparse

# define indices for icon lookups
SYMBOLS=r""" !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~  """
TABLES='/\\'

class Callsign:
    def __init__(self,callString=None):
        """
        Represent a station callsign and SSID ie., (MYCALL-9).
        
        Args
        ----
        callString - (optional) Station callsign string (MYCALL-9)
        """
        self.station=''
        self.ssid=None
        self.isGood=False

        if not callString is None:
            self.parse(callString)

    def parse(self,callString):
        """
        Parse a callsign with optional ssid (APRS form) ie. MYCALL-9

        args:
        callString - Station callsign string (MYCALL-9)
        """
        assert type(callString)==str, 'Callsign not a string -- %s' % str(call)
        cs=callString.split('-',1)
        self.station=cs[0].upper()
        if len(cs)>1:
            self.ssid=cs[1]
            ##TODO: what's the protocol on SSIDs
            #assert len(self.ssid)<=2, 'Nonconforming ssid -- %s' % callString
        assert len(self.station)<=9, 'Nonconforming callsign -- %s' % callString

        self.isGood=True

    def __str__(self):
        """
        CALLSIGN-SSID string representation
        """
        cs=self.station
        if not self.ssid is None:
            cs+='-%s' % self.ssid
        return cs

    def __repr__(self):
        return self.__str__()

class Digipeater(Callsign):
    def __init__(self,callString):
        """
        Represents a digipeater within the path of a frame
        """
        self.terminated=False
        if callString[-1]=='*':
            self.terminated=True
            callString=callString[:-1]
        Callsign.__init__(self,callString)

    def __str__(self):
        """
        CALLSIGN-SSID string representation
          with a terminating * if needed
        """
        cs=self.station
        if not self.ssid is None:
            cs+='-%s' % self.ssid
        if self.terminated: cs+='*'
        return cs

    def __repr__(self):
        return self.__str__()

class UIFrame:
    def __init__(self,aprsString=None):
        """
        Represents the fields of an AX.25 packet as used in the APRS protocol

        Args:
        aprsString - (optional) APRS packet string
        """
        self.destination=''
        self.source=''
        ##TODO: this should be path not digipeaters
        self.digipeaters=[]
        self.information=''

        if not aprsString is None:
            self._parseAprs(aprsString)

    ##TODO: this APRS stuff belongs in AprsFrame
    def parseAprs(self,aprsString):
        self._parseAprs(aprsString)

    def _parseAprs(self,aprsString):
        """
        Parse UI Frame fields from an APRS string

        Args:
        aprsString - APRS packet string
        """
        assert aprsString.find('>')>-1, 'Nonconforming APRS string (">") %s' % aprsString
        assert aprsString.find(':')>-1, 'Nonconforming APRS string (":") %s' % aprsString
        source,data=aprsString.split('>',1)
        path,info=data.split(':',1)
        digis=path.split(',')
        dest=digis.pop(0)

        self.source=Callsign(source)
        self.destination=Callsign(dest)
        self.digipeaters=[Digipeater(d) for d in digis]
        self.information=info

    def __str__(self):
        return '%s>%s,%s:%s' % (self.source,self.destination
                ,','.join(map(str,self.digipeaters)),self.information)

class AprsFrame(UIFrame):
    def __init__(self,aprsString=None):
        self.isGood=False #True if all relevant parameters parsed OK
        self.receivedTime=None #UTC time the packet was received
        self.port=None #If multiple streams of packets are being handled
        self.local=False #True if the packet was heard through a locally/over the air
        self.dataType='Unknown' #One of the known, parsable packet types
        self.payload=Payload() #Decoded information from the APRS packet

        UIFrame.__init__(self)

        if not aprsString is None:
            self.parseAprs(aprsString)

    def parseAprs(self,aprsString,receivedTime=None
            ,sourcePort='',heardLocal=False):

        debug('Parse APRSIS: %s' % (aprsString.strip(),))

        self.sourcePort=sourcePort
        self.heardLocal=heardLocal

        #set the received time
        try:
            if receivedTime is None:
                self.receivedTime=datetime.datetime.utcnow()
            elif not type(receivedTime)==datetime.datetime:
                self.receivedTime=self._timeStampToUTC(receivedTime)
            else:
                self.receivedTime=receivedTime
        except:
            self.isGood=False
            warning('Error setting received time from %s (%s)' % \
                    (receivedTime,aprsString))
            raise
            return False

        #parse the UIFrame fields
        try:
            self._parseAprs(aprsString)
        except:
            self.isGood=False
            info('Not a healthy packet: %s' % (aprsString.strip(),))
            raise
            return False

        ##TODO:
        try:
            r=self.payload.parse(self)
        except:
            self.isGood=False
            info('**Error parsing data: %s' % (aprsString.strip(),))
            raise
            return False

        if not r:
            #info("Can't parsing: %s" % aprsString)
            return False

        debug('APRSIS Parsed OK')
        return True

    def localTime(self,format='%c'):
        td=datetime.datetime.utcnow()-datetime.datetime.now()
        local=self.utcTime-td
        return local.strftime(format)

    def _timeStampToUTC(self,ts):
        return datetime.datetime.fromtimestamp(ts)

    def x__str__(self):
        msg=''
        for k,v in self.__dict__.items():
            msg+='\t%s : %s\n' % (k,v)
        return msg

##TODO: put parser in a seperate module
##TODO: get rid of Payload object.  MIC packets blow the idea
class Payload(object):
    def __init__(self):
        """
        Simple parser for APRS packet data payloads
        """
        self.hasLocation=False
        self.latitude=0.0
        self.longitude=0.0
        self.elevation=0
        self.symbolTable=1
        self.symbolCharacter=2
        self.symbolOverlay=''
        self.comment=''

    def parse(self,parent):
        self.parent=parent
        data=self.parent.information
        #---Locations
        ##TODO: ) packets
        if self.parent.information[0] in ('!','=',')'):
            pat=r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            if group:
                debug('re search group found')
                self.parent.reportType='location'
                d=group.groupdict()

                try:
                    self.latitude=int(d['lat'][:2]) + float(d['lat'][2:].replace(' ','5'))/60.0
                    if d['latNS'].lower()=='s':
                        self.latitude*=-1

                    self.longitude=int(d['lon'][:3]) + float(d['lon'][3:].replace(' ','5'))/60.0
                    if d['lonEW'].lower()=='w':
                        self.longitude*=-1
                except:
                    debug('Lat/Lon parsing error: %s' % data)
                    raise

                if d['table']=='/':
                    self.symbolTable=1
                    self.symbolOverlay=''
                else:
                    self.symbolTable=2
                    self.symbolOverlay==d['table']
                self.symbolCharacter=SYMBOLS.find(d['symbol'])

            else:
                info('Unable to parse: %s' % data)
                return False

        #---Locations with time
        elif self.parent.information[0] in (';','@','/'):
            pat=r'(?P<time>[0-9]{6}[zh]{1})(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            ##TODO: combine common parse actions
            ##TODO: position ambiguity
            if group:
                debug('re search group found')
                self.parent.reportType='location with time'
                d=group.groupdict()

                try:
                    self.latitude=int(d['lat'][:2]) + float(d['lat'][2:].replace(' ','5'))/60.0
                    if d['latNS'].lower()=='s':
                        self.latitude*=-1

                    self.longitude=int(d['lon'][:3]) + float(d['lon'][3:].replace(' ','5'))/60.0
                    if d['lonEW'].lower()=='w':
                        self.longitude*=-1
                except:
                    debug('Lat/Lon parsing error: %s' % data)
                    raise

                if d['table']=='/':
                    self.symbolTable=1
                    self.symbolOverlay=''
                else:
                    self.symbolTable=2
                    self.symbolOverlay==d['table']
                self.symbolCharacter=SYMBOLS.find(d['symbol'])

                ##TODO: parse time
                self.reportTime=d['time']

            else:
                info('Unable to parse: %s' % data)
                return False

        #--Status
        elif self.parent.information[0] in (">",):
            self.parent.reportType='Status'
            self.comment=data[1:]
            pat=r'(?P<time>[0-9]{6}[zh]{1})(P<comment>.*)'
            group=re.search(pat,data[1:])
            if group:
                self.parent.reportType='Status with time'
                d=group.groupdict()
                self.reportTime=d['time']
                self.comment=d['comment']

        #---MIC
        elif self.parent.information[0] in ("\'","`","\x1c","\x1d"):
            self.parent.reportType='mice'
            miceparse.decodeMice(self.parent)

        #---GPS RMC
        elif data[:6] in ('$GPRMC',):
            self.parent.reportType='$GPRMC'
            d=data.split(',')
            self.latitude=int(d[3][:2]) + float(d[3][2:])/60.0
            if d[4] in ('S','s'):
                self.latitude*=-1
            self.longitude=int(d[5][:3]) + float(d[5][3:])/60.0
            if d[5] in ('W','w'):
                self.longitude*=-1
            ##TODO: parse time
            self.reportTime=d[1]

        #---GPS GGA
        elif data[:6] in ('$GPGGA',):
            self.parent.reportType='$GPGGA'
            d=data.split(',')
            self.latitude=int(d[2][:2]) + float(d[2][2:])/60.0
            if d[3] in ('S','s'):
                self.latitude*=-1
            self.longitude=int(d[4][:3]) + float(d[4][3:])/60.0
            if d[4] in ('W','w'):
                self.longitude*=-1
            ##TODO: parse time
            self.reportTime=d[1]

        else:
            info('Unrecognized data: %s' % data)
            # Try to parse a lat/long from the packet
            latPat=r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])'
            lonPat=r'(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])'
            latG=re.search(latPat,data)
            lonG=re.search(lonPat,data)
            if latG and lonG:
                self.parent.reportType='Unhandled with position'
                latD=latG.groupdict()
                lonD=lonG.groupdict()
                try:
                    self.latitude=int(d['lat'][:2]) + float(d['lat'][2:].replace(' ','5'))/60.0
                    if d['latNS'].lower()=='s':
                        self.latitude*=-1

                    self.longitude=int(d['lon'][:3]) + float(d['lon'][3:].replace(' ','5'))/60.0
                    if d['lonEW'].lower()=='w':
                        self.longitude*=-1
                except:
                    debug('Lat/Lon parsing error: %s' % data)
                    raise

                debug('----lat/lon parsed anyway')
            return False

        return True

if __name__=='__main__':
    packets=[
        #"""AE6ST-2>S4QSUR,ONYX*,WIDE2-1,qAR,AK7V:`,6*l"Zj/]"?L}"""
        #,"""WA7PIX-9>T6SQUU,KOPEAK*,WIDE2-1,qAR,AC7YY-12:`3Q2 {bk/]"4'}="""
        #,"""JF3UYN>APU25N,TCPIP*,qAC,JG6YCL-JA:=3449.90N/13513.30E-PHG2450 Kita-Rokko Kobe WiRES6084 {UIV32N}"""
        #,"""JM6ISF>APU25N,JM6ISF-3*,TRACE3-2,qAR,JA6YWR:=3129.57N/13042.43EIJ-net 144.66MHz 9600bps I-gate {UIV32N}"""
        """VACA>APNU19,qAR,W6YX-5:;147.195+V*111111z382 .  N/1220 .  Wr T123 R60m"""
        ]
    for p in packets:
        print p
        #x=UIFrame(p)
        x=AprsFrame(p)
        print x
        print str(x).upper()==p.upper()
