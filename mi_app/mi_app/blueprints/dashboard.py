import os
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
from flask_caching import Cache
import pytz
from mi_app.mi_app.extensions import cache

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

# Crear blueprint
dashboard_bp = Blueprint("dashboard", __name__)

def init_cache(cache_instance):
    global cache
    cache = cache_instance

def get_ultimo_saldo_anterior(cliente, fecha, supabase):
    """
    Busca hacia atrás el último saldo final distinto de cero para el cliente antes de la fecha dada.
    Devuelve 0 si no encuentra ninguno.
    """
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    for _ in range(60):  # Máximo 60 días hacia atrás para evitar bucles infinitos
        fecha_dt -= timedelta(days=1)
        fecha_str = fecha_dt.strftime("%Y-%m-%d")
        # Pedidos y pagos del día
        pedidos = supabase.table("pedidos").select("clp").eq("fecha", fecha_str).eq("cliente", cliente).eq("eliminado", False).execute().data or []
        pagos = supabase.table("pagos_realizados").select("monto_total, fecha_registro").eq("cliente", cliente).eq("eliminado", False).execute().data or []
        pagos_dia = [float(p["monto_total"]) for p in pagos if p.get("fecha_registro", "")[:10] == fecha_str]
        clp = sum(float(p["clp"]) for p in pedidos)
        pagos_total = sum(pagos_dia)
        # Obtener saldo anterior de ese día
        saldo_ant = get_ultimo_saldo_anterior(cliente, fecha_str, supabase) if _ > 0 else 0
        saldo_final = saldo_ant + clp - pagos_total
        if clp != 0 or pagos_total != 0 or saldo_final != 0:
            return saldo_final
    return 0

@dashboard_bp.route("/", methods=["GET"])
@login_required
@cache.cached(timeout=60, query_string=True)
def index():
    try:
        current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
        fecha = request.args.get("fecha", current_date)
        cliente_filtro = request.args.get("cliente", "")
        # Filtrar y limpiar pedidos y pagos históricos
        pedidos_hist = [p for p in supabase.table("pedidos").select("cliente, fecha, clp, brs, eliminado").eq("eliminado", False).execute().data or []
                        if p.get("cliente") and p.get("fecha") and p.get("clp") is not None and p.get("brs") is not None]
        pagos_hist = [p for p in supabase.table("pagos_realizados").select("cliente, monto_total, fecha_registro, eliminado").eq("eliminado", False).execute().data or []
                      if p.get("cliente") and p.get("fecha_registro") and p.get("monto_total") is not None]
        # Construir set de fechas relevantes
        fechas_pedidos = set(p["fecha"] for p in pedidos_hist)
        fechas_pagos = set(p["fecha_registro"][:10] for p in pagos_hist if p.get("fecha_registro"))
        fechas_todas = sorted(set(list(fechas_pedidos) + list(fechas_pagos) + [fecha]))
        # Construir historial de saldos por cliente y fecha
        clientes_todos = set(p["cliente"] for p in pedidos_hist) | set(p["cliente"] for p in pagos_hist)
        saldo_por_cliente_fecha = {c: {} for c in clientes_todos}
        for cliente in clientes_todos:
            saldo = 0
            for f in fechas_todas:
                try:
                    pedidos_dia = [float(p["clp"]) for p in pedidos_hist if p["cliente"] == cliente and p["fecha"] == f]
                except Exception:
                    pedidos_dia = []
                try:
                    pagos_dia = [float(p["monto_total"]) for p in pagos_hist if p["cliente"] == cliente and p.get("fecha_registro", "")[:10] == f]
                except Exception:
                    pagos_dia = []
                saldo = saldo + sum(pedidos_dia) - sum(pagos_dia)
                saldo_por_cliente_fecha[cliente][f] = saldo
        # Ahora, para la fecha seleccionada, usar el saldo anterior correcto
        resumen = {}
        for cliente in clientes_todos:
            # Deuda anterior: saldo del día anterior
            idx_fecha = fechas_todas.index(fecha)
            if idx_fecha > 0:
                fecha_ant = fechas_todas[idx_fecha-1]
                deuda_anterior = saldo_por_cliente_fecha[cliente][fecha_ant]
            else:
                deuda_anterior = 0
            # Pedidos y pagos del día actual (solo del día seleccionado)
            try:
                brs = sum(float(p["brs"]) for p in pedidos_hist if p["cliente"] == cliente and p["fecha"] == fecha)
            except Exception:
                brs = 0
            try:
                clp = sum(float(p["clp"]) for p in pedidos_hist if p["cliente"] == cliente and p["fecha"] == fecha)
            except Exception:
                clp = 0
            try:
                pagos_dia = sum(float(p["monto_total"]) for p in pagos_hist if p["cliente"] == cliente and p.get("fecha_registro", "")[:10] == fecha)
            except Exception:
                pagos_dia = 0
            saldo_final = saldo_por_cliente_fecha[cliente][fecha]
            resumen[cliente] = {
                "cliente": cliente,
                "brs": brs,
                "clp": clp,
                "pagos": pagos_dia,
                "deuda_anterior": deuda_anterior,
                "diferencia": saldo_final
            }
        # Filtrar clientes con algún valor relevante
        clientes_filtrados = sorted([
            r["cliente"] for r in resumen.values()
            if r["brs"] != 0 or r["clp"] != 0 or r["pagos"] != 0 or r["diferencia"] != 0 or r["deuda_anterior"] != 0
        ])
        # Si hay filtro de cliente, mostrar solo ese cliente
        if cliente_filtro:
            if cliente_filtro in resumen:
                resumen_list = [resumen[cliente_filtro]]
            else:
                resumen_list = []
        else:
            resumen_list = [r for r in resumen.values() if r["cliente"] in clientes_filtrados]
        # Si no hay datos, mostrar mensaje amigable
        if not resumen_list:
            flash("No hay movimientos para la fecha y cliente seleccionados.")
    except Exception as e:
        logging.error(f"Error al cargar resumen de pedidos en dashboard: {e}")
        resumen_list = []
        clientes_filtrados = []
        fecha = current_date
        cliente_filtro = ""
    return render_template("dashboard/index.html", resumen=resumen_list, fecha=fecha, current_date=current_date, active_page="dashboard", clientes=clientes_filtrados, cliente_filtro=cliente_filtro)

@dashboard_bp.route("/detalle/<cliente>")
@login_required
def detalle(cliente):
    if cache is None:
        # Si no hay cache configurado, usar un decorador dummy
        def dummy_cache(timeout=60, query_string=True):
            def decorator(f):
                return f
            return decorator
        cache_decorator = dummy_cache
    else:
        cache_decorator = cache.cached
    
    @cache_decorator(timeout=60, query_string=True)
    def get_detalle_data(cliente):
        try:
            current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
            fecha_inicio = request.args.get("fecha_inicio", current_date)
            fecha_fin = request.args.get("fecha_fin", current_date)
            try:
                page = int(request.args.get("page", 1))
            except ValueError:
                page = 1
            per_page = 10
            query = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp") \
                .eq("cliente", cliente) \
                .gte("fecha", fecha_inicio) \
                .lte("fecha", fecha_fin)
            query = query.range((page - 1) * per_page, page * per_page - 1)
            response = query.execute()
            pedidos_data = response.data if response.data is not None else []
            count_response = supabase.table("pedidos").select("id", count="exact") \
                .eq("cliente", cliente) \
                .gte("fecha", fecha_inicio) \
                .lte("fecha", fecha_fin).execute()
            total_count = count_response.count if count_response.count is not None else 0
            total_pages = (total_count + per_page - 1) // per_page
            return {
                'pedidos_data': pedidos_data,
                'total_pages': total_pages,
                'page': page,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
        except Exception as e:
            logging.error("Error al obtener el detalle para el cliente %s: %s", cliente, e)
            flash("Error al obtener el detalle: " + str(e))
            return {
                'pedidos_data': [],
                'total_pages': 0,
                'page': 1,
                'fecha_inicio': current_date,
                'fecha_fin': current_date
            }
    
    data = get_detalle_data(cliente)
    return render_template("dashboard/detalle.html", 
                           pedidos=data['pedidos_data'], 
                           cliente=cliente, 
                           fecha_inicio=data['fecha_inicio'],
                           fecha_fin=data['fecha_fin'], 
                           page=data['page'], 
                           total_pages=data['total_pages'])

@dashboard_bp.route("/actualizar", methods=["POST"])
@login_required
def actualizar():
    try:
        cache.clear()
        flash("¡Dashboard actualizado!")
    except Exception as e:
        flash(f"Error al actualizar el dashboard: {e}")
    return redirect(url_for("dashboard.index"))

@dashboard_bp.route("/limpiar_cache", methods=["POST"])
@login_required
def limpiar_cache():
    try:
        cache.clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500 