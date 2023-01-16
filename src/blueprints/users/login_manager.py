from functools import wraps
from flask import session,url_for,redirect

def user_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "user_userid" in session:
            
            return f(*args,**kwargs)
        else:
            
            return redirect(url_for('users.user_login'))
            # return redirect(url_for(admin_dashboard))

    return wrap


