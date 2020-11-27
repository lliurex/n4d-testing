import n4d.responses
import xmlrpc.client
import ssl
import threading
import time
import socket
import os
import json

import n4d.server.core

class ClientManager:
	
	REGISTER_SLEEP_TIME=60*5
	RUN_DIR="/run/n4d/clients/"
	CLIENTS_FILE=RUN_DIR+"clients.json"
	MACHINE_FILE="/etc/machine-id"
	
	def __init__(self):
		
		self.clients={}
		self.core=n4d.server.core.Core.get_core()
		self.server_id=None
		if not os.path.exists(ClientManager.RUN_DIR):
			os.makedirs(ClientManager.RUN_DIR)
		self.load_clients_file()
		self.start_register_to_server_thread()
		
	#def __init__
	
	def startup(self,options):

		pass
		
	#def startup
	
	def dprint(self,data):
		if self.core.DEBUG:
			print("[ClientManager] %s"%str(data))
	#def dprint
	
	def register_client(self,protected_ip,mac,machine_id):
		
		client={}
		client["last_check"]=int(time.time())
		client["missed_pings"]=0
		client["ip"]=protected_ip
		client["mac"]=mac
				
		self.clients[machine_id]=client
		self.save_clients_file()
		#self.dprint("Client [%s] %s - %s registered"%(machine_id,mac,protected_ip))
		
		return n4d.responses.build_call_successful_response(self.core.id,"Client added")
		
	#def register_instance
	
	def start_register_to_server_thread(self):
		
		self.register_thread=threading.Thread(target=self.register_to_server)
		self.register_thread.daemon=True
		self.register_thread.start()
	
	def register_to_server(self):
		
		#self.dprint("Starting register thread...")
		
		while True:
		
			try:
				ret=self.core.variables_manager.get_variable("REMOTE_VARIABLES_SERVER")
				if ret["status"]==0:
					remote_server=ret["return"]
				
					server_ip=socket.gethostbyname(remote_server)
					if server_ip not in self.core.get_all_ips():
						
						context=ssl._create_unverified_context()
						c = xmlrpc.client.ServerProxy('https://%s:9779'%server_ip,context=context,allow_none=True)
						mac=self.core.get_mac_from_device(self.core.route_get_ip(server_ip))
						f=open(ClientManager.MACHINE_FILE)
						machine_id=f.readline().strip("\n")
						f.close()
						ret=c.register_client("","ClientManager","",mac,machine_id)
						if ret["status"]==0:
							self.server_id=ret["return"]
				
			except Exception as e:
				self.dprint(e)
				self.server_id=None
				
			time.sleep(ClientManager.REGISTER_SLEEP_TIME)

	#def register_n4d_instance_to_server
	
	def save_clients_file(self):
		
		f=open(ClientManager.CLIENTS_FILE,"w")
		data=json.dumps(self.clients,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()
		
		return True

	#def save_clients
	
	def load_clients_file(self):
	
		if os.path.exists(ClientManager.CLIENTS_FILE):
			try:
				#self.dprint("Loading previous client file...")
				f=open(ClientManager.CLIENTS_FILE)	
				data=json.load(f)
				f.close()
				self.clients=data
			except Expcetion as e:
				self.dprint(e)
		
	#def load_clients_file
	