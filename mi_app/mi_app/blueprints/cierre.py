from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask import session, redirect, url_for, flash
from mi_app.mi_app.blueprints.admin import login_required
from mi_app.mi_app.extensions import supabase
import json
import logging

def obtener_configuracion_inicial():
    """Obtiene la configuración inicial del sistema"""
    try:
        config_response = supabase.table("configuracion_sistema").select("*").eq("clave", "inicio_operaciones").execute()
        
        if config_response.data:
            config = config_response.data[0]
            try:
                valores = json.loads(config.get('valor', '{}'))
                if valores.get('configurado', False):
                    return {
                        'fecha_inicio': valores.get('fecha_inicio'),
                        'saldo_inicial': float(valores.get('saldo_inicial', 0)),
                        'configurado': True
                    }
            except Exception as e:
                logging.error(f"Error al parsear configuración inicial: {e}")
        
        # Si no hay configuración o hay error, devolver valores por defecto
        return {
            'fecha_inicio': None,
            'saldo_inicial': 248957,  # Valor por defecto legacy
            'configurado': False
        }
    except Exception as e:
        logging.error(f"Error al obtener configuración inicial: {e}")
        return {
            'fecha_inicio': None,
            'saldo_inicial': 248957,
            'configurado': False
        }

def obtener_saldo_inicial_inteligente(fecha_consulta):
    """
    Obtiene el saldo inicial de manera inteligente:
    1. Si es el primer día configurado, usa el saldo inicial configurado
    2. Si hay cierre del día anterior, usa su cierre_final
    3. Si no hay configuración, usa valor por defecto legacy
    """
    config = obtener_configuracion_inicial()
    
    # Convertir fecha_consulta a datetime para comparaciones
    try:
        fecha_consulta_dt = datetime.strptime(fecha_consulta, '%Y-%m-%d')
    except ValueError:
        logging.error(f"Formato de fecha inválido: {fecha_consulta}")
        return config['saldo_inicial']
    
    # Si está configurado y es el primer día, usar saldo inicial configurado
    if config['configurado'] and config['fecha_inicio']:
        try:
            fecha_inicio_dt = datetime.strptime(config['fecha_inicio'], '%Y-%m-%d')
            if fecha_consulta_dt == fecha_inicio_dt:
                logging.info(f"Usando saldo inicial configurado para el primer día: {config['saldo_inicial']}")
                return config['saldo_inicial']
        except ValueError:
            logging.error(f"Formato de fecha de inicio inválido: {config['fecha_inicio']}")
    
    # Para cualquier otro día, buscar cierre del día anterior
    fecha_ayer_dt = fecha_consulta_dt - timedelta(days=1)
    fecha_ayer = fecha_ayer_dt.strftime('%Y-%m-%d')
    
    try:
        response_ayer = supabase.table("cierre_caja").select("cierre_final").eq("fecha", fecha_ayer).execute()
        if response_ayer.data:
            saldo_del_ayer = float(response_ayer.data[0].get("cierre_final", 0))
            logging.info(f"Usando cierre final del día anterior ({fecha_ayer}): {saldo_del_ayer}")
            return saldo_del_ayer
    except Exception as e:
        logging.error(f"Error al obtener cierre del día anterior ({fecha_ayer}): {e}")
    
    # Si llegamos aquí, no hay cierre del día anterior
    # Si está configurado el primer día y estamos después de esa fecha, algo está mal
    if config['configurado'] and config['fecha_inicio']:
        try:
            fecha_inicio_dt = datetime.strptime(config['fecha_inicio'], '%Y-%m-%d')
            if fecha_consulta_dt > fecha_inicio_dt:
                logging.warning(f"Falta cierre del día anterior para fecha {fecha_consulta}, usando saldo configurado como fallback")
                return config['saldo_inicial']
        except ValueError:
            pass
    
    # Usar valor por defecto (configurado o legacy)
    logging.info(f"Usando saldo por defecto: {config['saldo_inicial']}")
    return config['saldo_inicial']

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
    
    # Obtener saldo inicial usando la lógica inteligente
    saldo_inicial = obtener_saldo_inicial_inteligente(fecha)
    
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
        resp_ped = supabase.table("pedidos").select("brs,cliente").eq("fecha", fecha).eq("eliminado", False).execute()
        egresos_no_detal = sum(item.get("brs", 0) for item in resp_ped.data if item.get("cliente") != "DETAL") if resp_ped.data else 0
        egresos_detal = sum(item.get("brs", 0) for item in resp_ped.data if item.get("cliente") == "DETAL") if resp_ped.data else 0
    except Exception as e:
        logging.error("Error al obtener egresos: %s", e)
        egresos_no_detal = 0
        egresos_detal = 0
    formatted_egresos = format(egresos_no_detal, ",.0f").replace(",", ".")
    formatted_egresos_detal = format(egresos_detal, ",.0f").replace(",", ".")
    formatted_saldo_inicial = format(saldo_inicial, ",.0f").replace(",", ".")

    # Buscar si ya existe un cierre guardado para la fecha seleccionada
    cierre_guardado = None
    try:
        cierre_resp = supabase.table("cierre_caja").select("*").eq("fecha", fecha).execute()
        if cierre_resp.data:
            cierre_guardado = cierre_resp.data[0]
    except Exception as e:
        logging.error(f"Error al consultar cierre guardado: {e}")

    # Valores por defecto
    egresos_detal = ''
    gastos = 0
    pago_movil = 0
    cierre_detal = 0
    saldo_bancos = 0
    ingresos_extra_detalle = []
    gastos_detalle = []

    # Si hay cierre guardado, sobreescribir valores SOLO de los campos manuales
    if cierre_guardado:
        egresos_detal = str(cierre_guardado.get("egresos_detal", ''))
        gastos = cierre_guardado.get("gastos", 0)
        pago_movil = cierre_guardado.get("pago_movil", 0)
        cierre_detal = cierre_guardado.get("cierre_detal", 0)
        saldo_bancos = cierre_guardado.get("saldo_bancos", 0)
        # Refuerzo para ingresos_extra_detalle
        try:
            ingresos_extra_detalle = cierre_guardado.get("ingresos_extra_detalle", "[]")
            if not ingresos_extra_detalle:
                ingresos_extra_detalle = []
            elif isinstance(ingresos_extra_detalle, str):
                ingresos_extra_detalle = json.loads(ingresos_extra_detalle)
            if not isinstance(ingresos_extra_detalle, list):
                ingresos_extra_detalle = []
        except Exception:
            ingresos_extra_detalle = []
        # Refuerzo para gastos_detalle
        try:
            gastos_detalle = cierre_guardado.get("gastos_detalle", "[]")
            if not gastos_detalle:
                gastos_detalle = []
            elif isinstance(gastos_detalle, str):
                gastos_detalle = json.loads(gastos_detalle)
            if not isinstance(gastos_detalle, list):
                gastos_detalle = []
        except Exception:
            gastos_detalle = []

    # Obtener información de configuración para mostrar en la interfaz
    config_info = obtener_configuracion_inicial()
    
    return render_template('cierre/index.html', active_page='cierre',
                           ingresos=formatted_ingresos, egresos=formatted_egresos,
                           egresos_detal=egresos_detal,
                           saldo_inicial=formatted_saldo_inicial, fecha_iso=fecha,
                           fecha_mostrar=fecha_mostrar,
                           gastos=gastos, pago_movil=pago_movil, cierre_detal=cierre_detal,
                           saldo_bancos=saldo_bancos, ingresos_extra_detalle=ingresos_extra_detalle,
                           gastos_detalle=gastos_detalle, config_info=config_info)

@cierre_bp.route('/guardar', methods=['POST'])
@login_required
def guardar_cierre():
    """Guarda o actualiza el cierre de caja del día"""
    try:
        # Obtener datos del formulario
        data = request.get_json()
        fecha = data.get('fecha') or datetime.now().strftime('%Y-%m-%d')
        usuario_email = session.get('email', 'usuario_desconocido')
        
        # Validar datos requeridos
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos'}), 400
        
        # Obtener saldo inicial usando la lógica inteligente
        saldo_inicial = obtener_saldo_inicial_inteligente(fecha)
            
        # Extraer valores del frontend
        ingresos_binance = float(data.get('ingresos_binance', 0))
        ingresos_extra = float(data.get('ingresos_extra', 0))
        total_ingresos = float(data.get('total_ingresos', 0))
        egresos_pedidos = float(data.get('egresos_pedidos', 0))
        egresos_detal = float(data.get('egresos_detal', 0))
        gastos = float(data.get('gastos', 0))
        gastos_detalle = data.get('gastos_detalle', [])
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
            'gastos_detalle': json.dumps(gastos_detalle),
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