import n4d.responses
import time
import threading

def server_changed(self,n4d_id,variable_name,value):

	UNKNOWN_N4D_ID=-5
	
	if n4d_id == self.clients_manager.server_id:
		self.n4d_id_validation_errors_count=0
		if variable_name in self.variables_manager.triggers:
			self.dprint("N4D ID validated. Executing triggers for %s ..."%variable_name)
			for item in self.variables_manager.triggers[variable_name]:
				try:
					class_name,function=item
					t=threading.Thread(target=function,args=(value,))
					t.daemon=True
					t.start()
				except:
					pass
		
		return n4d.responses.build_successful_call_response(True)
	
	self.n4d_id_validation_errors_count+=1
	time.sleep(Core.ERROR_SLEEP_TIME*self.n4d_id_validation_errors_count)
	return n4d.responses.build_failed_call_response(UNKNOWN_N4D_ID,"Unknown N4D id")

#def set_variable

