from flask import Blueprint,session,redirect,url_for
from functools import wraps
admin_bp = Blueprint("admin",__name__)


def admin_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        try:
            x = session["username"]
            return f(*args,**kwargs)
        except:
            print("HI")
            return redirect(url_for(admin_dashboard))
            # return redirect(url_for(admin_dashboard))

    return wrap

@admin_bp.route("/")
@admin_login_required
def admin_dashboard():
    # session["username"]="HLLO"
    return session["username"]


# @admin_bp.route("")