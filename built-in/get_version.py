import pkg_resources
import n4d.responses

def get_version(self):
	
	version=pkg_resources.get_distribution('n4d').version
	return n4d.responses.build_successful_call_response(version)

#def test
