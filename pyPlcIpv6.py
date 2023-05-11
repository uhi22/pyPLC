
# This module handles the IPv6 related functionality of the communication between charging station and car.
#
# It has the following sub-functionalities:
# - IP.UDP.SDP for EvseMode: listen to requests from the car, and responding to them.
#   Eth --> IPv6 --> UDP --> V2GTP --> SDP
#                                       |
#                                       v
#   Eth <-- IPv6 <-- UDP <-- V2GTP <-- SDP
#
# - IP.UDP.SDP for PevMode: initiate an SDP request, and listen to the response of the charger
#     +----  Eth <-- IPv6 <-- UDP <-- V2GTP <-- SDP
# homeplug
#   EVSE
# homeplug                                                                         
#     +--->  Eth --> IPv6 --> UDP --> V2GTP --> SDP
#
# Abbreviations:
# SECC: Supply Equipment Communication Controller. The "computer" of the charging station.
# EVCC: Electric Vehicle Communication Controller. The "computer" of the vehicle.
# SDP: SECC Discovery Protocol. The UDP based protocol to find out the IP address of the charging station.
# SLAAC: Stateless auto address configuration (not SLAC!). A method to automatically set IPv6 address, based
#        on the 6 byte MAC address.

from helpers import showAsHex, prettyHexMessage, prettyMac
import udpChecksum


class ipv6handler():
    def fillMac(self, macbytearray, position=6): # position 6 is the source MAC
        for i in range(0, 6):
            self.EthTxFrame[6+i] = macbytearray[i]
            
    def packResponseIntoEthernet(self, buffer):
        # packs the IP packet into an ethernet packet
        self.EthTxFrame = bytearray(len(buffer) + 6 + 6 + 2) # Ethernet header needs 14 bytes:
                                                      #  6 bytes destination MAC
                                                      #  6 bytes source MAC
                                                      #  2 bytes EtherType
        for i in range(0, 6): # fill the destination MAC with the source MAC of the received package
            self.EthTxFrame[i] = self.myreceivebuffer[6+i]
        self.fillMac(self.ownMac) # bytes 6 to 11 are the source MAC
        self.EthTxFrame[12] = 0x86 # 86dd is IPv6
        self.EthTxFrame[13] = 0xdd
        for i in range(0, len(buffer)):
            self.EthTxFrame[14+i] = buffer[i]
        self.transmit(self.EthTxFrame)
        
                                                      
    def packResponseIntoIp(self, buffer):
        # embeds the (SDP) response into the lower-layer-protocol: IP, Ethernet
        self.IpResponse = bytearray(len(buffer) + 8 + 16 + 16) # IP6 needs 40 bytes:
                                                      #   4 bytes traffic class, flow
                                                      #   2 bytes destination port
                                                      #   2 bytes length (incl checksum)
                                                      #   2 bytes checksum
        self.IpResponse[0] = 0x60 # traffic class, flow
        self.IpResponse[1] = 0
        self.IpResponse[2] = 0
        self.IpResponse[3] = 0
        plen = len(buffer) # length of the payload. Without headers.
        self.IpResponse[4] = plen >> 8
        self.IpResponse[5] = plen & 0xFF
        self.IpResponse[6] = 0x11 # next level protocol, 0x11 = UDP in this case
        self.IpResponse[7] = 0x0A # hop limit
        for i in range(0, 16):
            self.IpResponse[8+i] = self.SeccIp[i] # source IP address
        for i in range(0, 16):
            self.IpResponse[24+i] = self.EvccIp[i] # destination IP address
        for i in range(0, len(buffer)):
            self.IpResponse[40+i] = buffer[i]
        #showAsHex(self.IpResponse, "IP response ")
        self.packResponseIntoEthernet(self.IpResponse)


    def packResponseIntoUdp(self, buffer):
        # embeds the (SDP) response into the lower-layer-protocol: UDP
        self.UdpResponse = bytearray(len(buffer) + 8) # UDP needs 8 bytes:
                                                      #   2 bytes source port
                                                      #   2 bytes destination port
                                                      #   2 bytes length (incl checksum)
                                                      #   2 bytes checksum
        self.UdpResponse[0] = 15118 >> 8
        self.UdpResponse[1] = 15118 & 0xFF
        self.UdpResponse[2] = self.evccPort >> 8
        self.UdpResponse[3] = self.evccPort  & 0xFF
        lenInclChecksum = len(buffer) + 8
        self.UdpResponse[4] = lenInclChecksum >> 8
        self.UdpResponse[5] = lenInclChecksum & 0xFF
        # checksum will be calculated afterwards
        self.UdpResponse[6] = 0
        self.UdpResponse[7] = 0
        for i in range(0, len(buffer)):
            self.UdpResponse[8+i] = buffer[i]
        #showAsHex(self.UdpResponse, "UDP response ")
        # The content of buffer is ready. We can calculate the checksum. see https://en.wikipedia.org/wiki/User_Datagram_Protocol
        checksum = udpChecksum.calculateUdpChecksumForIPv6(self.UdpResponse, self.SeccIp, self.EvccIp)   
        self.UdpResponse[6] = checksum >> 8
        self.UdpResponse[7] = checksum & 0xFF        
        self.packResponseIntoIp(self.UdpResponse)
        
    def sendSdpResponse(self):
        # SECC Discovery Response.
        # The response from the charger to the EV, which transfers the IPv6 address of the charger to the car.
        if (self.faultInjectionSuppressSdpResponse>0):
            print("Fault injection: SDP response suppressed")
            self.faultInjectionSuppressSdpResponse-=1
            return
        self.SdpPayload = bytearray(20) # SDP response has 20 bytes
        for i in range(0, 16):
            self.SdpPayload[i] = self.SeccIp[i] # 16 bytes IP address of the charger
        # Here the charger decides, on which port he will listen for the TCP communication.
        # We use port 15118, same as for the SDP. But also dynamically assigned port would be ok.
        # The alpitronics seems to use different ports on different chargers, e.g. 0xC7A7 and 0xC7A6.
        # The ABB Triple and ABB HPC are reporting port 0xD121, but in fact (also?) listening
        # to the port 15118.
        seccPort = 15118
        self.SdpPayload[16] = seccPort >> 8 # SECC port high byte.
        self.SdpPayload[17] = seccPort & 0xFF # SECC port low byte. 
        self.SdpPayload[18] = 0x10 # security. We only support "no transport layer security, 0x10".
        self.SdpPayload[19] = 0x00 # transport protocol. We only support "TCP, 0x00".
        showAsHex(self.SdpPayload, "SDP payload ")
        # add the SDP header
        lenSdp = len(self.SdpPayload)
        self.V2Gframe = bytearray(lenSdp + 8) # V2GTP header needs 8 bytes:
                                                    # 1 byte protocol version
                                                    # 1 byte protocol version inverted
                                                    # 2 bytes payload type
                                                    # 4 byte payload length
        self.V2Gframe[0] = 0x01 # version
        self.V2Gframe[1] = 0xfe # version inverted
        self.V2Gframe[2] = 0x90 # payload type. 0x9001 is the SDP response message
        self.V2Gframe[3] = 0x01 # 
        self.V2Gframe[4] = (lenSdp >> 24) & 0xff # length 4 byte.
        self.V2Gframe[5] = (lenSdp >> 16) & 0xff
        self.V2Gframe[6] = (lenSdp >> 8) & 0xff
        self.V2Gframe[7] = lenSdp & 0xff
        for i in range(0, lenSdp):
            self.V2Gframe[8+i] = self.SdpPayload[i]
        showAsHex(self.V2Gframe, "V2Gframe ")
        self.packResponseIntoUdp(self.V2Gframe)
        
    def evaluateUdpPayload(self):
        if ((self.destinationport == 15118) or (self.sourceport == 15118)): # port for the SECC
            if ((self.udpPayload[0]==0x01) and (self.udpPayload[1]==0xFE)): # protocol version 1 and inverted
                # it is a V2GTP message
                if (self.iAmEvse) and (self.destinationport == 15118):
                    # if we are the charger, and it is a message from car to charger, lets save the cars IP for later use.
                    self.EvccIp = self.sourceIp
                    self.addressManager.setPevIp(self.EvccIp)
                showAsHex(self.udpPayload, "V2GTP ")
                if (self.destinationport == 15118): #if the destination is the charger,
                    self.evccPort = self.sourceport #then the source is the vehicle
                v2gptPayloadType = self.udpPayload[2] * 256 + self.udpPayload[3]
                # 0x8001 EXI encoded V2G message (Will NOT come with UDP. Will come with TCP.)
                # 0x9000 SDP request message (SECC Discovery)
                # 0x9001 SDP response message (SECC response to the EVCC)
                if (v2gptPayloadType == 0x9000):
                    v2gptPayloadLen = self.udpPayload[4] * 256 ** 3 + self.udpPayload[5] * 256 ** 2 + self.udpPayload[6] * 256 + self.udpPayload[7]
                    if (v2gptPayloadLen == 2):
                        # 2 is the only valid length for a SDP request.
                        seccDiscoveryReqSecurity = self.udpPayload[8] # normally 0x10 for "no transport layer security". Or 0x00 for "TLS".
                        seccDiscoveryReqTransportProtocol = self.udpPayload[9] # normally 0x00 for TCP
                        if (seccDiscoveryReqSecurity!=0x10):
                            print("seccDiscoveryReqSecurity " + str(seccDiscoveryReqSecurity) + " is not supported")
                        else:    
                            if (seccDiscoveryReqTransportProtocol!=0x00):
                                print("seccDiscoveryReqTransportProtocol " + str(seccDiscoveryReqTransportProtocol) + " is not supported")
                            else:
                                # This was a valid SDP request. Let's respond, if we are the charger.
                                if (self.iAmEvse==1):
                                    print("Ok, this was a valid SDP request. We are the SECC. Sending SDP response.")
                                    self.callbackShowStatus("SDP 2", "evseState")
                                    self.sendSdpResponse()
                    else:
                        print("v2gptPayloadLen on SDP request is " + str(v2gptPayloadLen) + " not supported")
                    return
                if (v2gptPayloadType == 0x9001):
                    # it is a SDP response from the charger to the car
                    if (self.iAmPev):
                        v2gptPayloadLen = self.udpPayload[4] * 256 ** 3 + self.udpPayload[5] * 256 ** 2 + self.udpPayload[6] * 256 + self.udpPayload[7]
                        if (v2gptPayloadLen == 20):
                            # 20 is the only valid length for a SDP response.
                            print("[PEV] Checkpoint203: Received SDP response")
                            # at byte 8 of the UDP payload starts the IPv6 address of the charger.
                            for i in range(0, 16):
                                self.SeccIp[i] = self.udpPayload[8+i] # 16 bytes IP address of the charger
                            # Extract the TCP port, on which the charger will listen:
                            seccTcpPort = (self.udpPayload[8+16]*256) + self.udpPayload[8+16+1]
                            self.addressManager.setSeccIp(self.SeccIp)
                            self.addressManager.setSeccTcpPort(seccTcpPort)
                            self.connMgr.SdpOk()
                    return    
                print("v2gptPayloadType " + hex(v2gptPayloadType) + " not supported")
                    
    def initiateSdpRequest(self):
        if (self.iAmPev == 1):
            # We are the car. We want to find out the IPv6 address of the charger. We
            # send a SECC Discovery Request.
            # The payload is just two bytes: 10 00.
            # First step is, to pack this payload into a V2GTP frame.
            print("[PEV] initiating SDP request")
            self.v2gtpFrame = bytearray(8 + 2) # 8 byte header plus 2 bytes payload
            self.v2gtpFrame[0] = 0x01 # version
            self.v2gtpFrame[1] = 0xFE # version inverted
            self.v2gtpFrame[2] = 0x90 # 9000 means SDP request message
            self.v2gtpFrame[3] = 0x00
            self.v2gtpFrame[4] = 0x00
            self.v2gtpFrame[5] = 0x00
            self.v2gtpFrame[6] = 0x00
            self.v2gtpFrame[7] = 0x02 # payload size
            self.v2gtpFrame[8] = 0x10 # payload
            self.v2gtpFrame[9] = 0x00 # payload
            # Second step: pack this into an UDP frame.
            self.packRequestIntoUdp(self.v2gtpFrame)

    def packRequestIntoUdp(self, buffer):
        # embeds the (SDP) request into the lower-layer-protocol: UDP
        # Reference: wireshark trace of the ioniq car
        self.UdpRequest = bytearray(len(buffer) + 8) # UDP header needs 8 bytes:
                                                      #   2 bytes source port
                                                      #   2 bytes destination port
                                                      #   2 bytes length (incl checksum)
                                                      #   2 bytes checksum
        self.pevPort = 50032 # "random" port. Todo: Do we need to ask the OS for a unique number, to avoid collision with existing port?
        self.UdpRequest[0] = self.pevPort >> 8
        self.UdpRequest[1] = self.pevPort  & 0xFF
        self.UdpRequest[2] = 15118 >> 8
        self.UdpRequest[3] = 15118 & 0xFF
        
        lenInclChecksum = len(buffer) + 8
        self.UdpRequest[4] = lenInclChecksum >> 8
        self.UdpRequest[5] = lenInclChecksum & 0xFF
        # checksum will be calculated afterwards
        self.UdpRequest[6] = 0
        self.UdpRequest[7] = 0
        for i in range(0, len(buffer)):
            self.UdpRequest[8+i] = buffer[i]
        #showAsHex(self.UdpRequest, "UDP request ")
        self.broadcastIPv6 = [ 0xff, 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        # The content of buffer is ready. We can calculate the checksum. see https://en.wikipedia.org/wiki/User_Datagram_Protocol
        checksum = udpChecksum.calculateUdpChecksumForIPv6(self.UdpRequest, self.EvccIp, self.broadcastIPv6)   
        self.UdpRequest[6] = checksum >> 8
        self.UdpRequest[7] = checksum & 0xFF        
        self.packRequestIntoIp(self.UdpRequest)
        
    def packRequestIntoIp(self, buffer):
        # embeds the (SDP) request into the lower-layer-protocol: IP, Ethernet
        self.IpRequest = bytearray(len(buffer) + 8 + 16 + 16) # IP6 header needs 40 bytes:
                                                      #   4 bytes traffic class, flow
                                                      #   2 bytes destination port
                                                      #   2 bytes length (incl checksum)
                                                      #   2 bytes checksum
        self.IpRequest[0] = 0x60 # traffic class, flow
        self.IpRequest[1] = 0
        self.IpRequest[2] = 0
        self.IpRequest[3] = 0
        plen = len(buffer) # length of the payload. Without headers.
        self.IpRequest[4] = plen >> 8
        self.IpRequest[5] = plen & 0xFF
        self.IpRequest[6] = 0x11 # next level protocol, 0x11 = UDP in this case
        self.IpRequest[7] = 0x0A # hop limit
        # We are the PEV. So the EvccIp is our own link-local IP address.
        self.EvccIp = self.addressManager.getLinkLocalIpv6Address("bytearray")
        for i in range(0, 16):
            self.IpRequest[8+i] = self.EvccIp[i] # source IP address
        for i in range(0, 16):
            self.IpRequest[24+i] = self.broadcastIPv6[i] # destination IP address
        for i in range(0, len(buffer)):
            self.IpRequest[40+i] = buffer[i]
        #showAsHex(self.IpRequest, "IpRequest ")
        self.packRequestIntoEthernet(self.IpRequest)

    def packRequestIntoEthernet(self, buffer):
        # packs the IP packet into an ethernet packet
        self.EthTxFrame = bytearray(len(buffer) + 6 + 6 + 2) # Ethernet header needs 14 bytes:
                                                      #  6 bytes destination MAC
                                                      #  6 bytes source MAC
                                                      #  2 bytes EtherType
        # fill the destination MAC with the IPv6 multicast
        self.EthTxFrame[0] = 0x33
        self.EthTxFrame[1] = 0x33
        self.EthTxFrame[2] = 0x00
        self.EthTxFrame[3] = 0x00
        self.EthTxFrame[4] = 0x00
        self.EthTxFrame[5] = 0x01
        self.fillMac(self.ownMac) # bytes 6 to 11 are the source MAC
        self.EthTxFrame[12] = 0x86 # 86dd is IPv6
        self.EthTxFrame[13] = 0xdd
        for i in range(0, len(buffer)):
            self.EthTxFrame[14+i] = buffer[i]
        self.transmit(self.EthTxFrame)

            

    def enterPevMode(self):
        self.iAmEvse = 0 # not emulating a charging station
        self.iAmPev = 1 # emulating a vehicle
    def enterEvseMode(self):
        self.iAmEvse = 1 # emulating a charging station
        self.iAmPev = 0 # not emulating a vehicle
        # If we are an charger, we need to support the SDP, which requires to know our IPv6 adrress.
        self.SeccIp = self.addressManager.getLinkLocalIpv6Address("bytearray")
        
    def enterListenMode(self):
        self.iAmEvse = 0 # not emulating a charging station
        self.iAmPev = 0 # not emulating a vehicle
        
    def evaluateV2GTP(self):
        # We sniffed a V2GTP frame via TCP. This should contain an EXI encoded payload.
        v2gptPayloadType = self.v2gframe[2] * 256 + self.v2gframe[3]
        # 0x8001 EXI encoded V2G message
        if (v2gptPayloadType == 0x8001):
            self.ExiPacket = self.v2gframe[8:] # the exi payload, without the 8 bytes V2GTP header
            s = "[SNIFFER] EXI from " + str(self.tcpsourceport) + " to " + str(self.tcpdestinationport) + " " + prettyHexMessage(self.ExiPacket)
            print(s)
            # print(s, file=self.exiLogFile)
            # Todo: further process the EXI packet. E.g. write it into file for offline analysis.
            # And send it to decoder.

    def evaluateTcpPacket(self):
        # We received a TCP packet. We do NOT want to make real TCP here (the OS will do it much better). We
        # just want to listen to the conversation of two others, and extract what we hear.
        self.tcpsourceport = self.myreceivebuffer[54] * 256 + self.myreceivebuffer[55]
        self.tcpdestinationport = self.myreceivebuffer[56] * 256 + self.myreceivebuffer[57]
        if (True): # we do not check port, because the TCP port is variable. (self.tcpsourceport == 15118) or (self.tcpdestinationport == 15118))
            if (len(self.myreceivebuffer)>=74+9): # 74 is the TCP without any data. A V2GTP has 8 bytes header, plus at least 1 payload byte.
                startOfV2gtp = 74 # the index of the first V2GTP byte in the ethernet buffer
                if ((self.myreceivebuffer[startOfV2gtp] == 0x01) and (self.myreceivebuffer[startOfV2gtp+1] == 0xFE)):
                    # version and inverted version of the V2GTP are fine -> it is a V2G TP frame.
                    self.v2gframe = self.myreceivebuffer[startOfV2gtp:]
                    self.evaluateV2GTP()
        
        
    def evaluateReceivedPacket(self, pkt):
        # The evaluation function for received ipv6 packages.
        if (len(pkt)>60):
            self.myreceivebuffer = pkt
            # extract the source ipv6 address
            self.sourceIp = bytearray(16)
            for i in range(0, 16):
                self.sourceIp[i] = self.myreceivebuffer[22+i]
            self.nextheader = self.myreceivebuffer[20]
            if (self.nextheader == 0x11): # it is an UDP frame
                self.sourceport = self.myreceivebuffer[54] * 256 + self.myreceivebuffer[55]
                self.destinationport = self.myreceivebuffer[56] * 256 + self.myreceivebuffer[57]
                self.udplen = self.myreceivebuffer[58] * 256 + self.myreceivebuffer[59]
                self.udpsum = self.myreceivebuffer[60] * 256 + self.myreceivebuffer[61]
                # udplen is including 8 bytes header at the begin
                if (self.udplen>8):
                    self.udpPayload = bytearray(self.udplen-8)
                    # print("self.udplen=" + str(self.udplen))
                    # print("self.myreceivebuffer len=" + str(len(self.myreceivebuffer)))
                    for i in range(0, self.udplen-8):
                        #print("index " + str(i) + " " + hex(self.myreceivebuffer[62+i]))
                        self.udpPayload[i] = self.myreceivebuffer[62+i]
                    self.evaluateUdpPayload()
            if (self.nextheader == 0x06): # it is an TCP frame
                self.evaluateTcpPacket()
                        
    def __init__(self, transmitCallback, addressManager, connMgr, callbackShowStatus):
        self.iAmEvse = 0
        self.iAmPev = 0
        self.transmit = transmitCallback
        self.addressManager = addressManager
        self.connMgr = connMgr
        self.callbackShowStatus = callbackShowStatus
        #self.exiLogFile = open('SnifferExiLog.txt', 'w')
        # 16 bytes, a default IPv6 address for the charging station
        # self.SeccIp = [ 0xfe, 0x80, 0, 0, 0, 0, 0, 0, 0x06, 0xaa, 0xaa, 0xff, 0xfe, 0, 0xaa, 0xaa ]
        # fe80::e0ad:99ac:52eb:85d3 is the Win10 laptop
        # self.SeccIp = [ 0xfe, 0x80, 0, 0, 0, 0, 0, 0, 0xe0, 0xad, 0x99, 0xac, 0x52, 0xeb, 0x85, 0xd3 ]
        # just a default for the chargers IP, will be filled later with the correct value from SDP
        self.SeccIp = bytearray(16)
        # 16 bytes, a default IPv6 address for the vehicle
        # Just a default, will be overwritten later:
        self.EvccIp = [ 0xfe, 0x80, 0, 0, 0, 0, 0, 0, 0x06, 0x65, 0x65, 0xff, 0xfe, 0, 0x64, 0xC3 ] 
        self.ownMac = self.addressManager.getLocalMacAddress()
        self.faultInjectionSuppressSdpResponse = 0 # can be set to >0 for fault injection. Number of "lost" SDP responses.
        print("pyPlcIpv6 started with ownMac " + prettyMac(self.ownMac))

