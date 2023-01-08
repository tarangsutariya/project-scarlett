from flask import Flask
from blueprints.adminpannel.admin import admin_bp
from config import secret_key
app = Flask(__name__)
app.secret_key=secret_key
app.register_blueprint(admin_bp,url_prefix="/admin")







if __name__ == "__main__":
    app.run(debug=True)