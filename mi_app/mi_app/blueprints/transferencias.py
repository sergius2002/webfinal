import os
import time
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from supabase import create_client, Client
import pytz
from mi_app.mi_app.extensions import chile_tz

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

        empresas_filtro = request.args.getlist("empresa")
        logging.info(f"[FILTRO] Empresas seleccionadas en el filtro: {empresas_filtro}")

        # Obtener lista única de empresas de las 1000 transferencias más recientes para el select
        response_empresas = supabase.table("transferencias").select("empresa").order("fecha", desc=True).limit(1000).execute()
        empresas_select = sorted(set(e["empresa"] for e in response_empresas.data if e["empresa"] is not None)) if response_empresas.data else []
        empresas_select = ["Todas"] + empresas_select  # Agregar opción "Todas" al inicio

        # Obtener lista única de empresas de la tabla transferencias (para log)
        response_empresas_log = supabase.table("transferencias").select("empresa").execute()
        empresas_db = sorted(set(e["empresa"] for e in response_empresas_log.data if e["empresa"] is not None)) if response_empresas_log.data else []
        logging.info(f"[FILTRO] Empresas únicas en la base de datos: {empresas_db}")

        # Aplicar filtro de empresas a la consulta principal
        if empresas_filtro and not (len(empresas_filtro) == 1 and empresas_filtro[0] == ""):
            empresas_filtradas = [emp for emp in empresas_filtro if emp.strip()]
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
        if empresas_filtro and not (len(empresas_filtro) == 1 and empresas_filtro[0] == ""):
            empresas_filtradas = [emp for emp in empresas_filtro if emp.strip()]
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
        
        return render_template(
            "transferencias/index.html",
            transfers=transfers_data,
            cliente=clientes_ordenados,
            empresas=empresas_select,
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

def procesar_archivo_inmediato(ruta_archivo, nombre_original):
    """
    Procesa un archivo inmediatamente después de subirlo
    """
    try:
        import shutil
        import subprocess
        import os
        
        # Directorio base del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Ya no necesitamos carpetas de destino, procesamos directamente desde uploads
        
        # Obtener ruta del Python del entorno virtual
        # Usar la misma ruta que el monitor para consistencia
        venv_python = '/home/sacristobalspa/webfinal/venv/bin/python'
        if not os.path.exists(venv_python):
            # Fallback para desarrollo local
            venv_python = os.path.join(base_dir, 'venv', 'bin', 'python3')
        if not os.path.exists(venv_python):
            # Fallback para Windows
            venv_python = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
        if not os.path.exists(venv_python):
            # Fallback al Python del sistema
            venv_python = 'python3'
            
        logging.info(f"Usando Python: {venv_python}")
        
        # Palabras clave
        bci_keyword = 'Movimientos_Detallado_Cuenta'
        santander_keyword = 'CartolaMovimiento-'
        
        if bci_keyword in nombre_original:
            logging.info(f"Procesando archivo BCI: {nombre_original}")
            
            # Ejecutar script BCI directamente (sin copiar archivo)
            try:
                subprocess.run([venv_python, 'bci.py'], cwd=base_dir, check=True, timeout=300)
                logging.info("Script bci.py ejecutado exitosamente")
                return True, "Archivo BCI procesado exitosamente"
            except subprocess.TimeoutExpired:
                logging.error("Script bci.py excedió el tiempo límite")
                return False, "Script BCI excedió el tiempo límite"
            except subprocess.CalledProcessError as e:
                logging.error(f"Error ejecutando bci.py: {e}")
                return False, f"Error ejecutando script BCI: {e}"
                
        elif santander_keyword in nombre_original:
            logging.info(f"Procesando archivo Santander: {nombre_original}")
            
            # Ejecutar script Santander directamente (sin copiar archivo)
            try:
                subprocess.run([venv_python, 'Santander.py'], cwd=base_dir, check=True, timeout=300)
                logging.info("Script Santander.py ejecutado exitosamente")
                return True, "Archivo Santander procesado exitosamente"
            except subprocess.TimeoutExpired:
                logging.error("Script Santander.py excedió el tiempo límite")
                return False, "Script Santander excedió el tiempo límite"
            except subprocess.CalledProcessError as e:
                logging.error(f"Error ejecutando Santander.py: {e}")
                return False, f"Error ejecutando script Santander: {e}"
        else:
            logging.warning(f"Archivo no reconocido: {nombre_original}")
            return False, "Archivo no reconocido (no es BCI ni Santander)"
            
    except Exception as e:
        logging.error(f"Error procesando archivo {nombre_original}: {e}")
        return False, f"Error procesando archivo: {str(e)}"

@transferencias_bp.route('/subir_archivo', methods=['POST'])
@login_required
def subir_archivo():
    try:
        # Verificar si se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo.'}), 400
        
        file = request.files['archivo']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo.'}), 400
        
        # Verificar extensión del archivo
        if not file.filename.lower().endswith('.xlsx'):
            return jsonify({'success': False, 'message': 'El archivo debe ser un Excel (.xlsx).'}), 400
        
        # Obtener parámetros (ya no necesarios para XLSX)
        # verificar_duplicados = request.form.get('verificar_duplicados', 'false').lower() == 'true'
        # marcar_verificada = request.form.get('marcar_verificada', 'false').lower() == 'true'
        
        # Crear nombre único para el archivo
        import os
        from datetime import datetime
        
        # Obtener información del usuario
        usuario = session.get('email', 'desconocido')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Crear nombre de archivo único
        nombre_original = file.filename
        nombre_base = os.path.splitext(nombre_original)[0]
        extension = os.path.splitext(nombre_original)[1]
        nombre_archivo = f"{nombre_base}_{usuario}_{timestamp}{extension}"
        
        # Ruta donde guardar el archivo
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'transferencias', 'uploads')
        
        # Crear la carpeta si no existe
        os.makedirs(upload_folder, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(upload_folder, nombre_archivo)
        
        # Guardar el archivo físicamente
        file.save(file_path)
        
        # Obtener tamaño del archivo
        tamano_archivo = os.path.getsize(file_path)
        
        # Registrar el archivo en la base de datos
        registro_archivo = supabase.table('archivos_subidos').insert({
            'nombre_archivo': nombre_archivo,
            'nombre_original': nombre_original,
            'ruta_archivo': file_path,
            'usuario': usuario,
            'estado': 'en_proceso',
            'verificar_duplicados': False,  # No aplica para XLSX
            'marcar_verificada': False,     # No aplica para XLSX
            'tamano_archivo': tamano_archivo
        }).execute()
        
        archivo_id = registro_archivo.data[0]['id'] if registro_archivo.data else None
        
        # Procesar el archivo inmediatamente
        exito, mensaje = procesar_archivo_inmediato(file_path, nombre_original)
        
        # Detectar tipo de banco basado en el nombre del archivo
        tipo_banco = "No reconocido"
        if "Movimientos_Detallado_Cuenta" in nombre_original:
            tipo_banco = "BCI"
        elif "CartolaMovimiento-" in nombre_original:
            tipo_banco = "Santander"
        
        # Actualizar registro con el resultado del procesamiento
        if archivo_id:
            estado = 'procesado' if exito else 'error'
            supabase.table('archivos_subidos').update({
                'estado': estado,
                'mensaje_error': mensaje
            }).eq('id', archivo_id).execute()
        
        if exito:
            return jsonify({
                'success': True,
                'message': f'Archivo {tipo_banco} subido y procesado exitosamente.',
                'archivo_guardado': nombre_archivo,
                'tipo_banco': tipo_banco
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Archivo subido pero error en procesamiento: {mensaje}',
                'archivo_guardado': nombre_archivo,
                'tipo_banco': tipo_banco
            }), 400
            
    except Exception as e:
        import traceback
        logging.error(f"Error al procesar archivo: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error inesperado: {str(e)}', 'traceback': traceback.format_exc()}), 500

@transferencias_bp.route('/historial_archivos')
@login_required
def historial_archivos():
    try:
        # Obtener parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # Obtener archivos subidos ordenados por fecha descendente
        response = supabase.table('archivos_subidos').select('*').order('fecha_subida', desc=True).range(offset, offset + per_page - 1).execute()
        
        # Obtener total de registros para paginación
        count_response = supabase.table('archivos_subidos').select('id', count='exact').execute()
        total_records = count_response.count if hasattr(count_response, 'count') else 0
        total_pages = (total_records + per_page - 1) // per_page
        
        archivos = response.data if response.data else []
        
        # Calcular información de paginación
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_records': total_records,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
        }
        
        return render_template(
            'transferencias/historial_archivos.html',
            archivos=archivos,
            pagination=pagination,
            active_page="transferencias"
        )
        
    except Exception as e:
        logging.error(f"Error al obtener historial de archivos: {e}")
        flash("Error al cargar el historial de archivos", "error")
        return redirect(url_for("transferencias.index"))

@transferencias_bp.route('/descargar_archivo/<int:archivo_id>')
@login_required
def descargar_archivo(archivo_id):
    try:
        # Obtener información del archivo
        response = supabase.table('archivos_subidos').select('*').eq('id', archivo_id).execute()
        
        if not response.data:
            flash("Archivo no encontrado", "error")
            return redirect(url_for("transferencias.historial_archivos"))
        
        archivo = response.data[0]
        ruta_archivo = archivo['ruta_archivo']
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_archivo):
            flash("El archivo físico no existe", "error")
            return redirect(url_for("transferencias.historial_archivos"))
        
        # Enviar archivo como descarga
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=archivo['nombre_original']
        )
        
    except Exception as e:
        logging.error(f"Error al descargar archivo {archivo_id}: {e}")
        flash("Error al descargar el archivo", "error")
        return redirect(url_for("transferencias.historial_archivos")) 