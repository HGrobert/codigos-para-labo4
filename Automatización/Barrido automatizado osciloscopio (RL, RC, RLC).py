import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd

rm = visa.ResourceManager()

resource_name_osc = 'USB0::0xF4EC::0xEE38::SDG1XCA4161035::INSTR'

fungen = rm.open_resource(resource_name_osc)

resource_name_osc= 'USB0::0x0699::0x03C4::C041039::INSTR'

osci = rm.open_resource(resource_name_osc)

osci.write('DAT:ENC RPB')
osci.write('DAT:WID 1')
osci.write('SEL:CH1 ON')
osci.write('SEL:CH2 ON') 
osci.write('MEASU:MEAS2:TYPe PK2 ; MEASU:MEAS2:SOU CH1')
osci.write('MEASU:MEAS3:TYPe PK2 ; MEASU:MEAS2:SOU CH1')
osci.write('MEASU:MEAS4:TYPe PHA ; MEASU:MEAS4:SOU1 CH1 ; MEASU:MEAS4:SOU2 CH2')
osci.write('DAT:SOU CH1')
osci.write('DAT:SOU CH2')

datos = []
#frecuencias del barrido
frecuencias = np.logspace(2, 5, 20)
 
# 2. BARRIDO
for f in frecuencias:
    escala = (1/f) * 0.4

    osci.write(f"HORizontal:MAIn:SCAle {escala:.2E}")
    osci.write("CH1:SCAle 2V") #Ver para cada frecuencia la mejor escala
    osci.write("CH2:SCAle 2V") #Ver para cada frecuencia la mejor escala
    
    time.sleep(1)
    
    fungen.write(f'C2:BSWV FRQ,{f}')
    
    time.sleep(1)
    vin = float(osci.query('MEASU:MEAS2:VAL?'))
    time.sleep(0.1)
    vout = float(osci.query('MEASU:MEAS3:VAL?'))
    time.sleep(0.1)
    fase = float(osci.query('MEASU:MEAS4:VAL?'))
    time.sleep(0.1)
    escalat = float(osci.query('HOR:MAIN:SCA?'))
    time.sleep(0.1)
    escalavin =float(osci.query('CH1:SCAle?'))
    time.sleep(0.1)
    escalavout = float(osci.query('CH2:SCAle?'))
    time.sleep(0.1)
    
    fila = {
            'Frecuencia_Hz': f,
            'Vin_Vpp': vin,
            'Vout_Vpp': vout,
            'Fase_Deg': fase,
            'Escala_T': escalat,
            'Escala_V1': escalavin,
            'Escala_V2': escalavout    
        }
    datos.append(fila)
    print(f"Freq: {f:.1f}Hz | Vout: {fila['Vout_Vpp']:.2f}V| Vin: {fila['Vin_Vpp']:.2f}V fase: {fila['Fase_Deg']:.2f}grad \n", end='')


df = pd.DataFrame(datos)
df.to_csv('bode_autoset_hibrido_Rl_pasaaltos.csv', index=False)
print("\n\n--- Medición terminada. Archivo guardado ---")

plt.figure(figsize = (6,5))
plt.plot(df['Frecuencia_Hz'], (df['Vout_Vpp'] / df['Vin_Vpp']))
plt.xlabel('Frecuencias')
plt.xscale('log')
plt.ylabel('Transferencia')
plt.show()
