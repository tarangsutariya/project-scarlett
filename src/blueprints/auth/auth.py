from flask import request,session,Blueprint,render_template,redirect,url_for

from authlib.integrations.flask_client import OAuth
from models import db
from ..admin.admin import admin_github_tokens


auth_bp = Blueprint("auth",__name__,template_folder="templates",static_folder="static")


@auth_bp.route("/")
def auth_root():
    return "auth root"
    