import core
import glob
import json
import os
import configparser

class PluginManager:
	
	PYTHON_PLUGINS_PATH="python-plugins/"
	OLD_PYTHON_PLUGINS_PATH="/usr/share/n4d/python-plugins/"
	CONF_PATH="conf.d/"
	
	def dprint(self,data):
		
		if self.core.DEBUG:
			print("[PluginManager] %s"%data)
		
	#def dprint
	
	def __init__(self):
		
		#this should be the first thing called
		self.core=core.Core.get_core()

		self.plugin_path={}
		self.plugin_path["python"]=PluginManager.PYTHON_PLUGINS_PATH
		#self.plugin_path["python"]=PluginManager.OLD_PYTHON_PLUGINS_PATH
		
		self.plugins=self.get_plugins()
		#self.plugins=self.get_old_plugins()
		
	#def init
	
	def get_plugins(self):
		
		ret={}
		
		for item in glob.glob(PluginManager.CONF_PATH+"*.json"):
			
			try:
				plugin_name=item.split("/")[-1].split(".json")[0]
				ret[plugin_name]={}
				f=open(item)
				data=json.load(f)
				f.close()
				ret[plugin_name]["setup"]=data["SETUP"]
				ret[plugin_name]["methods"]=data["METHODS"]
				ret[plugin_name]["plugin_path"]=self.plugin_path[ret[plugin_name]["setup"]["type"]]+ret[plugin_name]["setup"]["path"]
				if os.path.exists(ret[plugin_name]["plugin_path"]):
					ret[plugin_name]["found"]=True
				else:
					ret[plugin_name]["found"]=False
				
			except Exception as e:
				ret[plugin_name]["found"]=False

		return ret
		
	#def get_python_plugins_list
	
	def get_old_plugins(self):
		
		ret={}
		
		cp=configparser.ConfigParser()
		cp.optionxform=str
		
		for item in glob.glob("/etc/n4d/conf.d/*"):
			
			try:
				cp.read(item)
				if cp.get("SETUP","type")=="python":
					plugin_name=cp.get("SETUP","class")
					ret[plugin_name]={}
					ret[plugin_name]["setup"]={}
					ret[plugin_name]["setup"]["type"]="python"
					ret[plugin_name]["setup"]["path"]=cp.get("SETUP","path")
					ret[plugin_name]["setup"]["class"]=cp.get("SETUP","class")
					ret[plugin_name]["plugin_path"]=self.plugin_path[ret[plugin_name]["setup"]["type"]]+ret[plugin_name]["setup"]["path"]
					if os.path.exists(ret[plugin_name]["plugin_path"]):
						ret[plugin_name]["found"]=True
					else:
						ret[plugin_name]["found"]=False
						
					ret[plugin_name]["found"]=True
					ret[plugin_name]["methods"]={}
					options=cp.options("METHODS")
					for option in options:
						tmp=cp.get("METHODS",option)
						tmp=tmp.replace(' ','')
						perm_list=tmp.split(",")
						ret[plugin_name]["methods"][option]={}
						ret[plugin_name]["methods"][option]["allowed_groups"]=perm_list
							
					
			except Exception as e:
				raise e
		
		#self.dprint(ret)
		
		return ret
		
	#def get_old_plugins
	
#class PluginManager