# 📚 MANUAL COMPLETO DE EJECUCIÓN

## 🎯 **RESUMEN RÁPIDO**

### Para ejecutar la aplicación:
```bash
cd mi_app
python wsgi.py
```

### Para gestionar el bot de Telegram:
```bash
# Limpiar múltiples instancias y reiniciar
python bot_manager.py --clean

# Reinicio simple
python bot_manager.py --restart

# Verificar token y reiniciar
python bot_manager.py --verify-token

# Instalar dependencias y reiniciar
python bot_manager.py --install-deps

# Verificar configuración de chat ID
python bot_manager.py --check-chat-id
```

### Para hacer git push:
```bash
git add mi_app/mi_app/
git commit -m "Descripción"
git push origin main
```

---

## 🚀 **EJECUCIÓN LOCAL**

### **Método Recomendado (con entorno virtual)**
```bash
cd mi_app
source venv/bin/activate
python wsgi.py
```
**✅ Información del servidor:**
- **URL:** http://127.0.0.1:5000 o http://localhost:5000
- **Puerto:** 5000
- **Modo:** Debug activado
- **Entorno virtual:** `mi_app/venv`

**✅ Ventajas:**
- Funciona igual que en PythonAnywhere
- No requiere cambios en importaciones
- Es el método estándar para producción
- Usa el entorno virtual correcto

### **Opción alternativa (sin venv - no recomendada)**
```bash
cd mi_app
python wsgi.py
```
**⚠️ Nota:** Puede fallar si no tienes las dependencias instaladas globalmente

---

## 🐍 **ENTORNO VIRTUAL**

### **Ubicación del venv:**
```
mi_app/venv/
```

### **Activar entorno virtual:**
```bash
cd mi_app
source venv/bin/activate
```

### **Verificar que está activado:**
- El prompt debe mostrar `(venv)` al inicio
- Ejemplo: `(venv) usuario@mac mi_app %`

### **Desactivar entorno virtual:**
```bash
deactivate
```

### **¿Por qué usar el entorno virtual?**
- ✅ Garantiza las versiones correctas de las dependencias
- ✅ Evita conflictos con otras instalaciones de Python
- ✅ Replica el entorno de producción
- ✅ Previene errores de "módulo no encontrado"

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
│   ├── venv/                 # ✅ Entorno virtual
│   ├── mi_app/               # Aplicación Flask
│   │   ├── app.py            # Aplicación principal
│   │   ├── blueprints/       # Módulos (admin, clientes, etc.)
│   │   ├── templates/        # Plantillas HTML
│   │   ├── static/           # CSS, JS, imágenes
│   │   └── extensions.py     # Configuraciones
│   └── requirements.txt      # Dependencias
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
cd mi_app && source venv/bin/activate && python wsgi.py
```
**Acceder en:** http://localhost:5000

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

## 🤖 **GESTIÓN DEL BOT DE TELEGRAM**

### **Utilidad Centralizada: bot_manager.py**

**✅ Reemplaza todos los scripts SSH anteriores:**
- ~~limpiar_y_reiniciar_bot.py~~ (eliminado)
- ~~reiniciar_bot_telegram.py~~ (eliminado)
- ~~verificar_token_y_reiniciar.py~~ (eliminado)
- ~~instalar_dependencias_y_reiniciar.py~~ (eliminado)
- ~~verificar_chat_id.py~~ (eliminado)

### **Comandos disponibles:**

#### **🧹 Limpiar múltiples instancias:**
```bash
python bot_manager.py --clean
```
- Mata todos los procesos de Telegram
- Limpia logs anteriores
- Inicia una sola instancia
- Verifica que no haya conflictos

#### **🔄 Reinicio simple:**
```bash
python bot_manager.py --restart
```
- Detiene el bot actual
- Verifica token correcto
- Reinicia el bot

#### **🔑 Verificar token:**
```bash
python bot_manager.py --verify-token
```
- Verifica token correcto (8065976460)
- Confirma que no esté el token anterior
- Verifica módulos necesarios
- Reinicia el bot

#### **📦 Instalar dependencias:**
```bash
python bot_manager.py --install-deps
```
- Instala requirements.txt
- Verifica supabase y telebot
- Reinicia el bot

#### **💬 Verificar chat ID:**
```bash
python bot_manager.py --check-chat-id
```
- Muestra chat ID configurado
- Revisa logs de permisos denegados
- Lista chat IDs que intentan usar comandos
- Verifica estado del bot

### **Ventajas de bot_manager.py:**
- ✅ **Una sola herramienta** para todas las operaciones
- ✅ **Código consolidado** sin duplicación
- ✅ **Interfaz consistente** con argumentos claros
- ✅ **Mantenimiento simplificado**
- ✅ **Documentación integrada** (`--help`)

---

## 🔍 **SCRIPTS DE VERIFICACIÓN ESPECÍFICOS**

### **Scripts mantenidos (funciones específicas):**

#### **verificar_cache.py**
```bash
python verificar_cache.py
```
- Verifica asignaciones de transferencias específicas
- Simula comportamiento del backend
- Útil para debugging de asignaciones

#### **verificar_flujo_capital.py**
```bash
python verificar_flujo_capital.py
```
- Verifica datos de flujo de capital
- Identifica fechas faltantes
- Analiza cálculos automáticos

#### **verificar_asignacion.py**
```bash
python verificar_asignacion.py [TRANSFERENCIA_ID]
```
- Verifica estado de asignación de transferencias
- Muestra todas las asignaciones recientes
- Acepta ID específico como parámetro

---

## 📝 **NOTAS IMPORTANTES**

1. **Siempre usa `wsgi.py`** para ejecutar la aplicación
2. **Las importaciones deben ser `mi_app.mi_app.`** para compatibilidad
3. **No subas archivos SQL** al repositorio
4. **PythonAnywhere se actualiza automáticamente** desde git
5. **La aplicación corre en http://localhost:5000** localmente
6. **Usa `bot_manager.py`** para todas las operaciones del bot de Telegram
7. **Los scripts de verificación específicos** siguen disponibles para debugging

---

*Manual creado: 2025-01-03*
*Última actualización: 2025-01-03 - Consolidación de scripts SSH*