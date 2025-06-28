import os
import logging
import hashlib
import asyncio
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import pytz
from mi_app.usdt_ves import obtener_valor_usdt_por_banco

# Configuración de zona horaria
chile_tz = pytz.timezone('America/Santiago')

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de ajuste de hora
HOUR_ADJUSTMENT = int(os.getenv('HOUR_ADJUSTMENT', '0'))

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

# Decorador login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para módulos restringidos
def user_allowed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        email = session.get("email")
        if not email:
            flash("Debes iniciar sesión.")
            return redirect(url_for("login"))
        try:
            response = supabase.table("allowed_users").select("email").eq("email", email).execute()
            if not response.data:
                flash("No tienes permisos para acceder a este módulo.")
                return redirect(url_for("index"))
        except Exception as e:
            logging.error("Error al verificar usuario permitido: %s", e)
            flash("Error interno al verificar permisos.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

# Función para generar hash único para cada transferencia
def generar_hash_transferencia(transferencia):
    data = f"{transferencia.get('id')}-{transferencia.get('fecha')}-{transferencia.get('monto')}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Crear blueprint
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@login_required
@user_allowed
def index():
    return redirect(url_for('admin.tasa_compras'))

@admin_bp.route("/tasa_compras", methods=["GET"])
@login_required
@user_allowed
def tasa_compras():
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    try:
        response = supabase.table("vista_compras_fifo") \
            .select("totalprice, paymethodname, createtime, unitprice, costo_no_vendido") \
            .eq("fiat", "VES") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .execute()
        compras_data = response.data if response.data else []
        query = supabase.table("vista_compras_fifo").select("costo_no_vendido") \
            .eq("fiat", "VES") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .order("createtime", desc=True) \
            .limit(1) \
            .execute()
        if query.data:
            costo_no_vendido = query.data[0]["costo_no_vendido"]
        else:
            costo_no_vendido = None
        for row in compras_data:
            if costo_no_vendido:
                row['tasa'] = round(row['unitprice'] / costo_no_vendido, 6)
    except Exception as e:
        logging.error("Error al obtener los datos: %s", e)
        compras_data = []
    return render_template("admin/tasa_compras.html", active_page="admin",
                           compras_data=compras_data, fecha=fecha)

@admin_bp.route("/ingresar_usdt", methods=["GET", "POST"])
@login_required
@user_allowed
def ingresar_usdt():
    if request.method == "POST":
        try:
            totalprice_str = request.form.get("totalprice", "")
            if not totalprice_str:
                flash("El campo Total Price es requerido.")
                return redirect(url_for("admin.ingresar_usdt"))
            
            totalprice = float(totalprice_str.replace(".", "").replace(",", ".").strip())
            tasa_str = request.form.get("tasa")
            tasa = float(tasa_str)
            tradetype = request.form.get("tradetype")
            fiat = request.form.get("fiat")
            asset = "USDT"
            paymethodname = "OTC"
            orderstatus = "COMPLETED"
            amount = totalprice / tasa
            costo_real = amount
            commission = 0
            createtime = request.form.get("createtime")
            # Asegurarse de que la fecha está en la zona horaria correcta y ajustar
            dt_createtime = datetime.strptime(createtime, "%Y-%m-%dT%H:%M")
            dt_createtime = adjust_datetime(dt_createtime)
            createtime = dt_createtime.isoformat()
            hash_input = f"{totalprice}{tasa}{tradetype}{fiat}{asset}{createtime}"
            ordernumber = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:20]
            response = supabase.table("compras").insert({
                "totalprice": totalprice,
                "unitprice": tasa,
                "tradetype": tradetype,
                "fiat": fiat,
                "asset": asset,
                "amount": amount,
                "costo_real": costo_real,
                "commission": commission,
                "paymethodname": paymethodname,
                "createtime": createtime,
                "orderstatus": orderstatus,
                "ordernumber": ordernumber
            }).execute()
            flash("Compra de USDT ingresada con éxito.")
            return redirect(url_for("admin.ingresar_usdt"))
        except Exception as e:
            logging.error("Error al ingresar compra de USDT: %s", e)
            flash("Error al ingresar la compra de USDT: " + str(e))
            return redirect(url_for("admin.ingresar_usdt"))
    
    # Asegurarse de que la fecha actual está en la zona horaria correcta y ajustada
    current_datetime = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%dT%H:%M")
    tradetype_options = ["BUY", "SELL"]
    fiat_options = ["CLP", "VES", "USD"]
    
    # Renderizar el template sin valor por defecto para totalprice
    return render_template("admin/ingresar_usdt.html", 
                         active_page="admin", 
                         current_datetime=current_datetime,
                         tradetype_options=tradetype_options, 
                         fiat_options=fiat_options)

@admin_bp.route("/tasa_actual", methods=["GET"])
@login_required
@user_allowed
def tasa_actual():
    try:
        query = supabase.table("vista_compras_fifo").select("costo_no_vendido, createtime, stock_usdt") \
            .order("createtime", desc=True) \
            .limit(1)
        response = query.execute()
        if response.data and len(response.data) > 0:
            record = response.data[0]
            costo_no_vendido = record.get("costo_no_vendido")
            stock_usdt = record.get("stock_usdt")
        else:
            costo_no_vendido = None
            stock_usdt = None
            flash("No se encontró ningún registro.", "warning")
    except Exception as e:
        logging.error("Error al obtener la tasa actual desde Supabase: %s", e)
        flash("Error al obtener la tasa actual: " + str(e), "danger")
        costo_no_vendido = None
        stock_usdt = None

    resultado_banesco = None
    resultado_bank = None

    if costo_no_vendido is not None:
        try:
            async def obtener_valores():
                logging.info("Intentando obtener valor de Banesco...")
                banesco_val = await obtener_valor_usdt_por_banco("Banesco")
                logging.info(f"Valor de Banesco obtenido: {banesco_val}")
                
                logging.info("Intentando obtener valor de BANK...")
                bank_val = await obtener_valor_usdt_por_banco("BANK")
                logging.info(f"Valor de BANK obtenido: {bank_val}")
                
                return banesco_val, bank_val
            banesco_val, bank_val = asyncio.run(obtener_valores())
            if banesco_val and bank_val:
                resultado_banesco = round(float(banesco_val) / float(costo_no_vendido), 6)
                resultado_bank = round(float(bank_val) / float(costo_no_vendido), 6)
                logging.info(f"Tasas calculadas - Banesco: {resultado_banesco}, Venezuela: {resultado_bank}")
            else:
                logging.warning("No se pudieron obtener los valores de los bancos")
                flash("No se pudieron obtener las tasas de conversión de Banesco y BANK.", "warning")
        except Exception as e:
            logging.error("Error al obtener valores USDT/VES: %s", e)
            flash("Error al obtener valores USDT/VES: " + str(e), "danger")

    return render_template(
        "admin/tasa_actual.html",
        active_page="admin",
        costo_no_vendido=costo_no_vendido,
        stock_usdt=stock_usdt,
        resultado_banesco=resultado_banesco,
        resultado_bank=resultado_bank
    )

@admin_bp.route("/resumen_compras_usdt", methods=["GET"])
@login_required
@user_allowed
def resumen_compras_usdt():
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    
    try:
        # Obtener compras
        response_compras = supabase.table("compras") \
            .select("*") \
            .eq("fiat", "CLP") \
            .eq("tradetype", "BUY") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .execute()
        
        compras_data = response_compras.data if response_compras.data else []
        
        # Obtener ventas
        response_ventas = supabase.table("compras") \
            .select("*") \
            .eq("fiat", "CLP") \
            .eq("tradetype", "SELL") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .execute()
        
        ventas_data = response_ventas.data if response_ventas.data else []
        
        # Combinar y ordenar todos los datos
        all_data = []
        for compra in compras_data:
            all_data.append({
                "id": compra.get("id"),
                "createtime": compra.get("createtime", ""),
                "totalprice": compra.get("totalprice", 0),
                "amount": compra.get("amount", 0),
                "unitprice": compra.get("unitprice", 0),
                "tradetype": "BUY",
                "paymethodname": compra.get("paymethodname", "")
            })
        
        for venta in ventas_data:
            all_data.append({
                "id": venta.get("id"),
                "createtime": venta.get("createtime", ""),
                "totalprice": -venta.get("totalprice", 0),  # Negativo para ventas
                "amount": -venta.get("amount", 0),  # Negativo para ventas
                "unitprice": venta.get("unitprice", 0),
                "tradetype": "SELL",
                "paymethodname": venta.get("paymethodname", "")
            })
        
        all_data.sort(key=lambda x: x.get("createtime", ""), reverse=True)
        
        # Calcular totales
        total_clp = sum(item.get("totalprice", 0) for item in all_data)
        total_usdt = sum(item.get("amount", 0) for item in all_data)
        tasa_promedio = total_clp / total_usdt if total_usdt != 0 else 0
        
        return render_template(
            "admin/resumen_compras_usdt.html",
            active_page="admin",
            compras_data=all_data,
            total_clp=total_clp,
            total_usdt=total_usdt,
            tasa_promedio=tasa_promedio,
            fecha=fecha
        )
    except Exception as e:
        logging.error("Error al obtener resumen de compras USDT: %s", e)
        flash("Error al obtener el resumen de compras USDT.")
        return redirect(url_for("admin.index"))

@admin_bp.route("/resumen_ventas_usdt", methods=["GET"])
@login_required
@user_allowed
def resumen_ventas_usdt():
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    
    try:
        response = supabase.table("compras") \
            .select("*") \
            .eq("fiat", "CLP") \
            .eq("tradetype", "SELL") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .execute()
        
        ventas_data = response.data if response.data else []
        ventas_data.sort(key=lambda x: x.get("createtime", ""), reverse=True)
        
        # Calcular totales
        total_clp = sum(venta.get("totalprice", 0) for venta in ventas_data)
        total_usdt = sum(venta.get("amount", 0) for venta in ventas_data)
        tasa_promedio = total_clp / total_usdt if total_usdt > 0 else 0
        
        return render_template(
            "admin/resumen_ventas_usdt.html",
            active_page="admin",
            ventas_data=ventas_data,
            total_clp=total_clp,
            total_usdt=total_usdt,
            tasa_promedio=tasa_promedio,
            fecha=fecha
        )
    except Exception as e:
        logging.error("Error al obtener resumen de ventas USDT: %s", e)
        flash("Error al obtener el resumen de ventas USDT.")
        return redirect(url_for("admin.index"))

@admin_bp.route("/eliminar_transaccion_usdt/<int:transaccion_id>", methods=["POST"])
@login_required
@user_allowed
def eliminar_transaccion_usdt(transaccion_id):
    try:
        # Obtener la transacción para verificar paymethodname
        response = supabase.table("compras").select("id, paymethodname").eq("id", transaccion_id).single().execute()
        if not response.data:
            flash("Transacción no encontrada.", "danger")
            return redirect(url_for("admin.resumen_compras_usdt"))
        if response.data.get("paymethodname") != "OTC":
            flash("Solo se pueden eliminar transacciones con método OTC.", "danger")
            return redirect(url_for("admin.resumen_compras_usdt"))
        # Eliminar físicamente
        supabase.table("compras").delete().eq("id", transaccion_id).execute()
        flash("Transacción eliminada correctamente.", "success")
    except Exception as e:
        logging.error(f"Error al eliminar transacción USDT: {e}")
        flash("Error al eliminar la transacción: " + str(e), "danger")
    return redirect(url_for("admin.resumen_compras_usdt")) 