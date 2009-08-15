#sqlconsumer.py

"""
Consumes basic packets and stores them in a SQL database

Currently SQLite3 only
"""
from aprsconsumer import Consumer
from aprspacket import BasicPacket

from sqlite3 import dbapi2 as dba

import logging,sys
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info
exception=logger.exception

##TODO: This is sqlite3 specific
def adapt_datetime(ts):
    return time.mktime(ts.timetuple()) + float(str(ts.microsecond)[:3])/1000
dba.register_adapter(datetime.datetime, adapt_datetime)

class Main(Consumer):
    def __init__(self,parameters,name,connString=':memory:'):
        Consumer.__init__(self,parameters,name)

    def _runFirst(self):
        debug('Connecting to DB')
        self.__connect()
        if self.parameters.build_db==1:
            self._buildDB()

    def consume(self,packet):
        #check to see if the packet is already in the system
        debug('Storing Packet')
        cur=self.dbConn.cursor()
        cur.execute("""select * from Reports
            where fromCall=? and fromSSID=?
                and payload=?
            """,(packet.fromCall,packet.fromSSID,packet.payload.data)
            )
        storedReport=cur.fetchone()

        ##TODO: add time/dupe filter
        if storedReport:
            if storedReport.heardLocal:
                debug('dupe report previously heard locally')
                return
            if packet.heardLocal:
                debug('Replace dupe with local')
                self.__updateReport(packet)

        else:
            debug('insert new packet report')
            self.__insertReport(packet)

    def __updateReport(self,packet):
        ##TODO: update query
        pass

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
        debug('SQL report insert successfull')

    def __connect(self):
        ##TODO: error trap db connection
        self.dbConn=dba.connect(self.parameters.connection_string)
        #sql="""SELECT load_extension('bin/libspatialite-2.dll')"""
        #self.dbConn.execute(sql)

    def __disconnect(self):
        self.dbConn.close()

    def _buildDB(self):
        """
        Creates the tables necessary for tracking APRS stations

        """
        info('Rebuilding DB')

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
            ,reportType (30) not null
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
##        sql="""
##            alter table Reports
##            add constraint pk_Reports_reportId
##            primary key (fromCall,fromSSID,receivedTime)
##            """
##        self.dbConn.execute(sql)
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

        info('DB rebuild complete')

def test():
    import ConfigParser
    from main import ConfigSection
    from aprspacket import BasicPacket
    dbConn=':memory:'
    iniFile='aprsmonitor.ini'
    cfg=ConfigParser.ConfigParser()
    cfg.read(iniFile)
    params=ConfigSection(cfg.items('sqlite_1'))
    print cfg.sections()
    consumer=Main(params,'sqlite_1',':memory:')
    consumer._runFirst()
    consumer._buildDB()

    reports=("""JF3UYN>APU25N,TCPIP*,qAC,JG6YCL-JA:=3449.90N/13513.30E-PHG2450 Kita-Rokko Kobe WiRES6084 {UIV32N}"""
            ,"""JM6ISF>APU25N,JM6ISF-3*,TRACE3-2,qAR,JA6YWR:=3129.57N/13042.43EIJ-net 144.66MHz 9600bps I-gate {UIV32N}"""
            )

    packets=[]
    for report in reports:
        bp=BasicPacket()
        bp.fromAPRSIS(report)
        packets.append(bp)

    for packet in packets:
        print 'Storing: \n%s::%s' % ('-'.join((packet.fromCall,packet.fromSSID)),packet.payload.data)
        consumer.consume(packet)

    #consumer._buildDB()

if __name__=='__main__':
    test()