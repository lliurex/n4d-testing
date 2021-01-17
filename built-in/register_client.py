
args={}
args["protected_ip"]=0
self.set_builtin_protected_args("register_client",args)

def register_client(self,client_ip,mac,machine_id):

	#internal core function
	return self.clients_manager.register_client(client_ip,mac,machine_id)

#def get_variable
