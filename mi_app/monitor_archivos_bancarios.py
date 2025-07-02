import os
import time
import shutil
import subprocess
import logging

# Directorio base del proyecto
BASE_DIR = os.path.dirname(__file__)

# Carpeta donde tu web deja los archivos subidos
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads', 'transferencias', 'uploads')

# Carpeta esperada por bci.py
BCI_INPUT_DIR = os.path.join(BASE_DIR, 'Bancos')
BCI_EXPECTED_NAME = 'excel_detallado.xlsx'

# Carpeta esperada por Santander.py (definida en la variable de entorno CARPETA_ARCHIVOS o carpeta por defecto)
SANTANDER_INPUT_DIR = os.getenv(
    'CARPETA_ARCHIVOS',
    os.path.join(BASE_DIR, 'Santander_archivos')
)

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
        if BCI_KEYWORD in nombre:
            logging.info(f"Archivo identificado como BCI: {nombre}")
            os.makedirs(BCI_INPUT_DIR, exist_ok=True)
            destino = os.path.join(BCI_INPUT_DIR, BCI_EXPECTED_NAME)
            shutil.copy2(ruta_completa, destino)
            logging.info(f"Copiado a {destino}")
            subprocess.run(['/home/sacristobalspa/webfinal/venv/bin/python', 'bci.py'], cwd=BASE_DIR, check=True)
            logging.info("Ejecución de bci.py completada.")

        elif SANTANDER_KEYWORD in nombre:
            logging.info(f"Archivo identificado como Santander: {nombre}")
            os.makedirs(SANTANDER_INPUT_DIR, exist_ok=True)
            destino = os.path.join(SANTANDER_INPUT_DIR, nombre)
            shutil.copy2(ruta_completa, destino)
            logging.info(f"Copiado a {destino}")
            subprocess.run(['/home/sacristobalspa/webfinal/venv/bin/python', 'Santander.py'], cwd=BASE_DIR, check=True)
            logging.info("Ejecución de Santander.py completada.")

        else:
            logging.warning(f"Archivo no reconocido, se omite: {nombre}")

    except Exception as e:
        logging.error(f"Error al procesar {nombre}: {e}")

    procesados.add(ruta_completa)


def main():
    logging.info("Iniciando monitor de archivos bancarios...")
    logging.info(f"Directorio de uploads: {UPLOAD_DIR}")
    logging.info(f"Directorio BCI: {BCI_INPUT_DIR}")
    logging.info(f"Directorio Santander: {SANTANDER_INPUT_DIR}")
    
    # Crear carpetas si no existen
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(BCI_INPUT_DIR, exist_ok=True)
    os.makedirs(SANTANDER_INPUT_DIR, exist_ok=True)

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