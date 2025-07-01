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
    # Fecha actual en formato YYYY-MM-DD
    fecha = datetime.now().strftime('%Y-%m-%d')
    
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
        logging.error(f"Error al obtener saldo inicial: {e}")
        saldo_inicial = 215027  # Valor de respaldo
    
    # Consulta a la tabla compras para obtener el total de BRS cambiados por USDT (tradetype SELL, fiat VES)
    query = supabase.table("compras") \
        .select("totalprice") \
        .eq("fiat", "VES") \
        .eq("tradetype", "SELL") \
        .gte("createtime", fecha + "T00:00:00") \
        .lte("createtime", fecha + "T23:59:59")
    response = query.execute()
    total_ingresos = sum(item.get("totalprice", 0) for item in response.data) if response.data else 0
    formatted_ingresos = format(total_ingresos, ",.0f").replace(",", ".")
    
    # Consulta a la tabla pedidos para obtener el total de BRS del día
    query_pedidos = supabase.table("pedidos") \
        .select("brs") \
        .eq("fecha", fecha) \
        .eq("eliminado", False)
    response_pedidos = query_pedidos.execute()
    total_egresos_brs = sum(item.get("brs", 0) for item in response_pedidos.data) if response_pedidos.data else 0
    formatted_egresos = format(total_egresos_brs, ",.0f").replace(",", ".")
    
    # Formatear saldo inicial
    formatted_saldo_inicial = format(saldo_inicial, ",.0f").replace(",", ".")
    
    return render_template('cierre/index.html', active_page='cierre', 
                         ingresos=formatted_ingresos, egresos=formatted_egresos,
                         saldo_inicial=formatted_saldo_inicial)

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