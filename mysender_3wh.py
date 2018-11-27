#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from socket import *
import sys
import os
import math
import time
import numpy as np

#para medir el tiempo que toma el envío
ti = time.time()

#recibe el nombre y numero de puerto al que conectarse
serverName=sys.argv[1]
serverPort=int(sys.argv[2])
address = (serverName,serverPort)


#recibe como argumento también el nombre del archivo
filename = ''.join(sys.argv[3])

#crea el socket
clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.settimeout(2)


#inicializa los numeros de secuencia y el tamaño de ventana
nextSeqnum=0
windowSize=10
total_seq_numbers = 2*windowSize

#variable para determinar la cantidad de datos a enviar en una cierta iteracion
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
#se usa un header al estilo Ivana
for i in range(0,windowSize):
	data = fileOpen.read(buf_read)
	#el cuarto parámetro lo utilizamos para diferenciar aquellos mensajes con datos del documento enviado
	#y los que se usan a la hora de establecer la conexión.
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
# INICIAR LA CONEXION
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
	#envia el SYN y también la cantidad de numeros de secuencia a utilizar
	data_connect_toServer = str(filename)+"|||"+str(total_size)+"|||"+str(total_seq_numbers)+"|||"+str(0)+"|||"+str(syn)
	clientSocket.sendto(data_connect_toServer, address)

	#Recibo SYN-ACK
	try:
		data_server, address = clientSocket.recvfrom(4096)
	except:
		retry_open+=1
		if retry_open>10:
			print "no se pudo establecer la conexion"
			exit(0)
		continue
	(filename, total_size, nextSeqnum_con, tipo_ack, syn)= data_server.split("|||")
	#si corresponde al SYN-ACK se envia un ack 
	if data_server:	
		if tipo_ack=="0" and syn=="1" and str(total_seq_numbers)==str(nextSeqnum_con):
			print "Recibi SYN-ACK"
			data_connect_toServer2 = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum_con)+"|||"+str(0)+"|||"+str(0)
			clientSocket.sendto(data_connect_toServer2, address)
			print "ack enviado"
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
		
		#las variables new son para re-ordenar los buffer circulares
		#de tal forma que el primer elemento quede en el índice 0
		new_tiempos = []
		new_window = []
		new_seq = []
		#se re-ordena y se envia la nueva ventana
		for j in range( (last_sent+1), (last_sent+1+sentSize) ):
			tiempos[j%windowSize]=time.time()
			clientSocket.sendto(window[j%windowSize], address)
			new_tiempos.append(tiempos[j%windowSize])
			new_window.append(window[j%windowSize])
			new_seq.append(seqNums[j%windowSize])
			print "package %d sent" %(seqNums[j%windowSize])
		
		#si ya terminó de enviar
		if sentSize<windowSize and done==True:
			end_of_sending=seqNums[j%windowSize]
		#se prepara para una siguiente iteracion	
		window=new_window
		tiempos=new_tiempos
		seqNums=new_seq
		lastacked=0
		last_sent=-1
		retransmisiones+=1
		lastackreceived=time.time()

	else:
		#si no debo enviar, espero recibir acks
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
		# TERMINAR LA CONEXION
		#
		###############################################################
		###############################################################
		if done==True and packet==end_of_sending:
			#Envia fin de cierre
			while True:
				#se manda el fin de la conexion
				fin_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+ str(1)
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
					
				#recibe el fin por parte del servidor
				(file_name, total_size, nextSeqnum, isData, ack_disconnection) = packet.split("|||")
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

						(file_name, total_size, nextSeqnum, isData, ack_disconnection) = packet.split("|||")
						#confirma la recepcion del fin del servidor
						if isData=="1" and ack_disconnection=="1":
							ack_toclose = str(filename)+"|||"+str(total_size)+"|||"+str(nextSeqnum)+ "|||"+str(0)+"|||"+ str(1)
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
		
		
		

		#si no hay que terminar la conexion, actualizo el buffer circular en funcion del ack recibido
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

		#si me confirman todos los elementos del buffer, envio una nueva ventana:					
		if updateto==windowSize-1:
			lastacked=0
			lastackreceived=0
			retransmisiones=0

				

fileOpen.close()


tf = time.time()

print "tiempo total para el envio = %.5f" %(tf-ti)
