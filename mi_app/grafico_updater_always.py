#!/usr/bin/env python3
"""
Script para actualizar datos del gráfico de tasas USDT/VES
Ejecutar como Always Task en PythonAnywhere
"""

import os
import sys
import time
import logging
from datetime import datetime
import pytz

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sacristobalspa/webfinal/mi_app/grafico_updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Agregar el directorio del proyecto al path
project_dir = '/home/sacristobalspa/webfinal'
sys.path.insert(0, project_dir)

def actualizar_datos():
    """Función para actualizar los datos del gráfico"""
    try:
        # Importar aquí para evitar problemas de path
        from mi_app.mi_app.blueprints.utilidades import actualizar_datos as actualizar_datos_func
        actualizar_datos_func()
        logging.info("✅ Datos del gráfico actualizados correctamente")
        return True
    except Exception as e:
        logging.error(f"❌ Error al actualizar datos del gráfico: {e}")
        return False

def main():
    """Función principal del script"""
    logging.info("🚀 Iniciando script de actualización de datos del gráfico")
    
    # Configurar zona horaria
    chile_tz = pytz.timezone('America/Santiago')
    
    # Contador de actualizaciones exitosas y fallidas
    exitosas = 0
    fallidas = 0
    
    while True:
        try:
            # Obtener hora actual
            ahora = datetime.now(chile_tz)
            logging.info(f"⏰ Hora actual: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Actualizar datos
            if actualizar_datos():
                exitosas += 1
            else:
                fallidas += 1
            
            # Mostrar estadísticas cada 10 actualizaciones
            if (exitosas + fallidas) % 10 == 0:
                logging.info(f"📊 Estadísticas: {exitosas} exitosas, {fallidas} fallidas")
            
            # Esperar 3 minutos (180 segundos)
            logging.info("⏳ Esperando 3 minutos hasta la próxima actualización...")
            time.sleep(180)
            
        except KeyboardInterrupt:
            logging.info("🛑 Script interrumpido por el usuario")
            break
        except Exception as e:
            logging.error(f"💥 Error crítico en el script: {e}")
            time.sleep(60)  # Esperar 1 minuto antes de reintentar

if __name__ == "__main__":
    main() 