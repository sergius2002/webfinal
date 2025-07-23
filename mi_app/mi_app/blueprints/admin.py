import os
import logging
import hashlib
import asyncio
from datetime import datetime, timedelta
from functools import wraps
import json

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import pytz
from mi_app.mi_app.usdt_ves import obtener_valor_usdt_por_banco
from mi_app.mi_app.blueprints.pedidos import registrar_movimiento_cuenta

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

# Decorador para módulos restringidos - SOLO SUPERUSUARIOS
def user_allowed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        email = session.get("email")
        logging.info(f"Verificando acceso para email: {email}")
        if not email:
            flash("Debes iniciar sesión.")
            return redirect(url_for("login"))
        try:
            # SOLO verificar si es superusuario
            logging.info(f"Consultando tabla superusuarios para: {email}")
            superuser_response = supabase.table("superusuarios").select("email").eq("email", email).execute()
            logging.info(f"Respuesta de superusuarios: {superuser_response.data}")
            if not superuser_response.data:
                flash("Acceso denegado. Solo superusuarios pueden acceder al módulo administrativo.")
                return redirect(url_for("index"))
            logging.info(f"Acceso permitido para superusuario: {email}")
        except Exception as e:
            logging.error("Error al verificar superusuario: %s", e)
            flash("Error interno al verificar permisos.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

# Decorador específico para superusuarios
def superuser_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        email = session.get("email")
        if not email:
            flash("Debes iniciar sesión.")
            return redirect(url_for("login"))
        try:
            response = supabase.table("superusuarios").select("email").eq("email", email).execute()
            if not response.data:
                flash("Acceso denegado. Solo superusuarios pueden acceder a esta función.")
                return redirect(url_for("index"))
        except Exception as e:
            logging.error("Error al verificar superusuario: %s", e)
            flash("Error interno al verificar permisos.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

# Función para generar hash único para cada transferencia
def generar_hash_transferencia(transferencia):
    data = f"{transferencia.get('id')}-{transferencia.get('fecha')}-{transferencia.get('monto')}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

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
    tasa_str = f"{tasa:.10f}"
    if '.' in tasa_str:
        parte_entera = tasa_str.split('.')[0]
        parte_decimal = tasa_str.split('.')[1]
    else:
        parte_entera = tasa_str
        parte_decimal = ""
    digitos_enteros = len(parte_entera)
    if digitos_enteros >= 6:
        return f"{tasa:.0f}"
    decimales_necesarios = 6 - digitos_enteros
    return f"{tasa:.{decimales_necesarios}f}"

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
            .select("id, totalprice, paymethodname, createtime, unitprice, costo_no_vendido") \
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
        # CONSULTA DE CUENTAS ACTIVAS
        cuentas_activas = supabase.table("cuentas_activas").select("*").eq("activa", True).execute().data
        # CONSULTA DE DEPOSITOS BRS PARA EL DIA
        depositos = supabase.table("depositos_brs").select("compra_id, cuenta_id").execute().data
        # Crear un diccionario para lookup rápido
        cuenta_por_compra = {dep['compra_id']: dep['cuenta_id'] for dep in depositos}
        # SUMAR BRS POR CUENTA
        brs_por_cuenta = {}
        for row in compras_data:
            # Asignar cuenta_id a cada compra si existe
            row['cuenta_id'] = cuenta_por_compra.get(row['id'])
        for dep in depositos:
            compra = next((c for c in compras_data if c['id'] == dep['compra_id']), None)
            if compra:
                cuenta_id = dep['cuenta_id']
                brs = compra['totalprice']
                if cuenta_id not in brs_por_cuenta:
                    brs_por_cuenta[cuenta_id] = 0
                brs_por_cuenta[cuenta_id] += brs
        resumen_cuentas = []
        for cuenta in cuentas_activas:
            resumen_cuentas.append({
                "nombre_titular": cuenta["nombre_titular"],
                "brs": brs_por_cuenta.get(cuenta["id"], 0)
            })
    except Exception as e:
        logging.error("Error al obtener los datos: %s", e)
        compras_data = []
        cuentas_activas = []
        resumen_cuentas = []
    return render_template("admin/tasa_compras.html", active_page="admin",
                           compras_data=compras_data, fecha=fecha, cuentas_activas=cuentas_activas, resumen_cuentas=resumen_cuentas)

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
        # Obtener el costo_no_vendido de la vista_compras_fifo (para mostrar como referencia)
        query = supabase.table("vista_compras_fifo").select("costo_no_vendido, createtime") \
            .order("createtime", desc=True) \
            .limit(1)
        response = query.execute()
        if response.data and len(response.data) > 0:
            record = response.data[0]
            costo_no_vendido = record.get("costo_no_vendido")
        else:
            costo_no_vendido = None
            flash("No se encontró ningún registro de costo.", "warning")
        
        # Calcular el stock USDT usando la misma lógica exacta del módulo de márgenes
        # SIEMPRE usar cálculo dinámico, NO depender de stock_diario de hoy
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        fecha_ayer = (datetime.strptime(fecha_hoy, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 1. Obtener saldo anterior USDT (de stock_diario del día anterior)
        row_anterior = supabase.table("stock_diario").select("usdt_stock").eq("fecha", fecha_ayer).execute().data
        usdt_anterior = float(row_anterior[0]["usdt_stock"]) if row_anterior and row_anterior[0].get("usdt_stock") is not None else 0
        
        # 2. Obtener USDT COMPRADOS hoy (costo_real de compras CLP BUY)
        inicio = fecha_hoy + "T00:00:00"
        fin = fecha_hoy + "T23:59:59"
        compras_usdt = supabase.table("compras").select("costo_real, unitprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_comprados = sum(float(c["costo_real"]) for c in compras_usdt) if compras_usdt else 0
        
        # 3. Obtener USDT VENDIDOS hoy (amount de compras CLP SELL) - ¡IMPORTANTE! Usar 'amount', no 'costo_real'
        ventas_usdt_clp = supabase.table("compras").select("amount").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_vendidos_clp = sum(float(c["amount"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0

        # 3.1. Obtener USDT VENDIDOS hoy en VES (amount + commission de compras VES SELL) - ¡IMPORTANTE! Usar amount + commission como en márgenes
        ventas_usdt_ves = supabase.table("compras").select("amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_vendidos_ves = sum(float(c["amount"]) + float(c.get("commission", 0)) for c in ventas_usdt_ves) if ventas_usdt_ves else 0

        # 4. Calcular stock USDT actual: Saldo Anterior + USDT COMPRADOS - USDT VENDIDOS (CLP + VES)
        stock_usdt = usdt_anterior + usdt_comprados - usdt_vendidos_clp - usdt_vendidos_ves
        
        # 5. OPCIÓN 1: Calcular el costo promedio ponderado real del stock USDT actual
        if stock_usdt > 0:
            # Calcular el valor CLP total del stock actual
            # Esto incluye: stock anterior + compras de hoy - ventas de hoy
            valor_clp_stock_anterior = usdt_anterior * costo_no_vendido
            
            # Calcular valor CLP de las compras de hoy
            valor_clp_compras_hoy = 0
            if compras_usdt:
                for compra in compras_usdt:
                    # Usar costo_real * unitprice para obtener el valor CLP total
                    valor_clp_compras_hoy += float(compra.get("costo_real", 0)) * float(compra.get("unitprice", 0))
            
            # Calcular valor CLP de las ventas de hoy (para restar)
            valor_clp_ventas_clp_hoy = usdt_vendidos_clp * costo_no_vendido
            valor_clp_ventas_ves_hoy = usdt_vendidos_ves * costo_no_vendido
            
            # Valor CLP total del stock actual
            valor_clp_stock = valor_clp_stock_anterior + valor_clp_compras_hoy - valor_clp_ventas_clp_hoy - valor_clp_ventas_ves_hoy
            
            # Costo promedio ponderado real del stock actual
            costo_promedio_stock = valor_clp_stock / stock_usdt if stock_usdt > 0 else costo_no_vendido
        else:
            valor_clp_stock = 0
            costo_promedio_stock = costo_no_vendido if costo_no_vendido else 0
        
    except Exception as e:
        logging.error("Error al obtener la tasa actual desde Supabase: %s", e)
        flash("Error al obtener la tasa actual: " + str(e), "danger")
        costo_no_vendido = None
        stock_usdt = None
        valor_clp_stock = 0
        costo_promedio_stock = 0

    resultado_banesco = None
    resultado_bank = None
    resultado_banesco_stock = None
    resultado_bank_stock = None

    if costo_no_vendido is not None and stock_usdt is not None and stock_usdt > 0:
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
                # Tasa tradicional (usando costo_no_vendido)
                resultado_banesco = format_tasa_6_digits(float(banesco_val) / float(costo_no_vendido))
                resultado_bank = format_tasa_6_digits(float(bank_val) / float(costo_no_vendido))
                
                # OPCIÓN 1: Tasa basada en stock USDT real
                if valor_clp_stock > 0:
                    # Fórmula: precio_binance / (valor_clp_stock / stock_usdt)
                    # Esto es equivalente a: precio_binance / costo_promedio_stock
                    # Pero más preciso porque usa el stock real
                    tasa_banesco_stock = float(banesco_val) / costo_promedio_stock
                    tasa_bank_stock = float(bank_val) / costo_promedio_stock
                    resultado_banesco_stock = format_tasa_6_digits(tasa_banesco_stock)
                    resultado_bank_stock = format_tasa_6_digits(tasa_bank_stock)
                
                logging.info(f"Tasas calculadas - Banesco: {resultado_banesco}, Venezuela: {resultado_bank}")
                logging.info(f"Tasas basadas en stock - Banesco: {resultado_banesco_stock}, Venezuela: {resultado_bank_stock}")
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
        valor_clp_stock=valor_clp_stock,
        costo_promedio_stock=costo_promedio_stock,
        resultado_banesco=resultado_banesco,
        resultado_bank=resultado_bank,
        resultado_banesco_stock=resultado_banesco_stock,
        resultado_bank_stock=resultado_bank_stock
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

@admin_bp.route('/configuracion-inicial')
@login_required
def configuracion_inicial():
    """Configuración del primer día y saldo inicial del sistema"""
    try:
        # Buscar configuración existente
        config_response = supabase.table("configuracion_sistema").select("*").eq("clave", "inicio_operaciones").execute()
        
        config_data = {
            'fecha_inicio': '',
            'saldo_inicial': 0,
            'configurado': False
        }
        
        if config_response.data:
            config = config_response.data[0]
            try:
                valores = json.loads(config.get('valor', '{}'))
                config_data.update(valores)
                config_data['configurado'] = True
            except:
                pass
        
        return render_template('admin/configuracion_inicial.html', 
                             active_page='admin',
                             config=config_data)
    except Exception as e:
        logging.error(f"Error al cargar configuración inicial: {e}")
        flash("Error al cargar la configuración")
        return redirect(url_for('admin.index'))

@admin_bp.route('/guardar-configuracion-inicial', methods=['POST'])
@login_required
def guardar_configuracion_inicial():
    """Guarda la configuración inicial del sistema"""
    try:
        data = request.get_json()
        fecha_inicio = data.get('fecha_inicio')
        saldo_inicial = float(data.get('saldo_inicial', 0))
        
        # Validar fecha
        try:
            datetime.strptime(fecha_inicio, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de fecha inválido'}), 400
        
        # Validar saldo
        if saldo_inicial < 0:
            return jsonify({'success': False, 'message': 'El saldo inicial no puede ser negativo'}), 400
        
        # Preparar datos de configuración
        configuracion = {
            'fecha_inicio': fecha_inicio,
            'saldo_inicial': saldo_inicial,
            'configurado': True,
            'usuario_config': session.get('email', 'usuario_desconocido'),
            'fecha_config': datetime.now().isoformat()
        }
        
        config_data = {
            'clave': 'inicio_operaciones',
            'valor': json.dumps(configuracion),
            'descripcion': 'Configuración del primer día de operaciones y saldo inicial',
            'usuario_modificacion': session.get('email', 'usuario_desconocido')
        }
        
        # Verificar si ya existe configuración
        existing_response = supabase.table("configuracion_sistema").select("id").eq("clave", "inicio_operaciones").execute()
        
        if existing_response.data:
            # Actualizar existente
            config_id = existing_response.data[0]['id']
            response = supabase.table("configuracion_sistema").update(config_data).eq("id", config_id).execute()
            message = "Configuración actualizada exitosamente"
        else:
            # Crear nueva configuración
            response = supabase.table("configuracion_sistema").insert(config_data).execute()
            message = "Configuración guardada exitosamente"
        
        if response.data:
            logging.info(f"Configuración inicial guardada: {fecha_inicio} con saldo {saldo_inicial}")
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
            
    except ValueError:
        return jsonify({'success': False, 'message': 'Saldo inicial debe ser un número válido'}), 400
    except Exception as e:
        logging.error(f"Error al guardar configuración inicial: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@admin_bp.route('/superusuarios')
@login_required
@user_allowed
def gestion_superusuarios():
    """Gestión de superusuarios - solo accesible por superusuarios"""
    try:
        # Obtener lista de superusuarios
        superusuarios_response = supabase.table("superusuarios").select("*").order("created_at", desc=True).execute()
        superusuarios = superusuarios_response.data if superusuarios_response.data else []
        
        # Obtener lista de usuarios permitidos (para migración)
        try:
            # Primero intentar obtener solo las columnas básicas
            allowed_response = supabase.table("allowed_users").select("id, email").execute()
            allowed_users = allowed_response.data if allowed_response.data else []
            logging.info(f"Usuarios permitidos encontrados: {len(allowed_users)}")
        except Exception as e:
            logging.warning(f"No se pudo obtener usuarios permitidos: {e}")
            allowed_users = []
        
        return render_template('admin/superusuarios.html', 
                             active_page='admin',
                             superusuarios=superusuarios,
                             allowed_users=allowed_users)
    except Exception as e:
        logging.error(f"Error al cargar gestión de superusuarios: {e}")
        flash("Error al cargar la gestión de superusuarios")
        return redirect(url_for('admin.index'))

@admin_bp.route('/agregar-superusuario', methods=['POST'])
@login_required
@user_allowed
def agregar_superusuario():
    """Agregar un nuevo superusuario"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'El email es requerido'}), 400
        
        # Validar formato de email
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400
        
        # Verificar si ya existe
        existing_response = supabase.table("superusuarios").select("id").eq("email", email).execute()
        if existing_response.data:
            return jsonify({'success': False, 'message': 'Este email ya está registrado como superusuario'}), 400
        
        # Agregar superusuario
        superusuario_data = {
            'email': email,
            'usuario_creacion': session.get('email', 'usuario_desconocido'),
            'activo': True
        }
        
        response = supabase.table("superusuarios").insert(superusuario_data).execute()
        
        if response.data:
            logging.info(f"Superusuario agregado: {email} por {session.get('email')}")
            return jsonify({'success': True, 'message': 'Superusuario agregado exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'Error al agregar superusuario'}), 500
            
    except Exception as e:
        logging.error(f"Error al agregar superusuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@admin_bp.route('/eliminar-superusuario/<int:superusuario_id>', methods=['POST'])
@login_required
@user_allowed
def eliminar_superusuario(superusuario_id):
    """Eliminar un superusuario"""
    try:
        # Verificar que no se elimine a sí mismo
        current_email = session.get('email')
        superusuario_response = supabase.table("superusuarios").select("email").eq("id", superusuario_id).execute()
        
        if not superusuario_response.data:
            return jsonify({'success': False, 'message': 'Superusuario no encontrado'}), 404
        
        superusuario_email = superusuario_response.data[0]['email']
        
        if superusuario_email == current_email:
            return jsonify({'success': False, 'message': 'No puedes eliminar tu propia cuenta de superusuario'}), 400
        
        # Eliminar superusuario
        response = supabase.table("superusuarios").delete().eq("id", superusuario_id).execute()
        
        if response.data:
            logging.info(f"Superusuario eliminado: {superusuario_email} por {current_email}")
            return jsonify({'success': True, 'message': 'Superusuario eliminado exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'Error al eliminar superusuario'}), 500
            
    except Exception as e:
        logging.error(f"Error al eliminar superusuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@admin_bp.route('/migrar-usuario-a-superusuario/<int:user_id>', methods=['POST'])
@login_required
@user_allowed
def migrar_usuario_a_superusuario(user_id):
    """Migrar un usuario permitido a superusuario"""
    try:
        # Obtener datos del usuario permitido
        user_response = supabase.table("allowed_users").select("*").eq("id", user_id).execute()
        
        if not user_response.data:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        
        user_data = user_response.data[0]
        email = user_data['email']
        
        # Verificar si ya es superusuario
        existing_response = supabase.table("superusuarios").select("id").eq("email", email).execute()
        if existing_response.data:
            return jsonify({'success': False, 'message': 'Este usuario ya es superusuario'}), 400
        
        # Agregar como superusuario
        superusuario_data = {
            'email': email,
            'usuario_creacion': session.get('email', 'usuario_desconocido'),
            'activo': True
        }
        
        response = supabase.table("superusuarios").insert(superusuario_data).execute()
        
        if response.data:
            logging.info(f"Usuario migrado a superusuario: {email} por {session.get('email')}")
            return jsonify({'success': True, 'message': 'Usuario migrado a superusuario exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'Error al migrar usuario'}), 500
            
    except Exception as e:
        logging.error(f"Error al migrar usuario a superusuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@admin_bp.route("/asignar_cuenta_compra", methods=["POST"])
@login_required
@user_allowed
def asignar_cuenta_compra():
    data = request.get_json()
    compra_id = data.get("compra_id")
    cuenta_id = data.get("cuenta_id")
    if not compra_id or not cuenta_id:
        return jsonify({"success": False, "error": "Datos incompletos"}), 400
    try:
        # Verificar si ya existe un registro para esa compra
        existing = supabase.table("depositos_brs").select("cuenta_id").eq("compra_id", compra_id).execute().data
        cuenta_anterior = existing[0]["cuenta_id"] if existing else None
        if existing:
            # Actualizar el registro existente
            supabase.table("depositos_brs").update({
                "cuenta_id": cuenta_id,
                "fecha_asignacion": datetime.now().isoformat()
            }).eq("compra_id", compra_id).execute()
        else:
            # Crear nuevo registro
            supabase.table("depositos_brs").insert({
                "compra_id": compra_id,
                "cuenta_id": cuenta_id
            }).execute()
        # Obtener el monto de la compra (BRS)
        compra = supabase.table("vista_compras_fifo").select("totalprice").eq("id", compra_id).single().execute().data
        logging.info(f"[asignar_cuenta_compra] compra_id={compra_id}, cuenta_id={cuenta_id}, compra={compra}, cuenta_anterior={cuenta_anterior}")
        if compra and "totalprice" in compra:
            monto_brs = int(round(compra["totalprice"]))
            descripcion = f"Compra asignada desde módulo compras"
            # Si la cuenta anterior es distinta, revertir saldo en la anterior
            if cuenta_anterior and cuenta_anterior != cuenta_id:
                descripcion_ajuste = f"Ajuste por reasignación de compra (ID {compra_id})"
                registrar_movimiento_cuenta(cuenta_anterior, "AJUSTE", -monto_brs, compra_id, "compra", descripcion_ajuste)
                logging.info(f"[asignar_cuenta_compra] Ajuste negativo en cuenta_anterior={cuenta_anterior} por {-monto_brs}")
            # Registrar movimiento COMPRA en la cuenta nueva
            resultado = registrar_movimiento_cuenta(cuenta_id, "COMPRA", monto_brs, compra_id, "compra", descripcion)
            logging.info(f"[asignar_cuenta_compra] registrar_movimiento_cuenta resultado={resultado}, monto_brs={monto_brs}")
        else:
            logging.warning(f"[asignar_cuenta_compra] No se encontró totalprice para compra_id={compra_id}")
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"[asignar_cuenta_compra] Excepción: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route("/resumen_cuentas_brs", methods=["GET"])
@login_required
@user_allowed
def resumen_cuentas_brs():
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    try:
        compras_data = supabase.table("vista_compras_fifo") \
            .select("id, totalprice, paymethodname, createtime, unitprice, costo_no_vendido") \
            .eq("fiat", "VES") \
            .gte("createtime", inicio) \
            .lte("createtime", fin) \
            .execute().data or []
        cuentas_activas = supabase.table("cuentas_activas").select("*").eq("activa", True).execute().data
        depositos = supabase.table("depositos_brs").select("compra_id, cuenta_id").execute().data
        brs_por_cuenta = {}
        for dep in depositos:
            compra = next((c for c in compras_data if c['id'] == dep['compra_id']), None)
            if compra:
                cuenta_id = dep['cuenta_id']
                brs = compra['totalprice']
                if cuenta_id not in brs_por_cuenta:
                    brs_por_cuenta[cuenta_id] = 0
                brs_por_cuenta[cuenta_id] += brs
        resumen_cuentas = []
        for cuenta in cuentas_activas:
            resumen_cuentas.append({
                "nombre_titular": cuenta["nombre_titular"],
                "brs": brs_por_cuenta.get(cuenta["id"], 0)
            })
        # Solo cuentas con más de 1000 BRS
        resumen_cuentas = [c for c in resumen_cuentas if c["brs"] > 1000]
        return jsonify({"resumen_cuentas": resumen_cuentas})
    except Exception as e:
        return jsonify({"resumen_cuentas": [], "error": str(e)}), 500 