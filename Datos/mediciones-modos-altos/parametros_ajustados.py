import numpy as np
import matplotlib.pyplot as plt

fs = np.array([50096.113, 150156.427, 248286.690, 349165.877])
fp = np.array([50284.052, 150220.160, 248323.463, 349193.664])

R = np.array([11100, 19730, 33180, 81300]) # en ohms
errorR = np.array([390, 560, 700, 2400]) 

L = np.array([545.77, 759.352, 1010.205, 977.52]) # en henrrys
errorL = np.array([0.44, 0.090, 0.041, 0.15]) 

C = np.array([0.018, 0.00148, 0.000407, 0.000213]) * 1e-15 # faradios
errorC = np.array([0.015, 0.00018, 0.000017, 0.000032]) * 1e-15

C2 = np.array([2.4602, 1.7425, 1.3731, 1.3353]) * 1e-12 
errorC2 = np.array([0.0023, 0.0026, 0.0029, 0.0093]) * 1e-12

Cr = np.array([137.7, 193.56, 149.50, 148.1]) * 1e-12 
errorCr = np.array([1.0, 0.94, 0.68, 1.3]) * 1e-12

fp_c = fs * np.sqrt(1 + ((L*C)/C2))
error_fp_c = (fs/(2*np.sqrt(1 + ((L*C)/C2))))*np.sqrt(((C*errorL)/C2)**2 + ((errorC * L)/C2)**2 +((L*C*errorC2)/C2**2)**2)
diferencia = fp - fs
print(fs)
for i in range(len(fs)-1):
    tamaño = fs[i+1] - fs[i]
    print(tamaño)
    
plt.errorbar(fp, fp_c, yerr=error_fp_c, fmt='o', color='blue', markersize = 4, capsize = 3, label = 'comparación')
plt.xlabel('f_p [Hz]')
plt.ylabel('f_{p,c} [Hz]')
plt.title('Comparación de frecuencias')
plt.legend()
#plt.show()