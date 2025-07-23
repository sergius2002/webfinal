# COMANDOS Y REGLAS PARA RECORDAR

## 🚨 REGLA MÁS IMPORTANTE - SIEMPRE VERIFICAR TERMINALES:
**ANTES de monitorear, SIEMPRE verificar:**
1. **¿El proceso está corriendo?** `ps aux | grep wsgi.py`
2. **¿Existe el archivo de log?** `ls -la server.log`
3. **¿El puerto está ocupado?** `lsof -ti:5001`
4. **Si algo falla, ejecutar directamente:** `python wsgi.py` (sin &) para ver el error

**NUNCA intentar monitorear sin verificar primero si el servidor está funcionando.**

## 🚨 REGLAS IMPORTANTES:
1. **SIEMPRE responder** aunque no tengas solución inmediata
2. **SIEMPRE verificar terminales** antes de monitorear
3. **SIEMPRE monitorear logs en segundo plano** con `tail -f server.log &`
4. **SIEMPRE recordar** que el puerto 5000 está ocupado por ControlCenter de macOS
5. **SIEMPRE usar puerto 5001** para el servidor Flask
6. **SIEMPRE matar todos los procesos conflictivos** cuando el usuario lo pida

## 🔧 SECUENCIA EXACTA PARA INICIALIZAR SERVIDOR:

### 1. MATAR TODOS LOS PROCESOS CONFLICTIVOS:
```bash
ps aux | grep wsgi.py | grep -v grep
kill -9 [PID1] [PID2] [PID3]
```

### 2. IR AL DIRECTORIO CORRECTO:
```bash
cd /Users/sergioplaza/Library/CloudStorage/OneDrive-Personal/Sergio/WEB/mi_app
```

### 3. LANZAR SERVIDOR DIRECTAMENTE:
```bash
source venv/bin/activate
python wsgi.py
```

### 4. MONITOREAR DESDE DIRECTORIO CORRECTO:
```bash
tail -f server.log &
```

## 🌐 URL DEL SERVIDOR:
- **PUERTO 5000:** http://127.0.0.1:5000 (por defecto)
- **Tasa Actual:** http://127.0.0.1:5000/admin/tasa_actual

## 📝 NOTAS:
- El puerto 5000 está ocupado por ControlCenter de macOS (AirPlay/Handoff)
- NO intentar eliminar ControlCenter (es proceso del sistema)
- SIEMPRE usar puerto 5001 para evitar conflictos
- SIEMPRE monitorear logs en segundo plano
- SIEMPRE responder al usuario aunque no tengas solución inmediata

## 🔍 VERIFICACIÓN:
```bash
# Verificar que el servidor esté corriendo
ps aux | grep wsgi.py
# Verificar que el puerto 5001 esté ocupado
lsof -ti:5001
# Verificar logs
tail -f server.log
``` 