import N4dLib
import os

def get_ticket(self,user,password):

	ret=self.validate_user(user,password)
	if ret["status"]!=0:
		return N4dLib.build_authentication_failed_response()
		
	ticket=self.tickets_manager.get_ticket(user)
	return N4dLib.build_call_successful_response(ticket)

#def set_variable

