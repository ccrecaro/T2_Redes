# -*- coding: utf-8 -*-
import socket
import sys


# Parámetros para echar a correr el recibidor
if len(sys.argv) != 2:
    print "python receiver.py [PORTNUMBER]"

SW_IP = ""
SW_PORT = int(sys.argv[1])
# Armamos el socket
the_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# Asociamos el socket a la dirección y el puerto especificados
the_socket.bind((SW_IP,SW_PORT))

# Establecemos parámetros
buf = 1024
ack = 0
current_size = 0
percent = round(0,2)
can_receive = True

# Partimos con la secuencia inicial: aquí abrimos el archivo a descargar
while True:
    # Recibimos un string con los datos y la dirección del socket que mandó los datos
    data, address = the_socket.recvfrom(buf)

    if data:
        # Separamos los datos recibidos
        (file_name, total_size, seq) = data.split("|||")

        # Si recibimos los datos que esperabamos guardamos el archivo
        if str(seq) == str(ack):
            downloading_file = open("received_" + file_name,"wb")
            # Mostramos el avance
            print str(current_size) + " / " + str(total_size) + " (current size / total size), " + str(percent) + "%"
            # Actualizamos el ack
            ack = (ack + 1) % 2
            # Enviamos el ack
            the_socket.sendto(str(ack),address)
            break

# Seteamos un timeout (bloqueamos el socket después de 0.5s)
the_socket.settimeout(0.5)

# Contador de intentos
try_counter = 0

# Continuamos con la secuencia de descarga
while True:
    if can_receive:
        try:
            # Si en 10 intentos no funciona, salimos
            if try_counter == 10:
                print "error"
                break

            # Obtenemos los datos desde el socket
            data, address = the_socket.recvfrom(buf)

            # Si no me llegó nada, paramos
            if not data:
                break

            # Obtenemos el número de secuencia y los datos
            seq = data[len(data)-1]
            data = data[0:len(data)-1]

            # Si no es lo que esperabamos, descartamos
            if (str(ack) != str(seq)):
                print "seq is not equal to ack"
                continue
            # Si es, el socket queda tomado
            can_receive = False

        except:
            # Si ocurre un error avisamos y aumentamos el contador
            try_counter += 1
            print "timed out"
            the_socket.sendto(str(ack),address)


    if not can_receive:
        # Escribimos los datos en el archivo que abrimos antes
        downloading_file.write(data)
        
        # Actualizamos los parámetros
        current_size += len(data)
        percent = round(float(current_size) / float(total_size) * 100,2)
        
        # Actualizamos cómo va el envío
        print str(current_size) + " / " + str(total_size) + " (current size / total size), "  + str(percent) + "%"

        # Enviamos el ack para que el enviador sepa que los datos llegaron
        ack = (ack + 1) % 2
        try_counter = 0
        the_socket.sendto(str(ack),address)

        # Ahora podemos volver a recibir cosas
        can_receive = True

# Cerramos conexion y archivo
downloading_file.close()
the_socket.close()

# y, si no fallamos mucho, el archivo fue descargado :D
if try_counter < 10:
    print "File Downloaded"