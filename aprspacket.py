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

class BasicPacket(object):
    def __init__(self,):
        self.utcTime=None
        self.sourcePort=''
        self.heardLocal=False
        self.reportTime=None  ##TODO: report time is part of the payload
        self.aprsisString=''
        self.fromCall=''
        self.fromSSID=''
        self.path=''
        self.payload=Payload(self)
        self.toCall=''
        self.toSSID=''

    def fromDbRow(self,row):
        self.utcTime=self.timeStampToUTC(row[0])
        self.aprsisString=row[1]
        self.sourcePort=row[2]
        self.heardLocal=row[3]
        self.fromCall=row[4]
        self.fromSSID=row[5]
        self.toCall=row[6]
        self.toSSID=row[7]
        self.path=row[8]
        self.reportType=row[9]
        self.payload.parse('%s-%s' % (self.toCall,self.toSSID),row[10])
##        self.symbolTable=row[11]
##        self.symbolCharacter=row[12]
##        self.symbolOverlay=row[13]
##        self.latitude=row[14]
##        self.longitude=row[15]
##        self.elevation=row[16]

    def timeStampToUTC(self,ts):
        return datetime.datetime.fromtimestamp(ts)

    def fromAPRSIS(self,aprsisString,utcTime=datetime.datetime.utcnow()
            ,sourcePort='',heardLocal=False):
        debug('Parse APRSIS: %s' % (aprsisString.strip(),))
        try:
            fromCall,data=aprsisString.strip().split('>',1)
            if '-' in fromCall:
                fromCall,fromSSID=fromCall.split('-',1)
            else:
                fromSSID=''
            toCall,data=data.split(',',1)
            if '-' in toCall:
                toCall,toSSID=toCall.split('-',1)
            else:
                toSSID=''
            path,data=data.split(':',1)
        except:
            info('Not a complete packet: %s' % (aprsisString.strip(),))
            return False
        self.utcTime=utcTime
        self.sourcePort=sourcePort
        self.heardLocal=heardLocal
        self.aprsisString=aprsisString
        self.fromCall=fromCall
        self.fromSSID=fromSSID
        self.toCall=toCall
        self.path=path
        try:
            r=self.payload.parse(self.toCall,data)
        except:
            info('**Error parsing data: %s' % (aprsisString.strip(),))
            return False

        if not r:
            #info("Can't parsing: %s" % aprsisString)
            return False

        debug('APRSIS Parsed OK')
        return True

    def localTime(self,format='%c'):
        td=datetime.datetime.utcnow()-datetime.datetime.now()
        local=self.utcTime-td
        return local.strftime(format)

    def __str__(self):
        msg=''
        for k,v in self.__dict__.items():
            msg+='\t%s : %s\n' % (k,v)
        return msg

##TODO: put parser in a seperate module
##TODO: get rid of Payload object.  MIC packets blow the idea
class Payload(object):
    def __init__(self,parent):
        """
        Simple parser for APRS packet data payloads
        """
        self.parent=parent
        self.reportType=''
        self.data=''
        self.latitude=0.0
        self.longitude=0.0
        self.elevation=0
        self.symbolTable=1
        self.symbolCharacter=2
        self.symbolOverlay=''

    def parse(self,toCall,data):
        self.data=data

        #---Standard reports
        ##TODO: ) packets
        if self.data[0] in ('!','=',')'):
            pat=r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            if group:
                debug('re search group found')
                self.reportType='standard'
                d=group.groupdict()

                self.latitude=int(d['lat'][:2]) + float(d['lat'][2:])/60.0
                if d['latNS'].lower()=='s':
                    self.latitude*=-1

                self.longitude=int(d['lon'][:3]) + float(d['lon'][3:])/60.0
                if d['lonEW'].lower()=='w':
                    self.longitude*=-1

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

        #---Reports with time
        elif self.data[0] in (';','@','/'):
            pat=r'(?P<time>[0-9]{6}[zh]{1})(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])(?P<table>.)(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])(?P<symbol>.)'
            group=re.search(pat,data)
            ##TODO: combine common parse actions
            if group:
                debug('re search group found')
                self.reportType='standard with time'
                d=group.groupdict()

                self.latitude=int(d['lat'][:2]) + float(d['lat'][2:])/60.0
                if d['latNS'].lower()=='s':
                    self.latitude*=-1

                self.longitude=int(d['lon'][:3]) + float(d['lon'][3:])/60.0
                if d['lonEW'].lower()=='w':
                    self.longitude*=-1

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

        #---MIC
        elif self.data[0] in ("\'","`","\x1c","\x1d"):
            self.reportType='mice'
            miceparse.decodeMice(self.parent)

        #---GPS RMC
        elif data[:6] in ('$GPRMC',):
            self.reportType='$GPRMC'
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
            self.reportType='$GPGGA'
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
                self.reportType='Unhandled with position'
                latD=latG.groupdict()
                lonD=lonG.groupdict()
                self.latitude=int(latD['lat'][:2]) + float(latD['lat'][2:])/60.0
                if latD['latNS'].lower()=='s':
                    self.latitude*=-1

                self.longitude=int(lonD['lon'][:3]) + float(lonD['lon'][3:])/60.0
                if lonD['lonEW'].lower()=='w':
                    self.longitude*=-1
                debug('----lat/lon parsed anyway')
            return False

        return True

if __name__=='__main__':
    x=BasicPacket()
    #p=';KC7RWC-10*120712z4541.2 NW11852.5 Wa144.950MHz 1200 R11m RMSPacket EMCOMM'
    #p='=4502.25N/00737.52e- info: www.qsl.net/ik1mtx'
    #p='!5045.65n/01909.12e#phg2070 MiniDigi Czestochowa 342mnpm na testach'
    #p='$GPRMC,073728,A,3157.8168,N,11017.8101,W,0.000,0.0,120709,11.4,E*5D'
    #p='$GPGGA,081200,4451.2358,N,08936.9620,W,2,07,1.5,341.4,M,-34.6,M,,*74'
    p="""WA7PIX-9>T6SQUU,KOPEAK*,WIDE2-1,qAR,AC7YY-12:`3Q2 {bk/]"4'}="""
    payload=Payload(x)
    x.fromAPRSIS(p)
    #payload.parse()
    print x