from flask import Blueprint,render_template,session,redirect,url_for,request,flash
from ..admin_login_manager import admin_login_required
from ..models import admin_user,admin_servers
from models import db
import re
admin_settings_bp = Blueprint("settings",__name__,template_folder="templates",static_folder="static")

@admin_settings_bp.route("/")
@admin_login_required
def settings_root():
    return redirect(url_for("admin.settings.settings_servers"))


@admin_settings_bp.route("/account",methods=["GET","POST"])
@admin_login_required
def settings_admin_account():
    if request.method == "POST":
        form_data = request.form.to_dict()
        usr = admin_user.query.filter_by(username=session["admin_username"]).first()
        print(form_data)
        if "currentpassword" not in form_data or not usr.check_password(form_data["currentpassword"]):
            
            flash("Invalid Current password")
        elif "newpassword" not in form_data or "confirmpassword" not in form_data or len(form_data["newpassword"])==0:
            flash("INVALID NEW Or CONFIRM PASSWORD")
        elif form_data["newpassword"]!=form_data["confirmpassword"]:
            flash("new and confirm password do not match")
        else:
            usr.set_password(form_data["newpassword"])
            db.session.commit()
            flash("Password updated","success")


    return render_template("admin_account_settings.html",username=session["admin_username"])

@admin_settings_bp.route("/servers")
@admin_login_required
def settings_servers():

    servers_list = admin_servers.query.filter_by().all()
    
    return render_template("server_settings.html",username=session["admin_username"],servers_list=servers_list)


@admin_settings_bp.route("/addserver",methods=["POST"])
@admin_login_required
def settings_addserver():
    ip_to_add = request.json["ip"]
    prefix_to_add = request.json["prefix"]
    ipregex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if not re.search(ipregex,ip_to_add):
        return "INVALID IP"
    if admin_servers.query.filter_by(ip_address=ip_to_add).first() != None:
        return "IP address is already used by another server"
    if admin_servers.query.filter_by(domain_prefix=prefix_to_add).first() != None:
        return "prefix already in use"
    svr_to_add = admin_servers(ip_address=ip_to_add,domain_prefix=prefix_to_add,server_health="offline")
    db.session.add(svr_to_add)
    db.session.commit()
    return "OK"




@admin_settings_bp.route("/editserver",methods=["POST"])
@admin_login_required
def settings_editserver():

    ip_to_add = request.json["ip"]
    prefix_to_add = request.json["prefix"]
    svr_id = request.json["server_id"]
    ipregex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if not re.search(ipregex,ip_to_add):
        return "INVALID IP"

    svr_to_update = admin_servers.query.filter_by(server_id=svr_id).first()
    if svr_to_update == None:
        return "INVALILD SERVER ID"

    ######################################
    #########CASCADING EDIT EFFECTS HERE ###
    if admin_servers.query.filter_by(ip_address=ip_to_add).first() != None:
        return "IP address is already used by another server"
    if admin_servers.query.filter_by(domain_prefix=prefix_to_add).first() != None:
        return "prefix already in use"
    
    return "OK"


@admin_settings_bp.route("/deleteserver",methods=["POST"])
@admin_login_required
def settings_deleteserver():
    #########################
    ##todo############
    return "OK"






@admin_settings_bp.route("/server/<server_id>")
@admin_login_required
def server_details(server_id):
    svr = admin_servers.query.filter_by(server_id=server_id).first_or_404()
    server_details = {}
    server_details["server_id"]=svr.server_id
    server_details["domain"]=svr.domain_prefix
    server_details["ip"]=svr.ip_address
    server_details["health"]=svr.server_health
    if svr.number_of_cores == None or svr.server_health=="offline":
        server_details["cores"]="NA"
        server_details["cpu_usage"]="0"
        server_details["cpu"]=0
    else:
        server_details["cores"]=svr.number_of_cores
        server_details["cpu_usage"]=svr.cpu_usage
        server_details["cpu"]=svr.cpu_usage
    if svr.total_ram == None or svr.server_health=="offline":
        server_details["total_ram"]="NA"
        server_details["ram_usage"]="NA"
        server_details["ram"]=0
    else:
        server_details["ram"]=round(100*(svr.ram_usage/svr.total_ram),1)
        if svr.total_ram>1024:
            server_details["total_ram"]=str(round(svr.total_ram/1024,2))+" GB"
        else:
            server_details["total_ram"]=str(svr.total_ram)+" MB"
        if svr.ram_usage>1024:
            server_details["ram_usage"]=str(round(svr.ram_usage/1024,2))+" GB"
        else:
            server_details["ram_usage"]=str(svr.ram_usage)+" MB"

    if svr.total_disk==None or svr.server_health == "offline":
        server_details["total_disk"]="NA"
        server_details["disk_usage"]="NA"
        server_details["disk"]=0
    else:
        server_details["disk"]=round(100*(svr.disk_usage/svr.total_disk),1)
        if svr.total_disk>1024:
            server_details["total_disk"]=str(round(svr.total_disk/1024,2))+" TB"
        else:
            server_details["total_disk"]=str(svr.total_disk)+" GB"
        if svr.disk_usage>1024:
            server_details["disk_usage"]=str(round(svr.disk_usage/1024,2))+" TB"
        else:
            server_details["disk_usage"]=str(svr.disk_usage)+" GB"



    return render_template("server_details.html",username=session["admin_username"],svr=server_details)