# -*- coding: utf-8 -*-
import socket
import sys
import os
import time

# Parámetros para echar a correr el enviador
if len(sys.argv) != 4:
    print "python sender.py [IPADDRESS] [PORTNUMBER] [FILENAME]"
    sys.exit()

# Armamos el socket
the_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# Obtenemos el puerto y la IP
Server_IP = sys.argv[1]
Server_Port = int(sys.argv[2])

# Establecemos parámetros
buf = 1024
address = (Server_IP,Server_Port)
ack = 0

#Inicializamos ventana
base=0
seq = 0
window_size=7
window=[]

# Obtenemos los parámetros del archivo a enviar
file_name=sys.argv[3]
total_size = os.path.getsize(file_name)
current_size = 0
done = False
percent = round(0,2)
t_lastackrecieved = time.time()
tamano_pkg = 500

# Abrimos el archivo
sending_file = open(file_name,"rb")
data = sending_file.read(tamano_pkg)
# 'Codificamos' el header
header = str(file_name) + "|||" + str(tamano_pkg) + "|||" + str(seq)

# while para enviar datos
while True:
    #Ver si la ventana esta llena
    if (seq<base+window_size) and not done:
        sending_pkg=[]

        sending_pkg.append(header)
        sending_pkg.append(data)

        # Mandamos los datos donde corresponde
        the_socket.sendto(data,address)

        # Actualizamos el número de secuencia
        seq = (seq + 1) % window_size

        if not data:
            done=True
        window.append(sending_pkg)
        data = sending_file.read(tamano_pkg) #leer mas info
        # Seteamos un timeout (bloqueamos el socket después de 0.5s)
        the_socket.settimeout(0.5)

        # Contador de intentos
        try_counter = 0

    # Vemos que llegue el ACK
    while True:
        try:
            # Si en 10 intentos no funciona, salimos
            if try_counter == 10:
                print "error"
                break

            # Obtenemos la respuesta (estamos esperando un ACK)
            ack, address = the_socket.recvfrom(buf)

            # Si recibimos lo que esperabamos, actualizamos cómo va el envío
            if (str(ack) == str(seq)):
                print str(current_size) + " / " + str(total_size) + "(current size / total size), " + str(percent) + "%"

                # y pasamos a actualizar los parametros en (**)
                break

            # Si no, seguimos esperando el ack
            else:
                print "ack is not equal to seq"

        except:
            # Si ocurre un error avisamos y aumentamos el contador
            try_counter += 1
            print "timed out"
            the_socket.sendto(data,address)

    # Si en 10 intentos no funciona, salimos
    if try_counter == 10:
        break

    # (**) Actualizamos los parámetros :
    data = sending_file.read(buf-1)
    current_size += len(data)
    percent = round(float(current_size) / float(total_size) * 100,2)

    # Si no hay datos mandamos un string vacío y dejamos de enviar cosas
    if not data or done:
        the_socket.sendto("",address)
        break

    # Actualizamos los datos a enviar
    data += str(seq)

# Cerramos conexión y archivo
the_socket.close()
sending_file.close()