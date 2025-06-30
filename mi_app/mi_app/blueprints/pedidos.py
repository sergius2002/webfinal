import os
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import pytz

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
    
    # Si no tiene zona horaria, asumir que está en la zona local
    if dt.tzinfo is None:
        dt = chile_tz.localize(dt)
    
    # Aplicar ajuste de hora solo si es diferente de 0
    if HOUR_ADJUSTMENT != 0:
        dt = dt + timedelta(hours=HOUR_ADJUSTMENT)
    
    return dt

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
pedidos_bp = Blueprint("pedidos", __name__)

def parse_tasa(num_str):
    """
    Parsea y valida una tasa de cambio.
    Args:
        num_str: String con el valor de la tasa
    Returns:
        float: Valor de la tasa validado
    Raises:
        ValueError: Si el valor no es válido o es menor o igual a 0
    """
    if num_str is None or not str(num_str).strip():
        raise ValueError("La tasa no puede estar vacía")
    
    try:
        num_str = str(num_str).strip()
        if ',' in num_str and '.' in num_str:
            num_str = num_str.replace('.', '').replace(',', '.')
        elif ',' in num_str:
            num_str = num_str.replace(',', '.')
        
        result = float(num_str)
        if result <= 0:
            raise ValueError(f"La tasa debe ser mayor a 0, se recibió: {num_str}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"Valor de tasa no válido: {num_str}. Error: {str(e)}")

def parse_brs(num_str):
    """
    Parsea y valida un valor BRS.
    Args:
        num_str: String con el valor BRS
    Returns:
        int: Valor BRS validado
    Raises:
        ValueError: Si el valor no es válido o es menor o igual a 0
    """
    if num_str is None or not str(num_str).strip():
        raise ValueError("El BRS no puede estar vacío")
    
    try:
        # Limpiar el string de caracteres no numéricos excepto punto y coma
        cleaned = str(num_str).strip()
        
        # Detectar el formato basado en la posición de los separadores
        if ',' in cleaned and '.' in cleaned:
            # Determinar cuál es el separador de miles y cuál el decimal
            comma_pos = cleaned.rfind(',')
            dot_pos = cleaned.rfind('.')
            
            if comma_pos > dot_pos:
                # Formato europeo: "1.000,50" -> "1000.50"
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # Formato americano: "1,000.50" -> "1000.50"
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Solo tiene coma - determinar si es separador de miles o decimal
            if len(cleaned) > 3 and cleaned[-4] == ',':
                # Es separador de miles: "1,000" -> "1000"
                cleaned = cleaned.replace(',', '')
            else:
                # Es decimal: "1,5" -> "1.5"
                cleaned = cleaned.replace(',', '.')
        elif '.' in cleaned:
            # Solo tiene punto - determinar si es separador de miles o decimal
            if len(cleaned) > 3 and cleaned[-4] == '.':
                # Es separador de miles: "1.000" -> "1000"
                cleaned = cleaned.replace('.', '')
            # Si no, el punto ya es decimal y está bien
        
        # Convertir a float primero para manejar decimales correctamente
        float_result = float(cleaned)
        result = int(round(float_result))
        
        if result <= 0:
            raise ValueError(f"El BRS debe ser mayor a 0, se recibió: {num_str}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"Valor BRS no válido: {num_str}. Error: {str(e)}")

@pedidos_bp.route("/")
@login_required
def index():
    try:
        query = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp")
        
        # Filtrar pedidos no eliminados
        query = query.eq("eliminado", False)
        
        # Aplicar filtros
        cliente = request.args.get("cliente")
        if cliente:
            query = query.eq("cliente", cliente)

        fecha = request.args.get("fecha")
        if not fecha:
            fecha = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
        query = query.eq("fecha", fecha)

        brs = request.args.get("brs", "").strip()
        if brs:
            try:
                query = query.eq("brs", float(brs))
            except ValueError:
                logging.warning("Valor de BRS no válido: %s", brs)

        clp = request.args.get("clp", "").replace(".", "").strip()
        if clp:
            try:
                query = query.eq("clp", int(clp))
            except ValueError:
                logging.warning("Valor de CLP no válido: %s", clp)

        query = query.order("fecha", desc=False)
        response = query.execute()
        pedidos_data = response.data if response.data is not None else []
        clientes = sorted({p["cliente"] for p in pedidos_data if p.get("cliente")})
        # Obtener tasas desde la tabla de configuración
        tasas_resp = supabase.table("configuracion").select("clave, valor").in_("clave", ["tasa_banesco", "tasa_venezuela", "tasa_otros"]).execute()
        tasas_dict = {t["clave"]: t["valor"] for t in tasas_resp.data} if tasas_resp.data else {}
        tasa_banesco = tasas_dict.get("tasa_banesco", "0.000")
        tasa_venezuela = tasas_dict.get("tasa_venezuela", "0.000")
        tasa_otros = tasas_dict.get("tasa_otros", "0.000")
        # Verificar si el usuario es admin
        is_admin = False
        if "email" in session:
            try:
                response_admin = supabase.table("allowed_users").select("email").eq("email", session["email"]).execute()
                is_admin = bool(response_admin.data)
            except Exception as e:
                logging.error("Error al verificar permisos de usuario: %s", e)
    except Exception as e:
        logging.error("Error al cargar los pedidos: %s", e)
        flash("Error al cargar los pedidos: " + str(e))
        pedidos_data, clientes = [], []
        tasa_banesco = tasa_venezuela = tasa_otros = "0.000"
        is_admin = False
    current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    return render_template("pedidos/index.html", pedidos=pedidos_data, cliente=clientes, active_page="pedidos",
                           current_date=current_date,
                           tasa_banesco=tasa_banesco, tasa_venezuela=tasa_venezuela, tasa_otros=tasa_otros,
                           is_admin=is_admin)

@pedidos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    # Verificar estructura de tabla al inicio
    table_valid, table_error = check_table_structure()
    if not table_valid:
        logging.error(f"Error en estructura de tabla: {table_error}")
        flash(f"Error de configuración: {table_error}. Contacte al administrador.")
        return redirect(url_for("pedidos.index"))
    
    try:
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        cliente_pagadores = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
        # Obtener tasa_venezuela como valor por defecto
        tasa_resp = supabase.table("configuracion").select("valor").eq("clave", "tasa_venezuela").single().execute()
        tasa_venezuela = tasa_resp.data["valor"] if tasa_resp.data and "valor" in tasa_resp.data else "0.000"
    except Exception as e:
        logging.error("Error al obtener cliente de pagadores o tasa venezuela: %s", e)
        flash("Error al cargar datos iniciales. Por favor, recarga la página.")
        cliente_pagadores = []
        tasa_venezuela = "0.000"
    
    if request.method == "POST":
        try:
            # Sanitizar y obtener datos del formulario
            cliente = sanitize_input(request.form.get("cliente", ""))
            brs_raw = sanitize_input(request.form.get("brs", ""))
            tasa_raw = sanitize_input(request.form.get("tasa", ""))
            fecha = sanitize_input(request.form.get("fecha", ""))
            
            # Procesar valores con manejo de errores mejorado
            try:
                brs_num = parse_brs(brs_raw)
                tasa_num = round(parse_tasa(tasa_raw), 6)
            except ValueError as e:
                flash(f"Error en los datos ingresados: {str(e)}")
                return render_template("pedidos/nuevo.html", 
                                     cliente_pagadores=cliente_pagadores, 
                                     current_date=adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d"),
                                     active_page="pedidos", 
                                     tasa_venezuela=tasa_venezuela)
            
            # Validar datos usando la función de validación mejorada
            is_valid, error_message = validate_pedido_data(cliente, brs_num, tasa_num, fecha)
            if not is_valid:
                flash(error_message)
                return render_template("pedidos/nuevo.html", 
                                     cliente_pagadores=cliente_pagadores, 
                                     current_date=adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d"),
                                     active_page="pedidos", 
                                     tasa_venezuela=tasa_venezuela)
            
            # Calcular CLP para mostrar al usuario
            clp_calculado = round(brs_num / tasa_num, 2)
            usuario = session.get("email")
            
            # Log de información (sin datos sensibles)
            logging.info(f"Insertando pedido - Cliente: {cliente}, Fecha: {fecha}, Usuario: {usuario}")
            
            # Insertar en base de datos
            result = supabase.table("pedidos").insert({
                "cliente": cliente, 
                "brs": str(brs_num), 
                "tasa": str(tasa_num), 
                "fecha": fecha, 
                "usuario": usuario
            }).execute()
            
            if result.data:
                flash(f"Pedido ingresado con éxito. CLP calculado: {clp_calculado:,.0f}")
            else:
                flash("Error: No se pudo insertar el pedido en la base de datos.")
                
            return redirect(url_for("pedidos.nuevo"))
            
        except Exception as e:
            logging.error("Error al insertar pedido: %s", e)
            flash(f"Error al insertar pedido: {str(e)}")
            return redirect(url_for("pedidos.nuevo"))
    
    current_date = adjust_datetime(datetime.now(chile_tz)).strftime("%Y-%m-%d")
    return render_template("pedidos/nuevo.html", cliente_pagadores=cliente_pagadores, current_date=current_date,
                           active_page="pedidos", tasa_venezuela=tasa_venezuela)

@pedidos_bp.route("/editar/<pedido_id>", methods=["GET", "POST"])
@login_required
def editar(pedido_id):
    try:
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        cliente_pagadores = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
    except Exception as e:
        logging.error("Error al obtener cliente de pagadores: %s", e)
        cliente_pagadores = []
    
    try:
        pedido_response = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp").eq("id", pedido_id).eq("eliminado", False).execute()
        if not pedido_response.data:
            flash("Pedido no encontrado.")
            return redirect(url_for("pedidos.index"))
        pedido = pedido_response.data[0]
    except Exception as e:
        logging.error("Error al obtener pedido: %s", e)
        flash("Error al obtener pedido: " + str(e))
        return redirect(url_for("pedidos.index"))
    
    # Obtener historial de cambios
    logs = []
    try:
        logs_response = supabase.table("pedidos_log").select("*").eq("pedido_id", pedido_id).order("fecha", desc=True).execute()
        logs = logs_response.data if logs_response.data is not None else []
    except Exception as e:
        logging.error("Error al obtener historial de cambios: %s", e)
    
    if request.method == "POST":
        try:
            # Sanitizar y obtener datos del formulario
            nuevo_cliente = sanitize_input(request.form.get("cliente"))
            nuevo_brs_raw = sanitize_input(request.form.get("brs"))
            nuevo_tasa_raw = sanitize_input(request.form.get("tasa"))
            nuevo_fecha = sanitize_input(request.form.get("fecha"))
            
            # Procesar valores con manejo de errores mejorado
            try:
                nuevo_brs = parse_brs(nuevo_brs_raw)
                nuevo_tasa = parse_tasa(nuevo_tasa_raw)
            except ValueError as e:
                flash(f"Error en los datos ingresados: {str(e)}")
                return render_template("pedidos/editar.html", pedido=pedido, cliente_pagadores=cliente_pagadores, logs=logs,
                                       active_page="pedidos")
            
            # Validar datos usando la función de validación mejorada
            is_valid, error_message = validate_pedido_data(nuevo_cliente, nuevo_brs, nuevo_tasa, nuevo_fecha)
            if not is_valid:
                flash(error_message)
                return render_template("pedidos/editar.html", pedido=pedido, cliente_pagadores=cliente_pagadores, logs=logs,
                                       active_page="pedidos")
            
            # Detectar cambios
            cambios = []
            if pedido["cliente"] != nuevo_cliente:
                cambios.append(f"cliente: {pedido['cliente']} -> {nuevo_cliente}")
            if int(pedido["brs"]) != nuevo_brs:
                cambios.append(f"brs: {pedido['brs']} -> {nuevo_brs}")
            if float(pedido["tasa"]) != nuevo_tasa:
                cambios.append(f"tasa: {pedido['tasa']} -> {nuevo_tasa}")
            if pedido["fecha"] != nuevo_fecha:
                cambios.append(f"fecha: {pedido['fecha']} -> {nuevo_fecha}")
            
            # Actualizar pedido
            supabase.table("pedidos").update({
                "cliente": nuevo_cliente, 
                "brs": str(nuevo_brs), 
                "tasa": str(nuevo_tasa), 
                "fecha": nuevo_fecha
            }).eq("id", pedido_id).execute()
            
            # Registrar cambios en el log
            if cambios:
                cambios_str = "; ".join(cambios)
                try:
                    supabase.table("pedidos_log").insert({
                        "pedido_id": pedido_id, 
                        "usuario": session.get("email"), 
                        "cambios": cambios_str,
                        "fecha": adjust_datetime(datetime.now(chile_tz)).isoformat()
                    }).execute()
                except Exception as log_error:
                    logging.error("Error al insertar en el log de cambios: %s", log_error)
                    flash("Error al registrar el historial de cambios: " + str(log_error))
            
            flash("Pedido actualizado con éxito.")
            return redirect(url_for("pedidos.index"))
            
        except Exception as e:
            logging.error("Error al actualizar pedido: %s", e)
            flash("Error al actualizar pedido: " + str(e))
            return redirect(url_for("pedidos.editar", pedido_id=pedido_id))
    
    return render_template("pedidos/editar.html", pedido=pedido, cliente_pagadores=cliente_pagadores, logs=logs,
                           active_page="pedidos")

@pedidos_bp.route("/test_insert")
@login_required
def test_insert():
    """Ruta de prueba para insertar un pedido con valores hardcodeados"""
    try:
        # Valores de prueba MUY pequeños
        test_data = {
            "cliente": "TEST",
            "brs": 100,  # Valor muy pequeño
            "tasa": 1.0,
            "fecha": "2025-06-24",
            "usuario": "test@test.com"
        }
        
        logging.info(f"Intentando insertar datos de prueba: {test_data}")
        
        result = supabase.table("pedidos").insert(test_data).execute()
        
        logging.info(f"Resultado de inserción: {result}")
        
        return jsonify({"success": True, "data": result.data})
        
    except Exception as e:
        logging.error(f"Error en test_insert: {e}")
        return jsonify({"success": False, "error": str(e)})

@pedidos_bp.route("/check_table_structure")
@login_required
def check_table_structure_route():
    """
    Ruta para verificar la estructura de la tabla pedidos
    Returns: JSON response
    """
    try:
        table_valid, table_error = check_table_structure()
        return jsonify({
            "success": table_valid,
            "message": table_error if not table_valid else "Estructura de tabla válida"
        })
    except Exception as e:
        logging.error(f"Error en check_table_structure_route: {e}")
        return jsonify({
            "success": False,
            "message": f"Error al verificar estructura: {str(e)}"
        })

@pedidos_bp.route("/eliminar/<int:pedido_id>", methods=["POST"])
@login_required
def eliminar(pedido_id):
    try:
        logging.info(f"Eliminando pedido con ID: {pedido_id}")
        usuario = session.get("email", "desconocido")
        ahora = adjust_datetime(datetime.now(chile_tz)).isoformat()
        
        # Obtener información del pedido antes de eliminarlo
        pedido_response = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp").eq("id", pedido_id).execute()
        if not pedido_response.data:
            flash("Pedido no encontrado.")
            return redirect(url_for("pedidos.index"))
        
        pedido = pedido_response.data[0]
        
        # Marcar como eliminado (borrado lógico)
        result = supabase.table("pedidos").update({"eliminado": True}).eq("id", pedido_id).execute()
        logging.info(f"Resultado del update en Supabase: {result}")
        
        # Registrar en historial
        supabase.table("pedidos_log").insert({
            "pedido_id": pedido_id,
            "usuario": usuario,
            "cambios": f"Pedido eliminado - Cliente: {pedido['cliente']}, BRS: {pedido['brs']}, Tasa: {pedido['tasa']}, CLP: {pedido['clp']}, Fecha: {pedido['fecha']}",
            "fecha": ahora
        }).execute()
        
        flash("Pedido eliminado (borrado lógico).")
    except Exception as e:
        logging.error(f"Error al eliminar pedido: {e}")
        flash(f"Error al eliminar el pedido: {str(e)}")
    
    return redirect(url_for("pedidos.index"))

@pedidos_bp.route('/editar_tasas', methods=['POST'])
@login_required
def editar_tasas():
    # Solo permitir a administradores
    if "email" not in session:
        return jsonify({"success": False, "error": "No autorizado"})
    
    try:
        response_admin = supabase.table("allowed_users").select("email").eq("email", session["email"]).execute()
        if not response_admin.data:
            return jsonify({"success": False, "error": "Solo administradores pueden editar tasas"})
    except Exception as e:
        logging.error("Error al verificar permisos de usuario: %s", e)
        return jsonify({"success": False, "error": "Error al verificar permisos"})
    
    try:
        data = request.get_json()
        tasa_banesco = data.get('tasa_banesco')
        tasa_venezuela = data.get('tasa_venezuela')
        tasa_otros = data.get('tasa_otros')
        
        # Validar que los valores sean números válidos
        for tasa, valor in [('tasa_banesco', tasa_banesco), ('tasa_venezuela', tasa_venezuela), ('tasa_otros', tasa_otros)]:
            try:
                float(valor)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": f"Valor inválido para {tasa}"})
        
        # Actualizar tasas en la base de datos (workaround manual)
        for clave, valor in [
            ("tasa_banesco", tasa_banesco),
            ("tasa_venezuela", tasa_venezuela),
            ("tasa_otros", tasa_otros)
        ]:
            # Intentar update primero
            update_result = supabase.table("configuracion").update({
                "valor": str(valor)
            }).eq("clave", clave).execute()
            # Si no se actualizó ninguna fila, hacer insert
            if not update_result.data or (isinstance(update_result.data, list) and len(update_result.data) == 0):
                supabase.table("configuracion").insert({
                    "clave": clave,
                    "valor": str(valor)
                }).execute()
        
        return jsonify({"success": True, "message": "Tasas actualizadas correctamente"})
        
    except Exception as e:
        logging.error("Error al actualizar tasas: %s", e)
        return jsonify({"success": False, "error": str(e)})

@pedidos_bp.route('/clp_maximo/<cliente>')
@login_required
def obtener_clp_maximo(cliente):
    """Obtiene el CLP máximo permitido para un cliente específico (insensible a mayúsculas/minúsculas y espacios)"""
    try:
        if not cliente or not cliente.strip():
            logging.warning("Cliente vacío o nulo en obtener_clp_maximo")
            return jsonify({
                "success": False,
                "error": "Cliente no especificado",
                "clp_maximo": 0
            })
        
        cliente_normalizado = cliente.strip().lower()
        logging.info(f"Buscando CLP máximo para cliente: '{cliente}' (normalizado: '{cliente_normalizado}')")
        
        # Obtener todos los clientes y buscar el que coincida normalizado
        response = supabase.table("clientes").select("cliente, clp_maximo").execute()
        
        if not response.data:
            logging.warning("No se encontraron clientes en la base de datos")
            return jsonify({
                "success": True,
                "clp_maximo": 0,
                "message": "No hay clientes registrados"
            })
        
        clp_maximo = 0
        cliente_encontrado = False
        
        for row in response.data:
            if row["cliente"] and row["cliente"].strip().lower() == cliente_normalizado:
                clp_maximo = row.get("clp_maximo", 0)
                cliente_encontrado = True
                logging.info(f"Cliente encontrado: '{row['cliente']}' con CLP máximo: {clp_maximo}")
                break
        
        if not cliente_encontrado:
            logging.info(f"Cliente '{cliente}' no encontrado en la base de datos")
            return jsonify({
                "success": True,
                "clp_maximo": 0,
                "message": f"Cliente '{cliente}' no encontrado"
            })
        
        return jsonify({
            "success": True,
            "clp_maximo": float(clp_maximo) if clp_maximo else 0,
            "message": "CLP máximo obtenido correctamente"
        })
        
    except Exception as e:
        logging.error(f"Error en obtener_clp_maximo para cliente '{cliente}': {e}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}",
            "clp_maximo": 0
        })

@pedidos_bp.route("/system_status")
@login_required
def system_status():
    """Ruta para verificar el estado del sistema de pedidos"""
    try:
        status = {
            "database_connection": False,
            "table_structure": False,
            "required_tables": {},
            "config_values": {},
            "errors": []
        }
        
        # Verificar conexión a base de datos
        try:
            test_query = supabase.table("pedidos").select("id").limit(1).execute()
            status["database_connection"] = True
        except Exception as e:
            status["errors"].append(f"Error de conexión a base de datos: {str(e)}")
        
        # Verificar estructura de tabla
        table_valid, table_error = check_table_structure()
        status["table_structure"] = table_valid
        if not table_valid:
            status["errors"].append(f"Error en estructura de tabla: {table_error}")
        
        # Verificar tablas requeridas
        required_tables = ["pedidos", "pagadores", "configuracion", "clientes"]
        for table in required_tables:
            try:
                test_query = supabase.table(table).select("*").limit(1).execute()
                status["required_tables"][table] = True
            except Exception as e:
                status["required_tables"][table] = False
                status["errors"].append(f"Error en tabla {table}: {str(e)}")
        
        # Verificar valores de configuración
        try:
            config_response = supabase.table("configuracion").select("clave, valor").in_("clave", ["tasa_banesco", "tasa_venezuela", "tasa_otros"]).execute()
            if config_response.data:
                for config in config_response.data:
                    status["config_values"][config["clave"]] = config["valor"]
        except Exception as e:
            status["errors"].append(f"Error al obtener configuración: {str(e)}")
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"Error en system_status: {e}")
        return jsonify({
            "error": str(e),
            "database_connection": False,
            "table_structure": False,
            "required_tables": {},
            "config_values": {},
            "errors": [str(e)]
        })

# -----------------------------------------------------------------------------
# Funciones de validación y utilidades
# -----------------------------------------------------------------------------

def validate_pedido_data(cliente, brs, tasa, fecha):
    """
    Valida los datos de un pedido antes de insertar
    Args:
        cliente: Nombre del cliente
        brs: Valor BRS
        tasa: Tasa de cambio
        fecha: Fecha del pedido
    Returns: 
        tuple: (is_valid, error_message)
    """
    # Validar cliente
    if not cliente or not cliente.strip():
        return False, "El campo Cliente es obligatorio."
    
    # Validar BRS
    if brs <= 0:
        return False, "El BRS debe ser mayor a 0."
    
    # Validar tasa
    if tasa <= 0:
        return False, "La tasa debe ser mayor a 0."
    
    # Validar fecha
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return False, "Formato de fecha inválido. Use YYYY-MM-DD."
    
    # Validar que la fecha no sea futura
    fecha_pedido = datetime.strptime(fecha, "%Y-%m-%d").date()
    fecha_actual = adjust_datetime(datetime.now(chile_tz)).date()
    if fecha_pedido > fecha_actual:
        return False, "La fecha del pedido no puede ser futura."
    
    # Validar CLP máximo del cliente
    try:
        cliente_normalizado = cliente.strip().lower()
        response = supabase.table("clientes").select("clp_maximo").eq("cliente", cliente).execute()
        
        if response.data:
            clp_maximo = response.data[0].get("clp_maximo", 0)
            if clp_maximo > 0:
                clp_calculado = brs / tasa
                if clp_calculado > clp_maximo:
                    return False, f"El CLP calculado ({clp_calculado:,.0f}) excede el límite del cliente ({clp_maximo:,.0f})."
    except Exception as e:
        logging.warning(f"Error al validar CLP máximo para cliente {cliente}: {e}")
        # No fallar la validación si hay error al consultar CLP máximo
    
    return True, ""

def sanitize_input(data):
    """
    Sanitiza los datos de entrada para prevenir inyección de código
    Args:
        data: Datos a sanitizar
    Returns:
        str: Datos sanitizados
    """
    if isinstance(data, str):
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '/']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    return str(data).strip() if data else ""

def check_table_structure():
    """
    Verifica que la tabla pedidos tenga la estructura correcta
    Returns: (is_valid, error_message)
    """
    try:
        # Intentar una consulta simple para verificar la estructura
        test_query = supabase.table("pedidos").select("id, cliente, fecha, brs, tasa, clp, usuario, eliminado").limit(1).execute()
        
        if test_query.data is None:
            return False, "No se pudo acceder a la tabla pedidos"
        
        # Verificar que los campos requeridos para inserción existan
        # Nota: clp es una columna generada, no se inserta manualmente
        required_fields = ["id", "cliente", "fecha", "brs", "tasa", "usuario", "eliminado"]
        if test_query.data:
            available_fields = list(test_query.data[0].keys())
            missing_fields = [field for field in required_fields if field not in available_fields]
            if missing_fields:
                return False, f"Campos faltantes en la tabla: {', '.join(missing_fields)}"
        
        return True, "Estructura de tabla válida"
        
    except Exception as e:
        logging.error(f"Error al verificar estructura de tabla: {e}")
        return False, f"Error al verificar estructura: {str(e)}" 