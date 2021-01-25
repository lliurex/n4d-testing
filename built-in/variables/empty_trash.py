
def empty_trash(self,auth):

	ret=self.builtin_validation(auth)
	
	if ret["status"]==0:	
		#internal core funciton
		return self.empty_trash()
	else:
		return ret

#def set_variable

