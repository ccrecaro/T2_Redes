#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from socket import *
import sys
import os
import math
import time
import numpy as np

ti = time.time()


#takes the port number as command line arguments
serverName=sys.argv[1]
serverPort=int(sys.argv[2])
address = (serverName,serverPort)


#takes the file name as command line arguments
filename = ''.join(sys.argv[3])

#create client socket
clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.settimeout(2)


#initializes window variables (upper and lower window bounds, position of next seq number)
nextSeqnum=0
windowSize=10
total_seq_numbers = 2*windowSize

#cantidad de datos a enviar
sentSize = 0

#buffer circular para datos
window = []
#buffer circular con los numeros de secuencia enviados
seqNums = np.zeros(windowSize,int)

#arreglo de tiempos para el algoritmo de Karn
tiempos = np.ones(windowSize,float)
alpha = 1.0/8.0
beta = 1.0/4.0

#timeout inicial
time_out = 1
estimatedRTT = time_out
devRTT = 0

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
	nextSeqnum = (nextSeqnum + 1)%total_seq_numbers
	sentSize+=1
	if(not data):
		done=True
		break
	last_sent = i
	

###############################################################
###############################################################
#
# AQUI HAY QUE HACER LO DE INICIAR LA CONEXION
#
###############################################################
###############################################################
sender_conectado=False
# Inicio conexion
# Envio SYN
syn = 1
ack = 0

retry_open = 0
retry_close = 0

while True:
	data_connect_toServer = str(filename)+"|||"+str(total_size)+"|||"+str(total_seq_numbers)+"|||"+str(0)+"|||"+str(syn)
	clientSocket.sendto(data_connect_toServer, address)

	# Recibo SYN-ACK
	try:
		data_server, address = clientSocket.recvfrom(4096)
	except:
		retry_open+=1
		if retry_open>10:
			print "no se pudo establecer la conexion"
			exit(0)
		continue
	(filename, total_size, nextSeqnum_con, tipo_ack, syn)= data_server.split("|||")
	if data_server:	
		if tipo_ack=="0" and syn=="1" and str(total_seq_numbers)==str(nextSeqnum_con):
			print "Recibi SYN-ACK"
			sender_conectado=True
			
	
	if sender_conectado==True:
		break
	retry_open+=1
	if retry_open>10:
		print "no se pudo establecer la conexion"
		exit(0)
###############################################################
###############################################################
###############################################################
###############################################################

retransmisiones = 0
end_of_sending = -1

while sender_conectado:
	
	#si se excede el timeout
	if time.time()-lastackreceived>time_out:
		#si ya se envio muchas veces
		if retransmisiones==10:
			print "terminado por exceso de re-transmisiones"
			break
		#sino, envia la ventana
		print "\nsending window\n"
		new_tiempos = []
		new_window = []
		new_seq = []
		
		for j in range( (last_sent+1), (last_sent+1+sentSize) ):
			tiempos[j%windowSize]=time.time()
			clientSocket.sendto(window[j%windowSize], address)
			new_tiempos.append(tiempos[j%windowSize])
			new_window.append(window[j%windowSize])
			new_seq.append(seqNums[j%windowSize])
			print "package %d sent" %(seqNums[j%windowSize])
		
		if sentSize<windowSize and done==True:
			end_of_sending=seqNums[j%windowSize]
		window=new_window
		tiempos=new_tiempos
		seqNums=new_seq
		lastacked=0
		last_sent=-1

		#si envie menos elementos que el total de la ventana, es porque se termino el archivo
		
		retransmisiones+=1
		lastackreceived=time.time()

	else:
		#se lee paquete de entrada
		try:
			packet,serverAddress = clientSocket.recvfrom(4096)
		except:
			continue
		packet = int(str(packet))
		tiempo_recibido = time.time()
		#es un ack
		print "received ack for %d " %(packet)		
		
		#se busca acumulativamente el elemento confirmado
		for i in range(0,len(seqNums)):
			if seqNums[i]==packet:
				updateto=i
				break
				
		#re-calcular el timeout usando algoritmo de Karn
		if retransmisiones<=1:
			sampleRTT = tiempo_recibido-tiempos[updateto]
			estimatedRTT = (1.0 - alpha)*estimatedRTT + alpha*sampleRTT
			devRTT = (1-beta)*devRTT + beta*abs(sampleRTT-estimatedRTT)
			time_out = estimatedRTT + 4*devRTT
			
			
			
		#si era el ultimo enviado termina
		###############################################################
		###############################################################
		#
		# AQUI HAY QUE HACER LO DE TERMINAR LA CONEXION, EN EL IF
		#
		###############################################################
		###############################################################
		if done==True and packet==end_of_sending:
			#Envia fin de cierre
			while True:
				fin_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(0)
				clientSocket.sendto(fin_toclose, serverAddress)

				#Recibe ack de cierre
				try:
					packet,senderAddress= clientSocket.recvfrom(4096)
				except:
					retry_close+=1
					if retry_close>10:
						clientSocket.close()
						print "Se fuerza el cierre de la conexion"
						sender_conectado=False
						break
					continue
					

				(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
				if isData=="0" and ack_disconnection=="1":
					while True:
						try:
							packet,senderAddress= clientSocket.recvfrom(4096)
						except:
							retry_close+=1
							if retry_close>10:
								clientSocket.close()
								print "Se fuerza el cierre de la conexion"
								sender_conectado=False
								break
							continue

						(file_name, total_size, nextSeqnum, isData, fin, ack_disconnection) = packet.split("|||")
						if isData=="0" and fin=="1":
							ack_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+str(1)+"|||"+ str(1)
							clientSocket.sendto(ack_toclose, serverAddress)

							clientSocket.close()
							print "\n\nfinished\n\n"
							print "Sender cerrado"
							break
						else:
							continue
				else:
					retry_close+=1
					if retry_close>10:
						clientSocket.close()
						print "Se fuerza el cierre de la conexion"
						sender_conectado=False
						break
						
				break
			break
		###############################################################
		###############################################################
		###############################################################
		###############################################################
		
		
		
			
		
		
		#actualizo el buffer circular en funcion del ack recibido
		for i in range(lastacked,updateto+1):
			data = fileOpen.read(buf_read)
			window[i]= str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+"|||"+str(1)+"|||"+str(data)
			seqNums[i]=nextSeqnum
			nextSeqnum = (nextSeqnum + 1)%total_seq_numbers
			#si se acaba el archivo
			if(not data):
				done=True
				sentSize-=1
				last_sent+=1
				break
			#no se acaba el archivo, asi que sigo sumando	
			last_sent+=1
			retransmisiones=0
		lastacked=updateto+1

		
		#si me confirman todos los elementos del buffer:					
		if updateto==windowSize-1:
			lastacked=0
			lastackreceived=0
			retransmisiones=0

				

fileOpen.close()

tf = time.time()

print "tiempo total para el envio = %.5f" %(tf-ti)
