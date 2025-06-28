import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import pytz
from mi_app.extensions import chile_tz

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
transferencias_bp = Blueprint("transferencias", __name__)

@transferencias_bp.route("/")
@login_required
def index():
    try:
        # Calcular fecha límite (15 días atrás)
        fecha_limite = adjust_datetime(datetime.now(chile_tz) - timedelta(days=15)).strftime("%Y-%m-%d")
        
        # Obtener parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = 150
        offset = (page - 1) * per_page
        
        # Iniciar la consulta base con filtro de fecha
        query = supabase.table("transferencias").select(
            "id, cliente, empresa, rut, monto, fecha, fecha_detec, verificada, manual"
        ).gte("fecha", fecha_limite)  # Solo últimos 15 días

        # Aplicar filtros
        cliente = request.args.get("cliente")
        if cliente:
            if cliente == "Desconocido":
                query = query.is_("cliente", "null")
            else:
                query = query.eq("cliente", cliente)

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
        logging.info(f"[FILTRO] Empresas seleccionadas en el filtro: {empresas}")

        # Obtener lista única de empresas de la tabla transferencias (para log)
        response_empresas_log = supabase.table("transferencias").select("empresa").execute()
        empresas_db = sorted(set(e["empresa"] for e in response_empresas_log.data if e["empresa"] is not None)) if response_empresas_log.data else []
        logging.info(f"[FILTRO] Empresas únicas en la base de datos: {empresas_db}")

        if empresas and not (len(empresas) == 1 and empresas[0] == ""):
            empresas_filtradas = [emp for emp in empresas if emp.strip()]
            logging.info(f"[FILTRO] Empresas que se usarán para filtrar: {empresas_filtradas}")
            if empresas_filtradas:
                query = query.in_("empresa", empresas_filtradas)
        else:
            logging.info("[FILTRO] No se aplica filtro de empresas (opción 'Todas' seleccionada)")

        # Aplicar ordenamiento
        sort_fields = []
        for i in range(1, 4):  # Para sort1, sort2, sort3
            sort = request.args.get(f"sort{i}")
            order = request.args.get(f"order{i}", "asc")
            if sort:
                query = query.order(sort, desc=(order == "desc"))

        # Si no hay ordenamiento específico, ordenar por fecha_detec descendente
        if not any(request.args.get(f"sort{i}") for i in range(1, 4)):
            query = query.order("fecha_detec", desc=True)

        # Aplicar paginación
        query = query.range(offset, offset + per_page - 1)

        # Ejecutar la consulta
        response_transfers = query.execute()

        # Obtener el total de registros para la paginación
        count_query = supabase.table("transferencias").select("id", count="exact").gte("fecha", fecha_limite)
        
        # Aplicar los mismos filtros al count query
        if cliente:
            if cliente == "Desconocido":
                count_query = count_query.is_("cliente", "null")
            else:
                count_query = count_query.eq("cliente", cliente)
        
        if rut:
            count_query = count_query.ilike("rut", f"%{rut}%")
        
        if monto:
            try:
                count_query = count_query.eq("monto", int(monto))
            except ValueError:
                pass
        
        if verificada == "true":
            count_query = count_query.eq("verificada", True)
        elif verificada == "false":
            count_query = count_query.eq("verificada", False)
        
        # Filtro de empresas para el count_query (igual que arriba)
        if empresas and not (len(empresas) == 1 and empresas[0] == ""):
            empresas_filtradas = [emp for emp in empresas if emp.strip()]
            if empresas_filtradas:
                count_query = count_query.in_("empresa", empresas_filtradas)
        
        count_response = count_query.execute()
        total_records = count_response.count if hasattr(count_response, 'count') else 0
        total_pages = (total_records + per_page - 1) // per_page

        # Obtener todos los IDs de transferencias asignadas de una sola vez
        asignadas_resp = supabase.table('transferencias_pagos').select('transferencia_id').execute()
        ids_asignadas = set()
        if asignadas_resp.data:
            ids_asignadas = {item['transferencia_id'] for item in asignadas_resp.data}

        transfers_data = []
        clientes_en_transferencias = set()
        if response_transfers.data:
            for transfer in response_transfers.data:
                transfer_processed = {
                    'id': transfer.get('id'),
                    'cliente': transfer.get('cliente') if transfer.get('cliente') is not None else 'Desconocido',
                    'empresa': transfer.get('empresa') if transfer.get('empresa') is not None else '',
                    'rut': transfer.get('rut') if transfer.get('rut') is not None else '',
                    'monto': float(transfer.get('monto', 0)),
                    'fecha': transfer.get('fecha') if transfer.get('fecha') is not None else '',
                    'fecha_detec': transfer.get('fecha_detec') if transfer.get('fecha_detec') is not None else '',
                    'verificada': bool(transfer.get('verificada', False)),
                    'manual': bool(transfer.get('manual', False))
                }
                transfer_processed['asignado'] = transfer_processed['id'] in ids_asignadas
                transfers_data.append(transfer_processed)
                if transfer_processed['cliente'] and transfer_processed['cliente'] != 'Desconocido':
                    clientes_en_transferencias.add(transfer_processed['cliente'])

        # Obtener lista única de clientes y empresas
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        clientes_all = sorted(set(p["cliente"] for p in response_pagadores.data)) if response_pagadores.data else []
        # Ordenar: primero los clientes en transferencias, luego el resto
        clientes_ordenados = sorted(clientes_en_transferencias) + [c for c in clientes_all if c not in clientes_en_transferencias]
        
        # Obtener lista única de empresas de la tabla transferencias
        response_empresas = supabase.table("transferencias").select("empresa").execute()
        empresas = sorted(set(e["empresa"] for e in response_empresas.data if e["empresa"] is not None)) if response_empresas.data else []
        empresas = ["Todas"] + empresas  # Agregar opción "Todas" al inicio

        return render_template(
            "transferencias/index.html",
            transfers=transfers_data,
            cliente=clientes_ordenados,
            empresas=empresas,
            active_page="transferencias",
            pagination={
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_records': total_records,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            }
        )
    except Exception as e:
        logging.error(f"Error al obtener transferencias: {e}")
        flash("Error al cargar los datos de transferencias", "error")
        return render_template(
            "transferencias/index.html",
            transfers=[],
            cliente=[],
            empresas=[],
            active_page="transferencias",
            pagination={
                'page': 1,
                'per_page': 150,
                'total_pages': 0,
                'total_records': 0,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None
            }
        )

@transferencias_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        try:
            cliente = request.form.get("cliente")
            empresa = request.form.get("empresa")
            rut = request.form.get("rut")
            monto = int(float(request.form.get("monto")))
            fecha = request.form.get("fecha")
            verificada = True if request.form.get("verificada") == "on" else False
            fecha_detec = adjust_datetime(datetime.now(chile_tz)).isoformat()
            data = f"{cliente}-{empresa}-{rut}-{monto}-{fecha}-{verificada}"
            hash_value = hashlib.sha256(data.encode('utf-8')).hexdigest()
            supabase.table("transferencias").insert({
                "cliente": cliente,
                "empresa": empresa,
                "rut": rut,
                "monto": monto,
                "fecha": fecha,
                "fecha_detec": fecha_detec,
                "verificada": verificada,
                "hash": hash_value,
                "manual": True
            }).execute()
            flash("Transferencia ingresada con éxito.")
            return redirect(url_for("transferencias.nuevo"))
        except Exception as e:
            logging.error("Error al insertar transferencia: %s", e)
            flash("Error al ingresar la transferencia: " + str(e))
            return redirect(url_for("transferencias.nuevo"))
    current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    try:
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        cliente_pagadores = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
    except Exception as e:
        logging.error("Error al obtener clientes para transferencia: %s", e)
        cliente_pagadores = []
    empresa_options = ["Caja Vecina", "Depósito en efectivo", "Otro"]
    return render_template("transferencias/nuevo.html", current_date=current_date, active_page="transferencias",
                           cliente_pagadores=cliente_pagadores, empresa_options=empresa_options)

@transferencias_bp.route("/editar/<transfer_id>", methods=["GET", "POST"])
@login_required
def editar_transferencia(transfer_id):
    try:
        response = supabase.table("transferencias").select("*").eq("id", transfer_id).execute()
        if not response.data:
            flash("Transferencia no encontrada.")
            return redirect(url_for("transferencias.index"))
        transferencia = response.data[0]
    except Exception as e:
        logging.error("Error al obtener la transferencia: %s", e)
        flash("Error al obtener la transferencia: " + str(e))
        return redirect(url_for("transferencias.index"))
    if not transferencia.get("manual", False):
        flash("Esta transferencia no puede ser editada porque no fue ingresada manualmente.")
        return redirect(url_for("transferencias.index"))
    if request.method == "POST":
        try:
            cliente = request.form.get("cliente")
            empresa = request.form.get("empresa")
            rut = request.form.get("rut")
            monto = int(float(request.form.get("monto")))
            fecha = request.form.get("fecha")
            verificada = True if request.form.get("verificada") == "on" else False
            data = f"{cliente}-{empresa}-{rut}-{monto}-{fecha}-{verificada}"
            hash_value = hashlib.sha256(data.encode('utf-8')).hexdigest()
            supabase.table("transferencias").update({
                "cliente": cliente,
                "empresa": empresa,
                "rut": rut,
                "monto": monto,
                "fecha": fecha,
                "verificada": verificada,
                "hash": hash_value
            }).eq("id", transfer_id).execute()
            flash("Transferencia actualizada con éxito.")
            return redirect(url_for("transferencias.index"))
        except Exception as e:
            logging.error("Error al actualizar la transferencia: %s", e)
            flash("Error al actualizar la transferencia: " + str(e))
            return redirect(url_for("transferencias.editar_transferencia", transfer_id=transfer_id))
    current_date = transferencia.get("fecha", adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d"))
    try:
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        cliente_pagadores = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
    except Exception as e:
        logging.error("Error al obtener clientes para transferencia: %s", e)
        cliente_pagadores = []
    empresa_options = ["Caja Vecina", "Depósito en efectivo", "Otro"]
    return render_template(
        "transferencias/editar.html",
        transferencia=transferencia,
        current_date=current_date,
        cliente_pagadores=cliente_pagadores,
        empresa_options=empresa_options,
        active_page="transferencias"
    )

@transferencias_bp.route('/buscar_cliente')
@login_required
def buscar_cliente():
    term = request.args.get('term', '').strip().lower()
    # Buscar clientes que contengan el término (case-insensitive)
    response_pagadores = supabase.table("pagadores").select("cliente").execute()
    clientes = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
    resultados = []
    for c in clientes:
        if term in c.lower():
            resultados.append({"id": c, "text": c})
    # Limitar resultados para Select2
    return jsonify({"results": resultados[:30]})

@transferencias_bp.route('/asignar_pago', methods=['POST'])
@login_required
def asignar_pago():
    try:
        data = request.get_json()
        transferencia_id = data.get('transferencia_id')
        cliente = data.get('cliente')
        if not transferencia_id or not cliente:
            return jsonify({'success': False, 'message': 'Faltan datos requeridos.'}), 400

        # Verificar si ya existe una asignación para esta transferencia
        asignacion_existente = supabase.table('transferencias_pagos').select('id, cliente').eq('transferencia_id', transferencia_id).execute()
        if asignacion_existente.data:
            cliente_actual = asignacion_existente.data[0]['cliente']
            return jsonify({'success': False, 'message': f'Esta transferencia ya tiene un pago asignado al cliente {cliente_actual}.'}), 400

        # Obtener información de la transferencia
        transferencia_response = supabase.table('transferencias').select('monto, fecha').eq('id', transferencia_id).execute()
        if not transferencia_response.data:
            return jsonify({'success': False, 'message': 'Transferencia no encontrada.'}), 404
        
        transferencia = transferencia_response.data[0]
        monto = transferencia.get('monto')
        fecha_transferencia = transferencia.get('fecha')

        # Buscar si ya existe un pago con el mismo monto y cliente
        pago_existente = supabase.table('pagos_realizados').select('id').eq('cliente', cliente).eq('monto_total', monto).eq('eliminado', False).execute()
        
        pago_id = None
        if pago_existente.data:
            # Usar el pago existente
            pago_id = pago_existente.data[0]['id']
        else:
            # Crear un nuevo pago
            fecha_hora = datetime.now(chile_tz).isoformat()
            nuevo_pago = supabase.table('pagos_realizados').insert({
                'cliente': cliente,
                'monto_total': monto,
                'fecha_registro': fecha_hora
            }).execute()
            
            if nuevo_pago.data:
                pago_id = nuevo_pago.data[0]['id']
            else:
                return jsonify({'success': False, 'message': 'Error al crear el pago.'}), 500

        # Obtener el usuario actual de la sesión
        usuario = session.get('email', 'desconocido')

        # Insertar la relación en la tabla transferencias_pagos
        supabase.table('transferencias_pagos').insert({
            'transferencia_id': transferencia_id,
            'pago_id': pago_id,
            'cliente': cliente,
            'usuario_asignacion': usuario
        }).execute()

        # Actualizar también el cliente en la tabla transferencias
        supabase.table('transferencias').update({
            'cliente': cliente
        }).eq('id', transferencia_id).execute()

        return jsonify({'success': True, 'message': 'Pago asignado correctamente.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error inesperado: {str(e)}'}), 500 