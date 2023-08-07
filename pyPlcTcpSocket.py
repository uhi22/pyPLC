
# Server and client on a non-blocking socket
#
# explanation of socket handling:
# https://docs.python.org/3/howto/sockets.html
# https://realpython.com/python-sockets/
# https://stackoverflow.com/questions/5308080/python-socket-accept-nonblocking
#


import socket
import select
import sys # for argv
import time # for time.sleep()
import errno
import os
import subprocess
from configmodule import getConfigValue, getConfigValueBool

class pyPlcTcpClientSocket():
    def __init__(self, callbackAddToTrace):
        self.callbackAddToTrace = callbackAddToTrace
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use
        # The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without
        # waiting for its natural timeout to expire.
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.isConnected = False
        self.rxData = []

    def addToTrace(self, s):
        self.callbackAddToTrace(s)
        
    def connect(self, host, port):
        try:
            self.addToTrace("TCP connecting to " + str(host) + " port " + str(port) + "...")
            # for connecting, we are still in blocking-mode because
            # otherwise we run into error "[Errno 10035] A non-blocking socket operation could not be completed immediately"
            # We set a shorter timeout, so we do not block too long if the connection is not established:
            #print("step1")
            self.sock.settimeout(0.5)
            #print("step2")

            # https://stackoverflow.com/questions/71022092/python3-socket-program-udp-ipv6-bind-function-with-link-local-ip-address-gi
            # While on Windows10 just connecting to a remote link-local-address works, under
            # Raspbian the socket.connect says "invalid argument".
            # host = "2003:d1:170f:d500:1744:89d:d921:b20f" # works
            # host = "2003:d1:170f:d500:2052:326e:cef9:ad07" # works
            # host = "fe80::c690:83f3:fbcb:980e" # invalid argument. Link local address needs an interface specified.
            # host = "fe80::c690:83f3:fbcb:980e%eth0" # ok with socket.getaddrinfo
            if (os.name != 'nt'):
                # We are at the Raspberry
                #print(host[0:5].lower())
                if (host[0:5].lower()=="fe80:"):
                    #print("This is a link local address. We need to add %eth0 at the end.")
                    ethInterface = getConfigValue("eth_interface") # e.g. "eth0"
                    host = host + "%" + ethInterface
            socket_addr = socket.getaddrinfo(host,port,socket.AF_INET6,socket.SOCK_DGRAM,socket.SOL_UDP)[0][4]
            
            #print(socket_addr)
            #print("step2b")
            # https://stackoverflow.com/questions/5358021/establishing-an-ipv6-connection-using-sockets-in-python
            #  (address, port, flow info, scope id) 4-tuple for AF_INET6
            # On Raspberry, the ScopeId is important. Just giving 0 leads to "invalid argument" in case
            # of link-local ip-address.
            #self.sock.connect((host, port, 0, 0))
            self.sock.connect(socket_addr)
            #print("step3")
            self.sock.setblocking(0) # make this socket non-blocking, so that the recv function will immediately return
            self.isConnected = True
        except socket.error as e:
            self.addToTrace("TCP connection failed" + str(e))
            self.isConnected = False

    def disconnect(self):
        # When connection is broken, the OS may still keep the information of socket usage in the background,
        # and this could raise the error "A connect request was made on an already connected socket" when
        # we try a simple connect again. 
        # This is explained here:
        # https://www.codeproject.com/Questions/1187207/A-connect-request-was-made-on-an-already-connected
        try:
            self.sock.close() # Close is not just closing. It means destroying the socket object. So we
            # need a new one:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            # https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use
            # The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without
            # waiting for its natural timeout to expire.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)            
            pass
        except socket.error as e:
            # if it was already closed, it is also fine.
            pass
        self.isConnected = False
            
    def transmit(self, msg):
        if (self.isConnected == False):
            # if not connected, just ignore the transmission request
            return -1
        totalsent = 0
        MSGLEN = len(msg)
        while (totalsent < MSGLEN) and (self.isConnected):
            try:
                sent = self.sock.send(msg[totalsent:])
                if sent == 0:
                    self.isConnected = False
                    self.addToTrace("TCP socket connection broken")
                    return -1
                totalsent = totalsent + sent
            except:
                self.isConnected = False
                return -1
        return 0 # success
        
    def isRxDataAvailable(self):
        # check for availability of data, and get the data from the socket into local buffer.
        if (self.isConnected == False):
            return False
        blDataAvail=False
        try:
            msg = self.sock.recv(4096)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                # this is the normal case, if no data is available
                # print('No data available')
                pass
            else:
                # a "real" error occurred
                # print("real error")
                # print(e)
                self.isConnected = False
        else:
            if len(msg) == 0:
                # print('orderly shutdown on server end')
                self.isConnected = False
            else:
                # we received data. Store it.
                self.rxData = msg
                blDataAvail=True
        return blDataAvail
        
    def getRxData(self):
        # provides the received data, and clears the receive buffer
        d = self.rxData
        self.rxData = []
        return d 

class pyPlcTcpServerSocket():
    def __init__(self, callbackAddToTrace, callbackStateNotification):
        self.callbackAddToTrace = callbackAddToTrace
        self.callbackStateNotification = callbackStateNotification
        # Todo: find the link-local IPv6 address automatically.
        #self.ipAdress = 'fe80::e0ad:99ac:52eb:85d3'
        #self.ipAdress = 'fe80::c690:83f3:fbcb:980e%15'
        self.ipAdress = ''
        self.tcpPort = 15118 # The port for CCS
        self.BUFFER_SIZE = 1024  # Normally 1024
        # Concept explanation:
        # We create a socket, that is just listening for incoming connections.
        # Later in the cyclic loop, we use the "select" to wait for activity on this socket.
        # In case there is a connection request, we create a NEW socket, which will handle the
        # data exchange. The original socket is still listening for further incoming connections.
        # This would allow to handle multiple connections.
        self.ourSocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.ourSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ourSocket.bind((self.ipAdress, self.tcpPort))
        self.ourSocket.listen(1)
        self.callbackStateNotification(1) # inform the higher level state machines, that TCP is listening
        self.addToTrace("pyPlcTcpSocket listening on port " + str(self.tcpPort))
        hostname=socket.gethostname()
        self.addToTrace("Hostname is " + hostname)
        self.read_list = [self.ourSocket]
        self.rxData = []
        
    def resetTheConnection(self):
        # in case of a broken connection, here we try to start it again
        self.addToTrace("Trying to reset the TCP socket")
        # Todo: how to "reset" the socket?
        try:
            self.ourSocket.close()
        except:
            pass
        self.ourSocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        self.ourSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ourSocket.bind((self.ipAdress, self.tcpPort))
        self.ourSocket.listen(1)
        self.callbackStateNotification(1) # inform the higher level state machines, that TCP is listening
        self.addToTrace("pyPlcTcpSocket listening on port " + str(self.tcpPort))
        # (unused gethostbyname removed, see https://openinverter.org/forum/viewtopic.php?p=59970#p59970)
        self.read_list = [self.ourSocket]
        self.rxData = []
        
    def addToTrace(self, s):
        self.callbackAddToTrace(s)

    def isRxDataAvailable(self):
        return (len(self.rxData)>0)
        
    def getRxData(self):
        # provides the received data, and clears the receive buffer
        d = self.rxData
        self.rxData = []
        return d
        
    def transmit(self, txMessage):
        numberOfSockets = len(self.read_list)
        if (numberOfSockets<2):
            # print("we have " + str(numberOfSockets) + ", we should have 2, one for accepting and one for data transfer. Will not transmit.")
            return -1
        # Simplification: We will send to the FIRST open connection, even we would have more connections open. This is
        # ok, because in our use case we have exactly one client.
        # Improvement: Instead of using the first (oldest(?)) connection, lets use the last. This helps for the case, that one
        # connection has crashed and the charger makes a new connection.
        totalsent = 0
        MSGLEN = len(txMessage)
        while totalsent < MSGLEN:
            sent = self.read_list[numberOfSockets-1].send(txMessage[totalsent:])
            if sent == 0:
                self.addToTrace("socket connection broken")
                return -1
            totalsent = totalsent + sent
        return 0 # success
        
    def mainfunction(self):
        # The select() function will block until one of the socket states has changed.
        # We specify a timeout, to be able to run it in the main loop.
        timeout_s = 0.05 # 50ms
        readable, writable, errored = select.select(self.read_list, [], [], timeout_s)
        for s in readable:
            if s is self.ourSocket:
                # We received a connection request at ourSocket.
                # -> we create a new socket (named client_socket) for handling this connection.
                client_socket, address = self.ourSocket.accept()
                # and we append this new socket to the list of sockets, which in the next loop will be handled by the select.
                self.read_list.append(client_socket)
                self.addToTrace("Connection from " + str(address))
                self.callbackStateNotification(2) # inform the higher level state machines, that the connection is established.
            else:
                # It is not the "listener socket", it is an above created "client socket" for talking with a client.
                # Let's take the data from it:
                try:
                    data = s.recv(1024)
                except:
                    # The client closed the connection in the meanwhile.
                    #print("The client closed the connection in the meanwhile.")
                    data = None
                if data:
                    # print("received data:", data)
                    self.rxData = data
                else:
                    self.addToTrace("connection closed")
                    s.close()
                    self.callbackStateNotification(0) # inform the higher level state machines, that the connection is gone.
                    try:
                        self.read_list.remove(s)
                    except:
                        pass




def testServerSocket():
    print("Testing the pyPlcTcpServerSocket...")
    s = pyPlcTcpServerSocket()
    print("Press Ctrl-Break for aborting")
    nLoops = 0
    while True:
        s.mainfunction()
        nLoops+=1
        if ((nLoops % 10)==0):
            print(str(nLoops) + " loops")
            if (s.isRxDataAvailable()):
                d = s.getRxData()
                print("received " + str(d))
                msg = "ok, you sent " + str(d)
                print("responding " + msg)
                s.transmit(bytes(msg, "utf-8"))
        if ((nLoops % 50)==0):
            print("trying to send something else")
            msg = "ok, something else..."
            s.transmit(bytes(msg, "utf-8"))
            

def testClientSocket():
    print("Testing the pyPlcTcpClientSocket...")
    c = pyPlcTcpClientSocket()
    #c.connect('fe80::e0ad:99ac:52eb:85d3', 15118)
    #c.connect('fe80::e0ad:99ac:52eb:9999', 15118)
    #c.connect('localhost', 15118)
    c.connect('fe80::407d:89f9:f6c2:6ee0', 15118)
    print("connected="+str(c.isConnected))
    if (c.isConnected):
        print("sending something to the server")
        c.transmit(bytes("Test", "utf-8"))
        for i in range(0, 10):
            print("waiting 1s")
            time.sleep(1)
            if (c.isRxDataAvailable()):
                d = c.getRxData()
                print("received " + str(d))
            if ((i % 3)==0):
                print("sending something to the server")
                c.transmit(bytes("Test", "utf-8"))
            
    print("end")

def testExtra():
    print("testExtra")
    #findLinkLocalIpv6Address()
    

if __name__ == "__main__":
    print("Testing pyPlcTcpSocket.py....")
    
    if (len(sys.argv) == 1):
        print("Use command line argument c for clientSocket or s for serverSocket")
        exit()
    if (sys.argv[1] == "c"):
        testClientSocket()
        exit()
    if (sys.argv[1] == "s"):
        testServerSocket()
        exit()
    if (sys.argv[1] == "x"):
        testExtra()
        exit()
    print("Use command line argument c for clientSocket or s for serverSocket")
