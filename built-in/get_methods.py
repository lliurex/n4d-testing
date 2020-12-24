import n4d.responses
import n4d.server.core

def get_methods(self,*args):
	
	core=n4d.server.core.Core.get_core()
	ret={}
	for x in core.plugin_manager.plugins:
		if core.plugin_manager.plugins[x]["found"]:
			ret[x]=core.plugin_manager.plugins[x]["methods"]
	
	return n4d.responses.build_successful_call_response(ret)

#def test
