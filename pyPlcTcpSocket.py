
# Server on a non-blocking socket
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

class pyPlcClientSocket():
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.isConnected = False
        
    def connect(self, host, port):
        try:
            self.sock.connect((host, port))
            self.isConnected = True
        except:
            self.isConnected = False
            
    def mysend(self, msg):
        totalsent = 0
        MSGLEN = len(msg)
        while (totalsent < MSGLEN) and (self.isConnected):
            try:
                sent = self.sock.send(msg[totalsent:])
                if sent == 0:
                    self.isConnected = False
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent
            except:
                self.isConnected = False
    def isRxDataAvailable(self):
        # todo
        # ... = self.sock.recv(..., 2048))
        return 0

class pyPlcTcpServerSocket():
    def __init__(self):
        self.ipAdress = 'fe80::e0ad:99ac:52eb:85d3'
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
        print("pyPlcTcpSocket listening on port " + str(self.tcpPort))
        self.read_list = [self.ourSocket]
        self.rxData = []
        
    def isRxDataAvailable(self):
        return (len(self.rxData)>0)
        
    def getRxData(self):
        # provides the received data, and clears the receive buffer
        d = self.rxData
        self.rxData = []
        return d
        
    def transmit(self, txMessage):
        numberOfSockets = len(self.read_list)
        if (numberOfSockets!=2):
            print("we have " + str(numberOfSockets) + ", we should have 2, one for accepting and one for data transfer. Will not transmit.")
            return -1
        totalsent = 0
        MSGLEN = len(txMessage)
        while totalsent < MSGLEN:
            sent = self.read_list[1].send(txMessage[totalsent:])
            if sent == 0:
                print("socket connection broken")
                return -1
            totalsent = totalsent + sent
        return 0
        
    def mainfunction(self):
        # The select() function will block until one of the socket states has changed.
        # We specify a timeout, to be able to run it in the main loop.
        # print("before select")
        timeout_s = 0.05 # 50ms
        readable, writable, errored = select.select(self.read_list, [], [], timeout_s)
        for s in readable:
            if s is self.ourSocket:
                # We received a connection request at ourSocket.
                # -> we create a new socket (named client_socket) for handling this connection.
                client_socket, address = self.ourSocket.accept()
                # and we append this new socket to the list of sockets, which in the next loop will be handled by the select.
                self.read_list.append(client_socket)
                print("Connection from", address)
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
                    print("received data:", data)
                    self.rxData = data
                else:
                    print("connection closed")
                    s.close()
                    self.read_list.remove(s)    




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
                s.transmit(bytes(msg, "utf-8"))

def testClientSocket():
    print("Testing the pyPlcTcpClientSocket...")
    c = pyPlcClientSocket()
    c.connect('fe80::e0ad:99ac:52eb:85d3', 15118)
    print("connected="+str(c.isConnected))
    print("sending something to the server")
    c.mysend(bytes("Test", "utf-8"))
    print("waiting 3s")
    time.sleep(3)
    if (c.isRxDataAvailable()):
                d = c.getRxData()
                print("received " + str(d))
    print("end")


if __name__ == "__main__":
    if (len(sys.argv) == 1):
        print("Use command line argument c for clientSocket or s for serverSocket")
        exit()
    if (sys.argv[1] == "c"):
        testClientSocket()
        exit()
    if (sys.argv[1] == "s"):
        testServerSocket()
        exit()
    print("Use command line argument c for clientSocket or s for serverSocket")
