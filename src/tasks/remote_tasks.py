
from app import make_celery
import time

import psutil


from blueprints.admin.models import admin_servers
from models import db

celery = make_celery()
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
@celery.task
def reportstats():
    domain_prefix =  celery.current_task.request.delivery_info["routing_key"]
    svr = admin_servers.query.filter_by(domain_prefix=domain_prefix).first()
    svr.number_of_cores = psutil.cpu_count()
    svr.cpu_usage = psutil.cpu_percent(interval=1)
    svr.total_ram = int(psutil.virtual_memory().total/1048576)
    svr.ram_usage = int(psutil.virtual_memory().used/1048576)
    svr.total_disk = round(psutil.disk_usage('/').total/1073741824,2)
    svr.disk_usage = round(psutil.disk_usage('/').used/1073741824,2)
    db.session.commit()


@celery.task
def initdeloy(deploy_id):
    logger.info("RECIEVED CELERY TASK")

    
    
