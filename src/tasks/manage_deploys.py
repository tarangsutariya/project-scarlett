from app import make_celery
import time
import subprocess
import psutil
import os
import sys
import platform
from subprocess import Popen, PIPE
import shutil
import random
import json
from blueprints.admin.models import admin_servers,admin_github_tokens
from blueprints.deployement.models import deployments
from models import db,users
from github import Github
from fabric import Connection
from .helpers.caddy_editor import Caddy
import requests
import CloudFlare
from .helpers.utils import tryPort,vm_usage
import python_on_whales
celery = make_celery()

from celery.utils.log import get_task_logger
from celery.exceptions import Ignore

from config import storage_path,rootfs_path,kernel_path,vlan_ip_subnet_start,vlan_ip_subnet_end,default_network_interface,uid,gid,caddy_path,webhook_path
from config import cloudflare_api_key


cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
logger = get_task_logger(__name__)




@celery.task
def update_env_variables(deploy_id):
    dep = deployments.query.filter_by(deploy_id=deploy_id).first()
    with open("/tmp/env","w+") as envf:
        for envs in dep.env_variables:
            envf.write("%s=%s\n"%(str(envs),str(dep.env_variables[envs])))
    ssh_connect_retries = 0
    while ssh_connect_retries < 5:
        try:
            Connection("root@"+dep.internal_ip,connect_timeout=10).run("hostname")
            
            break
        except:
            time.sleep(10)
            ssh_connect_retries+=1
    if ssh_connect_retries>=5:
        raise Exception("SSH CONNECTION TIMED OUT")
    Connection("root@"+dep.internal_ip,connect_timeout=10).put("/tmp/env",'repo/.env')