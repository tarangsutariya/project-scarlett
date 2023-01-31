
#celery -A tasks.periodic_tasks worker --loglevel=info
#

from app import make_celery
from celery.utils.log import get_task_logger
from blueprints.admin.models import admin_servers


logger = get_task_logger(__name__)

celery = make_celery()


@celery.task(name="serverhealthcheck")
def serverhealthcheck():
    
    svrs = admin_servers.query.filter_by().all()
    for svr in svrs:
        logger.info(svr.ip_address)


@celery.on_after_configure.connect
def add_periodic(sender, **kwargs):
    
    
    sender.add_periodic_task(3, serverhealthcheck.s(), name='serverhealthcheck',expires=10)

# add periodic tasks here
# example periodic task
# @celery.task(name="everyminute")
# def periodt():  
#     logger.info("hello")

# @celery.on_after_configure.connect
# def add_periodic(sender, **kwargs):
#     sender.add_periodic_task(3, periodt.s(), name='add every 10',expires=10)
