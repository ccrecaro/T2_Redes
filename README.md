# T2_Redes
Para correr alguno de los casos se utiliza

- myreceiver: python myreceiver_XX.py [port]
- mysender: python mysender_XX.py [ip] [port] [filename]

donde XX debe ser reemplazo por 2wh para el caso de two way handshake o por 3wh.


Se usó un tamaño de ventana igual a 10 y el doble del tamaño de la ventana para la cantidad 
de números de secuencia, empezando desde el 0.

El enviador va imprimiendo en pantalla la ventana con los números de secuencia asociados 
al envío, e imprime el número de secuencia del elemento confirmado cada vez que recibe un ack. 

Para enviar el archivo por pedazos, y para establecer y terminar la conexión, se envian mensajes 
de la forma

filename + "|||" + total size + "|||" + next Sequence number + "|||"+is data or ack + "|||" + DATA

se simula un encabezado separando campos con |||. La información siempre contiene 5 campos.


Los ack enviados por el servidor al cliente contiene solo el número de secuencia que se confirma.


Al iniciar la comunicación, el cliente le comunica al servidor la cantidad de números de secuencia
que utilizará.

El detalle completo de la implementación está en los archivos mysender_3wh.py y myreceiver_3wh.py
Las versiones de 2wh tienen menos comentarios pues son totalmente análogos.
