#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo WSGI para despliegue en PythonAnywhere
Configura la aplicación Flask para producción
"""

import os
import sys
import signal
import multiprocessing

# Asegura que el path raíz esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importar la aplicación Flask
from mi_app.mi_app.app import app as application

def cleanup_resources(signum=None, frame=None):
    """Limpia recursos al cerrar la aplicación"""
    try:
        # Limpiar recursos de multiprocessing
        multiprocessing.current_process()._cleanup()
    except:
        pass
    
    # Salir limpiamente
    sys.exit(0)

# Registrar manejadores de señales
signal.signal(signal.SIGINT, cleanup_resources)
signal.signal(signal.SIGTERM, cleanup_resources)

# Configuración adicional para producción
if __name__ == "__main__":
    try:
        application.run(debug=True)
    except KeyboardInterrupt:
        cleanup_resources()
    finally:
        cleanup_resources() 