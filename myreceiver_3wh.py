#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from socket import *
import sys
import os
import math
import time

import random
#recibe el nombre y numero de puerto al que conectarse
serverIP=""
serverPort=int(sys.argv[2])

serverSocket=socket(AF_INET,SOCK_DGRAM)
serverSocket.bind((serverIP,serverPort))
serverSocket.settimeout(2)
print "Ready to serve"


#ack inicial a recibir
ack = 0


endoffile = False
lastpktreceived = time.time()	
starttime = time.time()

#############################################################################
#
# ESTABLECER CONEXION
#
#############################################################################

retries = 0

retry_open=0
retry_close=0


#SYN-ACK
receiver_conectado=False

while True:
	#intenta recibir el syn del cliente
	try:
		data_client, address = serverSocket.recvfrom(4096)
	except:
		retry_open+=1
		if retry_open>10:
			print "no se pudo establecer la conexion"
			exit(0)
		continue
	#si corresponde a un syn, se confirma
	if data_client:
		(filename, total_size, nextSeqnum_con, tipo_ack, syn)= data_client.split("|||")
		if tipo_ack!="0" or syn!="1":
			retry_open+=1
			continue
	
		ack_server = 1
		data_server = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum_con)+ "|||"+str(0)+"|||"+str(1)
		print "Recibi SYN desde cliente"
		serverSocket.sendto(data_server, address)

	#se intenta recibir el ack para iniciar la conexion
	while True:
		try:
			data_client, address = serverSocket.recvfrom(4096)
		except:
			retry_open+=1
			if retry_open>10:
				print "no se pudo establecer la conexion"
				exit(0)
			continue
			
		if data_client:
			(filename, total_size, nextSeqnum_con, tipo_ack, syn)= data_client.split("|||")
			if (tipo_ack!="0" or syn!="0"):
				retry_open+=1
				continue
			receiver_conectado=True
			break
	if receiver_conectado==True:
		print "Recibi ACK desde cliente"
		print "Conexion establecida"
		break


#se comunican el numero de secuencia en este paso
total_seq_numbers=int(nextSeqnum_con)

#abre el archivo de salida
f = open("output_"+filename, "wb")
	
while receiver_conectado:
	#recibe los datos
	try:
		packet,clientAddress= serverSocket.recvfrom(4096)
	except:
		retries+=1
		if retries>10:
			print "conexion terminada por exceso de re-intentos"
			break
		continue
	
	
	###################################################################################
	#
	# TERMINAR LA CONEXION SI SE RECIBE INDICADOR DE TERMINO DE CONEXION
	#
	###################################################################################
	#Termino conexion
	if packet.split("|||")[3]=="0":
		(file_name, total_size, nextSeqnum, ack_disconnection,fin) = packet.split("|||")
		if fin=="1" and ack_disconnection=="0": #Recibe ack de cierre
			#Manda ack de cierre
			while True:
				ack_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+ str(1)
				serverSocket.sendto(ack_toclose, clientAddress)
				#Manda fin de cierre
				fin_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(1)+"|||"+ str(1)
				serverSocket.sendto(fin_toclose, clientAddress)
				
				#recibe ack de cierre
				try:
					packet,clientAddress= serverSocket.recvfrom(4096)
				except:
					retry_close+=1
					if retry_close>10:
						print "Se fuerza el cierre de la conexion"
						serverSocket.close()
						receiver_conectado=False
						break
					continue
					
				(file_name, total_size, nextSeqnum, ack_disconnection,fin) = packet.split("|||")
				if fin=="1" and ack_disconnection=="0":
					serverSocket.close() #cerrar conexion con el cliente
					receiver_conectado=False
					print "Receiver cerrado"
					break
			break
	####################################################################################
	####################################################################################
	####################################################################################
	
	
	(file_name, total_size, nextSeqnum, isData, data) = packet.split("|||")
	
	#si recibo datos, valido que sea igual al ack esperado
	if str(nextSeqnum) == str(ack):
		serverSocket.sendto(str(ack),clientAddress)
		ack = (ack + 1)%total_seq_numbers
		f.write(data)
		retries=0
	
		
f.close()
