import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_ENTRADA = "Datos_señales.csv"
ARCHIVO_SALIDA = "Resultados_transferenciaBis.csv"

N_MUESTRAS = 2500

# ============================================================
# FUNCIÓN DE AJUSTE
# ============================================================

def sinusoidal(t, A, f, phi, offset):
    """
    Modelo sinusoidal:
        V(t) = A * sin(2*pi*f*t + phi) + offset
    """
    return A * np.sin(2 * np.pi * f * t + phi) + offset


def ajustar_seno(t, V, frecuencia):
    """
    Ajusta una señal sinusoidal con frecuencia conocida.
    Devuelve: amplitud, fase, offset
    """
    A0 = (np.max(V) - np.min(V)) / 2
    offset0 = np.mean(V)
    phi0 = 0
    p0 = [A0, frecuencia, phi0, offset0]

    parametros, _ = curve_fit(
        sinusoidal,
        t,
        V,
        p0=p0,
        maxfev=10000
    )

    A, f, phi, offset = parametros
    A = abs(A) # La amplitud la queremos positiva

    return A, phi, offset

# ============================================================
# LECTURA DE DATOS
# ============================================================

datos = pd.read_csv(ARCHIVO_ENTRADA)
print(f"Total de filas: {len(datos)}")

n_bloques = len(datos) // N_MUESTRAS
print(f"Cantidad de bloques de {N_MUESTRAS} muestras: {n_bloques}")

# ============================================================
# PROCESAMIENTO
# ============================================================

resultados = []

for i in range(n_bloques):
    inicio = i * N_MUESTRAS
    fin = inicio + N_MUESTRAS
    bloque = datos.iloc[inicio:fin].copy()

    # --- Frecuencia ---
    frecuencia = bloque["Frecuencia"].iloc[0]
    if not np.allclose(bloque["Frecuencia"], frecuencia):
        print(f"Advertencia: la frecuencia no es constante en el bloque {i + 1}")

    # --- CH1 ---
    t1 = bloque["Tiempo CH1"].to_numpy()
    v1 = bloque["V1"].to_numpy()
    A1, phi1, offset1 = ajustar_seno(t1, v1, frecuencia)

    # --- CH2 ---
    t2 = bloque["Tiempo CH2"].to_numpy()
    v2 = bloque["V2"].to_numpy()
    A2, phi2, offset2 = ajustar_seno(t2, v2, frecuencia)

    # --- TRANSFERENCIA Y FASE ---
    transferencia = A2 / A1 if A1 != 0 else np.nan
    
    fase_relativa = phi2 - phi1
    fase_relativa = np.arctan2(np.sin(fase_relativa), np.cos(fase_relativa))
    fase_grados = np.degrees(fase_relativa)

    # --- GUARDAR RESULTADOS ---
    resultados.append({
        "Frecuencia": frecuencia,
        "Amplitud CH1": A1,
        "Amplitud CH2": A2,
        "Transferencia": transferencia,
        "Fase CH1": phi1,
        "Fase CH2": phi2,
        "Fase relativa": fase_relativa,
        "Fase relativa (grados)": fase_grados,
        "Offset CH1": offset1,
        "Offset CH2": offset2
    })

    # --- IMPRESIÓN EN CONSOLA ---
    print(f"\n--- Bloque {i + 1}/{n_bloques} | f = {frecuencia:.2f} Hz ---")
    print(f"CH1 -> A: {A1:.4f} | Fase: {phi1:.4f} rad | Offset: {offset1:.4f}")
    print(f"CH2 -> A: {A2:.4f} | Fase: {phi2:.4f} rad | Offset: {offset2:.4f}")
    print(f"Transferencia: {transferencia:.4f} | Δφ: {fase_grados:.2f}°")

    # --- GRAFICACIÓN ---
    fig, ax = plt.subplots(figsize=(10, 6))

    # Curvas teóricas (alta resolución para el trazado)
    t1_fit = np.linspace(np.min(t1), np.max(t1), 1000)
    t2_fit = np.linspace(np.min(t2), np.max(t2), 1000)
    v1_fit = sinusoidal(t1_fit, A1, frecuencia, phi1, offset1)
    v2_fit = sinusoidal(t2_fit, A2, frecuencia, phi2, offset2)

    # Puntos de datos
    ax.plot(t1, v1, 'b.', alpha=0.3, label='Datos CH1')
    ax.plot(t2, v2, 'r.', alpha=0.3, label='Datos CH2')

    # Líneas de ajuste
    ax.plot(t1_fit, v1_fit, 'k-', linewidth=2, label='Ajuste CH1')
    ax.plot(t2_fit, v2_fit, 'k-', linewidth=2, label='Ajuste CH2')

    # Configuración de gráfico
    ax.set_title(f'Bloque {i + 1}/{n_bloques} - Frecuencia: {frecuencia:.2f} Hz\n'
                 f'Transferencia = {transferencia:.4f} | $\Delta\phi$ = {fase_grados:.2f}°')
    ax.set_xlabel('Tiempo [s]')
    ax.set_ylabel('Tensión [V]')
    ax.grid(True)
    ax.legend(loc='upper right')

    # Caja de texto con parámetros
    textstr = (f'Parámetros CH1:\n'
               f'A = {A1:.4f}\n'
               f'$\phi$ = {phi1:.4f}\n'
               f'Offset = {offset1:.4f}\n\n'
               f'Parámetros CH2:\n'
               f'A = {A2:.4f}\n'
               f'$\phi$ = {phi2:.4f}\n'
               f'Offset = {offset2:.4f}')
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray')
    ax.text(0.02, 0.95, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)

    # Mostrar gráfico y pausar (El script se detiene hasta que cierres la ventana)
    plt.tight_layout()
    plt.show()

# ============================================================
# GUARDAR CSV
# ============================================================

resultados_df = pd.DataFrame(resultados)
resultados_df.to_csv(ARCHIVO_SALIDA, index=False)

print("\n========================================")
print("Procesamiento terminado")
print(f"Archivo generado: {ARCHIVO_SALIDA}")
print(f"Cantidad de mediciones: {len(resultados_df)}")
print("========================================")