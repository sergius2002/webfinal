from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, g
from functools import wraps
import logging
from datetime import datetime
import pytz
from mi_app.extensions import supabase
from mi_app.blueprints.utilidades import adjust_datetime

# Configuración de zona horaria
chile_tz = pytz.timezone('America/Santiago')

cuentas_activas_bp = Blueprint('cuentas_activas', __name__)

def user_allowed(f):
    """Decorador para verificar si el usuario tiene permisos de superusuario"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.get('is_superuser', False):
            flash('No tienes permisos para acceder a esta sección.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@cuentas_activas_bp.route("/")
@user_allowed
def index():
    """Muestra la lista de cuentas activas"""
    try:
        response = supabase.table("cuentas_activas").select("*").order("banco").execute()
        cuentas = response.data if response.data else []
        return render_template("admin/cuentas_activas/index.html", 
                             cuentas=cuentas, 
                             active_page="admin")
    except Exception as e:
        logging.error(f"Error al obtener cuentas activas: {e}")
        flash("Error al cargar las cuentas activas", "error")
        return render_template("admin/cuentas_activas/index.html", 
                             cuentas=[], 
                             active_page="admin")

@cuentas_activas_bp.route("/nuevo", methods=["GET", "POST"])
@user_allowed
def nuevo():
    """Crear una nueva cuenta activa"""
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            banco = request.form.get("banco", "").strip()
            numero_cuenta = request.form.get("numero_cuenta", "").strip()
            cedula = request.form.get("cedula", "").strip()
            nombre_titular = request.form.get("nombre_titular", "").strip()
            pais = request.form.get("pais", "Venezuela").strip()
            activa = True if request.form.get("activa") == "on" else False
            
            # Validaciones
            if not banco:
                flash("El campo Banco es obligatorio", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            if not numero_cuenta:
                flash("El campo Número de Cuenta es obligatorio", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            try:
                numero_cuenta_int = int(numero_cuenta)
            except ValueError:
                flash("El número de cuenta debe ser un número válido", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            if not cedula:
                flash("El campo Cédula es obligatorio", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            if not nombre_titular:
                flash("El campo Nombre del Titular es obligatorio", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            # Verificar si ya existe una cuenta con el mismo número
            existing = supabase.table("cuentas_activas").select("id").eq("numero_cuenta", numero_cuenta_int).execute()
            if existing.data:
                flash("Ya existe una cuenta con ese número", "error")
                return render_template("admin/cuentas_activas/nuevo.html", 
                                     active_page="admin")
            
            # Insertar en la base de datos
            usuario = session.get('email', 'usuario_desconocido')
            result = supabase.table("cuentas_activas").insert({
                "banco": banco,
                "numero_cuenta": numero_cuenta_int,
                "cedula": cedula,
                "nombre_titular": nombre_titular,
                "pais": pais,
                "activa": activa,
                "usuario_creacion": usuario
            }).execute()
            
            if result.data:
                flash("Cuenta activa creada exitosamente", "success")
                return redirect(url_for("cuentas_activas.index"))
            else:
                flash("Error al crear la cuenta activa", "error")
                
        except Exception as e:
            logging.error(f"Error al crear cuenta activa: {e}")
            flash(f"Error al crear la cuenta activa: {str(e)}", "error")
    
    return render_template("admin/cuentas_activas/nuevo.html", 
                         active_page="admin")

@cuentas_activas_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@user_allowed
def editar(id):
    """Editar una cuenta activa existente"""
    try:
        if request.method == "POST":
            # Obtener datos del formulario
            banco = request.form.get("banco", "").strip()
            numero_cuenta = request.form.get("numero_cuenta", "").strip()
            cedula = request.form.get("cedula", "").strip()
            nombre_titular = request.form.get("nombre_titular", "").strip()
            pais = request.form.get("pais", "Venezuela").strip()
            activa = True if request.form.get("activa") == "on" else False
            
            # Validaciones
            if not banco:
                flash("El campo Banco es obligatorio", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            if not numero_cuenta:
                flash("El campo Número de Cuenta es obligatorio", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            try:
                numero_cuenta_int = int(numero_cuenta)
            except ValueError:
                flash("El número de cuenta debe ser un número válido", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            if not cedula:
                flash("El campo Cédula es obligatorio", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            if not nombre_titular:
                flash("El campo Nombre del Titular es obligatorio", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            # Verificar si ya existe otra cuenta con el mismo número (excluyendo la actual)
            existing = supabase.table("cuentas_activas").select("id").eq("numero_cuenta", numero_cuenta_int).neq("id", id).execute()
            if existing.data:
                flash("Ya existe otra cuenta con ese número", "error")
                return redirect(url_for("cuentas_activas.editar", id=id))
            
            # Actualizar en la base de datos
            usuario = session.get('email', 'usuario_desconocido')
            result = supabase.table("cuentas_activas").update({
                "banco": banco,
                "numero_cuenta": numero_cuenta_int,
                "cedula": cedula,
                "nombre_titular": nombre_titular,
                "pais": pais,
                "activa": activa,
                "usuario_modificacion": usuario
            }).eq("id", id).execute()
            
            if result.data:
                flash("Cuenta activa actualizada exitosamente", "success")
                return redirect(url_for("cuentas_activas.index"))
            else:
                flash("Error al actualizar la cuenta activa", "error")
        
        # GET: Obtener datos de la cuenta para mostrar en el formulario
        response = supabase.table("cuentas_activas").select("*").eq("id", id).single().execute()
        if response.data:
            cuenta = response.data
            return render_template("admin/cuentas_activas/editar.html", 
                                 cuenta=cuenta, 
                                 active_page="admin")
        else:
            flash("Cuenta no encontrada", "error")
            return redirect(url_for("cuentas_activas.index"))
            
    except Exception as e:
        logging.error(f"Error al editar cuenta activa: {e}")
        flash(f"Error al editar la cuenta activa: {str(e)}", "error")
        return redirect(url_for("cuentas_activas.index"))

@cuentas_activas_bp.route("/eliminar/<int:id>", methods=["POST"])
@user_allowed
def eliminar(id):
    """Eliminar una cuenta activa (marcar como inactiva)"""
    try:
        usuario = session.get('email', 'usuario_desconocido')
        result = supabase.table("cuentas_activas").update({
            "activa": False,
            "usuario_modificacion": usuario
        }).eq("id", id).execute()
        
        if result.data:
            flash("Cuenta desactivada exitosamente", "success")
        else:
            flash("Error al desactivar la cuenta", "error")
            
    except Exception as e:
        logging.error(f"Error al eliminar cuenta activa: {e}")
        flash(f"Error al desactivar la cuenta: {str(e)}", "error")
    
    return redirect(url_for("cuentas_activas.index"))

@cuentas_activas_bp.route("/activar/<int:id>", methods=["POST"])
@user_allowed
def activar(id):
    """Activar una cuenta que estaba desactivada"""
    try:
        usuario = session.get('email', 'usuario_desconocido')
        result = supabase.table("cuentas_activas").update({
            "activa": True,
            "usuario_modificacion": usuario
        }).eq("id", id).execute()
        
        if result.data:
            flash("Cuenta activada exitosamente", "success")
        else:
            flash("Error al activar la cuenta", "error")
            
    except Exception as e:
        logging.error(f"Error al activar cuenta: {e}")
        flash(f"Error al activar la cuenta: {str(e)}", "error")
    
    return redirect(url_for("cuentas_activas.index"))

@cuentas_activas_bp.route("/api/cuentas")
@user_allowed
def api_cuentas():
    """API para obtener cuentas activas en formato JSON"""
    try:
        response = supabase.table("cuentas_activas").select("*").eq("activa", True).order("banco").execute()
        cuentas = response.data if response.data else []
        return jsonify({"success": True, "data": cuentas})
    except Exception as e:
        logging.error(f"Error en API cuentas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500 