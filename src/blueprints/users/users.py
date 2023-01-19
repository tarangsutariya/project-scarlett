from flask import Blueprint,session,redirect,url_for,render_template,flash,request,abort
from models import db,user_requests,users
from .login_manager import user_login_required
import time
users_bp = Blueprint("users",__name__,template_folder="templates",static_folder="static")



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




@users_bp.route("/logout")
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



