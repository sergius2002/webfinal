from datetime import datetime
from flask import Blueprint, render_template
from flask import session, redirect, url_for, flash
from mi_app.mi_app.blueprints.admin import login_required
from mi_app.mi_app.extensions import supabase

cierre_bp = Blueprint('cierre', __name__)

@cierre_bp.route('/cierre')
@login_required
def index():
    # Fecha actual en formato YYYY-MM-DD
    fecha = datetime.now().strftime('%Y-%m-%d')
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
    
    return render_template('cierre/index.html', active_page='cierre', 
                         ingresos=formatted_ingresos, egresos=formatted_egresos) 