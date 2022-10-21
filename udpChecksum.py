
# Calculation for UDP checksum
#
# This module calculates the UDP checksum in case of IPv6 usage.
#
from helpers import showAsHex

# A valid ethernet frame, containing IPv6 and UDP, to verify the checksum algorithm.
testethernetframe = [
  0x33 , 0x33 , 0x00 , 0x00 , 0x00 , 0x01,
  0x04 , 0x65 , 0x65 , 0x00 , 0x64 , 0xc3 ,
  0x86 , 0xdd ,
  0x60 , 0x00
, 0x00 , 0x00 , 0x00 , 0x12 , 0x11 , 0x0a , 0xfe , 0x80 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x06 , 0x65
, 0x65 , 0xff , 0xfe , 0x00 , 0x64 , 0xc3 , 0xff , 0x02 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x00
, 0x00 , 0x00 , 0x00 , 0x00 , 0x00 , 0x01 , 0xcc , 0xaf , 0x3b , 0x0e , 0x00 , 0x12 , 0x89 , 0x5e , 0x01 , 0xfe
, 0x90 , 0x00 , 0x00 , 0x00 , 0x00 , 0x02 , 0x10 , 0x00 ]



def calculateUdpChecksumForIPv6(udpframe, ipv6source, ipv6dest):
    # Parameters:
    # udpframe: the udp frame including udp header and udppayload
    # ipv6source: the 16 byte IPv6 source address. Must be the same, which is used later for the transmission.
    # ipv6source: the 16 byte IPv6 destination address. Must be the same, which is used later for the transmission.
    udpframe[6] = 0 # at the beginning, set the checksum in the udp header to 00 00.
    udpframe[7] = 0
    # construct an array, consisting of a 40-byte-pseudo-ipv6-header, and the udp frame (consisting of udp header and udppayload)
    bufferlen = 40+len(udpframe)
    if ((bufferlen & 1)!=0):
        # if we have an odd buffer length, we need to add a padding byte in the end, because the sum calculation
        # will need 16-bit-aligned data.
        bufferlen+=1
    buffer = bytearray(bufferlen)
    for i in range(0, len(buffer)):
        buffer[i] = 0 # everything 0 for clean initialization
    # fill the pseudo-ipv6-header
    for i in range(0, 16): # copy 16 bytes IPv6 addresses
        buffer[i] = ipv6source[i] # IPv6 source address
        buffer[16+i] = ipv6dest[i] # IPv6 destination address
    udplen = len(udpframe)
    nxt = 0x11 # should be 0x11 in case of udp
    buffer[32] = 0 # high byte of the FOUR byte length is always 0
    buffer[33] = 0 # 2nd byte of the FOUR byte length is always 0
    buffer[34] = udplen >> 8 # 3rd
    buffer[35] = udplen & 0xFF # low byte of the FOUR byte length
    buffer[36] = 0 # 3 padding bytes with 0x00
    buffer[37] = 0
    buffer[38] = 0
    buffer[39] = nxt # the nxt is at the end of the pseudo header
    # pseudo-ipv6-header finished. Now lets put the udpframe into the buffer. (Containing udp header and udppayload)
    for i in range(0, len(udpframe)):
        buffer[40+i] = udpframe[i]
    # showAsHex(buffer, "buffer ")
    # buffer is prepared. Run the checksum over the complete buffer.
    totalSum = 0
    for i in range(0, len(buffer)>>1): # running through the complete buffer, in 2-byte-steps
        value16 = buffer[2*i] * 256 + buffer[2*i+1] # take the current 16-bit-word
        totalSum += value16 # we start with a normal addition of the value to the totalSum
        # But we do not want normal addition, we want a 16 bit one's complement sum,
        # see https://en.wikipedia.org/wiki/User_Datagram_Protocol
        if (totalSum>=65536): # On each addition, if a carry-out (17th bit) is produced, 
            totalSum-=65536 # swing that 17th carry bit around 
            totalSum+=1 # and add it to the least significant bit of the running total.
    # Finally, the sum is then one's complemented to yield the value of the UDP checksum field.
    checksum = totalSum ^ 0xffff
    return checksum


if __name__ == "__main__":
    print("Testing the udp checksum calculation...")
    showAsHex(testethernetframe, "testethernetframe ")
    ipv6frame = bytearray(len(testethernetframe)-6-6-2) # without the ethernet header (MAC, MAC, ethertype)
    for i in range(0, len(ipv6frame)):
        ipv6frame[i] = testethernetframe[14+i]
        
    showAsHex(ipv6frame, "ipv6frame ")    
    # checksum calculation see https://en.wikipedia.org/wiki/User_Datagram_Protocol

    # We want to calculate the UDP checksum. This needs to include also some data from "lower level" IP header, so we need the complete IP frame, not
    # only the UDP part.
    #
    # From wikipedia.org: Checksum is the 16-bit one's complement
    # of the one's complement sum of a pseudo header of information from
    #  * the IP header,
    #  * the UDP header,
    #  * and the data,
    # padded with zero octets at the end (if necessary) to make a multiple of two octets.

    # The pseudoIPv6 header for checksum calculation has a DIFFERENT format then a normal IPv6 header. So we cannot use the original frame,
    # instead, we copy the relevant information out of it into a dedicated buffer.
    # We have IPv6, so the IP header is 
    ipv6pseudoheader = bytearray(40)
    for i in range(0, 16):
        ipv6pseudoheader[i] = ipv6frame[8+i] # IPv6 source address
        ipv6pseudoheader[16+i] = ipv6frame[24+i] # IPv6 destination address
    udplen = ipv6frame[4]*256 + ipv6frame[5] # the real IPv6 header has a two byte length info
    nxt = ipv6frame[6] # the real IPv6 header next-protocol information (should be 0x11 in case of udp)
    print("udplen=" + str(udplen))
    print("nxt=" + str(nxt))
    ipv6pseudoheader[32] = 0 # high byte of the FOUR byte length is always 0
    ipv6pseudoheader[33] = 0 # 2nd byte of the FOUR byte length is always 0
    ipv6pseudoheader[34] = udplen >> 8 # 3rd
    ipv6pseudoheader[35] = udplen & 0xFF # low byte of the FOUR byte length
    ipv6pseudoheader[36] = 0 # 3 padding bytes with 0x00
    ipv6pseudoheader[37] = 0
    ipv6pseudoheader[38] = 0
    ipv6pseudoheader[39] = nxt # the nxt is at the end of the pseudo header
    showAsHex(ipv6pseudoheader, "ipv6pseudoheader ")

    udpHeader = bytearray(8)
    for i in range(0, 8):
        udpHeader[i] = ipv6frame[40+i] # in the real IPv6, we have also 40 byte IPv6 header, and afterwards the 8 byte UDP header
    showAsHex(udpHeader, "udpHeader ")

    udpPayload = bytearray(udplen-8) # payload size is the announced udp size minus udpHeaderSize
    for i in range(0, len(udpPayload)):
        udpPayload[i] = ipv6frame[40+8+i]

    showAsHex(udpPayload, "udpPayload ")

    transmittedChecksum = udpHeader[6] * 256 + udpHeader[7]
    print("The transmitted checksum is " + hex(transmittedChecksum))

    # Checksum algorithm:
    # 1. Set the checksum in the udp header to 00 00
    udpHeader[6] = 0
    udpHeader[7] = 0
    runningTotal = 0 # startvalue zero
    for i in range(0, len(ipv6pseudoheader)>>1):
        value16 = ipv6pseudoheader[2*i] * 256 + ipv6pseudoheader[2*i+1]
        runningTotal += value16
        if (runningTotal>=65536): # On each addition, if a carry-out (17th bit) is produced, 
            runningTotal-=65536 # swing that 17th carry bit around 
            runningTotal+=1 # and add it to the least significant bit of the running total.

    for i in range(0, len(udpHeader)>>1):
        value16 = udpHeader[2*i] * 256 + udpHeader[2*i+1]
        runningTotal += value16
        if (runningTotal>=65536): # On each addition, if a carry-out (17th bit) is produced, 
            runningTotal-=65536 # swing that 17th carry bit around 
            runningTotal+=1 # and add it to the least significant bit of the running total.

    for i in range(0, len(udpPayload)>>1):
        value16 = udpPayload[2*i] * 256 + udpPayload[2*i+1]
        runningTotal += value16
        if (runningTotal>=65536): # On each addition, if a carry-out (17th bit) is produced, 
            runningTotal-=65536 # swing that 17th carry bit around 
            runningTotal+=1 # and add it to the least significant bit of the running total.

    # Finally, the sum is then one's complemented to yield the value of the UDP checksum field.
    checksum = runningTotal ^ 0xffff
    print("calculated checksum=" + hex(checksum))

    # Same test, using the function
    myUdpFrame = bytearray(udplen) # payload size is the announced udp size
    for i in range(0, len(myUdpFrame)):
        myUdpFrame[i] = ipv6frame[40+i]
        
    myIpv6Source = bytearray(16)
    myIpv6Dest = bytearray(16)
    for i in range(0, 16):
        myIpv6Source[i] = ipv6frame[8+i] # IPv6 source address
        myIpv6Dest[i] = ipv6frame[24+i] # IPv6 destination address

    print("calculated with the function call: " + hex(calculateUdpChecksumForIPv6(myUdpFrame, myIpv6Source, myIpv6Dest)))