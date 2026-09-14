import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def modelo_log(f, R_ohm, L_H, C_pF, C2_pF, R2_val=10e3):
    R = R_ohm
    L = L_H
    C = C_pF * 1e-12
    C2 = C2_pF * 1e-12
    
    w = 2 * np.pi * f
    
    # Admitancias
    Y_m = 1.0 / (R + 1j * (w * L - 1.0 / (w * C)))
    Y_p = 1j * w * C2
    
    Y_pzt = Y_m + Y_p
    T = (R2_val * Y_pzt) / (1.0 + R2_val * Y_pzt)
    
    # Retornamos log10 para igualar el peso de residuos
    return np.log10(np.abs(T))

def modelo_fase(f, R_ohm, L_H, C_pF, C2_pF, R2_val=10e3):
    R = R_ohm
    L = L_H
    C = C_pF * 1e-12
    C2 = C2_pF * 1e-12
    
    w = 2 * np.pi * f
    
    # Admitancias
    Y_m = 1.0 / (R + 1j * (w * L - 1.0 / (w * C)))
    Y_p = 1j * w * C2
    
    Y_pzt = Y_m + Y_p
    T = (R2_val * Y_pzt) / (1.0 + R2_val * Y_pzt)
    
    # Retornamos la fase en radianes
    return np.angle(T)

# ============================================================
# 2. CARGA Y ESTIMACIÓN AUTOMÁTICA
# ============================================================

ARCHIVO = "Resultados_transferencia_ordenado.csv"
datos = pd.read_csv(ARCHIVO)

frecuencia = datos["Frecuencia"].to_numpy()
transferencia = datos["Transferencia"].to_numpy()
fase_relativa = datos["Fase relativa"].to_numpy()  # En radianes

R2_VALOR = 10e3

idx_max = np.argmax(transferencia)
idx_min = np.argmin(transferencia)

fs_est = frecuencia[idx_max]
fp_est = frecuencia[idx_min]
T_max = transferencia[idx_max]

T_base = (transferencia[0] + transferencia[-1]) / 2.0
f_base = (frecuencia[0] + frecuencia[-1]) / 2.0

C2_0_farads = T_base / (2 * np.pi * f_base * R2_VALOR)
C_0_farads = C2_0_farads * ((fp_est / fs_est)**2 - 1.0)
L_0_henrys = 1.0 / ((2 * np.pi * fs_est)**2 * C_0_farads)
R_0_ohms = R2_VALOR * ((1.0 / T_max) - 1.0)

p0 = [
    R_0_ohms,           # R en Ω
    L_0_henrys,         # L en H
    C_0_farads * 1e12,  # C en pF
    C2_0_farads * 1e12  # C2 en pF
]

# Cotas ampliadas para permitir L ~ 500H y C2 ~ pF
limites_inf = [1.0,   1.0,    1e-6, 1e-3]
limites_sup = [1e6, 5000.0, 100.0,  1000.0]

popt, pcov = curve_fit(
    lambda f, R, L, C, C2: modelo_log(f, R, L, C, C2, R2_val=R2_VALOR),
    frecuencia,
    np.log10(transferencia), # Ajuste sobre log10
    p0=p0,
    bounds=(limites_inf, limites_sup),
    maxfev=100000
)

R_fit, L_fit, C_fit_pF, C2_fit_pF = popt
errores = np.sqrt(np.diag(pcov))

print("--- PARÁMETROS OPTIMIZADOS ---")
print(f"R  = {R_fit:.4f} ± {errores[0]:.4f} Ω")
print(f"L  = {L_fit:.4f} ± {errores[1]:.4f} H")
print(f"C  = {C_fit_pF:.6f} ± {errores[2]:.6f} pF")
print(f"C2 = {C2_fit_pF:.4f} ± {errores[3]:.4f} pF")

f_fit = np.linspace(np.min(frecuencia), np.max(frecuencia), 5000)
log_T_fit = modelo_log(f_fit, *popt, R2_val=R2_VALOR)
T_fit = 10**log_T_fit # Revertimos el logaritmo para graficar
fase_fit = modelo_fase(f_fit, *popt, R2_val=R2_VALOR)

# Convertir fase a grados
fase_relativa_grados = np.degrees(fase_relativa)
OFFSET_FASE_DEG = -25.0 
fase_fit_grados = np.degrees(fase_fit) + OFFSET_FASE_DEG

# Crear figura con dual axis
fig, ax1 = plt.subplots(figsize=(12, 6))

# Eje izquierdo: Transferencia (Magnitud)
color_mag = 'b'
ax1.set_xlabel('Frecuencia [Hz]', fontsize=14)
ax1.set_ylabel('Transferencia', color=color_mag, fontsize=14)
ax1.scatter(frecuencia, transferencia, color=color_mag, s=15, alpha=0.6, label='Datos (Transferencia)')
ax1.plot(f_fit, T_fit, color=color_mag, linewidth=2, label='Ajuste (Transferenica)')
ax1.set_yscale('log')
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
ax1.tick_params(axis='y', labelcolor=color_mag, labelsize=14)
ax1.tick_params(axis='x', labelsize=14)

ax2 = ax1.twinx()
color_fase = 'r'
ax2.set_ylabel('Fase relativa [grados]', color=color_fase, fontsize=14)
ax2.scatter(frecuencia, fase_relativa_grados, color=color_fase, s=15, alpha=0.6, label='Datos (Fase)', marker='s')
ax2.plot(f_fit, fase_fit_grados, color=color_fase, linewidth=2, label='Ajuste BVD (Fase)')
ax2.tick_params(axis='y', labelcolor=color_fase, labelsize=14)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=18)

plt.tight_layout()
plt.show()