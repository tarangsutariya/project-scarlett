
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


@celery.task(bind=True)
def initdeloy(self,deploy_id):
    def initdeloy(self,deploy_id):
    # self.update_state(state='PENDING', meta={'curr': 1, 'total': 9,"message":"message 1"})
    # time.sleep(7)
    # logger.info("1")
    # self.update_state(state='PENDING', meta={'curr': 2, 'total': 9,"message":"message 2"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 3, 'total': 9,"message":"message 3"})
    # time.sleep(7)
    # logger.info("3")
    # self.update_state(state='PENDING', meta={'curr': 4, 'total': 9,"message":"message 4"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 5, 'total': 9,"message":"message 5"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 6, 'total': 9,"message":"message 6"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 7, 'total': 9,"message":"message 7"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 8, 'total': 9,"message":"message 8"})
    # time.sleep(7)
    # self.update_state(state='PENDING', meta={'curr': 9, 'total': 9,"message":"message 9"})
        logger.info("DONE")


# verifying deployment
# preparing rootfs
# copying rootfs and kernel image
# starting firecracker vm
# git cloning
# running docker compose up(this may take some time)
# configuring network rules
# clean up
# Done redirecting


    
    
