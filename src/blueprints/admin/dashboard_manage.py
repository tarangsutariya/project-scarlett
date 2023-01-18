from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort
import time
from github import Github
from .admin_login_manager import admin_login_required
from .models import admin_user
from models import users,user_orgs,user_requests,db

admin_manage = Blueprint("admin_manage",__name__,template_folder="templates",static_folder="static")


@admin_manage.route("/org/delete/<org>")
def dashoproot(org):
    time.sleep(10)
    return "HELLO"


@admin_manage.route("userrequest/delete/<request_id>")
@admin_login_required
def delete_user_request(request_id):
    try:
        req_id = int(request_id)
    except:
        abort(404)
    req = user_requests.query.filter_by(request_id=req_id).first()
    if req == None:
        abort(404)
    db.session.delete(req)
    db.session.commit()
    return "SUCCESS"
    
    




@admin_manage.route("/userrequest/accept/<request_id>")
@admin_login_required
def accept_user_request(request_id):
    try:
        req_id = int(request_id)
    except:
        abort(404)
    req = user_requests.query.filter_by(request_id=req_id).first()
    if req == None:
        abort(404)
    g = Github(req.github_token)
    org_list = []
    for org in g.get_user().get_orgs():
        org_details = {}
        org_details["org_id"]=org.id
        org_details["org_name"]=org.name
        org_list.append(org_details)
    new_user = users(github_user_id=req.github_user_id,github_username=req.github_username,github_oauth_token=req.github_token)
    db.session.add(new_user)
    db.session.commit()
    for org in org_list:
            org_to_insert = user_orgs(user_id=new_user.user_id,github_org_id=org["org_id"],github_org_name=org["org_name"])
            db.session.add(org_to_insert)
            db.session.commit()
    db.session.delete(req)
    db.session.commit()
    return "SUCCESS"
    