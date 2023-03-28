from flask import request,session,Blueprint,render_template,redirect,url_for
from github import Github
from authlib.integrations.flask_client import OAuth
from models import db,users,user_orgs,user_requests
from ..admin.models import admin_github_tokens,admin_user,admin_token_orgs
from config import github_client_id,github_client_secret,approved_domains,oauth_redirect
import requests

auth_bp = Blueprint("auth",__name__,template_folder="templates",static_folder="static")

oauth = OAuth()


github = oauth.register(
    name='github',
    client_id=github_client_id,
    client_secret=github_client_secret,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user,read:org,user:email'},
)

@auth_bp.route("/")
def redirecttodashboard():
    return redirect(url_for("users.user_dashboard"))

@auth_bp.route("/auth")
def auth_root():
    github = oauth.create_client('github')
    redirect_uri = oauth_redirect
    return github.authorize_redirect(redirect_uri)


@auth_bp.route("/authorize")
def authorize():
    github = oauth.create_client('github')
    try:
       token = github.authorize_access_token()
    except:
        return redirect(url_for("auth.auth_root"))
    
   
   # do something with the token and profile
    headers = {'Authorization': 'token %s'%(token["access_token"])}
    response = requests.get('https://api.github.com/user/emails', headers=headers)
    if response.status_code == 200:
        emails = response.json()
        

    github_client = Github(token["access_token"])
    try:
        user_raw_data = github_client.get_user().raw_data
    
    except:
        return redirect(url_for("auth.auth_root"))
    
    for tkn in admin_github_tokens.query.filter_by(is_oauth_token=True,github_user_id=user_raw_data["id"]).all():
        tkn.github_token=token["access_token"]
    db.session.commit()
    
    usr = users.query.filter_by(github_user_id=user_raw_data["id"]).first()
    if usr != None:
        usr.github_oauth_token = token["access_token"]
        db.session.commit
    

    if "admin_pannel" in session:
        session.pop("admin_pannel")
        
        username = session["admin_username"]
        user_id = admin_user.query.filter_by(username=username).first().admin_id
        session.clear()
        session["admin_username"]=username
        
        
        token_to_insert = admin_github_tokens(user_id=user_id,github_token=token["access_token"],
        is_oauth_token=True,github_user_id=user_raw_data["id"])
        
        db.session.add(token_to_insert)
        db.session.commit()
        token_to_insert.token_name = token_to_insert.token_id
        
        db.session.commit()
        
        g = Github(token["access_token"])
        for org in g.get_user().get_orgs():
            if admin_token_orgs.query.filter_by(org_id=org.id).first()!= None:
                continue
            org_to_insert = admin_token_orgs(token_id=token_to_insert.token_id,org_id=org.id,org_name=org.login)
            db.session.add(org_to_insert)
            db.session.commit()
        
        return redirect(url_for("admin.admin_dashboard"))
    elif "user_login" in session:
        session.pop("user_login")
        usr_curr = users.query.filter_by(github_user_id=user_raw_data["id"]).first()
        if  usr_curr != None:
            session["user_userid"] = usr_curr.user_id
            session["user_githubid"]= user_raw_data["id"]
            session["user_githubusername"]=user_raw_data["login"]
            usr_id = session["user_userid"]
            usr_curr.github_token = token["access_token"]
            db.session.commit()
            for org in github_client.get_user().get_orgs():
                if user_orgs.query.filter_by(user_id=usr_id,github_org_id=org.id)==None:
                    org_to_insert = user_orgs(user_id=usr_id,github_org_id=org.id,github_org_name=org.name)
                    db.session.add(org_to_insert)
                    db.session.commit()
            
            return redirect(url_for("users.user_dashboard"))
        g = Github(token["access_token"])
        org_list = []
        for org in g.get_user().get_orgs():
            org_details = {}
            org_details["org_id"]=org.id
            org_details["org_name"]=org.name
            org_list.append(org_details)
        
        user_belongs_to_approved_org = False
        for org in org_list:
            if admin_token_orgs.query.filter_by(org_id=org["org_id"]).first() != None:
                user_belongs_to_approved_org = True
                break
        
        email = emails[0]['email']
        domain = email.split('@')[-1]
        if domain in approved_domains:
            new_user = users(github_user_id=user_raw_data["id"],github_username=user_raw_data["login"],github_oauth_token=token["access_token"])
            db.session.add(new_user)
            db.session.commit()
            for org in org_list:
                org_to_insert = user_orgs(user_id=new_user.user_id,github_org_id=org["org_id"],github_org_name=org["org_name"])
                db.session.add(org_to_insert)
                db.session.commit()
            
            session["user_userid"]=new_user.user_id
            session["user_githubid"]=user_raw_data["id"]
            session["user_githubusername"]=user_raw_data["login"]
            return redirect(url_for("users.user_dashboard"))





        if not user_belongs_to_approved_org:
        

            if user_requests.query.filter_by(github_user_id=user_raw_data["id"]).first()!=None:
                session["pending_request_id"]=user_requests.query.filter_by(github_user_id=user_raw_data["id"]).first().request_id
                session["user_githubusername"]=user_raw_data["login"]
                return redirect(url_for("users.user_not_approved"))


            session["approve_request_not_sent"] = True
            session["github_oauth_token"] = token["access_token"]
            session["user_githubid"]= user_raw_data["id"]
            session["user_githubusername"]=user_raw_data["login"]
            return redirect(url_for("users.user_request_access"))
        
        new_user = users(github_user_id=user_raw_data["id"],github_username=user_raw_data["login"],github_oauth_token=token["access_token"])
        db.session.add(new_user)
        db.session.commit()
        for org in org_list:
            org_to_insert = user_orgs(user_id=new_user.user_id,github_org_id=org["org_id"],github_org_name=org["org_name"])
            db.session.add(org_to_insert)
            db.session.commit()
        
        session["user_userid"]=new_user.user_id
        session["user_githubid"]=user_raw_data["id"]
        session["user_githubusername"]=user_raw_data["login"]
        return redirect(url_for("users.user_dashboard"))




    return redirect(url_for("users.user_dashboard"))





    session.clear()
    return redirect('/')

