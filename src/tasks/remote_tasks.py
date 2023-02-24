
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
    self.update_state(state='PENDING', meta={'curr': 2, 'total': 9,"message":"coping rootfs and kernel image"})
    ###SELECTING TAP DEVICE AND IPRANGE
    second_octet_start = int(vlan_ip_subnet_start.split(".")[1])+1
    second_octet_end = int(vlan_ip_subnet_end.split(".")[1])
    third_octet_start = int(vlan_ip_subnet_start.split(".")[2])+1
    third_octet_end = int(vlan_ip_subnet_end.split(".")[2])
    tap_device = "tap"+str(random.randint(second_octet_start,second_octet_end))+"e"+str(random.randint(third_octet_start,third_octet_end))
    interfacetaken = subprocess.run(['/sbin/ifconfig',tap_device],capture_output=True, text=True)
    while interfacetaken.returncode==0:
        tap_device = "tap"+str(random.randint(second_octet_start,second_octet_end))+"e"+str(random.randint(third_octet_start,third_octet_end))
        interfacetaken = subprocess.run(['/sbin/ifconfig',tap_device],capture_output=True, text=True)
        
    tap_ip = vlan_ip_subnet_start.split(".")[0]+"."+tap_device[3:].split('e')[0]+"."+tap_device[3:].split('e')[1]
    firecracker_ip = tap_ip
    firecracker_ip+=".2"
    tap_ip+=".1"
    root_fs_size = int(dep.disk_allocated*1024)
    str_path = os.path.join(storage_path, str(deploy_id))
    os.mkdir(str_path)
    fs_path = os.path.join(str_path,"rootfs.ext4")
    k_path = os.path.join(str_path,"vmlinux")
    logger.info("COPYING File")
    shutil.copy(rootfs_path, fs_path)
    shutil.copy(kernel_path,k_path)
    subprocess.run(["truncate","-s",str(root_fs_size)+"M",fs_path])
    #subprocess.run(["/sbin/e2fsck","-f",fs_path])
    subprocess.run(["/sbin/resize2fs",fs_path])
    temp_folder = os.path.join("/tmp",tap_device+'d'+str(deploy_id))
    os.mkdir(temp_folder)
    subprocess.run(["sudo","mount",fs_path,temp_folder])
    subprocess.run(["sudo","chmod","777",os.path.join(temp_folder,"etc/local.d/networkinit.start")])
    with open(os.path.join(temp_folder,"etc/local.d/networkinit.start"),"w") as networkinitscript:
        networkinitscript.write("#!/bin/sh\n")
        networkinitscript.write("ifconfig eth0 up && ip addr add dev eth0 %s/24\n"%(firecracker_ip))
        networkinitscript.write("ip route add default via %s && echo nameserver 8.8.8.8 > /etc/resolv.conf"%(tap_ip))
    subprocess.run(["sudo","umount",temp_folder])
    
    self.update_state(state='PENDING', meta={'curr': 3, 'total': 9,"message":"Starting Firecracker"})

    subprocess.run(["sudo","ip","tuntap","add",tap_device,"mode","tap","user",str(uid),"group",str(gid)])
    subprocess.run(["sudo","ip","addr","add",tap_ip+"/24","dev",tap_device])
    subprocess.run(["sudo","ip","link","set",tap_device,"up"])
    subprocess.run(["sudo","sysctl","net.ipv4.ip_forward=1"])
    subprocess.run(["sudo","iptables","-t","nat","-A","POSTROUTING","-o",default_network_interface,"-j","MASQUERADE"])
    subprocess.run(["sudo","iptables","-A","FORWARD","-m","conntrack","--ctstate","RELATED,ESTABLISHED","-j","ACCEPT"])
    subprocess.run(["sudo","iptables","-A","FORWARD","-i",tap_device,"-o",default_network_interface,"-j","ACCEPT"])
    os.rmdir(temp_folder)

    self.update_state(state='PENDING', meta={'curr': 4, 'total': 9,"message":"Starting Firecracker"})
    ##LAUNChING FIRECRACKER PROCESS
    kwargs = {}
    if platform.system() == 'Windows':
      
        CREATE_NEW_PROCESS_GROUP = 0x00000200  
        DETACHED_PROCESS = 0x00000008         
        kwargs.update(creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, close_fds=True)  
    elif sys.version_info < (3, 2): 
        kwargs.update(preexec_fn=os.setsid)
    else: 
        kwargs.update(start_new_session=True)
    firecracker_socket = "/tmp/firecracker"+tap_device[3:]+".socket"
    p = Popen(["sudo","firecracker","--api-sock",firecracker_socket], stdin=PIPE, stdout=PIPE, stderr=PIPE, **kwargs)
    ###########################
    firecracker_pid = p.pid
    
    logger.info(firecracker_pid)
    fire_kernel_json = {
            "kernel_image_path": k_path,
            "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"
    }
    json_dump = json.dumps(fire_kernel_json)
    with open("/tmp/scarlett_curl.json","w") as f:
        f.write(json_dump)
    subprocess.run(["sudo","curl","--unix-socket",firecracker_socket,"-i","-X","PUT","http://localhost/boot-source","-H","'Accept: application/json'","-H","'Content-Type: application/json'","-d","@/tmp/scarlett_curl.json" ] )
    fire_rootfs_json = {
        "drive_id": "rootfs",
        "path_on_host": fs_path,
        "is_root_device": True,
        "is_read_only": False
    }
    json_dump = json.dumps(fire_rootfs_json)
    with open("/tmp/scarlett_curl.json","w") as f:
        f.write(json_dump)
    subprocess.run(["sudo","curl","--unix-socket",firecracker_socket,"-i","-X","PUT","http://localhost/drives/rootfs","-H","'Accept: application/json'","-H","'Content-Type: application/json'","-d","@/tmp/scarlett_curl.json" ] )
    fire_network_interface = {
      "iface_id": "eth0",
      "guest_mac": ("02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))).upper(),
      "host_dev_name": tap_device
    }
    
    json_dump = json.dumps(fire_network_interface)
    with open("/tmp/scarlett_curl.json","w") as f:
        f.write(json_dump)
    subprocess.run(["sudo","curl","--unix-socket",firecracker_socket,"-i","-X","PUT","http://localhost/network-interfaces/eth0","-H","'Accept: application/json'","-H","'Content-Type: application/json'","-d","@/tmp/scarlett_curl.json" ] )
    fire_specs_json = {
      "vcpu_count": dep.cpu_allocated,
      "mem_size_mib": dep.ram_allocated
    }
    json_dump = json.dumps(fire_specs_json)
    with open("/tmp/scarlett_curl.json","w") as f:
        f.write(json_dump)
    subprocess.run(["sudo","curl","--unix-socket",firecracker_socket,"-i","-X","PUT","http://localhost/machine-config","-H","'Accept: application/json'","-H","'Content-Type: application/json'","-d","@/tmp/scarlett_curl.json" ] )
    fire_action_json = {
      "action_type": "InstanceStart"
    }
    json_dump = json.dumps(fire_action_json)
    with open("/tmp/scarlett_curl.json","w") as f:
        f.write(json_dump)
    subprocess.run(["sudo","curl","--unix-socket",firecracker_socket,"-i","-X","PUT","http://localhost/actions","-H","'Accept: application/json'","-H","'Content-Type: application/json'","-d","@/tmp/scarlett_curl.json" ] )
    

    with open("/tmp/env","w+") as envf:
        for envs in dep.env_variables:
            envf.write("%s=%s\n"%(str(envs),str(dep.env_variables[envs])))
    logger.info(firecracker_ip)
    self.update_state(state='PENDING', meta={'curr': 5, 'total': 9,"message":"Git cloning"})
    ssh_connect_retries = 0
    while ssh_connect_retries < 5:
        try:
            Connection("root@"+firecracker_ip,connect_timeout=10).run("hostname")
            break
        except:
            time.sleep(10)
            ssh_connect_retries+=1
    if ssh_connect_retries>=5:
        raise Exception("SSH CONNECTION TIMED OUT")
    tokenn = users.query.filter_by(user_id=dep.user_id).first().github_oauth_token
    if dep.accessed_by_org_token == True:
        tokenn = admin_github_tokens.query.filter_by(token_id=dep.org_token_id).first().github_token
    elif dep.accessed_by_custom_token == True:
        tokenn = dep.custom_token
    hook_success  = True
    try:
        g = Github(tokenn)
        repo = g.get_repo(dep.repo_id)
        hooks = repo.get_hooks()
        already_set = False
        for hook in hooks:
            if hook.raw_data["config"]["url"]==webhook_path:
                already_set=True
                break
        if not already_set:
            repo.create_hook(name="web",config={'content_type': 'json', 'insecure_ssl': '0', 'url': webhook_path})
    except:
        hook_success = False
    
    with Connection("root@"+firecracker_ip) as ssh_connection:
        ssh_connection.run("git clone https://%s@%s repo"%(tokenn,"github.com/"+dep.repo_owner+"/"+dep.repo_name))
        ssh_connection.run("cd repo && git checkout %s"%(dep.branch_name))
        ssh_connection.put("/tmp/env",'repo/.env')
    logger.info("git clone done")
    self.update_state(state='PENDING', meta={'curr': 6, 'total': 9,"message":"running docker compose up"})
    compose_success = True
    try:
        with Connection("root@"+firecracker_ip) as ssh_connection:
            ssh_connection.run("cd repo && docker compose up -d")
    except:
        compose_success = False

    self.update_state(state='PENDING', meta={'curr': 7, 'total': 9,"message":"Configuring network rules"})
    
    p_cps = dep.primary_domain.split(".")
    base_domain_p = p_cps[-2]+"."+ p_cps[-1]
    prefix_p = ""
    for i in range(0,len(p_cps)-2):
        prefix_p+=p_cps[i]
        prefix_p+='.'
    prefix_p=prefix_p[:-1]

    s_cps = dep.secondary_domain.split(".")
    base_domain_s = s_cps[-2]+"."+ s_cps[-1]
    prefix_s = ""
    for i in range(0,len(s_cps)-2):
        prefix_s+=s_cps[i]
        prefix_s+='.'
    prefix_s=prefix_s[:-1]
    svr = admin_servers.query.filter_by(server_id=dep.server_id).first()
    zone_id = cf.zones.get(params = {'name':base_domain_p})[0]["id"]
    cf.zones.dns_records.post(zone_id, data={"name":prefix_p,"type":"A","content":svr.ip_address})

    zone_id = cf.zones.get(params = {'name':base_domain_s})[0]["id"]
    cf.zones.dns_records.post(zone_id, data={"name":prefix_s,"type":"A","content":svr.ip_address})
    caddy = Caddy(caddy_path)
    caddy.add(dep.primary_domain,firecracker_ip,80)
    headers = {
        'Content-Type': 'text/caddyfile',
    }
    caddy.add(dep.secondary_domain,firecracker_ip,80)


    with open(caddy_path, 'rb') as f:
        data = f.read()

    response = requests.post('http://localhost:2019/load', headers=headers, data=data)
    
    
    self.update_state(state='PENDING', meta={'curr': 8, 'total': 9,"message":"Performing clean-up"})
    #####
    kwargs = {}
    if platform.system() == 'Windows':
      
        CREATE_NEW_PROCESS_GROUP = 0x00000200  
        DETACHED_PROCESS = 0x00000008         
        kwargs.update(creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, close_fds=True)  
    elif sys.version_info < (3, 2): 
        kwargs.update(preexec_fn=os.setsid)
    else: 
        kwargs.update(start_new_session=True)
    socat_port = random.randint(20000,40000)
    while not tryPort(socat_port):
            socat_port = random.randint(20000,40000)
    socat = Popen(["socat","TCP4-LISTEN:%s,fork"%(socat_port),"TCP4:%s:22"%(firecracker_ip)], stdin=PIPE, stdout=PIPE, stderr=PIPE, **kwargs)
    usage = vm_usage(firecracker_ip)
    port_forwarded = {"socat_pid":socat.pid,"external_port":socat_port,"type":"SSH","internal_port":22}
    logger.info(socat_port)
#####
    dep.ram_usage = usage["ram_usage"]
    dep.disk_usage = usage["disk_usage"]
    dep.cpu_usage=int(usage["load_average"]/dep.cpu_allocated)
    dep.initial_deploy=False
    dep.hook_set = hook_success
    dep.deploy_path = str_path
    if compose_success:
        dep.health="healthy"
        dep.last_deployment_status="Deployed"
        dep.deployment_process_desc="Successfully deployed"
    else:
        dep.health="failure"
        dep.last_deployment_status="composeerror"
        dep.deployment_process_desc="docker compose failed"
    dep.tap_device=tap_device
    dep.interal_ip=firecracker_ip
    dep.firecracker_ip=firecracker_pid
    dep.firecracker_socket=firecracker_socket
    dep.forwarded_ports = port_forwarded
    docker = python_on_whales.DockerClient(host="ssh://root@%s"%(firecracker_ip))
    containers = list(docker.ps())
    contn = {}
    for container in containers:
        contn[container.id]=container.name[5:-2]
    dep.containers = contn
    db.session.commit()

    
    
    self.update_state(state='PENDING', meta={'curr': 9, 'total': 9,"message":"Done"})
    logger.info(firecracker_ip)
    logger.info("DONE")

# ##SHUTDOWN
# from celery.signals import worker_shutdown
# def at_shoutdown(sender, **k):
#     print("SHUTTING DOWN")


# ##STARTUP
# from celery.signals import worker_ready
# @worker_ready.connect
# @celery.task(bind=True)
# def at_start(self,sender, **k):
    
#     # if gethostname()=="periodic":
#     #     return
    


######
### r.create_hook(name="web",config={'content_type': 'json', 'insecure_ssl': '0', 'url': 'http://arm.tarang.uk:5000/webhook/'})
#git clone url foldername
#git fetch
#git merge
#socat TCP4-LISTEN:8111,fork,bind=127.0.0.1 TCP4:10.156.166.2:80
#######
#Cloudflare
#cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
#
###x = datetime.now()-(dt_object+diff)
###dt_object = datetime.strptime(utc_string, '%Y-%m-%dT%H:%M:%S.%fZ')


# verifying deployment
# coping rootfs and kernel image
# preparing network devices
# starting firecracker vm
# git cloning
# running docker compose up(this may take some time)
# configuring network rules
# clean up
# Done redirecting


    
    
