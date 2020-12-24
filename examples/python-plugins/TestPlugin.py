import n4d.responses
import n4d.server.core


class TestPlugin:
	
	#predepends=["ClientManager"]
	
	def __init__(self):
		
		self.core=core.Core.get_core()
		
	#def init
	
	def startup(self,options={}):

		if options["boot"]:
			pass
		
		self.core.register_variable_trigger("REMOTE_VARIABLES_SERVER","TestPlugin",self.kolibri)
		self.core.set_variable("PABLITO","CLAVITO")
		
	#def startup
	
	def kolibri(self,remote_variables_server):
		
		self.core.dprint("KOLIBRI %s"%remote_variables_server)
		
	#def
	
	def test(self,a,b):
		return n4d.responses.build_successful_call_response(a+b)
		
	def protected_args(self,user,ip):
		return n4d.responses.build_successful_call_response((user,ip))
		
	#def protected_args

	
#class TestPlugin


