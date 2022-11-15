

import subprocess
import os
from helpers import * # prettyMac etc

MAC_LAPTOP    = [0xdc, 0x0e, 0xa1, 0x11, 0x67, 0x08 ] # Win10 laptop
#MAC_RANDOM    = [0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff ]
#MAC_ALPI      = [0x0A, 0x19, 0x4A, 0x39, 0xD6, 0x98 ] # alpitronics
#MAC_TPLINK_E4 = [0x98, 0x48, 0x27, 0x5A, 0x3C, 0xE4 ] # TPlink PLC adaptor
#MAC_TPLINK_E6 = [0x98, 0x48, 0x27, 0x5A, 0x3C, 0xE6 ] # TPlink PLC adaptor
#MAC_DEVOLO_26 = [0xBC, 0xF2, 0xAF, 0x0B, 0x8E, 0x26 ] # Devolo PLC adaptor


class addressManager():
    def __init__(self):
        self.localIpv6Addresses=[]
        self.findLocalMacAddress()
        self.findLinkLocalIpv6Address()
        pass
        
    def findLinkLocalIpv6Address(self):
        # For the IPv4 address, this works:
        # print(socket.gethostbyname(socket.gethostname())) # Result: The ipv4 address of the ethernet adaptor
        # But this does not help, we need the IPv6 address.
        #
        # On windows we can use command line tool "ipconfig".
        # The link-local addresses always start with fe80::, so we just parse the output of ipconfig line-by-line.
        # If we have multiple interfaces (e.g. ethernet and WLAN), it will find multiple link-local-addresses.
        foundAddresses = []
        if os.name == 'nt':
            result = subprocess.run(["ipconfig.exe"], capture_output=True, text=True, encoding="ansi")    
            if (len(result.stderr)>0):
                print(result.stderr)
            else:
                lines = result.stdout.split("\n")
                for line in lines:
                    if (line.find("IPv6")>0):
                        k = line.find(" fe80::")
                        if (k>0):
                            foundAddresses.append(line[k+1:])
        print("[addressManager] Found " + str(len(foundAddresses)) + " link-local IPv6 addresses.")
        for a in foundAddresses:
            print(a)
        self.localIpv6Addresses = foundAddresses
        if (len(self.localIpv6Addresses)==0):
            print("[addressManager] Error: No local Ipv6 address was found.")
            self.localIpv6Address = "localhost"
        else:
            # at least one address was found. Take the first one (this may be the wrong adaptor).
            self.localIpv6Address = self.localIpv6Addresses[0]
            if (len(self.localIpv6Addresses)>1):
                print("[addressManager] Warning: Multiple Ipv6 addresses were found. If you have multiple network adaptors, try to disconnect the not relevant ones.")
                print("[addressManager] Using the first detected, " + self.localIpv6Addresses[0])
        print("[addressManager] Local IPv6 is " + self.localIpv6Address)

    def findLocalMacAddress(self):
        # Find out the MAC address of the local ethernet interface.
        # Todo: Find this out dynamically.
        self.localMac = MAC_LAPTOP
        print("[addressManager] we have local MAC " + prettyMac(self.localMac) + ". Todo: find this out dynamically.")
        
    def setPevMac(self, pevMac):
        # During the SLAC, the MAC of the PEV was found out. Store it, maybe we need it later.
        self.pevMac = pevMac
        print("[addressManager] pev has MAC " + prettyMac(self.pevMac))

    def setEvseMac(self, evseMac):
        # During the SLAC, the MAC of the EVSE was found out. Store it, maybe we need it later.
        self.evseMac = evseMac
        print("[addressManager] evse has MAC " + prettyMac(self.evseMac))

    def setPevIp(self, pevIp):
        # During SDP, the IPv6 of the PEV was found out. Store it, maybe we need it later.
        if (type(pevIp)==type(bytearray([0]))):
            # the parameter was a bytearray. We want a string, so convert it.
            # print("this is a byte array")
            if (len(pevIp)!=16):
                print("[addressManager] ERROR: setPevIp: invalid ip address len " + str(len(pevIp)))
                return
            s = ""
            for i in range(0, 16):
                s = s + twoCharHex(pevIp[i])
                if (((i % 2)==1) and (i!=15)):
                    s = s + ":"
            self.pevIp = s.lower()
        else:
            # the parameter was a string, assumingly. Just take it over.
            self.pevIp = pevIp
        print("[addressManager] pev has IP " + self.pevIp)

        
    def getLocalMacAddress(self):
        print("[addressManager] will give local MAC " + prettyMac(self.localMac))
        return self.localMac;
        
    def getLinkLocalIpv6Address(self, resulttype="string"):
        if (resulttype=="string"):
            return self.localIpv6Address;
        if (resulttype=="bytearray"):
            # The caller wants a byte array. We need to convert a string like
            # "fe80::4c46:fea5:b6c9:25a9%3" into a byte array of 16 bytes.
            # "fe80::4c46:fea5:b6c9:25a9"
            ba = bytearray(16) 
            s = self.localIpv6Address
            print("[addressManager] converting self.localIpv6Address into bytearray")
            # Step1: remove the % and all behind:
            x = s.find("%")
            #print("percent found at " + str(x))
            #print(s)
            if (x>0):
                s=s[0:x]
                print(s)
            # Step 2: expand the ommited zeros
            x = s.find("::")
            #print(":: found at " + str(x))
            if (x>0):
                # a :: means four bytes which are 0x00 each.
                # Todo: but we need two bytes more?!?
                s = s.replace("::", ":0000:0000:0000:")
            print(s)
            # Step 3: Remove all ":"
            s = s.replace(":", "")
            print(s)
            if (len(s)!=32):
                print("[addressManager] ERROR: invalid length of IPv6 string. Expected be 16 bytes, means 32 hex characters. Found " + str(len(s)))
            else:
                for i in range(0, 16):
                    sTwoChar = s[2*i : 2*i+2]
                    ba[i] = int(sTwoChar, 16)
                    #print(sTwoChar)
            #fe80::4c46:fea5:b6c9:25a9%3
            return ba


if __name__ == "__main__":
    print("Testing addressManager.py....")
    am = addressManager()
    #am.setPevIp(bytearray([0xfe, 0x80]))
    am.setPevIp(bytearray([0xfe, 0x80, 0x00, 0x00, 0xfe, 0x80, 0x00, 0x00, 0xfe, 0x80, 0x00, 0x00, 0xDE, 0xAD, 0xBE, 0xEF]))
    print(am.getLinkLocalIpv6Address())
    print(am.getLinkLocalIpv6Address(resulttype="bytearray"))
    