import os
import time
import subprocess
import logging

# Directorio base del proyecto
BASE_DIR = os.path.dirname(__file__)

# Carpeta donde tu web deja los archivos subidos
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads', 'transferencias', 'uploads')

# Palabras clave en nombre de archivo
BCI_KEYWORD = 'Movimientos_Detallado_Cuenta'
SANTANDER_KEYWORD = 'CartolaMovimiento-'

# Intervalo de sondeo (en segundos)
POLL_INTERVAL = 10

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'monitor_archivos.log')),
        logging.StreamHandler()
    ]
)

# Conjunto para rastrear archivos ya procesados
procesados = set()


def procesar_archivo(ruta_completa):
    nombre = os.path.basename(ruta_completa)
    try:
        # Obtener ruta del Python del entorno virtual
        venv_python = '/home/sacristobalspa/webfinal/venv/bin/python'
        
        if BCI_KEYWORD in nombre:
            logging.info(f"Archivo identificado como BCI: {nombre}")
            # Ejecutar script BCI directamente (procesa desde uploads)
            subprocess.run([venv_python, 'bci.py'], cwd=BASE_DIR, check=True, timeout=300)
            logging.info("Ejecución de bci.py completada.")

        elif SANTANDER_KEYWORD in nombre:
            logging.info(f"Archivo identificado como Santander: {nombre}")
            # Ejecutar script Santander directamente (procesa desde uploads)
            subprocess.run([venv_python, 'Santander.py'], cwd=BASE_DIR, check=True, timeout=300)
            logging.info("Ejecución de Santander.py completada.")

        else:
            logging.warning(f"Archivo no reconocido, se omite: {nombre}")

    except subprocess.TimeoutExpired:
        logging.error(f"Script para {nombre} excedió el tiempo límite")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al procesar {nombre}: {e}")
    except Exception as e:
        logging.error(f"Error inesperado al procesar {nombre}: {e}")

    procesados.add(ruta_completa)


def main():
    logging.info("Iniciando monitor de archivos bancarios...")
    logging.info(f"Directorio de uploads: {UPLOAD_DIR}")
    logging.info("Los scripts procesarán archivos directamente desde uploads")
    
    # Crear carpeta de uploads si no existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    while True:
        try:
            for nombre in os.listdir(UPLOAD_DIR):
                ruta = os.path.join(UPLOAD_DIR, nombre)
                if ruta not in procesados and os.path.isfile(ruta) and nombre.lower().endswith('.xlsx'):
                    logging.info(f"Nuevo archivo detectado: {nombre}")
                    procesar_archivo(ruta)
        except Exception as e:
            logging.error(f"Error al escanear carpeta de uploads: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main() 