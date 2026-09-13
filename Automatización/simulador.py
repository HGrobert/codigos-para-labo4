import sys
from unittest.mock import MagicMock

# 1. Creamos la estructura falsa (mock) de pyvisa
mock_pyvisa = MagicMock()

# Emulamos la excepción específica de PyVISA para probar el manejo de errores
class SimVisaIOError(Exception): 
    pass
mock_pyvisa.errors.VisaIOError = SimVisaIOError

# 2. Configuramos el comportamiento del ResourceManager falso
mock_rm = MagicMock()

# Simulamos 4 puertos conectados (las direcciones físicas que detectaría la PC)
mock_rm.list_resources.return_value = (
    'USB0::0x0699::0x0346::C034165::INSTR',  # Emulará el Tektronix AFG
    'USB0::0x0957::0x17A6::MY51360211::INSTR', # Emulará el Osciloscopio Agilent
    'GPIB0::8::INSTR',                       # Emulará el Lock-in SR830
    'ASRL3::INSTR'                           # Emulará un equipo que no responde
)

def simular_open_resource(res_name):
    inst = MagicMock()
    inst.resource_name = res_name
    
    def simular_query(comando):
        # Simulamos el Paso 2 (Identificación *IDN?)
        if comando == '*IDN?':
            if '0x0699' in res_name:
                return 'TEKTRONIX,AFG3021B,C034165,SCPI:99.0 FV:3.1.1'
            elif '0x0957' in res_name:
                return 'AGILENT,DSO-X 2002A,MY51360211,02.35'
            elif 'GPIB0' in res_name:
                return 'Stanford_Research_Systems,SR830,s/n12345,1.07'
            else:
                # Simulamos el error de comunicación de un equipo incompatible
                raise SimVisaIOError("Timeout simulado: El equipo no responde")
        
        # Simulamos el Paso 3 (Comandos de prueba)
        if comando in ['*TST?', 'OUTP?', 'OUTX?']:
            return "0 (Prueba OK)"
            
        return "Comando no reconocido"
        
    inst.query.side_effect = simular_query
    return inst

mock_rm.open_resource.side_effect = simular_open_resource
mock_pyvisa.ResourceManager.return_value = mock_rm

# 3. El truco principal: inyectamos el mock en los módulos del sistema
sys.modules['pyvisa'] = mock_pyvisa

# 4. Importamos tu script (NO SE MODIFICA NADA DEL CÓDIGO ORIGINAL)
try:
    import script_laboratorio
except ImportError:
    print("Error: Asegúrate de que tu código principal esté guardado como 'script_laboratorio.py' en esta misma carpeta.")
    sys.exit(1)

if __name__ == "__main__":
    print("--- INICIANDO ENTORNO DE SIMULACIÓN ---")
    script_laboratorio.main()