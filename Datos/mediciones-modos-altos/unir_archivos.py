import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

def combinar_archivos_csv(archivos_entrada: list, archivo_salida: str, encabezado: str):

    columnas = [col.strip() for col in encabezado.split(',')]
    lista_dfs = []

    for archivo in archivos_entrada:
        try:
            df = pd.read_csv(archivo, header=0, names=columnas)
            lista_dfs.append(df)
        except FileNotFoundError:
            sys.exit(f"Error fatal: No se encontró el archivo '{archivo}'. Terminando ejecución.")
        except Exception as e:
            sys.exit(f"Error fatal al leer '{archivo}': {e}. Terminando ejecución.")

    if not lista_dfs:
        sys.exit("Error fatal: La lista de archivos proporcionada está vacía.")

    try:
        df_concatenado = pd.concat(lista_dfs, ignore_index=True)
        df_concatenado.to_csv(archivo_salida, index=False)
    except Exception as e:
        sys.exit(f"Error fatal al crear el archivo '{archivo_salida}': {e}. Terminando ejecución.")

archivos_entrada = ['barrido_lockin.csv', 'barrido_lockin_fino.csv', 'barrido_lockin_fino_fino.csv',
                    'li_2modo_fino_fino.csv', 'li_2modo_fino.csv', 'li_3_fino_fino.csv', 'li_3_fino.csv',
                    'li_3.csv', 'li_4_fino.csv', 'li_4.csv', 'li_5_fino.csv', 'li_5.csv', 'li_n.csv']

archivo_salida = 'datos_combinados_resonancias.csv'
encabezado = 'Frecuencia,R,theta,X,Y'

combinar_archivos_csv(archivos_entrada, archivo_salida, encabezado)