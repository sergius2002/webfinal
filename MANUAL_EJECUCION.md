# 📚 MANUAL COMPLETO DE EJECUCIÓN

## 🎯 **RESUMEN RÁPIDO**

### Para ejecutar la aplicación:
```bash
cd mi_app
python wsgi.py
```

### Para hacer git push:
```bash
git add mi_app/mi_app/
git commit -m "Descripción"
git push origin main
```

---

## 🚀 **EJECUCIÓN LOCAL**

### **Opción 1: Método Recomendado (wsgi.py)**
```bash
cd mi_app
python wsgi.py
```
**✅ Ventajas:**
- Funciona igual que en PythonAnywhere
- No requiere cambios en importaciones
- Es el método estándar para producción

### **Opción 2: Método Directo (app.py)**
```bash
cd mi_app/mi_app
python app.py
```
**⚠️ Requisitos:**
- Las importaciones deben ser `mi_app.mi_app.extensions`
- No es compatible con PythonAnywhere

---

## 🌐 **EJECUCIÓN EN PYTHONANYWHERE**

### **Configuración automática:**
- PythonAnywhere usa automáticamente `wsgi.py`
- Las importaciones deben ser: `mi_app.mi_app.extensions`
- No requiere cambios adicionales

### **Si hay errores de importación:**
```
ModuleNotFoundError: No module named 'mi_app.extensions'
```
**Solución:** Cambiar a `mi_app.mi_app.extensions`

---

## 🔧 **IMPORTACIONES CORRECTAS**

### **✅ CORRECTO (para ambos entornos):**
```python
from mi_app.mi_app.extensions import supabase
from mi_app.mi_app.blueprints.utilidades import adjust_datetime
from mi_app.mi_app.blueprints.admin import login_required
```

### **❌ INCORRECTO:**
```python
from mi_app.extensions import supabase
from mi_app.blueprints.utilidades import adjust_datetime
from mi_app.blueprints.admin import login_required
```

---

## 📁 **ESTRUCTURA DEL PROYECTO**

```
WEB/
├── mi_app/                    # Directorio principal
│   ├── wsgi.py               # ✅ Punto de entrada
│   ├── mi_app/               # Aplicación Flask
│   │   ├── app.py            # Aplicación principal
│   │   ├── blueprints/       # Módulos (admin, clientes, etc.)
│   │   ├── templates/        # Plantillas HTML
│   │   ├── static/           # CSS, JS, imágenes
│   │   └── extensions.py     # Configuraciones
│   └── requirements.txt      # Dependencias
├── venv/                     # Entorno virtual
└── MANUAL_EJECUCION.md       # Este archivo
```

---

## 🔄 **FLUJO DE TRABAJO CON GIT**

### **1. Verificar cambios:**
```bash
git status
```

### **2. Agregar archivos (SOLO aplicación):**
```bash
# Agregar archivos de la aplicación
git add mi_app/mi_app/app.py
git add mi_app/mi_app/blueprints/
git add mi_app/mi_app/templates/
git add mi_app/mi_app/static/

# NO agregar archivos SQL o de configuración
# ❌ git add mi_app/CREATE_CUENTAS_ACTIVAS.sql
# ❌ git add mi_app/README_CUENTAS_ACTIVAS.md
```

### **3. Commit y Push:**
```bash
git commit -m "Descripción del cambio"
git push origin main
```

---

## 🐛 **SOLUCIÓN DE PROBLEMAS**

### **Error: "No module named 'mi_app'":**
```
ModuleNotFoundError: No module named 'mi_app'
```
**Causa:** Ejecutando desde directorio incorrecto
**Solución:** 
```bash
cd mi_app
python wsgi.py
```

### **Error: "No module named 'mi_app.extensions'":**
```
ModuleNotFoundError: No module named 'mi_app.extensions'
```
**Causa:** Importaciones incorrectas en blueprints
**Solución:** Cambiar en el archivo:
```python
# ANTES:
from mi_app.extensions import supabase

# DESPUÉS:
from mi_app.mi_app.extensions import supabase
```

### **Error: "can't open file 'app.py'":**
```
can't open file '/path/app.py': [Errno 2] No such file or directory
```
**Causa:** Ejecutando desde directorio incorrecto
**Solución:** 
```bash
cd mi_app
python wsgi.py
```

---

## 📋 **CHECKLIST ANTES DE GIT PUSH**

- [ ] ¿Las importaciones usan `mi_app.mi_app.`?
- [ ] ¿Estoy agregando solo archivos de la aplicación?
- [ ] ¿No estoy subiendo archivos SQL?
- [ ] ¿La aplicación funciona localmente con `python wsgi.py`?
- [ ] ¿El mensaje de commit es descriptivo?

---

## 🎯 **COMANDOS RÁPIDOS**

### **Ejecutar aplicación:**
```bash
cd mi_app && python wsgi.py
```

### **Verificar git:**
```bash
git status
```

### **Agregar cambios:**
```bash
git add mi_app/mi_app/
```

### **Commit y push:**
```bash
git commit -m "Descripción" && git push origin main
```

---

## 📝 **NOTAS IMPORTANTES**

1. **Siempre usa `wsgi.py`** para ejecutar la aplicación
2. **Las importaciones deben ser `mi_app.mi_app.`** para compatibilidad
3. **No subas archivos SQL** al repositorio
4. **PythonAnywhere se actualiza automáticamente** desde git
5. **La aplicación corre en http://localhost:5000** localmente

---

*Manual creado: 2025-01-03*
*Última actualización: 2025-01-03* 