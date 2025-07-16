from flask_caching import Cache
from functools import wraps
from flask import session, flash, redirect, url_for
from supabase import create_client
import os
import pytz

cache = Cache() 

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

chile_tz = pytz.timezone('America/Santiago')

def user_allowed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        email = session.get("email")
        if not email:
            flash("Debes iniciar sesión.")
            return redirect(url_for("login"))
        try:
            response = supabase.table("allowed_users").select("email").eq("email", email).execute()
            if not response.data:
                flash("No tienes permisos para acceder a este módulo.")
                return redirect(url_for("index"))
        except Exception as e:
            flash("Error interno al verificar permisos.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

def format_number(value):
    """Filtro para formatear números con separadores de miles"""
    if value is None:
        return "0"
    try:
        return "{:,}".format(int(value)).replace(",", ".")
    except (ValueError, TypeError):
        return str(value) 