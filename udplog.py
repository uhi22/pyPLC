
# This module "prints" log messages to UDP broadcasts to port 514.

from helpers import prettyMac
from configmodule import getConfigValue, getConfigValueBool

class udplog():
    def fillMac(self, macbytearray, position=6): # position 6 is the source MAC
        for i in range(0, 6):
            self.EthTxFrame[6+i] = macbytearray[i]
            
                          
    def log(self, s, purpose=""):
        # return # activate this line to disable the logging completely
        #
        # The frame format follows the Syslog protocol, https://en.wikipedia.org/wiki/Syslog
        # Level consists of
        #  Facility = 1 = "user"
        #  Severity = 7 = "debug"
        # print("[UDPLOG] Logging " + s)
        if (purpose==""):
            if (not self.isUpdSyslogEnabled):
                # If no special purpose, and the logging is disabled, we stop here.
                return
        # Logging is not suppressed, so continue to construct the message:
        strLevel="<15>"
        # The String to be logged. Terminated by 00.
        if (len(s)>700):
            s = s[0:700] # Limit the length. Too long messages crash the transmit. Todo: Find out the real limit.
        strMessage=s+"\0"
      
        lenPayLoad = 4 + len(strMessage) # length of level is 4
        
        buffer=bytearray(lenPayLoad+28) # prepare the IPv4 buffer. Including 28 bytes IP header.
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
        buffer[14] = self.ownMac[4] # quick&dirty: we just fill the last two bytes of the MAC here.
        buffer[15] = self.ownMac[5] #
        # destination ip 4 bytes: broadcast
        buffer[16] = 0xff
        buffer[17] = 0xff
        buffer[18] = 0xff
        buffer[19] = 0xff
        # source port
        buffer[20] = 0xff
        buffer[21] = 0x95
        # destination port. 0x0202 = 514 = the official Syslog UDP port
        buffer[22] = 0x02
        buffer[23] = 0x02
        udplen = lenPayLoad + 8 # payload plus 8 byte udp header
        buffer[24] = udplen >> 8
        buffer[25] = (udplen & 0xff)
        udpchecksum = 0 # checksum 0 has the special meaning: no checksum. Receiver ignores it.
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
        for i in range(0, len(buffer)): # copy the IPv4 buffer content into the Ethernet buffer
            self.EthTxFrame[14+i] = buffer[i]
        self.transmit(self.EthTxFrame) # and finally transmit the Ethernet frame

                        
    def __init__(self, transmitCallback, addressManager):
        self.transmit = transmitCallback
        self.addressManager = addressManager
        self.ownMac = self.addressManager.getLocalMacAddress()
        print("udplog started with ownMac " + prettyMac(self.ownMac))
        self.isUpdSyslogEnabled = getConfigValueBool("udp_syslog_enable")
        if (self.isUpdSyslogEnabled):
            print("logging to UDP Syslog is enabled")
        else:
            print("logging to UDP Syslog is disabled")

def udplog_init(transmitCallback, addressManager):
    global udplogger
    udplogger = udplog(transmitCallback, addressManager) # create a global logger object
    
def udplog_log(s, purpose=""):
    global udplogger
    udplogger.log(s, purpose)