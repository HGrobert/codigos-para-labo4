import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("datos_recuperados.csv")

freq = df["Frecuencia"].to_numpy()
T = df["Transferencia"].to_numpy()

plt.figure(figsize = (6,6))
plt.scatter(freq, T)
plt.xlabel('frecuencia')
plt.ylabel('Transferencia')
plt.yscale('log')
#plt.xlim(48000, 51000)
plt.show()