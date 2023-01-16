from flask import Blueprint,session,redirect,url_for,render_template,flash,request
import time

admin_manage = Blueprint("admin_manage",__name__,template_folder="templates",static_folder="static")


@admin_manage.route("/org/delete/<org>")
def dashoproot(org):
    time.sleep(10)
    return "HELLO"