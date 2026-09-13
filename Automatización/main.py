import pyvisa as visa
from clases_equipos import TDS1002B
from clases_equipos import AFG3021B
import numpy as np 
import matplotlib.pyplot as plt
import time as time
import pandas as pd
from config_equipos import *

osci = TDS1002B(osci)
fungen = AFG3021B(fungen)

freq = np.linspace(50100, 54000, 30)
T = np.zeros(len(freq))
all_frecuencias = []
all_tiempo = []
all_tiempo2 =[]
all_volt_entrada = []
all_volt_salida = []

for i in range(len(freq)):
        fungen.setFrequency(freq[i])
        escala = (1/freq[i])*0.4
        osci.set_time(escala)
        osci.set_channel(1, 500e-3)
        osci.set_channel(2, 500e-3)
        time.sleep(2)
        
        tiempo, volt_entrada = osci.read_data(channel = 1)
        tiempo2, volt_salida = osci.read_data(channel = 2)
        all_frecuencias.extend([freq[i]] * len(tiempo))
        all_tiempo.extend(tiempo)
        all_tiempo2.extend(tiempo2)
        all_volt_entrada.extend(volt_entrada)
        all_volt_salida.extend(volt_salida)
        df = pd.DataFrame({"Frecuencia": all_frecuencias,'Tiempo CH1':all_tiempo,'V1':all_volt_entrada, 'Tiempo CH2':all_tiempo2, 'V2':all_volt_salida})
        df.set_index(["Frecuencia", "Tiempo CH1", "Tiempo CH2"])

df.to_csv('octavo_Barrido_transferencia.csv', index=False)

