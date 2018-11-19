from socket import *
import hashlib
import pickle
import sys
import os
import math
import time

#takes the port number as command line arguments
serverName=sys.argv[1]
serverPort=int(sys.argv[2])

#takes the file name as command line arguments
filename = ''.join(sys.argv[3])

#create client socket
clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.settimeout(0.001)

#initializes window variables (upper and lower window bounds, position of next seq number)
base=1
nextSeqnum=1
windowSize=7
window = []

#SENDS DATA
fileOpen= open(filename, 'rb') 
data = fileOpen.read(500)
done = False
lastackreceived = time.time()

address = (serverName,serverPort)

while not done or window:
#	check if the window is full	or EOF has reached
	if(nextSeqnum<base+windowSize) and not done:
#		create packet(seqnum,data,checksum)
		sndpkt = []
		sndpkt.append(nextSeqnum)
		sndpkt.append(data)
		h = hashlib.md5()
		h.update(pickle.dumps(sndpkt))
		sndpkt.append(h.digest())
#		send packet
		clientSocket.sendto(pickle.dumps(sndpkt), address)
		print "Sent data", nextSeqnum
#		increment variable nextSeqnum
		nextSeqnum = nextSeqnum + 1
#		check if EOF has reached
		if(not data):
			done = True
#		append packet to window
		window.append(sndpkt)
#		read more data
		data = fileOpen.read(500)

#RECEIPT OF AN ACK
	try:
		packet,serverAddress = clientSocket.recvfrom(4096)
		rcvpkt = []
		rcvpkt = pickle.loads(packet)
#		check value of checksum received (c) against checksum calculated (h) 
		c = rcvpkt[-1]
		del rcvpkt[-1]
		h = hashlib.md5()
		h.update(pickle.dumps(rcvpkt))
		if c == h.digest():
			print "Received ack for", rcvpkt[0]
#			slide window and reset timer
			while rcvpkt[0]>base and window:
				lastackreceived = time.time()
				del window[0]
				base = base + 1
		else:
			print "error detected"
#TIMEOUT
	except:
		if(time.time()-lastackreceived>0.01):
			for i in window:
				clientSocket.sendto(pickle.dumps(i), address)

fileOpen.close()

print "connection closed"    
clientSocket.close()