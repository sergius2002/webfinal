#!/usr/bin/env python3
"""
Script de Telegram para procesar comprobantes bancarios
======================================================

Este script permite:
- Recibir imágenes de comprobantes bancarios por Telegram
- Extraer montos, fechas y números de operación usando OCR
- Almacenar los datos en Supabase
- Detectar duplicados automáticamente
- Calcular totales diarios

Uso:
    python sumar_comprobantes_telegram.py

Comandos disponibles:
    /detalle - Mostrar listado de montos del día
    /total - Mostrar total con duplicados
    /total_sin_duplicados - Mostrar total sin duplicados
    /ingreso_manual <monto> - Ingresar monto manualmente
    /permitir - Confirmar inserción de duplicado
    /denegar - Rechazar inserción de duplicado

Autor: Sistema de Gestión Empresarial
Fecha: 2024
"""

import pytesseract
from PIL import Image
import requests
import re
import os
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from supabase import create_client, Client
import hashlib
import datetime
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_comprobantes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración del bot
TELEGRAM_BOT_TOKEN = '7522395434:AAHg1uPMnT94tRqoY_gWB8IjKt1GTS4cw3o'
TELEGRAM_CHAT_ID = -4644705137

# Configuración de Supabase
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"

# Inicializar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def formato_bs(monto):
    """Formatea un monto en formato boliviano"""
    return f"{monto:,.2f} Bs".replace(",", ".").replace(".", ",", 1)

def extraer_datos(texto):
    """
    Extrae monto, fecha y operación del texto OCR
    
    Args:
        texto (str): Texto extraído de la imagen
        
    Returns:
        tuple: (monto, fecha, operacion)
    """
    # Buscar monto en formato boliviano
    monto_match = re.search(r'([\d\.]+,\d{2})\s*[Bb][sS]', texto, re.MULTILINE)
    monto = float(monto_match.group(1).replace('.', '').replace(',', '.')) if monto_match else None
    
    # Buscar fecha
    fecha_match = re.search(r'Fecha[:\s]+([\d/]+)', texto)
    fecha = fecha_match.group(1) if fecha_match else ""
    
    # Buscar número de operación
    operacion_match = re.search(r'Operaci[oó]n[:\s]+([\d]+)', texto)
    operacion = operacion_match.group(1) if operacion_match else ""
    
    return monto, fecha, operacion

class ComprobantesManager:
    """Clase para gestionar el estado de los comprobantes"""
    
    def __init__(self):
        self.suma_total = 0.0
        self.montos = []
        self.pendiente_actual = None
        self.cargar_historial_hoy()
    
    def cargar_historial_hoy(self):
        """Carga el historial de comprobantes del día actual"""
        hoy = datetime.date.today().strftime('%d/%m/%Y')
        try:
            res = supabase.table("comprobantes").select("brs,es_duplicado").eq("fecha", hoy).execute()
            self.montos = [float(item['brs']) for item in res.data if not item.get('es_duplicado', False)]
            self.suma_total = sum(self.montos)
            logger.info(f"Historial del día {hoy} cargado: {len(self.montos)} comprobantes originales, suma total: {self.suma_total}")
        except Exception as e:
            logger.error(f"Error cargando historial del día: {e}")
            self.montos = []
            self.suma_total = 0.0
    
    async def subir_a_supabase(self, fecha, brs, operacion, context=None, update=None, es_duplicado=False):
        """
        Sube un comprobante a Supabase
        
        Args:
            fecha (str): Fecha del comprobante
            brs (float): Monto en bolivianos
            operacion (str): Número de operación
            context: Contexto de Telegram
            update: Update de Telegram
            es_duplicado (bool): Si es un duplicado permitido
            
        Returns:
            tuple: (success, hash_val)
        """
        hash_str = f"{fecha}-{brs}-{operacion}"
        hash_val = hashlib.sha256(hash_str.encode()).hexdigest()
        
        data = {
            "fecha": fecha,
            "brs": brs,
            "operacion": operacion,
            "hash": hash_val,
            "es_duplicado": es_duplicado
        }
        
        try:
            # Verificar si ya existe el hash
            res_check = supabase.table("comprobantes").select("hash").eq("hash", hash_val).execute()
            if res_check.data and len(res_check.data) > 0 and not es_duplicado:
                # Duplicado detectado
                if context and update:
                    self.pendiente_actual = data
                    mensaje = (
                        "⚠️ Este comprobante al parecer ya fue ingresado.\n"
                        "¿Quieres insertar de todos modos?\n"
                        "Responde con /permitir para insertar o /denegar para descartar."
                    )
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
                logger.warning("Duplicado detectado (consulta previa): %s", hash_val)
                return False, hash_val
            
            # Insertar normalmente
            res = supabase.table("comprobantes").insert(data).execute()
            logger.info("Subido a Supabase: %s", res)
            return True, hash_val
            
        except Exception as e:
            if context and update:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error subiendo a Supabase: {e}")
            logger.error("Error subiendo a Supabase: %s", e)
            return False, hash_val

# Instancia global del manager
manager = ComprobantesManager()

async def procesar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa una imagen de comprobante enviada por Telegram"""
    if update.message.photo:
        try:
            foto = update.message.photo[-1]
            file = await context.bot.get_file(foto.file_id)
            img_bytes = await file.download_as_bytearray()
            imagen = Image.open(BytesIO(img_bytes))
            
            # OCR
            texto = pytesseract.image_to_string(imagen, lang='spa')
            logger.info("OCR recibido: %s", texto)
            
            monto, fecha, operacion = extraer_datos(texto)
            
            if monto is not None:
                mensaje = f"Monto detectado: {formato_bs(monto)}"
                
                if fecha and operacion:
                    ok, hash_val = await manager.subir_a_supabase(fecha, monto, operacion, context, update)
                    if ok:
                        manager.suma_total += monto
                        manager.montos.append(monto)
                        mensaje += f"\nSuma total: {formato_bs(manager.suma_total)}"
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total actualizado: {formato_bs(manager.suma_total)}")
                    else:
                        mensaje += f"\n(Advertencia: comprobante pendiente de confirmación por duplicado.)"
                else:
                    mensaje += "\n(Advertencia: No se pudo extraer fecha u operación para Supabase)"
            else:
                mensaje = "No se pudo detectar el monto en la imagen."
                
            await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
            
        except Exception as e:
            logger.error("Error procesando imagen: %s", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error procesando imagen: {e}")

async def permitir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite la inserción de un comprobante duplicado"""
    if manager.pendiente_actual:
        data = manager.pendiente_actual
        # Modificar hash para permitir duplicado
        nuevo_hash = data['hash'] + '_dup'
        data['hash'] = nuevo_hash
        data['es_duplicado'] = True
        
        try:
            supabase.table("comprobantes").insert(data).execute()
            # Sumar también los duplicados permitidos
            manager.suma_total += float(data['brs'])
            manager.montos.append(float(data['brs']))
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Comprobante insertado de todos modos.")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total actualizado: {formato_bs(manager.suma_total)}")
        except Exception as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al insertar duplicado: {e}")
        
        manager.pendiente_actual = None
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No hay comprobante pendiente para insertar.")

async def denegar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rechaza la inserción de un comprobante duplicado"""
    if manager.pendiente_actual:
        manager.pendiente_actual = None
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Comprobante descartado.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total actualizado: {formato_bs(manager.suma_total)}")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No hay comprobante pendiente para descartar.")

async def detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el detalle de todos los montos del día"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs").eq("fecha", hoy).execute()
        montos_todos = [float(item['brs']) for item in res.data]
        
        if montos_todos:
            lista = '\n'.join([f"{i+1}. {formato_bs(m)}" for i, m in enumerate(montos_todos)])
            mensaje = f"Listado de montos detectados (incluyendo duplicados):\n{lista}\n\nTotal: {formato_bs(sum(montos_todos))}"
        else:
            mensaje = "Aún no hay montos registrados."
            
        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al consultar detalle: {e}")

async def ingreso_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite ingresar un monto manualmente"""
    try:
        if context.args:
            monto = float(context.args[0].replace(',', '.'))
            manager.suma_total += monto
            manager.montos.append(monto)
            mensaje = f"Ingreso manual registrado: {formato_bs(monto)}\nSuma total: {formato_bs(manager.suma_total)}"
        else:
            mensaje = "Por favor, indica el monto. Ejemplo: /ingreso_manual 1.234,56"
    except Exception:
        mensaje = "Error: el monto debe ser un número. Ejemplo: /ingreso_manual 1.234,56"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)

async def total_sin_duplicados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el total sin duplicados"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs,es_duplicado").eq("fecha", hoy).execute()
        suma = sum(float(item['brs']) for item in res.data if not item.get('es_duplicado', False))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total sin duplicados: {formato_bs(suma)}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al consultar total: {e}")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el total con duplicados"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs").eq("fecha", hoy).execute()
        suma = sum(float(item['brs']) for item in res.data)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total con duplicados: {formato_bs(suma)}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al consultar total: {e}")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda con los comandos disponibles"""
    mensaje = """
🤖 Bot de Comprobantes Bancarios

Comandos disponibles:
• Envía una foto de comprobante para procesarla automáticamente
• /detalle - Mostrar listado de montos del día
• /total - Mostrar total con duplicados
• /total_sin_duplicados - Mostrar total sin duplicados
• /ingreso_manual <monto> - Ingresar monto manualmente
• /permitir - Confirmar inserción de duplicado
• /denegar - Rechazar inserción de duplicado
• /ayuda - Mostrar esta ayuda

Ejemplo: /ingreso_manual 1.234,56
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)

def main():
    """Función principal del bot"""
    logger.info("Iniciando bot de comprobantes...")
    
    # Crear aplicación
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(MessageHandler(filters.PHOTO, procesar_imagen))
    app.add_handler(CommandHandler('detalle', detalle))
    app.add_handler(CommandHandler('ingreso_manual', ingreso_manual))
    app.add_handler(CommandHandler('permitir', permitir))
    app.add_handler(CommandHandler('denegar', denegar))
    app.add_handler(CommandHandler('total_sin_duplicados', total_sin_duplicados))
    app.add_handler(CommandHandler('total', total))
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.add_handler(CommandHandler('start', ayuda))
    
    logger.info("Bot escuchando comprobantes en Telegram...")
    
    # Ejecutar bot
    import asyncio
    asyncio.run(app.run_polling())

if __name__ == '__main__':
    main() 