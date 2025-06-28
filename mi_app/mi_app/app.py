import os
import time
from dotenv import load_dotenv
import ssl
import shutil
import requests
import json
import urllib.parse
import logging

# Cargar variables de entorno
load_dotenv()

# Debug prints
print("SUPABASE_URL:", os.getenv('SUPABASE_URL'))
print("SUPABASE_KEY:", os.getenv('SUPABASE_KEY'))

# Configurar zona horaria
os.environ['TZ'] = 'America/Santiago'  # Forzar zona horaria
time.tzset()

import pytz
chile_tz = pytz.timezone('America/Santiago')  # Forzar zona horaria

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Blueprint, current_app, send_file
from supabase import create_client, Client
from datetime import datetime, timedelta

from flask_caching import Cache
import hashlib
from functools import wraps
# from usdt_ves import obtener_valor_usdt_por_banco  # Eliminado porque el módulo ya no existe
import asyncio
import aiohttp
import csv
import io

from blueprints.utilidades import utilidades_bp
from blueprints.transferencias import transferencias_bp
from blueprints.pedidos import pedidos_bp
from blueprints.dashboard import dashboard_bp, init_cache
from blueprints.admin import admin_bp
from blueprints.pagos import pagos_bp
from blueprints.clientes import clientes_bp

from extensions import cache

# -----------------------------------------------------------------------------
# Configuración de logging
# -----------------------------------------------------------------------------
# Configuración de logging para archivo y consola
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("app.log", encoding="utf-8")
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

# -----------------------------------------------------------------------------
# Configuración de ajuste de hora
# -----------------------------------------------------------------------------
HOUR_ADJUSTMENT = int(os.getenv('HOUR_ADJUSTMENT', '0'))  # Ajuste de hora en horas (puede ser positivo o negativo)

def adjust_datetime(dt):
    """
    Ajusta un datetime según la configuración de HOUR_ADJUSTMENT.
    Args:
        dt: datetime a ajustar
    Returns:
        datetime ajustado
    """
    if not isinstance(dt, datetime):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    
    if dt.tzinfo is None:
        dt = chile_tz.localize(dt)
    
    return dt + timedelta(hours=HOUR_ADJUSTMENT)

# -----------------------------------------------------------------------------
# Inicialización de la aplicación y cache
# -----------------------------------------------------------------------------
app = Flask(__name__)
print("Rutas de templates:", app.jinja_loader.searchpath)
app.secret_key = os.getenv('SECRET_KEY', 'mi_clave_secreta')
cache.init_app(app, config={
    "CACHE_TYPE": os.getenv('CACHE_TYPE', 'SimpleCache'),
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
})

# Inicializar cache para el dashboard
init_cache(cache)

# -----------------------------------------------------------------------------
# Registro de blueprints
# -----------------------------------------------------------------------------
app.register_blueprint(utilidades_bp)
app.register_blueprint(transferencias_bp, url_prefix="/transferencias")
app.register_blueprint(pedidos_bp, url_prefix="/pedidos")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(pagos_bp, url_prefix="/pagos")
app.register_blueprint(clientes_bp, url_prefix="/clientes")

# -----------------------------------------------------------------------------
# Decorador login_required
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
# Configuración de Supabase
# -----------------------------------------------------------------------------
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------------------------------------------------
# Procesador de contexto para verificar si el usuario es admin
# -----------------------------------------------------------------------------
@app.context_processor
def inject_user_permissions():
    is_admin = False
    if "email" in session:
        try:
            response = supabase.table("allowed_users").select("email").eq("email", session["email"]).execute()
            is_admin = bool(response.data)  # True si el email está en allowed_users
        except Exception as e:
            logging.error("Error al verificar permisos de usuario: %s", e)
    return dict(is_admin=is_admin)

# -----------------------------------------------------------------------------
# Función para generar hash único para cada transferencia
# -----------------------------------------------------------------------------
def generar_hash_transferencia(transferencia):
    data = f"{transferencia.get('id')}-{transferencia.get('fecha')}-{transferencia.get('monto')}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# -----------------------------------------------------------------------------
# Filtros personalizados para Jinja2
# -----------------------------------------------------------------------------
def format_monto(value):
    try:
        return "{:,.0f}".format(value).replace(",", ".")
    except Exception:
        return value

def format_date(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%d-%m")
    except Exception:
        return value

def format_time(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return value

app.jinja_env.filters['format_time'] = format_time

@app.template_filter("format_fecha_detec")
def format_fecha_detec(value):
    if not value:
        return ""
    try:
        if isinstance(value, str):
            # Si es una cadena ISO, convertirla a datetime
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            # Convertir a zona horaria local y ajustar
            dt = adjust_datetime(dt)
            # Formatear la fecha
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, datetime):
            # Si ya es datetime, asegurarse de que tenga zona horaria y ajustar
            dt = adjust_datetime(value)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)
    except Exception as e:
        logging.error(f"Error formateando fecha_detec: {e}, valor: {value}")
        return str(value)

def format_clp(value):
    try:
        number = int(abs(float(value)))
        return "{:,.0f}".format(number).replace(",", ".")
    except Exception:
        return value

def format_int(value):
    try:
        return "{:,.0f}".format(int(float(value))).replace(",", ".")
    except Exception:
        return value

def format_datetime(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    except Exception:
        return value

def format_decimal(value, decimals=3):
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return value

def format_decimal5(value):
    try:
        return f"{float(value):.5f}"
    except Exception:
        return value

def format_clp_decimal(value):
    try:
        # Formatea con separador de miles (punto) y decimales (coma)
        formatted = "{:,.2f}".format(float(value)).replace(",", ".")
        # Solo el primer punto se cambia por coma (el decimal)
        if "." in formatted:
            parts = formatted.rsplit(".", 1)
            return parts[0] + "," + parts[1]
        return formatted
    except Exception:
        return value

app.jinja_env.filters['format_monto'] = format_monto
app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['format_clp'] = format_clp
app.jinja_env.filters['format_int'] = format_int
app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['format_decimal'] = format_decimal
app.jinja_env.filters['format_decimal5'] = format_decimal5
app.jinja_env.filters['format_clp_decimal'] = format_clp_decimal

# -----------------------------------------------------------------------------
# Funciones helper para filtrar y ordenar consultas
# -----------------------------------------------------------------------------
def filter_transferencias(query):
    cliente = request.args.get("cliente")
    if cliente:
        if cliente == "Desconocido":
            query = query.is_("cliente", "null")
        else:
            query = query.ilike("cliente", f"%{cliente}%")
    rut = request.args.get("rut")
    if rut:
        query = query.ilike("rut", f"%{rut}%")
    monto = request.args.get("monto", "").replace(".", "").strip()
    if monto:
        try:
            query = query.eq("monto", int(monto))
        except ValueError:
            logging.warning("Valor de monto no válido: %s", monto)
    verificada = request.args.get("verificada")
    if verificada == "true":
        query = query.eq("verificada", True)
    elif verificada == "false":
        query = query.eq("verificada", False)
    empresas = request.args.getlist("empresa")
    if empresas:
        query = query.in_("empresa", empresas)
    return query

def filter_pedidos(query):
    cliente = request.args.get("cliente")
    if cliente:
        query = query.ilike("cliente", f"%{cliente}%")
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    query = query.eq("fecha", fecha)
    brs = request.args.get("brs", "").strip()
    if brs:
        try:
            query = query.eq("brs", float(brs))
        except ValueError:
            logging.warning("Valor de BRS no válido: %s", brs)
    clp = request.args.get("clp", "").replace(".", "").strip()
    if clp:
        try:
            query = query.eq("clp", int(clp))
        except ValueError:
            logging.warning("Valor de CLP no válido: %s", clp)
    return query

def apply_ordering(query, sort_params):
    for sort_field, order in sort_params:
        if sort_field:
            query = query.order(sort_field, desc=(order == "desc"))
    return query

# -----------------------------------------------------------------------------
# Rutas generales
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("transferencias.index"))
    else:
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e:
            logging.error("Error al iniciar sesión: %s", e)
            flash("Error al iniciar sesión: " + str(e))
            return redirect(url_for("login"))
        if auth_response.session:
            session["user_id"] = auth_response.user.id
            session["email"] = auth_response.user.email
            flash("¡Sesión iniciada con éxito!")
            return redirect(url_for("transferencias.index"))
        else:
            flash("Credenciales incorrectas.")
            return redirect(url_for("login"))
    return render_template("login.html", title="Iniciar Sesión", active_page="")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

@app.route("/update/<transfer_id>", methods=["POST"])
@login_required
def update_transfer(transfer_id):
    nuevo_valor = request.form.get("nuevo_valor")
    try:
        nuevo_valor = bool(int(nuevo_valor))
    except Exception as e:
        logging.error("Error al convertir nuevo_valor: %s", e)
        nuevo_valor = False
    try:
        result = supabase.table("transferencias").update({"verificada": nuevo_valor}).eq("id", transfer_id).execute()
        if result.data and len(result.data) > 0:
            flash(f"Registro actualizado (ID = {transfer_id}).")
        else:
            flash("No se encontró el registro para actualizar. Verifica las políticas de seguridad.")
    except Exception as e:
        logging.error("Error al actualizar el registro: %s", e)
        flash("Error al actualizar el registro: " + str(e))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=True)
    return redirect(request.referrer or url_for("transferencias.index"))

def get_current_datetime():
    """Helper function to get current datetime in local timezone"""
    return adjust_datetime(datetime.now(chile_tz))

def format_datetime_with_timezone(dt):
    """Helper function to format datetime with timezone"""
    if dt is None:
        return ""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = chile_tz.localize(dt)
    dt = adjust_datetime(dt)
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Agregar filtro para formatear moneda
@app.template_filter('format_currency')
def format_currency(value):
    if value is None:
        return ""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)