from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort
from models import db,user_requests,users
from blueprints.admin.models import admin_token_orgs,admin_github_tokens,admin_servers
from .login_manager import user_login_required
from github import Github
import time
from config import minimum_ram,minimum_disk,minimum_cpu,domains
from blueprints.deployement.countries import random_words
import random
from blueprints.deployement.models import deployments
users_bp = Blueprint("users",__name__,template_folder="templates",static_folder="static")

######DANGER DELETE THIS##
@users_bp.route("/grid")
def user_grid():
    return render_template("testgrid.html")



@users_bp.route("/")
@user_login_required
def user_dashboard():
    return render_template("user_dashboard.html")

@users_bp.route("/login")
def user_login():
    if "pending_request_id" in session:
        return redirect(url_for("users.user_not_approved"))
    if "approve_request_not_sent" in session:
        return redirect(url_for("users.user_request_access"))
    return render_template("user_login.html")


@users_bp.route("/requestaccess",methods=["GET","POST"])
def user_request_access():
    if "user_userid" in session:
        return redirect(url_for("users.user_dashboard"))
    if "pending_request_id" in session:
        return redirect(url_for("users.user_not_approved"))
    if "approve_request_not_sent" not in session:
        return redirect(url_for("users.user_login"))
    if request.method=="GET":    
        return render_template("user_requestaccess.html",github_username=session["user_githubusername"])
    formdata = request.form.to_dict()
    new_request = user_requests(github_user_id=session["user_githubid"],github_username=session["user_githubusername"],
                  github_token=session["github_oauth_token"],request_message=formdata["request_message"])
    db.session.add(new_request)
    db.session.commit()
    session.pop("approve_request_not_sent")
    session.pop("github_oauth_token")
    session.pop("user_githubid")
    session["pending_request_id"] = new_request.request_id
    return redirect(url_for("users.user_not_approved"))


    
    
@users_bp.route("/userapproved")
def user_approved_login():
    if "pending_request_id" not in session or "user_githubusername" not in session:
        return redirect(url_for("users.user_not_approved"))
    usr = users.query.filter_by(github_username=session["user_githubusername"]).first()
    if usr==None:
        return redirect(url_for("users.user_not_approved"))
    session.pop("pending_request_id")
    session.pop("user_githubusername")
    session["user_userid"]=usr.user_id
    session["user_githubid"]=usr.github_user_id
    session["user_githubusername"]=usr.github_username
    return redirect(url_for("users.user_dashboard"))


@users_bp.route("/checkapproved")
def checkapproved():
    if "pending_request_id" not in session or "user_githubusername" not in session:
        abort(404)
    dur = 0
    while dur < 15 and user_requests.query.filter_by(request_id=session["pending_request_id"]).first()!=None:
        print(user_requests.query.filter_by(request_id=session["pending_request_id"]).first()==None)
        time.sleep(2)
        dur+=2
    if user_requests.query.filter_by(request_id=session["pending_request_id"]).first()==None:
        return "approved"
    return "notapproved"



@users_bp.route("/notapproved",methods=["GET","POST"])
def user_not_approved():
    if "user_userid" in session:
        return redirect(url_for("users.user_dashboard"))
    if "approve_request_not_sent" in session:
        return redirect(url_for("users.user_request_access"))
    if "pending_request_id" not in session:
        return redirect(url_for("users.user_login"))
    if user_requests.query.filter_by(request_id=session["pending_request_id"]).first()==None:
        if users.query.filter_by(github_username=session["user_githubusername"]).first()!=None:
            return redirect(url_for("users.user_approved_login"))
        return render_template("user_notapproved.html",notFound=True,request_id=session["pending_request_id"])
    if request.method=="POST":
        request_to_delete = user_requests.query.filter_by(request_id=session["pending_request_id"]).first()
        db.session.delete(request_to_delete)
        db.session.commit()
        session.pop("pending_request_id")
        session.pop("user_githubusername")
        return redirect(url_for("users.user_login"))
    
    return render_template("user_notapproved.html",notFound=False,github_username=session["user_githubusername"],
           request_id=session["pending_request_id"])




@users_bp.route("/deploy")
@user_login_required
def create_deploy():
    usr = users.query.filter_by(user_id=session["user_userid"]).first()
    g = Github(usr.github_oauth_token)
    g_usr = g.get_user()
    repos = {}
    for repo in g_usr.get_repos():
        if repo.owner.login  not in repos:
            repos[repo.owner.login]=[]
        repos[repo.owner.login].append([repo.id,repo.name])
    
    owner_list = [session["user_githubusername"]]
    for owner in repos:
        if owner == session["user_githubusername"]:
            continue
        owner_list.append(owner)
    return render_template("deploy_new.html",owners=owner_list,repos=repos)



@users_bp.route('/config/repo')
@user_login_required
def configuredeployment():
    repo_id = request.args.get('id')
    github_access_token = request.args.get('token')
    org_needed_to_access = request.args.get("org")
    g = Github()
    if org_needed_to_access!=None:
        try:
            org_needed_to_access=int(org_needed_to_access)
        except:
            abort(418)
        orgg =  admin_token_orgs.query.filter_by(org_id=org_needed_to_access).first_or_404()
        tkn = admin_github_tokens.query.filter_by(token_id=orgg.token_id).first_or_404().github_token
        g=Github(tkn)
    elif github_access_token !=None:
        g=Github(github_access_token)
    try:
        repo = g.get_repo(int(repo_id))
    except:
        return redirect(url_for("users.create_deploy"))
    dep_details = {}
    dep_details["repo_url"]=repo.html_url
    dep_details["repo_id"]=repo.id
    dep_details["owner_id"]=repo.owner.id
    dep_details["owner_name"]=repo.owner.login
    dep_details["repo_name"]=repo.name
    dep_details["min_cpu"]=minimum_cpu
    dep_details["min_ram"]=minimum_ram
    dep_details["min_disk"]=minimum_disk
    dep_details["ram_step"]=128
    dep_details["disk_step"]=0.5
    dep_details["cpu_step"]=1
    dep_details["domains"]=domains

    branches = []
    branches.append(repo.default_branch)
    for branch in repo.get_branches():
        if branch.name == branches[0]:
            continue
        branches.append(branch.name)
    dep_details["branches"]=branches


    svrs = admin_servers.query.filter_by().all()
    dep_details["svrs"]=[]
    usr = users.query.filter_by(user_id=session["user_userid"]).first()
    for svr in svrs:
        if svr.server_health!="offline" and  (svr.total_ram-svr.ram_usage>=minimum_ram) and (svr.total_disk-svr.disk_usage>=minimum_disk):
            svr_details = {}
            svr_details["server_id"]=svr.server_id
            svr_details["server_location_code"]=svr.server_location_code
            svr_details["server_location_description"]=svr.server_location_description
            svr_details["domain_prefix"]=svr.domain_prefix
            svr_details["av_cpu"]=min(svr.number_of_cores,usr.max_cpu_cores)
            svr_details["av_ram"]=min(svr.total_ram-svr.ram_usage,usr.max_ram)
            svr_details["av_disk"]=min(svr.total_disk-svr.disk_usage,usr.max_disk)
         


            dep_details["svrs"].append(svr_details)
    
    
    return render_template("configure_new_deploy.html",details=dep_details)



@users_bp.route("/config/createnew",methods=["POST"])
@user_login_required
def create_new_deploy():
    try:
        usr = users.query.filter_by(user_id=session["user_userid"]).first()
        repo_id = int(request.json["repo_id"])
        org = request.json["org"]

        dep = deployments()
        p_token = request.json["token"]
        github_token = None
        if org != None:
            org = int(org)
            orgg =  admin_token_orgs.query.filter_by(org_id=org).first()
            tkn = admin_github_tokens.query.filter_by(token_id=orgg.token_id).first()
            dep.accessed_by_org_token=True
            dep.org_token_id = tkn.token_id
            github_token = tkn.github_token
            dep.accessed_by_custom_token=False
        elif p_token!=None:
            dep.accessed_by_org_token=False
            dep.accessed_by_custom_token=True
            dep.custom_token=p_token
            github_token=p_token
        else:
            dep.accessed_by_custom_token=False
            dep.accessed_by_org_token=False
            github_token=usr.github_oauth_token
        g = Github(github_token)
        r = g.get_repo(repo_id)
        dep.repo_id = repo_id
        dep.repo_owner=r.owner.login
        dep.repo_owner_id=r.owner.id
        dep.server_id=request.json["server_id"]
        dep.repo_name=r.name
        dep.branch_name = request.json["branch"]
        dep.primary_domain=request.json["subdomain"]
        dep.secondary_domain=random_words[random.randint(0,999)]+'-'+random_words[random.randint(0,999)]+'-'+random_words[random.randint(0,999)]+'.'+domains[0]
        dep.initial_deploy=True
        envs = {}
        for v in request.json["env_variables"]:
            envs[v[0]]=v[1]
        dep.env_variables = envs
        dep.redeploy_process=request.json["reloadtype"]
        dep.cpu_allocated=request.json["cpucores"]
        dep.ram_allocated=request.json["ramsize"]
        dep.disk_allocated=request.json["disksize"]
        dep.user_id=usr.user_id
        db.session.add(dep)
        db.session.commit()


        return str(dep.deploy_id)

    except:
        return "notok"

    

@users_bp.route("/c")
def celerytest():
    from tasks.remote_tasks import initdeloy
    initdeloy.delay(1,queue="de")





@users_bp.route("/config/ava/<subdomain>")
@user_login_required
def verifysubav(subdomain):
    try:
        subsplit = subdomain.rsplit(".",2)
        curr_domain = subsplit[-2]+'.'+subsplit[-1]
    except:
        return "something went wrong"
    if curr_domain not in domains:
        return "something went wrong"
    new_domain = subdomain
    while deployments.query.filter_by(primary_domain=new_domain).first()!=None:
        new_domain=random_words[random.randint(0,999)]+'-'+new_domain
    while deployments.query.filter_by(secondary_domain=new_domain).first()!=None:
        new_domain=random_words[random.randint(0,999)]+'-'+new_domain
    if subdomain==new_domain:
        return "OK"
    else:
        return new_domain

        







@users_bp.route("/logout")
@user_login_required
def logoutuser():
    if "user_userid" in session:
        session.pop("user_userid")
    if "user_githubid" in session:
        session.pop("user_githubid")
    if "user_githubusername" in session:
        session.pop("user_githubusername")
    if "approve_request_not_sent" in session:
        session.pop("approve_request_not_sent")
    if "github_oauth_token" in session:
        session.pop("github_oauth_token")
    if "pending_request_id" in session:
        session.pop("pending_request_id")
    return redirect(url_for("users.user_dashboard"))

@users_bp.route("/githuboauthlogin")
def user_githuboauthlogin():
    if "user_userid" in session:
        return redirect(url_for("users.user_dashboard"))
    elif "pending_request_id" in session:
        return redirect(url_for("users.user_not_approved"))
    session["user_login"] =True
    return redirect(url_for("auth.auth_root"))



