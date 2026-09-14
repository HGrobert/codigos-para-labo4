import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

ARCHIVOS = ['barrido_lockin', 'barrido_lockin_fino', 'barrido_lockin_fino_fino']
R_r = 10e3  # Resistencia de carga fija [Ω]

# Parámetros iniciales: [R, L, C, C2, Cr]
p0 = np.array([23e3, 404.0, 0.025e-12, 3.18e-12, 100e-12])

# Límites físicos: (min, max)
bounds_physical = (
    np.array([1e2, 1e-1, 1e-15, 1e-15, 1e-12]),
    np.array([1e6, 1e4, 1e-9, 1e-9, 1e-6])
)

def transfer_complex(omega, R, L, C, C2, R_r, C_r):
    """Función de transferencia compleja H(ω) = z_r / (z + z_r)"""
    # Impedancia del brazo PZT: Z_pzt = R + j(ωL - 1/(ωC))
    Z_pzt = R + 1j * (omega * L - 1 / (omega * C))
    # Paralelo Z_pzt || C2
    Y = 1 / Z_pzt + 1j * omega * C2
    z = 1 / Y
    # Paralelo R_r || C_r
    z_r = 1 / (1 / R_r + 1j * omega * C_r)
    # Divisor de tensión
    return z_r / (z + z_r)

def transfer_magnitude(omega, R, L, C, C2, C_r):
    """Módulo de H(ω): |H(ω)|"""
    return np.abs(transfer_complex(omega, R, L, C, C2, R_r, C_r))

def transfer_phase(omega, R, L, C, C2, C_r):
    """Fase de H(ω): ∠H(ω) en radianes"""
    return np.angle(transfer_complex(omega, R, L, C, C2, R_r, C_r))

def phase_difference(phi_model, phi_data):
    """Diferencia angular correcta entre dos fases (siempre en [-π, π])"""
    return np.angle(np.exp(1j * (phi_model - phi_data)))

def physical_to_log(p):
    """Convierte parámetros físicos a escala logarítmica (log10)"""
    return np.log10(p)

def log_to_physical(x):
    """Convierte parámetros log10 a unidades físicas"""
    return 10**x

def calculate_errors(result, p_values):
    """Calcula errores de parámetros a partir del jacobiano (en escala log10)"""
    # Matriz de covarianza en escala log10
    J = result.jac
    try:
        cov = np.linalg.inv(J.T @ J)
        errors_log = np.sqrt(np.diag(cov))
    except:
        errors_log = np.full_like(p_values, np.inf)
    
    # Convertir errores a escala física: error_p ≈ p * ln(10) * error_log10
    errors_physical = np.abs(p_values * np.log(10) * errors_log)
    return errors_physical

def format_with_error(value, error):
    """Formatea un valor con su error redondeado a 2 cifras significativas"""
    if np.isinf(error) or np.isnan(error):
        return f"{value:.6e} ± ∞"
    if error == 0:
        return f"{value:.6e} ± 0"
    
    # Redondear error a 2 cifras significativas
    order = np.floor(np.log10(np.abs(error)))
    error_rounded = np.round(error / 10**order, 1) * 10**order
    
    # Redondear valor al mismo orden de magnitud del error
    value_rounded = np.round(value / error_rounded) * error_rounded
    
    return f"{value:.6e} ± {error_rounded:.2e}"

print("\nCargando datos...")
data_list = [pd.read_csv(f"{nombre}.csv") for nombre in ARCHIVOS]
for nombre in ARCHIVOS:
    print(f"  → {nombre}.csv")

# Combinar, eliminar duplicados y ordenar
df_merged = pd.concat(data_list, ignore_index=True)
df_merged = df_merged.drop_duplicates(subset=['Frecuencia']).sort_values('Frecuencia').reset_index(drop=True)

# Extraer datos
frec = df_merged['Frecuencia'].to_numpy(dtype=float)
transf = np.abs(df_merged['R'].to_numpy(dtype=float)) * np.sqrt(2)  # T = |R| × √2
fase_deg = df_merged['theta'].to_numpy(dtype=float)  # Fase en grados
fase_rad = np.deg2rad(fase_deg)  # Fase en radianes
omega = 2 * np.pi * frec  # Frecuencia angular

# Limpieza de datos (eliminar valores inválidos)
mask = (np.isfinite(frec) & np.isfinite(transf) & np.isfinite(fase_rad) & (frec > 0) & (transf > 0))
frec, transf, fase_rad, fase_deg, omega = frec[mask], transf[mask], fase_rad[mask], fase_deg[mask], omega[mask]

print(f"\nPuntos de datos: {len(frec)}")
print(f"Frecuencia: {frec.min():.2f} - {frec.max():.2f} Hz")
print(f"Magnitud: {transf.min():.3e} - {transf.max():.3e}")

def model_magnitude_log(x, omega):
    """Modelo de magnitud con parámetros en escala log10"""
    R, L, C, C2, C_r = log_to_physical(x)
    return transfer_magnitude(omega, R, L, C, C2, C_r)

def model_phase_log(x, omega):
    """Modelo de fase con parámetros en escala log10"""
    R, L, C, C2, C_r = log_to_physical(x)
    return transfer_phase(omega, R, L, C, C2, C_r)

def residuals_magnitude(x, omega, transf_data):
    """Residuo para ajuste de magnitud (escala logarítmica)"""
    T_model = model_magnitude_log(x, omega)
    T_model = np.maximum(T_model, 1e-300)  # Evitar log(0)
    return (np.log(T_model) - np.log(transf_data)) / sigma_log_mag

def residuals_joint(x, omega, transf_data, fase_data):
    """Residuo combinado de magnitud y fase"""
    T_model = model_magnitude_log(x, omega)
    T_model = np.maximum(T_model, 1e-300)
    residual_mag = (np.log(T_model) - np.log(transf_data)) / sigma_log_mag
    
    phi_model = model_phase_log(x, omega)
    residual_phase = phase_difference(phi_model, fase_data) / sigma_phase
    
    return np.concatenate([residual_mag, residual_phase])

# Pesos para el ajuste
sigma_log_mag = 0.05  # Error relativo de magnitud (~5%)
sigma_phase_deg = 3.0  # Error de fase (3 grados)
sigma_phase = np.deg2rad(sigma_phase_deg)

x0 = physical_to_log(p0)
bounds_log = (physical_to_log(bounds_physical[0]), physical_to_log(bounds_physical[1]))

# Modelo inicial
T_initial = transfer_magnitude(omega, *p0)
phi_initial = transfer_phase(omega, *p0)

print("\n" + "=" * 70)
print("STAGE 1 - AJUSTE DE MAGNITUD")
print("=" * 70)

result_mag = least_squares(
    residuals_magnitude, x0,
    args=(omega, transf),
    bounds=bounds_log,
    max_nfev=50000, x_scale='jac',
    ftol=1e-12, xtol=1e-12, gtol=1e-12,
    verbose=0
)

p_mag = log_to_physical(result_mag.x)
R_mag, L_mag, C_mag, C2_mag, Cr_mag = p_mag

# Calcular errores
errors_mag = calculate_errors(result_mag, p_mag)
err_R_mag, err_L_mag, err_C_mag, err_C2_mag, err_Cr_mag = errors_mag

print(f"\nParámetros obtenidos para la trasferencia:")
print(f"  R   = {format_with_error(R_mag, err_R_mag)} Ω")
print(f"  L   = {format_with_error(L_mag, err_L_mag)} H")
print(f"  C   = {format_with_error(C_mag, err_C_mag)} F")
print(f"  C2  = {format_with_error(C2_mag, err_C2_mag)} F")
print(f"  Cr  = {format_with_error(Cr_mag, err_Cr_mag)} F")
print(f"  Rr  = {R_r:.8e} Ω (fijo)")

T_mag_fit = transfer_magnitude(omega, *p_mag)
phi_mag_fit = transfer_phase(omega, *p_mag)

print("\n" + "=" * 70)
print("STAGE 2 - AJUSTE CONJUNTO MAGNITUD + FASE")
print("=" * 70)

result_joint = least_squares(
    residuals_joint,
    result_mag.x,  # Comenzar desde resultado de Stage 1
    args=(omega, transf, fase_rad),
    bounds=bounds_log,
    max_nfev=50000, x_scale='jac',
    ftol=1e-12, xtol=1e-12, gtol=1e-12,
    verbose=0
)

p_joint = log_to_physical(result_joint.x)
R_fit, L_fit, C_fit, C2_fit, Cr_fit = p_joint

# Calcular errores
errors_joint = calculate_errors(result_joint, p_joint)
err_R_fit, err_L_fit, err_C_fit, err_C2_fit, err_Cr_fit = errors_joint

print(f"\nParámetros obtenidos (ajuste conjunto):")
print(f"  R   = {format_with_error(R_fit, err_R_fit)} Ω")
print(f"  L   = {format_with_error(L_fit, err_L_fit)} H")
print(f"  C   = {format_with_error(C_fit, err_C_fit)} F")
print(f"  C2  = {format_with_error(C2_fit, err_C2_fit)} F")
print(f"  Cr  = {format_with_error(Cr_fit, err_Cr_fit)} F")
print(f"  Rr  = {R_r:.8e} Ω (fijo)")

T_fit = transfer_magnitude(omega, *p_joint)
phi_fit = transfer_phase(omega, *p_joint)

# Residuos de magnitud
mag_residuals = transf - T_mag_fit
mag_residuals_relative = (transf - T_fit) / transf

# Residuos de fase
phase_residuals_rad = phase_difference(phi_fit, fase_rad)
phase_residuals_deg = np.rad2deg(phase_residuals_rad)

# Frecuencia de resonancia y antiresonancia
C_eq = (C_fit * C2_fit) / (C_fit + C2_fit)  # Capacitancia equivalente en serie
f0 = 1 / (2 * np.pi * np.sqrt(L_fit * C_fit))  # Frecuencia de resonancia
f_anti = 1 / (2 * np.pi * np.sqrt(L_fit * C_eq))  # Frecuencia de antiresonancia

print(f"\nFrecuencia de resonancia (LC) : {f0:.4f} Hz")
print(f"Frecuencia de antiresonancia  : {f_anti:.4f} Hz")

# ============================================================
# INCERTIDUMBRES SR830 (Stanford Research Systems)
# ============================================================
# Especificaciones típicas:
# - Amplitud: 0.5% + 0.1% del fondo de escala
# - Fase: 0.1° + 0.02° × |desviación de fase|

# Incertidumbres de magnitud (amplitud)
# Usando 1% como error relativo típico
err_transf = 0.01 * transf  # 1% de la lectura

# Incertidumbres de fase (en grados)
# Usando 0.2° como error típico
err_fase_deg = 0.2 * np.ones_like(fase_deg)  # 0.2 grados constante

fig = plt.figure(figsize=(25, 6))
gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[2, 2],hspace=0.1, wspace=0.2, left=0.06, right=0.95)

# Crear subplots con gridspec
ax_mag = fig.add_subplot(gs[0, 0])
ax_mag_res = fig.add_subplot(gs[1, 0], sharex=ax_mag)

ax_phase = fig.add_subplot(gs[0, 1])
ax_phase_res = fig.add_subplot(gs[1, 1], sharex=ax_phase)

# --- MAGNITUD (con barras de error) ---
ax_mag.errorbar(frec, transf, yerr=err_transf, fmt='o', color='b', 
                ecolor='b', markerfacecolor='none', alpha=0.6, elinewidth=1, capsize=3, markersize=4, label='Datos SR830')
ax_mag.plot(frec, T_mag_fit, color='k', linewidth=2, label='Ajuste transferencia \n (modelo alternativo)')
ax_mag.set_yscale('log')
ax_mag.set_ylabel('Transferencia')
ax_mag.grid(True, which='both', linestyle='--', alpha=0.5)
ax_mag.set_xlim(49800, 50800)
ax_mag.axvline(f0, color='g', linestyle='--', linewidth=2, label=f'Resonancia: {f0:.2f} Hz')
ax_mag.axvline(f_anti, color='m', linestyle='--', linewidth=2, label=f'Antiresonancia: {f_anti:.2f} Hz')
ax_mag.legend()

# --- RESIDUOS MAGNITUD ---
ax_mag_res.errorbar(frec, mag_residuals, yerr=err_transf, fmt='o', color='b', 
                    ecolor='b', markerfacecolor='none', alpha=0.6, elinewidth=1, capsize=3, markersize=4)
ax_mag_res.axhline(0, color='k', linestyle='--', linewidth=1)
ax_mag_res.set_xlabel('Frecuencia (Hz)')
ax_mag_res.set_ylabel('Residuo')
ax_mag_res.grid(True, linestyle='--', alpha=0.5)

# --- FASE (con barras de error) ---
ax_phase.errorbar(frec, fase_deg, yerr=err_fase_deg, fmt='o', color='r', 
                  ecolor='r', markerfacecolor='none', alpha=0.6, elinewidth=1, capsize=3, markersize=4, label='Datos SR830')
ax_phase.plot(frec, np.rad2deg(phi_fit), color='k', linestyle='-', linewidth=2, label='Ajuste de fase \n (modelo alternativo)')
ax_phase.set_ylabel('Fase (grados)')
ax_phase.set_xlim(49800, 50800)
ax_phase.grid(True, linestyle='--', alpha=0.5)
ax_phase.axvline(f0, color='g', linestyle='--', linewidth=2, label=f'Resonancia: {f0:.2f} Hz')
ax_phase.axvline(f_anti, color='m', linestyle='--', linewidth=2, label=f'Antiresonancia: {f_anti:.2f} Hz')
ax_phase.legend()

# --- RESIDUOS FASE ---
ax_phase_res.errorbar(frec, phase_residuals_deg, yerr=err_fase_deg, fmt='o', color='r', 
                      ecolor='r', markerfacecolor='none', alpha=0.6, elinewidth=1, capsize=3, markersize=4)
ax_phase_res.axhline(0, color='k', linestyle='--', linewidth=1)
ax_phase_res.set_xlabel('Frecuencia (Hz)')
ax_phase_res.set_ylabel('Residuo (°)')
ax_phase_res.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()