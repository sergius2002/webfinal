# Bot de Comprobantes Bancarios - Telegram

## Descripción

Este script es una herramienta de apoyo independiente que permite procesar comprobantes bancarios a través de Telegram. **No está integrado directamente con la web**, sino que funciona como una herramienta auxiliar para la empresa.

## Funcionalidades

- 📸 **OCR Automático**: Procesa imágenes de comprobantes bancarios
- 💰 **Extracción de Datos**: Detecta montos, fechas y números de operación
- 🗄️ **Almacenamiento**: Guarda datos en Supabase
- 🔍 **Detección de Duplicados**: Identifica comprobantes repetidos
- 📊 **Cálculo de Totales**: Suma automática de montos diarios
- 📝 **Ingreso Manual**: Permite agregar montos manualmente
- 👤 **Detección de Usuarios**: Registra quién envía cada comprobante
- 📈 **Estadísticas por Usuario**: Muestra resúmenes por persona
- 🎯 **Totales Personalizados**: Cada usuario ve su contribución individual

## Instalación

### Dependencias

```bash
pip install pytesseract pillow python-telegram-bot supabase requests
```

### Tesseract OCR

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**Windows:**
Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki

## Configuración

1. **Token de Telegram**: Obtener de @BotFather
2. **Chat ID**: ID del grupo/canal donde funcionará el bot
3. **Supabase**: Configurar URL y API key

## Base de Datos

### Actualizar tabla comprobantes

Ejecutar el script SQL `ACTUALIZAR_TABLA_COMPROBANTES.sql` en Supabase para agregar los campos de usuario:

```sql
-- Ejecutar en Supabase SQL Editor
ALTER TABLE comprobantes 
ADD COLUMN IF NOT EXISTS usuario_id BIGINT,
ADD COLUMN IF NOT EXISTS usuario_username TEXT,
ADD COLUMN IF NOT EXISTS usuario_nombre TEXT,
ADD COLUMN IF NOT EXISTS usuario_apellido TEXT,
ADD COLUMN IF NOT EXISTS timestamp_envio TIMESTAMP WITH TIME ZONE;
```

## Uso

### Ejecutar el bot

```bash
cd mi_app/mi_app/scripts
python sumar_comprobantes_telegram.py
```

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| Enviar foto | Procesa automáticamente el comprobante |
| `/detalle` | Lista todos los montos del día con usuarios |
| `/total` | Muestra total con duplicados |
| `/total_sin_duplicados` | Muestra total sin duplicados |
| `/ingreso_manual <monto>` | Agrega monto manualmente |
| `/permitir` | Confirma inserción de duplicado |
| `/denegar` | Rechaza inserción de duplicado |
| `/estadisticas` | Ver estadísticas por usuario |

### 📊 Comandos Personales

| Comando | Descripción |
|---------|-------------|
| `/mi_total` | Ver tu total personal vs general |
| `/mi_detalle` | Ver tus comprobantes del día |
| `/ayuda` | Mostrar ayuda completa |

### Ejemplos

```
/ingreso_manual 1.234,56
/detalle
/estadisticas
/mi_total
/mi_detalle
/total_sin_duplicados
```

## Estructura de Datos

### Tabla `comprobantes` en Supabase

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `fecha` | text | Fecha del comprobante (DD/MM/YYYY) |
| `brs` | numeric | Monto en bolivianos |
| `operacion` | text | Número de operación |
| `hash` | text | Hash único del comprobante |
| `es_duplicado` | boolean | Si es un duplicado permitido |
| `usuario_id` | bigint | ID único del usuario de Telegram |
| `usuario_username` | text | Username del usuario de Telegram |
| `usuario_nombre` | text | Nombre del usuario de Telegram |
| `usuario_apellido` | text | Apellido del usuario de Telegram |
| `timestamp_envio` | timestamp | Cuando se envió el comprobante |

## Funcionalidades de Usuario

### Detección Automática
- ✅ Registra automáticamente quién envía cada comprobante
- ✅ Almacena nombre, username, ID y timestamp
- ✅ Muestra información del usuario en cada respuesta

### Respuesta al Enviar Comprobante
Cuando envías una foto, recibes:
```
Monto detectado: 50.000,00 Bs
Enviado por: Juan Pérez (@juanperez)
✅ Comprobante registrado exitosamente
📊 Tu total personal: 125.000,00 Bs
🌐 Total general: 250.000,00 Bs
```

### Comando `/detalle`
Muestra listado con formato:
```
1. 50.000,00 Bs - Juan Pérez (@juanperez)
2. 25.000,00 Bs - María García (@mariagarcia)
3. 35.000,00 Bs - Carlos López (@carloslopez)

Total: 110.000,00 Bs
```

### Comando `/estadisticas`
Muestra resumen por usuario:
```
📊 Estadísticas por usuario (14/07/2025):

• Juan Pérez (@juanperez): 3 comprobantes - 75.000,00 Bs
• María García (@mariagarcia): 2 comprobantes - 45.000,00 Bs
• Carlos López (@carloslopez): 1 comprobante - 35.000,00 Bs

Total general: 155.000,00 Bs
```

### Comando `/mi_total`
Muestra tu resumen personal:
```
📊 Resumen personal de Juan Pérez (@juanperez)

💰 Tu total: 75.000,00 Bs
🌐 Total general: 155.000,00 Bs
📈 Porcentaje: 48.4%
```

### Comando `/mi_detalle`
Muestra tus comprobantes del día:
```
📋 Tus comprobantes del día (14/07/2025):

1. 25.000,00 Bs 14:30
2. 30.000,00 Bs 15:45
3. 20.000,00 Bs 16:20

💰 Tu total: 75.000,00 Bs
🌐 Total general: 155.000,00 Bs
📈 Porcentaje: 48.4%
```

## Logs

El script genera logs en:
- **Archivo**: `telegram_comprobantes.log`
- **Consola**: Salida en tiempo real
- **Formato**: `Usuario (@username): OCR recibido`

## Seguridad

- ✅ Detección automática de duplicados
- ✅ Confirmación manual para duplicados
- ✅ Logs detallados de todas las operaciones
- ✅ Validación de datos antes de insertar
- ✅ Registro de usuarios para auditoría
- ✅ Totales personalizados por usuario

## Mantenimiento

### Reiniciar el bot
```bash
# Detener proceso actual
pkill -f sumar_comprobantes_telegram.py

# Reiniciar
python sumar_comprobantes_telegram.py
```

### Verificar logs
```bash
tail -f telegram_comprobantes.log
```

### Consultar usuarios activos
```sql
-- En Supabase SQL Editor
SELECT DISTINCT usuario_nombre, usuario_username, COUNT(*) as comprobantes
FROM comprobantes 
WHERE fecha = '14/07/2025'
GROUP BY usuario_nombre, usuario_username
ORDER BY comprobantes DESC;
```

### Consultar totales por usuario
```sql
-- En Supabase SQL Editor
SELECT 
    usuario_nombre,
    usuario_username,
    COUNT(*) as comprobantes,
    SUM(brs) as total_brs
FROM comprobantes 
WHERE fecha = '14/07/2025'
GROUP BY usuario_nombre, usuario_username
ORDER BY total_brs DESC;
```

## Notas Importantes

1. **Independiente de la web**: Este bot funciona por separado
2. **Solo para tareas**: Es una herramienta de apoyo, no reemplaza el sistema principal
3. **Backup automático**: Los datos se guardan en Supabase
4. **Formato boliviano**: Los montos deben estar en formato Bs (1.234,56)
5. **Detección de usuarios**: Registra automáticamente quién envía cada comprobante
6. **Auditoría completa**: Timestamp y usuario en cada registro
7. **Totales personalizados**: Cada usuario ve su contribución individual
8. **Porcentajes**: Muestra qué porcentaje del total representa cada usuario

## Soporte

Para problemas o mejoras:
1. Revisar logs en `telegram_comprobantes.log`
2. Verificar conexión a Supabase
3. Comprobar que Tesseract esté instalado correctamente
4. Ejecutar script SQL para actualizar tabla si es necesario

---

**Autor**: Sistema de Gestión Empresarial  
**Versión**: 3.0  
**Fecha**: 2024  
**Nuevas funcionalidades**: Detección de usuarios, estadísticas, auditoría completa, totales personalizados 