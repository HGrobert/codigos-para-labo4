ÚLTIMOS RESULTADOS/AJUSTES
OSCILOSCOPIO

<img width="1200" height="600" alt="Mediciones y ajuste con osciloscopio" src="https://github.com/user-attachments/assets/3663c519-43dd-4cab-a2d9-1add70bf7b64" />
LOCKIN

<img width="637" height="603" alt="Solo mediciones lockin" src="https://github.com/user-attachments/assets/ed8ccf7a-8eb8-4d59-bec0-0d5f942fe9ec" />

Una pequeña guia de mis archivos:

Todos los scripts de Automatización son los que usamos en el laboratorio para medir...

La carpeta de datos contiene todo lo que hemos medido para el experimento PZT, barrido en frecuencia usando es osci y el lockin.

Lo importante de la carpeta 'mediciones-osciloscopio' es el archivo grafico_barrido_noAutomatico.py,
que es el que contiene la figura de datos y ajuste de transferencia y fase de las señales que medimos con el osciloscopio.

Lo importante de la carpeta 'mediciones-lockin' es el único archivo con código, no hay secreto con eso. Aun no tiene los ajustes
de trasferencia y fase... También falta depurar teóricamente en qué variable (o mezcla de ellas) está guardada la información 
física de la la transferencia (me refiero a si está en R, X, Y o alguna combinación). La fase ya sabemos que la medimos perfectamente
y la información se guardó en la variable theta.
