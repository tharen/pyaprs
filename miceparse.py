#miceparse.py
"""
Utilities for parsing MICE (encoded) APRS reports
"""

DIGITS = '0123456789'
LOWASCII = 'ABCDEFGHIJ'
SPACEASCII = 'KLZ'
HIGHASCII = 'PQRSTUVWXY'

def decodeMice(packet):
    p=packet
    p.destination=p.path.split(',')[0]

    # MIC type
    if p.payload.data[0] in ["\'","`","\x1c","\x1d"]:
        p.micType="MIC1" #MIC-E Packet
    else:
        p.micType='Unknown'

    # Is this a current report
    p.micCurrent=p.payload.data[0]=='`' #or '\x1c'

    p.ambiguity=len([c for c in p.destination if c in SPACEASCII])

    # Latitude
    j=DIGITS+LOWASCII+HIGHASCII
    l=p.destination[:-p.ambiguity]+'K'*p.ambiguity

    ##TODO: handle ambiguity digits
    latD=int('%d%d' % (j.find(p.destination[0])%10,j.find(p.destination[1])%10))
    m=int('%d%d' % (j.find(p.destination[2])%10,j.find(p.destination[3])%10))
    latM=m+int('%d%d' % (j.find(p.destination[2])%10,j.find(p.destination[3])%10))/100.0
    p.latitude=latD+latM/60.0
    if p.destination[3] in DIGITS+'L':
        p.latitude*=-1



if __name__=='__main__':
    import aprspacket
    r="""KD7NVB-14>TU3UQS,LARCH,WIDE1*,WIDE2-1,qAR,WH6KO:`2Di sEu/]"4F}"""
    p=aprspacket.BasicPacket()
    p.fromAPRSIS(r)
    decodeMice(p)
    print p
