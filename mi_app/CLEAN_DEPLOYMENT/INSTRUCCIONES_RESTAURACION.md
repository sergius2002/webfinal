# 🔧 INSTRUCCIONES DE RESTAURACIÓN POST-HACKEO

## 1. ANTES DE SUBIR A PYTHONANYWHERE:

### Cambiar contraseñas:
- [ ] PythonAnywhere
- [ ] GitHub (si usas el mismo password)
- [ ] Email asociado

### Revocar tokens en @BotFather:
- [ ] San_Cristobal_bot (6962665881...)
- [ ] dolarbcvVES_BOT (7503093829...)
- [ ] Suma_captures_Bot (7522395434...)

### Crear nuevos tokens:
- [ ] Crear nuevo bot para tasas
- [ ] Crear nuevo bot para dólar BCV  
- [ ] Crear nuevo bot para comprobantes

## 2. EN PYTHONANYWHERE:

### Detener procesos comprometidos:
```bash
# En consola de PythonAnywhere
pkill -f telegram
pkill -f python
```

### Hacer backup del código comprometido:
```bash
mv /home/sacristobalspa/webfinal /home/sacristobalspa/webfinal_COMPROMISED_$(date +%Y%m%d)
```

### Subir código limpio:
```bash
git clone https://github.com/sergius2002/webfinal.git
cd webfinal
git pull origin main
```

### Actualizar variables de entorno:
```bash
# Editar .env con nuevos tokens
nano .env
```

### Verificar archivos:
```bash
# Comparar hashes con los archivos limpios
sha256sum telegram_bot_always.py
sha256sum mi_app/dolar_bcv.py
```

## 3. VERIFICACIÓN DE SEGURIDAD:

- [ ] Revisar logs de acceso en PythonAnywhere
- [ ] Verificar que no hay procesos sospechosos
- [ ] Confirmar que bots responden solo a comandos legítimos
- [ ] Monitorear actividad por 24-48 horas

## 4. PREVENCIÓN FUTURA:

- [ ] Activar 2FA en PythonAnywhere
- [ ] Usar tokens de solo lectura cuando sea posible
- [ ] Monitorear logs regularmente
- [ ] Rotar credenciales periódicamente
