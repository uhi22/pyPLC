
# This module "prints" log messages to UDP broadcasts to port 514.

from helpers import prettyMac

class udplog():
    def fillMac(self, macbytearray, position=6): # position 6 is the source MAC
        for i in range(0, 6):
            self.EthTxFrame[6+i] = macbytearray[i]
            
                          
    def log(self, s):
        strLevel="<15>"
        strMessage=s+"\0"
      
        lenPayLoad = 4 + len(strMessage)
        
        buffer=bytearray(lenPayLoad+28)
        # syslog level (4 characters)
        for i in range(0, len(strLevel)):
            buffer[28+i] = ord(strLevel[i])
        # the message, terminated by 00    
        for i in range(0, len(strMessage)):
            buffer[32+i] = ord(strMessage[i])        
        buffer[0] = 0x45 # IP header len
        buffer[1] = 0
        iplen=len(buffer) # including IP header and all payload
        buffer[2] = iplen >> 8
        buffer[3] = (iplen & 0xff)
        ipid = 0x8a9f
        buffer[4] = ipid >> 8
        buffer[5] = (ipid & 0xff)
        fragoffset = 0
        buffer[6] = fragoffset >> 8
        buffer[7] = (fragoffset & 0xff)
        buffer[8] = 0x80 # ttl
        buffer[9] = 0x11 # proto
        checksum = 0
        buffer[10] = checksum >> 8
        buffer[11] = (checksum & 0xff)
        # source ip 4 bytes
        buffer[12] = 192 # does this really matter?
        buffer[13] = 168
        buffer[14] = 2
        buffer[15] = 222
        # destination ip 4 bytes: broadcast
        buffer[16] = 0xff
        buffer[17] = 0xff
        buffer[18] = 0xff
        buffer[19] = 0xff
        # source port
        buffer[20] = 0xff
        buffer[21] = 0x95
        # destination port
        buffer[22] = 0x02
        buffer[23] = 0x02
        udplen = lenPayLoad + 8 # payload plus 8 byte udp header
        buffer[24] = udplen >> 8
        buffer[25] = (udplen & 0xff)
        udpchecksum = 0
        buffer[26] = udpchecksum >> 8
        buffer[27] = (udpchecksum & 0xff)
        

            
        # packs the IP packet into an ethernet packet
        self.EthTxFrame = bytearray(len(buffer) + 6 + 6 + 2) # Ethernet header needs 14 bytes:
                                                      #  6 bytes destination MAC
                                                      #  6 bytes source MAC
                                                      #  2 bytes EtherType
        # fill the destination MAC with broadcast MAC
        self.EthTxFrame[0] = 0xFF
        self.EthTxFrame[1] = 0xFF
        self.EthTxFrame[2] = 0xFF
        self.EthTxFrame[3] = 0xFF
        self.EthTxFrame[4] = 0xFF
        self.EthTxFrame[5] = 0xFF
        self.fillMac(self.ownMac) # bytes 6 to 11 are the source MAC
        self.EthTxFrame[12] = 0x08 # 0800 is IPv4
        self.EthTxFrame[13] = 0x00
        for i in range(0, len(buffer)):
            self.EthTxFrame[14+i] = buffer[i]
        self.transmit(self.EthTxFrame)

                        
    def __init__(self, transmitCallback, addressManager):
        self.transmit = transmitCallback
        self.addressManager = addressManager
        self.ownMac = self.addressManager.getLocalMacAddress()
        print("udplog started with ownMac " + prettyMac(self.ownMac))
