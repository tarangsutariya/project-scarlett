from models import db
from werkzeug.security import generate_password_hash, check_password_hash

class admin_user(db.Model):
    admin_id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String)
    password_hash = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class admin_github_tokens(db.Model):
    token_id = db.Column(db.Integer,primary_key=True)
    token_name = db.Column(db.String)
    user_id = db.Column(db.Integer)
    github_token = db.Column(db.String)
    token_status = db.Column(db.String,default="working")
    is_oauth_token = db.Column(db.Boolean)
    github_user_id = db.Column(db.Integer)


class admin_token_orgs(db.Model):
    r_id = db.Column(db.Integer,primary_key=True)
    token_id = db.Column(db.Integer)
    org_id = db.Column(db.Integer)
    org_name = db.Column(db.String)

class admin_servers(db.Model):
    server_id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,primary_key=True)
    ip_address = db.Column(db.String)
    server_state = db.Column(db.String)
    domain_prefix = db.Column(db.String)
    server_health = db.Column(db.String)
    number_of_cores = db.Column(db.Integer)
    cpu_usage = db.Column(db.Float)
    total_ram = db.Column(db.Integer)
    ram_usage = db.Column(db.Integer)
    total_disk = db.Column(db.Float)
    disk_usage = db.Column(db.Float)


