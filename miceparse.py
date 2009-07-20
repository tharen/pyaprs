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

    # MIC type
    if packet.payload.data[0] in ["\'","`","\x1c","\x1d"]:
        packet.micType="MIC1" #MIC-E Packet
    else:
        packet.micType='Unknown'

    # Is this a current report
    packet.micCurrent=False
    packet.micCurrent=packet.payload.data[0] in ('`','\x1c')

    #count the ambiguity characters
    packet.ambiguity=len([c for c in packet.toCall if c in SPACEASCII])

    # Latitude
    l=''.join([LAT_LOOKUP[c] for c in packet.toCall])
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
    packet.latitude=d+mm/60.0

    # Convert N/S latitude
    if packet.toCall[4] in DIGITS+'L': packet.latitude*=-1

    lonOffset=0
    if packet.toCall[5] in HIGHASCII+'Z':lonOffset=100

    lonDirection=1
    if packet.toCall[5] in HIGHASCII+'Z':lonDirection=-1

    #message bits, type, lookup
    ## this ignores the 'unknown' message type in the spec
    packet.messageType='Emergency'
    msgBits=[0,0,0]
    for i in range(3):
        c=packet.toCall[i]
        if c in LOWASCII+'K':
            msgBits[i]=1
            packet.messageType='Custom'
        if c in HIGHASCII+'Z':
            msgBits[i]=1
            packet.messageType='Standard'
    packet.messageBits=tuple(msgBits)
    packet.message=MESSAGES[packet.messageType][packet.messageBits]

    ##TODO: destination SSID field

    #longitude
    info=packet.payload.data[1:9]
    d=(ord(info[0])-28)+lonOffset
    if 180<=d<=189: d-=80
    elif 190<=d<=199: d-=190

    m=ord(info[1])-28
    if m>=60:m-=60
    h=(ord(info[2])-28)/100.0

    m+=h

    ddm=d+m/60.0
    ddm*=lonDirection

    packet.longitude=ddm

    ##TODO: finish

if __name__=='__main__':
    import aprspacket
    r="""WA7PIX-9>T6SQUU,KOPEAK*,WIDE2-1,qAR,AC7YY-12:`3Q2 {bk/]"4'}="""
    packet=aprspacket.BasicPacket()
    packet.fromAPRSIS(r)
    decodeMice(packet)
    print packet
    print packet.latitude,packet.longitude
