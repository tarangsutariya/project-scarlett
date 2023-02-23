from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort,jsonify
from functools import wraps
from blueprints.users.login_manager import user_login_required
import time
from models import users,db
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
        if deploy.initial_deploy==True:
            from tasks.remote_tasks import celery
            try:
                if celery.AsyncResult(deploy.celery_process_id).failed():
                    db.session.delete(deploy)
                    db.session.commit()
                    return "Deployment failed due to some error please try deploying again,this task is deleted now"
                elif celery.AsyncResult(deploy.celery_process_id).status in ["PENDING","STARTED"]:
                    info = celery.AsyncResult(deploy.celery_process_id).info
                    if info == None:
                        info = {"curr":0,"total":9,"message":"waiting for server"}
                    
                    return render_template("deploying.html",dep=deploy,info=info)
            except:
                db.session.delete(deploy)
                db.session.commit()

        return f(deploy,*args,**kwargs)
            
    return wrap




@deploy_bp.route("/<deploy_id>/initdeploystatus/<st>")
@user_login_required
def initdeploystatus(deploy_id,st):
    deploy=deployments.query.filter_by(deploy_id=deploy_id).first_or_404()
    if deploy.user_id!=session["user_userid"]:
        abort(403)
    if deploy.initial_deploy==False:
        return jsonify({"curr":9,"total":9,"message":"Redirecting.."})
    from tasks.remote_tasks import celery
    if celery.AsyncResult(deploy.celery_process_id).failed():
        return jsonify({"curr":9,"total":9,"message":"Some error has occured redirecting.."})
    if celery.AsyncResult(deploy.celery_process_id).status in ["PENDING","STARTED"]:
        p = 0
        while celery.AsyncResult(deploy.celery_process_id).info==None and p<15:
            time.sleep(1)
            p+=1
        
        if celery.AsyncResult(deploy.celery_process_id).info==None:

            return jsonify({"curr":0,"total":9,"message":"Waiting for server.."})
        p = 0
        while celery.AsyncResult(deploy.celery_process_id).status!='SUCCESS' and celery.AsyncResult(deploy.celery_process_id).info["curr"]==st:
            time.sleep(1)
            p+=1
        info = celery.AsyncResult(deploy.celery_process_id).info
        if celery.AsyncResult(deploy.celery_process_id).status in ['SUCCESS','Failure'] or info==None:
            return jsonify({"curr":9,"total":9,"message":celery.AsyncResult(deploy.celery_process_id).status+"redirecting.."})
        else:
            return jsonify({"curr":info["curr"],"total":info["total"],"message":info["message"]})
        


    return jsonify({"curr":9,"total":9,"message":"redirecting.."})






@deploy_bp.route("/<deploy_id>")
@user_login_required
@user_owns_deployment
def deployment_home(dep):
    from tasks.remote_tasks import celery
    return render_template("deployment.html",dep=dep)




@deploy_bp.route("/<deploy_id>/settings")
@user_login_required
@user_owns_deployment
def deployment_settings(dep):
    return render_template("settings.html",dep=dep)

@deploy_bp.route("/<deploy_id>/logs")
@user_login_required
@user_owns_deployment
def deployment_logs(dep):
    return render_template("logs.html",dep=dep)

@deploy_bp.route("/<deploy_id>/networking")
@user_login_required
@user_owns_deployment
def deployment_networking(dep):
    return render_template("networking.html",dep=dep)

@deploy_bp.route("/<deploy_id>/notifications")
@user_login_required
@user_owns_deployment
def deployment_notifications(dep):
    return render_template("notifications.html",dep=dep)

@deploy_bp.route("/<deploy_id>/envvariables")
@user_login_required
@user_owns_deployment
def deployment_envvariables(dep):
    return render_template("env_variables.html",dep=dep)