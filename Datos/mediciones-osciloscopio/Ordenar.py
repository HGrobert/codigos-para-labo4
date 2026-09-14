import pandas as pd

# ============================================================
# CONFIGURACIÓN
# ============================================================
ARCHIVO_ENTRADA = "Resultados_transferencia.csv"
ARCHIVO_SALIDA = "Resultados_transferencia_ordenado.csv"
COLUMNA_ORDEN = "Frecuencia"

def ordenar_resultados():
    # 1. Leer el archivo CSV
    try:
        datos = pd.read_csv(ARCHIVO_ENTRADA)
        print(f"Archivo cargado exitosamente. Total de filas: {len(datos)}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ARCHIVO_ENTRADA}")
        return

    # 2. Verificar que la columna exista
    if COLUMNA_ORDEN not in datos.columns:
        print(f"Error: La columna '{COLUMNA_ORDEN}' no existe en el archivo.")
        print(f"Columnas disponibles: {list(datos.columns)}")
        return

    # 3. Ordenar los datos
    # inplace=False crea una copia ordenada, ascendente por defecto
    datos_ordenados = datos.sort_values(by=COLUMNA_ORDEN, ascending=True)

    # 4. Guardar el nuevo archivo
    # index=False evita que se guarde la columna con el número de fila original
    datos_ordenados.to_csv(ARCHIVO_SALIDA, index=False)
    
    print(f"Datos ordenados por '{COLUMNA_ORDEN}' de menor a mayor.")
    print(f"Archivo guardado como: {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    ordenar_resultados()