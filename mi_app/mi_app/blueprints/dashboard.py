import os
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
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
@cache.cached(timeout=300, query_string=True)  # Aumentar cache a 5 minutos
def index():
    try:
        current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
        fecha = request.args.get("fecha", current_date)
        cliente_filtro = request.args.get("cliente", "")
        
        # Optimización: Solo cargar datos de los últimos 30 días para cálculos
        fecha_inicio = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Consulta optimizada: Solo pedidos y pagos relevantes
        pedidos_query = supabase.table("pedidos").select("cliente, fecha, clp, brs").eq("eliminado", False).gte("fecha", fecha_inicio).lte("fecha", fecha)
        pagos_query = supabase.table("pagos_realizados").select("cliente, monto_total, fecha_registro").eq("eliminado", False).gte("fecha_registro", fecha_inicio + "T00:00:00").lte("fecha_registro", fecha + "T23:59:59")
        
        # Ejecutar consultas en paralelo (simulado)
        try:
            pedidos_hist = pedidos_query.execute().data or []
            logging.info(f"[DASHBOARD] Consulta pedidos ejecutada. Total pedidos: {len(pedidos_hist)}")
            
            # Verificar si hay pedidos de MaxiGiros Richard
            maxigiros_pedidos = [p for p in pedidos_hist if 'maxigiros' in p.get('cliente', '').lower() or 'richard' in p.get('cliente', '').lower()]
            if maxigiros_pedidos:
                logging.info(f"[DASHBOARD] Pedidos de MaxiGiros Richard encontrados: {len(maxigiros_pedidos)}")
                for p in maxigiros_pedidos:
                    logging.info(f"[DASHBOARD] Pedido MaxiGiros: {p}")
            else:
                logging.info(f"[DASHBOARD] NO se encontraron pedidos de MaxiGiros Richard")
                
            # Debug: Verificar todos los pedidos de hoy
            pedidos_hoy = [p for p in pedidos_hist if p.get('fecha') == fecha]
            logging.info(f"[DASHBOARD] Total pedidos de hoy ({fecha}): {len(pedidos_hoy)}")
            logging.info(f"[DASHBOARD] Fechas únicas en pedidos: {list(set([p.get('fecha') for p in pedidos_hist if p.get('fecha')]))}")
                
        except Exception as e:
            logging.error(f"[DASHBOARD] Error al consultar pedidos: {e}")
            pedidos_hist = []
            
        try:
            pagos_hist = pagos_query.execute().data or []
            logging.info(f"[DASHBOARD] Consulta pagos ejecutada. Total pagos: {len(pagos_hist)}")
        except Exception as e:
            logging.error(f"[DASHBOARD] Error al consultar pagos: {e}")
            pagos_hist = []
        
        # Procesar datos de manera más eficiente
        clientes_activos = set()
        resumen = {}
        
        # Procesar pedidos
        for p in pedidos_hist:
            if p.get("cliente") and p.get("fecha") and p.get("clp") is not None:
                cliente = p["cliente"]
                
                # Log específico para MaxiGiros Richard
                if 'maxigiros' in cliente.lower() or 'richard' in cliente.lower():
                    logging.info(f"[DASHBOARD] Procesando pedido para {cliente}: fecha={p.get('fecha')}, clp={p.get('clp')}")
                
                clientes_activos.add(cliente)
                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if p["fecha"] == fecha:
                    resumen[cliente]["brs"] += float(p.get("brs", 0))
                    resumen[cliente]["clp"] += float(p["clp"])
                    
                    # Log específico para MaxiGiros Richard
                    if 'maxigiros' in cliente.lower() or 'richard' in cliente.lower():
                        logging.info(f"[DASHBOARD] Pedido de hoy para {cliente}: BRS={p.get('brs')}, CLP={p.get('clp')}")
                        logging.info(f"[DASHBOARD] Resumen actualizado para {cliente}: BRS={resumen[cliente]['brs']}, CLP={resumen[cliente]['clp']}")
                else:
                    # Log para pedidos que NO son de hoy
                    if 'maxigiros' in cliente.lower() or 'richard' in cliente.lower():
                        logging.info(f"[DASHBOARD] Pedido NO de hoy para {cliente}: fecha={p.get('fecha')}, fecha_busqueda={fecha}")
        
        # Procesar pagos
        for p in pagos_hist:
            if p.get("cliente") and p.get("monto_total") is not None:
                cliente = p["cliente"]
                fecha_pago = p.get("fecha_registro", "")[:10]
                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if fecha_pago == fecha:
                    resumen[cliente]["pagos"] += float(p["monto_total"])
        
        # Calcular deuda anterior (todos los pedidos hasta el día anterior)
        fecha_anterior = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Consulta para TODOS los pedidos hasta el día anterior
        pedidos_anterior = supabase.table("pedidos").select("cliente, clp").eq("eliminado", False).lte("fecha", fecha_anterior).execute().data or []
        # Consulta para TODOS los pagos hasta el día anterior CON PAGINACIÓN
        pagos_anterior = []
        offset = 0
        limit = 1000
        while True:
            pedidos_batch = supabase.table("pedidos").select("cliente, clp").eq("eliminado", False).lte("fecha", fecha_anterior).order("fecha", desc=True).range(offset, offset + limit - 1).execute().data or []
            if not pedidos_batch:
                break
            pedidos_anterior.extend(pedidos_batch)
            offset += limit
            if len(pedidos_batch) < limit:
                break
        # Consulta para TODOS los pagos hasta el día anterior CON PAGINACIÓN
        pagos_anterior = []
        offset = 0
        limit = 1000
        while True:
            pagos_batch = supabase.table("pagos_realizados").select("cliente, monto_total").eq("eliminado", False).lte("fecha_registro", fecha_anterior + "T23:59:59").range(offset, offset + limit - 1).execute().data or []
            if not pagos_batch:
                break
            pagos_anterior.extend(pagos_batch)
            offset += limit
            if len(pagos_batch) < limit:
                break
        
        deuda_anterior_por_cliente = {}
        for p in pedidos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] += float(p["clp"])
        
        for p in pagos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] -= float(p["monto_total"])
        
        # Aplicar deuda anterior al resumen
        for cliente in resumen:
            resumen[cliente]["deuda_anterior"] = deuda_anterior_por_cliente.get(cliente, 0)
            resumen[cliente]["diferencia"] = (
                resumen[cliente]["deuda_anterior"] + 
                resumen[cliente]["clp"] - 
                resumen[cliente]["pagos"]
            )
        
        # Log final para MaxiGiros Richard
        if 'MaxiGiros Richard' in resumen:
            maxigiros_final = resumen['MaxiGiros Richard']
            print(f"[API] RESULTADO FINAL MaxiGiros Richard: {maxigiros_final}")
        else:
            print(f"[API] MaxiGiros Richard NO encontrado en resumen final")
        
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
        
        # Log final del resumen para MaxiGiros Richard
        if 'MaxiGiros Richard' in resumen:
            maxigiros_final = resumen['MaxiGiros Richard']
            logging.info(f"[DASHBOARD] RESUMEN FINAL MaxiGiros Richard: {maxigiros_final}")
        
        # Si no hay datos, mostrar mensaje amigable
        if not resumen_list:
            flash("No hay movimientos para la fecha y cliente seleccionados.")
            
    except Exception as e:
        logging.error(f"Error al cargar resumen de pedidos en dashboard: {e}")
        resumen_list = []
        clientes_filtrados = []
        fecha = current_date
        cliente_filtro = ""
        
    return render_template("dashboard/index.html", 
                         resumen=resumen_list, 
                         fecha=fecha, 
                         current_date=current_date, 
                         active_page="dashboard", 
                         clientes=clientes_filtrados, 
                         cliente_filtro=cliente_filtro)

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
            
            # Obtener pedidos
            query_pedidos = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp") \
                .eq("cliente", cliente) \
                .eq("eliminado", False) \
                .gte("fecha", fecha_inicio) \
                .lte("fecha", fecha_fin) \
                .order("fecha", desc=True)
            query_pedidos = query_pedidos.range((page - 1) * per_page, page * per_page - 1)
            response_pedidos = query_pedidos.execute()
            pedidos_data = response_pedidos.data if response_pedidos.data is not None else []
            
            # Contar total de pedidos para paginación
            count_response = supabase.table("pedidos").select("id", count="exact") \
                .eq("cliente", cliente) \
                .eq("eliminado", False) \
                .gte("fecha", fecha_inicio) \
                .lte("fecha", fecha_fin).execute()
            total_count = count_response.count if count_response.count is not None else 0
            total_pages = (total_count + per_page - 1) // per_page
            
            # Obtener pagos (sin paginación, todos en el rango de fechas)
            query_pagos = supabase.table("pagos_realizados").select("id, monto_total, fecha_registro") \
                .eq("cliente", cliente) \
                .eq("eliminado", False) \
                .gte("fecha_registro", fecha_inicio + "T00:00:00") \
                .lte("fecha_registro", fecha_fin + "T23:59:59") \
                .order("fecha_registro", desc=True)
            response_pagos = query_pagos.execute()
            pagos_data = response_pagos.data if response_pagos.data is not None else []
            
            # Calcular flujo de caja
            flujo_caja = []
            saldo_acumulado = 0
            
            # Combinar pedidos y pagos en una sola lista con tipo
            movimientos = []
            
            # Agregar pedidos
            for pedido in pedidos_data:
                movimientos.append({
                    'fecha': pedido['fecha'],
                    'tipo': 'pedido',
                    'monto': float(pedido['clp']),
                    'descripcion': f"Pedido #{pedido['id']} - {pedido['fecha']}",
                    'brs': float(pedido.get('brs', 0)),
                    'tasa': float(pedido.get('tasa', 0))
                })
            
            # Agregar pagos
            for pago in pagos_data:
                fecha_pago = pago['fecha_registro'][:10] if pago['fecha_registro'] else ""
                movimientos.append({
                    'fecha': fecha_pago,
                    'tipo': 'pago',
                    'monto': -float(pago['monto_total']),  # Negativo para pagos
                    'descripcion': f"Pago #{pago['id']} - {fecha_pago}",
                    'brs': 0,
                    'tasa': 0
                })
            
            # Ordenar por fecha (más antiguos primero)
            movimientos.sort(key=lambda x: x['fecha'])
            
            # Calcular saldo acumulado
            for movimiento in movimientos:
                saldo_acumulado += movimiento['monto']
                flujo_caja.append({
                    'fecha': movimiento['fecha'],
                    'tipo': movimiento['tipo'],
                    'monto': movimiento['monto'],
                    'descripcion': movimiento['descripcion'],
                    'saldo_acumulado': saldo_acumulado,
                    'brs': movimiento['brs'],
                    'tasa': movimiento['tasa']
                })
            
            return {
                'pedidos_data': pedidos_data,
                'pagos_data': pagos_data,
                'flujo_caja': flujo_caja,
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
                'pagos_data': [],
                'total_pages': 0,
                'page': 1,
                'fecha_inicio': current_date,
                'fecha_fin': current_date
            }
    
    data = get_detalle_data(cliente)
    return render_template("dashboard/detalle.html", 
                           pedidos=data['pedidos_data'], 
                           pagos=data['pagos_data'],
                           flujo_caja=data['flujo_caja'],
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

@dashboard_bp.route("/api/datos")
@login_required
# Sin caché para datos siempre frescos
def api_datos():
    """API para obtener datos del dashboard de manera eficiente"""
    try:
        fecha = request.args.get("fecha", adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d"))
        cliente_filtro = request.args.get("cliente", "")
        
        # Optimización: Solo cargar datos de los últimos 7 días para cálculos (más eficiente)
        fecha_inicio = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Consultas optimizadas - Rango de 7 días con límite aumentado
        pedidos_query = supabase.table("pedidos").select("cliente, fecha, clp, brs").eq("eliminado", False).gte("fecha", fecha_inicio).lte("fecha", fecha).order("fecha", desc=True).limit(5000)
        pagos_query = supabase.table("pagos_realizados").select("cliente, monto_total, fecha_registro").eq("eliminado", False).gte("fecha_registro", fecha_inicio + "T00:00:00").lte("fecha_registro", fecha + "T23:59:59")
        
        pedidos_hist = pedidos_query.execute().data or []
        pagos_hist = pagos_query.execute().data or []
        
        # Procesar datos
        resumen = {}
        
        # Procesar pedidos
        for p in pedidos_hist:
            if p.get("cliente") and p.get("fecha") and p.get("clp") is not None:
                cliente = p["cliente"]
                

                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if p["fecha"] == fecha:
                    resumen[cliente]["brs"] += float(p.get("brs", 0))
                    resumen[cliente]["clp"] += float(p["clp"])
                    

        
        # Procesar pagos
        for p in pagos_hist:
            if p.get("cliente") and p.get("monto_total") is not None:
                cliente = p["cliente"]
                fecha_pago = p.get("fecha_registro", "")[:10]
                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if fecha_pago == fecha:
                    resumen[cliente]["pagos"] += float(p["monto_total"])
        
        # Calcular deuda anterior (todos los pedidos hasta el día anterior)
        fecha_anterior = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Consulta para TODOS los pedidos hasta el día anterior CON PAGINACIÓN
        pedidos_anterior = []
        offset = 0
        limit = 1000
        while True:
            pedidos_batch = supabase.table("pedidos").select("cliente, clp").eq("eliminado", False).lte("fecha", fecha_anterior).order("fecha", desc=True).range(offset, offset + limit - 1).execute().data or []
            if not pedidos_batch:
                break
            pedidos_anterior.extend(pedidos_batch)
            offset += limit
            if len(pedidos_batch) < limit:
                break
        # Consulta para TODOS los pagos hasta el día anterior CON PAGINACIÓN
        pagos_anterior = []
        offset = 0
        limit = 1000
        while True:
            pagos_batch = supabase.table("pagos_realizados").select("cliente, monto_total").eq("eliminado", False).lte("fecha_registro", fecha_anterior + "T23:59:59").range(offset, offset + limit - 1).execute().data or []
            if not pagos_batch:
                break
            pagos_anterior.extend(pagos_batch)
            offset += limit
            if len(pagos_batch) < limit:
                break
        
        deuda_anterior_por_cliente = {}
        for p in pedidos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] += float(p["clp"])
        
        for p in pagos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] -= float(p["monto_total"])
        
        # Aplicar deuda anterior
        for cliente in resumen:
            resumen[cliente]["deuda_anterior"] = deuda_anterior_por_cliente.get(cliente, 0)
            resumen[cliente]["diferencia"] = (
                resumen[cliente]["deuda_anterior"] + 
                resumen[cliente]["clp"] - 
                resumen[cliente]["pagos"]
            )
        
        # Filtrar clientes con algún valor relevante
        clientes_filtrados = sorted([
            r["cliente"] for r in resumen.values()
            if r["brs"] != 0 or r["clp"] != 0 or r["pagos"] != 0 or r["diferencia"] != 0 or r["deuda_anterior"] != 0
        ])
        
        # Aplicar filtro de cliente si existe
        if cliente_filtro:
            if cliente_filtro in resumen:
                resumen_list = [resumen[cliente_filtro]]
            else:
                resumen_list = []
        else:
            resumen_list = [r for r in resumen.values() if r["cliente"] in clientes_filtrados]
        
        return jsonify({
            "success": True,
            "data": resumen_list,
            "clientes": clientes_filtrados,
            "fecha": fecha,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error en API dashboard: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "clientes": [],
            "fecha": fecha,
            "timestamp": datetime.now().isoformat()
        }), 500 

@dashboard_bp.route("/exportar-csv")
@login_required
def exportar_csv():
    """Exportar datos del dashboard en formato CSV compatible con Excel (UTF-16LE, punto y coma, números como números)"""
    try:
        fecha = request.args.get("fecha", adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d"))
        cliente_filtro = request.args.get("cliente", "")
        
        # Optimización: Solo cargar datos de los últimos 30 días
        fecha_inicio = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Consultas optimizadas
        pedidos_query = supabase.table("pedidos").select("cliente, fecha, clp, brs").eq("eliminado", False).gte("fecha", fecha_inicio).lte("fecha", fecha)
        pagos_query = supabase.table("pagos_realizados").select("cliente, monto_total, fecha_registro").eq("eliminado", False).gte("fecha_registro", fecha_inicio + "T00:00:00").lte("fecha_registro", fecha + "T23:59:59")
        
        pedidos_hist = pedidos_query.execute().data or []
        pagos_hist = pagos_query.execute().data or []
        
        # Procesar datos
        resumen = {}
        
        # Procesar pedidos
        for p in pedidos_hist:
            if p.get("cliente") and p.get("fecha") and p.get("clp") is not None:
                cliente = p["cliente"]
                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if p["fecha"] == fecha:
                    resumen[cliente]["brs"] += float(p.get("brs", 0))
                    resumen[cliente]["clp"] += float(p["clp"])
        
        # Procesar pagos
        for p in pagos_hist:
            if p.get("cliente") and p.get("monto_total") is not None:
                cliente = p["cliente"]
                fecha_pago = p.get("fecha_registro", "")[:10]
                
                if cliente not in resumen:
                    resumen[cliente] = {
                        "cliente": cliente,
                        "brs": 0,
                        "clp": 0,
                        "pagos": 0,
                        "deuda_anterior": 0,
                        "diferencia": 0
                    }
                
                if fecha_pago == fecha:
                    resumen[cliente]["pagos"] += float(p["monto_total"])
        
        # Calcular deuda anterior (todos los pedidos hasta el día anterior)
        fecha_anterior = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Consulta para TODOS los pedidos hasta el día anterior
        pedidos_anterior = supabase.table("pedidos").select("cliente, clp").eq("eliminado", False).lte("fecha", fecha_anterior).execute().data or []
        # Consulta para TODOS los pagos hasta el día anterior CON PAGINACIÓN
        pagos_anterior = []
        offset = 0
        limit = 1000
        while True:
            pagos_batch = supabase.table("pagos_realizados").select("cliente, monto_total").eq("eliminado", False).lte("fecha_registro", fecha_anterior + "T23:59:59").range(offset, offset + limit - 1).execute().data or []
            if not pagos_batch:
                break
            pagos_anterior.extend(pagos_batch)
            offset += limit
            if len(pagos_batch) < limit:
                break
        
        deuda_anterior_por_cliente = {}
        for p in pedidos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] += float(p["clp"])
        
        for p in pagos_anterior:
            cliente = p["cliente"]
            if cliente not in deuda_anterior_por_cliente:
                deuda_anterior_por_cliente[cliente] = 0
            deuda_anterior_por_cliente[cliente] -= float(p["monto_total"])
        
        # Aplicar deuda anterior
        for cliente in resumen:
            resumen[cliente]["deuda_anterior"] = deuda_anterior_por_cliente.get(cliente, 0)
            resumen[cliente]["diferencia"] = (
                resumen[cliente]["deuda_anterior"] + 
                resumen[cliente]["clp"] - 
                resumen[cliente]["pagos"]
            )
        
        # Filtrar clientes con algún valor relevante
        clientes_filtrados = sorted([
            r["cliente"] for r in resumen.values()
            if r["brs"] != 0 or r["clp"] != 0 or r["pagos"] != 0 or r["diferencia"] != 0 or r["deuda_anterior"] != 0
        ])
        
        # Aplicar filtro de cliente si existe
        if cliente_filtro:
            if cliente_filtro in resumen:
                resumen_list = [resumen[cliente_filtro]]
            else:
                resumen_list = []
        else:
            resumen_list = [r for r in resumen.values() if r["cliente"] in clientes_filtrados]
        
        # Generar CSV en memoria (UTF-16LE)
        output = io.StringIO()
        separador = ';'
        encabezado = ["Cliente", "Deuda Anterior", "BRS", "Deuda de Hoy", "Pagos", "Saldo Final", "Estado"]
        output.write(separador.join(encabezado) + "\n")
        for r in resumen_list:
            if r["diferencia"] > 0:
                estado = f"Saldo pendiente {int(r['diferencia'])} Clp"
            elif r["diferencia"] < 0:
                estado = f"Saldo a Favor de {abs(int(r['diferencia']))} Clp"
            else:
                estado = "Sin saldo pendiente"
            cliente = r["cliente"].replace('"', '""')
            fila = [
                f'"{cliente}"',
                str(int(r["deuda_anterior"])),
                str(int(r["brs"])),
                str(int(r["clp"])),
                str(int(r["pagos"])),
                str(int(r["diferencia"])),
                f'"{estado}"'
            ]
            output.write(separador.join(fila) + "\n")
        csv_text = output.getvalue()
        output.close()
        # Codificar a UTF-16LE con BOM
        bom = b'\xff\xfe'
        csv_bytes = bom + csv_text.encode('utf-16le')
        from flask import Response
        response = Response(csv_bytes, mimetype='text/csv; charset=utf-16')
        response.headers['Content-Disposition'] = f'attachment; filename=dashboard_{fecha}.csv'
        return response
    except Exception as e:
        logging.error(f"Error al exportar CSV del dashboard: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@dashboard_bp.route("/api/cliente/<cliente>")
@login_required
def api_cliente_detalle(cliente):
    """API para obtener detalles del cliente para el modal"""
    try:
        # Obtener TODOS los pedidos del cliente (sin límite)
        pedidos_resp = supabase.table("pedidos").select(
            "id, fecha, brs, clp, tasa"
        ).eq("cliente", cliente).eq("eliminado", False).order(
            "fecha", desc=True
        ).execute()
        
        pedidos = pedidos_resp.data or []
        
        # Obtener TODOS los pagos del cliente (sin límite)
        pagos_resp = supabase.table("pagos_realizados").select(
            "id, monto_total, fecha_registro"
        ).eq("cliente", cliente).eq("eliminado", False).order(
            "fecha_registro", desc=True
        ).execute()
        
        pagos = pagos_resp.data or []
        
        # Calcular resumen de deuda
        fecha_actual = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
        fecha_anterior = (datetime.strptime(fecha_actual, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Deuda anterior (todos los pedidos hasta ayer)
        pedidos_hist = supabase.table("pedidos").select("clp").eq("cliente", cliente).eq("eliminado", False).lte("fecha", fecha_anterior).execute().data or []
        pagos_hist = supabase.table("pagos_realizados").select("monto_total").eq("cliente", cliente).eq("eliminado", False).lte("fecha_registro", fecha_anterior + "T23:59:59").execute().data or []
        
        deuda_anterior = sum(float(p["clp"]) for p in pedidos_hist) - sum(float(p["monto_total"]) for p in pagos_hist)
        
        # Pedidos de hoy
        pedidos_hoy = supabase.table("pedidos").select("clp").eq("cliente", cliente).eq("eliminado", False).eq("fecha", fecha_actual).execute().data or []
        clp_hoy = sum(float(p["clp"]) for p in pedidos_hoy)
        
        # Pagos de hoy
        pagos_hoy = supabase.table("pagos_realizados").select("monto_total").eq("cliente", cliente).eq("eliminado", False).gte("fecha_registro", fecha_actual + "T00:00:00").lte("fecha_registro", fecha_actual + "T23:59:59").execute().data or []
        pagos_hoy_total = sum(float(p["monto_total"]) for p in pagos_hoy)
        
        # Saldo final
        saldo_final = deuda_anterior + clp_hoy - pagos_hoy_total
        
        # Formatear datos para el frontend
        pedidos_formateados = []
        for p in pedidos:
            brs = float(p.get("brs", 0))
            clp = float(p["clp"])
            
            pedidos_formateados.append({
                "fecha": p["fecha"],
                "brs": brs,
                "clp": clp
            })
        
        pagos_formateados = []
        for p in pagos:
            fecha_pago = p["fecha_registro"][:10] if p["fecha_registro"] else ""
            pagos_formateados.append({
                "fecha": fecha_pago,
                "monto": float(p["monto_total"])
            })
        
        return jsonify({
            "success": True,
            "cliente": cliente,
            "fecha_servidor": fecha_actual,  # Agregar fecha del servidor
            "pedidos": pedidos_formateados,
            "pagos": pagos_formateados,
            "resumen": {
                "deuda_anterior": deuda_anterior,
                "pedidos_hoy": clp_hoy,
                "pagos_hoy": pagos_hoy_total,
                "saldo_final": saldo_final
            }
        })
        
    except Exception as e:
        logging.error(f"Error al obtener detalles del cliente {cliente}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 

 