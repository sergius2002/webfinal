#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivo WSGI para despliegue en PythonAnywhere
Configura la aplicación Flask para producción
"""

import os
import sys

# Asegura que el path raíz esté en sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importar la aplicación Flask
from mi_app.mi_app.app import app as application

# Configuración adicional para producción
if __name__ == "__main__":
    application.run(debug=True) 