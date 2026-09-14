import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ARCHIVOS = ['barrido_lockin', 'barrido_lockin_fino', 'barrido_lockin_fino_fino']

# Creamos una figura con 2 subplots verticales (uno para X o Magnitud, otro para Fase)
fig, (ax_transf, ax_fase) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

for nombre in ARCHIVOS:
    df = pd.read_csv(f"{nombre}.csv")
    
    frec = df["Frecuencia"].values
    transf = abs(df['R'].values)*np.sqrt(2)
    fase = df['theta'].values

    # Graficar Componente X / Transferencia
    ax_transf.scatter(frec, transf, marker=".", color = 'b')
    
    # Graficar Fase (eje Y lineal para aceptar valores negativos)
    ax_fase.scatter(frec, fase, marker=".", color = 'r')

# Formato del gráfico de Transferencia / X
ax_transf.set_yscale("log")
ax_transf.set_ylabel("T (V)")
ax_transf.grid(True, which="both", linestyle="--")

# Formato del gráfico de Fase
ax_fase.set_ylabel("Fase θ (grados o rad)")
ax_fase.set_xlabel("Frecuencia (Hz)")
ax_fase.grid(True, which="both", linestyle="--")

plt.suptitle("Comparación de barridos con Lock-in")
plt.tight_layout()
plt.show()