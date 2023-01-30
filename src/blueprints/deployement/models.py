from models import db


class deployments(db.Model):
    deploy_id = db.Column(db.Integer,primary_key = True)
    repo_id = db.Column(db.Integer)
    repo_name = db.Column(db.Integer)
    repo_owner = db.Column(db.Integer)
    server_id  = db.Column(db.String)
    deploy_path = db.Column(db.String)
    branch_name = db.Column(db.String)
    commit_hash = db.Column(db.String)
    health = db.Column(db.String)
    primary_domain = db.Column(db.String)
    secondary_domain = db.Column(db.String)
    last_deployment = db.Column(db.String)
    last_deployment_status = db.Column(db.Strig)




    