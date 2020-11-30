import xmlrpc.client
import ssl
import random
import os
context=ssl._create_unverified_context()
s = xmlrpc.client.ServerProxy('https://localhost:9779',context=context,allow_none=True)

user=os.environ["USER"]

ret=s.create_ticket(user)
print(ret)

f=open("/run/n4d/tickets/%s"%user)
password=f.readline()
f.close()

ret=s.set_variable((user,password),"TRALARI","127.0.0.1")
print(ret)

ret=s.get_variables()
print(ret)

ret=s.delete_variable((user,password),"TRALARI")
print(ret)

ret=s.get_variables()
print(ret)