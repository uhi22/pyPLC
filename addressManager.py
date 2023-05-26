
#
# Address Manager
#
# Keeps, provides and finds the MAC and IPv6 addresses
#
import subprocess
import os
import sys
import ipaddress
from helpers import * # prettyMac etc
from configmodule import getConfigValue, getConfigValueBool

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
        self.pevIp=""
        self.SeccIp=""
        self.SeccTcpPort = 15118 # just a default. Will be overwritten during SDP if we are pev.
        pass
        
    def findLinkLocalIpv6Address(self):
        # For the IPv4 address, this works:
        # print(socket.gethostbyname(socket.gethostname())) # Result: The ipv4 address of the ethernet adaptor
        # But this does not help, we need the IPv6 address.
        #
        # On windows we can use command line tool "ipconfig".
        # The link-local addresses always start with fe80::, so we just parse the output of ipconfig line-by-line.
        # If we have multiple interfaces (e.g. ethernet and WLAN), it will find multiple link-local-addresses.
        #
        # On Linux, we use "ip addr". From its output we can directly see the ethernet IPv6 and MAC, even if
        # there are multiple other interfaces (e.g. WLAN). Pitfall: As long as there is nothing connected to the
        # ethernet, the Raspberry will not tell a link-local IPv6 in the command "ip addr". This means, we must
        # make sure that the modem is connected and powered, when the script is starting.
        ba = bytearray(6) 
        foundAddresses = []
        if os.name == 'nt':
            # on Windows
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
        else:
            # on Raspberry
            # instead of the deprecated ifconfig, use "ip addr"
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True)    
            if (len(result.stderr)>0):
                print(result.stderr)
            else:
                blInTheEthernetChapter = 0
                lines = result.stdout.split("\n")
                for line in lines:
                    # print(line);
                    if (line[0:1]!=" "): # if the line does not start with a blank, then it is a heading, e.g.
                                         # 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
                                         # 3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
                        # print("This is a heading")
                        sFind = ": " + getConfigValue("eth_interface") # e.g. "eth0"
                        if (line.find(sFind)>0):
                            # print("This is the heading for the ethernet.")
                            blInTheEthernetChapter = 1 # we are in the ethernet chapter
                        else:
                            blInTheEthernetChapter = 0 # we are not in the ethernet chapter
                    else:
                        # The line started with a blank. This means, it is no heading.
                        # In the best case, we find here something like
                        #     inet6 fe80::181f:efdf:97e5:2191/64 scope link 
                        if ((blInTheEthernetChapter==1) and (line.find("  inet6")>0) and (line.find(" scope link")>0)):
                            k = line.find(" fe80::") # the beginning of the IPv6
                            if (k>0):
                                sIpWithText = line[k+1:]
                                x = sIpWithText.find(" ") # the space is the end of the IPv6
                                sIp = sIpWithText[0:x]
                                x = sIp.find("/") # remove the /64 at the end
                                if (x>0):
                                  sIp = sIp[0:x]
                                # print("[addressManager] IP=>" + sIp + "<")
                                foundAddresses.append(sIp)

                        # Also the ethernet MAC is visible here, something like
                        #    link/ether b8:27:eb:27:33:53 brd ff:ff:ff:ff:ff:ff
                        if ((blInTheEthernetChapter==1) and (line.find(" link/ether")>0)):
                            # print(line)
                            k = line.find("link/ether ")
                            # print(k)
                            strMac = line[k+11:k+28]
                            # e.g. "b8:27:eb:12:34:56"
                            # print(strMac)
                            # Remove all ":"
                            strMac = strMac.replace(":", "")
                            # print(strMac)
                            if (len(strMac)!=12):
                               print("[addressManager] ERROR: invalid length of MAC string. Expected be 6 bytes, means 12 hex characters. Found " + str(len(strMac)))
                            else:
                               for i in range(0, 6):
                                  sTwoChar = strMac[2*i : 2*i+2]
                                  ba[i] = int(sTwoChar, 16)
                               self.localMac = ba
                               print("[addressManager] we have local MAC " + prettyMac(self.localMac) + ".")


        print("[addressManager] Found " + str(len(foundAddresses)) + " link-local IPv6 addresses.")
        for a in foundAddresses:
            print(a)
        self.localIpv6Addresses = foundAddresses
        if (len(self.localIpv6Addresses)==0):
            print("[addressManager] Error: No local Ipv6 address was found.")
            self.localIpv6Address = "localhost"
            cfg_exitIfNoLocalLinkAddressIsFound = 1
            if (cfg_exitIfNoLocalLinkAddressIsFound!=0):
                print("Exiting, because it does not make sense to continue without IPv6 address");
                sys.exit(1);
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
        ba = bytearray(6) 
        if os.name == 'nt':  
            # on Windows
            self.localMac = MAC_LAPTOP
            print("[addressManager] we have local MAC " + prettyMac(self.localMac) + ". Todo: find this out dynamically.")
        else:
            # on raspberry
            # nothing to do here. The MAC address is found together with the IPv6 address above.
            pass
            
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

    def setSeccIp(self, SeccIp):
        # During SDP, the IPv6 of the charger was found out. Store it, maybe we need it later.
        if (type(SeccIp)==type(bytearray([0]))):
            # the parameter was a bytearray. We want a string, so convert it.
            # print("this is a byte array")
            if (len(SeccIp)!=16):
                print("[addressManager] ERROR: setSeccIp: invalid ip address len " + str(len(SeccIp)))
                return
            s = ""
            for i in range(0, 16):
                s = s + twoCharHex(SeccIp[i])
                if (((i % 2)==1) and (i!=15)):
                    s = s + ":"
            self.SeccIp = s.lower()
        else:
            # the parameter was a string, assumingly. Just take it over.
            self.SeccIp = SeccIp
        print("[addressManager] charger has IP " + self.SeccIp)

    def getSeccIp(self):
        # The IPv6 address of the charger. Type is String.
        return self.SeccIp

    def setSeccTcpPort(self, SeccTcpPort):
        # During SDP, the TCP port of the charger was found out. Store it, we need it later.
        self.SeccTcpPort = SeccTcpPort
        print("[addressManager] charger has TCP port " + str(self.SeccTcpPort))
        
    def getSeccTcpPort(self):
        # The chargers TCP port, which it announced in the SDP response.
        return self.SeccTcpPort

        
    def getLocalMacAddress(self):
        print("[addressManager] will give local MAC " + prettyMac(self.localMac))
        return self.localMac;
        
    def getLocalMacAsTwelfCharString(self):
        # gives the own MAC as string of 12 hex characters, without : or spaces.
        s = ""
        for i in range(0, 6):
            s = s + twoCharHex(self.localMac[i])
        return s
        
    def getLinkLocalIpv6Address(self, resulttype="string"):
        if (resulttype=="string"):
            return self.localIpv6Address;
        if (resulttype=="bytearray"):
            # The caller wants a byte array. We need to convert a string like
            # "fe80::4c46:fea5:b6c9:25a9%3" into a byte array of 16 bytes.
            # "fe80::4c46:fea5:b6c9:25a9"
            # print("[addressManager] converting self.localIpv6Address into bytearray")
            # Step1: remove the % and all behind:
            s = self.localIpv6Address
            s = s.partition('%')[0]
            #print(s)
            # Step 2: expand the ommited zeros
            # Step 3: Fill in leading zeroes for each 16 bit field
            # Step 4: Remove all ":"
            s = ipaddress.IPv6Address(s).exploded.replace(':', '')
            #print(s)
            ba = bytearray(s, 'utf-8')
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
    print("Test result: LinkLocalIpv6=" + am.getLinkLocalIpv6Address())
    print("same as byte array: " + str(am.getLinkLocalIpv6Address(resulttype="bytearray")))
    
