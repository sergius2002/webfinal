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
    # Buscar monto en formato boliviano (más flexible)
    monto_patterns = [
        r'([\d\.]+,\d{2})\s*[Bb][sS]',  # 5,600.00 Bs
        r'([\d\.]+,\d{2})\s*[Bb][oO][Ll][Ii][Vv][Ii][Aa][Nn][Oo][Ss]',  # 5,600.00 Bolivianos
        r'([\d\.]+,\d{2})',  # Solo el número
        r'([\d,]+\.\d{2})',  # Formato alternativo
    ]
    
    monto = None
    for pattern in monto_patterns:
        monto_match = re.search(pattern, texto, re.MULTILINE | re.IGNORECASE)
        if monto_match:
            try:
                monto_str = monto_match.group(1).replace('.', '').replace(',', '.')
                monto = float(monto_str)
                break
            except ValueError:
                continue
    
    # Buscar fecha (más flexible)
    fecha_patterns = [
        r'Fecha[:\s]+([\d/]+)',  # Fecha: 14/07/2025
        r'([\d]{1,2}/[\d]{1,2}/[\d]{4})',  # 14/07/2025
        r'([\d]{1,2}-[\d]{1,2}-[\d]{4})',  # 14-07-2025
        r'([\d]{1,2}\.[\d]{1,2}\.[\d]{4})',  # 14.07.2025
    ]
    
    fecha = ""
    for pattern in fecha_patterns:
        fecha_match = re.search(pattern, texto, re.MULTILINE | re.IGNORECASE)
        if fecha_match:
            fecha = fecha_match.group(1)
            break
    
    # Buscar número de operación (más flexible)
    operacion_patterns = [
        r'Operaci[oó]n[:\s]+([\d]+)',  # Operación: 123456789
        r'([\d]{10,})',  # Números largos (10+ dígitos)
        r'Ref[:\s]+([\d]+)',  # Ref: 123456789
        r'ID[:\s]+([\d]+)',  # ID: 123456789
    ]
    
    operacion = ""
    for pattern in operacion_patterns:
        operacion_match = re.search(pattern, texto, re.MULTILINE | re.IGNORECASE)
        if operacion_match:
            operacion = operacion_match.group(1)
            break
    
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
    
    async def subir_a_supabase(self, fecha, brs, operacion, context=None, update=None, es_duplicado=False, user_info=None):
        """
        Sube un comprobante a Supabase
        
        Args:
            fecha (str): Fecha del comprobante
            brs (float): Monto en bolivianos
            operacion (str): Número de operación
            context: Contexto de Telegram
            update: Update de Telegram
            es_duplicado (bool): Si es un duplicado permitido
            user_info (dict): Información del usuario que envió el comprobante
            
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
        
        # Agregar información del usuario si está disponible
        if user_info:
            data.update({
                "usuario_id": user_info['id'],
                "usuario_username": user_info['username'],
                "usuario_nombre": user_info['first_name'],
                "usuario_apellido": user_info['last_name'],
                "timestamp_envio": user_info['timestamp']
            })
        
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
            # Obtener información del usuario
            user = update.effective_user
            user_info = {
                'id': user.id,
                'username': user.username or 'Sin username',
                'first_name': user.first_name or 'Sin nombre',
                'last_name': user.last_name or '',
                'timestamp': update.message.date.isoformat()
            }
            
            foto = update.message.photo[-1]
            file = await context.bot.get_file(foto.file_id)
            img_bytes = await file.download_as_bytearray()
            imagen = Image.open(BytesIO(img_bytes))
            
            # Mejorar calidad de imagen para OCR
            # Convertir a escala de grises
            imagen_gris = imagen.convert('L')
            
            # Aumentar contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(imagen_gris)
            imagen_contraste = enhancer.enhance(2.0)
            
            # OCR con configuración optimizada
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÁÉÍÓÚáéíóúÑñ.,:()/- '
            texto = pytesseract.image_to_string(imagen_contraste, lang='spa', config=config)
            logger.info("OCR recibido de %s (@%s): %s", user_info['first_name'], user_info['username'], texto)
            
            monto, fecha, operacion = extraer_datos(texto)
            
            if monto is not None:
                mensaje = f"Monto detectado: {formato_bs(monto)}\nEnviado por: {user_info['first_name']} (@{user_info['username']})"
                
                if fecha and operacion:
                    ok, hash_val = await manager.subir_a_supabase(fecha, monto, operacion, context, update, False, user_info)
                    if ok:
                        manager.suma_total += monto
                        manager.montos.append(monto)
                        
                        # Calcular total personalizado del usuario
                        total_usuario = await calcular_total_usuario(user_info['id'])
                        
                        mensaje += f"\n✅ Comprobante registrado exitosamente"
                        mensaje += f"\n📊 Tu total personal: {formato_bs(total_usuario)}"
                        mensaje += f"\n🌐 Total general: {formato_bs(manager.suma_total)}"
                        
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
                    else:
                        mensaje += f"\n(Advertencia: comprobante pendiente de confirmación por duplicado.)"
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
                else:
                    mensaje += "\n(Advertencia: No se pudo extraer fecha u operación para Supabase)"
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
            else:
                mensaje = f"No se pudo detectar el monto en la imagen.\nEnviado por: {user_info['first_name']} (@{user_info['username']})"
                await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
            
        except Exception as e:
            logger.error("Error procesando imagen: %s", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error procesando imagen: {e}")

async def calcular_total_usuario(user_id):
    """Calcula el total de comprobantes de un usuario específico"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs").eq("fecha", hoy).eq("usuario_id", user_id).execute()
        total = sum(float(item['brs']) for item in res.data)
        return total
    except Exception as e:
        logger.error("Error calculando total del usuario %s: %s", user_id, e)
        return 0.0

async def mi_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el total personal del usuario que ejecuta el comando"""
    user = update.effective_user
    user_info = {
        'id': user.id,
        'username': user.username or 'Sin username',
        'first_name': user.first_name or 'Sin nombre',
        'last_name': user.last_name or ''
    }
    
    try:
        total_personal = await calcular_total_usuario(user_info['id'])
        total_general = await calcular_total_general()
        
        mensaje = f"📊 Resumen personal de {user_info['first_name']} (@{user_info['username']})\n\n"
        mensaje += f"💰 Tu total: {formato_bs(total_personal)}\n"
        mensaje += f"🌐 Total general: {formato_bs(total_general)}\n"
        
        if total_general > 0:
            porcentaje = (total_personal / total_general) * 100
            mensaje += f"📈 Porcentaje: {porcentaje:.1f}%"
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
        
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al calcular tu total: {e}")

async def calcular_total_general():
    """Calcula el total general del día"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs").eq("fecha", hoy).execute()
        total = sum(float(item['brs']) for item in res.data)
        return total
    except Exception as e:
        logger.error("Error calculando total general: %s", e)
        return 0.0

async def mi_detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el detalle personal del usuario que ejecuta el comando"""
    user = update.effective_user
    user_info = {
        'id': user.id,
        'username': user.username or 'Sin username',
        'first_name': user.first_name or 'Sin nombre',
        'last_name': user.last_name or ''
    }
    
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs,timestamp_envio").eq("fecha", hoy).eq("usuario_id", user_info['id']).execute()
        montos_personales = res.data
        
        if montos_personales:
            lista = []
            for i, item in enumerate(montos_personales):
                monto = float(item['brs'])
                timestamp = item.get('timestamp_envio', '')
                hora = timestamp.split('T')[1][:5] if timestamp else ''
                
                lista.append(f"{i+1}. {formato_bs(monto)} {hora}")
            
            lista_texto = '\n'.join(lista)
            total_personal = sum(float(item['brs']) for item in montos_personales)
            total_general = await calcular_total_general()
            
            mensaje = f"📋 Tus comprobantes del día ({hoy}):\n\n{lista_texto}\n\n"
            mensaje += f"💰 Tu total: {formato_bs(total_personal)}\n"
            mensaje += f"🌐 Total general: {formato_bs(total_general)}"
            
            if total_general > 0:
                porcentaje = (total_personal / total_general) * 100
                mensaje += f"\n📈 Porcentaje: {porcentaje:.1f}%"
        else:
            mensaje = f"No has enviado comprobantes hoy, {user_info['first_name']}."
            
        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
        
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al consultar tu detalle: {e}")

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
            
            # Calcular total personal del usuario
            user_id = data.get('usuario_id')
            if user_id:
                total_usuario = await calcular_total_usuario(user_id)
                mensaje = "Comprobante insertado de todos modos."
                mensaje += f"\n📊 Tu total personal: {formato_bs(total_usuario)}"
                mensaje += f"\n🌐 Total general: {formato_bs(manager.suma_total)}"
            else:
                mensaje = "Comprobante insertado de todos modos."
                mensaje += f"\n🌐 Total general: {formato_bs(manager.suma_total)}"
            
            await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
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
    """Muestra el detalle de todos los montos del día con información del usuario"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs,usuario_nombre,usuario_username,timestamp_envio").eq("fecha", hoy).execute()
        montos_todos = res.data
        
        if montos_todos:
            lista = []
            for i, item in enumerate(montos_todos):
                monto = float(item['brs'])
                usuario = item.get('usuario_nombre', 'Desconocido')
                username = item.get('usuario_username', '')
                timestamp = item.get('timestamp_envio', '')
                
                if username:
                    usuario_info = f"{usuario} (@{username})"
                else:
                    usuario_info = usuario
                
                lista.append(f"{i+1}. {formato_bs(monto)} - {usuario_info}")
            
            lista_texto = '\n'.join(lista)
            total = sum(float(item['brs']) for item in montos_todos)
            mensaje = f"Listado de montos detectados (incluyendo duplicados):\n{lista_texto}\n\nTotal: {formato_bs(total)}"
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

async def estadisticas_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas de comprobantes por usuario"""
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    try:
        res = supabase.table("comprobantes").select("brs,usuario_nombre,usuario_username").eq("fecha", hoy).execute()
        montos_todos = res.data
        
        if montos_todos:
            # Agrupar por usuario
            usuarios = {}
            for item in montos_todos:
                monto = float(item['brs'])
                usuario = item.get('usuario_nombre', 'Desconocido')
                username = item.get('usuario_username', '')
                
                if usuario not in usuarios:
                    usuarios[usuario] = {'total': 0, 'count': 0, 'username': username}
                
                usuarios[usuario]['total'] += monto
                usuarios[usuario]['count'] += 1
            
            # Crear mensaje de estadísticas
            stats = []
            for usuario, data in usuarios.items():
                if data['username']:
                    usuario_info = f"{usuario} (@{data['username']})"
                else:
                    usuario_info = usuario
                
                stats.append(f"• {usuario_info}: {data['count']} comprobantes - {formato_bs(data['total'])}")
            
            stats_texto = '\n'.join(stats)
            total_general = sum(data['total'] for data in usuarios.values())
            mensaje = f"📊 Estadísticas por usuario ({hoy}):\n\n{stats_texto}\n\nTotal general: {formato_bs(total_general)}"
        else:
            mensaje = "Aún no hay comprobantes registrados hoy."
            
        await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error al consultar estadísticas: {e}")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda con los comandos disponibles"""
    mensaje = """
🤖 Bot de Comprobantes Bancarios

Comandos disponibles:
• Envía una foto de comprobante para procesarla automáticamente
• /detalle - Mostrar listado de montos del día con usuarios
• /total - Mostrar total con duplicados
• /total_sin_duplicados - Mostrar total sin duplicados
• /ingreso_manual <monto> - Ingresar monto manualmente
• /permitir - Confirmar inserción de duplicado
• /denegar - Rechazar inserción de duplicado
• /estadisticas - Ver estadísticas por usuario

📊 Comandos personales:
• /mi_total - Ver tu total personal vs general
• /mi_detalle - Ver tus comprobantes del día
• /ayuda - Mostrar esta ayuda

Ejemplo: /ingreso_manual 1.234,56

📝 Nota: El bot registra automáticamente quién envía cada comprobante y muestra totales personalizados.
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
    app.add_handler(CommandHandler('estadisticas', estadisticas_usuarios))
    app.add_handler(CommandHandler('mi_total', mi_total))
    app.add_handler(CommandHandler('mi_detalle', mi_detalle))
    app.add_handler(CommandHandler('ayuda', ayuda))
    app.add_handler(CommandHandler('start', ayuda))
    
    logger.info("Bot escuchando comprobantes en Telegram...")
    
    # Ejecutar bot
    import asyncio
    asyncio.run(app.run_polling())

if __name__ == '__main__':
    main() 