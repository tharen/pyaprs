#miceparse.py
"""
Utilities for parsing MICE (encoded) APRS reports
"""

import logging
logger = logging.getLogger('MyLogger')
debug=logger.debug
info=logger.info
exception=logger.exception

DIGITS = '0123456789'
LOWASCII = 'ABCDEFGHIJ'
SPACEASCII = 'KLZ'
HIGHASCII = 'PQRSTUVWXY'

LAT_LOOKUP={ '0':'0','1':'1','2':'2','3':'3','4':'4','5':'5','6':'6','7':'7','8':'8','9':'9'
            ,'A':'0','B':'1','C':'2','D':'3','E':'4','F':'5','G':'6','H':'7','I':'8','J':'9'
            ,'P':'0','Q':'1','R':'2','S':'3','T':'4','U':'5','V':'6','W':'7','X':'8','Y':'9'
            ,'K':' ','L':' ','Z':' '
            }

MESSAGES={  'Standard':{
                        (1,1,1): 'OffDuty'
                        ,(1,1,0): 'En Route'
                        ,(1,0,1): 'In Service'
                        ,(1,0,0): 'Returning'
                        ,(0,1,1): 'Committed'
                        ,(0,1,0): 'Special'
                        ,(0,0,1): 'Priority'
                        }
            ,'Custom':{
                        (1,1,1): 'Custom-0'
                        ,(1,1,0): 'Custom-1'
                        ,(1,0,1): 'Custom-2'
                        ,(1,0,0): 'Custom-3'
                        ,(0,1,1): 'Custom-4'
                        ,(0,1,0): 'Custom-5'
                        ,(0,0,1): 'Custom-6'
                        }
            ,'Emergency':{(0,0,0):'Emergency'}
            }

def decodeMice(packet):
    debug('Parsing MIC')
    ##TODO: how does mic handle ssid
    destination=packet.destination.station
    # MIC type
    if packet.information[0] in ["\'","`","\x1c","\x1d"]:
        packet.payload.micType="MIC1" #MIC-E Packet
    else:
        packet.payload.micType='Unknown'

    # Is this a current report
    packet.payload.micCurrent=False
    packet.payload.micCurrent=packet.information[0] in ('`','\x1c')

    #count the ambiguity characters
    packet.payload.ambiguity=len([c for c in destination if c in SPACEASCII])

    # Latitude
    l=''.join([LAT_LOOKUP[c] for c in destination])
    d=int(l[:2])
    #overlay digits for abiguity
    #for every ambiguous space in the latitude decimal minutes
    #replace it with a mid point digit
    o='3555'
    mm=list(l[2:])
    mm=''.join([mm[i] or o[i] for i in range(len(mm))])
    #convert to mm.mm
    mm=int(mm)/100.0
    #complete the latitude
    packet.payload.latitude=d+mm/60.0

    # Convert N/S latitude
    if destination[4] in DIGITS+'L': packet.payload.latitude*=-1

    lonOffset=0
    if destination[5] in HIGHASCII+'Z':lonOffset=100

    lonDirection=1
    if destination[5] in HIGHASCII+'Z':lonDirection=-1

    #message bits, type, lookup
    ## this ignores the 'unknown' message type in the spec
    packet.payload.messageType='Emergency'
    msgBits=[0,0,0]
    for i in range(3):
        c=destination[i]
        if c in LOWASCII+'K':
            msgBits[i]=1
            packet.payload.messageType='Custom'
        if c in HIGHASCII+'Z':
            msgBits[i]=1
            packet.payload.messageType='Standard'
    packet.payload.messageBits=tuple(msgBits)
    packet.payload.message=MESSAGES[packet.payload.messageType][packet.payload.messageBits]

    ##TODO: destination SSID field

    #longitude
    info=packet.information[1:9]
    d=(ord(info[0])-28)+lonOffset
    if 180<=d<=189: d-=80
    elif 190<=d<=199: d-=190

    m=ord(info[1])-28
    if m>=60:m-=60
    h=(ord(info[2])-28)/100.0

    m+=h

    ddm=d+m/60.0
    ddm*=lonDirection

    packet.payload.longitude=ddm

    ##TODO: is this mic comment split right?
    packet.payload.comment=''
    if packet.payload.comment.find('}')>-1:
        packet.payload.comment=packet.information.split('}')[1]

    ##TODO: finish

if __name__=='__main__':
    import aprspacket
    r="""KE7NZA>T0TSWR-2,WIDE1-1,WIDE2-2,qAR,K2NWS-1:`'Ptl!\v/"B4}KE7NZA TinyTrak3"""
    packet=aprspacket.AprsFrame()
    packet.parseAprs(r)
    #decodeMice(packet)
    print packet
    print packet.payload.latitude,packet.payload.longitude
