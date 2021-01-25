import n4d.responses

def unload_plugin(self,auth,plugin_name):

	ret=self.builtin_validation(auth)
	if ret["status"]==0:
		#core internal function
		return self.unload_plugin(plugin_name)

#def unload_plugin

