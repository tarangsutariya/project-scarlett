
#celery -A tasks.periodic_tasks worker --loglevel=info
#

#################
##for beats : celery -A tasks.periodic_tasks beat --loglevel=info
##for woorker : celery -A tasks.periodic_tasks worker --loglevel=info -n periodic
## for remote worker : celery -A tasks.remote_tasks worker --loglevel=info -Q first -n first

from app import make_celery
from celery.utils.log import get_task_logger
from blueprints.admin.models import admin_servers
from .remote_tasks import reportstats
from models import db
logger = get_task_logger(__name__)

celery = make_celery()


@celery.task(name="serverhealthcheck")
def serverhealthcheck():
    
    
    active_workers_ping = celery.control.inspect().ping()
    active_workers = []
    for worker in active_workers_ping:
        worker_name = worker[7:]
        if worker_name == "periodic":
            continue
        active_workers.append(worker_name)
    
    servers_offline = admin_servers.query.filter_by().all()
    for offline_svr in servers_offline:
        if offline_svr.domain_prefix in active_workers:
            continue
        
        offline_svr.server_health = "offline"
        offline_svr.number_of_cores = None
        offline_svr.total_ram = None
        offline_svr.cpu_usage = None
        offline_svr.ram_usage = None
        offline_svr.total_disk = None
        offline_svr.disk_usage = None
        db.session.commit()
    
    for svr in active_workers:
        svr_mod = admin_servers.query.filter_by(domain_prefix=svr).first()
        if svr_mod==None:
            continue
        svr_mod.server_health = "healthy"
        db.session.commit()
        reportstats.apply_async(args=[],queue=svr)
    
    

       


@celery.on_after_configure.connect
def add_periodic(sender, **kwargs):
    
    
    sender.add_periodic_task(60, serverhealthcheck.s(), name='serverhealthcheck',expires=300)

# add periodic tasks here
# example periodic task
# @celery.task(name="everyminute")
# def periodt():  
#     logger.info("hello")

# @celery.on_after_configure.connect
# def add_periodic(sender, **kwargs):
#     sender.add_periodic_task(3, periodt.s(), name='add every 10',expires=10)
