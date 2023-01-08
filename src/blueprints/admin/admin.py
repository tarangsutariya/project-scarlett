from flask import Blueprint,session,redirect,url_for,render_template,flash,request
from functools import wraps
from models import db

admin_bp = Blueprint("admin",__name__,template_folder="templates",static_folder="static")



def admin_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "username" in session:
            
            return f(*args,**kwargs)
        else:
            
            return redirect(url_for('admin.admin_login'))
            # return redirect(url_for(admin_dashboard))

    return wrap

@admin_bp.route("/")
@admin_login_required
def admin_dashboard():
    
    # session["username"]="HLLO"
    #return session["username"]
    return "dashboard"

@admin_bp.route("/login",methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        flash("Wrong Credentials try again!")

        
    return render_template("login.html")