# from src folder 
# celery -A tasks.tasks_ref worker


from app import make_celery
from celery import current_task
celery = make_celery()
import time


@celery.task(bind=True)
def smm(self,a,b):
    for i in range(0,10):
        time.sleep(2)
        current_task
        print(i)
        self.update_state(state='PROGRESS',
                meta={'current': i, 'total': 10})
    
    print(a+b)
    return a+b