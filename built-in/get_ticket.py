import n4d.responses
import os

def get_ticket(self,user,password):

	ret=self.validate_user(user,password)
	if ret["status"]!=0:
		return n4d.responses.build_authentication_failed_response()
		
	ticket=self.tickets_manager.get_ticket(user)
	return n4d.responses.build_successful_call_response(ticket)

#def set_variable

