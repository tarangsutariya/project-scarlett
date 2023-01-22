#gunicorn -w 2 -k gevent "app:create_app()"
from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from blueprints.users.users import users_bp
from blueprints.admin.admin import admin_bp
from blueprints.auth.auth import auth_bp
from celery import Celery
from config import secret_key,postgres_uri,redis_uri


from models import db
from blueprints.auth.auth import oauth
from authlib.integrations.flask_client import OAuth






CELERY_TASK_LIST = [
    'tasks.tasks',
    'blueprints.admin.tasks'
   
]


def make_celery(app=None):
    app = app or create_app()

    celery = Celery(app.import_name, broker=redis_uri,backend=redis_uri,
                    include=CELERY_TASK_LIST)
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_uri
    app.secret_key=secret_key
    app.config["SQLALCHEMY_ECHO"]=True
    db.init_app(app)
    oauth.init_app(app)


    app.register_blueprint(admin_bp,url_prefix="/admin")

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp,url_prefix="/dashboard")
    return app
























# if __name__ == "__main__":
#     app.run(debug=True,host="0.0.0.0")