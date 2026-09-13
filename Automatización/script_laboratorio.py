import pyvisa

def paso1_identificacion(rm):
    """Escanea y lista los recursos conectados."""
    while True:
        recursos = rm.list_resources()
        if not recursos:
            print("\n[Paso 1] No se encontraron equipos conectados.")
        else:
            print(f"\n[Paso 1] Se encontraron {len(recursos)} equipos conectados:")
            for i, res in enumerate(recursos):
                print(f"  [{i}] {res}")
        
        accion = input("¿Desea avanzar (A) o volver a identificar (I)?: ").strip().upper()
        if accion == 'A':
            if recursos:
                return recursos
            else:
                print("No se puede avanzar sin equipos conectados.")
        # Si presiona 'I' u otra tecla, el bucle se repite y vuelve a escanear

def paso2_asignacion(rm, recursos):
    """Consulta la identidad de los equipos y les asigna un nombre evaluando el modelo."""
    equipos_asignados = {}
    
    for res in recursos:
        while True:
            try:
                inst = rm.open_resource(res)
                inst.timeout = 2000
                idn = inst.query('*IDN?').strip()
                
                # Separamos el string basándonos en las comas del estándar IEEE 488.2
                campos_idn = idn.split(',')
                nombre = 'desconocido'
                marca = "Desconocida"
                modelo = "Desconocido"
                
                # Verificamos que el equipo haya respondido con el formato estándar de 4 campos
                if len(campos_idn) >= 2:
                    marca = campos_idn[0].strip().upper()
                    modelo = campos_idn[1].strip().upper()
                    
                    # Clasificación por sufijos y prefijos de MODELO
                    if 'AFG' in modelo or 'AWG' in modelo:
                        nombre = 'fungen'
                    elif 'TDS' in modelo or 'TBS' in modelo or 'DPO' in modelo or 'MSO' in modelo or 'DSO' in modelo:
                        nombre = 'osci'
                    elif 'SR830' in modelo:
                        nombre = 'lock'
                else:
                    # Fallback por si hay un equipo viejo que no usa comas
                    if 'SR830' in idn.upper():
                        nombre = 'lock'
                
                print(f"\nRecurso: {res}")
                if nombre == 'desconocido':
                    print(f"Equipo desconocido. ID reportado completo: {idn}")
                else:
                    print(f"Equipo reconocido como '{nombre}' (Marca: {marca}, Modelo: {modelo})")
                
                accion = input("¿Confirmar asignación (C), reintentar (R) o nombrar manualmente (M)?: ").strip().upper()
                if accion == 'C':
                    equipos_asignados[nombre] = inst
                    break
                elif accion == 'M':
                    nombre_manual = input("Ingrese el nombre para este equipo: ").strip()
                    equipos_asignados[nombre_manual] = inst
                    break
                elif accion == 'R':
                    inst.close()
                    continue
            
            except pyvisa.errors.VisaIOError:
                print(f"Error al intentar leer {res}. Puede que el equipo no soporte *IDN?.")
                accion = input("¿Nombrar manualmente (M) o ignorar (I)?: ").strip().upper()
                if accion == 'M':
                    nombre_manual = input("Ingrese el nombre: ").strip()
                    # Si no hay IDN, instanciamos de todas formas bajo el nombre manual
                    equipos_asignados[nombre_manual] = inst 
                    break
                else:
                    inst.close()
                    break
                    
    return equipos_asignados

def paso3_prueba(equipos):
    """Envía un comando específico a cada equipo para confirmar funcionalidad."""
    print("\n[Paso 3] Iniciando pruebas de comunicación específica...")
    
    # Diccionario de comandos de prueba para cada tipo de equipo
    comandos_prueba = {
        'osci': '*TST?',      # Autotest
        'fungen': 'OUTP?',    # Preguntar estado de la salida
        'lock': 'OUTX?'       # Preguntar interfaz de salida del Lock-In
    }
    
    for nombre, inst in equipos.items():
        comando = comandos_prueba.get(nombre, '*IDN?') # Por defecto hace un IDN
        try:
            respuesta = inst.query(comando).strip()
            print(f"[EXITO] {nombre} respondió correctamente al comando {comando}: {respuesta}")
        except pyvisa.errors.VisaIOError:
            print(f"[ERROR] Dispositivo '{nombre}' identificado erróneamente o sin respuesta al comando {comando}.")
            
            # Opción para identificar a mano (Paso 3)
            accion = input(f"¿Desea reasignar/ignorar este equipo a mano? (R/I): ").strip().upper()
            if accion == 'R':
                print("Por favor, revise físicamente las conexiones o asigne los parámetros nuevamente.")
                # Aquí podrías volver a llamar a una función de asignación individual

def guardar_configuracion(equipos, nombre_archivo="config_equipos.py"):
    """Extrae las direcciones de los instrumentos y genera el archivo .py"""
    print(f"\n[Guardado] Generando archivo {nombre_archivo}...")
    try:
        with open(nombre_archivo, "w") as f:
            f.write("# Archivo autogenerado con las direcciones de los equipos\n")
            f.write("# Importa estas variables en tu script principal\n\n")
            f.write("import pyvisa as visa\n")
            f.write("rm = visa.ResourceManager()\n\n")
            
            for nombre, inst in equipos.items():
                # inst.resource_name contiene el string de la dirección física
                f.write(f"{nombre} = '{inst.resource_name}'\n")
                
        print(f"[EXITO] Archivo '{nombre_archivo}' generado correctamente.")
    except IOError as e:
        print(f"[ERROR] No se pudo crear el archivo: {e}")

def main():
    rm = pyvisa.ResourceManager()
    recursos = paso1_identificacion(rm)
    equipos = paso2_asignacion(rm, recursos)
    paso3_prueba(equipos)
    guardar_configuracion(equipos)
    
    print("\nInicialización finalizada. Equipos listos para el experimento.")
    for inst in equipos.values(): 
        inst.close()

if __name__ == "__main__":
    main()