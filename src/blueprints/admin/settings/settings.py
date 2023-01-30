from flask import Blueprint,render_template
from ..admin_login_manager import admin_login_required
admin_settings_bp = Blueprint("admin_settings",__name__,template_folder="templates",static_folder="static")


@admin_settings_bp.route("/")
@admin_login_required
def server_root():
    return render_template("server_settings.html")