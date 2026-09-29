import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.optimize import curve_fit

archivos = ['li_5_fino.csv', 'li_5.csv', 'li_n.csv']
datos = pd.concat((pd.read_csv(archivo) for archivo in archivos), ignore_index=True)
datos = datos.sort_values('Frecuencia')

xlim = (559, 563) # Asigna (xmin, xmax) en kHz para limitar el eje x.

fig, (ax_transferencia, ax_fase) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
frecuencia_khz = datos['Frecuencia'] / 1000
transferencia = datos['R']
error_transferencia = 0.05 * transferencia
fase = datos['theta']
error_fase = 0.01 * np.abs(fase)

ax_transferencia.fill_between(
	frecuencia_khz, transferencia - error_transferencia,
	transferencia + error_transferencia, color='#2A9D8F', alpha=0.2,
	linewidth=0
)
ax_transferencia.plot(frecuencia_khz, datos['R'], '-', color='#2A9D8F', markersize=3, label='Datos experimentales')
ax_transferencia.set_ylabel('Transferencia', fontsize=16, fontweight='bold')
ax_transferencia.set_yscale('log')
ax_transferencia.legend(prop={'size': 14, 'weight': 'bold'})

ax_fase.fill_between(
	frecuencia_khz, fase - error_fase, fase + error_fase,
	color='#E07A5F', alpha=0.2, linewidth=0
)
ax_fase.plot(frecuencia_khz, datos['theta'], '-', color='#E07A5F', markersize=3, label='Datos experimentales')
ax_fase.set_xlabel('Frecuencia [kHz]', fontsize=16, fontweight='bold')
ax_fase.set_ylabel('Fase', fontsize=16, fontweight='bold')
ax_fase.legend(prop={'size': 14, 'weight': 'bold'})

for ax in (ax_transferencia, ax_fase):
	ax.minorticks_on()
	ax.tick_params(axis='both', which='major', labelsize=14, length=8, width=2)
	ax.tick_params(axis='both', which='minor', length=5, width=1.4)
	for etiqueta in ax.get_xticklabels() + ax.get_yticklabels():
		etiqueta.set_fontweight('bold')
	ax.set_axisbelow(True)
	ax.grid(which='major', color='grey', linewidth=0.7, alpha=0.7)
	ax.grid(which='minor', color='grey', linestyle=':', linewidth=0.5, alpha=0.7)

if xlim is not None:
	ax_fase.set_xlim(xlim)

fig.tight_layout()
fig.savefig('mezcla.png', dpi=400, bbox_inches='tight')
plt.show()
