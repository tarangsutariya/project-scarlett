import socket
from fabric import Connection
def tryPort(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except:
        pass
    sock.close()
    return result



def vm_usage(ip):
    stats = {}
    with Connection("root@"+ip) as c:
        free_output = c.run("free",hide=True).stdout
        df_output = c.run("df /",hide=True).stdout
        uptime_output = c.run("uptime",hide=True).stdout
    free_output = free_output.strip().split()
    stats["ram_total"]=int(free_output[7])//1024
    stats["ram_usage"]=int(free_output[8])//1024
    df_output=df_output.strip().split()
    stats["disk_total"]=round((int(df_output[-4])+int(df_output[-3]))/1024/1024,2)
    stats["disk_usage"]=round((int(df_output[-4]))/1024/1024,2)
    uptime_output=uptime_output.strip().split()
    stats["load_average"]=float(uptime_output[-3][:-1])
    return stats
