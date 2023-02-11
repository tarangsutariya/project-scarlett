from models import db


class deployments(db.Model):
    deploy_id = db.Column(db.Integer,primary_key = True)
    repo_id = db.Column(db.Integer)
    repo_name = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    accessed_by_org_token = db.Column(db.Boolean)
    org_token_id = db.Column(db.String)
    accessed_by_custom_token = db.Column(db.Boolean)
    custom_token = db.Column(db.String)
    repo_owner_id = db.Column(db.Integer)
    repo_owner = db.Column(db.String)
    server_id  = db.Column(db.Integer)
    deploy_path = db.Column(db.String)
    branch_name = db.Column(db.String)
    commit_hash = db.Column(db.String)
    health = db.Column(db.String)
    primary_domain = db.Column(db.String)
    secondary_domain = db.Column(db.String)
    initial_deploy = db.Column(db.Boolean)
    celery_process_id = db.Column(db.String)
    last_deployment_status = db.Column(db.String)
    deployment_process_desc = db.Column(db.String)
    cpu_allocated = db.Column(db.Integer)
    ram_allocated = db.Column(db.Integer)
    disk_allocated = db.Column(db.Float)
    cpu_usage = db.Column(db.Float)
    ram_usage =db.Column(db.Integer)
    disk_usage = db.Column(db.Float)
    interal_ip = db.Column(db.String)
    slack_nofity = db.Column(db.JSON)
    email_notify = db.Column(db.JSON)
    pushover_notify = db.Column(db.JSON)
    tap_device = db.Column(db.String)
    redeploy_process = db.Column(db.String)
    env_variables = db.Column(db.JSON)
    containers = db.Column(db.JSON)


class deployement_ports(db.Model):
    r_id = db.Column(db.Integer,primary_key = True)
    internal_port = db.Column(db.Integer)
    protocol = db.Column(db.String)
    custom_domain = db.Column(db.String)
    external_port = db.Column(db.Integer)
    

    







    