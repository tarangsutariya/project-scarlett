from flask import Flask

from flask_sqlalchemy import SQLAlchemy

from blueprints.admin.admin import admin_bp
from blueprints.auth.auth import auth_bp
from config import secret_key,postgres_uri
from models import db


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
app.secret_key=secret_key
app.config["SQLALCHEMY_ECHO"]=True
db.init_app(app)


app.register_blueprint(admin_bp,url_prefix="/admin")
app.register_blueprint(auth_bp,url_prefix="/auth")








if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")