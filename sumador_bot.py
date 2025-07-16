#!/usr/bin/env python3
"""
Bot de Telegram para procesar comprobantes bancarios
Configurado para zona horaria de Chile
"""

import os
import datetime
import pytesseract
from PIL import Image
import re
from telegram.ext import Updater, MessageHandler, Filters
from io import BytesIO

# Configurar zona horaria de Chile (sin librerías adicionales)
os.environ['TZ'] = 'America/Santiago'

print("INICIO DEL SCRIPT")
print(f"📅 Zona horaria configurada: Chile")
print(f"⏰ Hora actual: {datetime.datetime.now()}")

# Configuración del bot
TELEGRAM_TOKEN = '7522395434:AAHg1uPMnT94tRqoY_gWB8IjKt1GTS4cw3o'
CHAT_ID = -4644705137

print("Token y chat_id cargados")

# Variable global para la suma
total_acumulado = 0
print("Variable total_acumulado inicializada")

def extraer_monto(texto):
    """Extrae montos en formato boliviano del texto OCR"""
    print("Entrando a extraer_monto")
    patron = r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*Bs'
    montos = re.findall(patron, texto)
    print(f"Montos encontrados: {montos}")
    total = 0
    for monto in montos:
        monto_num = float(monto.replace('.', '').replace(',', '.'))
        total += monto_num
    print(f"Total extraído: {total}")
    return total

def handle_any_message(update, context):
    """Maneja cualquier mensaje recibido"""
    print('Mensaje recibido')
    print('Contenido del mensaje:', update.message)
    
    imagen_bytes = None
    if update.message.photo:
        print('Tipo: Foto')
        archivo = update.message.photo[-1].get_file()
        imagen_bytes = archivo.download_as_bytearray()
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image'):
        print('Tipo: Documento imagen')
        archivo = update.message.document.get_file()
        imagen_bytes = archivo.download_as_bytearray()
    else:
        print('No es imagen, es tipo:', update.message)
        return
    
    try:
        imagen = Image.open(BytesIO(imagen_bytes))
        print('Imagen abierta correctamente')
        texto = pytesseract.image_to_string(imagen, lang='spa')
        print('Texto extraído OCR:')
        print(texto)
        monto = extraer_monto(texto)
        print(f'Monto extraído: {monto}')
        
        global total_acumulado
        total_acumulado += monto
        
        # Obtener información del usuario
        user = update.effective_user
        user_info = f"{user.first_name or 'Usuario'} (@{user.username or 'Sin username'})"
        
        # Obtener hora actual en Chile
        hora_chile = datetime.datetime.now()
        
        mensaje = (
            f"✅ Comprobante procesado exitosamente\n\n"
            f"💰 Monto: {monto:,.2f} Bs\n"
            f"👤 Usuario: {user_info}\n"
            f"⏰ Hora: {hora_chile.strftime('%H:%M:%S')} (Chile)\n\n"
            f"📊 Total acumulado: {total_acumulado:,.2f} Bs"
        )
        
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=mensaje
        )
        print('Mensaje enviado al chat')
        
    except Exception as e:
        print('Error procesando imagen:', e)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"❌ Error procesando la imagen: {str(e)}"
        )

def main():
    """Función principal del bot"""
    print('Bot iniciado y escuchando mensajes...')
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.all, handle_any_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main() 