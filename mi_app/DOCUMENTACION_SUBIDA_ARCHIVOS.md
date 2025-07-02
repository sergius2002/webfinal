# 📁 Documentación: Subida de Archivos Bancarios

## 🎯 **Resumen**

El sistema permite subir archivos XLSX de bancos (BCI y Santander) que se procesan automáticamente para extraer transferencias. **Hay dos modos de operación:**

### **🔄 Modo 1: Procesamiento Inmediato (ACTUAL)**
- Los archivos se procesan **inmediatamente** al subirlos
- **No requiere monitor externo**
- Ideal para **PythonAnywhere** y **desarrollo local**

### **⏰ Modo 2: Monitor Automático (OPCIONAL)**
- Los archivos se guardan y un monitor los procesa en segundo plano
- Requiere configurar una tarea programada
- Ideal para **servidores dedicados**

---

## 🚀 **Modo 1: Procesamiento Inmediato (Recomendado)**

### **¿Cómo Funciona?**
1. Usuario sube archivo XLSX
2. Sistema detecta automáticamente el banco (BCI o Santander)
3. Archivo se copia a la carpeta correspondiente
4. Script del banco se ejecuta inmediatamente
5. Resultado se muestra al usuario

### **Ventajas:**
- ✅ **Respuesta inmediata al usuario**
- ✅ **Fácil de debuggear**
- ✅ **Procesamiento automático**

### **⚠️ Requisito:**
- 🔄 **Necesita una tarea Always On en PythonAnywhere** para que los scripts bancarios funcionen correctamente

### **Configuración en PythonAnywhere:**
**Necesitas configurar una tarea Always On** para que el procesamiento funcione correctamente:

#### **Opción 1: Tarea Simple (Recomendada)**
```bash
# Comando
cd /home/tuusuario/mi_app && python3 keep_alive.py

# Programación: Cada 25 minutos
*/25 * * * *
```

#### **Opción 2: Tarea con Monitor**
```bash
# Comando
cd /home/tuusuario/mi_app && python3 run_monitor.py

# Programación: Cada 5 minutos
*/5 * * * *
```

---

## ⏰ **Modo 2: Monitor Automático (Opcional)**

### **¿Cuándo Usarlo?**
- Si tienes un servidor dedicado
- Si quieres procesar archivos en segundo plano
- Si necesitas más control sobre el procesamiento

### **Configuración:**

#### **1. Crear Tarea Programada en PythonAnywhere:**
```bash
# Comando
cd /home/tuusuario/mi_app && python3 run_monitor.py

# Programación: Cada 5 minutos
*/5 * * * *
```

#### **2. Para Desarrollo Local:**
```bash
cd mi_app
./iniciar_monitor.sh start
```

#### **3. Verificar Estado:**
```bash
./iniciar_monitor.sh status
```

---

## 📋 **Estructura de Archivos**

```
mi_app/
├── uploads/transferencias/uploads/  # Archivos subidos por usuarios
├── Bancos/                          # Archivos BCI procesados
├── Santander_archivos/              # Archivos Santander procesados
├── monitor_archivos_bancarios.py    # Script del monitor
├── run_monitor.py                   # Script para PythonAnywhere
└── iniciar_monitor.sh               # Control del monitor
```

---

## 🔧 **Scripts de Procesamiento**

### **BCI (`bci.py`)**
- **Entrada:** `Bancos/excel_detallado.xlsx`
- **Salida:** Transferencias en base de datos
- **Palabra clave:** `Movimientos_Detallado_Cuenta`

### **Santander (`Santander.py`)**
- **Entrada:** `Santander_archivos/[archivo].xlsx`
- **Salida:** Transferencias en base de datos
- **Palabra clave:** `CartolaMovimiento-`

---

## 📊 **Base de Datos**

### **Tabla: `archivos_subidos`**
```sql
- id: Identificador único
- nombre_archivo: Nombre del archivo guardado
- nombre_original: Nombre original del archivo
- ruta_archivo: Ruta física del archivo
- usuario: Usuario que subió el archivo
- estado: 'en_proceso', 'procesado', 'error'
- mensaje_error: Mensaje de error o éxito
- fecha_subida: Fecha y hora de subida
- tamano_archivo: Tamaño en bytes
```

---

## ⚙️ **Configuración Paso a Paso en PythonAnywhere**

### **1. Ir a la Sección Tasks**
- Inicia sesión en PythonAnywhere
- Ve a la pestaña **"Tasks"**

### **2. Crear Nueva Tarea**
- Haz clic en **"Add a new task"**

### **3. Configurar la Tarea**
```bash
# Comando (reemplaza 'tuusuario' con tu usuario)
cd /home/tuusuario/mi_app && python3 keep_alive.py

# Programación
*/25 * * * *
```

### **4. Guardar y Activar**
- Haz clic en **"Create"**
- La tarea se ejecutará automáticamente

### **5. Verificar Funcionamiento**
- Ve a la pestaña **"Files"**
- Navega a `mi_app/keep_alive.log`
- Deberías ver mensajes de verificación

---

## 🎯 **Recomendación**

**Para la mayoría de casos, usa el Modo 1 (Procesamiento Inmediato):**

1. ✅ **Más simple de configurar**
2. ✅ **Funciona en PythonAnywhere**
3. ✅ **Respuesta inmediata**
4. ✅ **Fácil de mantener**

**Solo usa el Modo 2 si:**
- Tienes un servidor dedicado
- Necesitas procesamiento en segundo plano
- Quieres más control sobre el timing

---

## 🚨 **Solución de Problemas**

### **Error: "Script no encontrado"**
- Verifica que `bci.py` y `Santander.py` existan en el directorio raíz
- Asegúrate de que tengan permisos de ejecución

### **Error: "Timeout"**
- Los scripts tienen un límite de 5 minutos
- Verifica que los archivos no sean muy grandes

### **Error: "Permisos"**
- En PythonAnywhere, asegúrate de que las carpetas tengan permisos correctos
- Usa `chmod +x` para los scripts si es necesario

---

## 📞 **Soporte**

Si tienes problemas:
1. Revisa los logs en la consola de PythonAnywhere
2. Verifica que los archivos de ejemplo funcionen
3. Comprueba que las carpetas de destino existan 