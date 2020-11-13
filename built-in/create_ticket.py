import N4dLib

def create_ticket(self,user):
	
	ret=self.tickets_manager.create_ticket(user)

	if ret:
		return N4dLib.build_call_successful_response(True,"Ticket created for user %s"%user)
	else:
		error_code=-5
		return N4dLib.build_authentication_failed_response(False,"Failed to create ticket fo ruser %s"%user,error_code)

#def test
