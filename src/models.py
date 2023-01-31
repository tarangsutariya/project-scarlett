from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()


class user_requests(db.Model):
    request_id = db.Column(db.Integer,primary_key=True)
    github_user_id = db.Column(db.Integer)
    github_username = db.Column(db.String)
    github_token = db.Column(db.String)
    request_message = db.Column(db.Text)


class users(db.Model):
    user_id = db.Column(db.Integer,primary_key=True)
    github_user_id = db.Column(db.Integer)
    github_username = db.Column(db.String)
    github_oauth_token = db.Column(db.String)

class user_orgs(db.Model):
    r_id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer)
    github_org_id = db.Column(db.Integer)
    github_org_name = db.Column(db.String)

class user_tokens(db.Model):
    r_id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer)
    github_token = db.Column(db.String)

class user_deployments(db.Model):
    r_id = db.Column(db.Integer,primary_key = True)
    user_id = db.Column(db.Integer)
    deploy_id = db.Column(db.Integer)

from blueprints.admin.models import admin_servers

