import datetime,re

import logging
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info

class BasicPacket(object):
    def __init__(self,):
        self.utcTime=None
        self.reportTime=None
        self.aprsisString=''
        self.station=''
        self.path=''
        self.payload=Payload()

    def fromAPRSIS(self,aprsisString,utcTime=datetime.datetime.utcnow()):
        debug('Parse APRSIS: %s' % (aprsisString.strip(),))
        try:
            stn,data=aprsisString.strip().split('>',1)
            path,data=data.split(':',1)
        except:
            info('Not a complete packet: %s' % (aprsisString.strip(),))
            return False
        self.utcTime=utcTime
        self.aprsisString=aprsisString
        self.station=stn
        self.path=path
        r=self.payload.parse(data)

        if not r:
            #info("Can't parsing: %s" % aprsisString)
            return False

        debug('APRSIS Parsed OK')
        return True

    def localTime(self,format='%c'):
        td=datetime.datetime.utcnow()-datetime.datetime.now()
        local=self.utcTime-td
        return local.strftime(format)

##TODO: put parser in a seperate module
class Payload(object):
    def __init__(self):
        """
        Simple parser for APRS packet data payloads
        """
        self.data=''
        self.latitude=0.0
        self.longitude=0.0
        self.elevation=0

    def parse(self,data):
        self.data=data

        #---Standard reports
        ##TODO: ) packets
        if self.data[0] in ('!','=',')'):
            pat=r'(?P<lat>[0-9]{4}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{4}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            if group:
                debug('re search group found')
                d=group.groupdict()

                self.latitude=int(d['lat'][:2]) + float(d['lat'][2:])/60.0
                if d['latNS'].lower()=='s':
                    self.latitude*=-1

                self.longitude=int(d['lon'][:3]) + float(d['lon'][3:])/60.0
                if d['lonEW'].lower()=='w':
                    self.longitude*=-1

                self.symbolTable=d['table']
                self.symbol=d['symbol']

            else:
                info('Unable to parse: %s' % data)
                return False

        #---Reports with time
        elif self.data[0] in (';','@','/'):
            pat=r'(?P<time>[0-9]{6}[zh/]{1})(?P<lat>[0-9]{4}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{4}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            ##TODO: combine common parse actions
            if group:
                debug('re search group found')
                d=group.groupdict()

                self.latitude=int(d['lat'][:2]) + float(d['lat'][2:])/60.0
                if d['latNS'].lower()=='s':
                    self.latitude*=-1

                self.longitude=int(d['lon'][:3]) + float(d['lon'][3:])/60.0
                if d['lonEW'].lower()=='w':
                    self.longitude*=-1

                self.symbolTable=d['table']
                self.symbol=d['symbol']
                ##TODO: parse time
                self.reportTime=d['time']

            else:
                info('Unable to parse: %s' % data)
                return False

        #---GPS RMC
        elif data[:6] in ('$GPRMC',):
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
            d=data.split(',')
            self.latitude=int(d[2][:2]) + float(d[3][2:])/60.0
            if d[3] in ('S','s'):
                self.latitude*=-1
            self.longitude=int(d[4][:3]) + float(d[5][3:])/60.0
            if d[4] in ('W','w'):
                self.longitude*=-1
            ##TODO: parse time
            self.reportTime=d[1]

        else:
            info('Unrecognized data: %s' % data)
            return False

        return True

if __name__=='__main__':
    #p=';KC7RWC-10*120712z4541.2 NW11852.5 Wa144.950MHz 1200 R11m RMSPacket EMCOMM'
    #p='=4502.25N/00737.52e- info: www.qsl.net/ik1mtx'
    p='!5045.65n/01909.12e#phg2070 MiniDigi Czestochowa 342mnpm na testach'
    #p='$GPRMC,073728,A,3157.8168,N,11017.8101,W,0.000,0.0,120709,11.4,E*5D'
    #p='$GPGGA,081200,4451.2358,N,08936.9620,W,2,07,1.5,341.4,M,-34.6,M,,*74'
    payload=Payload()
    payload.parse(p)
    print payload.__dict__