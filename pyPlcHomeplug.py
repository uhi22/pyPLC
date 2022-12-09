
# Preconditions:
# Library pcap-ct (not libpcap, not pylibpcap, not pypcap)
#
# Version 2022-08-14:
#  - Selection of interfaces ok
#  - Sniffing of the SLAC-request ok
#  - Transmission of a demo message ok
#
# Test results 2022-10-15
# 1. GET_SW.REQ broadcast is answered by both TPlinks, while the first is connected to eth, the other via PLC at the first.
# 2. Step 1 works also, if we use a different MAC address than the original laptop ethernet MAC.
# 3. CM_SET_KEY addressed to the correct destination works, with the following results:
#     - there were cases, when the TPlink responded "negative", but with a "valid" none (each time it used a new mynonce, and correctly
#       reflected our mynonce.
#     - but also there is "positive" response, also with correct nonces.
#     - also the Devolo reponds positive and with correct nonces.
#     - not yet checked, whether the NMK is really set
# 4. CM_GET_KEY with wrong NID is refused by the devolo. But at least it delivers the NID (e.g. d57c1fe9544e01), and if we use this NID in the next
#     request, it responds with KEY_GRANTED, Keytype=NMK, and a key 7f19ba0261892d59b7ea42aed875d2320000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
#     This key delivers exactly the NMK, which we have set in the CM_SET_KEY.
#     But: There are some pitfalls:
#       The CM_SET_KEY responds in some cases (wrong request) positive, but does not apply the NMK.
#       If the CM_SET_KEY is well-formatted, including the correct NID, we get a false-negative response, and
#       we see the LEDs on the adaptor shortly going completely off, completely on, and back to normal state. This
#       is the sign, that the new key was accepted. It means, the
#       adaptor is making a reset, to apply the new key.
# 5. CM_SET_KEY and CM_GET_KEY works also when sent to broadcast address. For both, devolo and tpLink.
# 2022-10-18 further tests
# 6. The devolo reports the SLAC_PARAM from the standalone-IONIQ to the wirkshark. Even in the case, when the devolo is paired to a tpLink.
# 7. The tpLink does NOT report the SLAC_PARAM to ethernet. Bad.
# 8. The tpLink has software from 2017, maybe the SLAC was removed at this version.
# 9. Article regarding firmware- and configuration update: https://fitzcarraldoblog.wordpress.com/2020/07/22/updating-the-powerline-adapters-in-my-home-network/


import pcap
import pyPlcIpv6
import udplog
import time
from helpers import * # prettyMac etc
from pyPlcModes import *

MAC_BROADCAST = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]

CM_SET_KEY = 0x6008
CM_GET_KEY = 0x600C
CM_SC_JOIN = 0x6010
CM_CHAN_EST = 0x6014
CM_TM_UPDATE = 0x6018
CM_AMP_MAP = 0x601C
CM_BRG_INFO = 0x6020
CM_CONN_NEW = 0x6024
CM_CONN_REL = 0x6028
CM_CONN_MOD = 0x602C
CM_CONN_INFO = 0x6030
CM_STA_CAP = 0x6034
CM_NW_INFO = 0x6038
CM_GET_BEACON = 0x603C
CM_HFID = 0x6040
CM_MME_ERROR = 0x6044
CM_NW_STATS = 0x6048
CM_SLAC_PARAM = 0x6064
CM_START_ATTEN_CHAR = 0x6068
CM_ATTEN_CHAR = 0x606C
CM_PKCS_CERT = 0x6070
CM_MNBC_SOUND = 0x6074
CM_VALIDATE = 0x6078
CM_SLAC_MATCH = 0x607C
CM_SLAC_USER_DATA = 0x6080
CM_ATTEN_PROFILE = 0x6084
CM_GET_SW = 0xA000

MMTYPE_REQ = 0x0000
MMTYPE_CNF = 0x0001
MMTYPE_IND = 0x0002
MMTYPE_RSP = 0x0003

STATE_INITIAL = 0
STATE_MODEM_SEARCH_ONGOING = 1
STATE_READY_FOR_SLAC       = 2
STATE_WAITING_FOR_MODEM_RESTARTED = 3
STATE_WAITING_FOR_SLAC_PARAM_CNF  = 4
STATE_SLAC_PARAM_CNF_RECEIVED     = 5
STATE_BEFORE_START_ATTEN_CHAR     = 6
STATE_SOUNDING                    = 7
STATE_WAIT_FOR_ATTEN_CHAR_IND     = 8
STATE_ATTEN_CHAR_IND_RECEIVED     = 9
STATE_DELAY_BEFORE_MATCH          = 10
STATE_WAITING_FOR_SLAC_MATCH_CNF  = 11
STATE_WAITING_FOR_RESTART2        = 12
STATE_FIND_MODEMS2                = 13
STATE_WAITING_FOR_SW_VERSIONS     = 14
STATE_READY_FOR_SDP               = 15
STATE_SDP                         = 16

 
class pyPlcHomeplug():    
    def showIpAddresses(self, mybytearray):
        addr = lambda pkt, offset: '.'.join(str(pkt[i]) for i in range(offset, offset + 4))
        print('SRC %-16s\tDST %-16s' % (addr(mybytearray, self.sniffer.dloff + 12), addr(mybytearray, self.sniffer.dloff + 16)))

    def showMacAddresses(self, mybytearray):
        strDestMac = ""
        for i in range(0, 6):
            strDestMac = strDestMac + twoCharHex(mybytearray[i]) + ":"
        strSourceMac = ""
        for i in range(5, 12):
            strSourceMac = strSourceMac + twoCharHex(mybytearray[i]) + ":"
        lastThreeOfSource = mybytearray[6]*256*256 + mybytearray[7]*256 + mybytearray[8]
        strSourceFriendlyName = ""
        if (lastThreeOfSource == 0x0a663a):
            strSourceFriendlyName="Fritzbox"
        if (lastThreeOfSource == 0x0064c3):
            strSourceFriendlyName="Ioniq"
            
        print("From " + strSourceMac + strSourceFriendlyName + " to " + strDestMac)

    def getEtherType(self, messagebufferbytearray):
        etherType=0
        if len(messagebufferbytearray)>(6+6+2):
            etherType=messagebufferbytearray[12]*256 + messagebufferbytearray[13]
        return etherType
        
        
    def fillSourceMac(self, mac, offset=6): # at offset 6 in the ethernet frame, we have the source MAC
        # we can give a different offset, to re-use the MAC also in the data area
        for i in range(0, 6):
            self.mytransmitbuffer[offset+i]=mac[i]
        
    def fillDestinationMac(self, mac, offset=0): # at offset 0 in the ethernet frame, we have the destination MAC
         # we can give a different offset, to re-use the MAC also in the data area
        for i in range(0, 6):
            self.mytransmitbuffer[offset+i]=mac[i]
        
    def cleanTransmitBuffer(self): # fill the complete ethernet transmit buffer with 0x00
        for i in range(0, len(self.mytransmitbuffer)):
            self.mytransmitbuffer[i]=0

    def setNmkAt(self, index):
        # sets the Network Membership Key (NMK) at a certain position in the transmit buffer
        for i in range(0, 16):
            self.mytransmitbuffer[index+i]=self.NMK[i] # NMK

    def setNidAt(self, index):
        # (b0f2e695666b03 was NID of TPlink)
        # copies the network ID (NID, 7 bytes) into the wished position in the transmit buffer
        for i in range(0, 7):
            self.mytransmitbuffer[index+i]=self.NID[i]
        
    def getManagementMessageType(self):
        # calculates the MMTYPE (base value + lower two bits), see Table 11-2 of homeplug spec
        return (self.myreceivebuffer[16]<<8) + self.myreceivebuffer[15]

    def composeGetSwReq(self):
		# GET_SW.REQ request, as used by the win10 laptop
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x00 # version
        self.mytransmitbuffer[15]=0x00 # GET_SW.REQ
        self.mytransmitbuffer[16]=0xA0 # 
        self.mytransmitbuffer[17]=0x00 # Vendor OUI
        self.mytransmitbuffer[18]=0xB0 # 
        self.mytransmitbuffer[19]=0x52 # 

    def composeGetSwWithRamdomMac(self):
		# GET_SW.REQ request, as used by the win10 laptop
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # patch the lower three bytes of the MAC with a random value
        self.mytransmitbuffer[8] = self.randomMac & 0xff
        self.mytransmitbuffer[9] = (self.randomMac>>16) & 0xff
        self.mytransmitbuffer[10] = (self.randomMac>>8) & 0xff
        self.mytransmitbuffer[11] = self.randomMac & 0xff
        if (1):
            if ((self.randomMac%16)==0):
                self.fillSourceMac([0xb8, 0x27, 0xeb, 0xa3, 0xaf, 0x34 ])
            if ((self.randomMac%16)==1):
                self.fillSourceMac([0xb8, 0x27, 0xeb, 0x72, 0x66, 0x06 ])
        self.randomMac += 1 # new MAC for the next round
        
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x00 # version
        self.mytransmitbuffer[15]=0x00 # GET_SW.REQ
        self.mytransmitbuffer[16]=0xA0 # 
        self.mytransmitbuffer[17]=0x00 # Vendor OUI
        self.mytransmitbuffer[18]=0xB0 # 
        self.mytransmitbuffer[19]=0x52 # 
        

    def composeSetKey(self, variation=0):
		# CM_SET_KEY.REQ request
        # From example trace from catphish https://openinverter.org/forum/viewtopic.php?p=40558&sid=9c23d8c3842e95c4cf42173996803241#p40558
        # Table 11-88 in the homeplug_av21_specification_final_public.pdf
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        #self.fillDestinationMac(MAC_DEVOLO_26)
        #self.fillDestinationMac(MAC_TPLINK_E4)
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x08 # CM_SET_KEY.REQ
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # frag_index
        self.mytransmitbuffer[18]=0x00 # frag_seqnum
        self.mytransmitbuffer[19]=0x01 # 0 key info type

        self.mytransmitbuffer[20]=0xaa # 1 my nonce
        self.mytransmitbuffer[21]=0xaa # 2
        self.mytransmitbuffer[22]=0xaa # 3
        self.mytransmitbuffer[23]=0xaa # 4

        self.mytransmitbuffer[24]=0x00 # 5 your nonce
        self.mytransmitbuffer[25]=0x00 # 6
        self.mytransmitbuffer[26]=0x00 # 7
        self.mytransmitbuffer[27]=0x00 # 8
        
        self.mytransmitbuffer[28]=0x04 # 9 nw info pid
        
        self.mytransmitbuffer[29]=0x00 # 10 info prn
        self.mytransmitbuffer[30]=0x00 # 11
        self.mytransmitbuffer[31]=0x00 # 12 pmn
        self.mytransmitbuffer[32]=0x00 # 13 cco cap
        self.setNidAt(33) # 14-20 nid  7 bytes from 33 to 39
                            # Network ID to be associated with the key distributed herein.
                            # The 54 LSBs of this field contain the NID (refer to Section 3.4.3.1). The
                            # two MSBs shall be set to 0b00.
        self.mytransmitbuffer[40]=0x01 # 21 peks (payload encryption key select) Table 11-83. 01 is NMK. We had 02 here, why???
                                       # with 0x0F we could choose "no key, payload is sent in the clear"
        self.setNmkAt(41) 
        self.mytransmitbuffer[41]+=variation # to try different NMKs
        # and three remaining zeros

    def composeGetKey(self):
		# CM_GET_KEY.REQ request
        # from https://github.com/uhi22/plctool2/blob/master/listen_to_eth.c
        # and homeplug_av21_specification_final_public.pdf
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        #self.fillDestinationMac(MAC_DEVOLO_26)
        #self.fillDestinationMac(MAC_TPLINK_E4)
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x0C # CM_GET_KEY.REQ https://github.com/uhi22/plctool2/blob/master/plc_homeplug.h
        self.mytransmitbuffer[16]=0x60 #
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 #
        
        self.mytransmitbuffer[19]=0x00 # 0 Request Type 0=direct
        self.mytransmitbuffer[20]=0x01 # 1 RequestedKeyType only "NMK" is permitted over the H1 interface.
                                       #    value see HomeplugAV2.1 spec table 11-89. 1 means AES-128.
                                       
        self.setNidAt(21)# NID starts here (table 11-91 Homeplug spec is wrong. Verified by accepted command.)
        self.mytransmitbuffer[28]=0xaa # 10-13 mynonce. The position at 28 is verified by the response of the devolo.
        self.mytransmitbuffer[29]=0xaa # 
        self.mytransmitbuffer[30]=0xaa # 
        self.mytransmitbuffer[31]=0xaa # 
        self.mytransmitbuffer[32]=0x04 # 14 PID. According to  ISO15118-3 fix value 4, "HLE protocol"
        self.mytransmitbuffer[33]=0x00 # 15-16 PRN Protocol run number
        self.mytransmitbuffer[34]=0x00 # 
        self.mytransmitbuffer[35]=0x00 # 17 PMN Protocol message number

    def composeSlacParamReq(self):
		# SLAC_PARAM request, as it was recorded 2021-12-17 WP charger 2
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.pevMac)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x64 # SLAC_PARAM.REQ
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # 
        self.mytransmitbuffer[20]=0x00 #
        self.fillSourceMac(self.pevMac, 21) # 21 to 28: 8 bytes runid. The Ioniq uses the PEV mac plus 00 00.
        self.mytransmitbuffer[27]=0x00 # 
        self.mytransmitbuffer[28]=0x00 # 
        # rest is 00
        
    def composeSlacParamCnf(self):
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(self.pevMac)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x65 # SLAC_PARAM.confirm
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0xff # 19-24 sound target
        self.mytransmitbuffer[20]=0xff # 
        self.mytransmitbuffer[21]=0xff # 
        self.mytransmitbuffer[22]=0xff # 
        self.mytransmitbuffer[23]=0xff # 
        self.mytransmitbuffer[24]=0xff # 
        self.mytransmitbuffer[25]=0x0A # sound count
        self.mytransmitbuffer[26]=0x06 # timeout
        self.mytransmitbuffer[27]=0x01 # resptype
        self.fillDestinationMac(self.pevMac, 28)  # forwarding_sta, same as PEV MAC, plus 2 bytes 00 00
        self.mytransmitbuffer[34]=0x00 # 
        self.mytransmitbuffer[35]=0x00 # 
        self.fillDestinationMac(self.pevMac, 36)  # runid, same as PEV MAC, plus 2 bytes 00 00 
        self.mytransmitbuffer[42]=0x0 # 
        self.mytransmitbuffer[43]=0x0 #
        # rest is 00
    
    def composeStartAttenCharInd(self):
        # reference: see wireshark interpreted frame from ioniq
        self.mytransmitbuffer = bytearray(60)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x6A # START_ATTEN_CHAR.IND
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # sectype
        self.mytransmitbuffer[21]=0x0a # number of sounds: 10
        self.mytransmitbuffer[22]=6 # timeout N*100ms. Normally 6, means in 600ms all sounds must have been tranmitted.
                                       # Todo: As long we are a little bit slow, lets give 1000ms instead of 600, so that the
                                       # charger is able to catch it all.
        self.mytransmitbuffer[23]=0x01 # response type 
        self.fillSourceMac(self.myMAC, 24) # 24 to 29: sound_forwarding_sta, MAC of the PEV
        self.fillSourceMac(self.myMAC, 30) # 30 to 37: runid, filled with MAC of PEV and two bytes 00 00
        # rest is 00

    def composeNmbcSoundInd(self):
        # reference: see wireshark interpreted frame from Ioniq
        self.mytransmitbuffer = bytearray(71)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(MAC_BROADCAST)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x76 # NMBC_SOUND.IND
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # sectype
        self.mytransmitbuffer[21]=0x00 # 21 to 37 sender ID, all 00
        self.mytransmitbuffer[38]=self.remainingNumberOfSounds # countdown. Remaining number of sounds. Starts with 9 and counts down to 0.
        self.fillSourceMac(self.myMAC, 39) # 39 to 46: runid, filled with MAC of PEV and two bytes 00 00
        self.mytransmitbuffer[47]=0x00 # 47 to 54: reserved, all 00
        # 55 to 70: random number. All 0xff in the ioniq message.
        for i in range(55, 71):
            self.mytransmitbuffer[i]=0xFF
        
    def composeAttenCharInd(self):
        self.mytransmitbuffer = bytearray(129)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(self.pevMac)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x6E # ATTEN_CHAR.IND
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # security
        self.fillDestinationMac(self.pevMac, 21) # The wireshark calls it source_mac, but alpitronic fills it with PEV mac. We use the PEV MAC.
        self.fillDestinationMac(self.pevMac, 27) # runid. The alpitronic fills it with the PEV mac, plus 00 00.
        self.mytransmitbuffer[35]=0x00 # 35 - 51 source_id, 17 bytes. The alpitronic fills it with 00
        
        self.mytransmitbuffer[52]=0x00 # 52 - 68 response_id, 17 bytes. The alpitronic fills it with 00.
        self.mytransmitbuffer[69]=0x0A # Number of sounds. 10 in normal case. Should this be more flexible, e.g. using the counter from first MNBC_SOUND?
        self.mytransmitbuffer[70]=0x3A # Number of groups = 58. Should this be more flexible?
        for i in range(71, 129):  # 71 to 128: The group attenuation for the 58 announced groups.
            self.mytransmitbuffer[i]=9 # Typical values are between 1 and 0x19. Since we have no real measurements from the AR7020,
                                          # we just simulate something. 0 seems to be interpreted as "defect", the IONIQ does not send
                                          # a positive response in this case.
        # higher attenuation for the higher frequencies, to be a little bit realistic (real data from alpitronic trace)
        self.mytransmitbuffer[126]=0x0f
        self.mytransmitbuffer[127]=0x13
        self.mytransmitbuffer[128]=0x19
        
    def composeAttenCharRsp(self):
        # reference: see wireshark interpreted frame from Ioniq
        self.mytransmitbuffer = bytearray(70)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(self.evseMac)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x6F # ATTEN_CHAR.RSP
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # sectype
        self.fillSourceMac(self.myMAC, 21) # 21 to 26: source MAC
        self.fillDestinationMac(self.myMAC, 27) # 27 to 34: runid. The PEV mac, plus 00 00.
        # 35 to 51: source_id, all 00
        # 52 to 68: resp_id, all 00
        # 69: result. 0 is ok
        
    def composeSlacMatchReq(self):
        # reference: see wireshark interpreted frame from Ioniq
        self.mytransmitbuffer = bytearray(85)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(self.evseMac)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x7C # SLAC_MATCH.REQ
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # sectype
        self.mytransmitbuffer[21]=0x3E # 21 to 22: length
        self.mytransmitbuffer[22]=0x00 #
        # 23 to 39: pev_id, all 00
        self.fillSourceMac(self.myMAC, 40) # 40 to 45: PEV MAC
        # 46 to 62: evse_id, all 00
        self.fillDestinationMac(self.evseMac, 63) # 63 to 68: EVSE MAC
        self.fillSourceMac(self.myMAC, 69) # 69 to 76: runid. The PEV mac, plus 00 00.
        # 77 to 84: reserved, all 00        
    
    def composeSlacMatchCnf(self):
        self.mytransmitbuffer = bytearray(109)
        self.cleanTransmitBuffer()
        # Destination MAC
        self.fillDestinationMac(self.pevMac)
        # Source MAC
        self.fillSourceMac(self.myMAC)
        # Protocol
        self.mytransmitbuffer[12]=0x88 # Protocol HomeplugAV
        self.mytransmitbuffer[13]=0xE1
        self.mytransmitbuffer[14]=0x01 # version
        self.mytransmitbuffer[15]=0x7D # SLAC_MATCH.CNF
        self.mytransmitbuffer[16]=0x60 # 
        self.mytransmitbuffer[17]=0x00 # 2 bytes fragmentation information. 0000 means: unfragmented.
        self.mytransmitbuffer[18]=0x00 # 
        self.mytransmitbuffer[19]=0x00 # apptype
        self.mytransmitbuffer[20]=0x00 # security
        self.mytransmitbuffer[21]=0x56 # length 2 byte
        self.mytransmitbuffer[22]=0x00 # 
                                       # 23 - 39: pev_id 17 bytes. All zero in alpi/Ioniq trace.
        self.fillDestinationMac(self.pevMac, 40) # 40 - 45 pev_mac                               
                                       # 46 - 62: evse_id 17 bytes. All zero in alpi/Ioniq trace.
        self.fillSourceMac(self.myMAC, 63) # 63 - 68 evse_mac 
        self.fillDestinationMac(self.pevMac, 69) # 69-76 run_id. Is the ioniq mac plus 00 00.
                                       # 77 to 84 reserved 0
        self.setNidAt(85) # 85-91 NID. We can nearly freely choose this, but the upper two bits need to be zero
                                       # 92 reserved 0                                 
        self.setNmkAt(93) # 93 to 108 NMK. We can freely choose this. Normally we should use a random number. 
        


    def sendTestFrame(self, selection): 
        if (selection=="1"):
            self.composeSlacParamReq()
            self.addToTrace("transmitting SLAC_PARAM.REQ...")
            self.transmit(self.mytransmitbuffer)
        if (selection=="2"):
            self.composeSlacParamCnf()
            self.addToTrace("transmitting SLAC_PARAM.CNF...")            
            self.transmit(self.mytransmitbuffer)
        if (selection=="S"):
            self.composeGetSwReq()
            self.addToTrace("transmitting GetSwReq...")
            self.transmit(self.mytransmitbuffer)
        if (selection=="s"):
            self.composeSetKey(0)
            self.addToTrace("transmitting SET_KEY.REQ (key 0)")
            self.transmit(self.mytransmitbuffer)
        if (selection=="t"):
            self.composeSetKey(2) # set key with modified content
            self.addToTrace("transmitting SET_KEY.REQ (key 2)")
            self.transmit(self.mytransmitbuffer)
        if (selection=="G"):
            self.composeGetKey()
            self.addToTrace("transmitting GET_KEY")           
            self.transmit(self.mytransmitbuffer)
        if (selection=="M"):
            self.composeGetSwWithRamdomMac()
            self.addToTrace("transmitting GetSwWithRamdomMac")           
            self.transmit(self.mytransmitbuffer)
            
    def transmit(self, pkt):
        self.sniffer.sendpacket(bytes(pkt))
      
    def evaluateGetKeyCnf(self):
        self.addToTrace("received GET_KEY.CNF")
        self.numberOfFoundModems += 1
        sourceMac=bytearray(6)
        for i in range(0, 6):
            sourceMac[i] = self.myreceivebuffer[6+i]
        strMac=prettyMac(sourceMac)
        result = self.myreceivebuffer[19] # 0 in case of success
        if (result==0):
            strResult="(OK)"
        else:
            strResult="(NOK)"
        self.addToTrace("Modem #" + str(self.numberOfFoundModems) + " has " + strMac + " and result code is " + str(result) + strResult)        
        if (self.numberOfFoundModems>1):
            self.addToTrace("Info: NOK is normal for remote modems.")
            
        # We observed the following cases:
        # (A) Result=1 (NOK), NID all 00, key all 00: We requested the key with the wrong NID.
        # (B) Result=0 (OK), NID all 00, key non-zero: We used the correct NID for the request.
        #            It is the local TPlink adaptor. A fresh started non-coordinator, like the PEV side.
        # (C) Result=0 (OK), NID non-zero, key non-zero: We used the correct NID for the request.
        #            It is the local TPlink adaptor.
        # (D) Result=1 (NOK), NID non-zero, key all 00: It was a remote device. They are rejecting the GET_KEY.
        if (result==0):
            # The ok case is for sure the local modem. Let's store its data.
            self.localModemMac = sourceMac
            self.localModemCurrentKey=bytearray(16)
            s=""
            for i in range(0, 16): # NMK has 16 bytes
                self.localModemCurrentKey[i] = self.myreceivebuffer[41+i]
                s=s+hex(self.localModemCurrentKey[i])+ " "
            self.addToTrace("The local modem has key " + s)
            if (self.localModemCurrentKey == bytearray(self.NMKdevelopment)):
                self.addToTrace("This is the developer NMK.")
                self.isDeveloperLocalKey = 1
            else:
                self.addToTrace("This is NOT the developer NMK.")            
            self.localModemFound=1 
        s = ""
        # The getkey response contains the Network ID (NID), even if the request was rejected. We store the NID,
        # to have it available for the next request. Use case: A fresh started, unconnected non-Coordinator
        # modem has the default-NID all 00. On the other hand, a fresh started coordinator has the
        # NID which he was configured before. We want to be able to cover both cases. That's why we
        # ask GET_KEY, it will tell the NID (even if response code is 1 (NOK), and we will use this
        # received NID for the next request. This will be ansered positive (for the local modem).
        for i in range(0, 7): # NID has 7 bytes
            self.NID[i] = self.myreceivebuffer[29+i]
            s=s+hex(self.NID[i])+ " "
        print("From GetKeyCnf, got network ID (NID) " + s)
        

    def evaluateSetKeyCnf(self):
        # The Setkey confirmation
        # In spec, the result 0 means "success". But in reality, the 0 means: did not work. When it works,
        # then the LEDs are blinking (device is restarting), and the response is 1.
        self.addToTrace("received SET_KEY.CNF")
        result = self.myreceivebuffer[19]
        if (result == 0):
            self.addToTrace("SetKeyCnf says 0, this would be a bad sign for local modem, but normal for remote.")
        else:
            self.addToTrace("SetKeyCnf says " + str(result) + ", this is formally 'rejected', but indeed ok.")

    def evaluateGetSwCnf(self):
        # The GET_SW confirmation. This contains the software version of the homeplug modem.
        # Reference: see wireshark interpreted frame from TPlink, Ioniq and Alpitronic charger
        self.addToTrace("[SNIFFER] received GET_SW.CNF")
        self.numberOfSoftwareVersionResponses+=1
        sourceMac=bytearray(6)
        for i in range(0, 6):
            sourceMac[i] = self.myreceivebuffer[6+i]
        strMac=prettyMac(sourceMac)
        verLen = self.myreceivebuffer[22]
        strVersion = ""
        if ((verLen>0) and (verLen<0x30)):
            for i in range(0, verLen):
                x = self.myreceivebuffer[23+i]
                if (x<0x20):
                    x=0x20 # make unprintable character to space.
                strVersion+=chr(x) # convert ASCII code to string
        self.addToTrace("[SNIFFER] For " + strMac + " the software version is " + strVersion)
        
    def evaluateSlacParamReq(self):
        # We received a SLAC_PARAM request from the PEV. This is the initiation of a SLAC procedure.
        # We extract the pev MAC from it.
        self.addToTrace("received SLAC_PARAM.REQ")
        for i in range(0, 6):
            self.pevMac[i] = self.myreceivebuffer[6+i]
        self.addressManager.setPevMac(self.pevMac)
        self.showStatus(prettyMac(self.pevMac), "pevmac")
        # If we want to emulate an EVSE, we want to answer.
        if (self.iAmEvse==1):
            self.composeSlacParamCnf()
            self.addToTrace("[EVSE] transmitting CM_SLAC_PARAM.CNF")
            self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
    
    def evaluateSlacParamCnf(self):
        # As PEV, we receive the first response from the charger.
        self.addToTrace("received SLAC_PARAM.CNF")
        if (self.iAmPev==1):
            if (self.pevSequenceState==STATE_WAITING_FOR_SLAC_PARAM_CNF): # we were waiting for the SlacParamCnf
                self.pevSequenceDelayCycles = 4 # original Ioniq is waiting 200ms
                self.enterState(STATE_SLAC_PARAM_CNF_RECEIVED) # enter next state. Will be handled in the cyclic runPevSequencer
            
    def evaluateMnbcSoundInd(self):
        # We received MNBC_SOUND.IND from the PEV. Normally this happens 10times, with a countdown (remaining number of sounds)
        # running from 9 to 0. If the countdown is 0, this is the last message. In case we are the EVSE, we need
        # to answer with a ATTEN_CHAR.IND, which normally contains the attenuation for 10 sounds, 58 groups.
        self.addToTrace("received MNBC_SOUND.IND")
        if (self.iAmEvse==1):
            countdown = self.myreceivebuffer[38]
            if (countdown == 0):
                self.composeAttenCharInd()
                self.addToTrace("[EVSE] transmitting ATTEN_CHAR.IND")
                self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
                
    def evaluateAttenCharInd(self):
        self.addToTrace("received ATTEN_CHAR.IND")    
        if (self.iAmPev==1):
            self.addToTrace("[PEVSLAC] received AttenCharInd in state " + str(self.pevSequenceState))
            if (self.pevSequenceState==STATE_WAIT_FOR_ATTEN_CHAR_IND): # we were waiting for the AttenCharInd
                # todo: Handle the case when we receive multiple responses from different chargers.
                #       Wait a certain time, and compare the attenuation profiles. Decide for the nearest charger.
                # Take the MAC of the charger from the frame, and store it for later use.
                for i in range(0, 6):
                    self.evseMac[i] = self.myreceivebuffer[6+i] # source MAC starts at offset 6
                self.addressManager.setEvseMac(self.evseMac)
                self.AttenCharIndNumberOfSounds = self.myreceivebuffer[69]
                self.addToTrace("[PEVSLAC] number of sounds reported by the EVSE (should be 10): " + str(self.AttenCharIndNumberOfSounds)) 
                self.composeAttenCharRsp()
                self.addToTrace("[PEVSLAC] transmitting ATTEN_CHAR.RSP...")
                self.transmit(self.mytransmitbuffer)                 
                self.pevSequenceState=STATE_ATTEN_CHAR_IND_RECEIVED # enter next state. Will be handled in the cyclic runPevSequencer
            
            
    def evaluateSlacMatchReq(self):
        # We received SLAC_MATCH.REQ from the PEV.
        # If we are EVSE, we send the response.
        self.addToTrace("received SLAC_MATCH.REQ")
        if (self.iAmEvse==1):
            self.composeSlacMatchCnf()
            self.addToTrace("[EVSE] transmitting SLAC_MATCH.CNF")
            self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
        
  
    def evaluateSlacMatchCnf(self):
        # The SLAC_MATCH.CNF contains the NMK and the NID.
        # We extract this information, so that we can use it for the CM_SET_KEY afterwards.
        # References: https://github.com/qca/open-plc-utils/blob/master/slac/evse_cm_slac_match.c
        # 2021-12-16_HPC_säule1_full_slac.pcapng
        if (self.iAmEvse==1):
            # If we are EVSE, nothing to do. We have sent the match.CNF by our own.
            # The SET_KEY was already done at startup.
            pass
        else:
            self.addToTrace("received SLAC_MATCH.CNF")
            s = ""
            for i in range(0, 7): # NID has 7 bytes
                self.NID[i] = self.myreceivebuffer[85+i]
                s=s+hex(self.NID[i])+ " "
            self.addToTrace("From SlacMatchCnf, got network ID (NID) " + s)        
            s = ""
            for i in range(0, 16):
                self.NMK[i] = self.myreceivebuffer[93+i]
                s=s+hex(self.NMK[i])+ " "
            self.addToTrace("From SlacMatchCnf, got network membership key (NMK) " + s) 
            # use the extracted NMK and NID to set the key in the adaptor:
            self.composeSetKey(0)
            self.addToTrace("transmitting CM_SET_KEY.REQ")
            self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
            if (self.pevSequenceState==STATE_WAITING_FOR_SLAC_MATCH_CNF): # we were waiting for finishing the SLAC_MATCH.CNF and SET_KEY.REQ
                self.enterState(STATE_WAITING_FOR_RESTART2)
    
    def evaluateReceivedHomeplugPacket(self):
        mmt = self.getManagementMessageType()
        # print(hex(mmt))
        if (mmt == CM_GET_KEY + MMTYPE_CNF):
            self.evaluateGetKeyCnf()
        if (mmt == CM_SLAC_MATCH + MMTYPE_REQ):
            self.evaluateSlacMatchReq()
        if (mmt == CM_SLAC_MATCH + MMTYPE_CNF):
            self.evaluateSlacMatchCnf()
        if (mmt == CM_SLAC_PARAM + MMTYPE_REQ):
            self.evaluateSlacParamReq()
        if (mmt == CM_SLAC_PARAM + MMTYPE_CNF):
            self.evaluateSlacParamCnf()
        if (mmt == CM_MNBC_SOUND + MMTYPE_IND):
            self.evaluateMnbcSoundInd()
        if (mmt == CM_ATTEN_CHAR + MMTYPE_IND):
            self.evaluateAttenCharInd()
        if (mmt == CM_SET_KEY + MMTYPE_CNF):
            self.evaluateSetKeyCnf()
        if (mmt == CM_GET_SW + MMTYPE_CNF):
            self.evaluateGetSwCnf()

    def isEvseModemFound(self):
        #return 0 # todo: look whether the MAC of the EVSE modem is in the list of detected modems
        return self.numberOfFoundModems>1
        
    def enterState(self, n):
        print("[PEVSLAC] from " + str(self.pevSequenceState) + " entering " + str(n))
        self.pevSequenceState = n
        self.pevSequenceCyclesInState = 0
        
    def isTooLong(self):
        # The timeout handling function.
        return (self.pevSequenceCyclesInState > 500)

    def runPevSequencer(self):
        # in PevMode, check whether homeplug modem is connected, run the SLAC and SDP
        self.pevSequenceCyclesInState+=1
        if (self.pevSequenceState==STATE_INITIAL): # Initial state.
            # In real life we would check whether we see 5% PWM on the pilot line. We skip this check.
            self.isSimulationMode = self.isForcedSimulationMode # from command line, we can force the simulation mode
            self.isSDPDone = 0
            self.numberOfFoundModems = 0
            self.localModemFound = 0
            self.isDeveloperLocalKey = 0
            self.nEvseModemMissingCounter = 0
            # First action: find the connected homeplug modems, by sending a GET_KEY
            self.composeGetKey()
            self.addToTrace("[PEVSLAC] searching for modems, transmitting GET_KEY.REQ...")
            self.transmit(self.mytransmitbuffer)                
            self.enterState(STATE_MODEM_SEARCH_ONGOING)
            return
        if (self.pevSequenceState==STATE_MODEM_SEARCH_ONGOING): # Waiting for the modems to answer.
            if (self.pevSequenceCyclesInState>=10):
                # It was sufficient time to get the answers from the modems.
                self.addToTrace("[PEVSLAC] It was sufficient time to get the answers from the modems.")
                # Let's see what we received.
                if (self.numberOfFoundModems==0):
                    self.addToTrace("[PEVSLAC] No modem connected. We assume, we run in a simulation environment.")
                    self.isSimulationMode = 1
                    self.enterState(STATE_READY_FOR_SLAC)
                    return
                else:
                    if (self.localModemFound):
                        # we have at least a local modem. Maybe more remote.
                        # We want to make sure, that the local modem is set to the "default key", so that
                        # it is possible to connect to the PLC network for development purposes.
                        # That's why we check the key, and if it is not the intended, we set the default.
                        if (self.isDeveloperLocalKey):
                            self.enterState(STATE_READY_FOR_SLAC)
                            return
                        else:
                            self.composeSetKey() # set the default ("developer") key
                            self.addToTrace("[PEVSLAC] setting the default developer key...")
                            self.transmit(self.mytransmitbuffer)        
                            self.enterState(STATE_WAITING_FOR_MODEM_RESTARTED)
                            return
                    else:
                        # we found modems, but non of it could be identified as the local modem. This happens
                        # when we do not use the matching NID for the request. We try again, because in the
                        # first response we got a better NID in the meanwhile.
                        self.addToTrace("[PEVSLAC] local modem not yet identified.")
                        self.numberOfFoundModems = 0
                        # find the connected homeplug modems, by sending a GET_KEY
                        self.composeGetKey()
                        self.addToTrace("[PEVSLAC] searching for modems, transmitting GET_KEY.REQ...")
                        self.transmit(self.mytransmitbuffer)                
                        self.enterState(STATE_MODEM_SEARCH_ONGOING)
                        return
                        
            return            
        if (self.pevSequenceState==STATE_WAITING_FOR_MODEM_RESTARTED): # Waiting for the modem to restart after SetKey.
            if (self.pevSequenceCyclesInState>=100):
                self.addToTrace("[PEVSLAC] Assuming the modem is up again.")
                self.enterState(STATE_READY_FOR_SLAC)
            return
        if (self.pevSequenceState==STATE_READY_FOR_SLAC):
            self.addToTrace("[PEVSLAC] Sending SLAC_PARAM.REQ...")
            self.composeSlacParamReq()
            self.transmit(self.mytransmitbuffer)                
            self.enterState(STATE_WAITING_FOR_SLAC_PARAM_CNF)
            return
        if (self.pevSequenceState==STATE_WAITING_FOR_SLAC_PARAM_CNF): # Waiting for slac_param confirmation.
            if (self.pevSequenceCyclesInState>=30):
                # No response for 1s, this is an error.
                self.addToTrace("[PEVSLAC] Timeout while waiting for SLAC_PARAM.CNF")
                self.enterState(STATE_INITIAL)
            # (the normal state transition is done in the reception handler)
            return
        if (self.pevSequenceState==STATE_SLAC_PARAM_CNF_RECEIVED): # slac_param confirmation was received.
            self.pevSequenceDelayCycles = 1 # 1*30=30ms as preparation for the next state.
                                            # Between the SLAC_PARAM.CNF and the first START_ATTEN_CHAR.IND the Ioniq waits 100ms.
                                            # The allowed time TP_match_sequence is 0 to 100ms.
                                            # Alpitronic and ABB chargers are more tolerant, they worked with a delay of approx
                                            # 250ms. In contrast, Supercharger and Compleo do not respond anymore if we
                                            # wait so long.
            self.nRemainingStartAttenChar = 3 # There shall be 3 START_ATTEN_CHAR messages.
            self.enterState(STATE_BEFORE_START_ATTEN_CHAR)
            return
        if (self.pevSequenceState==STATE_BEFORE_START_ATTEN_CHAR): # received SLAC_PARAM.CNF. Multiple transmissions of START_ATTEN_CHAR.                
            if (self.pevSequenceDelayCycles>0):
                self.pevSequenceDelayCycles-=1
                return
            # The delay time is over. Let's transmit.
            if (self.nRemainingStartAttenChar>0):
                self.nRemainingStartAttenChar-=1
                self.composeStartAttenCharInd()
                self.addToTrace("[PEVSLAC] transmitting START_ATTEN_CHAR.IND...")
                self.transmit(self.mytransmitbuffer)        
                self.pevSequenceDelayCycles = 0 # original from ioniq is 20ms between the START_ATTEN_CHAR. Shall be 20ms to 50ms. So we set to 0 and the normal 30ms call cycle is perfect.
                return
            else:
                # all three START_ATTEN_CHAR.IND are finished. Now we send 10 MNBC_SOUND.IND
                self.pevSequenceDelayCycles = 0 # original from ioniq is 40ms after the last START_ATTEN_CHAR.IND.
                                                # Shall be 20ms to 50ms. So we set to 0 and the normal 30ms call cycle is perfect.
                self.remainingNumberOfSounds = 10 # We shall transmit 10 sound messages.
                self.enterState(STATE_SOUNDING)
            return
        if (self.pevSequenceState==STATE_SOUNDING): # Multiple transmissions of MNBC_SOUND.IND.                
            if (self.pevSequenceDelayCycles>0):
                self.pevSequenceDelayCycles-=1
                return
            if (self.remainingNumberOfSounds>0):
                self.remainingNumberOfSounds-=1
                self.composeNmbcSoundInd()
                self.addToTrace("[PEVSLAC] transmitting MNBC_SOUND.IND...") # original from ioniq is 40ms after the last START_ATTEN_CHAR.IND
                self.transmit(self.mytransmitbuffer)
                if (self.remainingNumberOfSounds==0):
                    self.enterState(STATE_WAIT_FOR_ATTEN_CHAR_IND) # move fast to the next state, so that a fast response is catched in the correct state
                self.pevSequenceDelayCycles = 0 # original from ioniq is 20ms between the messages.
                                                # Shall be 20ms to 50ms. So we set to 0 and the normal 30ms call cycle is perfect.
            return
        if (self.pevSequenceState==STATE_WAIT_FOR_ATTEN_CHAR_IND):  # waiting for ATTEN_CHAR.IND
            # todo: it is possible that we receive this message from multiple chargers. We need
            # to select the charger with the loudest reported signals.
            if (self.isTooLong()):
                self.enterState(STATE_INITIAL)
            return
            #(the normal state transition is done in the reception handler)
        if (self.pevSequenceState==STATE_ATTEN_CHAR_IND_RECEIVED):  # ATTEN_CHAR.IND was received and the
                                                                    # nearest charger decided and the 
                                                                    # ATTEN_CHAR.RSP was sent.
            self.enterState(STATE_DELAY_BEFORE_MATCH)
            self.pevSequenceDelayCycles = 30 # original from ioniq is 860ms to 980ms from ATTEN_CHAR.RSP to SLAC_MATCH.REQ
            return
        if (self.pevSequenceState==STATE_DELAY_BEFORE_MATCH): # Waiting time before SLAC_MATCH.REQ
            if (self.pevSequenceDelayCycles>0):
                self.pevSequenceDelayCycles-=1
                return
            self.composeSlacMatchReq()
            self.addToTrace("[PEVSLAC] transmitting SLAC_MATCH.REQ...")
            self.transmit(self.mytransmitbuffer)  
            self.enterState(STATE_WAITING_FOR_SLAC_MATCH_CNF)
            return
        if (self.pevSequenceState==STATE_WAITING_FOR_SLAC_MATCH_CNF):  # waiting for SLAC_MATCH.CNF
            if (self.isTooLong()):
                self.enterState(STATE_INITIAL)
                return
            self.pevSequenceDelayCycles = 100 # 3s reset wait time (may be a little bit too short, need a retry)
            # (the normal state transition is done in the receive handler of SLAC_MATCH.CNF,
            # including the transmission of SET_KEY.REQ)
            return
        if (self.pevSequenceState==STATE_WAITING_FOR_RESTART2):  # SLAC is finished, SET_KEY.REQ was 
                                                                 # transmitted. The homeplug modem makes
                                                                 # the reset and we need to wait until it
                                                                 # is up with the new key.
            if (self.pevSequenceDelayCycles>0):
                self.pevSequenceDelayCycles-=1
                return
            self.addToTrace("[PEVSLAC] Checking whether the pairing worked, by GET_KEY.REQ...")
            self.numberOfFoundModems = 0 # reset the number, we want to count the modems newly.
            self.composeGetKey()
            self.transmit(self.mytransmitbuffer)                
            self.enterState(STATE_FIND_MODEMS2)
            return
        if (self.pevSequenceState==STATE_FIND_MODEMS2): # Waiting for the modems to answer.
            if (self.pevSequenceCyclesInState>=10):
                # It was sufficient time to get the answers from the modems.
                self.addToTrace("[PEVSLAC] It was sufficient time to get the answers from the modems.")
                # Let's see what we received.
                if ((not self.isEvseModemFound()) and (not self.isSimulationMode)):
                    self.nEvseModemMissingCounter+=1
                    self.addToTrace("[PEVSLAC] No EVSE seen (yet). Still waiting for it.")
                    # At the Alpitronic we measured, that it takes 7s between the SlacMatchResponse and
                    # the chargers modem reacts to GetKeyRequest. So we should wait here at least 10s.
                    if (self.nEvseModemMissingCounter>10):
                        if (self.isSimulationMode):
                            self.addToTrace("[PEVSLAC] No EVSE modem. But this is fine, we are in SimulationMode.")
                        else:
                            # We lost the connection to the EVSE modem. Back to the beginning.
                            self.addToTrace("[PEVSLAC] We lost the connection to the EVSE modem. Back to the beginning.")
                            self.enterState(STATE_INITIAL)
                            return
                    # The EVSE modem is (shortly) not seen. Ask again.
                    self.pevSequenceDelayCycles=30
                    self.enterState(STATE_WAITING_FOR_RESTART2)
                    return
                # The EVSE modem is present (or we are simulating)
                self.addToTrace("[PEVSLAC] EVSE is up, pairing successful.")
                if (self.isSimulationMode):
                    self.addToTrace("[PEVSLAC] But this is only simulated.")
                self.nEvseModemMissingCounter=0
                self.pevSequenceDelayCycles=0
                self.composeGetSwReq()
                self.addToTrace("[PEVSLAC] Requesting SW versions from the modems...")
                self.transmit(self.mytransmitbuffer)
                self.enterState(STATE_WAITING_FOR_SW_VERSIONS)
            return
        if (self.pevSequenceState==STATE_WAITING_FOR_SW_VERSIONS):
            if (self.pevSequenceCyclesInState>=2): # 2 cycles = 60ms are more than sufficient.
                # Measured: The local modem answers in less than 1ms. The remote modem in ~5ms.
                # It was sufficient time to get the answers from the modems.
                self.addToTrace("[PEVSLAC] It was sufficient time to get the SW versions from the modems.")
                self.enterState(STATE_READY_FOR_SDP)
            return
        if (self.pevSequenceState==STATE_READY_FOR_SDP):
            # The AVLN is established, we have at least two modems in the network.
            # If we did not SDP up to now, let's do it.
            if (self.isSDPDone):
                # SDP is already done. No need to do it again. We are finished for the normal case.
                # But we want to check whether the connection is still alive, so we start the
                # modem-search from time to time.
                self.pevSequenceDelayCycles = 300 # e.g. 10s
                self.enterState(STATE_WAITING_FOR_RESTART2)
                return
            # SDP was not done yet. Now we start it.
            self.addToTrace("[PEVSLAC] SDP was not done yet. Now we start it.")
            # Next step is to discover the chargers communication controller (SECC) using discovery protocol (SDP).
            self.pevSequenceDelayCycles=0
            self.SdpRepetitionCounter = 50 # prepare the number of retries for the SDP. The more the better.
            self.enterState(STATE_SDP)
            return
                
        if (self.pevSequenceState==STATE_SDP):  # SDP request transmission and waiting for SDP response.
            if (len(self.addressManager.getSeccIp())>0):
                # we received an SDP response, and can start the high-level communication
                print("[PEVSLAC] Now we know the chargers IP.")
                self.isSDPDone = 1
                self.callbackReadyForTcp(1)
                # Continue with checking the connection, for the case somebody pulls the plug.
                self.pevSequenceDelayCycles = 300 # e.g. 10s
                self.enterState(STATE_WAITING_FOR_RESTART2)
                return
            if (self.pevSequenceDelayCycles>0):
                # just waiting until next action
                self.pevSequenceDelayCycles-=1
                return
            if (self.SdpRepetitionCounter>0):
                # Reference: The Ioniq waits 4.1s from the slac_match.cnf to the SDP request.
                # Here we send the SdpRequest. Maybe too early, but we will retry if there is no response.
                self.ipv6.initiateSdpRequest()
                self.SdpRepetitionCounter-=1
                self.pevSequenceDelayCycles = 15 # e.g. half-a-second delay until re-try of the SDP
                self.enterState(STATE_SDP) # stick in the same state
                return
            # All repetitions are over, no SDP response was seen. Back to the beginning.    
            print("[PEVSLAC] ERROR: Did not receive SDP response. Starting from the beginning.")
            self.enterState(STATE_INITIAL)
            return
        # invalid state is reached. As robustness measure, go to initial state.
        self.enterState(STATE_INITIAL)

        
    def findEthernetAdaptor(self):
        self.strInterfaceName="eth0" # default, if the real is not found
        #print("Interfaces:\n" + '\n'.join(pcap.findalldevs()))
        for i in range(0, 10):
            strInterfaceName = pcap.ex_name("eth"+str(i))
            if (strInterfaceName == '\\Device\\NPF_{E4B8176C-8516-4D48-88BC-85225ABCF259}'):
                #print("This is the wanted Ethernet adaptor.")
                self.strInterfaceName="eth"+str(i)
            #print("eth"+ str(i) + " is " + strInterfaceName)
            
    def enterPevMode(self):
        self.iAmEvse = 0 # not emulating a charging station
        self.iAmPev = 1 # emulating a vehicle
        self.ipv6.enterPevMode()
        self.showStatus("PEV mode", "mode")
    def enterEvseMode(self):
        self.iAmEvse = 1 # emulating a charging station
        self.iAmPev = 0 # not emulating a vehicle
        self.ipv6.enterEvseMode()
        self.showStatus("EVSE mode", "mode")
    def enterListenMode(self):
        self.iAmEvse = 0 # not emulating a charging station
        self.iAmPev = 0 # not emulating a vehicle
        self.ipv6.enterListenMode()
        self.showStatus("LISTEN mode", "mode")

    def printToUdp(self, s):
        self.udplog.log(s)

    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None, mode=C_LISTEN_MODE, addrMan=None, callbackReadyForTcp=None, isSimulationMode=0):
        self.mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
        self.nPacketsReceived = 0
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.callbackReadyForTcp = callbackReadyForTcp
        self.addressManager = addrMan
        self.randomMac = 0
        self.pevSequenceState = 0
        self.pevSequenceCyclesInState = 0
        self.numberOfSoftwareVersionResponses = 0
        self.numberOfFoundModems = 0
        self.isForcedSimulationMode = isSimulationMode # simulation without homeplug modem
        #self.sniffer = pcap.pcap(name=None, promisc=True, immediate=True, timeout_ms=50)
        # eth3 means: Third entry from back, in the list of interfaces, which is provided by pcap.findalldevs.
        #  Improvement necessary: select the interface based on the name.
        # For debugging of the interface names, we can patch the file
        # C:\Users\uwemi\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\site-packages\pcap\_pcap_ex.py,
        # in the function
        #    def name(name: bytes) -> bytes:
        # in the place after
        # if i == idx:
        #           print("index match at " + str(i) + " dev name=" + str(dev.name) + " dev.description=" + str(dev.description))
        # This will print the description of the used interface.
        #
        # Patch for non-blocking read-iteration:
        #   in _pcap.py, function def __next__(self), in the case of timeout (if n==0), we need to "raise StopIteration" instead of "continue".
        #
        self.findEthernetAdaptor()
        self.sniffer = pcap.pcap(name=self.strInterfaceName, promisc=True, immediate=True, timeout_ms=50)
        self.sniffer.setnonblock(True)
        self.NMKdevelopment = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ] # a default network key        
        self.NMK = self.NMKdevelopment # a default network key
        self.NID = [ 1, 2, 3, 4, 5, 6, 7 ] # a default network ID
        self.pevMac = [0xDC, 0x0E, 0xA1, 0x11, 0x67, 0x08 ] # a default pev MAC. Will be overwritten later.
        self.evseMac = [0x55, 0x56, 0x57, 0xAA, 0xAA, 0xAA ] # a default evse MAC. Will be overwritten later.
        self.myMAC = self.addressManager.getLocalMacAddress()
        self.runningCounter=0
        self.ipv6 = pyPlcIpv6.ipv6handler(self.transmit, self.addressManager)
        self.ipv6.ownMac = self.myMAC
        self.udplog = udplog.udplog(self.transmit, self.addressManager)
        for k in range(0, 10):
            self.udplog.log("Test message number " + str(k))
            time.sleep(0.1)
        if (mode == C_LISTEN_MODE):
            self.enterListenMode()
        if (mode == C_EVSE_MODE):
            self.enterEvseMode()
        if (mode == C_PEV_MODE):
            self.enterPevMode()
            self.pevMac = self.myMAC
        self.showStatus(prettyMac(self.pevMac), "pevmac")
        print("sniffer created at " + self.strInterfaceName)

    def addToTrace(self, s):
        self.callbackAddToTrace(s)

    def showStatus(self, s, selection=""):
        self.callbackShowStatus(s, selection) 

    def receiveCallback(self, timestamp, pkt, *args):
        self.nPacketsReceived+=1
        # print('%d' % (ts)) # the time stamp
        # We received an ethernet package. Determine its type, and dispatch it to the related handler.
        etherType = self.getEtherType(pkt)
        if (etherType == 0x88E1): # it is a HomePlug message
            self.myreceivebuffer = pkt
            self.evaluateReceivedHomeplugPacket()
        if (etherType == 0x86dd): # it is an IPv6 frame
            self.ipv6.evaluateReceivedPacket(pkt)

    def mainfunction(self):  
        # https://stackoverflow.com/questions/31305712/how-do-i-make-libpcap-pcap-loop-non-blocking
        # Tell the sniffer to give max 100 received packets to the callback function:
        self.sniffer.dispatch(100, self.receiveCallback, None)                
        self.showStatus("nPacketsReceived=" + str(self.nPacketsReceived))
        if (self.iAmPev==1):
            self.runPevSequencer() # run the message sequencer for the PEV side
        
    def close(self):
        self.sniffer.close()

