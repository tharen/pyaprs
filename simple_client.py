
import socket,select,time,datetime
from aprspacket import BasicPacket
from sqlite3 import dbapi2 as dba

APPLICATION='pyaprs'
VERSION='0.0b'

class APRSISClient:
    def __init__(self,packetHandler,host,port
            ,username,password,adjunct
            ,timeout=10,pollInterval=.1
            ):
        self.hostName=host
        self.hostPort=port
        self.username=username
        self.password=password
        self.adjunct=adjunct
        self.timeout=timeout
        self.pollInterval=pollInterval
        self.packetHandler=packetHandler

        self.socket=None
        self.socketBuffer=''
        self.bps=0
        self.bytesTally=0
        self.packetTally=0
        self.bpsBytes={}
        self.bpsInterval=10

    def start(self):
        self.__connect()
        self.startTime=time.clock()
        q=time.clock()
        while 1:
##            try:
                #select returns 3 lists of sockets
                ##TODO: timeout is unnecessary if running in a private thread
                readReady,writeReady,inError=select.select([self.socket,],[],[],self.timeout)
                if self.socket in readReady:
                    try:
                        self.__handleData()
                    except:
                        print 'Error handling data'
                    #log something interesting
                    if time.clock()-q>10:
                        print 'Packet Tally: %d, Bytes Tally: %d, BPS: %.2f' % (self.packetTally,self.bytesTally,self.bps)
                        q=time.clock()
##            except:
##                ##TODO: seperate select exceptions from other errors
##                ##          ie. network failures, disapearing host, etc
##                print 'Select failed, attempt to reopen socket'
##                time.sleep(.5)
##                self.__connect()

                time.sleep(self.pollInterval)

    def __handleData(self):
        try:
            data=self.socket.recv(200)
        except:
            print 'Connection Error'
            self.__connect()
            time.sleep(.5)
            return False
        self.socketBuffer += data
        utcTime=datetime.datetime.utcnow()
        #lines=self.socketBuffer.split('\r\n')
        if self.socketBuffer.endswith('\r\n'):
            #buffer ends on a aprsis new line
            lines=self.socketBuffer.strip().split('\r\n')
            self.socketBuffer=''
        else:
            #buffer is not terminated by newline
            lines=self.socketBuffer.strip().split('\r\n')
            self.socketBuffer='%s' % lines.pop(-1)

        for line in lines:

            #track traffic volume
            x=time.clock()
            bytes=len(line)

            self.bytesTally+=bytes
            self.packetTally+=1

            #calculate the bits per second, processed packets
            self.bpsBytes[x]=bytes
            keys=self.bpsBytes.keys()
            for k in keys:
                if x-k>self.bpsInterval:
                    self.bpsBytes.pop(k)
            t=x-min(self.bpsBytes.keys())
            b=sum(self.bpsBytes.values())
            if t==0: self.bps=0
            else: self.bps=b*8/t

            #print line.strip()
            packet=BasicPacket()
            try:
                ok = packet.fromAPRSIS(line.strip(),utcTime)
            except:
                ok=False
                print 'Parse Error: %s' % line.strip()

            if ok!=True:
                print 'Unhandled Report: %s' % line.strip()
                continue
            #if all looks good, post the packet to the output queue

            try:self.packetHandler(packet)
            except:print line.strip()
            del packet

    def __connect(self):
        print 'Opening socket to %s,%d' % (self.hostName,self.hostPort)
        self.socket=socket.socket(
                family=socket.AF_INET
                ,type=socket.SOCK_STREAM
                )
        self.socketBuffer=''
        host=self.hostName
        port=int(self.hostPort)
        self.socket.connect((host,port))
        if not self.__aprsisLogin():
            raise Error
        return True

    def __aprsisLogin(self):
        print 'Attempting APRSIS Login'
        ##TODO: robustify
        ##TODO: do recv non-blocking
        self.socketBuffer=''
        h=self.socket.recv(200)
        print 'rcvd: %s' % h.strip()
        if not h.startswith('# javAPRSSrvr 3'):
            print 'Not a known APRSIS Server'
            return False

        connStr='user %s pass %s vers %s %s %s\r\n' % \
                (self.username,self.password,APPLICATION,VERSION,self.adjunct)
        self.socket.send(connStr)
        print 'sent: %s' % connStr.strip()
        d=self.socket.recv(200)
        print 'rcvd: %s' % d.strip()

        if d.startswith('# logresp %s verified' % self.username):
            print 'APRSIS Login Successful'
            return True
        else:
            print 'APRSIS Login Failed'
            return False

class SQLHandler:
    def __init__(self,connectionString,dupeSeconds=60
            ,purgeAge=1*24*60*60,purgeInterval=60):
        self.connectionString=connectionString
        self.dupeSeconds=dupeSeconds
        self.purgeAge=purgeAge
        self.purgeInterval=purgeInterval
        self.lastPurge=0
        self.__connect()

    def __connect(self):
        ##TODO: error trap db connection
        self.dbConn=dba.connect(self.connectionString)
        #sql="""SELECT load_extension('bin/libspatialite-2.dll')"""
        #self.dbConn.execute(sql)

    def __replaceReport(self,packet):
        cur=self.dbConn.cursor()
        cur.execute("""delete from Reports
            where fromCall=? and fromSSID=?
                and payload=?
            """,(packet.fromCall,packet.fromSSID,packet.payload.data)
            )
        cur.close()

        self.__insertReport(packet)

    def __insertReport(self,packet):
        sql="""insert into Reports (
            receivedTime
            ,aprsisString
            ,sourcePort
            ,heardLocal
            ,fromCall
            ,fromSSID
            ,toCall
            ,toSSID
            ,path
            ,reportType
            ,payload
            ,symbolTable
            ,symbolCharacter
            ,symbolOverlay
            ,latitude
            ,longitude
            ,elevation
            )
            values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
        vals=(  packet.utcTime
                ,packet.aprsisString
                ,packet.sourcePort
                ,packet.heardLocal
                ,packet.fromCall
                ,packet.fromSSID
                ,packet.toCall
                ,packet.toSSID
                ,packet.path
                ,packet.payload.reportType
                ,packet.payload.data
                ,packet.payload.symbolTable
                ,packet.payload.symbolCharacter
                ,packet.payload.symbolOverlay
                ,packet.payload.latitude
                ,packet.payload.longitude
                ,packet.payload.elevation
            )
        self.dbConn.execute(sql,vals)
        self.dbConn.commit()

    def _buildDB(self):
        """
        Creates the tables necessary for tracking APRS stations

        """
        #drop the table first
        self.dbConn.execute('drop table if exists Reports')

        sql="""create table Reports (
            receivedTime date not null
            ,aprsisString text(200) not null
            ,sourcePort text(50)
            ,heardLocal bit
            ,fromCall text(10) not null
            ,fromSSID text(2)
            ,toCall text(10) not null
            ,toSSID text(2)
            ,path text (50) not null
            ,reportType text (30) not null
            ,payload text (100) not null
            ,symbolTable text(1)
            ,symbolCharacter text(1)
            ,symbolOverlay text(1)
            ,latitude real
            ,longitude real
            ,elevation real

            ,constraint pk_Reports_reportId
                primary key (fromCall,fromSSID,receivedTime,payload)
            )
            """
        self.dbConn.execute(sql)
        sql="""
            create index idx_Reports_fromCall
                on Reports (fromCall)
            """
        self.dbConn.execute(sql)
        sql="""
            create index idx_Reports_Positions
                on Reports (
                    fromCall,fromSSID
                    ,latitude,longitude,elevation
                    )
            """
        self.dbConn.execute(sql)

        self.dbConn.commit()

        self.dbConn.execute('vacuum')

    def consume(self,packet):
        #check to see if the packet is already in the system
        cur=self.dbConn.cursor()
        cur.execute("""select receivedTime,heardLocal from Reports
            where fromCall=? and fromSSID=?
                and payload=?
            """,(packet.fromCall,packet.fromSSID,packet.payload.data)
            )
        storedReport=cur.fetchone()

        ##TODO: add time/dupe filter

        if storedReport:
            td=datetime.datetime.utcnow()-datetime.datetime.fromtimestamp(storedReport[0])

            #duplicate but dupe time has expired
            s=td.days*24*60*60 + td.seconds
            if s>=self.dupeSeconds:
                print 'Dupe (time ellapsed): %d - %s' % (s,packet.aprsisString)
                self.__insertReport(packet)
            else:
                if storedReport[1]:
                    print 'Dupe (previous local): %s' % packet.aprsisString
                    return
                elif packet.heardLocal:
                    print 'Dupe (local): %s' % packet.aprsisString
                    self.__replaceReport(packet)
                else:
                    print 'Dupe (ignored): %s' % packet.aprsisString
        else:
            self.__insertReport(packet)

        cur.close()

        x=time.time()
        if x-self.lastPurge>self.purgeInterval:
            self.__purge()
            self.lastPurge=x

    def __purge(self):
        print 'Purging old reports'
        td=datetime.timedelta(seconds=self.purgeAge)
        min=datetime.datetime.utcnow()-td
        self.dbConn.execute('delete from Reports where receivedTime<?', (min,))

def adapt_datetime(ts):
    return time.mktime(ts.timetuple()) + float(str(ts.microsecond)[:3])/1000

def run():
    dba.register_adapter(datetime.datetime, adapt_datetime)
    handler=SQLHandler('aprs.db')
    handler._buildDB()
    host='first.aprs.net'
    port=20152
    username='KE7FXL'
    password=22445
    adjunct=''
    client=APRSISClient(handler.consume,host,port,username,password,adjunct)
    client.start()

if __name__=='__main__':
    run()