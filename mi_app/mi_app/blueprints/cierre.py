from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask import session, redirect, url_for, flash
from mi_app.mi_app.blueprints.admin import login_required
from mi_app.mi_app.extensions import supabase
import json
import logging

cierre_bp = Blueprint('cierre', __name__)

@cierre_bp.route('/')
@login_required
def index():
    # Obtener fecha desde query param o usar hoy
    fecha_param = request.args.get('fecha')
    try:
        if fecha_param:
            fecha_dt = datetime.strptime(fecha_param, '%Y-%m-%d')
            fecha = fecha_dt.strftime('%Y-%m-%d')
        else:
            fecha_dt = datetime.now()
            fecha = fecha_dt.strftime('%Y-%m-%d')
    except ValueError:
        # Formato inválido -> usar hoy
        fecha_dt = datetime.now()
        fecha = fecha_dt.strftime('%Y-%m-%d')

    # Formato para mostrar en el header (DD-MMM)
    fecha_mostrar = fecha_dt.strftime('%d-%b').lower()
    
    # Obtener saldo inicial (cierre final del día anterior a la fecha seleccionada)
    fecha_ayer_dt = fecha_dt - timedelta(days=1)
    fecha_ayer = fecha_ayer_dt.strftime('%Y-%m-%d')
    saldo_inicial = 0
    try:
        response_ayer = supabase.table("cierre_caja").select("cierre_final").eq("fecha", fecha_ayer).execute()
        if response_ayer.data:
            saldo_inicial = float(response_ayer.data[0].get("cierre_final", 0))
        else:
            saldo_inicial = 215027
    except Exception as e:
        logging.error("Error al obtener saldo inicial: %s", e)
        saldo_inicial = 215027
    
    # Consulta ingresos (compras)
    try:
        resp_ing = supabase.table("compras") \
            .select("totalprice") \
            .eq("fiat", "VES") \
            .eq("tradetype", "SELL") \
            .gte("createtime", f"{fecha}T00:00:00") \
            .lte("createtime", f"{fecha}T23:59:59") \
            .execute()
        total_ingresos = sum(item.get("totalprice", 0) for item in resp_ing.data) if resp_ing.data else 0
    except Exception as e:
        logging.error("Error al obtener ingresos: %s", e)
        total_ingresos = 0
    formatted_ingresos = format(total_ingresos, ",.0f").replace(",", ".")
    
    # Consulta egresos (pedidos)
    try:
        resp_ped = supabase.table("pedidos").select("brs").eq("fecha", fecha).eq("eliminado", False).execute()
        total_egresos_brs = sum(item.get("brs", 0) for item in resp_ped.data) if resp_ped.data else 0
    except Exception as e:
        logging.error("Error al obtener egresos: %s", e)
        total_egresos_brs = 0
    formatted_egresos = format(total_egresos_brs, ",.0f").replace(",", ".")
    formatted_saldo_inicial = format(saldo_inicial, ",.0f").replace(",", ".")

    return render_template('cierre/index.html', active_page='cierre',
                           ingresos=formatted_ingresos, egresos=formatted_egresos,
                           saldo_inicial=formatted_saldo_inicial, fecha_iso=fecha,
                           fecha_mostrar=fecha_mostrar)

@cierre_bp.route('/guardar', methods=['POST'])
@login_required
def guardar_cierre():
    """Guarda o actualiza el cierre de caja del día"""
    try:
        # Obtener datos del formulario
        data = request.get_json()
        fecha = datetime.now().strftime('%Y-%m-%d')
        usuario_email = session.get('email', 'usuario_desconocido')
        
        # Validar datos requeridos
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos'}), 400
        
        # Obtener saldo inicial (cierre final del día anterior)
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        saldo_inicial = 0
        
        try:
            # Buscar el cierre del día anterior
            response_ayer = supabase.table("cierre_caja") \
                .select("cierre_final") \
                .eq("fecha", fecha_ayer) \
                .execute()
            
            if response_ayer.data:
                saldo_inicial = float(response_ayer.data[0].get("cierre_final", 0))
            else:
                # Si no hay cierre del día anterior, usar valor por defecto
                saldo_inicial = 215027  # Valor inicial proporcionado
                
        except Exception as e:
            logging.error(f"Error al obtener saldo inicial en guardar: {e}")
            saldo_inicial = 215027  # Valor de respaldo
            
        # Extraer valores del frontend
        ingresos_binance = float(data.get('ingresos_binance', 0))
        ingresos_extra = float(data.get('ingresos_extra', 0))
        total_ingresos = float(data.get('total_ingresos', 0))
        egresos_pedidos = float(data.get('egresos_pedidos', 0))
        egresos_detal = float(data.get('egresos_detal', 0))
        gastos = float(data.get('gastos', 0))
        pago_movil = float(data.get('pago_movil', 0))
        cierre_detal = float(data.get('cierre_detal', 0))
        saldo_bancos = float(data.get('saldo_bancos', 0))
        total_egresos = float(data.get('total_egresos', 0))
        cierre_mayor = float(data.get('cierre_mayor', 0))
        cierre_final = float(data.get('cierre_final', 0))
        diferencia = float(data.get('diferencia', 0))
        ingresos_extra_detalle = data.get('ingresos_extra_detalle', [])
        
        # Preparar datos para insertar/actualizar
        cierre_data = {
            'fecha': fecha,
            'saldo_inicial': saldo_inicial,
            'ingresos_binance': ingresos_binance,
            'ingresos_extra': ingresos_extra,
            'total_ingresos': total_ingresos,
            'egresos_pedidos': egresos_pedidos,
            'egresos_detal': egresos_detal,
            'gastos': gastos,
            'pago_movil': pago_movil,
            'cierre_detal': cierre_detal,
            'saldo_bancos': saldo_bancos,
            'total_egresos': total_egresos,
            'cierre_mayor': cierre_mayor,
            'cierre_final': cierre_final,
            'diferencia': diferencia,
            'ingresos_extra_detalle': json.dumps(ingresos_extra_detalle),
            'usuario_modificacion': usuario_email
        }
        
        # Verificar si ya existe un cierre para esta fecha
        existing_response = supabase.table("cierre_caja").select("id").eq("fecha", fecha).execute()
        
        if existing_response.data:
            # Actualizar registro existente
            cierre_id = existing_response.data[0]['id']
            response = supabase.table("cierre_caja").update(cierre_data).eq("id", cierre_id).execute()
            message = "Cierre actualizado exitosamente"
        else:
            # Crear nuevo registro
            cierre_data['usuario_creacion'] = usuario_email
            response = supabase.table("cierre_caja").insert(cierre_data).execute()
            message = "Cierre guardado exitosamente"
        
        if response.data:
            logging.info(f"Cierre guardado para fecha {fecha} por usuario {usuario_email}")
            return jsonify({'success': True, 'message': message})
        else:
            logging.error(f"Error al guardar cierre: {response}")
            return jsonify({'success': False, 'message': 'Error al guardar en la base de datos'}), 500
            
    except ValueError as e:
        logging.error(f"Error de validación en guardar_cierre: {e}")
        return jsonify({'success': False, 'message': 'Error en los datos enviados'}), 400
    except Exception as e:
        logging.error(f"Error inesperado en guardar_cierre: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@cierre_bp.route('/historial')
@login_required
def historial():
    """Muestra el historial de cambios de cierres (últimos 30 días)"""
    try:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        historial = []
        try:
            # Primero intentar la vista (si existe)
            response = supabase.table("vista_historial_cierre") \
                .select("*") \
                .gte("created_at", fecha_inicio) \
                .order("created_at", desc=True) \
                .limit(100) \
                .execute()
            historial = response.data if response.data else []
        except Exception as e:
            logging.warning("vista_historial_cierre no disponible, usando cierre_caja_historial: %s", e)
            # Fallback a la tabla historial si la vista aún no existe
            response = supabase.table("cierre_caja_historial") \
                .select("*") \
                .gte("created_at", fecha_inicio) \
                .order("created_at", desc=True) \
                .limit(100) \
                .execute()
            historial = response.data if response.data else []
            # Formatear valores numéricos si es posible
            for item in historial:
                for campo in ["valor_anterior", "valor_nuevo"]:
                    val = item.get(campo)
                    if val is not None:
                        try:
                            num = float(val)
                            item[f"{campo}_formateado"] = "{:,}".format(int(num)).replace(",", ".")
                        except ValueError:
                            # No era numérico
                            item[f"{campo}_formateado"] = val
        
        # Lista auxiliar para los usuarios ya renderizados en el select
        usuarios_vistos = []
        
        return render_template('cierre/historial.html', 
                             active_page='cierre',
                             historial=historial,
                             datetime=datetime,
                             timedelta=timedelta,
                             usuarios_vistos=usuarios_vistos)
        
    except Exception as e:
        logging.error(f"Error al obtener historial: {e}")
        flash("Error al cargar el historial de cambios")
        return redirect(url_for('cierre.index'))

@cierre_bp.route('/historial/<fecha>')
@login_required
def historial_fecha(fecha):
    """Obtiene el historial de una fecha específica"""
    try:
        # Validar formato de fecha
        datetime.strptime(fecha, '%Y-%m-%d')
        
        # Obtener historial de la fecha específica
        response = supabase.rpc('obtener_historial_cierre', {'fecha_consulta': fecha}).execute()
        
        historial = response.data if response.data else []
        
        return jsonify({
            'success': True,
            'fecha': fecha,
            'historial': historial
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de fecha inválido'}), 400
    except Exception as e:
        logging.error(f"Error al obtener historial de fecha {fecha}: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener historial'}), 500 