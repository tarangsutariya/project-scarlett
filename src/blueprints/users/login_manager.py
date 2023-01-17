from functools import wraps
from flask import session,url_for,redirect
from models import users
def user_login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if "approve_request_not_sent" in session:
            return redirect(url_for("users.user_request_access"))
        if "pending_request_id" in session:
            return redirect(url_for("users.user_not_approved"))
        if "user_userid" in session:
            if users.query.filter_by(user_id=session["user_userid"]).first() != None:
                return f(*args,**kwargs)
            else:
                session.pop("user_userid")
        
            
        return redirect(url_for('users.user_login'))
            
    return wrap


