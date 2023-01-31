
#celery -A tasks.periodic_tasks worker --loglevel=info
#

#################
##for beats : celery -A tasks.periodic_tasks beat --loglevel=info
##for woorker : celery -A tasks.periodic_tasks worker --loglevel=info -n periodic
## for remote worker : celery -A tasks.remote_tasks worker --loglevel=info -Q que -n que1

from app import make_celery
from celery.utils.log import get_task_logger
from blueprints.admin.models import admin_servers
from .remote_tasks import tasktestq

logger = get_task_logger(__name__)

celery = make_celery()


@celery.task(name="serverhealthcheck")
def serverhealthcheck():
    
    svrs = admin_servers.query.filter_by().all()
    for svr in svrs:
        x = tasktestq.apply_async(args=[],queue='que')
        result = celery.control.inspect().active()
        logger.info(result)

       


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
