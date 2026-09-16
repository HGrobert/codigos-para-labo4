ÚLTIMOS RESULTADOS/AJUSTES <br>
OSCILOSCOPIO <br>

<img width="4753" height="2360" alt="grafico_osciloscopio" src="https://github.com/user-attachments/assets/bdce1b9b-0f7a-4315-ac68-e9fba6a5afb0" /><br>
LOCKIN <br>
<img width="1280" height="612" alt="Comparativa de modelos" src="https://github.com/user-attachments/assets/2a038b14-37c1-46a0-80d5-a97ad8cc0446" /><br>

Una pequeña guia de mis archivos:

Todos los scripts de Automatización son los que usamos en el laboratorio para medir...

La carpeta de datos contiene todo lo que hemos medido para el experimento PZT, barrido en frecuencia usando es osci y el lockin.

Lo importante de la carpeta 'mediciones-osciloscopio' es el archivo grafico_barrido_noAutomatico.py,
que es el que contiene la figura de datos y ajuste de transferencia y fase de las señales que medimos con el osciloscopio.

Lo importante de la carpeta 'mediciones-lockin' es el único archivo con código, no hay secreto con eso. Aun no tiene los ajustes
de trasferencia y fase... También falta depurar teóricamente en qué variable (o mezcla de ellas) está guardada la información 
física de la la transferencia (me refiero a si está en R, X, Y o alguna combinación). La fase ya sabemos que la medimos perfectamente
y la información se guardó en la variable theta.
