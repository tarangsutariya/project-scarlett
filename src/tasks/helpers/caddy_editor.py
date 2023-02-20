class Caddy:
    def __init__(self,caddy_path):
        self.caddy_file_path = caddy_path
    def add(self,domain,ip,port):
        with open(self.caddy_file_path,'a') as c:
            c.write("%s {\n"%(domain))
            c.write("reverse_proxy %s:%s\n"%(str(ip),str(port)))
            c.write("}\n")
    def remove(self,domain):
        skip = 0
        with open(self.caddy_file_path,'r') as c:
            contents = c.readlines()
            with open(self.caddy_file_path,'w') as wr:
                for lines in contents:
                    if skip!=0:
                        skip-=1
                        continue
                    elif domain in lines:
                        skip = 2
                        continue
                    else:
                        wr.write(lines)