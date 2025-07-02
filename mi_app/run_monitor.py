#!/usr/bin/env python3
"""
Script para ejecutar el monitor de archivos bancarios en PythonAnywhere
Este script debe ser ejecutado como una tarea programada
"""

import os
import sys
import time
import logging
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Importar el monitor
from monitor_archivos_bancarios import main

if __name__ == '__main__':
    print("Iniciando monitor de archivos bancarios en PythonAnywhere...")
    print(f"Directorio del proyecto: {project_dir}")
    print(f"Directorio de uploads: {project_dir}/uploads/transferencias/uploads")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitor detenido por el usuario")
    except Exception as e:
        print(f"Error en el monitor: {e}")
        logging.error(f"Error fatal en el monitor: {e}") 