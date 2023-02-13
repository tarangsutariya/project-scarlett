from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort
from functools import wraps
from blueprints.users.login_manager import user_login_required

from models import users
from blueprints.admin.models import admin_user
from .models import deployments


deploy_bp = Blueprint("deployments",__name__,template_folder="templates",static_folder="static")




##check if deployment belongs to user
def user_owns_deployment(f):
    @wraps(f)
    def wrap(deploy_id,*args,**kwargs):
        deploy=deployments.query.filter_by(deploy_id=deploy_id).first_or_404()
        if session["user_userid"]!=deploy.user_id:
            return redirect(url_for("users.user_dashboard"))


        return f(deploy,*args,**kwargs)
            
    return wrap




@deploy_bp.route("/<deploy_id>")
@user_login_required
@user_owns_deployment
def deployment_home(dep):
    return str(dep.deploy_id)




@deploy_bp.route("/<deploy_id>/settings")
def deployment_settings(deploy_id):
    return str(2)
