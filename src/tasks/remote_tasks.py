
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
from blueprints.admin.models import admin_servers
from blueprints.deployement.models import deployments
from models import db

celery = make_celery()

from celery.utils.log import get_task_logger
from celery.exceptions import Ignore

from config import storage_path,rootfs_path,kernel_path,vlan_ip_subnet_start,vlan_ip_subnet_end,default_network_interface,uid,gid

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
    subprocess.run(["sudo","ip","tuntap","add",tap_device,"mode","tap","user",str(uid),"group",str(gid)])
    subprocess.run(["sudo","ip","addr","add",tap_ip+"/24","dev",tap_device])
    subprocess.run(["sudo","ip","link","set",tap_device,"up"])
    subprocess.run(["sudo","sysctl","net.ipv4.ip_forward=1"])
    subprocess.run(["sudo","iptables","-t","nat","-A","POSTROUTING","-o",default_network_interface,"-j","MASQUERADE"])
    subprocess.run(["sudo","iptables","-A","FORWARD","-m","conntrack","--ctstate","RELATED,ESTABLISHED","-j","ACCEPT"])
    subprocess.run(["sudo","iptables","-A","FORWARD","-i",tap_device,"-o",default_network_interface,"-j","ACCEPT"])
    os.rmdir(temp_folder)

    self.update_state(state='PENDING', meta={'curr': 3, 'total': 9,"message":"Starting Firecracker"})
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
    logger.info(firecracker_pid)
    logger.info(firecracker_ip)
    self.update_state(state='PENDING', meta={'curr': 4, 'total': 9,"message":"message 4"})
   
    self.update_state(state='PENDING', meta={'curr': 5, 'total': 9,"message":"message 5"})

    self.update_state(state='PENDING', meta={'curr': 6, 'total': 9,"message":"message 6"})

    self.update_state(state='PENDING', meta={'curr': 7, 'total': 9,"message":"message 7"})

    self.update_state(state='PENDING', meta={'curr': 8, 'total': 9,"message":"message 8"})

    self.update_state(state='PENDING', meta={'curr': 9, 'total': 9,"message":"message 9"})
    logger.info(firecracker_ip)
    logger.info("DONE")






#######
#Cloudflare
#cf = CloudFlare.CloudFlare(token=cloudflare_api_key)
#cf.zones.get(params = {'name':"domain_name"})



# verifying deployment
# coping rootfs and kernel image
# preparing network devices
# starting firecracker vm
# git cloning
# running docker compose up(this may take some time)
# configuring network rules
# clean up
# Done redirecting


    
    
