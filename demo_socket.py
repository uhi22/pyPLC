
# explanation of socket handling:
# https://realpython.com/python-sockets/
#

import socket
import select



print("Press Ctrl-Break for aborting")

TCP_IP = 'fe80::e0ad:99ac:52eb:85d3'
TCP_PORT = 15118 # The port for CCS
BUFFER_SIZE = 1024  # Normally 1024

ourSocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
ourSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

ourSocket.bind((TCP_IP, TCP_PORT))
ourSocket.listen(1)
print("listening on port " + str(TCP_PORT))

# example from https://stackoverflow.com/questions/5308080/python-socket-accept-nonblocking
read_list = [ourSocket]
while True:
    # The select() function will block until one of the socket states has changed.
    # We specify a timeout, to be able to run it in the main loop.
    print("before select")
    readable, writable, errored = select.select(read_list, [], [], 0.5)
    for s in readable:
        if s is ourSocket:
            client_socket, address = ourSocket.accept()
            read_list.append(client_socket)
            print("Connection from", address)
        else:
            data = s.recv(1024)
            if data:
                print("received data:", data)
            else:
                print("connection closed")
                s.close()
                read_list.remove(s)