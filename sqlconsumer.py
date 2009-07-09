#sqlconsumer.py

"""
Consumes basic packets and stores them in a SQL database

Currently SQLite3 only
"""
from consumer import *

from sqlite3 import dbapi2 as dba

class SQLConsumer(Consumer):
    def __init__(self,connString):
        Consumer.__init__(self)
        self.connString=connString

    def consume(self,rawPacket):
        pass

    def __connect(self):
        ##TODO: error trap db connection
        self.dbConn=dba.connect(self.connString)
        sql="""SELECT load_extension('bin/libspatialite-2.dll')"""
        self.dbConn.execute(sql)

    def __disconnect(self):
        self.dbConn.close()

    def _buildDB(self):
        """
        Creates the tables necessary for tracking APRS stations
        """
        self.__connect()
        sql="""create table Reports
            reportId int not null
            station text(10) not null
            path text (50) not null
            payload text (100) not null
            """
        self.dbConn.execute(sql)
        sql="""alter table reports
        add constraint pk_Reports_reportId
        primary key (reportId)
        """
        self.dbConn.execute(sql)
        sql="""
        """

        self.__disconnect()

if __name__=='__main__':
    dbConn=':memory:'
    consumer=SQLConsumer(dbConn)
    consumer._buildDB()