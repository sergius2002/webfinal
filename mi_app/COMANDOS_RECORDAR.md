# 🚨 COMANDOS Y REGLAS QUE DEBO RECORDAR SIEMPRE

## 🚨 REGLAS FUNDAMENTALES:
1. **SIEMPRE RESPONDER** - Incluso si no tengo respuesta (INACEPTABLE no responder)
2. **HACER EXACTAMENTE LO QUE PIDES** - No desviarme
3. **MONITOREO EN SEGUNDO PLANO** - Para poder conversar sin cerrar terminal

## 🖥️ COMANDOS PARA MONITOREO:
```bash
# 1. Matar procesos anteriores
pkill -f "python.*wsgi.py"

# 2. Lanzar servidor en segundo plano
cd mi_app && source venv/bin/activate && python wsgi.py > server.log 2>&1 &

# 3. Monitorear logs en segundo plano
tail -f server.log &

# 4. MANTENER TERMINAL ABIERTA para conversar
```

## 📍 DIRECTORIO CORRECTO:
- **Ubicación:** `/Users/sergioplaza/Library/CloudStorage/OneDrive-Personal/Sergio/WEB/mi_app`
- **Entorno virtual:** `venv/bin/activate`
- **Archivo a ejecutar:** `wsgi.py`
- **Puerto:** `5000` (no 5001)

## ❌ LO QUE NO DEBO HACER:
- Lanzar servidor en primer plano (cierra terminal)
- Olvidar matar procesos anteriores
- No responder cuando no tengo respuesta
- Desviarme de lo que pides
- Cambiar código sin permiso

## ✅ LO QUE SIEMPRE DEBO HACER:
- Responder SIEMPRE (incluso si no tengo respuesta)
- Monitorear en segundo plano
- Seguir tus instrucciones exactas
- Mantener terminal abierta para conversar
- Recordar estos comandos

## 🎯 LO QUE SIEMPRE PIDES:
1. **MONITOREAR** - Ver logs en tiempo real
2. **NO CAMBIAR NADA** - Mantener código original
3. **LANZAR BIEN** - Con el entorno virtual correcto
4. **TIEMPO REAL** - Servidor en primer plano

---
**ÚLTIMA ACTUALIZACIÓN:** $(date)
**RECORDAR:** Leer este archivo antes de cada sesión 