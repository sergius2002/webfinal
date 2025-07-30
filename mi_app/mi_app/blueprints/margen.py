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
            # Actualizar automáticamente el flujo de capital para esta fecha
            try:
                calcular_flujo_capital_automatico(fecha)
            except Exception as e:
                print(f"Error al actualizar flujo de capital automáticamente: {e}")
            
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
        
        # Verificar si ya existe un registro para esta fecha
        existing_response = supabase.table("stock_diario").select("fecha").eq("fecha", fecha).execute()
        
        if existing_response.data:
            # Actualizar solo los campos de gastos en el registro existente
            gastos_data = {
                'gastos': gastos,
                'pago_movil': pago_movil,
                'envios_al_detal': envios_al_detal
            }
            response = supabase.table("stock_diario").update(gastos_data).eq("fecha", fecha).execute()
            message = f"Gastos actualizados exitosamente para {fecha}"
        else:
            # Crear un nuevo registro con valores por defecto para los campos NOT NULL
            # y los gastos proporcionados
            nuevo_registro = {
                'fecha': fecha,
                'brs_stock': 0.0,  # Valor por defecto
                'usdt_stock': 0.0,  # Valor por defecto
                'tasa_ves_clp': 0.0,  # Valor por defecto
                'usdt_tasa': 0.0,  # Valor por defecto
                'gastos': gastos,
                'pago_movil': pago_movil,
                'envios_al_detal': envios_al_detal
            }
            response = supabase.table("stock_diario").insert(nuevo_registro).execute()
            message = f"Gastos guardados exitosamente para {fecha}"
        
        if response.data:
            # Actualizar automáticamente el flujo de capital para esta fecha
            try:
                calcular_flujo_capital_automatico(fecha)
            except Exception as e:
                print(f"Error al actualizar flujo de capital automáticamente: {e}")
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@margen_bp.route("/flujo_capital")
def flujo_capital():
    """Página de flujo de capital con recálculo automático"""
    # Obtener parámetros de fecha
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    recalcular = request.args.get('recalcular', 'false').lower() == 'true'
    
    if not fecha_inicio:
        # Por defecto, mostrar último mes
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    # Obtener datos del flujo de capital (CONSULTA OPTIMIZADA)
    try:
        # Solo seleccionar las columnas necesarias para mejorar rendimiento
        # CORRECCIÓN: Usar operadores más específicos para el filtro de fechas
        flujo_data = supabase.table("flujo_capital").select(
            "fecha, capital_inicial, ganancias, costo_gastos, gastos_manuales, capital_final"
        ).gte("fecha", fecha_inicio).lte("fecha", fecha_fin).order("fecha").execute().data
        
        # FILTRO ADICIONAL: Verificar que las fechas estén realmente en el rango
        flujo_data_filtrado = []
        for item in flujo_data:
            if fecha_inicio <= item['fecha'] <= fecha_fin:
                flujo_data_filtrado.append(item)
        
        flujo_data = flujo_data_filtrado
        
        # Si se solicita recálculo o hay datos desactualizados, recalcular automáticamente
        if recalcular or verificar_datos_desactualizados(flujo_data, fecha_inicio, fecha_fin):
            print("🔄 Recalculando flujo de capital automáticamente...")
            for item in flujo_data:
                try:
                    calcular_flujo_capital_automatico(item['fecha'])
                except Exception as e:
                    print(f"Error al recalcular {item['fecha']}: {e}")
            
            # Obtener datos actualizados (CONSULTA OPTIMIZADA)
            flujo_data = supabase.table("flujo_capital").select(
                "fecha, capital_inicial, ganancias, costo_gastos, gastos_manuales, capital_final"
            ).gte("fecha", fecha_inicio).lte("fecha", fecha_fin).order("fecha").execute().data
        
        # Calcular métricas
        total_entradas = sum(float(item.get('ganancias', 0)) for item in flujo_data)
        total_salidas = sum(float(item.get('costo_gastos', 0)) + float(item.get('gastos_manuales', 0)) for item in flujo_data)
        flujo_neto = total_entradas - total_salidas
        
        # Obtener capital inicial y final
        capital_inicial = flujo_data[0].get('capital_inicial', 0) if flujo_data else 0
        capital_final = flujo_data[-1].get('capital_final', 0) if flujo_data else 0
        
        # Calcular ROI
        roi = ((capital_final - capital_inicial) / capital_inicial * 100) if capital_inicial > 0 else 0
        
    except Exception as e:
        print(f"Error al obtener datos de flujo de capital: {e}")
        flujo_data = []
        total_entradas = 0
        total_salidas = 0
        flujo_neto = 0
        capital_inicial = 0
        capital_final = 0
        roi = 0
    
    return render_template("margen/flujo_capital.html", 
                         flujo_data=flujo_data,
                         total_entradas=total_entradas,
                         total_salidas=total_salidas,
                         flujo_neto=flujo_neto,
                         capital_inicial=capital_inicial,
                         capital_final=capital_final,
                         roi=roi,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

@margen_bp.route("/transacciones_detalladas")
def transacciones_detalladas():
    """Página de transacciones detalladas del flujo de capital"""
    # Obtener parámetros de fecha
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    if not fecha_inicio:
        # Por defecto, mostrar último mes
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    # Obtener transacciones del período
    try:
        transacciones_data = supabase.table("transacciones_flujo").select("*").gte("fecha", fecha_inicio).lte("fecha", fecha_fin).order("fecha, created_at").execute().data
        
        # Calcular métricas
        total_entradas = sum(float(item.get('monto', 0)) for item in transacciones_data if item.get('tipo') == 'ENTRADA')
        total_salidas = sum(float(item.get('monto', 0)) for item in transacciones_data if item.get('tipo') == 'SALIDA')
        flujo_neto = total_entradas - total_salidas
        
        # Obtener capital final
        capital_final = transacciones_data[-1].get('capital_posterior', 0) if transacciones_data else 0
        
    except Exception as e:
        print(f"Error al obtener transacciones: {e}")
        transacciones_data = []
        total_entradas = 0
        total_salidas = 0
        flujo_neto = 0
        capital_final = 0
    
    return render_template("margen/transacciones_detalladas.html", 
                         transacciones_data=transacciones_data,
                         total_entradas=total_entradas,
                         total_salidas=total_salidas,
                         flujo_neto=flujo_neto,
                         capital_final=capital_final,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

@margen_bp.route("/api/transaccion_flujo", methods=["POST"])
def agregar_transaccion():
    """API para agregar una transacción individual al flujo de capital"""
    try:
        data = request.get_json()
        fecha = data.get('fecha')
        tipo = data.get('tipo')  # 'ENTRADA' o 'SALIDA'
        monto = data.get('monto')
        categoria = data.get('categoria', 'OTROS')
        
        if not all([fecha, tipo, monto]):
            return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400
        
        if tipo not in ['ENTRADA', 'SALIDA']:
            return jsonify({'success': False, 'message': 'Tipo debe ser ENTRADA o SALIDA'}), 400
        
        try:
            monto = float(monto)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'El monto debe ser un número válido'}), 400
        
        if monto <= 0:
            return jsonify({'success': False, 'message': 'El monto debe ser mayor a 0'}), 400
        
        # Agregar transacción
        if agregar_transaccion_flujo(fecha, tipo, monto, categoria):
            return jsonify({'success': True, 'message': f'Transacción {tipo.lower()} agregada exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'Error al agregar transacción'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@margen_bp.route("/api/flujo_capital", methods=["POST"])
def actualizar_flujo_capital():
    """API para actualizar el flujo de capital de un día específico"""
    try:
        data = request.get_json()
        fecha = data.get('fecha')
        gastos_manuales = data.get('gastos_manuales', 0)
        
        if not fecha:
            return jsonify({'success': False, 'message': 'Fecha es requerida'}), 400
        
        # Obtener capital inicial (capital final del día anterior)
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        
        capital_anterior = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
        capital_inicial = float(capital_anterior[0]['capital_final']) if capital_anterior else 32000000
        
        # Obtener datos completos de márgenes para esta fecha
        # Usar la misma lógica que en la función index() del módulo de márgenes
        row_gastos = supabase.table("stock_diario").select("gastos, pago_movil, envios_al_detal").eq("fecha", fecha).execute().data
        if row_gastos and row_gastos[0]:
            gastos = float(row_gastos[0].get('gastos', 15330))
            pago_movil = float(row_gastos[0].get('pago_movil', 7190))
            envios_al_detal = float(row_gastos[0].get('envios_al_detal', 170984))
        else:
            gastos = 15330
            pago_movil = 7190
            envios_al_detal = 170984
        
        # Obtener saldo anterior
        row = supabase.table("stock_diario").select("brs_stock, usdt_stock, tasa_ves_clp, usdt_tasa").eq("fecha", fecha_ayer).execute().data
        saldo_anterior = row[0] if row else None
        
        # Calcular ponderado VES/CLP usando la lógica completa de márgenes
        # Sumar todos los BRS vendidos de la tabla pedidos para la fecha seleccionada
        pedidos = supabase.table("pedidos").select("brs, clp").eq("fecha", fecha).eq("eliminado", False).execute().data
        brs_vendidos_hoy = sum(float(p["brs"]) for p in pedidos) if pedidos else 0
        
        # Sumar todos los BRS comprados (VES recibidos por cambio de USDT) de la tabla compras
        inicio = fecha + "T00:00:00"
        fin = fecha + "T23:59:59"
        compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        brs_comprados = sum(float(c["totalprice"]) for c in compras_brs) if compras_brs else 0
        usdt_vendidos = sum(float(c["amount"]) + float(c.get("commission", 0)) for c in compras_brs) if compras_brs else 0
        
        # Sumar todos los USDT comprados (costo_real) de la tabla compras
        compras_usdt = supabase.table("compras").select("costo_real, totalprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_comprados = sum(float(c["costo_real"]) for c in compras_usdt) if compras_usdt else 0
        clp_invertidos = sum(float(c["totalprice"]) for c in compras_usdt) if compras_usdt else 0
        
        # Sumar todos los USDT vendidos en CLP (amount) de la tabla compras
        ventas_usdt_clp = supabase.table("compras").select("amount, totalprice").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_vendidos_clp = sum(float(c["amount"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
        clp_recibidos_usdt = sum(float(c["totalprice"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
        
        # Calcular tasas
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
        
        # Calcular BRS vendidos al cliente DETAL
        pedidos_detal = supabase.table("pedidos").select("brs").eq("fecha", fecha).eq("eliminado", False).eq("cliente", "DETAL").execute().data
        brs_vendidos_detal = sum(float(p["brs"]) for p in pedidos_detal) if pedidos_detal else 0
        brs_vendidos_mayor = brs_vendidos_hoy - brs_vendidos_detal
        
        # CLP recibidos del cliente DETAL
        pedidos_detal_clp = supabase.table("pedidos").select("clp").eq("fecha", fecha).eq("eliminado", False).eq("cliente", "DETAL").execute().data
        clp_recibidos_detal = sum(float(p["clp"]) for p in pedidos_detal_clp) if pedidos_detal_clp else 0
        
        # CLP recibidos de todos menos DETAL
        pedidos_mayor_clp = supabase.table("pedidos").select("clp").eq("fecha", fecha).eq("eliminado", False).neq("cliente", "DETAL").execute().data
        clp_recibidos_mayor = sum(float(p["clp"]) for p in pedidos_mayor_clp) if pedidos_mayor_clp else 0
        
        # Calcular márgenes
        if ponderado_ves_clp > 0:
            margen_mayor = clp_recibidos_mayor - (brs_vendidos_mayor / ponderado_ves_clp)
            margen_detal = clp_recibidos_detal - (brs_vendidos_detal / ponderado_ves_clp)
            costo_pago_movil = pago_movil / ponderado_ves_clp
            costo_gastos = gastos / ponderado_ves_clp
        else:
            margen_mayor = 0
            margen_detal = 0
            costo_pago_movil = 0
            costo_gastos = 0
        
        margen_total = margen_mayor + margen_detal
        margen_neto = margen_total - costo_pago_movil
        
        # Calcular ganancias (margen neto)
        ganancias = margen_neto
        
        # Calcular capital final
        capital_final = capital_inicial + ganancias - costo_gastos - gastos_manuales
        
        # Preparar datos para insertar/actualizar
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': ganancias,
            'costo_gastos': costo_gastos,
            'gastos_manuales': gastos_manuales,
            'capital_final': capital_final,
            'margen_neto': margen_neto,
            'ponderado_ves_clp': ponderado_ves_clp,
            'gastos_brs': gastos,
            'pago_movil_brs': pago_movil,
            'envios_al_detal_brs': envios_al_detal
        }
        
        # Verificar si ya existe un registro para esta fecha
        existing = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha).execute().data
        
        if existing:
            # Actualizar registro existente
            response = supabase.table("flujo_capital").update(flujo_data).eq("fecha", fecha).execute()
            message = f"Flujo de capital actualizado para {fecha}"
        else:
            # Crear nuevo registro
            response = supabase.table("flujo_capital").insert(flujo_data).execute()
            message = f"Flujo de capital creado para {fecha}"
        
        if response.data:
            return jsonify({'success': True, 'message': message, 'data': flujo_data})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

@margen_bp.route("/api/sincronizar_flujo_capital", methods=["POST"])
def sincronizar_flujo_capital():
    """API para sincronizar manualmente el flujo de capital desde las transacciones"""
    try:
        data = request.get_json()
        fecha = data.get('fecha')
        
        if not fecha:
            return jsonify({'success': False, 'message': 'Fecha es requerida'}), 400
        
        # Sincronizar flujo de capital
        if sincronizar_flujo_capital_desde_transacciones(fecha):
            return jsonify({'success': True, 'message': f'Flujo de capital sincronizado exitosamente para {fecha}'})
        else:
            return jsonify({'success': False, 'message': 'Error al sincronizar flujo de capital'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

def verificar_datos_desactualizados(flujo_data, fecha_inicio, fecha_fin):
    """Verifica si los datos del flujo de capital están desactualizados"""
    try:
        if not flujo_data:
            return True
        
        # Verificar si hay pedidos recientes que no están reflejados
        for item in flujo_data:
            fecha = item['fecha']
            
            # Obtener última actualización del flujo
            ultima_actualizacion_flujo = item.get('updated_at')
            
            # Obtener último pedido de esa fecha (usando fecha en lugar de created_at)
            ultimo_pedido = supabase.table("pedidos").select("fecha").eq("fecha", fecha).eq("eliminado", False).order("fecha", desc=True).limit(1).execute().data
            
            if ultimo_pedido and ultima_actualizacion_flujo:
                ultima_actualizacion_flujo = datetime.fromisoformat(ultima_actualizacion_flujo.replace('Z', '+00:00'))
                ultimo_pedido_time = datetime.strptime(ultimo_pedido[0]['fecha'], '%Y-%m-%d')
                
                # Si hay pedidos más recientes que la última actualización del flujo
                if ultimo_pedido_time > ultima_actualizacion_flujo:
                    print(f"⚠️ Datos desactualizados para {fecha}: pedidos más recientes que el flujo")
                    return True
        
        return False
        
    except Exception as e:
        print(f"Error al verificar datos desactualizados: {e}")
        return True

def calcular_flujo_capital_automatico(fecha):
    """Calcula automáticamente el flujo de capital para una fecha específica (OPTIMIZADO)"""
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # CONSULTAS OPTIMIZADAS - Proyecciones específicas
        # 1. Capital anterior - solo la columna necesaria
        capital_anterior = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
        capital_inicial = float(capital_anterior[0]['capital_final']) if capital_anterior else 32000000
        
        # 2. Stock diario - una sola consulta con todas las columnas necesarias
        stock_data = supabase.table("stock_diario").select(
            "gastos, pago_movil, envios_al_detal, brs_stock, usdt_stock, tasa_ves_clp, usdt_tasa"
        ).eq("fecha", fecha).execute().data
        
        if stock_data and stock_data[0]:
            gastos = float(stock_data[0].get('gastos', 15330))
            pago_movil = float(stock_data[0].get('pago_movil', 7190))
            envios_al_detal = float(stock_data[0].get('envios_al_detal', 170984))
            saldo_anterior = stock_data[0]
        else:
            gastos = 15330
            pago_movil = 7190
            envios_al_detal = 170984
            saldo_anterior = None
        
        # 3. Pedidos - filtros optimizados con solo las columnas necesarias
        pedidos = supabase.table("pedidos").select("brs, clp, cliente").eq("fecha", fecha).eq("eliminado", False).execute().data
        brs_vendidos_hoy = sum(float(p["brs"]) for p in pedidos) if pedidos else 0
        
        # 4. Compras - consultas específicas con rangos de fecha optimizados
        inicio = fecha + "T00:00:00"
        fin = fecha + "T23:59:59"
        
        # Compras BRS (VES recibidos por cambio de USDT)
        compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        brs_comprados = sum(float(c["totalprice"]) for c in compras_brs) if compras_brs else 0
        usdt_vendidos = sum(float(c["amount"]) + float(c.get("commission", 0)) for c in compras_brs) if compras_brs else 0
        
        # Compras USDT (costo_real)
        compras_usdt = supabase.table("compras").select("costo_real, totalprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_comprados = sum(float(c["costo_real"]) for c in compras_usdt) if compras_usdt else 0
        clp_invertidos = sum(float(c["totalprice"]) for c in compras_usdt) if compras_usdt else 0
        
        # Ventas USDT en CLP
        ventas_usdt_clp = supabase.table("compras").select("amount, totalprice").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        usdt_vendidos_clp = sum(float(c["amount"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
        clp_recibidos_usdt = sum(float(c["totalprice"]) for c in ventas_usdt_clp) if ventas_usdt_clp else 0
        
        # Calcular tasas
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
        
        # OPTIMIZACIÓN: Usar los datos de pedidos ya obtenidos en lugar de hacer consultas adicionales
        # Calcular BRS vendidos al cliente DETAL
        brs_vendidos_detal = sum(float(p["brs"]) for p in pedidos if p.get("cliente") == "DETAL") if pedidos else 0
        brs_vendidos_mayor = brs_vendidos_hoy - brs_vendidos_detal
        
        # CLP recibidos del cliente DETAL
        clp_recibidos_detal = sum(float(p["clp"]) for p in pedidos if p.get("cliente") == "DETAL") if pedidos else 0
        
        # CLP recibidos de todos menos DETAL
        clp_recibidos_mayor = sum(float(p["clp"]) for p in pedidos if p.get("cliente") != "DETAL") if pedidos else 0
        
        # Calcular márgenes
        if ponderado_ves_clp > 0:
            margen_mayor = clp_recibidos_mayor - (brs_vendidos_mayor / ponderado_ves_clp)
            margen_detal = clp_recibidos_detal - (brs_vendidos_detal / ponderado_ves_clp)
            costo_pago_movil = pago_movil / ponderado_ves_clp
            costo_gastos = gastos / ponderado_ves_clp
        else:
            margen_mayor = 0
            margen_detal = 0
            costo_pago_movil = 0
            costo_gastos = 0
        
        margen_total = margen_mayor + margen_detal
        margen_neto = margen_total - costo_pago_movil
        
        # Obtener gastos manuales si existen
        flujo_existente = supabase.table("flujo_capital").select("gastos_manuales").eq("fecha", fecha).execute().data
        gastos_manuales = float(flujo_existente[0]['gastos_manuales']) if flujo_existente else 0
        
        # Calcular ganancias (margen neto)
        ganancias = margen_neto
        
        # Calcular capital final
        capital_final = capital_inicial + ganancias - costo_gastos - gastos_manuales
        
        # Preparar datos para insertar/actualizar
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': ganancias,
            'costo_gastos': costo_gastos,
            'gastos_manuales': gastos_manuales,
            'capital_final': capital_final,
            'margen_neto': margen_neto,
            'ponderado_ves_clp': ponderado_ves_clp,
            'gastos_brs': gastos,
            'pago_movil_brs': pago_movil,
            'envios_al_detal_brs': envios_al_detal
        }
        
        # Verificar si ya existe un registro para esta fecha
        existing = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha).execute().data
        
        if existing:
            # Actualizar registro existente
            response = supabase.table("flujo_capital").update(flujo_data).eq("fecha", fecha).execute()
        else:
            # Crear nuevo registro
            response = supabase.table("flujo_capital").insert(flujo_data).execute()
        
        return response.data if response.data else None
        
    except Exception as e:
        print(f"Error al calcular flujo de capital automático: {e}")
        return None

def sincronizar_flujo_capital_desde_transacciones(fecha):
    """Sincroniza el flujo de capital basado en las transacciones de una fecha específica"""
    try:
        # Obtener todas las transacciones de la fecha
        transacciones = supabase.table("transacciones_flujo").select("*").eq("fecha", fecha).order("created_at").execute().data
        
        if not transacciones:
            print(f"ℹ️ No hay transacciones para sincronizar en {fecha}")
            return True
        
        # Calcular totales
        total_entradas = sum(float(t['monto']) for t in transacciones if t['tipo'] == 'ENTRADA')
        total_salidas = sum(float(t['monto']) for t in transacciones if t['tipo'] == 'SALIDA')
        
        # Obtener capital inicial (del día anterior)
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        capital_ayer = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
        capital_inicial = float(capital_ayer[0]['capital_final']) if capital_ayer else 32000000
        
        # Calcular capital final
        capital_final = capital_inicial + total_entradas - total_salidas
        
        # Categorizar gastos
        gastos_venezuela = sum(float(t['monto']) for t in transacciones 
                              if t['tipo'] == 'SALIDA' and t['categoria'] == 'GASTOS_VENEZUELA')
        gastos_chile = sum(float(t['monto']) for t in transacciones 
                          if t['tipo'] == 'SALIDA' and t['categoria'] == 'GASTOS_CHILE')
        
        # Actualizar o crear registro en flujo_capital
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': total_entradas,
            'costo_gastos': gastos_venezuela,
            'gastos_manuales': gastos_chile,
            'capital_final': capital_final
        }
        
        # Verificar si ya existe un registro para esta fecha
        existing = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha).execute().data
        
        if existing:
            # Actualizar registro existente
            response = supabase.table("flujo_capital").update(flujo_data).eq("fecha", fecha).execute()
        else:
            # Crear nuevo registro
            response = supabase.table("flujo_capital").insert(flujo_data).execute()
        
        print(f"✅ Flujo de capital sincronizado para {fecha}: Capital final = ${capital_final:,.0f}")
        return True
        
    except Exception as e:
        print(f"❌ Error al sincronizar flujo de capital: {e}")
        return False

def obtener_transacciones_dia(fecha):
    """Obtiene todas las transacciones de un día específico"""
    try:
        transacciones = supabase.table("transacciones_flujo").select("*").eq("fecha", fecha).order("created_at").execute().data
        return transacciones
    except Exception as e:
        print(f"❌ Error al obtener transacciones: {e}")
        return []

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
        # Calcular costo pago móvil
        costo_pago_movil = pago_movil / ponderado_ves_clp
        # Calcular costo gastos
        costo_gastos = gastos / ponderado_ves_clp
    else:
        margen_mayor = 0
        margen_detal = 0
        costo_pago_movil = 0
        costo_gastos = 0
    margen_total = margen_mayor + margen_detal
    # Margen neto después de restar el costo pago móvil
    margen_neto = margen_total - costo_pago_movil
    
    return render_template("margen/saldo_anterior.html", saldo_anterior=saldo_anterior, fecha_ayer=fecha_ayer, fecha_hoy=fecha_hoy, brs_vendidos_hoy=brs_vendidos_hoy, clp_recibidos=clp_recibidos, brs_comprados=brs_comprados, usdt_vendidos=usdt_vendidos, usdt_comprados=usdt_comprados, usdt_vendidos_clp=usdt_vendidos_clp, clp_recibidos_usdt=clp_recibidos_usdt, clp_invertidos=clp_invertidos, tasa_usdt_clp_actual=tasa_usdt_clp_actual, tasa_usdt_ves_actual=tasa_usdt_ves_actual, total_brs=total_brs, total_usdt=total_usdt, clp_anterior=clp_anterior, total_clp=total_clp, clp_por_usdt_vendido=clp_por_usdt_vendido, tasa_ves_clp_actual=tasa_ves_clp_actual, ponderado_ves_clp=ponderado_ves_clp, tasa_usdt_clp_general=tasa_usdt_clp_general, gastos=gastos, pago_movil=pago_movil, sobrante_usdt=sobrante_usdt, sobrante_brs=sobrante_brs, brs_vendidos_detal=brs_vendidos_detal, brs_vendidos_mayor=brs_vendidos_mayor, sobrante_al_mayor=sobrante_al_mayor, envios_al_detal=envios_al_detal, clp_recibidos_mayor=clp_recibidos_mayor, clp_recibidos_detal=clp_recibidos_detal, margen_mayor=margen_mayor, margen_detal=margen_detal, margen_total=margen_total, costo_pago_movil=costo_pago_movil, costo_gastos=costo_gastos, margen_neto=margen_neto) 

def agregar_transaccion_flujo(fecha, tipo, monto, categoria):
    """Agrega una transacción individual al flujo de capital"""
    try:
        # Obtener el capital actual para esa fecha
        capital_actual = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha).execute().data
        
        if capital_actual:
            capital_anterior = float(capital_actual[0]['capital_final'])
        else:
            # Si no existe, usar el capital del día anterior o 32M por defecto
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            capital_ayer = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
            capital_anterior = float(capital_ayer[0]['capital_final']) if capital_ayer else 32000000
        
        # Calcular capital posterior
        if tipo == 'ENTRADA':
            capital_posterior = capital_anterior + monto
        else:  # SALIDA
            capital_posterior = capital_anterior - monto
        
        # Insertar transacción
        transaccion_data = {
            'fecha': fecha,
            'tipo': tipo,
            'monto': monto,
            'categoria': categoria,
            'capital_anterior': capital_anterior,
            'capital_posterior': capital_posterior
        }
        
        response = supabase.table("transacciones_flujo").insert(transaccion_data).execute()
        
        if response.data:
            # Actualizar el capital final en flujo_capital
            supabase.table("flujo_capital").update({
                'capital_final': capital_posterior
            }).eq("fecha", fecha).execute()
            
            # Sincronizar flujo de capital basado en transacciones
            sincronizar_flujo_capital_desde_transacciones(fecha)
            
            print(f"✅ Transacción agregada: {tipo} ${monto:,.0f} - {categoria}")
            return True
        else:
            print(f"❌ Error al agregar transacción")
            return False
            
    except Exception as e:
        print(f"❌ Error al agregar transacción: {e}")
        return False 