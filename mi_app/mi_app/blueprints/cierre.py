from flask import Blueprint, render_template
from flask import session, redirect, url_for, flash
from mi_app.mi_app.blueprints.admin import login_required

cierre_bp = Blueprint('cierre', __name__)

@cierre_bp.route('/cierre')
@login_required
def index():
    return render_template('cierre/index.html', active_page='cierre') 