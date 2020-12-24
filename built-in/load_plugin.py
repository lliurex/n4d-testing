import n4d.responses

def load_plugin(self,auth,plugin_conf_path):

	ret=self.builtin_validation(auth)
	if ret["status"]==0:
		#core internal function
		loaded=self.load_plugin_on_runtime(plugin_conf_path)
		return n4d.responses.build_successful_call_response(loaded)
	else:
		return ret

#def set_variable

