from flask import Blueprint,session,redirect,url_for,render_template,flash,request
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
import bcrypt
admin_bp = Blueprint("admin",__name__,template_folder="templates",static_folder="static")

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
    return render_template("dashboard.html",username=session["admin_username"])


# @admin_bp.route("/check/<password>")
# def checkpass(password):
#     u =  admin_user.query.filter_by(username="test1").first()
#     return str(u.check_password(password))

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
    flash("user created please login")
    return redirect(url_for("admin.admin_login"))



@admin_bp.route("/addtoken",methods=["GET","POST"])
@admin_login_required
def admin_add_token():
    if request.method=="GET":
        return render_template("add_token.html",username=session["admin_username"])

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