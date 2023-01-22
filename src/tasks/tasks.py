from app import make_celery

celery = make_celery()



@celery.task()
def smm(a,b):
    

    print(a+b)
    return a+b