from flask import Blueprint,render_template,session,redirect,url_for,request,flash
from ..admin_login_manager import admin_login_required
from ..models import admin_user
from models import db
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
    return render_template("server_settings.html",username=session["admin_username"])