from flask import Blueprint,session,redirect,url_for,render_template,flash,request,make_response
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,user_requests
import bcrypt
from .dashboard_manage import admin_manage
from github import Github


admin_bp = Blueprint("admin",__name__,template_folder="templates",static_folder="static")
admin_bp.register_blueprint(admin_manage,url_prefix="/manage")
class admin_user(db.Model):
    admin_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String)
    password_hash = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class admin_github_tokens(db.Model):
    token_id = db.Column(db.Integer,primary_key=True)
    token_name = db.Column(db.String)
    user_id = db.Column(db.Integer)
    github_token = db.Column(db.String)
    is_oauth_token = db.Column(db.Boolean)
    github_user_id = db.Column(db.Integer)


class admin_token_orgs(db.Model):
    r_id = db.Column(db.Integer,primary_key=True)
    token_id = db.Column(db.Integer)
    org_id = db.Column(db.Integer)
    org_name = db.Column(db.Integer)
    

     


    




def admin_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "admin_username" in session:
            
            return f(*args,**kwargs)
        else:
            
            return redirect(url_for('admin.admin_login'))
            # return redirect(url_for(admin_dashboard))

    return wrap

@admin_bp.route("/")
@admin_login_required
def admin_dashboard():
    user = admin_user.query.filter_by(username=session["admin_username"]).first()
    
    tokens = admin_github_tokens.query.filter_by(user_id=user.admin_id).all()
    orgs_details = []
    for token in tokens:
        
        orgs = admin_token_orgs.query.filter_by(token_id=token.token_id).all()
        for org in orgs:
            curr = {}
            curr["org_name"]=org.org_name
            curr["org_id"]=org.org_id
            curr["token_name"]=token.token_name
            curr["token_id"]=token.token_id
            orgs_details.append(curr)

    user_reqs = []
    for req in user_requests.query.filter_by().all():
        req_details = {}
        req_details["request_id"]=req.request_id
        req_details["message"]=req.request_message
        req_details["github_username"]=req.github_username
        user_reqs.append(req_details)

    
    response = make_response(render_template("dashboard.html",username=session["admin_username"],orgs_details=orgs_details,
        user_reqs=user_reqs))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # HTTP 1.1.
    response.headers["Pragma"] = "no-cache" # HTTP 1.0.
    response.headers["Expires"] = "0" # Proxies.
    return response




@admin_bp.route("/login",methods=["GET","POST"])
def admin_login():
    if "admin_username" in session:
        redirect(url_for("admin.admin_dashboard"))
    
    if admin_user.query.count()==0:
        
        return redirect(url_for("admin.admin_register"))
    if request.method=="POST":
        formdata = request.form.to_dict()
        if "username" not in formdata or formdata["username"]==None or formdata["username"]=="":
            flash("username is required")
            return redirect(url_for("admin.admin_login"))
        if "password" not in formdata or formdata["password"]==None or formdata["password"]=="":
            flash("password is required")
            return redirect(url_for("admin.admin_login"))
        u = admin_user.query.filter_by(username=formdata["username"]).first()
        if u==None:
            flash("USER NOT FOUND")
            return redirect(url_for("admin.admin_login"))
        if  not u.check_password(formdata["password"]):
            flash("Wrong password")
            return redirect(url_for("admin.admin_login"))
        session["admin_username"]=formdata["username"]
        return redirect(url_for("admin.admin_dashboard"))
        
    return render_template("login.html")


@admin_bp.route("/register",methods=["GET","POST"])
def admin_register():
    
    if admin_user.query.count()>0:
        
        return redirect(url_for("admin.admin_login"))
    if request.method=="GET":
        return render_template("register.html")
    formdata = request.form.to_dict()

    if "username" not in  formdata or formdata["username"]==None or formdata["username"]=="":
        flash("username cannot be empty")
        return render_template("register.html")
    if "password" not in formdata or formdata["password"]==None or formdata["password"]=="":
        flash("Please Enter password")
        return render_template("register.html")
    if "confirm_password" not in formdata or formdata["confirm_password"]==None or formdata["confirm_password"] == "":
        flash("Please confirm password")
        return render_template("register.html")
    if formdata["password"]!=formdata["confirm_password"]:
        flash("passwords dont match")
        return render_template("register.html")

    if admin_user.query.filter_by(username=formdata["username"]).first()!=None:
        flash("User already exists")
        return render_template("register.html")    

    
    u = admin_user(username=formdata["username"])
    u.set_password(formdata["password"])
    db.session.add(u)
    db.session.commit()
    flash("user created please login","success")
    return redirect(url_for("admin.admin_login"))



@admin_bp.route("/addtoken",methods=["GET","POST"])
@admin_login_required
def admin_add_token():
    if request.method=="GET":
        return render_template("add_token.html",username=session["admin_username"])
    form_data = request.form.to_dict()
    if "token_name" not in form_data or form_data["token_name"]==None or form_data["token_name"]=="":
        flash("Token name is required")
        return render_template("add_token.html",username=session["admin_username"])
    if "github_token" not in form_data or form_data["github_token"]==None or form_data["github_token"]=="":
        flash("Github personal token is required")
        return render_template("add_token.html",username=session["admin_username"])
    g = Github(form_data["github_token"])
    try:
        user_raw_data = g.get_user().raw_data
    except:
        flash("Invalid github token")
        return render_template("add_token.html",username=session["admin_username"])
    username = session["admin_username"]
    user_id = admin_user.query.filter_by(username=username).first().admin_id
    token_to_insert = admin_github_tokens(user_id=user_id,github_token=form_data["github_token"],
        is_oauth_token=False,github_user_id=user_raw_data["id"])
        
    db.session.add(token_to_insert)
    db.session.commit()
    token_to_insert.token_name = form_data["token_name"]
        
    db.session.commit()
    
    for org in g.get_user().get_orgs():
            if admin_token_orgs.query.filter_by(org_id=org.id).first()!= None:
                continue
            org_to_insert = admin_token_orgs(token_id=token_to_insert.token_id,org_id=org.id,org_name=org.login)
            db.session.add(org_to_insert)
            db.session.commit()


    return redirect(url_for("admin.admin_dashboard"))

@admin_bp.route("/logout")
@admin_login_required
def admin_logout():
    session.pop("admin_username")
    return redirect(url_for("admin.admin_dashboard"))



@admin_bp.route("/githuboauth")
@admin_login_required
def admin_github_oauth():
    session["admin_pannel"] = True
    return redirect(url_for("auth.auth_root"))


@admin_bp.route("/as")
@admin_login_required
def modaltest():
    return render_template("modaltest.html")