# NOTAS PARA EJECUTAR LA APLICACIÓN

## 🚀 Cómo ejecutar la aplicación web

### Opción 1: Usando wsgi.py (RECOMENDADO)
```bash
cd mi_app
python wsgi.py
```
**Ventajas:**
- Funciona tanto localmente como en PythonAnywhere
- No requiere cambios en las importaciones
- Es la forma estándar para producción

### Opción 2: Usando app.py directamente
```bash
cd mi_app/mi_app
python app.py
```
**Nota:** Esta opción puede requerir ajustes en las importaciones y no es compatible con PythonAnywhere.

## 🔧 Antes de hacer git push

### 1. Verificar que las importaciones sean correctas
Asegúrate de que todos los archivos usen importaciones completas:
```python
# ✅ CORRECTO (para PythonAnywhere)
from mi_app.mi_app.extensions import supabase
from mi_app.mi_app.blueprints.utilidades import adjust_datetime

# ❌ INCORRECTO
from mi_app.extensions import supabase
from mi_app.blueprints.utilidades import adjust_datetime
```

### 2. Archivos que NO subir al git
- `CREATE_CUENTAS_ACTIVAS.sql`
- `README_CUENTAS_ACTIVAS.md`
- `crear_tabla_cuentas_activas.py`
- Archivos de configuración local (.env, etc.)

### 3. Comandos para git
```bash
# Verificar estado
git status

# Agregar solo archivos de la aplicación
git add mi_app/mi_app/app.py
git add mi_app/mi_app/blueprints/
git add mi_app/mi_app/templates/
git add mi_app/mi_app/static/

# Commit
git commit -m "Descripción del cambio"

# Push
git push origin main
```

## 🐛 Solución de problemas comunes

### Error: "No module named 'mi_app.extensions'"
**Causa:** Importaciones incorrectas en blueprints
**Solución:** Cambiar `from mi_app.extensions` por `from mi_app.mi_app.extensions`

### Error: "No module named 'mi_app'"
**Causa:** Ejecutando desde directorio incorrecto
**Solución:** Usar `python wsgi.py` desde el directorio `mi_app/`

## 📝 Estructura del proyecto
```
WEB/
├── mi_app/
│   ├── wsgi.py              # ✅ Punto de entrada principal
│   ├── mi_app/
│   │   ├── app.py           # Aplicación Flask
│   │   ├── blueprints/      # Módulos de la aplicación
│   │   ├── templates/       # Plantillas HTML
│   │   └── static/          # Archivos estáticos
│   └── requirements.txt     # Dependencias
└── venv/                    # Entorno virtual
```

## 🎯 Resumen rápido
1. **Para desarrollo local:** `cd mi_app && python wsgi.py`
2. **Para git:** Solo subir archivos de `mi_app/mi_app/`
3. **Importaciones:** Siempre usar `mi_app.mi_app.`
4. **Puerto:** La aplicación corre en http://localhost:5000

---
*Última actualización: 2025-01-03* 