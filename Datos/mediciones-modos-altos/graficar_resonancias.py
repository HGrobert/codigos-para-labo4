import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution, least_squares

def transfer_complex(omega, R, L, C, C2, R_r, C_r):
    """Función de transferencia compleja H(ω) = z_r / (z + z_r)"""
    Z_pzt = R + 1j * (omega * L - 1 / (omega * C))
    Y = 1 / Z_pzt + 1j * omega * C2
    z = 1 / Y
    z_r = 1 / (1 / R_r + 1j * omega * C_r)
    return z_r / (z + z_r)

def transfer_magnitude(omega, R, L, C, C2, R_r, C_r):
    return np.abs(transfer_complex(omega, R, L, C, C2, R_r, C_r))

def transfer_phase(omega, R, L, C, C2, R_r, C_r):
    return np.angle(transfer_complex(omega, R, L, C, C2, R_r, C_r))

def phase_difference(phi_model, phi_data):
    return np.angle(np.exp(1j * (phi_model - phi_data)))

def physical_to_log(p):
    return np.log10(p)

def log_to_physical(x):
    return 10**x

def format_with_error(value, error, unit=""):
    """Formatea valor y error a 2 cifras significativas en el error."""
    if not np.isfinite(error) or error == 0:
        return f"{value:.4e} ± {error} {unit}"
    
    order = np.floor(np.log10(np.abs(error)))
    scale = 10**(order - 1)
    
    error_rounded = np.round(error / scale) * scale
    value_rounded = np.round(value / scale) * scale
    
    decimals = max(0, int(-np.log10(scale))) if scale < 1 else 0
    
    return f"{value_rounded:.{decimals}f} ± {error_rounded:.{decimals}f} {unit}"


def ajustar_sistema_piezo(archivos, p0, bounds_physical, R_r=10e3, plotear=True):
    """
    Lee archivos CSV, ajusta el modelo de transferencia y grafica los resultados.
    """
    print(f"\n--- Analizando conjunto de datos: {archivos} ---")
    
    try:
        data_list = [pd.read_csv(f"{nombre}.csv") for nombre in archivos]
        df_merged = pd.concat(data_list, ignore_index=True)
        df_merged = df_merged.drop_duplicates(subset=['Frecuencia']).sort_values('Frecuencia').reset_index(drop=True)

        frec = df_merged['Frecuencia'].to_numpy(dtype=float)
        transf = np.abs(df_merged['R'].to_numpy(dtype=float)) * np.sqrt(2)
        fase_deg = df_merged['theta'].to_numpy(dtype=float)
        fase_rad = np.deg2rad(fase_deg)
        omega = 2 * np.pi * frec

        mask = (np.isfinite(frec) & np.isfinite(transf) & np.isfinite(fase_rad) & (frec > 0) & (transf > 0))
        frec, transf, fase_rad, fase_deg, omega = frec[mask], transf[mask], fase_rad[mask], fase_deg[mask], omega[mask]
        
    except Exception as e:
        print(f"[!] Falla al leer o procesar los archivos: {e}")
        return None

    sigma_log_mag = 0.05
    sigma_phase = np.deg2rad(3.0)

    def residuals_joint(x, w, t_data, f_data):
        R, L, C, C2, C_r = log_to_physical(x)
        T_model = np.maximum(transfer_magnitude(w, R, L, C, C2, R_r, C_r), 1e-300)
        res_mag = (np.log(T_model) - np.log(t_data)) / sigma_log_mag
        
        phi_model = transfer_phase(w, R, L, C, C2, R_r, C_r)
        res_phase = phase_difference(phi_model, f_data) / sigma_phase
        return np.concatenate([res_mag, res_phase])

    def objective_joint(x, w, t_data, f_data):
        residual = residuals_joint(x, w, t_data, f_data)
        return 0.5 * np.dot(residual, residual)

    x0 = physical_to_log(p0)
    bounds_log = (physical_to_log(bounds_physical[0]), physical_to_log(bounds_physical[1]))

    try:
        global_starts = [
            differential_evolution(
                objective_joint,
                bounds=list(zip(bounds_log[0], bounds_log[1])),
                args=(omega, transf, fase_rad),
                seed=seed,
                maxiter=180,
                popsize=8,
                tol=1e-7,
                polish=False,
                updating='immediate'
            ).x
            for seed in (37, 123, 314159)
        ]
    except Exception as e:
        print(f"[!] Falló la búsqueda global para {archivos}: {e}")
        return None

    try:
        result_candidates = [least_squares(
            residuals_joint, x0, args=(omega, transf, fase_rad),
            bounds=bounds_log, max_nfev=50000, x_scale='jac',
            ftol=1e-12, xtol=1e-12, gtol=1e-12
        )]
        result_candidates.extend(
            least_squares(
                residuals_joint, start, args=(omega, transf, fase_rad),
                bounds=bounds_log, max_nfev=50000, x_scale='jac',
                ftol=1e-12, xtol=1e-12, gtol=1e-12
            )
            for start in global_starts
        )
        result_joint = min(result_candidates, key=lambda result: result.cost)
    except Exception as e:
        print(f"[!] Falló el ajuste de STAGE 2 (Conjunto) para {archivos}: {e}")
        return None

    p_joint = log_to_physical(result_joint.x)
    R_fit, L_fit, C_fit, C2_fit, Cr_fit = p_joint
    
    cov_log = None
    try:
        J = result_joint.jac
        cov_log = np.linalg.inv(J.T @ J)
        errors_log = np.sqrt(np.diag(cov_log))
        err_physical = np.abs(p_joint * np.log(10) * errors_log)
    except:
        err_physical = np.full_like(p_joint, np.inf)

    err_R, err_L, err_C, err_C2, err_Cr = err_physical

    f0 = 1 / (2 * np.pi * np.sqrt(L_fit * C_fit))
    f_anti = 1 / (2 * np.pi * np.sqrt(L_fit * ((C_fit * C2_fit) / (C_fit + C2_fit))))
    Q = 2 * np.pi * f0 * L_fit / R_fit

    if cov_log is not None:
        grad_f0 = np.array([0, -0.5, -0.5, 0, 0])
        grad_f_anti = np.array([
            0, -0.5, -0.5 * C2_fit / (C_fit + C2_fit),
            -0.5 * C_fit / (C_fit + C2_fit), 0
        ])
        grad_Q = np.array([-1, 0.5, -0.5, 0, 0])
        err_f0 = f0 * np.log(10) * np.sqrt(max(grad_f0 @ cov_log @ grad_f0, 0))
        err_f_anti = f_anti * np.log(10) * np.sqrt(max(grad_f_anti @ cov_log @ grad_f_anti, 0))
        err_Q = Q * np.log(10) * np.sqrt(max(grad_Q @ cov_log @ grad_Q, 0))
    else:
        err_f0 = err_f_anti = err_Q = np.inf

    print("Ajuste exitoso. Parámetros obtenidos:")
    print("  R  = " + format_with_error(R_fit, err_R, "Ω"))
    print("  L  = " + format_with_error(L_fit, err_L, "H"))
    print("  C  = " + format_with_error(C_fit * 1e12, err_C * 1e15, "fF"))
    print("  C2 = " + format_with_error(C2_fit * 1e12, err_C2 * 1e12, "pF"))
    print("  Cr = " + format_with_error(Cr_fit * 1e12, err_Cr * 1e12, "pF"))
    print("  Factor de calidad Q = " + format_with_error(Q, err_Q))
    print("  Frecuencia de resonancia = " + format_with_error(f0, err_f0, "Hz"))
    print("  Frecuencia de antiresonancia = " + format_with_error(f_anti, err_f_anti, "Hz"))
    
    T_fit = transfer_magnitude(omega, R_fit, L_fit, C_fit, C2_fit, R_r, Cr_fit)
    phi_fit_deg = np.rad2deg(transfer_phase(omega, R_fit, L_fit, C_fit, C2_fit, R_r, Cr_fit))

    if plotear:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
        
        ax1.loglog(frec, transf, '.', markersize=2, label='Datos')
        ax1.loglog(frec, T_fit, 'r-', linewidth=1.5, label='Ajuste Conjunto')
        ax1.set_ylabel('Transferencia', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='both', labelsize=11)
        ax1.minorticks_on()
        ax1.tick_params(axis='both', which='major', width=1.5, length=6)
        ax1.tick_params(axis='both', which='minor', width=1.0, length=3)
        plt.setp(ax1.get_xticklabels(), fontweight='bold')
        plt.setp(ax1.get_yticklabels(), fontweight='bold')
        ax1.grid(True, which="both", ls="--", alpha=0.6)
        ax1.legend(fontsize=11)
        
        ax2.semilogx(frec, fase_deg, '.', markersize=2)
        ax2.semilogx(frec, phi_fit_deg, 'r-', linewidth=1.5)
        ax2.set_ylabel('Fase [°]', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Frecuencia [Hz]', fontsize=12, fontweight='bold')
        ax2.tick_params(axis='both', labelsize=11)
        ax2.minorticks_on()
        ax2.tick_params(axis='both', which='major', width=1.5, length=6)
        ax2.tick_params(axis='both', which='minor', width=1.0, length=3)
        plt.setp(ax2.get_xticklabels(), fontweight='bold')
        plt.setp(ax2.get_yticklabels(), fontweight='bold')
        ax2.grid(True, which="both", ls="--", alpha=0.6)
        
        plt.tight_layout()
        plt.show()

    resultados = {
        'R': R_fit, 'err_R': err_R,
        'R_r': R_r,
        'L': L_fit, 'err_L': err_L,
        'C': C_fit, 'err_C': err_C,
        'C2': C2_fit, 'err_C2': err_C2,
        'Cr': Cr_fit, 'err_Cr': err_Cr,
        'Q': Q, 'err_Q': err_Q,
        'f0': f0,
        'err_f0': err_f0,
        'f_anti': f_anti,
        'err_f_anti': err_f_anti,
        'frecuencia': frec,
        'transferencia': transf,
        'fase_deg': fase_deg,
        'transferencia_ajuste': T_fit,
        'fase_ajuste_deg': phi_fit_deg,
        'transferencia_error': np.vstack((
            transf * (1 - np.exp(-sigma_log_mag)),
            transf * (np.exp(sigma_log_mag) - 1)
        )),
        'fase_error_deg': np.full_like(fase_deg, np.rad2deg(sigma_phase))
    }
    
    return resultados


def graficar_modos(resultados_modos, xlims=None):
    """
    Grafica los subplots de los modos con zoom automático adaptado
    a la distancia entre la resonancia y antirresonancia.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    indices = ['a)', 'b)', 'c)', 'd)']
    handles = None

    for i, (ax, resultados, indice) in enumerate(zip(axes.flat, resultados_modos, indices)):
        if resultados is None:
            ax.set_visible(False)
            continue

        frecuencia_khz = resultados['frecuencia'] / 1e3
        ax_fase = ax.twinx()

        barras_transferencia = max(1, len(frecuencia_khz) // 30)
        
        # Gráficas de datos y ajustes
        transferencia_datos = ax.errorbar(
            frecuencia_khz, resultados['transferencia'],
            yerr=resultados['transferencia_error'], fmt='o', color='tab:red', facecolor= None,
            ecolor='tab:red', markersize=2.5, elinewidth=0.6, capsize=1,
            errorevery=barras_transferencia, alpha=0.8,
            label='Datos Transferencia'
        )
        transferencia_ajuste, = ax.plot(
            frecuencia_khz, resultados['transferencia_ajuste'], '-',
            color='k', linewidth=1.4, label='Ajuste Transferencia Modelo Real'
        )
        fase_datos = ax_fase.errorbar(
            frecuencia_khz, resultados['fase_deg'],
            yerr=resultados['fase_error_deg'], fmt='o', color='tab:orange', facecolor= None,
            ecolor='tab:orange', markersize=2.5, elinewidth=0.6, capsize=1,
            errorevery=barras_transferencia, alpha=0.8,
            label='Datos Fase'
        )
        fase_ajuste, = ax_fase.plot(
            frecuencia_khz, resultados['fase_ajuste_deg'], '-',
            color='tab:blue', linewidth=1.4, label='Ajuste Fase Modelo Real'
        )

        f_res_khz = resultados['f0'] / 1e3
        f_anti_khz = resultados['f_anti'] / 1e3
        
        resonancia = ax.axvline(
            f_res_khz, color='purple', linestyle='--', linewidth=1.3,
            label='Resonancia'
        )
        antiresonancia = ax.axvline(
            f_anti_khz, color='green', linestyle=':', linewidth=1.4,
            label='Antirresonancia'
        )

        # ---------------------------------------------------------
        # NUEVA LÓGICA DE XLIM Y TICKS (Matemática de espaciado)
        # ---------------------------------------------------------
        delta_f = f_anti_khz - f_res_khz
        step = delta_f / 2.0

        # Mantener los límites existentes, pero anclar los ticks a la resonancia.
        if xlims is not None and i < len(xlims) and xlims[i] is not None:
            x_min, x_max = xlims[i]
        else:
            x_min = f_res_khz - 2 * step
            x_max = f_anti_khz + 2 * step

        ax.set_xlim(x_min, x_max)

        if np.isfinite(step) and step > 0:
            lower, upper = sorted((x_min, x_max))
            tolerance = 8 * np.finfo(float).eps * max(
                1.0, abs(lower), abs(upper), abs(f_res_khz), abs(f_anti_khz)
            )
            first_index = int(np.ceil((lower - f_res_khz - tolerance) / step))
            last_index = int(np.floor((upper - f_res_khz + tolerance) / step))
            tick_indices = np.arange(first_index, last_index + 1)
            ticks = f_res_khz + tick_indices * step
            ticks[tick_indices == 0] = f_res_khz
            ticks[tick_indices == 2] = f_anti_khz
        else:
            tick_indices = np.array([], dtype=int)
            ticks = np.array([f_res_khz, f_anti_khz])
            ticks = ticks[(ticks >= min(x_min, x_max)) & (ticks <= max(x_min, x_max))]

        tick_labels = [f'{tick:.2f}' for tick in ticks]
        
        ax.set_xticks(ticks)
        ax.set_xticklabels(tick_labels, rotation=30, ha='right', fontsize=11, fontweight='bold')
        # ---------------------------------------------------------

        ax.set_yscale('log')
        
        # Etiquetas de ejes en negrita
        ax.set_xlabel('Frecuencia [kHz]', fontsize=13, fontweight='bold')
        ax.set_ylabel('Transferencia', color='tab:blue', fontsize=13, fontweight='bold')
        ax_fase.set_ylabel('Fase [°]', color='tab:orange', fontsize=13, fontweight='bold')
        
        # Formato de números de los ejes Y (tamaño y negrita)
        ax.tick_params(axis='y', labelcolor='tab:blue', labelsize=11)
        ax_fase.tick_params(axis='y', labelcolor='tab:orange', labelsize=11)
        ax.tick_params(axis='x', labelsize=11)
        for eje in (ax, ax_fase):
            eje.minorticks_on()
            eje.tick_params(axis='both', which='major', width=1.5, length=6)
            eje.tick_params(axis='both', which='minor', width=1.0, length=3)
        
        plt.setp(ax.get_yticklabels(), fontweight='bold')
        plt.setp(ax_fase.get_yticklabels(), fontweight='bold')

        ax.grid(True, which='both', linestyle='--', alpha=0.45)
        ax_fase.text(
            0.02, 0.98, indice, transform=ax_fase.transAxes,
            va='top', ha='left', fontweight='bold', fontsize=13, zorder=100,
            bbox={'facecolor': 'white', 'alpha': 0.7, 'edgecolor': 'none', 'pad': 0.2}
        )

        if handles is None:
            handles = [transferencia_datos, transferencia_ajuste, fase_datos,
                       fase_ajuste, resonancia, antiresonancia]

    # Leyenda global en negrita
    if handles is not None:
        leg = fig.legend(handles, [handle.get_label() for handle in handles],
                         loc='lower center', ncol=3, frameon=False,
                         prop={'weight': 'bold', 'size': 12})
        for text in leg.get_texts():
            text.set_fontweight('bold')
    
    # Espaciado con bottom en 0.23
    fig.subplots_adjust(hspace=0.45, wspace=0.38, bottom=0.23, top=0.96, left=0.08, right=0.92)
    plt.show()
    fig.savefig('grafico_resonacias.png', dpi=400, bbox_inches='tight')


def graficar_plano_complejo(resultados_modos):
    """Grafica H ajustada en el plano complejo, coloreada por frecuencia."""
    resultados_validos = [resultado for resultado in resultados_modos if resultado is not None]
    if not resultados_validos:
        print("[!] No hay resultados válidos para graficar el plano complejo.")
        return

    frecuencias_khz = np.concatenate([
        np.array([np.min(resultado['frecuencia']), np.max(resultado['frecuencia'])]) / 1e3
        for resultado in resultados_validos
    ])
    frecuencia_min, frecuencia_max = np.min(frecuencias_khz), np.max(frecuencias_khz)
    normalizacion = plt.Normalize(vmin=frecuencia_min, vmax=frecuencia_max)

    fig, ax = plt.subplots(figsize=(8, 8))
    for i, resultado in enumerate(resultados_modos):
        if resultado is None:
            continue

        frecuencia = np.linspace(
            np.min(resultado['frecuencia']), np.max(resultado['frecuencia']), 100_000
        )
        frecuencia_khz = frecuencia / 1e3
        H_ajustada = transfer_complex(
            2 * np.pi * frecuencia,
            resultado['R'], resultado['L'], resultado['C'], resultado['C2'],
            resultado['R_r'], resultado['Cr']
        )
        mascara = (
            np.isfinite(H_ajustada.real)
            & np.isfinite(H_ajustada.imag)
            & np.isfinite(frecuencia_khz)
        )

        ax.scatter(
            H_ajustada.real[mascara], H_ajustada.imag[mascara],
            c=frecuencia_khz[mascara], cmap='viridis', norm=normalizacion,
            s=5, label=f'Modo {2*i +1}'
        )

    barra_color = fig.colorbar(
        plt.cm.ScalarMappable(norm=normalizacion, cmap='viridis'), ax=ax
    )
    barra_color.set_label('Frecuencia [kHz]', fontsize=15, fontweight='bold')
    barra_color.ax.tick_params(labelsize=13, width=1.5, length=5)
    plt.setp(barra_color.ax.get_yticklabels(), fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.8, alpha=0.6)
    ax.axvline(0, color='black', linewidth=0.8, alpha=0.6)
    ax.set_xlabel('Re(H)', fontsize=15, fontweight='bold')
    ax.set_ylabel('Im(H)', fontsize=15, fontweight='bold')
    ax.minorticks_on()
    ax.tick_params(axis='both', which='major', labelsize=13, width=1.5, length=7)
    ax.tick_params(axis='both', which='minor', width=1.2, length=4)
    plt.setp(ax.get_xticklabels() + ax.get_yticklabels(), fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axis('equal')
    ax.legend(prop={'size': 14, 'weight': 'bold'})
    fig.tight_layout()
    fig.savefig('plano-complejo.png', dpi=400, bbox_inches='tight')
    plt.close(fig)


# Ejecución principal
archivos = ['barrido_lockin', 'barrido_lockin_fino', 'barrido_lockin_fino_fino']
p0 = np.array([23e3, 404.0, 0.025e-12, 3.18e-12, 100e-12])
bounds_physical = (np.array([1e2, 1e-1, 1e-15, 1e-15, 1e-12]), np.array([1e6, 1e4, 1e-9, 1e-9, 1e-6]))
resultado_1 = ajustar_sistema_piezo(archivos, p0, bounds_physical, R_r=10e3, plotear=False)

archivos_2 = ['li_2modo_fino_fino', 'li_2modo_fino']
p0_1 = np.array([10e3, 500.0, 0.025e-15, 3.2e-12, 180e-12])
bounds_physical_1 = (np.array([1e2, 1e-1, 1e-18, 1e-15, 1e-12]), np.array([1e6, 1e4, 1e-12, 1e-9, 1e-6]))
resultado_2 = ajustar_sistema_piezo(archivos_2, p0_1, bounds_physical_1, R_r=10e3, plotear=False)

archivos_3 = ['li_3_fino_fino', 'li_3_fino', 'li_3']
p0_2 = np.array([10e3, 500.0, 0.025e-15, 3.2e-12, 180e-12])
bounds_physical_2 = (np.array([1e2, 1e-1, 1e-18, 1e-15, 1e-12]), np.array([1e6, 1e4, 1e-12, 1e-9, 1e-6]))
resultado_3 = ajustar_sistema_piezo(archivos_3, p0_2, bounds_physical_2, R_r=10e3, plotear=False)

archivos_4 = ['li_4_fino', 'li_4']
p0_3 = np.array([10e3, 500.0, 0.025e-16, 3.2e-12, 180e-12])
bounds_physical_3 = (np.array([1e2, 1e-1, 1e-18, 1e-15, 1e-12]), np.array([1e6, 1e4, 1e-12, 1e-9, 1e-6]))
resultado_4 = ajustar_sistema_piezo(archivos_4, p0_3, bounds_physical_3, R_r=10e3, plotear=False)

# Ejemplo para definir xlims personalizados por subplot (en kHz):
xlims_personalizados = [(50.0, 50.36), (150.1, 150.28), None, (349.11, 349.24)]
graficar_modos([resultado_1, resultado_2, resultado_3, resultado_4], xlims=xlims_personalizados)
graficar_plano_complejo([resultado_1, resultado_2, resultado_3, resultado_4])
