
def read_inbox(self,auth):

	ret=self.builtin_validation(auth)
	
	if ret["status"]==0:	
		#internal core funciton
		return self.read_inbox()
	else:
		return ret

#def set_variable

