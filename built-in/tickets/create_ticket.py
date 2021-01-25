import n4d.responses

def create_ticket(self,user):
	
	ret=self.tickets_manager.create_ticket(user)

	if ret:
		return n4d.responses.build_successful_call_response(True,"Ticket created for user %s"%user)
	else:
		error_code=-5
		return n4d.responses.build_authentication_failed_response(False,"Failed to create ticket fo ruser %s"%user,error_code)

#def test
