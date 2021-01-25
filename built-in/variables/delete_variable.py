
def delete_variable(self,auth,variable_name):

	ret=self.builtin_validation(auth)
	if ret["status"]==0:
		#core internal function
		return self.delete_variable(variable_name)
	else:
		return ret

#def set_variable

