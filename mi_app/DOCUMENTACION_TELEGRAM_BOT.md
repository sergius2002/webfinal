# 🤖 Documentación: Bot de Telegram para Tasas USDT/VES

## 🎯 Descripción
Este bot de Telegram permite consultar tasas de cambio USDT/VES y ver compras en tiempo real. Está diseñado para ejecutarse como una tarea "Always On Task" en PythonAnywhere.

## ✅ Requisitos Previos

### 1. Dependencias
Todas las dependencias necesarias ya están incluidas en `requirements.txt`:
- `pyTelegramBotAPI==4.15.2`
- `supabase==2.16.0`
- `pandas==2.1.4`
- `pytz==2024.1`
- `Pillow` (para generar imágenes de tablas)

### 2. Configuración de Credenciales
El script actual usa credenciales por defecto. Para producción, debes:

#### Opción A: Variables de Entorno (Recomendado)
Crear un archivo `.env` en la raíz del proyecto:
```bash
# Telegram Bot
CHAT_ID_TELEGRAM=tu_chat_id
TOKEN_TELEGRAM=tu_token_bot

# Supabase
SUPABASE_URL=tu_url_supabase
SUPABASE_KEY=tu_key_supabase
```

#### Opción B: Modificar el Script
Editar directamente las credenciales en `telegram_bot_always.py`:
```python
# Líneas 67-68: Credenciales de Telegram
chat_id_telegram = os.getenv('CHAT_ID_TELEGRAM', 'tu_chat_id')
token_telegram = os.getenv('TOKEN_TELEGRAM', 'tu_token_bot')
```

## 🚀 Configuración en PythonAnywhere

### 1. Subir el Script
1. Ve a la pestaña **Files** en PythonAnywhere
2. Navega a `/home/sacristobalspa/webfinal/mi_app/`
3. Sube el archivo `telegram_bot_always.py`

### 2. Configurar Always Task
1. Ve a la pestaña **Tasks** en PythonAnywhere
2. En la sección **Always-on tasks**, agrega una nueva tarea:
   ```
   Command: python3 /home/sacristobalspa/webfinal/mi_app/telegram_bot_always.py
   ```

### 3. Verificar Permisos
En la consola de PythonAnywhere, ejecuta:
```bash
chmod +x /home/sacristobalspa/webfinal/mi_app/telegram_bot_always.py
```

## 📱 Comandos del Bot

### 1. `/tasa`
Muestra las tasas actuales de USDT/VES para Banesco y Venezuela.

**Ejemplo de respuesta:**
```
┌─────────┬──────────┐
│ Banco   │ Tasa     │
├─────────┼──────────┤
│ Banesco │ 3.456789 │
│ Venezuela│ 3.234567 │
└─────────┴──────────┘
```

### 2. `/compras [fecha]`
Muestra las compras del día (o fecha específica).

**Uso:**
- `/compras` - Compras del día actual
- `/compras 2024-06-30` - Compras de una fecha específica

**Ejemplo de respuesta:**
```
┌──────┬─────────┬──────────┬──────────┐
│ Hora │ Banco   │ Brs      │ Tasa     │
├──────┼─────────┼──────────┼──────────┤
│ 14:30│ Banesco │ 1,000,000│ 3.456789 │
│ 13:15│ Venezuela│ 500,000 │ 3.234567 │
└──────┴─────────┴──────────┴──────────┘
```

### 3. `/help` o `/start`
Muestra la ayuda con todos los comandos disponibles.

## 🔧 Funcionalidades del Bot

### 1. Generación de Tablas
- **Estilo Excel**: Tablas con formato profesional
- **Colores alternados**: Filas con colores alternados para mejor legibilidad
- **Bordes**: Bordes en cada celda como en Excel
- **Nitidez**: Imágenes optimizadas para mejor calidad

### 2. Seguridad
- **Chat ID restringido**: Solo responde al chat configurado
- **Validación de permisos**: Verifica que el usuario tenga acceso
- **Manejo de errores**: Respuestas amigables en caso de errores

### 3. Logging Detallado
- Logs se guardan en `/home/sacristobalspa/webfinal/mi_app/telegram_bot.log`
- Registra cada comando ejecutado
- Manejo robusto de errores

## 📊 Monitoreo

### 1. Verificar Logs
```bash
tail -f /home/sacristobalspa/webfinal/mi_app/telegram_bot.log
```

### 2. Verificar Estado de la Tarea
En PythonAnywhere → Tasks → Always-on tasks, verás:
- ✅ **Running**: Bot ejecutándose correctamente
- ❌ **Stopped**: Bot detenido (revisar logs)

### 3. Logs Esperados
```
🚀 Bot de Telegram iniciado. Esperando comandos...
✅ Comando /tasa ejecutado exitosamente para chat -4090514300
✅ Comando /compras ejecutado exitosamente para chat -4090514300
```

## ⚠️ Consideraciones Importantes

### 1. Configuración del Bot de Telegram
1. **Crear bot**: Usar @BotFather en Telegram
2. **Obtener token**: Guardar el token del bot
3. **Obtener Chat ID**: Usar @userinfobot para obtener el Chat ID
4. **Configurar permisos**: Asegurar que solo usuarios autorizados usen el bot

### 2. Dependencias de Imágenes
- **Pillow**: Para generar tablas como imágenes
- **Fuentes**: Usa fuentes del sistema para mejor calidad
- **Memoria**: Las imágenes se generan en memoria

### 3. Rate Limits
- **Telegram**: Respeta los límites de la API de Telegram
- **Supabase**: Respeta los límites de consultas a la base de datos

## 🔍 Troubleshooting

### Problema: "Module not found"
**Solución**: Verificar que todas las dependencias estén instaladas:
```bash
pip3 install -r /home/sacristobalspa/webfinal/mi_app/requirements.txt
```

### Problema: "Permission denied"
**Solución**: Verificar permisos del script:
```bash
chmod +x /home/sacristobalspa/webfinal/mi_app/telegram_bot_always.py
```

### Problema: "Bot not responding"
**Solución**: 
1. Verificar que el token del bot sea correcto
2. Verificar que el Chat ID sea correcto
3. Revisar logs para errores específicos

### Problema: "No data found"
**Solución**: Verificar que la tabla `vista_compras_fifo` tenga datos

## 📈 Optimizaciones Futuras

1. **Múltiples chats**: Permitir múltiples chats autorizados
2. **Notificaciones automáticas**: Enviar alertas cuando las tasas cambien
3. **Gráficos**: Agregar gráficos de evolución de tasas
4. **Comandos adicionales**: Más funcionalidades como estadísticas

## 🔐 Seguridad

### Credenciales de Producción
⚠️ **IMPORTANTE**: Nunca uses credenciales de prueba en producción:
1. Crea un bot real en Telegram con @BotFather
2. Obtén el Chat ID real de tu grupo/canal
3. Usa variables de entorno para las credenciales
4. Rota las credenciales periódicamente

### Logs Sensibles
El bot no logea información sensible, pero verifica que no se expongan credenciales en los logs.

## 🎯 Uso en Producción

### 1. Configurar Bot Real
```bash
# En .env
CHAT_ID_TELEGRAM=-1001234567890
TOKEN_TELEGRAM=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Probar Comandos
1. Enviar `/start` al bot
2. Probar `/tasa`
3. Probar `/compras`
4. Verificar que las tablas se generen correctamente

### 3. Monitoreo Continuo
```bash
# Monitorear logs en tiempo real
tail -f /home/sacristobalspa/webfinal/mi_app/telegram_bot.log

# Verificar estado del bot
ps aux | grep telegram_bot_always.py
``` 