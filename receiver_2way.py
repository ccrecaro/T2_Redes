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
serverSocket.settimeout(10)


#initializes packet variables 
expectedseqnum=1
windowSize=7
ack = 0
#RECEIVES DATA
f = open("output", "wb")
endoffile = False
lastpktreceived = time.time()	
starttime = time.time()
retries = 0

#SYN-ACK
receiver_conectado=False
data_client, address = serverSocket.recvfrom(4096)
if data_client:
	(filename, total_size, nextSeqnum_con, tipo_ack, syn, ack_connection)= data_client.split("|||")
	while (tipo_ack!="0" or syn!="1" or ack_connection!="0"):
		retries+=1
		data_client, address = serverSocket.recvfrom(4096)
		(filename, total_size, nextSeqnum_con, tipo_ack, syn, ack_connection)= data_client.split("|||")
		if retries>10:
			break

	if retries<=10:
		retries=0
		ack_server = 1
		data_server = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum_con)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(1)
		print "Recibi SYN desde cliente"
		receiver_conectado=True
		serverSocket.sendto(data_server, address)
		print "Conexion establecida"
	

while receiver_conectado:
	try:
		packet,clientAddress= serverSocket.recvfrom(4096)
	except:
		retries+=1
		if retries>10:
			print "conexion terminada por exceso de re-intentos"
			break
		continue

	

	#Termino conexion
	if packet.split("|||")[3]=="0":
		(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
		if fin=="1": #Recibe ack de cierre
			#Manda ack de cierre
			ack_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(1)
			serverSocket.sendto(ack_toclose, clientAddress)
			#Manda fin de cierre
			fin_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(0)
			serverSocket.sendto(fin_toclose, clientAddress)
			
			#recibe ack de cierre
			packet,clientAddress= serverSocket.recvfrom(4096)
			(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
			if isData=="0" and ack_disconnection=="1":
				serverSocket.close() #cerrar conexion con el cliente
				print "Receiver cerrado"
				break

		


	
	(file_name, total_size, nextSeqnum, isData, data) = packet.split("|||")
	
	
	if str(nextSeqnum) == str(ack):
		serverSocket.sendto(str(ack),clientAddress)
		ack = (ack + 1) % (windowSize+1)
		f.write(data)
		retries=0
	
		
f.close()