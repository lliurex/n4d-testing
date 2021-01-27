import sys
import time
import glob
import xmlrpc
import traceback
import random
import string
import imp
import grp
import pwd
import os
import netifaces
import subprocess
import threading

import n4d.responses

import n4d.server.pluginmanager
import n4d.server.pammanager
import n4d.server.variablesmanager
import n4d.server.ticketsmanager
import n4d.server.clientmanager


UNKNOWN_CLASS=-40
UNKNOWN_METHOD=-30
USER_NOT_ALLOWED=-20
AUTHENTICATION_ERROR=-10

ANONYMOUS_AUTH=50
PAM_AUTH=60
KEY_AUTH=70
UNKNOWN_AUTH=80

DEFAULT_ALLOWED_GROUPS=["sudo","admins","root"]

class Core:
	
	BASE_DIR="/usr/share/n4d/"
	BUILTIN_FUNCTIONS_PATH=BASE_DIR+"built-in/"
	N4D_KEY_PATH="/etc/n4d/key"
	PUBLIC_BASE_FUNCTIONS=[]
	DEBUG=False
	VALID_AUTH_TYPES=[ANONYMOUS_AUTH,PAM_AUTH,KEY_AUTH]
	SINGLETON=None
	RUN_DIR="/run/n4d/"
	RUN_TOKEN="/run/n4d/token"
	LOG_DIR="/var/log/n4d/"
	ERROR_SLEEP_TIME=2
	
	
	@classmethod
	def get_core(self,debug=False):
		
		if self.__module__ != "n4d.server.core":
			raise Exception("Core singletion exception: You should access Core using 'n4d.server.core' instead of '%s'"%self.__module__)
		if Core.SINGLETON==None:
			Core.SINGLETON=Core(debug)
			Core.SINGLETON.init()

		if Core.SINGLETON.load_ok:
			return Core.SINGLETON
		
		return None
	
	@classmethod
	def get_random_id(self):
		
		chars=string.ascii_lowercase
		size=10
		return ''.join(random.choice(chars) for _ in range(size))
		
	#def get_random_id

	class Builtin:
		pass
	
	def __init__(self,debug_mode=False):
		
		Core.DEBUG=debug_mode
		self.dprint("INIT ... ")
		
		self.load_ok=False
		self.boot=False
		
		self.id=self.get_random_id()
		self.load_ok=self.create_n4d_dirs()
		self.load_ok=self.create_token()
		
		self.validation_history={}
		self.builtin_protected_args={}
		self.executed_startups=[]
		
		self.n4d_id_validation_errors_count=0
		
		self.execute_auth={}
		self.execute_auth[ANONYMOUS_AUTH]=self.anonymous_auth
		self.execute_auth[KEY_AUTH]=self.key_auth
		self.execute_auth[PAM_AUTH]=self.pam_auth
				
		self.n4d_key=self.read_n4d_key()
			
		if not self.load_ok or not self.n4d_key:
			#THIS, we are printing
			print("You are either importing n4d.server.core outside n4d-server instance or something went really bad")
		
	#def init

	def init(self):
		
		#variables_manager should be first just in case
		self.variables_manager=n4d.server.variablesmanager.VariablesManager()
		self.clients_manager=n4d.server.clientmanager.ClientManager()
		self.tickets_manager=n4d.server.ticketsmanager.TicketsManager()
		self.load_builtin_functions()
		self.load_plugins()
		self.execute_startups()
		
	#def init
		
		
	def execute_startups(self):
		
		self.startup_thread=threading.Thread(target=self._startup_launcher)
		self.startup_thread.daemon=True
		self.startup_thread.start()
		
	#def execute_startups
	
	def _startup_launcher(self):
		
		self.dprint("[CORE] Executing startups ... ")
		
		withstartup = []
		next_objects = []
		
		for x in self.plugin_manager.plugins:
			try:
				if not self.plugin_manager.plugins[x]["found"]:
					continue
				if x in self.executed_startups:
					continue
				if not hasattr(self.plugin_manager.plugins[x]["object"],'startup'):
					continue
				if not callable(getattr(self.plugin_manager.plugins[x]["object"],'startup')):
					continue
				
				options={}
				options["boot"]=self.boot
				if not os.path.exists(Core.RUN_TOKEN):
					options["boot"]=True
				withstartup.append((self.plugin_manager.plugins[x]["object"],options))
				
			except Exception as e:
				self.dprint(e)
				
		change = True
		while change:
			change = False
			for x in range(len(withstartup)-1,-1,-1):
				if ( not hasattr(withstartup[x][0],'predepends') or len( set(withstartup[x][0].predepends) - set(self.executed_startups)) <= 0 ) \
				and ( not hasattr(withstartup[x][0],'next_to') or len( set(withstartup[x][0].next_to) - set(next_objects)) <= 0):
					try:
						self.dprint("[STARTUP] Executing " +  withstartup[x][0].__class__.__name__ + " with options " +  str(withstartup[x][1]) + " ...")
						withstartup[x][0].startup(withstartup[x][1])
						self.executed_startups.append(withstartup[x][0].__class__.__name__)
					except Exception as e:
						self.dprint(e)
					next_objects.append(withstartup[x][0].__class__.__name__)
					withstartup.pop(x)
					change = True
		
	#def startup_launcher

	# ####################  #
	# DEBUG PRINTING FUNCTIONS #
	
	def dprint(self,data):
		
		if Core.DEBUG:
			print("[Core] %s"%str(data))
			
	#def dprint

	def dstdout(self,data):
		
		if Core.DEBUG:
			sys.stdout.write(str(data))
			
	#def dstdout
	
	
	def pprint(self,plugin_name,data):
		
		if Core.DEBUG:
			print("[%s] %s"%(plugin_name,str(data)))
		
	#def pprint
	
	# ###################### #
	# NETWORK RELATED FUNCTIONS #
	
	def get_net_size(self,netmask):
		'''
		Calculates bitmask from netmask
		ex:
			get_broadcast("eth0")
		'''
		netmask=netmask.split(".")
		binary_str = ''
		for octet in netmask:
			binary_str += bin(int(octet))[2:].zfill(8)
		return str(len(binary_str.rstrip('0')))

	#def get_net_size
	
	def get_device_info(self,dev):
		'''
		Returns a dictionary with the information of a certain network interface.
		ex:
			get_device_info("eth0")
		'''	
		dic={}
		for item in netifaces.interfaces():
			if item==dev:
				info=netifaces.ifaddresses(item)
				dic["name"]=item
				if netifaces.AF_LINK in info:
					if "addr" in info[netifaces.AF_LINK][0]:
						dic["mac"]=info[netifaces.AF_LINK][0]["addr"]
					else:
						dic["mac"]=""
				if netifaces.AF_INET in info:
					if "broadcast" in info[netifaces.AF_INET][0]:
						dic["broadcast"]=info[netifaces.AF_INET][0]["broadcast"]
					else:
						dic["broadcast"]=""
					if "netmask" in info[netifaces.AF_INET][0]:
						dic["netmask"]=info[netifaces.AF_INET][0]["netmask"]
						dic["bitmask"]=self.get_net_size(dic["netmask"])
					else:
						dic["bitmask"]=""
						dic["netmask"]=""
					if "addr" in info[netifaces.AF_INET][0]:
						dic["ip"]=info[netifaces.AF_INET][0]["addr"]
					else:
						dic["ip"]=""
				return dic
	
	#def get_device_info
	
	def get_all_ips(self):
		
		ret=set()
		ret.add("127.0.0.1")
		for item in netifaces.interfaces():
			info=self.get_device_info(item)
			if "ip" in info:
				ret.add(info["ip"])
			
		return list(ret)
	
	#def get_all_ips
	
	def get_mac_from_device(self,dev):

		for item in netifaces.interfaces():
			
			try:
				i=netifaces.ifaddresses(item)
				mac=i[17][0]["addr"]
				broadcast=i[2][0]["broadcast"]
				network=broadcast
				netmask=i[2][0]["netmask"]
				network+="/%s"%self.get_net_size(netmask)
				ip=i[2][0]["addr"]
			except Exception as e:
				continue
			
			if dev=="lo":
				return mac
			
			if item==dev:
				return mac
				
		return None

	#def get_mac_from_device_in_server_network
	
	def route_get_ip(self,ip):
		
		p=subprocess.Popen(["ip route get %s"%ip],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
		output=p[0].decode("utf-8")
		if "dev" in output:
			dev=output.split("dev ")[1].split(" ")[0]
		else:
			dev=None

		return dev
		
	#def route_get_ip	
	
	# ################### #
	# INTERNAL FUNCTIONS
	
	def read_n4d_key(self):
		
		key=None
		self.dprint("Reading N4D key ... ")
		try:
			f = open(Core.N4D_KEY_PATH)
			key = f.readline().strip('\n')
			f.close()
		except Exception as e:
			self.dprint("FAILED: %s"%e)
		
		return key
		
	#def read_n4d_key
	
	def create_n4d_dirs(self):
		
		try:
			if not os.path.exists(Core.RUN_DIR):
				os.makedirs(Core.RUN_DIR)
				
			if not os.path.exists(Core.LOG_DIR):
				os.makedirs(Core.LOG_DIR)
				
			return True
			
		except:
			self.dprint("You need root privileges to run this daemon")
			#sys.exit(1)
			return False
			
			
	#def create_n4d_dirs
	
	def create_token(self):
		
		try:
		
			if not os.path.exists(Core.RUN_TOKEN):
				self.boot=True
			
			f=open(Core.RUN_TOKEN,"w")
			f.write(str(os.getpid()))
			f.close()
			return True
			
		except:
			self.dprint("You need root privileges to run this daemon")
			#sys.exit(1)
			return False

	#def create_token
	
	def get_user_groups(self,user):
		
		groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
		groups.append("*")
		groups.append("anonymous")
		gid = pwd.getpwnam(user).pw_gid
		groups.append(grp.getgrgid(gid).gr_name)
		return groups
		
	#def get_user_groups
	
	def load_builtin_functions(self):

		self.dprint("Sourcing built-in functions ...")
		for f in glob.glob(Core.BUILTIN_FUNCTIONS_PATH+"**/*.py",recursive=True):
			try:
				if not os.path.isfile(f):
					continue
				
				f_name=f.replace(Core.BUILTIN_FUNCTIONS_PATH,"")
				self.dstdout("\t\t%s ... "%f_name)
				f_name=f_name.strip(".py").split("/")[-1]
				exec(open(f).read())
				setattr(Core,"builtin_"+f_name,locals()[f_name])
				if not f_name.startswith("_"):
					Core.PUBLIC_BASE_FUNCTIONS.append(f_name)
				self.dstdout("OK\n")
			except Exception as e:
				self.dstdout(e)
				self.dstdout("\n")
				
	#def load_builtin_functions
	
	def load_plugins(self):
		
		self.dprint("Initializing plugins ...")
		self.plugin_manager=n4d.server.pluginmanager.PluginManager()
		
		for item in self.plugin_manager.plugins:
			self._load_plugin(item,True)

	#def load_plugins
	
	def _load_plugin(self,plugin,verbose=False):
		
		if "found" in self.plugin_manager.plugins[plugin] and self.plugin_manager.plugins[plugin]["found"]:
			if verbose:
				self.dstdout("\t\t%s ... "%plugin)
			try:
				class_=imp.load_source(plugin,self.plugin_manager.plugins[plugin]["plugin_path"])
				self.plugin_manager.plugins[plugin]["object"]=getattr(class_,plugin)()
				if verbose:
					self.dstdout("OK\n")
				return True
			except Exception as e:
				if verbose:
					self.dstdout("FAILED\n")
					self.dstdout("\t\t\t[!] " + str(e)+"\n")
				self.plugin_manager.plugins[plugin]["object"]=None
				return False
		
		return False
		
	#def _load_plugin
	
	def load_plugin_on_runtime(self,plugin_conf):

		plugin=self.plugin_manager.read_plugin_conf(plugin_conf)
		if plugin!=None:
			ret=self._load_plugin(plugin,True)
			if ret:
				self._startup_launcher()
				return ret
				
		return False

	#def _load_plugin
	
	def unload_plugin(self,plugin_name):
		
		if plugin_name in self.plugin_manager.plugins:
			self.plugin_manager.plugins.pop(plugin_name)
			self.dprint("\t\t%s unloaded"%plugin_name)
			return n4d.responses.build_successful_call_response(True,"Plugin unloaded")
		
		return n4d.responses.buid_failed_call_response(False,"Plugin not found")
		
	#def unload_plugin
	
	def parse_params(self,method,params):
		
		# 0 n4d_extra (dict : client_address, client_pid)
		# 1 authentication
		# 2 class
		# 3... function args
		
		def _verify_params(n4d_params):
			
			ok=True
			exc_txt="Unknown error"
			
			if type(n4d_params)!=dict:
				ok=False
				exc_txt="Could not build params dict."
			if not type(n4d_params["class"]) == str:
				ok=False
				exc_txt="class is not a string"
			if not (type(n4d_params["user"]) == str or n4d_params["user"] == None):
				ok=False
				exc_txt="Authentication user is not a string or None"
			if not (type(n4d_params["password"]) == str or n4d_params["password"] == None):
				ok=False
				exc_txt="Authentication password is not a string or None"
			if not ok:
				raise NameError(exc_txt)

			return True
			
		#def verify_params
		
		def _auth_parsing(auth):
		
			auth_type=PAM_AUTH
			user=None
			password=None
			
			if type(auth)==str:
				if len(auth)==0:
					auth_type=ANONYMOUS_AUTH
					user="anonymous"
				else:
					auth_type=KEY_AUTH
					user="root"
					password=auth
					
			if type(auth)==tuple or type(auth)==list:
				user,password=auth
			
			return user,password,auth_type
			
		#def auth_parsing
		
		try:
			
			n4d_call_data=params[0]
			n4d_call_data["error"]=None
			n4d_call_data["method"]=method
			
			if method in Core.PUBLIC_BASE_FUNCTIONS:
				n4d_call_data["user"]=None
				n4d_call_data["password"]=None
				n4d_call_data["auth_type"]=ANONYMOUS_AUTH
				n4d_call_data["class"]="Core"
				n4d_call_data["params"]=tuple(params[1:])
			else:
				if len(params)>1:
					n4d_call_data["user"],n4d_call_data["password"],n4d_call_data["auth_type"]=_auth_parsing(params[1])
					n4d_call_data["class"]=params[2]
					n4d_call_data["params"]=tuple(params[3:])
					_verify_params(n4d_call_data)
				else:
					n4d_call_data["error"]="Unknown built-in method and/or class"
					n4d_call_data["traceback"]="[Core.parse_params] Not enough arguments to parse a standard n4d call."
				
			return n4d_call_data
			
		except Exception as e:
			print(e)
			n4d_call_data["error"]=str(e)
			tback=traceback.format_exc()
			n4d_call_data["traceback"]=tback
			return n4d_call_data
			
		
	#def extract_extra_params
	
	def authenticate(self,n4d_data):
		
		if n4d_data["auth_type"] in Core.VALID_AUTH_TYPES:
			return self.execute_auth[n4d_data["auth_type"]](n4d_data)
		else:
			raise NameError("Unknown authentication type")
		
	#def authenticate

	def pam_auth(self,n4d_data):
		
		user=n4d_data["user"]
		password=n4d_data["password"]
		sleep_time=2
		
		if self.cache_auth(n4d_data):
			return True
			
		if self.n4d_ticket_auth(n4d_data):
			return True

		#self.dprint("PAM_AUTH")
		pv=n4d.server.pammanager.PamManager()
		
		if pv.authentication(user,password):
			if user not in self.validation_history:
				self.validation_history[user]={}
				self.validation_history[user]["tries"]=0
				self.validation_history[user]["password"]=None
				
			self.validation_history[user]["tries"]=0
			self.validation_history[user]["password"]=password
			return True
			
		else:
			
			if user not in self.validation_history:
				self.validation_history[user]={}
				self.validation_history[user]["password"]=None
				self.validation_history[user]["tries"]=0
			self.validation_history[user]["tries"]+=1
			if self.validation_history[user]["tries"] > 10:
				self.dprint("[PAM_AUTH] Too many unsuccessful tries for user %s. Sleeping response..."%user)
				time.sleep(self.validation_history[user]["tries"]*sleep_time)
			return False

		return False
		
	#def pam_auth
	
	def cache_auth(self,n4d_data):
		
		user=n4d_data["user"]
		password=n4d_data["password"]
		
		if user in self.validation_history and self.validation_history[user]["password"]!=None and self.validation_history[user]["password"]==password:
			#self.dprint("User found in validation_history. Returning true...")
			#self.dprint("CACHE_AUTH")
			return True
			
		return False
		
	#def cache_auth
	
	def n4d_ticket_auth(self,n4d_data):
		
		if n4d_data["user"] in self.tickets_manager.tickets:
			if self.tickets_manager.tickets[n4d_data["user"]]["password"]==n4d_data["password"]:
				#self.dprint("N4D_TICKET_AUTH")
				return True
				
		return False
		
	#def n4d_ticket_auth
	
	def key_auth(self,n4d_data):
		#self.dprint("KEY_AUTH")

		if n4d_data["password"]==self.n4d_key:
			return True
			
		return False
		
	#def key_auth
	
	def anonymous_auth(self,n4d_data):
		#self.dprint("ANONYMOUS_AUTH")
		return True
	
	#def anonymous_auth
	
	def builtin_validation(self,auth,extra_valid_group_list=[]):
		
		#used by core built-ins

		USER_NOT_VALIDATED=-5
		USER_NOT_ALLOWED=-10
		USER_ALLOWED=0
		HUMAN_RESPONSES={}
		HUMAN_RESPONSES[USER_NOT_VALIDATED]="User not validated"
		HUMAN_RESPONSES[USER_NOT_ALLOWED]="User not allowed"
		HUMAN_RESPONSES[USER_ALLOWED]="User allowed"
		
		ret=self.validate_auth(auth)

		
		if ret["status"]!=0:
			return n4d.responses.build_authentication_failed_response()
			
		groups=ret["return"][1]
		group_found=False
		
		for group in groups:
			if group in DEFAULT_ALLOWED_GROUPS or group in extra_valid_group_list:
				group_found=True
				break
				
		if not group_found:
			return n4d.responses.build_user_not_allowed_response()
		else:
			return n4d.responses.build_successful_call_response(groups,HUMAN_RESPONSES[USER_ALLOWED])		
		
	#def builtin_validation
	
	def validate_user(self,user,password):
		
		validated=False
		n4d_data={}
		auth_type="Invalid user and/or password"
		groups=[]
		
		n4d_data["user"]=user
		n4d_data["password"]=password
		validated=self.n4d_ticket_auth(n4d_data)
		if not validated:
			validated=self.pam_auth(n4d_data)
		if validated:
			groups=self.get_user_groups(user)
			auth_type="User validated"

		if validated:
			return n4d.responses.build_successful_call_response([validated,groups],auth_type)
		else:
			return n4d.responses.build_authentication_failed_response()

	#def validate_user
	
	def validate_auth(self,auth):
		
		validated=False
		n4d_data={}
		auth_type="Unknown authentication type"
		groups=[]
		
		if type(auth)==str:
			auth_type="Invalid key"
			n4d_data["password"]=auth
			validated=self.key_auth(n4d_data)
			groups=["*","root"]
			if validated:
				auth_type="Key validated"
			
		if type(auth)==tuple or type(auth)==list:
			auth_type="Invalid user and/or password"
			user,password=auth
			ret=self.validate_user(user,password)
			if ret["status"]==0:
				validated=True
				auth_type="User validated"
				groups=ret["return"][1]
				
			
		if validated:
			return n4d.responses.build_successful_call_response([validated,groups],auth_type)
		else:
			return n4d.responses.build_authentication_failed_response()

	#def test	

	def _dispatch_core_function(self,n4d_call_data):
		
		self.dprint("[%s@%s] Executing %s.%s ..."%(n4d_call_data["user"] or "anonymous",n4d_call_data["client_address"] ,n4d_call_data["class"],n4d_call_data["method"]))
		
		method=n4d_call_data["method"]
		params=n4d_call_data["params"]
		
		if method in self.builtin_protected_args:
			if "protected_user" in self.builtin_protected_args[method]:
				if len(n4d_call_data["params"]) > self.builtin_protected_args[method]["protected_user"]:
					new_params=list(n4d_call_data["params"])
					new_params[self.builtin_protected_args[method]["protected_user"]]=n4d_call_data["user"]
					n4d_call_data["params"]=tuple(new_params)
				
			if "protected_ip" in self.builtin_protected_args[method]:
				if len(n4d_call_data["params"]) > self.builtin_protected_args[method]["protected_ip"]:
					new_params=list(n4d_call_data["params"])
					new_params[self.builtin_protected_args[method]["protected_ip"]]=n4d_call_data["client_address"]
					n4d_call_data["params"]=tuple(new_params)
		
		response=getattr(self,"builtin_"+n4d_call_data["method"])(*n4d_call_data["params"])
		return response

	#def _dispatch_core_function
	
	def _dispatch_plugin_function(self,n4d_call_data):
		
		
		if n4d_call_data["method"] in self.plugin_manager.plugins[n4d_call_data["class"]]["methods"]:

			groups=[]
			if n4d_call_data["password"]!=None:
				groups=self.get_user_groups(n4d_call_data["user"])
			else:
				groups=["anonymous"]
			
			ok=False
			
			for group in groups:
				if group in self.plugin_manager.plugins[n4d_call_data["class"]]["methods"][n4d_call_data["method"]]["allowed_groups"]:
					ok=True
					break
					
			if not ok:
				if "allowed_users" in self.plugin_manager.plugins[n4d_call_data["class"]]["methods"][n4d_call_data["method"]]:
					if user in self.plugin_manager.plugins[n4d_call_data["class"]]["methods"][n4d_call_data["method"]]["allowed_users"]:
						ok=True
		
			if n4d_call_data["user"]=="root" and not ok:
				ok=True
		
			if ok:
				class_=n4d_call_data["class"]
				method=n4d_call_data["method"]
				
				if "protected_user" in self.plugin_manager.plugins[class_]["methods"][method]:
					if len(n4d_call_data["params"]) > self.plugin_manager.plugins[class_]["methods"][method]["protected_user"]:
						new_params=list(n4d_call_data["params"])
						new_params[self.plugin_manager.plugins[class_]["methods"][method]["protected_user"]]=n4d_call_data["user"]
						n4d_call_data["params"]=tuple(new_params)
				
				if "protected_ip" in self.plugin_manager.plugins[class_]["methods"][method]:
					if len(n4d_call_data["params"]) > self.plugin_manager.plugins[class_]["methods"][method]["protected_ip"]:
						new_params=list(n4d_call_data["params"])
						new_params[self.plugin_manager.plugins[class_]["methods"][method]["protected_ip"]]=n4d_call_data["client_address"]
						n4d_call_data["params"]=tuple(new_params)
				
				self.dprint("%s@%s calling %s.%s ..."%(n4d_call_data["user"],n4d_call_data["client_address"],n4d_call_data["class"],n4d_call_data["method"]))
				response=getattr(self.plugin_manager.plugins[n4d_call_data["class"]]["object"],n4d_call_data["method"])(*n4d_call_data["params"])
			else:
				self.dprint("[!] %s@%s not allowed to run %s.%s ."%(n4d_call_data["user"],n4d_call_data["client_address"],n4d_call_data["class"],n4d_call_data["method"]))
				response=n4d.responses.build_user_not_allowed_response()
			
		else:
			response=n4d.responses.build_unknown_method_response()
			
		return response
		
	#def _dispatch_plugin_function

	def _dispatch(self,method,params):

		try:

			n4d_call_data=self.parse_params(method,params)

			if n4d_call_data["error"]!=None:
				return n4d.responses.build_unhandled_error_response(n4d_call_data["error"],n4d_call_data["traceback"])

			# If no exception is raised we are ok to authenticate
			if not self.authenticate(n4d_call_data):
				
				return n4d.responses.build_authentication_failed_response()
			
			# If auth is ok we execute function

			# is it a core function 
			if method in Core.PUBLIC_BASE_FUNCTIONS:
				response=self._dispatch_core_function(n4d_call_data)
			else:
				# a valid plugin plugin
				if n4d_call_data["class"] in self.plugin_manager.plugins and self.plugin_manager.plugins[n4d_call_data["class"]]["found"]:
					response=self._dispatch_plugin_function(n4d_call_data)
				else:
					response=n4d.responses.build_unknown_class_response()
			
			if not n4d.responses.is_valid_response(response):
					response=n4d.responses.build_invalid_response(response)
			
			return response
			
		except Exception as e:
			
			tback=traceback.format_exc()
			self.dprint("[!] Exception captured [!]")
			self.dprint(tback)
			#if type(e)==TypeError:
			#	response=n4d.responses.build_invalid_arguments_response(None,str(e),tback)
			#else:
			response=n4d.responses.build_unhandled_error_response(str(e),tback)

			return response
			raise e
					
	#def dispatch
	
	# ######################  #
	# DEVELOPER HELPER FUNCTIONS #
	
	def set_builtin_protected_args(self,function_name,args_dic):
		
		if function_name not in self.builtin_protected_args:
			self.builtin_protected_args[function_name]={}
			
		for key in args_dic:
			self.builtin_protected_args[function_name][key]=args_dic[key]
		
	#def
	
	def get_plugin(self,plugin_name):
		'''
		Function to help access plugins from other plugins
		'''
		if plugin_name in self.plugin_manager.plugins and self.plugin_manager.plugins[plugin_name]["found"] and "object" in self.plugin_manager.plugins[plugin_name]:
			
			return self.plugin_manager.plugins[plugin_name]["object"]
			
		return None
		
	#def get_plugin
	
	def register_variable_trigger(self,variable_name,class_name,function):
		'''
		Function to help access trigger registration from other plugins 
		'''
		return self.variables_manager.register_trigger(variable_name,class_name,function)
		
	#def register_variable_trigger
	
	def get_variable(self,variable_name,full_info=False):
		'''
		Wrap to variables_manager.get_variable
		'''
		
		return self.variables_manager.get_variable(variable_name,full_info)
		
	#def get_variable
	
	def get_variables(self,full_info=False):
		'''
		Wrap to variables_manager.get_variables
		'''
		return self.variables_manager.get_variables(full_info)
		
	#def get_variables
	
	def get_variable_list(self,variable_list,full_info=False):
		
		return self.variables_manager.get_variable_list(variable_list,full_info)
		
	#def get_variable_list
	
	def variable_exists(self,variable_name):
		'''
		Wrap to variables_manager.variable_exists
		'''
		return self.variables_manager.variable_exists(variable_name)
		
	#def variable_exists
		
	
	def set_variable(self,variable_name,value,attr=None):
		'''
		Wrap to variables_manager.set_variable
		'''
		return self.variables_manager.set_variable(variable_name,value,attr)
		
	#def set_variable
	
	def delete_variable(self,variable_name):
		'''
		Wrap to variables_manager.delete_variable
		'''
		return self.variables_manager.delete_variable(variable_name)
		
	#def root_set_variable
	
	def set_attr(self,variable_name,attr_dic):
		'''
		Wrap to variables_manager.set_attr
		'''
		return self.variables_manager.set_attr(variable_name,attr_dic)
		
	#def set_attr
	
	def delete_attr(self,variable_name,attr_key):
		'''
		Wrap to variables_manager.delete_attr
		'''
		return self.variables_manager.delete_attr(variable_name,attr_key)
		
	#def set_attr
	
	def read_inbox(self):
		'''
		Wrap to variables_manager.read_inbox
		'''
		return self.variables_manager.read_inbox()
		
	#def read_inbox
	
	def empty_trash(self):
		'''
		Wrap to variables_manager.empty_trash
		'''
		return self.variables_manager.empty_trash()
		
	#def read_inbox
	
	def get_client_list(self,force_check=False):
		
		return self.clients_manager.get_client_list(foce_check)
		
	#def get_client_list
	
	def check_clients(self,wait_for_response=False):
		
		return self.clients_manager.check_clients(wait_for_response)
		
	#def get_client_list
	
	def check_client(self,machine_id):
		
		return self.clients_manager.check_client(machine_id)
		
	#def get_client_list
	
#class Core