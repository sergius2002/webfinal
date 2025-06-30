from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, render_template_string
from supabase import create_client
import os
import re
from mi_app.mi_app.extensions import cache, user_allowed
import secrets
from postgrest.exceptions import APIError
import logging
import time
import pytz

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

clientes_bp = Blueprint("clientes", __name__, template_folder="../templates/clientes")

# Caché simple para mejorar rendimiento
_clientes_cache = {}
_cache_timestamp = 0
CACHE_DURATION = 30  # segundos

chile_tz = pytz.timezone('America/Santiago')

def get_cached_clientes():
    """Obtiene clientes del caché si está válido, sino de la base de datos"""
    global _clientes_cache, _cache_timestamp
    current_time = time.time()
    
    # Si el caché es válido, retornarlo
    if current_time - _cache_timestamp < CACHE_DURATION and _clientes_cache:
        return _clientes_cache
    
    # Si no, obtener de la base de datos
    try:
        response = supabase.table("clientes").select("id, cliente, clp_maximo").order("cliente").execute()
        clientes = response.data if response.data else []
        
        # Obtener todos los pedidos en una sola consulta
        pedidos_resp = supabase.table("pedidos").select("cliente, clp").eq("eliminado", False).execute()
        pedidos = pedidos_resp.data if pedidos_resp.data else []

        # Obtener todos los pagos en una sola consulta
        pagos_resp = supabase.table("pagos_realizados").select("cliente, monto_total, eliminado").eq("eliminado", False).execute()
        pagos = pagos_resp.data if pagos_resp.data else []
        
        # Crear diccionario cliente -> suma de CLP (pedidos)
        clp_por_cliente = {}
        for pedido in pedidos:
            cliente = pedido.get("cliente")
            clp = float(pedido.get("clp", 0))
            if cliente:
                if cliente not in clp_por_cliente:
                    clp_por_cliente[cliente] = 0
                clp_por_cliente[cliente] += clp

        # Crear diccionario cliente -> suma de pagos realizados
        pagos_por_cliente = {}
        for pago in pagos:
            cliente = pago.get("cliente")
            monto = float(pago.get("monto_total", 0))
            if cliente:
                if cliente not in pagos_por_cliente:
                    pagos_por_cliente[cliente] = 0
                pagos_por_cliente[cliente] += monto
        
        # Obtener pagadores en una sola consulta
        pagador_fields = [f"pagador{i}" for i in range(1, 201)]
        select_fields = ["id", "cliente"] + pagador_fields
        select_str = ", ".join(select_fields)
        pagadores_resp = supabase.table("pagadores").select(select_str).execute()
        pagadores = pagadores_resp.data if pagadores_resp.data else []
        
        # Construir diccionario cliente -> set de RUTs únicos
        cliente_ruts = {}
        for p in pagadores:
            cli = p.get("cliente")
            if not cli:
                continue
            if cli not in cliente_ruts:
                cliente_ruts[cli] = set()
            for key in pagador_fields:
                rut = p.get(key)
                if rut and rut != "EMPTY":
                    cliente_ruts[cli].add(rut)
        
        # Procesar cada cliente
        for cliente in clientes:
            clp_total = clp_por_cliente.get(cliente["cliente"], 0)
            pagos_total = pagos_por_cliente.get(cliente["cliente"], 0)
            saldo_final = clp_total - pagos_total
            cliente["clp_total"] = clp_total
            cliente["pagos_total"] = pagos_total
            cliente["saldo_final"] = saldo_final
            clp_maximo = float(cliente.get("clp_maximo", 0))
            cliente["disponible"] = clp_maximo - saldo_final
            
            # Determinar si ha superado el límite
            if clp_maximo > 0:
                cliente["supera_limite"] = saldo_final > clp_maximo
                cliente["exceso"] = saldo_final - clp_maximo if saldo_final > clp_maximo else 0
            else:
                cliente["supera_limite"] = False
                cliente["exceso"] = 0
            
            # Asignar total de pagadores
            cliente["total_pagadores"] = len(cliente_ruts.get(cliente["cliente"], set()))
        
        # Actualizar caché
        _clientes_cache = clientes
        _cache_timestamp = current_time
        
        return clientes
        
    except Exception as e:
        logging.error(f"Error al obtener clientes: {e}")
        return []

def clear_clientes_cache():
    """Limpia el caché de clientes"""
    global _clientes_cache, _cache_timestamp
    _clientes_cache = {}
    _cache_timestamp = 0

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def calcular_digito_verificador(numero):
    """Calcula el dígito verificador usando el algoritmo módulo 11 (oficial chileno)"""
    suma = 0
    multiplicador = 2
    for d in reversed(numero):
        suma += int(d) * multiplicador
        multiplicador += 1
        if multiplicador > 7:
            multiplicador = 2
    resto = suma % 11
    dv = 11 - resto
    if dv == 11:
        return '0'
    elif dv == 10:
        return 'K'
    else:
        return str(dv)

def normalizar_y_validar_rut(rut):
    """Normaliza y valida un RUT chileno"""
    # Eliminar espacios, puntos y guiones
    rut_limpiado = re.sub(r'[\s\.\-]', '', rut)
    
    # Verificar que solo contenga números y posiblemente una K al final
    if not re.match(r'^[0-9]+[0-9kK]?$', rut_limpiado):
        return {'valido': False, 'error': 'El RUT solo puede contener números y una K al final'}
    
    # Separar número y dígito verificador
    if len(rut_limpiado) < 2:
        return {'valido': False, 'error': 'RUT demasiado corto'}
    
    # Si termina en K, separar
    if rut_limpiado[-1].upper() == 'K':
        numero = rut_limpiado[:-1]
        dv = 'K'
    else:
        # Si no termina en K, el último dígito es el verificador
        numero = rut_limpiado[:-1]
        dv = rut_limpiado[-1]
    
    # Verificar que el número tenga entre 7 y 8 dígitos
    if len(numero) < 7 or len(numero) > 8:
        return {'valido': False, 'error': 'El número del RUT debe tener entre 7 y 8 dígitos'}
    
    # Verificar que el número no exceda 99999999
    if int(numero) > 99999999:
        return {'valido': False, 'error': 'El número del RUT no puede exceder 99999999'}
    
    # Si no se proporcionó dígito verificador, calcularlo
    if not dv:
        dv_calculado = calcular_digito_verificador(numero)
        return {
            'valido': True,
            'rut_normalizado': f"{numero}-{dv_calculado}",
            'mensaje': f'Dígito verificador calculado: {dv_calculado}'
        }
    
    # Verificar que el dígito verificador sea correcto
    dv_calculado = calcular_digito_verificador(numero)
    if dv.upper() != dv_calculado:
        return {
            'valido': False,
            'error': f'Dígito verificador incorrecto. Debería ser: {dv_calculado}'
        }
    
    return {
        'valido': True,
        'rut_normalizado': f"{numero}-{dv.upper()}"
    }

@clientes_bp.route("/")
@login_required
@user_allowed
def index():
    clientes = get_cached_clientes()
    return render_template("clientes/index.html", clientes=clientes, active_page="clientes")

@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@user_allowed
def nuevo():
    if request.method == "POST":
        cliente = request.form.get("cliente")
        clp_maximo = request.form.get("clp_maximo", "0")
        
        if not cliente:
            flash("El nombre es obligatorio.")
            return render_template("clientes/nuevo.html")
        
        # Convertir clp_maximo a float, manejar valores vacíos
        try:
            clp_maximo_float = float(clp_maximo) if clp_maximo else 0.0
        except ValueError:
            clp_maximo_float = 0.0
        
        supabase.table("clientes").insert({
            "cliente": cliente,
            "clp_maximo": clp_maximo_float
        }).execute()
        
        # Limpiar caché después de crear nuevo cliente
        clear_clientes_cache()
        
        flash("Cliente creado con éxito.")
        return redirect(url_for("clientes.index"))
    return render_template("clientes/nuevo.html")

@clientes_bp.route("/editar/<int:cliente_id>", methods=["GET", "POST"])
@login_required
@user_allowed
def editar(cliente_id):
    response = supabase.table("clientes").select("id, cliente, clp_maximo").eq("id", cliente_id).single().execute()
    cliente = response.data if response.data else None
    if not cliente:
        flash("Cliente no encontrado.")
        return redirect(url_for("clientes.index"))
    if request.method == "POST":
        cliente_nuevo = request.form.get("cliente")
        clp_maximo = request.form.get("clp_maximo", "0")
        
        if not cliente_nuevo:
            flash("El nombre es obligatorio.")
            return render_template("clientes/editar.html", cliente=cliente)
        
        # Convertir clp_maximo a float, manejar valores vacíos
        try:
            clp_maximo_float = float(clp_maximo) if clp_maximo else 0.0
        except ValueError:
            clp_maximo_float = 0.0
        
        supabase.table("clientes").update({
            "cliente": cliente_nuevo,
            "clp_maximo": clp_maximo_float
        }).eq("id", cliente_id).execute()
        
        # Limpiar caché después de editar cliente
        clear_clientes_cache()
        
        flash("Cliente actualizado.")
        return redirect(url_for("clientes.index"))
    return render_template("clientes/editar.html", cliente=cliente)

@clientes_bp.route("/detalle/<int:cliente_id>")
@login_required
@user_allowed
def detalle(cliente_id):
    response = supabase.table("clientes").select("id, cliente").eq("id", cliente_id).single().execute()
    cliente = response.data if response.data else None
    if not cliente:
        flash("Cliente no encontrado.")
        return redirect(url_for("clientes.index"))
    # Construir lista de campos pagador1 a pagador200
    pagador_fields = [f"pagador{i}" for i in range(1, 201)]
    select_fields = ["id", "cliente"] + pagador_fields
    select_str = ", ".join(select_fields)
    pagadores_resp = supabase.table("pagadores").select(select_str).eq("cliente", cliente["cliente"]).execute()
    pagadores = pagadores_resp.data if pagadores_resp.data else []
    # Construir una lista de RUTs únicos para mostrar
    ruts = []
    for p in pagadores:
        for key in pagador_fields:
            rut = p.get(key)
            if rut and rut != "EMPTY" and rut not in ruts:
                ruts.append(rut)
    return render_template("clientes/detalle.html", cliente=cliente, ruts=ruts)

@clientes_bp.route("/agregar_pagador/<int:cliente_id>", methods=["POST"])
@login_required
@user_allowed
def agregar_pagador(cliente_id):
    try:
        data = request.get_json()
        rut = data.get("rut")
        
        if not rut:
            return jsonify({"success": False, "error": "RUT es obligatorio"})
        
        # Validar y normalizar el RUT
        resultado_validacion = normalizar_y_validar_rut(rut)
        if not resultado_validacion['valido']:
            return jsonify({"success": False, "error": resultado_validacion['error']})
        
        # Usar el RUT normalizado
        rut_normalizado = resultado_validacion['rut_normalizado']
        
        # Obtener el cliente
        cliente_resp = supabase.table("clientes").select("cliente").eq("id", cliente_id).single().execute()
        if not cliente_resp.data:
            return jsonify({"success": False, "error": "Cliente no encontrado"})
        
        cliente_nombre = cliente_resp.data["cliente"]
        
        # Verificar si ya existe un registro para este cliente en la tabla pagadores
        pagador_fields = [f"pagador{i}" for i in range(1, 201)]
        select_fields = ["id"] + pagador_fields
        select_str = ", ".join(select_fields)
        
        pagadores_resp = supabase.table("pagadores").select(select_str).eq("cliente", cliente_nombre).execute()
        
        if pagadores_resp.data:
            # Buscar la primera columna vacía
            registro = pagadores_resp.data[0]
            columna_vacia = None
            
            for field in pagador_fields:
                valor = registro.get(field)
                if not valor or valor == "" or valor == "EMPTY":
                    columna_vacia = field
                    break
            
            if not columna_vacia:
                return jsonify({"success": False, "error": "No hay columnas disponibles. El cliente ya tiene 200 pagadores."})
            
            # Actualizar registro existente en la primera columna vacía
            update_data = {columna_vacia: rut_normalizado}
            supabase.table("pagadores").update(update_data).eq("cliente", cliente_nombre).execute()
        else:
            # Crear nuevo registro con el pagador en la primera columna
            insert_data = {"cliente": cliente_nombre, "pagador1": rut_normalizado}
            supabase.table("pagadores").insert(insert_data).execute()
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@clientes_bp.route("/eliminar_pagador/<int:cliente_id>", methods=["POST"])
@login_required
@user_allowed
def eliminar_pagador(cliente_id):
    try:
        data = request.get_json()
        rut = data.get("rut")
        
        if not rut:
            return jsonify({"success": False, "error": "RUT es obligatorio"})
        
        # Obtener el cliente
        cliente_resp = supabase.table("clientes").select("cliente").eq("id", cliente_id).single().execute()
        if not cliente_resp.data:
            return jsonify({"success": False, "error": "Cliente no encontrado"})
        
        cliente_nombre = cliente_resp.data["cliente"]
        
        # Buscar en qué columna está el RUT
        pagador_fields = [f"pagador{i}" for i in range(1, 201)]
        select_fields = ["id"] + pagador_fields
        select_str = ", ".join(select_fields)
        
        pagadores_resp = supabase.table("pagadores").select(select_str).eq("cliente", cliente_nombre).execute()
        
        if not pagadores_resp.data:
            return jsonify({"success": False, "error": "No se encontraron pagadores para este cliente"})
        
        # Encontrar la columna donde está el RUT
        columna_encontrada = None
        for p in pagadores_resp.data:
            for field in pagador_fields:
                if p.get(field) == rut:
                    columna_encontrada = field
                    break
            if columna_encontrada:
                break
        
        if not columna_encontrada:
            return jsonify({"success": False, "error": "RUT no encontrado en este cliente"})
        
        # Eliminar el RUT de la columna (poner NULL o vacío)
        update_data = {columna_encontrada: None}
        supabase.table("pagadores").update(update_data).eq("cliente", cliente_nombre).execute()
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@clientes_bp.route("/eliminar/<int:cliente_id>", methods=["POST"])
@login_required
@user_allowed
def eliminar(cliente_id):
    supabase.table("clientes").delete().eq("id", cliente_id).execute()
    
    # Limpiar caché después de eliminar cliente
    clear_clientes_cache()
    
    flash("Cliente eliminado.")
    return redirect(url_for("clientes.index"))

@clientes_bp.route("/link_pagador/<int:cliente_id>")
@login_required
@user_allowed
def link_pagador(cliente_id):
    try:
        # Obtener el cliente
        cliente_resp = supabase.table("clientes").select("id, cliente, token_link_pagador").eq("id", cliente_id).single().execute()
        if not cliente_resp.data:
            return jsonify({"success": False, "error": "Cliente no encontrado"})
        cliente = cliente_resp.data
        token = cliente.get("token_link_pagador")
        # Si no existe token, generarlo y guardarlo
        if not token:
            token = secrets.token_urlsafe(16)
            supabase.table("clientes").update({"token_link_pagador": token}).eq("id", cliente_id).execute()
        # Construir el link
        base_url = request.host_url.rstrip('/')
        link = f"{base_url}/clientes/agregar-pagador/{token}"
        return jsonify({"success": True, "link": link})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Ruta pública para que los clientes agreguen pagadores usando un token
# Esta ruta es intencionalmente pública pero tiene validación de token
@clientes_bp.route('/agregar-pagador/<token>', methods=['GET', 'POST'])
def agregar_pagador_publico(token):
    # Validar que el token tenga el formato correcto (seguridad adicional)
    if not token or len(token) < 16:
        return render_template_string("""
        <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
        <div class='container d-flex justify-content-center align-items-center' style='min-height:100vh;'>
            <div class='card shadow p-4' style='max-width:400px;'>
                <h3 class='mb-3 text-center'>Enlace inválido</h3>
                <p class='text-center'>El enlace no es válido o ha expirado.</p>
            </div>
        </div>
        """)
    
    # Buscar cliente por token
    cliente_resp = supabase.table("clientes").select("id, cliente").eq("token_link_pagador", token).single().execute()
    if not cliente_resp.data:
        return render_template_string("""
        <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
        <div class='container d-flex justify-content-center align-items-center' style='min-height:100vh;'>
            <div class='card shadow p-4' style='max-width:400px;'>
                <h3 class='mb-3 text-center'>Enlace inválido</h3>
                <p class='text-center'>El enlace no es válido o ha expirado.</p>
            </div>
        </div>
        """)
    cliente = cliente_resp.data
    mensaje = None
    error = None
    if request.method == 'POST':
        rut = request.form.get('rut', '').strip()
        resultado = normalizar_y_validar_rut(rut)
        if not resultado['valido']:
            error = resultado['error']
        else:
            rut_normalizado = resultado['rut_normalizado']
            # Buscar pagadores
            pagador_fields = [f"pagador{i}" for i in range(1, 201)]
            select_fields = ["id"] + pagador_fields
            select_str = ", ".join(select_fields)
            pagadores_resp = supabase.table("pagadores").select(select_str).eq("cliente", cliente["cliente"]).execute()
            if pagadores_resp.data:
                registro = pagadores_resp.data[0]
                columna_vacia = None
                for field in pagador_fields:
                    valor = registro.get(field)
                    if not valor or valor == "" or valor == "EMPTY":
                        columna_vacia = field
                        break
                if not columna_vacia:
                    error = "No hay columnas disponibles. El cliente ya tiene 200 pagadores."
                else:
                    try:
                        supabase.table("pagadores").update({columna_vacia: rut_normalizado}).eq("cliente", cliente["cliente"]).execute()
                        mensaje = f"Pagador {rut_normalizado} agregado con éxito."
                    except APIError as e:
                        msg = getattr(e, 'message', None)
                        if not msg and hasattr(e, 'args') and e.args:
                            try:
                                import ast
                                err_dict = ast.literal_eval(e.args[0]) if isinstance(e.args[0], str) else e.args[0]
                                msg = err_dict.get('message', str(e))
                            except Exception:
                                msg = str(e)
                        if msg and 'ya está asociado al cliente' in msg:
                            error = "RUT ya registrado por otro cliente"
                        elif msg and 'duplicad' in msg.lower():
                            error = "RUT duplicado"
                        else:
                            error = msg or str(e)
            else:
                try:
                    supabase.table("pagadores").insert({"cliente": cliente["cliente"], "pagador1": rut_normalizado}).execute()
                    mensaje = f"Pagador {rut_normalizado} agregado con éxito."
                except APIError as e:
                    msg = getattr(e, 'message', None)
                    if not msg and hasattr(e, 'args') and e.args:
                        try:
                            import ast
                            err_dict = ast.literal_eval(e.args[0]) if isinstance(e.args[0], str) else e.args[0]
                            msg = err_dict.get('message', str(e))
                        except Exception:
                            msg = str(e)
                    if msg and 'ya está asociado al cliente' in msg:
                        error = "RUT ya registrado por otro cliente"
                    elif msg and 'duplicad' in msg.lower():
                        error = "RUT duplicado"
                    else:
                        error = msg or str(e)
    return render_template_string("""
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css' rel='stylesheet'>
    <div class='container d-flex justify-content-center align-items-center' style='min-height:100vh;'>
      <div class='card shadow p-4' style='max-width:400px;width:100%;'>
        <h3 class='mb-3 text-center'>Agregar pagador para <b>{{cliente}}</b></h3>
        <form method='post' autocomplete='off' id='formAgregarPagador'>
          <div class='mb-3'>
            <label for='rut' class='form-label'>RUT del pagador</label>
            <input type='text' class='form-control form-control-lg' id='rut' name='rut' required autofocus placeholder='Ej: 12345678-9, 26829547K, 26.829.547-K'>
            <div id='rutFeedback' class='invalid-feedback'></div>
          </div>
          {% if mensaje %}
          <div class='alert alert-success text-center'>{{mensaje}}</div>
          {% endif %}
          {% if error %}
          <div class='alert alert-danger text-center'>{{error}}</div>
          {% endif %}
          <button type='submit' class='btn btn-primary btn-lg w-100 mt-2' id='btnSubmit'>Agregar pagador</button>
        </form>
      </div>
    </div>
    <script>
    function normalizarYValidarRUT(rut) {
      let rutLimpio = rut.replace(/[\s\.\-]/g, '');
      if (!/^[0-9]+[0-9kK]?$/.test(rutLimpio)) {
        return { valido: false, error: 'El RUT solo puede contener números y una K al final' };
      }
      let numero, dv;
      if (rutLimpio.length === 1) {
        return { valido: false, error: 'RUT demasiado corto' };
      }
      if (rutLimpio.slice(-1).toUpperCase() === 'K') {
        numero = rutLimpio.slice(0, -1);
        dv = 'K';
      } else {
        numero = rutLimpio.slice(0, -1);
        dv = rutLimpio.slice(-1);
      }
      if (numero.length < 7 || numero.length > 8) {
        return { valido: false, error: 'El número del RUT debe tener entre 7 y 8 dígitos' };
      }
      if (parseInt(numero) > 99999999) {
        return { valido: false, error: 'El número del RUT no puede exceder 99999999' };
      }
      if (!dv) {
        dv = calcularDigitoVerificador(numero);
        return { valido: true, rutNormalizado: numero + '-' + dv, mensaje: `Dígito verificador calculado: ${dv}` };
      }
      let dvCalculado = calcularDigitoVerificador(numero);
      if (dv.toUpperCase() !== dvCalculado) {
        return { valido: false, error: `Dígito verificador incorrecto. Debería ser: ${dvCalculado}` };
      }
      return { valido: true, rutNormalizado: numero + '-' + dv.toUpperCase() };
    }
    function calcularDigitoVerificador(numero) {
      let suma = 0;
      let multiplicador = 2;
      for (let i = numero.length - 1; i >= 0; i--) {
        suma += parseInt(numero[i]) * multiplicador;
        multiplicador++;
        if (multiplicador > 7) multiplicador = 2;
      }
      let resto = suma % 11;
      let dv = 11 - resto;
      if (dv === 11) return '0';
      if (dv === 10) return 'K';
      return dv.toString();
    }
    document.addEventListener('DOMContentLoaded', function() {
      const rutInput = document.getElementById('rut');
      const feedback = document.getElementById('rutFeedback');
      const btnSubmit = document.getElementById('btnSubmit');
      rutInput.addEventListener('input', function() {
        const rut = this.value;
        if (rut.length > 0) {
          const resultado = normalizarYValidarRUT(rut);
          this.classList.remove('is-valid', 'is-invalid');
          feedback.textContent = '';
          if (resultado.valido) {
            this.classList.add('is-valid');
            btnSubmit.disabled = false;
            feedback.textContent = resultado.mensaje || 'RUT válido';
            feedback.className = 'valid-feedback';
            if (resultado.rutNormalizado) {
              this.value = resultado.rutNormalizado;
            }
          } else {
            this.classList.add('is-invalid');
            btnSubmit.disabled = true;
            feedback.textContent = resultado.error;
            feedback.className = 'invalid-feedback';
          }
        } else {
          this.classList.remove('is-valid', 'is-invalid');
          feedback.textContent = '';
          btnSubmit.disabled = false;
        }
      });
    });
    </script>
    """, cliente=cliente["cliente"], mensaje=mensaje, error=error)

@clientes_bp.route('/buscar_por_rut', methods=['POST'])
@login_required
@user_allowed
def buscar_por_rut():
    data = request.get_json()
    rut = data.get('rut', '').strip()
    resultado = normalizar_y_validar_rut(rut)
    if not resultado['valido']:
        return jsonify({'success': False, 'error': resultado['error']})
    rut_normalizado = resultado['rut_normalizado']
    pagador_fields = [f"pagador{i}" for i in range(1, 201)]
    select_fields = ["cliente"] + pagador_fields
    select_str = ", ".join(select_fields)
    pagadores_resp = supabase.table("pagadores").select(select_str).execute()
    if not pagadores_resp.data:
        return jsonify({'success': False, 'error': 'No hay datos de pagadores.'})
    clientes_encontrados = set()
    for registro in pagadores_resp.data:
        for field in pagador_fields:
            if registro.get(field) == rut_normalizado:
                clientes_encontrados.add(registro.get('cliente'))
    if clientes_encontrados:
        return jsonify({'success': True, 'clientes': list(clientes_encontrados)})
    else:
        return jsonify({'success': False, 'error': 'No se encontró ningún cliente con ese RUT.'})

@clientes_bp.route("/limpiar-cache", methods=["POST"])
@login_required
@user_allowed
def limpiar_cache():
    """Limpia el caché de clientes manualmente"""
    clear_clientes_cache()
    return jsonify({"success": True, "message": "Caché limpiado correctamente"}) 