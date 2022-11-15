
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

MMTYPE_REQ = 0x0000
MMTYPE_CNF = 0x0001
MMTYPE_IND = 0x0002
MMTYPE_RSP = 0x0003


 
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
        self.mytransmitbuffer[21]=0x04 # runid 8 bytes
        self.mytransmitbuffer[22]=0x65 # 
        self.mytransmitbuffer[23]=0x65 # 
        self.mytransmitbuffer[24]=0x00 # 
        self.mytransmitbuffer[25]=0x64 # 
        self.mytransmitbuffer[26]=0xC3 # 
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
        # todo
        print("todo: implement composeStartAttenCharInd")
        pass

    def composeNmbcSoundInd(self):
        # todo
        print("todo: implement composeNmbcSoundInd")
        pass
        
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
        

    def runPevSequencer(self):
        # in PEV mode, initiate the SLAC sequence
        # Todo: Timing between the states, and timeout handling to be implemented
        if (self.iAmPev==1):
            if (self.pevSequenceState==0): # waiting for start condition
                # In real life we would check whether we see 5% PWM on the pilot line.
                # Then we would maybe wait a little bit until the homeplug modems are awake.
                # Now sending the first packet for the SLAC sequence:
                self.composeSlacParamReq()
                self.addToTrace("transmitting SLAC_PARAM.REQ...")
                self.transmit(self.mytransmitbuffer)                
                self.pevSequenceState = 1
                return
            if (self.pevSequenceState==1): # waiting for SLAC_PARAM.CNF
                return
            if (self.pevSequenceState==2): # received SLAC_PARAM.CNF
                # todo: transmit the START_ATTEN_CHAR.IND 3 times
                self.composeStartAttenCharInd()
                self.addToTrace("transmitting START_ATTEN_CHAR.IND...")
                self.transmit(self.mytransmitbuffer)                
                self.pevSequenceState = 3
                return
            if (self.pevSequenceState==3):
                # todo: transmit the START_ATTEN_CHAR.IND 3 times
                self.composeStartAttenCharInd()
                self.addToTrace("transmitting START_ATTEN_CHAR.IND...")
                self.transmit(self.mytransmitbuffer)                
                self.pevSequenceState = 4
                return
            if (self.pevSequenceState==4):
                # todo: transmit the START_ATTEN_CHAR.IND 3 times
                self.composeStartAttenCharInd()
                self.addToTrace("transmitting START_ATTEN_CHAR.IND...")
                self.transmit(self.mytransmitbuffer)                
                self.pevSequenceState = 5
                self.SoundCountDown=10
                return
            if (self.pevSequenceState==5): # START_ATTEN_CHAR.IND are finished. Now we send 10 MNBC_SOUND.IND
                self.composeNmbcSoundInd()
                self.addToTrace("transmitting MNBC_SOUND.IND...")
                self.transmit(self.mytransmitbuffer)  
                if (self.SoundCountDown>0):
                    self.SoundCountDown-=1
                else:
                    self.pevSequenceState = 6
                return
            if (self.pevSequenceState==6):  # waiting for ATTEN_CHAR.IND
                # todo: it is possible that we receive this message from multiple chargers. We need
                # to select the charger with the loudest reported signals.
                return
            if (self.pevSequenceState==7):  # ATTEN_CHAR.IND was received and the nearest charger decided
                self.composeAttenCharRsp()
                self.addToTrace("transmitting ATTEN_CHAR.RSP...")
                self.transmit(self.mytransmitbuffer)  
                self.pevSequenceState = 8
                return
            if (self.pevSequenceState==8):  # ATTEN_CHAR.RSP was transmitted. Next is SLAC_MATCH.REQ
                self.composeSlacMatchReq()
                self.addToTrace("transmitting SLAC_MATCH.REQ...")
                self.transmit(self.mytransmitbuffer)  
                self.pevSequenceState = 9
                return
            if (self.pevSequenceState==9):  # waiting for SLAC_MATCH.CNF
                return
            if (self.pevSequenceState==10):  # SLAC is finished, KEY is set, AVLN is established.
                # todo: inform the higher-level state machine, that now it can start the SDP
                return
                
                

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
            
    def transmit(self, pkt):
        self.sniffer.sendpacket(bytes(pkt))
      
    def evaluateGetKeyCnf(self):
        # The getkey response contains the Network ID (NID), even if the request was rejected. We store the NID,
        # to have it available for the next request.
        s = ""
        for i in range(0, 7): # NID has 7 bytes
            self.NID[i] = self.myreceivebuffer[29+i]
            s=s+hex(self.NID[i])+ " "
        print("From GetKeyCnf, got network ID (NID) " + s)

    def evaluateSetKeyCnf(self):
        # The Setkey confirmation
        # In spec, the result 0 means "success". But in reality, the 0 means: did not work. When it works,
        # then the LEDs are blinking (device is restarting), and the response is 1.
        result = self.myreceivebuffer[19]
        if (result == 0):
            self.addToTrace("SetKeyCnf says 0, this is a bad sign")
        else:
            self.addToTrace("SetKeyCnf says " + str(result) + ", this is formally 'rejected', but indeed ok.")

    def evaluateSlacParamReq(self):
        # We received a SLAC_PARAM request from the PEV. This is the initiation of a SLAC procedure.
        # We extract the pev MAC from it.
        
        for i in range(0, 6):
            self.pevMac[i] = self.myreceivebuffer[6+i]
        self.addressManager.setPevMac(self.pevMac)
        self.showStatus(prettyMac(self.pevMac), "pevmac")
        # If we want to emulate an EVSE, we want to answer.
        if (self.iAmEvse==1):
            self.composeSlacParamCnf()
            self.addToTrace("transmitting CM_SLAC_PARAM.CNF")
            self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
    
    def evaluateSlacParamCnf(self):
        # As PEV, we receive the first response from the charger.
        if (self.iAmPev==1):
            if (self.pevSequenceState==1): # we were waiting for the SlacParamCnf
                self.pevSequenceState=2 # enter next state. Will be handled in the cyclic runPevSequencer
            
    def evaluateMnbcSoundInd(self):
        # We received MNBC_SOUND.IND from the PEV. Normally this happens 10times, with a countdown (remaining number of sounds)
        # running from 9 to 0. If the countdown is 0, this is the last message. In case we are the EVSE, we need
        # to answer with a ATTEN_CHAR.IND, which normally contains the attenuation for 10 sounds, 58 groups.
        if (self.iAmEvse==1):
            countdown = self.myreceivebuffer[38]
            if (countdown == 0):
                self.composeAttenCharInd()
                self.addToTrace("transmitting ATTEN_CHAR.IND")
                self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
            
    def evaluateSlacMatchReq(self):
        # We received SLAC_MATCH.REQ from the PEV.
        # If we are EVSE, we send the response.
        if (self.iAmEvse==1):
            self.composeSlacMatchCnf()
            self.addToTrace("transmitting SLAC_MATCH.CNF")
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
            s = ""
            for i in range(0, 7): # NID has 7 bytes
                self.NID[i] = self.myreceivebuffer[85+i]
                s=s+hex(self.NID[i])+ " "
            print("From SlacMatchCnf, got network ID (NID) " + s)        
            s = ""
            for i in range(0, 16):
                self.NMK[i] = self.myreceivebuffer[93+i]
                s=s+hex(self.NMK[i])+ " "
            print("From SlacMatchCnf, got network membership key (NMK) " + s) 
            # use the extracted NMK and NID to set the key in the adaptor:
            self.composeSetKey(0)
            self.addToTrace("transmitting CM_SET_KEY.REQ")
            self.sniffer.sendpacket(bytes(self.mytransmitbuffer))
    
    def evaluateReceivedHomeplugPacket(self):
        mmt = self.getManagementMessageType()
        print(hex(mmt))
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
        if (mmt == CM_SET_KEY + MMTYPE_CNF):
            self.evaluateSetKeyCnf()

        
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

    def __init__(self, callbackAddToTrace=None, callbackShowStatus=None, mode=C_LISTEN_MODE, addrMan=None):
        self.mytransmitbuffer = bytearray("Hallo das ist ein Test", 'UTF-8')
        self.nPacketsReceived = 0
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackShowStatus = callbackShowStatus
        self.addressManager = addrMan
        self.pevSequenceState = 0
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
        self.NMK = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 ] # a default network key
        self.NID = [ 1, 2, 3, 4, 5, 6, 7 ] # a default network ID
        self.pevMac = [0x55, 0x56, 0x57, 0x58, 0x59, 0x5A ] # a default pev MAC. Will be overwritten later.
        self.myMAC = self.addressManager.getLocalMacAddress()
        self.runningCounter=0
        self.ipv6 = pyPlcIpv6.ipv6handler(self.transmit, self.addressManager)
        self.ipv6.ownMac = self.myMAC
        if (mode == C_LISTEN_MODE):
            self.enterListenMode()
        if (mode == C_EVSE_MODE):
            self.enterEvseMode()
        if (mode == C_PEV_MODE):
            self.enterPevMode()
        self.showStatus(prettyMac(self.pevMac), "pevmac")
        print("sniffer created at " + self.strInterfaceName)

    def addToTrace(self, s):
        self.callbackAddToTrace(s)

    def showStatus(self, s, selection=""):
        self.callbackShowStatus(s, selection) 
        
    def mainfunction(self):  
        # print("will evaluate self.sniffer")
        for ts, pkt in self.sniffer: # attention: for using this in non-blocking manner, we need the patch described above.
            self.nPacketsReceived+=1
            # print('%d' % (ts)) # the time stamp
            # We received an ethernet package. Determine its type, and dispatch it to the related handler.
            etherType = self.getEtherType(pkt)
            if (etherType == 0x88E1): # it is a HomePlug message
                self.myreceivebuffer = pkt
                self.evaluateReceivedHomeplugPacket()
            if (etherType == 0x86dd): # it is an IPv6 frame
                self.ipv6.evaluateReceivedPacket(pkt)
                
        self.showStatus("nPacketsReceived=" + str(self.nPacketsReceived))
        self.runPevSequencer() # run the message sequencer for the PEV side
        
    def close(self):
        self.sniffer.close()

