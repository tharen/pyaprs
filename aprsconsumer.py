#aprsconsumer.py
"""
APRS consumer superclass and associated objects
"""
import Queue,datetime
import re
import logging

# Reference the global logger
my_logger = logging.getLogger('MyLogger')
debug=my_logger.debug
info=my_logger.info

class Consumer:
    def __init__(self,name,*args,**kwargs):
        self.name=name
        self.status=0 #0=init, 1=ready, -1=error
        self.queueIn=Queue.Queue()

    def start(self):
        """
        Main loop to handle BasicPackets placed in the queue
        """
        while 1:
            #block while waiting for data to handle
            flag,basicPacket=self.queueIn.get()
            if flag=='stop':
                break
            self.consume(basicPacket)

    def consume(self,basicPacket):
        """
        Do something with packet data
        """
        x=basicPacket

class BasicPacket(object):
    def __init__(self,):
        self.utcTime=None
        self.aprsisString=''
        self.station=''
        self.path=''
        self.payload=Payload()

    def fromAPRSIS(self,aprsisString,utcTime=datetime.datetime.utcnow()):
        debug('fromAPRSIS: %s' % (aprsisString.strip(),))
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
        if self.data.startswith('!'):
            pat=r'!(?P<lat>[0-9]{4}\.[0-9]{2})(?P<latNS>[NS]).(?P<lon>[01][0-9]{4}\.[0-9]{2})(?P<lonEW>[EW])'
            latlon=re.match(pat,data)
            if latlon:
                d=latlon.groupdict()

                latD=int(d['lat'][:2])
                latDM=float(d['lat'][2:])
                lat=latD+latDM/60.0
                if d['latNS'].lower()=='s': lat*=-1

                lonD=int(d['lon'][:3])
                lonDM=float(d['lon'][3:])
                lon=lonD+lonDM/60.0
                if d['lonEW'].lower()=='w': lon*=-1

                self.lat=lat
                self.lon=lon

            else:
                info('Parsing failed with: %s' % data)
                return False
        else:
            info('Unrecognized data payload %s' % data)
            return False

        return True

class Producer:
    def __init__(self,name):
        """
        Producer super class
        """
        self.name=name
        self.status=0 #0-init, 1-running, 3-error
        self.errorMessage=''
        self.queueOut=Queue.Queue()

    def start(self):
        """
        Start producing packets.  This would most likely be a loop
        of some sort to respond to a data stream, query interval, etc.

        ** This should be overwritten
        """
        while 1:
            data='Error: Super Class instance'
            self.queueOut.put(data)
            time.sleep(0.5)

if __name__=='__main__':
    p='!3858.21N/09007.02W#PHG3430/W3,Godfrey IL kb9bpf@arrl.net TNX K9SD\r\n'
    payload=Payload(p)
