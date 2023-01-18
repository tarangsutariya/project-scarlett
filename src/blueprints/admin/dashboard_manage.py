from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort
import time
from .admin_login_manager import admin_login_required
from .models import admin_user

admin_manage = Blueprint("admin_manage",__name__,template_folder="templates",static_folder="static")


@admin_manage.route("/org/delete/<org>")
def dashoproot(org):
    time.sleep(10)
    return "HELLO"


@admin_manage.route("/userrequest/accept/<request_id>")
@admin_login_required
def accept_user_request(request_id):
    try:
        req_id = int(request_id)
    except:
        abort(404)
    return req_id