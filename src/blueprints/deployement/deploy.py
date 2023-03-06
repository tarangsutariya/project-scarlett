from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort,jsonify
from functools import wraps
from blueprints.users.login_manager import user_login_required
import time
from models import users,db
from blueprints.admin.models import admin_user,admin_servers
from .models import deployments,delete_deploy
from config import domains
import python_on_whales
from ansi2html import Ansi2HTMLConverter
from datetime import timedelta,datetime
conv = Ansi2HTMLConverter()
deploy_bp = Blueprint("deployments",__name__,template_folder="templates",static_folder="static")
from config import cloudflare_api_key
import CloudFlare
import copy
cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
import random


##check if deployment belongs to user
def user_owns_deployment(f):
    @wraps(f)
    def wrap(deploy_id,*args,**kwargs):
        deploy=deployments.query.filter_by(deploy_id=deploy_id).first_or_404()
        if session["user_userid"]!=deploy.user_id:
            return redirect(url_for("users.user_dashboard"))
        if delete_deploy.query.filter_by(deploy_id=deploy_id).first()!=None:
            return "This deployment is being deleted "

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
    # from tasks.remote_tasks import celery
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    return render_template("deployment.html",dep=dep,svr=svr)




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
    return render_template("networking.html",dep=dep,domains=domains)

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


###deploy apis


@deploy_bp.route("/<deploy_id>/editenv",methods=["POST"])
@user_login_required
@user_owns_deployment
def edit_env(dep):
    varss = request.json["env_variables"]
    env_vars = {}
    for v in varss:
        env_vars[v[0]]=v[1]
    dep.env_variables = dict(env_vars)
    db.session.commit()
    from tasks.manage_deploys import update_env_variables
    prefix = admin_servers.query.filter_by(server_id=dep.server_id).first().domain_prefix
    update_env_variables.apply_async(args=[dep.deploy_id],queue=prefix)
    return "OK"


###LOGS STREAMING


@deploy_bp.route("/<deploy_id>/containerlogs",methods=['POST'])
@user_login_required
@user_owns_deployment
def streamlogs(dep):
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first().ip_address
    container_id = request.json["container_id"]
    docker = python_on_whales.DockerClient(host="ssh://root@%s:%s"%(svr,str(dep.forwarded_ports["SSH"][0]["external_port"])))
    timestamp = request.json["timestamp"]
    if timestamp!=None:
        
        date_format = '%Y-%m-%d %H:%M:%S.%f'
        last_time = datetime.strptime(timestamp, date_format)

        logs =docker.container.logs(container_id,since=datetime.now()-last_time)
        total_sleep =0
        
        while logs=="" and total_sleep<10:
            
            total_sleep+=2
            logs =docker.container.logs(container_id,since=datetime.now()-last_time)
        response = {}
        response["timestamp"]=str(datetime.now())
        logs = conv.convert(logs,full=False)
        logs = logs.split('\n')
        response["logs"]=logs
        
        return jsonify(response)
    else:
        
        response = {}
        logs =docker.container.logs(container_id,tail=100)
        logs = conv.convert(logs,full=False)
        logs = logs.split('\n')
        response["timestamp"]=str(datetime.now())
        response["logs"]=logs
        return jsonify(response)
    
####edit network forwards

@deploy_bp.route("/<deploy_id>/addhttpforward",methods=['POST'])
@user_login_required
@user_owns_deployment
def add_http_forward(dep):
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    subdomain = request.json["subdomain"]
    internal_port = int(request.json["port"])
    subsplit = subdomain.rsplit(".",2)
    curr_domain = subsplit[-2]+'.'+subsplit[-1]
    zone_id = cf.zones.get(params = {'name':curr_domain})[0]["id"]
    subd = subdomain.split('.')[0]
    cf.zones.dns_records.post(zone_id, data={"name":subd,"type":"A","content":svr.ip_address})
    # dep.forwarded_ports["HTTP"].append({"subdomain":subdomain,"port":internal_port})
    new_forwarded = dict(dep.forwarded_ports)
    new_forwarded = copy.deepcopy(new_forwarded)
    new_forwarded["HTTP"].append({"subdomain":subdomain,"internal_port":internal_port})
    dep.forwarded_ports=new_forwarded
    #print(dep.forwarded_ports)
    db.session.commit()
    from tasks.remote_tasks import addhttpforward
    addhttpforward.apply_async(args=[dep.internal_ip,subdomain,internal_port],queue=svr.domain_prefix)

    return "OK"

@deploy_bp.route("/<deploy_id>/deletehttpforward",methods=['POST'])
@user_login_required
@user_owns_deployment
def deletehttpforward(dep):
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    subdomain=request.json["subdomain"]
    subsplit = subdomain.rsplit(".",2)
    curr_domain = subsplit[-2]+'.'+subsplit[-1]
    new_forwarded = dict(dep.forwarded_ports)
    new_forwarded = copy.deepcopy(new_forwarded)
    indx = 0
    for rule in new_forwarded["HTTP"]:
        if rule["subdomain"]==subdomain:
            break
        indx+=1
    new_forwarded["HTTP"].pop(indx)
    dep.forwarded_ports=new_forwarded
    db.session.commit()
    zone_id = cf.zones.get(params = {'name':curr_domain})[0]["id"]
    record_id = cf.zones.dns_records.get(zone_id, params={"name":subdomain,"type":"A"})[0]["id"]
    cf.zones.dns_records.delete(zone_id,record_id)
    from tasks.remote_tasks import deletehttpforward
    deletehttpforward.apply_async(args=[subdomain],queue=svr.domain_prefix)
    
    return "OK"

@deploy_bp.route("/<deploy_id>/addportforward",methods=['POST'])
@user_login_required
@user_owns_deployment
def addportforward(dep):
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    port  = int(request.json["port"])
    new_forwarded = dict(dep.forwarded_ports)
    new_forwarded = copy.deepcopy(new_forwarded)
    new_forwarded["PORT"].append({"external_port":None,"internal_port":port,"socat_pid":None})
    dep.forwarded_ports=new_forwarded
    db.session.commit()
    from tasks.remote_tasks import addportforward
    addportforward.apply_async(args=[dep.deploy_id,port],queue=svr.domain_prefix)
    
    return "OK"

@deploy_bp.route("/<deploy_id>/deleteport",methods=['POST'])
@user_login_required
@user_owns_deployment
def deleteport(dep):
    pid = int(request.json["pid"])
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    new_forwarded = dict(dep.forwarded_ports)
    new_forwarded = copy.deepcopy(new_forwarded)
    indx = 0
    for rule in new_forwarded["PORT"]:
        if rule["socat_pid"]==pid:
            break
        pid+=1
    if indx == len(new_forwarded["PORT"]):
        abort(418)
    new_forwarded["PORT"].pop(indx)
    dep.forwarded_ports = new_forwarded
    db.session.commit()
    from tasks.remote_tasks import deleteportforward
    deleteportforward.apply_async(args=[pid],queue=svr.domain_prefix)
    
    return "OK"

@deploy_bp.route("/<deploy_id>/delete")
@user_login_required
@user_owns_deployment
def reclonetest(dep):
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    # from tasks.manage_deploys import redeloy
    # redeloy.apply_async(args=[dep.deploy_id],queue=svr.domain_prefix)
    delete_record = delete_deploy(deploy_id=dep.deploy_id)
    db.session.add(delete_record)
    db.session.commit()
    from tasks.manage_deploys import deletedeploy
    deletedeploy.apply_async(args=[dep.deploy_id,True],queue=svr.domain_prefix)
    return "OK"

@deploy_bp.route("/<deploy_id>/status",methods=['POST'])
@user_login_required
@user_owns_deployment
def depstatus(dep):
    last_status  =request.json["last_status"]
    if dep.last_deployment_status != "redeploying":
        timeout = 0
        while last_status == dep.last_deployment_status and timeout<20:
            time.sleep(2)
            timeout+=2
            db.session.refresh(dep)
    else:
        from tasks.remote_tasks import celery
        timeout = 0
        while celery.AsyncResult(dep.celery_process_id).status!='SUCCESS' and  (not(celery.AsyncResult(dep.celery_process_id).failed())) and celery.AsyncResult(dep.celery_process_id).info["message"]==last_status:
            time.sleep(2)
            timeout+=2
        response={}
        response["status"]=celery.AsyncResult(dep.celery_process_id).info["message"]


    response={}
    response["status"]=dep.last_deployment_status
    return jsonify(response)


 
