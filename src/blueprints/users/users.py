from flask import Blueprint,session,redirect,url_for,render_template,flash,request

from .login_manager import user_login_required

users_bp = Blueprint("users",__name__,template_folder="templates",static_folder="static")



@users_bp.route("/")
@user_login_required
def user_dashboard():
    return "hello"

@users_bp.route("/login")
def user_login():
    return render_template("user_login.html")


@users_bp.route("/requestaccess")
def user_request_access():
    return render_template("user_requestaccess.html")

@users_bp.route("/notapproved")
def user_not_approved():
    return render_template("user_notapproved.html")



@users_bp.route("/githuboauthlogin")
def user_githuboauthlogin():
    if "user_userid" in session:
        return redirect(url_for("users.dashboard"))
    elif "not_approved" in session:
        return redirect(url_for("users.user_not_approved"))
    session["user_login"] =True
    return redirect(url_for("auth.auth_root"))

