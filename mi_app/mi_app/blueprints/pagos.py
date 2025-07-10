from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from supabase import create_client
import os
from datetime import datetime, timedelta
import logging
import pytz
from functools import wraps

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurar zona horaria de Chile
chile_tz = pytz.timezone('America/Santiago')

pagos_bp = Blueprint("pagos", __name__, template_folder="../templates/pagos")

# Decorador login_required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Helper para validar duplicados de pagos
def validar_pago_duplicado(cliente, monto_float, fecha_hora, pago_id=None):
    advertir = False
    cliente_duplicado = None
    mensaje_advertencia = None
    fecha_busqueda = datetime.strptime(fecha_hora[:10], "%Y-%m-%d")
    fecha_inicio = (fecha_busqueda - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
    fecha_fin = fecha_busqueda.strftime("%Y-%m-%dT23:59:59")
    query_dup = supabase.table("pagos_realizados").select("id, cliente, monto_total, fecha_registro, eliminado") \
        .eq("eliminado", False) \
        .gte("fecha_registro", fecha_inicio) \
        .lte("fecha_registro", fecha_fin) \
        .eq("monto_total", monto_float)
    pagos_duplicados = query_dup.execute().data or []
    if pago_id is not None:
        pagos_duplicados = [p for p in pagos_duplicados if p["id"] != pago_id]
    if monto_float > 500000:
        monto_formateado = f"{monto_float:,.0f}".replace(",", ".")
        if pagos_duplicados:
            advertir = True
            cliente_duplicado = pagos_duplicados[0]["cliente"]
            mensaje_advertencia = f"Ya existe un pago registrado por el cliente <b>{cliente_duplicado}</b> con este monto (<b>${monto_formateado}</b>) en el último día.<br>¿Deseas continuar de todos modos?"
        else:
            advertir = True
            mensaje_advertencia = f"Estás ingresando un pago de alto valor: <b>${monto_formateado}</b>.<br>¿Deseas continuar de todos modos?"
    elif monto_float % 100000 == 0 or monto_float % 10000 == 0:
        for p in pagos_duplicados:
            if p["cliente"] == cliente:
                advertir = True
                cliente_duplicado = p["cliente"]
                monto_formateado = f"{monto_float:,.0f}".replace(",", ".")
                mensaje_advertencia = f"Ya existe un pago registrado por el cliente <b>{cliente_duplicado}</b> con este monto (<b>${monto_formateado}</b>) en el último día.<br>¿Deseas continuar de todos modos?"
                break
    else:
        for p in pagos_duplicados:
            if p["cliente"] == cliente:
                advertir = True
                cliente_duplicado = p["cliente"]
                monto_formateado = f"{monto_float:,.0f}".replace(",", ".")
                mensaje_advertencia = f"Ya existe un pago registrado por el cliente <b>{cliente_duplicado}</b> con este monto (<b>${monto_formateado}</b>) en el último día.<br>¿Deseas continuar de todos modos?"
                break
    return advertir, cliente_duplicado, mensaje_advertencia

@pagos_bp.route("/")
@login_required
def index():
    try:
        # Obtener clientes ÚNICOS que ya tienen pagos registrados (no eliminados)
        response_clientes = supabase.table("pagos_realizados").select("cliente").eq("eliminado", False).execute()
        clientes = sorted({p["cliente"] for p in response_clientes.data if p.get("cliente")}) if response_clientes.data else []
        # Filtros
        query = supabase.table("pagos_realizados").select("id, cliente, monto_total, fecha_registro, eliminado")
        cliente = request.args.get("cliente")
        if cliente:
            query = query.eq("cliente", cliente)
        fecha = request.args.get("fecha")
        if not fecha:
            fecha = datetime.now(chile_tz).strftime("%Y-%m-%d")
        if fecha:
            inicio = f"{fecha}T00:00:00"
            fin = f"{fecha}T23:59:59"
            query = query.gte("fecha_registro", inicio).lte("fecha_registro", fin)
        clp = request.args.get("clp", "").replace(".", "").strip()
        if clp:
            try:
                query = query.eq("monto_total", float(clp))
            except ValueError:
                pass
        # Filtrar pagos no eliminados
        query = query.eq("eliminado", False)
        response = query.order("fecha_registro", desc=True).execute()
        pagos = response.data if response.data else []
        return render_template("pagos/index.html", active_page="pagos", pagos=pagos, clientes=clientes)
    except Exception as e:
        logging.error(f"Error en index de pagos: {e}")
        flash("Error al cargar los pagos.")
        return render_template("pagos/index.html", active_page="pagos", pagos=[], clientes=[])

@pagos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    try:
        # Obtener clientes para el select
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        clientes = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []
        
        if request.method == "POST":
            cliente = request.form.get("cliente")
            monto = request.form.get("monto")
            fecha = request.form.get("fecha")
            
            if not cliente or not monto:
                flash("Cliente y monto son obligatorios.")
                return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes)
            
            try:
                monto_float = float(monto)
                # Permitir montos negativos para puesta en marcha
                if monto_float == 0:
                    flash("El monto no puede ser cero.")
                    return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes)
            except ValueError:
                flash("El monto debe ser un número válido.")
                return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes)
            
            # Crear fecha y hora completa
            if fecha:
                # Si se especifica fecha, usar esa fecha con la hora actual de Chile
                fecha_hora = f"{fecha}T{datetime.now(chile_tz).strftime('%H:%M:%S')}"
            else:
                # Si no se especifica fecha, usar fecha y hora actual de Chile
                fecha_hora = datetime.now(chile_tz).strftime("%Y-%m-%dT%H:%M:%S")
            
            # Validación de duplicados antes de guardar (solo para montos positivos)
            if not request.form.get("forzar_guardado") and monto_float > 0:  # Solo validar si no viene de la confirmación y es positivo
                advertir, cliente_duplicado, mensaje_advertencia = validar_pago_duplicado(cliente, monto_float, fecha_hora)
                if advertir:
                    return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes, advertencia_duplicado=True, cliente_duplicado=cliente_duplicado, mensaje_advertencia=mensaje_advertencia, cliente=cliente, monto=monto, fecha=fecha)
            
            # Guardar en pagos_realizados
            result = supabase.table("pagos_realizados").insert({
                "cliente": cliente,
                "monto_total": monto_float,
                "fecha_registro": fecha_hora
            }).execute()
            
            if result.data:
                # Guardar el cliente en la sesión para el próximo ingreso
                session['ultimo_cliente_pagos'] = cliente
                
                # Mensaje diferenciado para pagos negativos
                if monto_float < 0:
                    flash(f"Pago negativo registrado correctamente: {monto_float:,.0f} CLP", "warning")
                else:
                    flash("Pago registrado correctamente.")
                    
                return redirect(url_for("pagos.nuevo"))
            else:
                flash("Error al guardar el pago.")
                
        # Obtener fecha de hoy para el formulario (hora de Chile)
        today_date = datetime.now(chile_tz).strftime("%Y-%m-%d")
        # Si hay POST y se vuelve a mostrar el formulario, mantener la fecha seleccionada
        fecha_form = request.form.get("fecha") if request.method == "POST" else today_date
        
        # Obtener el último cliente de la sesión para preseleccionarlo
        ultimo_cliente = session.get('ultimo_cliente_pagos', '')
        
        return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes, today_date=today_date, fecha_form=fecha_form, ultimo_cliente=ultimo_cliente)
    except Exception as e:
        logging.error(f"Error en nuevo pago: {e}")
        flash(f"Error al procesar el pago: {str(e)}")
        today_date = datetime.now(chile_tz).strftime("%Y-%m-%d")
        ultimo_cliente = session.get('ultimo_cliente_pagos', '')
        return render_template("pagos/nuevo.html", active_page="pagos", clientes=clientes, today_date=today_date, ultimo_cliente=ultimo_cliente)

@pagos_bp.route("/editar/<int:pago_id>", methods=["GET", "POST"])
@login_required
def editar(pago_id):
    try:
        # Obtener el pago actual
        pago_resp = supabase.table("pagos_realizados").select("id, cliente, monto_total, fecha_registro").eq("id", pago_id).single().execute()
        pago = pago_resp.data if pago_resp.data else None
        if not pago:
            flash("Pago no encontrado.")
            return redirect(url_for("pagos.index"))

        # Obtener clientes para el select
        response_pagadores = supabase.table("pagadores").select("cliente").execute()
        clientes = [p["cliente"] for p in response_pagadores.data] if response_pagadores.data else []

        # Obtener historial de modificaciones
        historial_resp = supabase.table("pagos_historial").select("*").eq("pago_id", pago_id).order("fecha_modificacion", desc=True).execute()
        historial = historial_resp.data if historial_resp.data else []

        if request.method == "POST":
            nuevo_cliente = request.form.get("cliente")
            nuevo_monto = request.form.get("monto")
            nueva_fecha = request.form.get("fecha")
            usuario = session.get("email", "desconocido")
            ahora = datetime.now(chile_tz).isoformat()
            cambios = []

            # Validación de duplicados antes de guardar (solo para montos positivos)
            if not request.form.get("forzar_guardado"):  # Solo validar si no viene de la confirmación
                try:
                    nuevo_monto_float = float(nuevo_monto)
                    # Permitir montos negativos para puesta en marcha
                    if nuevo_monto_float == 0:
                        flash("El monto no puede ser cero.")
                        return render_template("pagos/editar.html", pago=pago, clientes=clientes, historial=historial, fecha_form=nueva_fecha)
                except ValueError:
                    flash("El monto debe ser un número válido.")
                    return render_template("pagos/editar.html", pago=pago, clientes=clientes, historial=historial, fecha_form=nueva_fecha)
                
                # Solo validar duplicados para montos positivos
                if nuevo_monto_float > 0:
                    # Determinar la fecha a usar
                    if nueva_fecha:
                        fecha_hora = f"{nueva_fecha}T{datetime.now(chile_tz).strftime('%H:%M:%S')}"
                    else:
                        fecha_hora = datetime.now(chile_tz).strftime("%Y-%m-%dT%H:%M:%S")
                    advertir, cliente_duplicado, mensaje_advertencia = validar_pago_duplicado(nuevo_cliente, nuevo_monto_float, fecha_hora, pago_id=pago_id)
                    if advertir:
                        return render_template("pagos/editar.html", pago=pago, clientes=clientes, historial=historial, fecha_form=nueva_fecha, advertencia_duplicado=True, cliente_duplicado=cliente_duplicado, mensaje_advertencia=mensaje_advertencia, cliente=nuevo_cliente, monto=nuevo_monto, fecha=nueva_fecha)

            # Comparar y registrar cambios
            if nuevo_cliente != pago["cliente"]:
                cambios.append({
                    "campo_modificado": "cliente",
                    "valor_anterior": pago["cliente"],
                    "valor_nuevo": nuevo_cliente
                })
            if float(nuevo_monto) != float(pago["monto_total"]):
                cambios.append({
                    "campo_modificado": "monto_total",
                    "valor_anterior": pago["monto_total"],
                    "valor_nuevo": nuevo_monto
                })
            # Solo cambiar la fecha si el usuario la cambió manualmente
            fecha_registro_original = pago["fecha_registro"]
            fecha_original = fecha_registro_original[:10] if fecha_registro_original else ""
            hora_original = fecha_registro_original[11:19] if fecha_registro_original and len(fecha_registro_original) >= 19 else "00:00:00"
            if nueva_fecha and nueva_fecha != fecha_original:
                nueva_fecha_registro = f"{nueva_fecha}T{hora_original}"
                cambios.append({
                    "campo_modificado": "fecha_registro",
                    "valor_anterior": fecha_registro_original,
                    "valor_nuevo": nueva_fecha_registro
                })
            else:
                nueva_fecha_registro = fecha_registro_original

            # Actualizar el pago
            supabase.table("pagos_realizados").update({
                "cliente": nuevo_cliente,
                "monto_total": float(nuevo_monto),
                "fecha_registro": nueva_fecha_registro
            }).eq("id", pago_id).execute()

            # Guardar en historial (siempre, aunque no haya cambios)
            if not cambios:
                cambios.append({
                    "campo_modificado": "sin_cambios",
                    "valor_anterior": "-",
                    "valor_nuevo": "-"
                })
            for cambio in cambios:
                supabase.table("pagos_historial").insert({
                    "pago_id": pago_id,
                    "fecha_modificacion": ahora,
                    "usuario": usuario,
                    "campo_modificado": cambio["campo_modificado"],
                    "valor_anterior": str(cambio["valor_anterior"]),
                    "valor_nuevo": str(cambio["valor_nuevo"]),
                    "comentario": "Edición de pago"
                }).execute()

            flash("Pago editado y registrado en historial.")
            return redirect(url_for("pagos.editar", pago_id=pago_id))

        # Para el formulario, extraer solo la fecha (YYYY-MM-DD)
        fecha_form = pago["fecha_registro"][:10] if pago["fecha_registro"] else ""
        return render_template("pagos/editar.html", pago=pago, clientes=clientes, historial=historial, fecha_form=fecha_form)
    except Exception as e:
        logging.error(f"Error al editar pago: {e}")
        flash(f"Error al editar el pago: {str(e)}")
        return redirect(url_for("pagos.index"))

@pagos_bp.route("/eliminar/<int:pago_id>", methods=["POST"])
@login_required
def eliminar(pago_id):
    try:
        print(f"[DEBUG] Eliminando pago con ID: {pago_id}")
        usuario = session.get("email", "desconocido")
        ahora = datetime.now(chile_tz).isoformat()
        # Solo marcar como eliminado, sin tocar fecha_registro ni otros campos
        result = supabase.table("pagos_realizados").update({"eliminado": True}).eq("id", pago_id).execute()
        print(f"[DEBUG] Resultado del update en Supabase: {result}")
        # Eliminar también la relación en transferencias_pagos
        supabase.table("transferencias_pagos").delete().eq("pago_id", pago_id).execute()
        # Registrar en historial
        supabase.table("pagos_historial").insert({
            "pago_id": pago_id,
            "fecha_modificacion": ahora,
            "usuario": usuario,
            "campo_modificado": "eliminado",
            "valor_anterior": "False",
            "valor_nuevo": "True",
            "comentario": "Pago marcado como eliminado"
        }).execute()
        flash("Pago eliminado (borrado lógico).")
    except Exception as e:
        logging.error(f"Error al eliminar pago: {e}")
        flash(f"Error al eliminar el pago: {str(e)}")
    return redirect(url_for("pagos.index")) 