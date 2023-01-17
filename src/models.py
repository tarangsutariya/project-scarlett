from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class user_requests:
    request_id = db.Column(db.Integer,primary_key=True)
    github_user_id = db.Column(db.Integer)
    github_username = db.Column(db.String)
    github_token = db.Column(db.String)
    request_message = db.Column(db.Text)


class users:
    user_id = db.Column(db.Integer,primary_key=True)
    github_user_id = db.Column(db.Integer)
    github_username = db.Column(db.String)
    github_oauth_token = db.Column(db.String)

class user_orgs:
    r_id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer)
    github_org_id = db.Column(db.Integer)
    github_org_name = db.Column(db.String)

class user_tokens:
    r_id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer)
    github_token = db.Column(db.String)


