# 📊 Documentación: Script de Sincronización Binance P2P

## 🎯 Descripción
Este script sincroniza automáticamente los datos de transacciones P2P de Binance con la base de datos Supabase. Está diseñado para ejecutarse como una tarea "Always On Task" en PythonAnywhere.

## ✅ Requisitos Previos

### 1. Dependencias
Todas las dependencias necesarias ya están incluidas en `requirements.txt`:
- `python-binance==1.0.19`
- `supabase==2.16.0`
- `pandas==2.1.4`
- `pytz==2024.1`

### 2. Configuración de Credenciales
El script actual usa credenciales de **pruebas**. Para producción, debes:

#### Opción A: Variables de Entorno (Recomendado)
Crear un archivo `.env` en la raíz del proyecto:
```bash
# Binance API (Reemplazar con credenciales reales)
BINANCE_API_KEY=tu_api_key_real
BINANCE_API_SECRET=tu_api_secret_real

# Supabase (Reemplazar con credenciales reales)
SUPABASE_URL=tu_url_supabase
SUPABASE_KEY=tu_key_supabase
```

#### Opción B: Modificar el Script
Editar directamente las credenciales en `binance_updater_always.py`:
```python
# Líneas 75-76: Credenciales de Binance
api_key = 'tu_api_key_real'
api_secret = 'tu_api_secret_real'

# Líneas 79-80: Credenciales de Supabase
supabase_url = "tu_url_supabase"
supabase_key = "tu_key_supabase"
```

## 🚀 Configuración en PythonAnywhere

### 1. Subir el Script
1. Ve a la pestaña **Files** en PythonAnywhere
2. Navega a `/home/sacristobalspa/webfinal/mi_app/`
3. Sube el archivo `binance_updater_always.py`

### 2. Configurar Always Task
1. Ve a la pestaña **Tasks** en PythonAnywhere
2. En la sección **Always-on tasks**, agrega una nueva tarea:
   ```
   Command: python3 /home/sacristobalspa/webfinal/mi_app/binance_updater_always.py
   ```

### 3. Verificar Permisos
En la consola de PythonAnywhere, ejecuta:
```bash
chmod +x /home/sacristobalspa/webfinal/mi_app/binance_updater_always.py
```

## 📋 Estructura de la Base de Datos

### Tabla `compras` en Supabase
El script espera una tabla con la siguiente estructura:
```sql
CREATE TABLE compras (
    ordernumber TEXT PRIMARY KEY,
    tradetype TEXT,
    asset TEXT,
    fiat TEXT,
    amount NUMERIC,
    totalprice NUMERIC,
    unitprice NUMERIC,
    commission NUMERIC,
    orderstatus TEXT,
    createtime TIMESTAMP,
    paymethodname TEXT
);
```

## 🔧 Funcionalidades del Script

### 1. Sincronización Automática
- Se ejecuta cada **1 minuto**
- Filtra solo transacciones **COMPLETED**
- Evita duplicados usando `ordernumber` como clave única

### 2. Procesamiento de Datos
- Convierte timestamps de UTC a zona horaria de Argentina
- Normaliza métodos de pago (SpecificBank/BANK → Venezuela)
- Ajusta comisiones usando `takerCommission` cuando está disponible

### 3. Logging Detallado
- Logs se guardan en `/home/sacristobalspa/webfinal/mi_app/binance_updater.log`
- Muestra estadísticas cada 10 ejecuciones
- Manejo robusto de errores

## 📊 Monitoreo

### 1. Verificar Logs
```bash
tail -f /home/sacristobalspa/webfinal/mi_app/binance_updater.log
```

### 2. Verificar Estado de la Tarea
En PythonAnywhere → Tasks → Always-on tasks, verás:
- ✅ **Running**: Script ejecutándose correctamente
- ❌ **Stopped**: Script detenido (revisar logs)

### 3. Estadísticas en Logs
```
📊 Estadísticas: 45 exitosas, 2 fallidas
```

## ⚠️ Consideraciones Importantes

### 1. Límites de API de Binance
- **Rate Limits**: El script respeta los límites de la API
- **Intervalo**: 1 minuto entre consultas para evitar sobrecarga

### 2. Zona Horaria
- Configurado para zona horaria de Argentina
- Ajuste manual de -2 horas para sincronización

### 3. Manejo de Errores
- Reintentos automáticos en caso de fallos
- Logs detallados para debugging
- No se detiene por errores temporales

## 🔍 Troubleshooting

### Problema: "Module not found"
**Solución**: Verificar que todas las dependencias estén instaladas:
```bash
pip3 install -r /home/sacristobalspa/webfinal/mi_app/requirements.txt
```

### Problema: "Permission denied"
**Solución**: Verificar permisos del script:
```bash
chmod +x /home/sacristobalspa/webfinal/mi_app/binance_updater_always.py
```

### Problema: "API Error"
**Solución**: Verificar credenciales de Binance y Supabase en el script

### Problema: "No data received"
**Solución**: Verificar que la API de Binance esté funcionando y las credenciales sean correctas

## 📈 Optimizaciones Futuras

1. **Variables de Entorno**: Migrar credenciales a archivo `.env`
2. **Configuración Dinámica**: Permitir ajustar intervalos desde configuración
3. **Múltiples Assets**: Extender para otros activos además de USDT
4. **Métricas Avanzadas**: Agregar dashboard de métricas de sincronización

## 🔐 Seguridad

### Credenciales de Producción
⚠️ **IMPORTANTE**: Nunca uses credenciales de pruebas en producción:
1. Crea una cuenta de API real en Binance
2. Configura permisos mínimos necesarios
3. Usa variables de entorno para las credenciales
4. Rota las credenciales periódicamente

### Logs Sensibles
El script no logea información sensible, pero verifica que no se expongan credenciales en los logs. 