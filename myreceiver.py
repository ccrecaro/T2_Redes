#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from socket import *
import pickle
import hashlib
import sys
import os
import math
import time

import random
#takes the port number as command line arguments and create server socket
serverIP=""
serverPort=int(sys.argv[2])

serverSocket=socket(AF_INET,SOCK_DGRAM)
serverSocket.bind((serverIP,serverPort))
serverSocket.settimeout(2)
print "Ready to serve"

#initializes packet variables 
expectedseqnum=1
windowSize=7;
ack = 0
#RECEIVES DATA
f = open("output", "wb")
endoffile = False
lastpktreceived = time.time()	
starttime = time.time()

#############################################################################
#
# ESTABLECER CONEXION
#
#############################################################################

retries = 0

while True:
	try:
		packet,clientAddress= serverSocket.recvfrom(4096)
	except:
		retries+=1
		if retries>10:
			print "conexion terminada por exceso de re-intentos"
			break
		continue
	
	#############################################################################
	#
	# TERMINAR LA CONEXION SI SE RECIBE INDICADOR DE TERMINO DE CONEXION
	#
	#############################################################################
	
	
	(file_name, total_size, nextSeqnum, isData, data) = packet.split("|||")
	
	
	if str(nextSeqnum) == str(ack):
		serverSocket.sendto(str(ack),clientAddress)
		ack = (ack + 1) % (windowSize+1)
		f.write(data)
		retries=0
	
		
f.close()
