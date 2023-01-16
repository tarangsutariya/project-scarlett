from flask import request,session,Blueprint,render_template,redirect,url_for
from github import Github
from authlib.integrations.flask_client import OAuth
from models import db
from ..admin.admin import admin_github_tokens,admin_user,admin_token_orgs
from config import github_client_id,github_client_secret


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
    client_kwargs={'scope': 'user,repo,admin,user:email'},
)



@auth_bp.route("/auth")
def auth_root():
    github = oauth.create_client('github')
    redirect_uri = url_for('auth.authorize', _external=True)
    return github.authorize_redirect(redirect_uri)


@auth_bp.route("/authorize")
def authorize():
    github = oauth.create_client('github')
    try:
       token = github.authorize_access_token()
    except:
        return redirect(url_for("auth.auth_root"))
    resp = github.get('user', token=token)
   
   # do something with the token and profile
    github_client = Github(token["access_token"])
    try:
        user_raw_data = github_client.get_user().raw_data
    
    except:
        return redirect(url_for("auth.auth_root"))
    

    if "admin_pannel" in session:
        username = session["admin_username"]
        user_id = admin_user.query.filter_by(username=username).first().admin_id
        session.clear()
        session["admin_username"]=username
        curr_count = admin_github_tokens.query.count()+1
        
        token_to_insert = admin_github_tokens(token_name=str(curr_count),user_id=user_id,github_token=token["access_token"])
        
        db.session.add(token_to_insert)
        db.session.commit()
        token_to_insert.token_name = token_to_insert.token_id
        
        db.session.commit()
        
        g = Github(token["access_token"])
        for org in g.get_user().get_orgs():
            org_to_insert = admin_token_orgs(token_id=token_to_insert.token_id,org_id=org.id,org_name=org.login)
            db.session.add(org_to_insert)
            db.session.commit()
        
        return redirect(url_for("admin.admin_dashboard"))
    elif "user_login" in session:
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
        if not user_belongs_to_approved_org:
            print("HI")
        





        return redirect(url_for("users.user_dashboard"))





    session.clear()
    return redirect('/')

