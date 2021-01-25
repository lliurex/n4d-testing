
def set_attr(self,auth,variable_name,attr_dic):

	ret=self.builtin_validation(auth)
	
	if ret["status"]==0:	
		#internal core funciton
		return self.set_variable(variable_name,value,attr_dic)
		#return self.variables_manager.set_variable(variable_name,value,extra_info)
	else:
		return ret

#def set_variable

