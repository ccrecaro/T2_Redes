#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from socket import *
import hashlib
import pickle
import sys
import os
import math
import time
import numpy as np
import random
#takes the port number as command line arguments
serverName=sys.argv[1]
serverPort=int(sys.argv[2])
address = (serverName,serverPort)


#takes the file name as command line arguments
filename = ''.join(sys.argv[3])

#create client socket
clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.settimeout(0.01)


#initializes window variables (upper and lower window bounds, position of next seq number)
nextSeqnum=0
windowSize=7

#cantidad de datos a enviar
sentSize = 0

#buffer circular para datos
window = []
#buffer circular con los numeros de secuencia enviados
seqNums = np.zeros(windowSize,int)

time_out = 2

#tamaño a leer del archivo de entrada
buf_read = 500

#para validar que se terminó
done = False

#ultimo elemento confirmado
lastacked = 0

#hora del ultimo elemento confirmado
lastackreceived = 0

#parametros del archivo de entrada
total_size = os.path.getsize(filename)
fileOpen= open(filename, 'rb') 

#indice del ultimo elemento enviado
last_sent = -1

#se leen los elementos hasta que se llene una venta o termine el archivo
for i in range(0,windowSize):
	data = fileOpen.read(buf_read)
	window.append( str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+"|||"+str(1)+"|||"+str(data))
	seqNums[i]=nextSeqnum
	nextSeqnum = (nextSeqnum + 1)%(windowSize+1)
	sentSize+=1
	if(not data):
		done=True
		break
	last_sent = i
	
sender_conectado=False
# Inicio conexion
# Envio SYN
syn = 1
ack = 0
data_connect_toServer = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+"|||"+str(0)+"|||"+str(syn)+"|||"+str(ack)
clientSocket.sendto(data_connect_toServer, address)

# Recibo SYN-ACK
data_server, address = clientSocket.recvfrom(4096)
(filename, total_size, nextSeqnum_con, tipo_ack, syn, ack_connection)= data_server.split("|||")
if data_server:	
	if tipo_ack=="0" and ack_connection=="1" and syn=="1":
		print "Recibi SYN-ACK"
		sender_conectado=True




retransmisiones = 0
end_of_sending = -1

while sender_conectado:
	
	#si se excede el timeout
	if time.time()-lastackreceived>time_out:
		#si ya se envio muchas veces
		if retransmisiones==10:
			break
		#sino, envia la ventana
		print "sending window"
		for i in range( (last_sent+1), (last_sent+1+sentSize) ):
			clientSocket.sendto(window[i%windowSize], address)
			print "package %d sent" %(seqNums[i%windowSize])
		#si envie menos elementos que el total de la ventana, es porque se termino el archivo
		if sentSize<windowSize and done==True:
			end_of_sending=seqNums[i%windowSize]
		retransmisiones+=1
		lastackreceived=time.time()

	else:
		#se lee paquete de entrada
		try:
			packet,serverAddress = clientSocket.recvfrom(4096)
		except:
			continue
		packet = int(str(packet))
		#es un ack
		print "received ack for %d " %(packet)
		
		#se busca acumulativamente el elemento confirmado
		for i in range(0,len(seqNums)):
			if seqNums[i]==packet:
				updateto=i
				break
		
		#si era el ultimo enviado termina
		
		#Termino conexion
		if done==True and packet==end_of_sending:
			#Envia fin de cierre
			fin_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(0)
			clientSocket.sendto(fin_toclose, serverAddress)

			#Recibe ack de cierre
			packet,senderAddress= clientSocket.recvfrom(4096)
			(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
			if isData=="0" and ack_disconnection=="1":
				# Recibe fin de cierre
				packet,senderAddress= clientSocket.recvfrom(4096)
				(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
				if isData=="0" and fin=="1":
					ack_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(1)
					clientSocket.sendto(ack_toclose, serverAddress)

					#Cierro conexion
					clientSocket.close()
					print "\n\nfinished\n\n"
					print "Sender cerrado"
					break




		
		#actualizo el buffer circular en funcion del ack recibido
		for i in range(lastacked,updateto+1):
			data = fileOpen.read(buf_read)
			window[i]= str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+"|||"+str(1)+"|||"+str(data)
			seqNums[i]=nextSeqnum
			nextSeqnum = (nextSeqnum + 1)%(windowSize+1)
			#si se acaba el archivo
			if(not data):
				done=True
				sentSize-=1
				last_sent+=1
				break
			#no se acaba el archivo, asi que sigo sumando	
			last_sent+=1
				
		#si me confirman todos los elementos del buffer:					
		lastacked=updateto+1
		if updateto==windowSize-1:
			lastacked=0
			lastackreceived=0
			retransmisiones=0

				

fileOpen.close()

print "connection closed"    
clientSocket.close()
