# blueprints/utilidades.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import logging
from supabase import create_client, Client
from datetime import datetime, timedelta
import hashlib
from functools import wraps
import csv
import threading
import os
import ssl
import shutil
import requests
import json
import urllib.parse
import asyncio
import aiohttp
import pytz
import time
import pathlib

# -----------------------------------------------------------------------------
# Definición del Blueprint
# -----------------------------------------------------------------------------
utilidades_bp = Blueprint('utilidades', __name__, url_prefix='/utilidades')

# -----------------------------------------------------------------------------
# Configuración de Supabase
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0."
    "tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"
)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

GRAFICO_CSV = os.path.join(os.path.dirname(__file__), '../../data_tasas.csv')

# -----------------------------------------------------------------------------
# Decorador de login (puedes reutilizar el que ya tienes)
# -----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

# -----------------------------------------------------------------------------
# Rutas del Módulo de Utilidades
# -----------------------------------------------------------------------------

@utilidades_bp.route("/")
@login_required
def index():
    # Vista principal del módulo de utilidades
    return render_template("utilidades/utilidades.html", active_page="utilidades")

@utilidades_bp.route("/compras", methods=["GET", "POST"])
@login_required
def compras():
    """
    Permite seleccionar una fecha para filtrar la tabla "compras" en Supabase.
    Se filtra por:
      - fiat = 'VES'
      - tradetype = 'SELL'
    Se suma la columna "totalprice" de los registros correspondientes al día seleccionado
    y se formatea el resultado con separador de miles y sin decimales.
    """
    if request.method == "POST":
        # Recibimos la fecha seleccionada y redirigimos usando query string
        fecha = request.form.get("fecha")
        return redirect(url_for("utilidades.compras", fecha=fecha))

    # Para el método GET, se obtiene la fecha del query string (si existe)
    fecha = request.args.get("fecha")

    # Preparamos la consulta filtrando por fiat y tradetype
    query = supabase.table("compras") \
        .select("totalprice") \
        .eq("fiat", "VES") \
        .eq("tradetype", "SELL")

    # Si se ha seleccionado una fecha, filtramos también por el campo "createtime"
    if fecha:
        # Asumimos que "createtime" almacena la fecha y hora en formato ISO (YYYY-MM-DDThh:mm:ss)
        inicio = fecha + "T00:00:00"
        fin = fecha + "T23:59:59"
        query = query.gte("createtime", inicio).lte("createtime", fin)

    response = query.execute()
    total = sum(item.get("totalprice", 0) for item in response.data) if response.data is not None else 0
    # Formatear el total: separador de miles y sin decimales (ej. 1234567 se mostrará como "1.234.567")
    formatted_total = format(total, ",.0f").replace(",", ".")

    return render_template("utilidades/compras_resultado.html", total=formatted_total, fecha=fecha,
                           active_page="utilidades")

# Endpoint para la página del gráfico
@utilidades_bp.route('/grafico')
@login_required
def grafico():
    try:
        # Actualizar datos al cargar la página (consultar Binance y guardar en CSV)
        actualizar_datos()
        return render_template('utilidades/grafico.html', active_page='utilidades')
    except Exception as e:
        logging.error(f"Error al cargar el gráfico: {e}")
        flash("Error al cargar el gráfico", "error")
        return render_template('utilidades/grafico.html', active_page='utilidades')

# Endpoint para obtener los datos del gráfico en tiempo real
@utilidades_bp.route('/grafico_datos')
@login_required
def grafico_datos():
    try:
        # Recargar el CSV desde disco en cada petición
        datos = []
        if os.path.exists(GRAFICO_CSV):
            with open(GRAFICO_CSV, mode="r", newline="") as file:
                reader = csv.reader(file)
                next(reader)  # Saltar encabezados
                for row in reader:
                    if len(row) >= 5:
                        tiempo, banesco, bank, mercantil, provincial = row
                        datos.append({
                            'tiempo': tiempo,
                            'precio_banesco': float(banesco) if banesco else 0,
                            'precio_venezuela': float(bank) if bank else 0,
                            'precio_mercantil': float(mercantil) if mercantil else 0,
                            'precio_provincial': float(provincial) if provincial else 0
                        })
        # Filtrar duplicados por timestamp, quedándose con el último registro de cada timestamp
        datos_filtrados = {}
        for d in datos:
            datos_filtrados[d['tiempo']] = d  # Sobrescribe si ya existe, así queda el último
        datos_final = list(datos_filtrados.values())
        datos_final.sort(key=lambda x: x['tiempo'])  # Ordenar por tiempo ascendente
        return jsonify({
            'datos': datos_final,
            'ultima_actualizacion': adjust_datetime(datetime.now(chile_tz)).strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logging.error(f"Error al obtener datos del gráfico: {e}")
        return jsonify({'error': str(e), 'datos': []})

# Lógica de reinicio a las 8am (puede ejecutarse en un hilo background)
def reiniciar_csv_diario():
    while True:
        ahora = datetime.now()
        if ahora.hour == 8 and ahora.minute == 0:
            with open(GRAFICO_CSV, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Tiempo', 'Banesco', 'Venezuela', 'Mercantil', 'Provincial'])
            time.sleep(60)  # Esperar un minuto para evitar múltiples reinicios
        time.sleep(30)

# Lanzar el hilo de reinicio si no está corriendo
def lanzar_reinicio_csv():
    if not hasattr(lanzar_reinicio_csv, 'hilo'):
        hilo = threading.Thread(target=reiniciar_csv_diario, daemon=True)
        hilo.start()
        lanzar_reinicio_csv.hilo = hilo
lanzar_reinicio_csv()

# Configuración de zona horaria
chile_tz = pytz.timezone('America/Santiago')

# Configuración de ajuste de hora
HOUR_ADJUSTMENT = int(os.getenv('HOUR_ADJUSTMENT', '0'))

# Configuración del gráfico
SELL_API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

def adjust_datetime(dt):
    """Ajusta un datetime según la configuración de HOUR_ADJUSTMENT."""
    if not isinstance(dt, datetime):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    
    if dt.tzinfo is None:
        dt = chile_tz.localize(dt)
    
    return dt + timedelta(hours=HOUR_ADJUSTMENT)

# Variables globales para el gráfico
GRAFICO_DIR = os.path.dirname(GRAFICO_CSV)
LAST_RESET_FILE = os.path.join(GRAFICO_DIR, 'last_reset.txt')
tiempos = []
precios_banesco = []
precios_bank_transfer = []
precios_mercantil = []
precios_provincial = []
last_reset_date = None

def guardar_last_reset(date):
    try:
        with open(LAST_RESET_FILE, 'w') as f:
            f.write(str(date))
    except Exception as e:
        logging.error(f"Error al guardar last_reset_date: {e}")

def cargar_last_reset():
    try:
        if os.path.exists(LAST_RESET_FILE):
            with open(LAST_RESET_FILE, 'r') as f:
                return f.read().strip()
    except Exception as e:
        logging.error(f"Error al leer last_reset_date: {e}")
    return None

# Al iniciar, cargar last_reset_date desde archivo
last_reset_date = cargar_last_reset()

def cargar_datos_historicos():
    """Carga los datos históricos del CSV."""
    global tiempos, precios_banesco, precios_bank_transfer, precios_mercantil, precios_provincial
    try:
        if os.path.exists(GRAFICO_CSV):
            with open(GRAFICO_CSV, mode="r", newline="") as file:
                reader = csv.reader(file)
                next(reader)  # Saltar encabezados
                for row in reader:
                    if len(row) >= 5:
                        tiempo, banesco, bank, mercantil, provincial = row
                        tiempos.append(tiempo)
                        precios_banesco.append(float(banesco) if banesco else 0)
                        precios_bank_transfer.append(float(bank) if bank else 0)
                        precios_mercantil.append(float(mercantil) if mercantil else 0)
                        precios_provincial.append(float(provincial) if provincial else 0)
            logging.info(f"Datos históricos cargados: {len(tiempos)} registros")
    except Exception as e:
        logging.error(f"Error al cargar datos históricos: {e}")

def reiniciar_datos_diarios():
    """Reinicia los datos cada día a las 8:00 am."""
    global last_reset_date, tiempos, precios_banesco, precios_bank_transfer, precios_mercantil, precios_provincial
    now = adjust_datetime(datetime.now(chile_tz))
    # Si last_reset_date es string, convertir a date
    if last_reset_date and isinstance(last_reset_date, str):
        try:
            last_reset_date = datetime.fromisoformat(last_reset_date).date()
        except Exception:
            try:
                last_reset_date = datetime.strptime(last_reset_date, '%Y-%m-%d').date()
            except Exception:
                last_reset_date = None
    # Solo reiniciar si es realmente un nuevo día a las 8am
    if last_reset_date is None or (now.hour == 8 and now.date() > last_reset_date):
        logging.info(f"Reiniciando datos del gráfico y CSV a las {now.strftime('%Y-%m-%d %H:%M:%S')}...")
        # Crear backup antes de reiniciar
        if os.path.exists(GRAFICO_CSV):
            backup_file = f"{GRAFICO_CSV}.{now.strftime('%Y%m%d')}.bak"
            try:
                shutil.copy2(GRAFICO_CSV, backup_file)
                logging.info(f"Backup creado: {backup_file}")
            except Exception as e:
                logging.error(f"Error al crear backup: {e}")
        # Reiniciar las listas
        tiempos.clear()
        precios_banesco.clear()
        precios_bank_transfer.clear()
        precios_mercantil.clear()
        precios_provincial.clear()
        # Crear nuevo archivo CSV
        with open(GRAFICO_CSV, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Tiempo", "Banesco", "Venezuela", "Mercantil", "Provincial"])
        last_reset_date = now.date()
        guardar_last_reset(last_reset_date)
        logging.info("Reinicio completado")

def guardar_datos_csv(tiempo, banesco, bank, mercantil, provincial):
    """Guarda los datos en el CSV."""
    try:
        with open(GRAFICO_CSV, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([tiempo, banesco, bank, mercantil, provincial])
    except Exception as e:
        logging.error(f"Error al guardar datos en CSV: {e}")

async def obtener_tasa_usdt_ves(bancos, ultimo_valor=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
    }
    payload = {
        'proMerchantAds': False,
        'page': 1,
        'transAmount': 200000,  # 200.000 VES
        'rows': 20,
        'payTypes': bancos,
        'publisherType': 'merchant',
        'asset': 'USDT',
        'fiat': 'VES',
        'tradeType': 'SELL'
    }
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.post(SELL_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data and data["data"]:
                        precios = [float(adv["adv"]["price"]) for adv in data["data"][:3] if "adv" in adv and "price" in adv["adv"]]
                        if len(precios) == 0:
                            return ultimo_valor if ultimo_valor is not None else None
                        if len(precios) == 1:
                            return precios[0]
                        if len(precios) == 2:
                            return sum(precios) / 2
                        # Si hay 3 precios, aplicar la lógica de outlier
                        primero = precios[0]
                        promedio_otros = sum(precios[1:]) / 2
                        if abs(primero - promedio_otros) / promedio_otros > 0.01:
                            # Es outlier, usar el promedio de los otros dos
                            logging.warning(f"Primer precio {primero} es outlier respecto a {precios[1:]}, usando promedio {promedio_otros}")
                            return promedio_otros
                        else:
                            return primero
                    else:
                        logging.warning("No se encontraron datos en la respuesta.")
                        return ultimo_valor if ultimo_valor is not None else None
                else:
                    logging.error(f"Error en la solicitud: {response.status}")
                    return ultimo_valor if ultimo_valor is not None else None
        except Exception as e:
            logging.error(f"Error al obtener tasa USDT/VES: {e}")
            return ultimo_valor if ultimo_valor is not None else None

def actualizar_datos():
    """Actualiza los datos consultando Binance y guardando en CSV."""
    global tiempos, precios_banesco, precios_bank_transfer, precios_mercantil, precios_provincial
    reiniciar_datos_diarios()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    precio_banesco_actualizado = loop.run_until_complete(obtener_tasa_usdt_ves(["Banesco"], precios_banesco[-1] if precios_banesco else None))
    precio_bank_transfer_actualizado = loop.run_until_complete(obtener_tasa_usdt_ves(["BANK"], precios_bank_transfer[-1] if precios_bank_transfer else None))
    precio_mercantil_actualizado = loop.run_until_complete(obtener_tasa_usdt_ves(["Mercantil"], precios_mercantil[-1] if precios_mercantil else None))
    precio_provincial_actualizado = loop.run_until_complete(obtener_tasa_usdt_ves(["Provincial"], precios_provincial[-1] if precios_provincial else None))
    loop.close()

    tiempo_actual = adjust_datetime(datetime.now(chile_tz))
    tiempo_str = tiempo_actual.strftime('%H:%M\n%d - %b')
    tiempos.append(tiempo_str)

    precios_banesco.append(precio_banesco_actualizado if precio_banesco_actualizado is not None else (precios_banesco[-1] if precios_banesco else 0))
    precios_bank_transfer.append(precio_bank_transfer_actualizado if precio_bank_transfer_actualizado is not None else (precios_bank_transfer[-1] if precios_bank_transfer else 0))
    precios_mercantil.append(precio_mercantil_actualizado if precio_mercantil_actualizado is not None else (precios_mercantil[-1] if precios_mercantil else 0))
    precios_provincial.append(precio_provincial_actualizado if precio_provincial_actualizado is not None else (precios_provincial[-1] if precios_provincial else 0))

    guardar_datos_csv(tiempo_str, precios_banesco[-1], precios_bank_transfer[-1], precios_mercantil[-1], precios_provincial[-1])

def inicializar_csv():
    """Inicializa el archivo CSV si no existe."""
    try:
        if not os.path.exists(GRAFICO_CSV):
            with open(GRAFICO_CSV, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo", "Banesco", "Venezuela", "Mercantil", "Provincial"])
            logging.info(f"Archivo CSV creado: {GRAFICO_CSV}")
    except Exception as e:
        logging.error(f"Error al inicializar CSV: {e}")

# Inicializar y cargar datos al importar el módulo
inicializar_csv()
cargar_datos_historicos()

@utilidades_bp.route("/compras_resultado")
@login_required
def compras_resultado():
    return render_template("utilidades/compras_resultado.html", active_page="utilidades")

@utilidades_bp.route("/actualizar_datos")
@login_required
def actualizar_datos_endpoint():
    """Endpoint para forzar la actualización de datos."""
    try:
        actualizar_datos()
        return jsonify({
            'success': True,
            'mensaje': 'Datos actualizados correctamente',
            'ultima_actualizacion': adjust_datetime(datetime.now(chile_tz)).strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logging.error(f"Error al actualizar datos: {e}")
        return jsonify({'error': str(e)}), 500
