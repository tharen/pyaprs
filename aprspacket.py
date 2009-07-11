import datetime,re

import logging
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info

class BasicPacket(object):
    def __init__(self,):
        self.utcTime=None
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
            debug('Not a complete packet: %s' % (aprsisString.strip(),))
            return False
        self.utcTime=utcTime
        self.aprsisString=aprsisString
        self.station=stn
        self.path=path
        r=self.payload.parse(data)

        if not r: return False

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
        self.lat=0.0
        self.lon=0.0
        self.elev=0

    def parse(self,data):
        self.data=data
        if self.data[0] in ('!'):
            pat=r'(?P<lat>[0-9]{4}\.[0-9]{2})(?P<latNS>[NS])(?P<symbol>.)(?P<lon>[01][0-9]{4}\.[0-9]{2})(?P<lonEW>[EW])'
            group=re.search(pat,data)
            if group:
                debug('re search group found')
                d=group.groupdict()

                latD=int(d['lat'][:2])
                latDM=float(d['lat'][2:])
                lat=latD+latDM/60.0
                if d['latNS'].lower()=='s': lat*=-1

                lonD=int(d['lon'][:3])
                lonDM=float(d['lon'][3:])
                lon=lonD+lonDM/60.0
                if d['lonEW'].lower()=='w': lon*=-1

                self.latitude=lat
                self.longitude=lon
                self.symbol=d['symbol']

            else:
                debug('Unable to parse: %s' % data)
                return False
        else:
            debug('Unrecognized data: %s' % data)
            return False

        return True
