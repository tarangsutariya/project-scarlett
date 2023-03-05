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
import copy
from celery.utils.log import get_task_logger
from celery.exceptions import Ignore

from config import storage_path,rootfs_path,kernel_path,vlan_ip_subnet_start,vlan_ip_subnet_end,default_network_interface,uid,gid,caddy_path,webhook_path
from config import cloudflare_api_key
from .manage_deploys import redeloy,gitfetch,dockerrebuild,deletedeploy

cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
logger = get_task_logger(__name__)

@celery.task
def process_webhook(branch_name,commit_hash,repo_id):
    deploys = deployments.query.filter_by(branch_name=branch_name,repo_id=repo_id).all()
    for dep in deploys:
        ###ONLY FOR TESTING
        if dep.deploy_id<=18:
            continue
        if dep.commit_hash == commit_hash:
            continue
        tokenn = users.query.filter_by(user_id=dep.user_id).first().github_oauth_token
        if dep.accessed_by_org_token == True:
            tokenn = admin_github_tokens.query.filter_by(token_id=dep.org_token_id).first().github_token
        elif dep.accessed_by_custom_token == True:
            tokenn = dep.custom_token
        g = Github(tokenn)
        b = g.get_repo(repo_id).get_branch(dep.branch_name).commit.sha
        if dep.initial_deploy:
            continue
        if b == dep.commit_hash:
            continue
        if dep.redeploy_process == "manual":
            continue
        svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
        if dep.redeploy_process == "hotreload":
            dep.celery_process_id = str(gitfetch.apply_async(args=[dep.deploy_id],queue=svr.domain_prefix))
            dep.last_deployment_status = "fetching changes"
        elif dep.redeploy_process == "rebuild":
            dep.celery_process_id = str(dockerrebuild.apply_async(args=[dep.deploy_id,True,False],queue=svr.domain_prefix))
            dep.last_deployment_status = "fetching changes"
        elif dep.redeploy_process == "redeploy":
            dep.celery_process_id = str(deletedeploy.apply_async(args=[dep.deploy_id,False,True],queue=svr.domain_prefix))
            dep.last_deployment_status = "fetching changes"
        db.session.commit()
        
        