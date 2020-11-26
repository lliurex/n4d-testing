import threading
import time
import json
import random
import os
import sys
import copy
import xmlrpc.client
import ssl
import traceback


import n4d.server.core
import n4d.responses

class VariablesManager:
	
	VARIABLES_DIR="/var/lib/n4d/variables/"
	VARIABLES_DIR="/var/lib/n4d/variables-dir/"
	RUN_DIR="/run/n4d/variables/"
	INBOX="/var/lib/n4d/variables-inbox/"
	TRASH="/var/lib/n4d/variables-trash/"
	LOG="/var/log/n4d/variables-manager"
	
	VARIABLE_NOT_FOUND_ERROR=-5
	PROTECTED_VARIABLE_ERROR=-10
	REMOTE_VARIABLES_SERVER_ERROR=-15
	
	LOCK_FILE=RUN_DIR+"lock"
	
	def __init__(self):

		#this should be the first thing called
		self.core=core.Core.get_core()
		
		self.variables={}
		self.triggers={}
		
		self.create_run_dir()
		self.load_variables()
		
		'''
		t=threading.Thread(target=self.check_clients,args=())
		t.daemon=True
		t.start()
		
		self.read_inbox(False)
		self.empty_trash(False)
		'''
		
		#self.save_variables()
		
	#def init
	
	def dprint(self,data):
		
		if core.Core.DEBUG:
			print("[VariablesManager] %s"%data)
			
	#def dprint

	def dstdout(self,data):
		
		if core.Core.DEBUG:
			sys.stdout.write(str(data))
			
	#def dstdout
	
	def create_run_dir(self):
		
		if not os.path.exists(VariablesManager.RUN_DIR):
			os.makedirs(VariablesManager.RUN_DIR)
			
		if os.path.exists(VariablesManager.LOCK_FILE):
			os.remove(VariablesManager.LOCK_FILE)
			
	#def create_run_dir
	
	def load_variables(self):
		
		self.dprint("Loading variables...")
		
		self.variables={}
		
		for file_ in os.listdir(VariablesManager.VARIABLES_DIR):
			try:
				self.dstdout("\tLoading " + file_ + " ... ")
				f=open(VariablesManager.VARIABLES_DIR+file_)	
				data=json.load(f)
				f.close()
				self.variables[file_]=data[file_]
				self.dstdout("OK\n")
			except Exception as e:
				self.dstdout("FAILED ["+str(e)+"]\n")
	
	#def load_variables
	
	def save_variables(self,variable_name=None):
		
		try:
			while os.path.exists(VariablesManager.LOCK_FILE):
				time.sleep(2)
				
			f=open(VariablesManager.LOCK_FILE,"w")
			f.close()
			
			if variable_name==None:
			
				tmp_vars={}
				for item in self.variables:
					if "volatile" in self.variables[item] and self.variables[item]["volatile"]==False:
						tmp_vars[item]=self.variables[item]
						
				for item in tmp_vars:
					
					tmp={}
					tmp[item]=tmp_vars[item]
					f=open(VariablesManager.VARIABLES_DIR+item+".sav","w")
					data=json.dumps(tmp,indent=4,ensure_ascii=False)
					f.write(data)
					f.close()
					'''
					if "root_protected" in tmp_vars[item]:
						if tmp_vars[item]["root_protected"]:
							self.chmod(VariablesManager.VARIABLES_DIR+item,0600)
					'''
			else:
				if variable_name in self.variables and not self.variables[variable_name]["volatile"]:
					var={}
					var[variable_name]={}
					var[variable_name]=self.variables[variable_name]
					f=open(VariablesManager.VARIABLES_DIR+variable_name,"w")
					data=json.dumps(var,indent=4,ensure_ascii=False)
					f.write(data)
					f.close()
					
						
			os.remove(VariablesManager.LOCK_FILE)
			return True
			
		except Exception as e:
			os.remove(VariablesManager.LOCK_FILE)
			print(e)
			return False
		
	#def save_variables
			
	def set_variable(self,name,value,attr=None):
		
		if name not in self.variables:
			variable={}
			variable["value"]=None
			self.variables[name]=variable
			self.variables[name]["volatile"]=False
			
		self.variables[name]["value"]=value
		
		if type(attr)==dict:
			for key in attr:
				if key != "value":
					self.variables[name][key]=attr[key]
		
		self.save_variables(name)
		self.notify_changes(name,value)
		
		return n4d.responses.build_call_successful_response(True)
			
		
	#def set_variable
	
	def set_attr(self,name,attr):
		
		if name in self.variables:
			for key in attr:
				if key!="value":
					self.variables[name][key]=attr[key]
			self.save_variables(name)
		
			return n4d.responses.build_call_successful_response(True,"Attributes set")
		
		return n4d.responses.build_call_failed_response(None,"Variable not found",VariablesManager.VARIABLE_NOT_FOUND_ERROR)
		
	#def set_attr
	
	def delete_attr(self,name,key):
		
		if name in self.variables:
			if key != "value" and key in self.variables["name"]:
				self.variables["name"].pop(key)
				self.save_variables(name)
			
			return n4d.responses.build_call_successful_response(True,"Attribute deleted")
		
		return n4d.responses.build_call_failed_response(None,"Variable not found",VariablesManager.VARIABLE_NOT_FOUND_ERROR)
		
	#def delete_attr
	
	def get_variable(self,name,full_description=False):
		
		if name in self.variables:
			
			if "root_protected" in self.variables[name] and self.variables[name]["root_protected"]:
				return n4d.responses.build_call_failed_response(None,"Root protected variable. File is found in %s%s"%(VariablesManager.WATCH_DIR,name),VariablesManager.PROTECTED_VARIABLE_ERROR)
			
			if full_description:
				return n4d.responses.build_call_successful_response(copy.deepcopy(self.variables[name]))
			else:
				return n4d.responses.build_call_successful_response(copy.deepcopy(self.variables[name]["value"]))
				
		elif "REMOTE_VARIABLES_SERVER" in self.variables:
			
			if self.variables["REMOTE_VARIABLES_SERVER"]["value"] not in self.core.get_all_ips():
				context=ssl._create_unverified_context()
				s = xmlrpc.client.ServerProxy('https://%s:9779'%self.variables["REMOTE_VARIABLES_SERVER"]["value"],context=context,allow_none=True)
				try:
					#ret=s.get_variable(name,full_description)
					#if ret["status"]==0:
					#	return ret
					
					#HACK
					ret=s.get_variable("","VariablesManager",name)
					return ret
					
				except Exception as e:
					tback=traceback.format_exc()
					return n4d.responses.build_call_failed_response(None,str(e),VariablesManager.REMOTE_VARIABLES_SERVER_ERROR,tback)
				
		return n4d.responses.build_call_failed_response(None,"Variable not found",VariablesManager.VARIABLE_NOT_FOUND_ERROR)
		
	#def get_variable
	
	
	def get_variables(self,full_info=False):
		
		if full_info:
			return n4d.responses.build_call_successful_response(copy.deepcopy(self.variables))
		
		ret={}
		
		for variable in self.variables:
			ret[variable]=copy.deepcopy(self.variables[variable]["value"])
		
		return n4d.responses.build_call_successful_response(ret)
		
	#def get_variables
	
	def delete_variable(self,name):
		
		if name in self.variables:
			self.variables.pop(name)
			if os.path.exists(VariablesManager.VARIABLES_DIR+name):
				os.remove(VariablesManager.VARIABLES_DIR+name)
				
			return n4d.responses.build_call_successful_response(True,"Variable deleted")
			
		return n4d.responses.build_call_failed_response(None,"Variable not found",VariablesManager.VARIABLE_NOT_FOUND_ERROR)
		
	#def delete_variable
	
	def notify_changes(self,variable_name,value):
		
		t=threading.Thread(target=self._notify_changes,args=(variable_name,value))
		t.daemon=True
		t.start()
		
	#def notify_changes
	
	def _notify_changes(self,variable_name,value):
		
		cm=self.core.get_plugin("ClientManager")
		if cm==None:
			return False
			
		for client in cm.clients:
			try:
				#self.dprint("Notifying %s changes to %s..."%(variable_name,cm.clients[client]["ip"]))
				context=ssl._create_unverified_context()
				s = xmlrpc.client.ServerProxy('https://%s:9800'%cm.clients[client]["ip"],context=context,allow_none=True)
				s.server_changed(self.core.id,variable_name,value)
			except:
				pass
			
			
	#def notify_changes
	
	def register_trigger(self,variable_name,class_name,function):
		
		if variable_name not in self.triggers:
			self.triggers[variable_name]=set()
		
		self.triggers[variable_name].add((class_name,function))
		
		self.dprint("Trigger registered %s %s"%(variable_name,class_name))
		
		return True
		
	#def register_trigger
	

#class VariablesManager