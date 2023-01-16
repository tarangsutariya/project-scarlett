from flask import Blueprint,session,redirect,url_for,render_template,flash,request

users_bp = Blueprint("users",__name__,template_folder="templates",static_folder="static")


@users_bp.route("/")
def user_dashboard():
    return "hello"

