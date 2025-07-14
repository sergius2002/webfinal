# Bot de Suma de Comprobantes Bancarios (Telegram)

Este bot es completamente independiente de tu proyecto principal. Se encuentra en la carpeta `bot_telegram` y tiene su propio entorno virtual y dependencias.

## Requisitos previos
- Python 3.9 o superior
- Acceso a terminal
- Homebrew instalado (en Mac) para instalar Tesseract

## Instalación de Tesseract OCR

Tesseract es necesario para que el bot pueda leer los montos de las imágenes.

En MacOS, ejecuta:

```bash
brew install tesseract
```

En Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr
```

## Pasos para arrancar el bot

1. **Ir a la carpeta del bot:**
   ```bash
   cd ~/bot_telegram
   ```

2. **Activar el entorno virtual:**
   ```bash
   source venv/bin/activate
   ```

3. **Instalar dependencias (solo la primera vez):**
   ```bash
   pip install python-telegram-bot==13.15 pytesseract pillow
   ```

4. **Ejecutar el bot:**
   ```bash
   python sumador_bot.py
   ```

## ¿Cómo funciona?
- Envía imágenes de comprobantes bancarios al grupo de Telegram.
- El bot extrae el monto en Bs de cada imagen y lo suma.
- El bot responde en el grupo con el monto extraído y la suma acumulada.

## Notas importantes
- Este bot NO tiene relación ni dependencia con tu proyecto principal.
- Todo lo que instales aquí (dependencias, código) es solo para el bot.
- Si necesitas reiniciar la suma, reinicia el script.

---

¿Dudas? Puedes pedirme ayuda para cualquier paso o para adaptar el bot a tus necesidades. 