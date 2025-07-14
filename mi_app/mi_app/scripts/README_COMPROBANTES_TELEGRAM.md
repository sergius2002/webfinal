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

## Instalación

### Dependencias

```bash
pip install pytesseract pillow python-telegram-bot supabase
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
| `/detalle` | Lista todos los montos del día |
| `/total` | Muestra total con duplicados |
| `/total_sin_duplicados` | Muestra total sin duplicados |
| `/ingreso_manual <monto>` | Agrega monto manualmente |
| `/permitir` | Confirma inserción de duplicado |
| `/denegar` | Rechaza inserción de duplicado |
| `/ayuda` | Muestra esta ayuda |

### Ejemplos

```
/ingreso_manual 1.234,56
/detalle
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

## Logs

El script genera logs en:
- **Archivo**: `telegram_comprobantes.log`
- **Consola**: Salida en tiempo real

## Seguridad

- ✅ Detección automática de duplicados
- ✅ Confirmación manual para duplicados
- ✅ Logs detallados de todas las operaciones
- ✅ Validación de datos antes de insertar

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

## Notas Importantes

1. **Independiente de la web**: Este bot funciona por separado
2. **Solo para tareas**: Es una herramienta de apoyo, no reemplaza el sistema principal
3. **Backup automático**: Los datos se guardan en Supabase
4. **Formato boliviano**: Los montos deben estar en formato Bs (1.234,56)

## Soporte

Para problemas o mejoras:
1. Revisar logs en `telegram_comprobantes.log`
2. Verificar conexión a Supabase
3. Comprobar que Tesseract esté instalado correctamente

---

**Autor**: Sistema de Gestión Empresarial  
**Versión**: 1.0  
**Fecha**: 2024 