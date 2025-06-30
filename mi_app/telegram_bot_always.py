#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para responder a los comandos /tasa y /compras en Telegram usando telebot,
obteniendo datos de Supabase, calculando tasas y enviando el resultado como
una tabla dibujada con Pillow (con estilo similar a una tabla de Excel y mayor nitidez)
para mayor legibilidad.
Adaptado para ejecutarse como Always Task en PythonAnywhere
"""

import os
import sys
import time
import pytz
import asyncio
import logging
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = '/home/sacristobalspa/webfinal'
sys.path.insert(0, project_dir)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sacristobalspa/webfinal/mi_app/telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Reducir mensajes de módulos externos
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("postgrest").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
def cargar_variables_entorno():
    """Carga las variables de entorno desde el archivo .env"""
    try:
        env_file = Path(project_dir) / '.env'
        if env_file.exists():
            logging.info(f"📁 Cargando variables de entorno desde: {env_file}")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            logging.info("✅ Variables de entorno cargadas correctamente")
        else:
            logging.warning(f"⚠️ Archivo .env no encontrado en: {env_file}")
    except Exception as e:
        logging.error(f"❌ Error al cargar variables de entorno: {e}")

# Cargar variables de entorno antes de importar módulos
cargar_variables_entorno()

# Zona horaria
local_tz = pytz.timezone('America/Santiago')

def obtener_credenciales():
    """Obtiene las credenciales desde variables de entorno o usa valores por defecto"""
    # Credenciales de Telegram
    chat_id_telegram = os.getenv('CHAT_ID_TELEGRAM', '-4090514300')
    token_telegram = os.getenv('TOKEN_TELEGRAM', '6962665881:AAG7e9l9rRtcnWyyia8i9jR5aLiU4ldlTzI')
    
    # Credenciales de Supabase
    supabase_url = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
    supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')
    
    return {
        'chat_id_telegram': int(chat_id_telegram),
        'token_telegram': token_telegram,
        'supabase_url': supabase_url,
        'supabase_key': supabase_key
    }

def format_tasa_6_digits(tasa):
    """
    Formatea una tasa para que tenga exactamente 6 cifras en total.
    Ejemplos:
    - 3.456789 -> 3.45679 (6 cifras: 3,4,5,6,7,9)
    - 12.345 -> 12.3450 (6 cifras: 1,2,3,4,5,0)
    - 1.23 -> 1.23000 (6 cifras: 1,2,3,0,0,0)
    """
    if tasa == 0:
        return "0.00000"
    
    # Convertir a string con muchos decimales
    tasa_str = f"{tasa:.10f}"
    
    # Contar dígitos antes del punto decimal
    if '.' in tasa_str:
        parte_entera = tasa_str.split('.')[0]
        parte_decimal = tasa_str.split('.')[1]
    else:
        parte_entera = tasa_str
        parte_decimal = ""
    
    digitos_enteros = len(parte_entera)
    
    # Si tiene más de 6 dígitos enteros, truncar
    if digitos_enteros >= 6:
        return f"{tasa:.0f}"
    
    # Calcular cuántos decimales necesitamos para tener 6 cifras total
    decimales_necesarios = 6 - digitos_enteros
    
    # Formatear con los decimales necesarios
    return f"{tasa:.{decimales_necesarios}f}"

def adjust_datetime(dt):
    """
    Ajusta un datetime según la configuración de HOUR_ADJUSTMENT.
    Args:
        dt: datetime a ajustar
    Returns:
        datetime ajustado
    """
    HOUR_ADJUSTMENT = int(os.getenv('HOUR_ADJUSTMENT', '0'))  # Ajuste de hora en horas
    
    if not isinstance(dt, datetime):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    
    if dt.tzinfo is None:
        dt = local_tz.localize(dt)
    
    return dt + timedelta(hours=HOUR_ADJUSTMENT)

async def iniciar_bot():
    """Función principal para iniciar el bot de Telegram"""
    try:
        # Importar aquí para evitar problemas de path
        from supabase import create_client, Client
        from mi_app.mi_app.usdt_ves import obtener_valor_usdt_por_banco
        from telebot.async_telebot import AsyncTeleBot
        from PIL import Image, ImageDraw, ImageFont, ImageEnhance
        
        # Obtener credenciales
        creds = obtener_credenciales()
        
        # Configurar Supabase y Bot
        supabase: Client = create_client(creds['supabase_url'], creds['supabase_key'])
        bot = AsyncTeleBot(creds['token_telegram'])
        
        # Configuraciones de tabla/imagen con estilo Excel
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        FONT_SIZE = 50
        PADDING = 20
        COL_SPACING = 0
        ROW_SPACING = 0

        def create_table_image(table_data, font_path=FONT_PATH, font_size=FONT_SIZE,
                               padding=PADDING, col_spacing=COL_SPACING, row_spacing=ROW_SPACING,
                               header_bg_color="#4F81BD", header_text_color="white",
                               even_row_bg_color="white", odd_row_bg_color="#DCE6F1",
                               cell_border_color="#A6A6A6", border_width=1, sharpness_factor=2.0):
            """
            Crea una imagen con formato de tabla a partir de table_data (lista de listas),
            aplicando un estilo similar a una tabla de Excel.
            """
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.error(f"Error cargando la fuente '{font_path}': {e}")
                font = ImageFont.load_default()

            num_rows = len(table_data)
            if num_rows == 0:
                return None
            num_cols = len(table_data[0])

            # Determinar el ancho de cada columna y la altura de cada fila
            col_widths = [0] * num_cols
            row_heights = [0] * num_rows
            temp_image = Image.new("RGB", (1, 1))
            draw_temp = ImageDraw.Draw(temp_image)

            for r in range(num_rows):
                for c in range(num_cols):
                    cell_text = str(table_data[r][c])
                    bbox = draw_temp.textbbox((0, 0), cell_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    if text_width > col_widths[c]:
                        col_widths[c] = text_width
                    if text_height > row_heights[r]:
                        row_heights[r] = text_height

            # Relleno interno para cada celda
            cell_padding = 10
            col_widths = [w + 2 * cell_padding for w in col_widths]
            row_heights = [h + 2 * cell_padding for h in row_heights]

            # Calcular dimensiones totales de la imagen
            table_width = sum(col_widths) + (col_spacing * (num_cols - 1)) + (2 * padding)
            table_height = sum(row_heights) + (row_spacing * (num_rows - 1)) + (2 * padding)

            # Crear imagen final
            image = Image.new("RGB", (table_width, table_height), color="white")
            draw = ImageDraw.Draw(image)

            y_offset = padding
            for r in range(num_rows):
                x_offset = padding
                # Definir color de fondo y color de texto según la fila
                if r == 0:
                    row_bg_color = header_bg_color
                    text_color = header_text_color
                else:
                    row_bg_color = even_row_bg_color if r % 2 == 0 else odd_row_bg_color
                    text_color = "black"

                for c in range(num_cols):
                    cell_text = str(table_data[r][c])
                    cell_width = col_widths[c]
                    cell_height = row_heights[r]

                    # Dibujar fondo de la celda
                    draw.rectangle(
                        [x_offset, y_offset, x_offset + cell_width, y_offset + cell_height],
                        fill=row_bg_color
                    )

                    # Dibujar borde de la celda (simulando el grid de Excel)
                    draw.rectangle(
                        [x_offset, y_offset, x_offset + cell_width, y_offset + cell_height],
                        outline=cell_border_color, width=border_width
                    )

                    # Calcular posición para centrar el texto
                    bbox = draw.textbbox((0, 0), cell_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    text_x = x_offset + (cell_width - text_width) / 2
                    text_y = y_offset + (cell_height - text_height) / 2

                    draw.text((text_x, text_y), cell_text, font=font, fill=text_color)
                    x_offset += cell_width + col_spacing
                y_offset += row_heights[r] + row_spacing

            # Aplicar mejora de nitidez para evitar imagen borrosa
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(sharpness_factor)

            return image

        async def send_table_as_image(chat_id, table_data):
            """
            Crea una imagen a partir de table_data (lista de listas) y la envía al chat.
            """
            image = create_table_image(table_data)
            if image is None:
                await bot.send_message(chat_id, "No hay datos para mostrar en tabla.")
                return

            bio = BytesIO()
            bio.name = 'tabla.png'
            image.save(bio, 'PNG')
            bio.seek(0)
            await bot.send_photo(chat_id, bio)

        # ---------------------------------------------------------------------
        # Comando /tasa
        # ---------------------------------------------------------------------
        @bot.message_handler(commands=['tasa'])
        async def manejar_tasa(message):
            try:
                if message.chat.id != creds['chat_id_telegram']:
                    await bot.send_message(message.chat.id, "No tienes permiso para usar este comando.")
                    return

                response = supabase.table("vista_compras_fifo") \
                    .select("costo_no_vendido") \
                    .order("id", desc=True) \
                    .limit(1) \
                    .execute()

                if not response.data or len(response.data) == 0:
                    await bot.send_message(message.chat.id, "No se encontró información en la tabla vista_compras_fifo.")
                    return

                costo_no_vendido = response.data[0]["costo_no_vendido"]
                if costo_no_vendido == 0:
                    await bot.send_message(
                        message.chat.id,
                        "El valor de costo_no_vendido es 0, no se puede realizar la división."
                    )
                    return

                banesco_val = await obtener_valor_usdt_por_banco("Banesco")
                bank_val = await obtener_valor_usdt_por_banco("BANK")

                tasa_banesco = banesco_val / costo_no_vendido
                tasa_venezuela = bank_val / costo_no_vendido

                # Construimos la tabla
                table_data = [
                    ["Banco", "Tasa"],  # Encabezados
                    ["Banesco", format_tasa_6_digits(tasa_banesco)],
                    ["Venezuela", format_tasa_6_digits(tasa_venezuela)]
                ]

                await send_table_as_image(message.chat.id, table_data)
                logger.info(f"✅ Comando /tasa ejecutado exitosamente para chat {message.chat.id}")

            except Exception as e:
                logger.error(f"Error en el comando /tasa: {e}")
                await bot.send_message(message.chat.id, "Ha ocurrido un error al procesar la solicitud.")

        # ---------------------------------------------------------------------
        # Comando /compras
        # ---------------------------------------------------------------------
        @bot.message_handler(commands=['compras'])
        async def manejar_compras(message):
            try:
                if message.chat.id != creds['chat_id_telegram']:
                    await bot.send_message(message.chat.id, "No tienes permiso para usar este comando.")
                    return

                parts = message.text.split()
                if len(parts) > 1:
                    fecha = parts[1]
                else:
                    fecha = adjust_datetime(datetime.now(local_tz)).strftime("%Y-%m-%d")

                inicio = f"{fecha}T00:00:00"
                fin = f"{fecha}T23:59:59"

                response = supabase.table("vista_compras_fifo") \
                    .select("totalprice, paymethodname, createtime, unitprice, costo_no_vendido") \
                    .eq("fiat", "VES") \
                    .gte("createtime", inicio) \
                    .lte("createtime", fin) \
                    .execute()

                compras_data = response.data if response.data else []
                compras_data.sort(key=lambda row: row.get("createtime", ""), reverse=True)

                if not compras_data:
                    await bot.send_message(message.chat.id, f"No se encontraron transacciones para la fecha {fecha}.")
                    return

                # Construimos la tabla
                table_data = []
                table_data.append(["Hora", "Banco", "Brs", "Tasa"])  # Encabezados

                for row in compras_data:
                    costo = row.get('costo_no_vendido')
                    if costo and costo != 0:
                        tasa = row['unitprice'] / costo
                    else:
                        tasa = 0
                    createtime = row.get('createtime', '')
                    hora = createtime.split("T")[1][:5] if "T" in createtime else createtime
                    banco = row.get('paymethodname', '')
                    brs = row.get('totalprice', 0)

                    table_data.append([
                        hora,
                        banco,
                        f"{brs:,.0f}",
                        format_tasa_6_digits(tasa)
                    ])

                await send_table_as_image(message.chat.id, table_data)
                logger.info(f"✅ Comando /compras ejecutado exitosamente para chat {message.chat.id}")

            except Exception as e:
                logger.error(f"Error en el comando /compras: {e}")
                await bot.send_message(message.chat.id, "Ha ocurrido un error al obtener los datos de compras.")

        # ---------------------------------------------------------------------
        # Comando /help
        # ---------------------------------------------------------------------
        @bot.message_handler(commands=['help', 'start'])
        async def manejar_help(message):
            try:
                if message.chat.id != creds['chat_id_telegram']:
                    await bot.send_message(message.chat.id, "No tienes permiso para usar este comando.")
                    return

                help_text = """
🤖 **Bot de Tasas USDT/VES**

Comandos disponibles:

📊 `/tasa` - Muestra las tasas actuales de Banesco y Venezuela

📈 `/compras [fecha]` - Muestra las compras del día (o fecha específica)
   Ejemplo: `/compras 2024-06-30`

❓ `/help` - Muestra esta ayuda

---
Desarrollado para PythonAnywhere
                """
                
                await bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
                logger.info(f"✅ Comando /help ejecutado exitosamente para chat {message.chat.id}")

            except Exception as e:
                logger.error(f"Error en el comando /help: {e}")
                await bot.send_message(message.chat.id, "Ha ocurrido un error al mostrar la ayuda.")

        # Iniciar el bot
        logger.info("🚀 Bot de Telegram iniciado. Esperando comandos...")
        await bot.polling()
        
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar el bot: {e}")
        return False

def main():
    """Función principal del script"""
    logger.info("🚀 Iniciando bot de Telegram para PythonAnywhere")
    
    try:
        # Ejecutar el bot
        asyncio.run(iniciar_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrumpido por el usuario")
    except Exception as e:
        logger.error(f"💥 Error crítico en el bot: {e}")

if __name__ == "__main__":
    main()