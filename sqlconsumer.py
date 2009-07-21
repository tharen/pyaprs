#sqlconsumer.py

"""
Consumes basic packets and stores them in a SQL database

Currently SQLite3 only
"""
from aprsconsumer import Consumer
from aprspacket import BasicPacket

from sqlite3 import dbapi2 as dba

class Main(Consumer):
    def __init__(self,connString,parameters,name):
        Consumer.__init__(self,parameters,name)
        self.__connect()

    def consume(self,rawPacket):
        pass

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
        sql="""create table Reports
            reportId int not null
            fromCall text(10) not null
            path text (50) not null
            payload text (100) not null
            utcTime date not null
            """
        self.dbConn.execute(sql)
        sql="""
            alter table reports
            add constraint pk_Reports_reportId
            primary key (reportId)
            """
        self.dbConn.execute(sql)
        sql="""
            create index idx_Reports_fromCall
                on Reports (fromCall)
            """
        self.dbConn.execute(sql)


if __name__=='__main__':
    import ConfigParser
    dbConn=':memory:'
    iniFile='aprsmonitor.ini'
    cfg=ConfigParser.ConfigParser()
    cfg.read(iniFile)

    consumer=Main(dbConn,cfg,'sqlite_1')
    consumer._buildDB()