import N4dLib
import core

def dec(in_params,out_params):
	
	def inner(f):
		
		f.introspection={}
		f.introspection["in"]=in_params
		f.introspection["out"]=out_params
		return f
	
	return inner


class TestPlugin:
	
	#predepends=["ClientManager"]
	
	def __init__(self):
		
		self.core=core.Core.get_core()
		
	#def init
	
	def startup(self,options={}):
		
		self.core.register_variable_trigger("REMOTE_VARIABLES_SERVER","TestPlugin",self.kolibri)
		self.core.set_variable("PABLITO","CLAVITO")
		
	#def startup
	
	def kolibri(self,remote_variables_server):
		
		self.core.dprint("KOLIBRI %s"%remote_variables_server)
		
	#def
	
	@dec("ss","i")
	def test(self,a,b):
		
		return N4dLib.build_call_successful_response(a+b)
		
		
	def protected_args(self,user,ip):
		
		return N4dLib.build_call_successful_response((user,ip))
		
	#def protected_args

	
#class TestPlugin


