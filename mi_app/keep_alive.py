#!/usr/bin/env python3
"""
Script para mantener la tarea Always On activa en PythonAnywhere
Este script verifica que el sistema esté funcionando correctamente
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keep_alive.log'),
        logging.StreamHandler()
    ]
)

def verificar_sistema():
    """Verifica que el sistema esté funcionando correctamente"""
    try:
        # Verificar directorios necesarios
        base_dir = Path(__file__).parent
        directorios = [
            base_dir / 'uploads' / 'transferencias' / 'uploads',
            base_dir / 'Bancos',
            base_dir / 'Santander_archivos'
        ]
        
        for directorio in directorios:
            if not directorio.exists():
                directorio.mkdir(parents=True, exist_ok=True)
                logging.info(f"Directorio creado: {directorio}")
            else:
                logging.info(f"Directorio existe: {directorio}")
        
        # Verificar scripts bancarios
        scripts = ['bci.py', 'Santander.py']
        for script in scripts:
            script_path = base_dir / script
            if script_path.exists():
                logging.info(f"Script encontrado: {script}")
            else:
                logging.warning(f"Script no encontrado: {script}")
        
        # Verificar conexión a base de datos (opcional)
        try:
            # Aquí podrías agregar una verificación de conexión a Supabase
            logging.info("Sistema verificado correctamente")
            return True
        except Exception as e:
            logging.error(f"Error verificando base de datos: {e}")
            return False
            
    except Exception as e:
        logging.error(f"Error en verificación del sistema: {e}")
        return False

def main():
    """Función principal"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"=== Verificación del sistema - {timestamp} ===")
    
    if verificar_sistema():
        logging.info("✅ Sistema funcionando correctamente")
        print(f"✅ Sistema OK - {timestamp}")
    else:
        logging.error("❌ Problemas detectados en el sistema")
        print(f"❌ Problemas detectados - {timestamp}")
    
    logging.info("=" * 50)

if __name__ == '__main__':
    main() 