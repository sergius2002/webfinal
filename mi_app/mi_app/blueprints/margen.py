from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for
from datetime import datetime, timedelta
from supabase import create_client
import os

margen_bp = Blueprint("margen", __name__)

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Protección por contraseña simple
@ margen_bp.before_request
def require_password():
    if session.get('margen_autorizado'):
        return None
    if request.method == 'POST' and request.form.get('margen_password') == 'Ps.1784':
        session['margen_autorizado'] = True
        return redirect(request.path)
    if request.endpoint and request.endpoint.startswith('margen.'):
        return '''
        <form method="post" style="max-width:350px;margin:60px auto;padding:2em 2em 1em 2em;border:1px solid #ccc;border-radius:8px;box-shadow:0 2px 8px #eee;background:#fafbfc;">
            <h4 style="text-align:center;">Acceso protegido</h4>
            <div class="mb-3">
                <input type="password" class="form-control" name="margen_password" placeholder="Contraseña" autofocus required style="width:100%;padding:0.5em;margin-bottom:1em;">
            </div>
            <button type="submit" class="btn btn-primary w-100">Entrar</button>
        </form>
        '''

@margen_bp.route("/guardar_sobrantes", methods=["POST"])
def guardar_sobrantes():
    """Guarda los sobrantes del día en la tabla stock_diario"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos'}), 400
        
        fecha = data.get('fecha')
        brs_stock = data.get('brs_stock')
        usdt_stock = data.get('usdt_stock')
        tasa_ves_clp = data.get('tasa_ves_clp')
        usdt_tasa = data.get('usdt_tasa')
        
        if not all([fecha, brs_stock is not None, usdt_stock is not None, tasa_ves_clp is not None, usdt_tasa is not None]):
            return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400
        
        # Validar que los valores sean números válidos
        try:
            brs_stock = float(brs_stock)
            usdt_stock = float(usdt_stock)
            tasa_ves_clp = float(tasa_ves_clp)
            usdt_tasa = float(usdt_tasa)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Los valores deben ser números válidos'}), 400
        
        # Preparar datos para insertar/actualizar
        stock_data = {
            'fecha': fecha,
            'brs_stock': brs_stock,
            'usdt_stock': usdt_stock,
            'tasa_ves_clp': tasa_ves_clp,
            'usdt_tasa': usdt_tasa
        }
        
        # Verificar si ya existe un registro para esta fecha
        existing_response = supabase.table("stock_diario").select("fecha").eq("fecha", fecha).execute()
        
        if existing_response.data:
            # Actualizar registro existente
            response = supabase.table("stock_diario").update(stock_data).eq("fecha", fecha).execute()
            message = f"Sobrantes actualizados exitosamente para {fecha}"
        else:
            # Crear nuevo registro
            response = supabase.table("stock_diario").insert(stock_data).execute()
            message = f"Sobrantes guardados exitosamente para {fecha}"
        
        if response.data:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@margen_bp.route("/guardar_gastos", methods=["POST"])
def guardar_gastos():
    """Guarda los gastos, pago_movil y envios_al_detal para la fecha seleccionada en la tabla stock_diario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos'}), 400
        fecha = data.get('fecha')
        gastos = data.get('gastos')
        pago_movil = data.get('pago_movil')
        envios_al_detal = data.get('envios_al_detal')
        if not all([fecha, gastos is not None, pago_movil is not None, envios_al_detal is not None]):
            return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400
        try:
            gastos = float(gastos)
            pago_movil = float(pago_movil)
            envios_al_detal = float(envios_al_detal)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Los valores deben ser números válidos'}), 400
        # Preparar datos para insertar/actualizar
        gastos_data = {
            'fecha': fecha,
            'gastos': gastos,
            'pago_movil': pago_movil,
            'envios_al_detal': envios_al_detal
        }
        # Verificar si ya existe un registro para esta fecha
        existing_response = supabase.table("stock_diario").select("fecha").eq("fecha", fecha).execute()
        if existing_response.data:
            response = supabase.table("stock_diario").update(gastos_data).eq("fecha", fecha).execute()
            message = f"Gastos actualizados exitosamente para {fecha}"
        else:
            response = supabase.table("stock_diario").insert(gastos_data).execute()
            message = f"Gastos guardados exitosamente para {fecha}"
        if response.data:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@margen_bp.route("/", methods=["GET", "POST"])
def index():
    # Obtener fecha anterior (ayer)
    fecha = request.args.get("fecha")
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    fecha_ayer = (datetime.strptime(fecha, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Consultar gastos de la fecha seleccionada desde la base de datos
    row_gastos = supabase.table("stock_diario").select("gastos, pago_movil, envios_al_detal").eq("fecha", fecha).execute().data
    if row_gastos and row_gastos[0]:
        gastos = float(row_gastos[0].get('gastos', 15330))
        pago_movil = float(row_gastos[0].get('pago_movil', 7190))
        envios_al_detal = float(row_gastos[0].get('envios_al_detal', 170984))
    else:
        # Usar valores por defecto si no hay datos para esta fecha
        gastos = 15330
        pago_movil = 7190
        envios_al_detal = 170984
    
    # Consultar stock diario de ayer
    row = supabase.table("stock_diario").select("brs_stock, usdt_stock, tasa_ves_clp, usdt_tasa").eq("fecha", fecha_ayer).execute().data
    saldo_anterior = row[0] if row else None
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    # Consultar stock diario de hoy
    row_hoy = supabase.table("stock_diario").select("brs_stock").eq("fecha", fecha).execute().data
    brs_vendidos_hoy = row_hoy[0]["brs_stock"] if row_hoy else None
    
    # Sumar todos los BRS vendidos de la tabla pedidos para la fecha seleccionada
    pedidos = supabase.table("pedidos").select("brs, clp").eq("fecha", fecha).eq("eliminado", False).execute().data
    brs_vendidos_hoy = sum(float(p["brs"]) for p in pedidos) if pedidos else 0
    
    # Sumar todos los CLP recibidos de la tabla pedidos para la fecha seleccionada
    clp_recibidos = sum(float(p["clp"]) for p in pedidos) if pedidos else 0
    
    # Sumar todos los BRS comprados (VES recibidos por cambio de USDT) de la tabla compras para la fecha seleccionada
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
    brs_comprados = sum(float(c["totalprice"]) for c in compras_brs) if compras_brs else 0
    usdt_vendidos = sum(float(c["amount"]) + float(c.get("commission", 0)) for c in compras_brs) if compras_brs else 0
    
    # Sumar todos los USDT comprados (costo_real) de la tabla compras para la fecha seleccionada
    compras_usdt = supabase.table("compras").select("costo_real, totalprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
    usdt_comprados = sum(float(c["costo_real"]) for c in compras_usdt) if compras_usdt else 0
    clp_invertidos = sum(float(c["totalprice"]) for c in compras_usdt) if compras_usdt else 0
    
    # Sumar todos los USDT vendidos en CLP (amount) de la tabla compras para la fecha seleccionada
    ventas_usdt_clp = supabase.table("compras").select("amount, totalprice").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
    usdt_vendidos_clp = sum(float(c["amount"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
    clp_recibidos_usdt = sum(float(c["totalprice"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
    
    tasa_usdt_ves_actual = brs_comprados / usdt_vendidos if usdt_vendidos > 0 else 0
    tasa_usdt_clp_actual = clp_invertidos / usdt_comprados if usdt_comprados > 0 else 0
    total_brs = (float(saldo_anterior["brs_stock"]) if saldo_anterior and saldo_anterior.get("brs_stock") is not None else 0) + brs_comprados
    total_usdt = (float(saldo_anterior["usdt_stock"]) if saldo_anterior and saldo_anterior.get("usdt_stock") is not None else 0) + usdt_comprados - usdt_vendidos_clp
    
    clp_anterior = 0
    if saldo_anterior and saldo_anterior.get('usdt_stock') is not None and saldo_anterior.get('usdt_tasa') is not None:
        clp_anterior = float(saldo_anterior['usdt_stock']) * float(saldo_anterior['usdt_tasa'])
    
    total_clp = clp_anterior + clp_invertidos + clp_recibidos_usdt
    usdt_anterior = float(saldo_anterior["usdt_stock"]) if saldo_anterior and saldo_anterior.get("usdt_stock") is not None else 0
    tasa_usdt_clp_anterior = float(saldo_anterior["usdt_tasa"]) if saldo_anterior and saldo_anterior.get("usdt_tasa") is not None else 0
    tasa_usdt_clp_general = 0
    if total_usdt > 0:
        tasa_usdt_clp_general = (usdt_anterior * tasa_usdt_clp_anterior + usdt_comprados * tasa_usdt_clp_actual) / total_usdt
    clp_por_usdt_vendido = usdt_vendidos * tasa_usdt_clp_general
    tasa_ves_clp_actual = brs_comprados / clp_por_usdt_vendido if clp_por_usdt_vendido > 0 else 0
    
    brs_anterior = float(saldo_anterior["brs_stock"]) if saldo_anterior and saldo_anterior.get("brs_stock") is not None else 0
    tasa_ves_clp_anterior = float(saldo_anterior["tasa_ves_clp"]) if saldo_anterior and saldo_anterior.get("tasa_ves_clp") is not None else 0
    ponderado_ves_clp = 0
    if total_brs > 0:
        ponderado_ves_clp = (brs_anterior * tasa_ves_clp_anterior + brs_comprados * tasa_ves_clp_actual) / total_brs
    
    sobrante_usdt = total_usdt - usdt_vendidos
    sobrante_brs = total_brs - brs_vendidos_hoy
    
    # Calcular BRS vendidos al cliente DETAL
    pedidos_detal = supabase.table("pedidos").select("brs").eq("fecha", fecha).eq("eliminado", False).eq("cliente", "DETAL").execute().data
    brs_vendidos_detal = sum(float(p["brs"]) for p in pedidos_detal) if pedidos_detal else 0
    brs_vendidos_mayor = brs_vendidos_hoy - brs_vendidos_detal
    
    print(f"[DEBUG] total_brs={total_brs}, brs_vendidos_mayor={brs_vendidos_mayor}, gastos={gastos}, pago_movil={pago_movil}, envios_al_detal={envios_al_detal}")
    print(f"[DEBUG] usdt_vendidos_clp={usdt_vendidos_clp}, clp_recibidos_usdt={clp_recibidos_usdt}, total_usdt={total_usdt}, sobrante_usdt={sobrante_usdt}")
    sobrante_al_mayor = total_brs - brs_vendidos_mayor - gastos - pago_movil - envios_al_detal
    
    # CLP recibidos del cliente DETAL
    pedidos_detal_clp = supabase.table("pedidos").select("clp").eq("fecha", fecha).eq("eliminado", False).eq("cliente", "DETAL").execute().data
    clp_recibidos_detal = sum(float(p["clp"]) for p in pedidos_detal_clp) if pedidos_detal_clp else 0
    
    # CLP recibidos de todos menos DETAL
    pedidos_mayor_clp = supabase.table("pedidos").select("clp").eq("fecha", fecha).eq("eliminado", False).neq("cliente", "DETAL").execute().data
    clp_recibidos_mayor = sum(float(p["clp"]) for p in pedidos_mayor_clp) if pedidos_mayor_clp else 0
    
    if ponderado_ves_clp > 0:
        margen_mayor = clp_recibidos_mayor - (brs_vendidos_mayor / ponderado_ves_clp)
        margen_detal = clp_recibidos_detal - (brs_vendidos_detal / ponderado_ves_clp)
    else:
        margen_mayor = 0
        margen_detal = 0
    margen_total = margen_mayor + margen_detal
    
    return render_template("margen/saldo_anterior.html", saldo_anterior=saldo_anterior, fecha_ayer=fecha_ayer, fecha_hoy=fecha_hoy, brs_vendidos_hoy=brs_vendidos_hoy, clp_recibidos=clp_recibidos, brs_comprados=brs_comprados, usdt_vendidos=usdt_vendidos, usdt_comprados=usdt_comprados, usdt_vendidos_clp=usdt_vendidos_clp, clp_recibidos_usdt=clp_recibidos_usdt, clp_invertidos=clp_invertidos, tasa_usdt_clp_actual=tasa_usdt_clp_actual, tasa_usdt_ves_actual=tasa_usdt_ves_actual, total_brs=total_brs, total_usdt=total_usdt, clp_anterior=clp_anterior, total_clp=total_clp, clp_por_usdt_vendido=clp_por_usdt_vendido, tasa_ves_clp_actual=tasa_ves_clp_actual, ponderado_ves_clp=ponderado_ves_clp, tasa_usdt_clp_general=tasa_usdt_clp_general, gastos=gastos, pago_movil=pago_movil, sobrante_usdt=sobrante_usdt, sobrante_brs=sobrante_brs, brs_vendidos_detal=brs_vendidos_detal, brs_vendidos_mayor=brs_vendidos_mayor, sobrante_al_mayor=sobrante_al_mayor, envios_al_detal=envios_al_detal, clp_recibidos_mayor=clp_recibidos_mayor, clp_recibidos_detal=clp_recibidos_detal, margen_mayor=margen_mayor, margen_detal=margen_detal, margen_total=margen_total) 