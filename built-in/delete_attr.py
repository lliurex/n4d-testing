
def delete_attr(self,auth,variable_name,attr_name):

	ret=self.builtin_validation(auth)
	if ret["status"]==0:
		#core internal function
		return self.delete_attr(variable_name,attr_name)
	else:
		return ret

#def set_variable

