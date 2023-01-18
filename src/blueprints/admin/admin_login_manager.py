from flask import redirect,session,url_for
from .models import admin_user
from functools import wraps

def admin_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "admin_username" in session:
            if admin_user.query.filter_by(username=session["admin_username"]).first()==None:
                session.pop("admin_username")
                return redirect(url_for("admin.admin_login"))

            return f(*args,**kwargs)
        else:
            
            return redirect(url_for('admin.admin_login'))
            # return redirect(url_for(admin_dashboard))

    return wrap