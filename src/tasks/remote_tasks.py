
from app import make_celery
import time
import subprocess
import psutil
import os
import shutil
import random
from blueprints.admin.models import admin_servers
from blueprints.deployement.models import deployments
from models import db

celery = make_celery()

from celery.utils.log import get_task_logger
from celery.exceptions import Ignore

from config import storage_path,rootfs_path,kernel_path

logger = get_task_logger(__name__)
@celery.task
def reportstats():
    domain_prefix =  celery.current_task.request.delivery_info["routing_key"]
    svr = admin_servers.query.filter_by(domain_prefix=domain_prefix).first()
    svr.number_of_cores = psutil.cpu_count()
    svr.cpu_usage = psutil.cpu_percent(interval=1)
    svr.total_ram = int(psutil.virtual_memory().total/1048576)
    svr.ram_usage = int(psutil.virtual_memory().used/1048576)
    svr.total_disk = round(psutil.disk_usage('/').total/1073741824,2)-1
    svr.disk_usage = round(psutil.disk_usage('/').used/1073741824,2)
    db.session.commit()


@celery.task(bind=True)
def initdeloy(self,deploy_id):
    self.update_state(state='PENDING', meta={'curr': 1, 'total': 9,"message":"verifying deployment request"})
    freespace = round(psutil.disk_usage('/').free/1073741824,2)-1
    total_ram = int(psutil.virtual_memory().total/1048576)
    number_of_cores = psutil.cpu_count()
    dep = deployments.query.filter_by(deploy_id=deploy_id).first()
    if dep == None or number_of_cores<dep.cpu_allocated or total_ram < dep.ram_allocated or freespace < dep.disk_allocated:
        self.update_state(state='FAILURE', meta={'curr': 9, 'total': 9,"message":"Server does not have free resouces to serve this request"})
        raise Ignore()
    ##Preparing rootfs
    self.update_state(state='PENDING', meta={'curr': 2, 'total': 9,"message":"Preparing rootfs"})
    root_fs_size = int(dep.disk_allocated*1024)
    str_path = os.path.join(storage_path, str(deploy_id))
    fs_path = os.path.join(str_path,"rootfs.ext4")
    k_path = os.path.join(str_path,"vmlinux")
    logger.info("COPYING File")
    shutil.copy(rootfs_path, fs_path)
    shutil.copy(kernel_path,k_path)
    subprocess.run(["truncate","-s",str(root_fs_size)+"M",fs_path])
    subprocess.run(["resize2fs",rootfs_path])


     

    


    




    self.update_state(state='PENDING', meta={'curr': 3, 'total': 9,"message":"message 3"})
  
    logger.info("3")
    self.update_state(state='PENDING', meta={'curr': 4, 'total': 9,"message":"message 4"})
   
    self.update_state(state='PENDING', meta={'curr': 5, 'total': 9,"message":"message 5"})

    self.update_state(state='PENDING', meta={'curr': 6, 'total': 9,"message":"message 6"})

    self.update_state(state='PENDING', meta={'curr': 7, 'total': 9,"message":"message 7"})

    self.update_state(state='PENDING', meta={'curr': 8, 'total': 9,"message":"message 8"})

    self.update_state(state='PENDING', meta={'curr': 9, 'total': 9,"message":"message 9"})
    logger.info("DONE")






#######
#Cloudflare
#cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
#cf.zones.get(params = {'name':"domain_name"})



# verifying deployment
# preparing rootfs
# copying rootfs and kernel image
# starting firecracker vm
# git cloning
# running docker compose up(this may take some time)
# configuring network rules
# clean up
# Done redirecting


    
    
