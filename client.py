import xmlrpc.client
import ssl
import random
context=ssl._create_unverified_context()
s = xmlrpc.client.ServerProxy('https://localhost:9800',context=context,allow_none=True)

key="oQNxVe6ZL06N6vq79LLFqHtCi3mtA8uDHTKCj52wVN0IwQpvl3"
#ret=s.get_methods("","Core",1,2,3)

#ret=s.test(key,"TestPlugin",1,4)
#ret=s.lliurex_version(key,"LliurexVersion")

#ret=s.test(key,"TestPlugin",1,4)
#print(ret)

#ret=s.get_methods()
#print(ret["return"])

#ret=s.get_variable("SLAVE_BLACKLIST")
#print(ret)

'''
ret=s.get_variables()

for var in ret["return"]:
	print("%s=%s"%(var,ret["return"][var]))
print()

ret=s.set_variable(key,"TRALARI",123)
print(ret)

extra_info={}
extra_info["comment"]="Molo mogollon"
extra_info["volatile"]=True

ret=s.set_variable(key,"TRALARO",1234,extra_info)
print(ret)
print()

ret=s.get_variables(True)


for var in ret["return"]:
	print("%s=%s"%(var,ret["return"][var]))

'''

ret=s.create_ticket("cless")
print(ret)

f=open("/run/n4d/tickets/cless")
password=f.readline()
f.close()


'''
ret=s.set_variable(("cless",password),"REMOTE_VARIABLES_SERVER","127.0.0.1")
print(ret)

ret=s.get_variable("SRV_IP")
print(ret)
ret=s.delete_variable(("cless",password),"REMOTE_VARIABLES_SERVER")
print(ret)

'''

#ret=s.set_variable(("cless",password),"REMOTE_VARIABLES_SERVER","127.0.0.1")
#print(ret)

ret=s.get_variables()
print(ret)

