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
		self.core=n4d.server.core.Core.get_core()
		
		self.variables={}
		self.triggers={}
		
		self.create_variables_dirs()
		
		self.load_variables()
		self.read_inbox()
		self.empty_trash()
		
	#def init
	
	def dprint(self,data):
		
		self.core.pprint("VariablesManager","%s"%data)
			
	#def dprint

	def dstdout(self,data):
		
		if n4d.server.core.Core.DEBUG:
			sys.stdout.write(str(data))
			
	#def dstdout
	
	def create_variables_dirs(self):
		
		if not os.path.exists(VariablesManager.VARIABLES_DIR):
			os.makedirs(VariablesManager.VARIABLES_DIR)
		
		if not os.path.exists(VariablesManager.INBOX):
			os.makedirs(VariablesManager.INBOX)
		
		if not os.path.exists(VariablesManager.TRASH):
			os.makedirs(VariablesManager.TRASH)
		
		if not os.path.exists(VariablesManager.RUN_DIR):
			os.makedirs(VariablesManager.RUN_DIR)
			
		if os.path.exists(VariablesManager.LOCK_FILE):
			os.remove(VariablesManager.LOCK_FILE)
			
	#def create_run_dir
	
	def load_variables(self):
		
		self.dprint("Loading variables...")
		for file_ in os.listdir(VariablesManager.VARIABLES_DIR):
			self.dstdout("\tLoading " + file_ + " ... ")
			try:
				f=open(os.path.join(VariablesManager.VARIABLES_DIR,file_))
				data=json.load(f)
				f.close()
				self.variables[file_]=data[file_]
				self.dstdout("OK\n")
			except Exception as e:
				self.dstdout("FAILED ["+str(e)+"]\n")
	
	#def load_variables
	
	def read_inbox(self):
		
		modified=False
		file_list=os.listdir(VariablesManager.INBOX)
		if len(file_list)>0:
			self.dprint("Loading variables inbox...")
			for file_ in file_list:
				try:
					self.dstdout("\tLoading " + file_ + " ... ")
					f=open(os.path.join(VariablesManager.INBOX,file_))
					data=json.load(f)
					f.close()

					for key in data:
						if "value" not in data[key]:
							self.dstdout("SKIPPED\n")
							continue
						if key not in self.variables:
							self.variables[key]=data[key]
							if "volatile" not in self.variables[key]:
								self.variables[key]["volatile"]=False
							if "force_update" not in self.variables[key]:
								self.variables[key]["force_update"]=False
							modified=True
							self.dstdout("OK\n")
						else:
							if "force_update" in data[key] and data:
								self.variables[key]=data[key]
								if "volatile" not in self.variables[key]:
									self.variables[key]["volatile"]=False
								if "force_update" not in self.variables[key]:
									self.variables[key]["force_update"]=False
								modified=True
								self.dstdout("OK\n")
							else:
								self.dstdout("SKIPPED\n")
				except Exception as e:
					self.dstdout("FAILED ["+str(e)+"]\n")
							
				os.remove(VariablesManager.INBOX+file_)
				
			if modified:
				self.save_variables()
		
		return n4d.responses.build_successful_call_response(True,"Inbox read")
		
	#def read_inbox
	
	def empty_trash(self):
		
		modified=False
		file_list=os.listdir(VariablesManager.TRASH)
		if len(file_list)>0:
			self.dprint("Emptying variables trash...")
			for file_ in file_list:
				self.dstdout("\tEmptying " + file_ + " ... ")
				if file_ in self.variables:
					self.variables.pop(file_)
					modified=True
				os.remove(VariablesManager.TRASH+file_)
		
		if modified:
			self.save_variables()
		
		return n4d.responses.build_successful_call_response(True,"Trash emptied")
		
	#def empty_trash
	
	def save_variables(self,variable_name=None):
		
		try:
			while os.path.exists(VariablesManager.LOCK_FILE):
				time.sleep(2)
				
			f=open(VariablesManager.LOCK_FILE,"w")
			f.close()
			
			if variable_name==None:
			
				tmp_vars={}
				for item in self.variables:
					if "volatile" in self.variables[item] and self.variables[item]["volatile"]:
						continue
					tmp_vars[item]=self.variables[item]
						
				for item in tmp_vars:
					
					tmp={}
					tmp[item]=tmp_vars[item]
					f=open(VariablesManager.VARIABLES_DIR+item,"w")
					data=json.dumps(tmp,indent=4,ensure_ascii=False)
					f.write(data)
					f.close()
					'''
					if "root_protected" in tmp_vars[item]:
						if tmp_vars[item]["root_protected"]:
							self.chmod(VariablesManager.VARIABLES_DIR+item,0600)
					'''
			else:
				if variable_name in self.variables:
					if "volatile" in self.variables[variable_name] and self.variables[variable_name]["volatile"]:
						return True
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
	
	def variable_exists(self,vname):
		
		value=vname in self.variables
		return n4d.responses.build_successful_call_response(value)
		
	#def variable_exists
			
	def set_variable(self,name,value,attr=None):
		
		if name not in self.variables:
			variable={}
			variable["value"]=None
			self.variables[name]=variable
			self.variables[name]["volatile"]=False
			
		self.variables[name]["value"]=value
		
		if type(attr)==dict:
			self.set_attr(name,attr)
		
		self.save_variables(name)
		if name in self.triggers:
			self.notify_changes(name,value)
		
		return n4d.responses.build_successful_call_response(True)
			
		
	#def set_variable
	
	def set_attr(self,name,attr_dic):
		
		if name in self.variables:
			for key in attr:
				if key!="value":
					self.variables[name][key]=attr[key]
			self.save_variables(name)

			return n4d.responses.build_successful_call_response(True,"Attributes set")
		
		return n4d.responses.build_failed_call_response(VariablesManager.VARIABLE_NOT_FOUND_ERROR,"Variable not found")
		
	#def set_attr
	
	def delete_attr(self,name,key):
		
		if name in self.variables:
			if key != "value" and key in self.variables["name"]:
				self.variables["name"].pop(key)
				self.save_variables(name)
			
			return n4d.responses.build_successful_call_response(True,"Attribute deleted")
		
		return n4d.responses.build_failed_call_response(VariablesManager.VARIABLE_NOT_FOUND_ERROR,"Variable not found")
		
	#def delete_attr
	
	def get_variable(self,name,full_description=False):
		
		if name in self.variables:
			
			if "root_protected" in self.variables[name] and self.variables[name]["root_protected"]:
				return n4d.responses.build_failed_call_response(VariablesManager.PROTECTED_VARIABLE_ERROR,"Root protected variable. File is found in %s%s"%(VariablesManager.WATCH_DIR,name))
			
			if full_description:
				return n4d.responses.build_successful_call_response(copy.deepcopy(self.variables[name]))
			else:
				return n4d.responses.build_successful_call_response(copy.deepcopy(self.variables[name]["value"]))
				
		elif "REMOTE_VARIABLES_SERVER" in self.variables:
			
			if self.variables["REMOTE_VARIABLES_SERVER"]["value"] not in self.core.get_all_ips():
				context=ssl._create_unverified_context()
				s = xmlrpc.client.ServerProxy('https://%s:9779'%self.variables["REMOTE_VARIABLES_SERVER"]["value"],context=context,allow_none=True)
				try:
					ret=s.get_variable(name,full_description)
					if ret["status"]==0:
						return ret

				except Exception as e:
					tback=traceback.format_exc()
					return n4d.responses.build_failed_call_response(VariablesManager.REMOTE_VARIABLES_SERVER_ERROR,str(e),tback)
				
		return n4d.responses.build_failed_call_response(VariablesManager.VARIABLE_NOT_FOUND_ERROR,"Variable not found")
		
	#def get_variable
	
	def get_variable_list(self,variable_list=[],full_info=False):
	
		ret={}
		
		for variable in variable_list:
			tmp=self.get_variable(variable,full_info)
			if tmp["status"]==0:
				ret[variable]=tmp["return"]
		
		return n4d.responses.build_successful_call_response(ret)
	
	#def get_variable_list
	
	def get_variables(self,full_info=False):
		
		if full_info:
			return n4d.responses.build_successful_call_response(copy.deepcopy(self.variables))
		
		ret={}
		
		for variable in self.variables:
			ret[variable]=copy.deepcopy(self.variables[variable]["value"])
		
		return n4d.responses.build_successful_call_response(ret)
		
	#def get_variables
	
	def delete_variable(self,name):
		
		if name in self.variables:
			self.variables.pop(name)
			if os.path.exists(VariablesManager.VARIABLES_DIR+name):
				os.remove(VariablesManager.VARIABLES_DIR+name)
				
			return n4d.responses.build_successful_call_response(True,"Variable deleted")
			
		return n4d.responses.build_failed_call_response(VariablesManager.VARIABLE_NOT_FOUND_ERROR,"Variable not found")
		
	#def delete_variable
	
	def notify_changes(self,variable_name,value):
		
		t=threading.Thread(target=self._notify_changes,args=(variable_name,value))
		t.daemon=True
		t.start()
		
	#def notify_changes
	
	def _notify_changes(self,variable_name,value):
		
		cm=self.core.clients_manager
		for client in cm.clients:
			try:
				#self.dprint("Notifying %s changes to %s..."%(variable_name,cm.clients[client]["ip"]))
				context=ssl._create_unverified_context()
				s = xmlrpc.client.ServerProxy('https://%s:9779'%cm.clients[client]["ip"],context=context,allow_none=True)
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